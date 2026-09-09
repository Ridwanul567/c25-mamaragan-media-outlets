"""Integration unit tests for pipeline."""

from unittest.mock import patch
import pytest


@patch("pipeline.save_articles_to_dynamodb")
@patch("pipeline.enrich_articles")
@patch("pipeline.filter_new_articles")
@patch("pipeline.get_all_articles")
def test_run_pipeline_success(
    mock_get_all, mock_filter, mock_enrich, mock_save
):
    """Verify full orchestration loop completes without invoking real AWS APIs or external HTTP endpoints."""
    # 1. Mock article collection step
    sample_article = {
        "article_id": "https://www.bbc.co.uk/news/123",
        "title": "Sample Article",
        "link": "https://www.bbc.co.uk/news/123",
        "description": "Sample description",
        "outlet": "BBC News",
    }
    mock_get_all.return_value = [sample_article]

    # 2. Mock deduplication filter step
    mock_filter.return_value = [sample_article]

    # 3. Mock enrichment step
    mock_enrich.return_value = [
        {
            **sample_article,
            "entities": [{"text": "BBC", "label": "ORG"}],
            "sentiment_score": 0.5,
            "subjectivity_score": 0.5,
        }
    ]

    # 4. Mock database step
    mock_save.return_value = 1

    # Execute
    from pipeline import run_pipeline

    run_pipeline()

    # Assertions
    mock_get_all.assert_called_once()
    mock_filter.assert_called_once_with([sample_article])
    mock_enrich.assert_called_once()
    mock_save.assert_called_once()


@patch("pipeline.filter_new_articles")
@patch("pipeline.get_all_articles")
def test_run_pipeline_empty_collection_exits_early(mock_get_all, mock_filter):
    """Verify pipeline halts gracefully if no new articles are found after filtering."""
    mock_get_all.return_value = []
    mock_filter.return_value = []

    from pipeline import run_pipeline

    run_pipeline()

    mock_get_all.assert_called_once()
    mock_filter.assert_called_once_with([])
