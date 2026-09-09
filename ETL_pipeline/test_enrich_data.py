"""Test suite for enrich_data.py functions."""

from unittest.mock import MagicMock, patch
import pytest
from requests.exceptions import HTTPError

from enrich_data import (
    enrich_articles,
    extract_entities,
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


# spacy and textblob tests

def test_extract_entities_spacy():
    """Verify spaCy extracts PERSON, ORG, or PRODUCT labels cleanly."""
    text = "Sir Paul Smith went to New York City to meet Apple executives."
    entities = extract_entities(text)

    entity_texts = [e["text"] for e in entities]
    assert "Paul Smith" in entity_texts or "Sir Paul Smith" in entity_texts
    assert "Apple" in entity_texts


def test_extract_entities_handles_empty_string():
    """Verify empty text inputs return empty entity lists safely."""
    assert extract_entities("") == []
    assert extract_entities(None) == []


@patch("enrich_data.get_html_content")
@patch("enrich_data.requests.Session")
def test_enrich_articles_success(mock_session_cls, mock_get_html):
    """Verify in-memory dictionary payload is injected with sentiment and entity fields."""
    mock_get_html.return_value = VALID_HTML_ARTICLE
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
    assert "sentiment_score" in enriched[0]
    assert "subjectivity_score" in enriched[0]
    assert isinstance(enriched[0]["sentiment_score"], float)


@patch("enrich_data.get_html_content")
@patch("enrich_data.requests.Session")
def test_enrich_articles_handles_http_failure_fallback(mock_session_cls, mock_get_html):
    """Ensure if full-body scraping fails (404/403), it falls back to title/description."""
    mock_get_html.side_effect = HTTPError("403 Forbidden")
    sample_articles = [{
        "article_id": "https://www.independent.co.uk/arts-entertainment/failed",
        "title": "Taylor Swift Tour",
        "link": "https://www.independent.co.uk/arts-entertainment/failed",
        "description": "Taylor Swift announces new tour dates.",
        "outlet": "The Independent"
    }]

    # Should NOT crash
    enriched = enrich_articles(sample_articles)

    assert len(enriched) == 1
    entity_texts = [e["text"] for e in enriched[0]["entities"]]
    assert "Taylor Swift" in entity_texts
