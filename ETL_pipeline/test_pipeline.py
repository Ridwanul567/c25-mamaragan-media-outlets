"""Integration unit tests for pipeline."""

from pipeline import run_pipeline
import pytest
from unittest.mock import patch, MagicMock


@patch("pipeline.save_articles_to_dynamodb")
@patch("pipeline.enrich_articles")
@patch("pipeline.filter_new_articles")
@patch("pipeline.get_boto3_session")
@patch("pipeline.get_all_articles")
def test_run_pipeline_success(
    mock_get_all, mock_get_session, mock_filter, mock_enrich, mock_save
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

    # 2. Mock boto3 session step
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    # 3. Mock deduplication filter step
    mock_filter.return_value = [sample_article]

    # 4. Mock enrichment step
    mock_enrich.return_value = [
        {
            **sample_article,
            "entities": [{"text": "BBC", "label": "ORG"}],
            "sentiment_score": 0.5,
            "subjectivity_score": 0.5,
        }
    ]

    # 5. Mock database step
    mock_save.return_value = 1

    run_pipeline()

    # Assertions
    mock_get_all.assert_called_once()
    mock_get_session.assert_called_once()
    mock_filter.assert_called_once_with([sample_article], session=mock_session)
    mock_enrich.assert_called_once_with([sample_article])
    mock_save.assert_called_once_with(mock_enrich.return_value, session=mock_session)


@patch("pipeline.filter_new_articles")
@patch("pipeline.get_boto3_session")
@patch("pipeline.get_all_articles")
def test_run_pipeline_empty_collection_exits_early(mock_get_all, mock_get_session, mock_filter):
    """Verify pipeline halts gracefully if no new articles are found after filtering."""
    mock_get_all.return_value = []
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    mock_filter.return_value = []

    run_pipeline()

    mock_get_all.assert_called_once()
    mock_get_session.assert_called_once()
    mock_filter.assert_called_once_with([], session=mock_session)
