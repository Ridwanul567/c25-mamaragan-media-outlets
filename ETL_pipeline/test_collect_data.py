"""Unit tests for enrich_data module functions contained in test_collect_data.py."""

from enrich_data import (
    enrich_articles,
    extract_text_from_html,
    get_html_content,
)
from requests.exceptions import HTTPError
import pytest
from unittest.mock import MagicMock, patch


# Sample HTML fixtures for testing
VALID_HTML = """<html>
    <body>
        <article>
            <p>BBC News reports that Taylor Swift performed a concert in London for Apple.</p>
        </article>
    </body>
</html>"""

NON_ARTICLE_HTML = """<html>
    <body>
        <script>console.log('ignore me');</script>
        <p>Simple body content without an article tag.</p>
    </body>
</html>"""

# Successful Path Tests


def test_get_html_content_success():
    """Verify HTML string is returned on a successful 200 response."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.text = VALID_HTML
    mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}
    mock_session.get.return_value = mock_response

    html = get_html_content(
        "https://example.com/story/test", session=mock_session)
    assert "Taylor Swift" in html
    mock_session.get.assert_called_once()


def test_extract_text_from_html_strip_tags():
    """Verify script/style elements are stripped and body text is extracted."""
    text = extract_text_from_html(NON_ARTICLE_HTML)
    assert "ignore me" not in text
    assert "Simple body content" in text


@patch("enrich_data.get_html_content")
@patch("enrich_data.requests.Session")
def test_enrich_articles_populates_scores_and_entities(mock_session_cls, mock_get_html):
    """Verify raw article dictionary is injected with sentiment and entity lists."""
    mock_get_html.return_value = VALID_HTML
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


# Edge Case & Fallback Tests
def test_get_html_content_rejects_non_html():
    """Ensure non-HTML content types (like PDFs or MP3s) raise a ValueError."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/pdf"}
    mock_session.get.return_value = mock_response

    with pytest.raises(ValueError, match="did not return HTML"):
        get_html_content("https://example.com/download.pdf",
                         session=mock_session)


@patch("enrich_data.analyse_text_with_openai")
@patch("enrich_data.get_html_content")
@patch("enrich_data.requests.Session")
def test_enrich_articles_handles_http_failure_fallback(
    mock_session_cls, mock_get_html, mock_analyze
):
    """Ensure if scraping full text fails (404/403), it falls back to title/description."""
    mock_get_html.side_effect = HTTPError("403 Forbidden")
    mock_analyze.return_value = {
        "entities": [{"text": "Taylor Swift", "label": "PERSON", "count": 1}],
        "keywords": ["tour", "music"],
        "sentiment_score": 0.5,
        "subjectivity_score": 0.3,
    }

    sample_articles = [{
        "article_id": "https://www.independent.co.uk/arts-entertainment/failed",
        "title": "Taylor Swift Tour",
        "link": "https://www.independent.co.uk/arts-entertainment/failed",
        "description": "Taylor Swift announces tour dates.",
        "outlet": "The Independent",
    }]

    # Should NOT raise an exception
    enriched = enrich_articles(sample_articles)

    assert len(enriched) == 1
    entity_texts = [e["text"] for e in enriched[0]["entities"]]
    assert "Taylor Swift" in entity_texts
    mock_analyze.assert_called_once_with(
        "Taylor Swift Tour Taylor Swift announces tour dates."
    )
    assert "keywords" in enriched[0]
