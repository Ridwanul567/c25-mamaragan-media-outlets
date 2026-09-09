"""Integration tests for pipeline."""

from unittest.mock import patch, MagicMock
from pipeline import run_pipeline


@patch("pipeline.save_articles_to_dynamodb")
@patch("pipeline.enrich_articles")
@patch("pipeline.get_all_articles")
def test_run_pipeline_success(mock_get_all, mock_enrich, mock_save_db):
    """Verify full end-to-end flow executes functions sequentially in-memory."""
    # Setup mock returns
    raw_mock_data = [
        {"article_id": "1", "title": "Test News", "link": "https://example.com"}]
    enriched_mock_data = [{
        "article_id": "1",
        "title": "Test News",
        "link": "https://example.com",
        "sentiment_score": 0.5,
        "entities": []
    }]

    mock_get_all.return_value = raw_mock_data
    mock_enrich.return_value = enriched_mock_data
    mock_save_db.return_value = 1

    run_pipeline()

    # Verify calls each stage in sequence
    mock_get_all.assert_called_once()
    mock_enrich.assert_called_once_with(raw_mock_data)
    mock_save_db.assert_called_once_with(enriched_mock_data)


@patch("pipeline.save_articles_to_dynamodb")
@patch("pipeline.enrich_articles")
@patch("pipeline.get_all_articles")
def test_run_pipeline_empty_collection_exits_early(mock_get_all, mock_enrich, mock_save_db):
    """Verify pipeline halts gracefully if collection returns no articles."""
    mock_get_all.return_value = []

    run_pipeline()

    mock_get_all.assert_called_once()
    # Should exit early without calling enrichment or database writes
    mock_enrich.assert_not_called()
    mock_save_db.assert_not_called()
