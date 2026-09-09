"""Integration unit tests for pipeline."""

from unittest.mock import MagicMock, patch
import pytest

from pipeline import run_pipeline


# <--- Mock out real DynamoDB calls
@patch("pipeline.save_articles_to_dynamodb")
@patch("pipeline.enrich_articles")
@patch("pipeline.collect_feed_articles")
def test_run_pipeline_success(mock_collect, mock_enrich, mock_save):
    """Verify full orchestration loop completes without invoking real AWS APIs."""
    # 1. Mock article collection step
    mock_collect.return_value = [
        {
            "article_id": "https://www.bbc.co.uk/news/123",
            "title": "Sample Article",
            "link": "https://www.bbc.co.uk/news/123",
            "description": "Sample description",
            "outlet": "BBC News",
        }
    ]

    # 2. Mock enrichment step
    mock_enrich.return_value = [
        {
            "article_id": "https://www.bbc.co.uk/news/123",
            "title": "Sample Article",
            "link": "https://www.bbc.co.uk/news/123",
            "description": "Sample description",
            "outlet": "BBC News",
            "entities": [{"text": "BBC", "label": "ORG"}],
            "sentiment_score": 0.5,
            "subjectivity_score": 0.5,
        }
    ]

    # 3. Mock database step
    mock_save.return_value = 1

    # Run orchestration
    run_pipeline()

    # Assertions
    mock_collect.assert_called()
    mock_enrich.assert_called_once()
    mock_save.assert_called_once()


@patch("pipeline.collect_feed_articles")
def test_run_pipeline_empty_collection_exits_early(mock_collect):
    """Verify pipeline halts gracefully if no new articles are found."""
    mock_collect.return_value = []

    run_pipeline()

    mock_collect.assert_called()
