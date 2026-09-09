"""Test suite for enrich_data.py functions."""

from unittest.mock import MagicMock, patch
import pytest
from requests.exceptions import HTTPError

from enrich_data import (
    analyse_text_with_openai,
    enrich_articles,
    extract_text_from_html,
    get_html_content,
)

SAMPLE_URL = "https://random.co.uk/random"

VALID_HTML_ARTICLE = """
<html>
    <head><title>Sample Page</title></head>
    <body>
        <article>
            <p>Taylor Swift and Apple performed in London for a massive stadium event.</p>
        </article>
    </body>
</html>"""


# HTTP get tests

def test_get_html_content_client_error():
    """Verify HTTP 400 client error raises an HTTPError exception."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = HTTPError("400 Client Error")
    mock_session.get.return_value = mock_response

    with pytest.raises(HTTPError):
        get_html_content(SAMPLE_URL, session=mock_session)

    mock_session.get.assert_called_once()


def test_get_html_content_server_error():
    """Verify HTTP 500 server error raises an HTTPError exception."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = HTTPError("500 Server Error")
    mock_session.get.return_value = mock_response

    with pytest.raises(HTTPError):
        get_html_content(SAMPLE_URL, session=mock_session)

    mock_session.get.assert_called_once()


def test_get_html_content_rejects_non_html():
    """Ensure non-HTML content types raise a ValueError."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/pdf"}
    mock_session.get.return_value = mock_response

    with pytest.raises(ValueError, match="did not return HTML"):
        get_html_content("https://example.com/download.pdf",
                         session=mock_session)


# HTML extraction tests

def test_extract_text_from_html_standard():
    """Verify text extraction when no article tag is present."""
    html_content = """
    <html><head><title>Sample Page</title></head><body><p>This is a <b>sample</b> paragraph.</p>
    <p>Another paragraph with <a href="#">a link</a>.</p></body></html>
    """
    text = extract_text_from_html(html_content)
    assert "This is a sample paragraph." in text
    assert "Another paragraph with a link ." in text


def test_extract_text_from_html_with_article_tag():
    """Verify extraction prioritizes inner article tags."""
    html_content = """
    <html><head><title>Sample Page</title></head><body><p>This is a <b>sample</b> paragraph.</p>
    <article><p>Another paragraph with <a href="#">a link</a>.</p></article></body></html>
    """
    text = extract_text_from_html(html_content)
    assert text == "Another paragraph with a link ."


# OpenAI NLP tests

@patch("enrich_data.OpenAI")
def test_analyse_text_with_openai_success(mock_openai_cls):
    """Verify OpenAI structured output parsing returns normalized entities and keywords."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client

    mock_parsed_data = MagicMock()
    mock_parsed_data.model_dump.return_value = {
        "entities": [
            {"text": "Donald Trump", "label": "PERSON", "count": 3},
            {"text": "London", "label": "GPE", "count": 1},
        ],
        "keywords": ["politics", "elections", "uk speech"],
        "sentiment_score": 0.15,
        "subjectivity_score": 0.45,
    }

    mock_client.beta.chat.completions.parse.return_value.choices[
        0
    ].message.parsed = mock_parsed_data

    result = analyse_text_with_openai("Trump spoke in London today.")

    assert result["entities"][0]["text"] == "Donald Trump"
    assert result["entities"][0]["count"] == 3
    assert result["keywords"] == ["politics", "elections", "uk speech"]
    assert result["sentiment_score"] == 0.15


@patch("enrich_data.analyse_text_with_openai")
@patch("enrich_data.get_html_content")
@patch("enrich_data.requests.Session")
def test_enrich_articles_success(mock_session_cls, mock_get_html, mock_analyze):
    """Verify in-memory dictionary payload is injected with OpenAI analysis results."""
    mock_get_html.return_value = VALID_HTML_ARTICLE
    mock_analyze.return_value = {
        "entities": [{"text": "Taylor Swift", "label": "PERSON", "count": 1}],
        "keywords": ["music", "concerts"],
        "sentiment_score": 0.8,
        "subjectivity_score": 0.5,
    }

    sample_articles = [{
        "article_id": "https://www.bbc.co.uk/news/123",
        "title": "Concert News",
        "link": "https://www.bbc.co.uk/news/123",
        "description": "Short description",
        "outlet": "BBC News"
    }]

    enriched = enrich_articles(sample_articles)

    assert len(enriched) == 1
    assert "entities" in enriched[0]
    assert "keywords" in enriched[0]
    assert enriched[0]["keywords"] == ["music", "concerts"]
    assert isinstance(enriched[0]["sentiment_score"], float)


@patch("enrich_data.analyse_text_with_openai")
@patch("enrich_data.get_html_content")
@patch("enrich_data.requests.Session")
def test_enrich_articles_handles_http_failure_fallback(mock_session_cls, mock_get_html, mock_analyze):
    """Ensure if full-body scraping fails (404/403), it falls back to title/description for OpenAI analysis."""
    mock_get_html.side_effect = HTTPError("403 Forbidden")
    mock_analyze.return_value = {
        "entities": [{"text": "Taylor Swift", "label": "PERSON", "count": 2}],
        "keywords": ["tour", "dates"],
        "sentiment_score": 0.5,
        "subjectivity_score": 0.3,
    }

    sample_articles = [{
        "article_id": "https://www.independent.co.uk/arts-entertainment/failed",
        "title": "Taylor Swift Tour",
        "link": "https://www.independent.co.uk/arts-entertainment/failed",
        "description": "Taylor Swift announces new tour dates.",
        "outlet": "The Independent"
    }]

    # Should NOT crash and still execute fallback analysis
    enriched = enrich_articles(sample_articles)

    assert len(enriched) == 1
    assert enriched[0]["entities"][0]["text"] == "Taylor Swift"
    mock_analyze.assert_called_once_with(
        "Taylor Swift Tour Taylor Swift announces new tour dates.")
