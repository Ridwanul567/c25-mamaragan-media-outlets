"""Unit tests for db_writer."""

from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest

from db_writer import _format_floats, save_articles_to_dynamodb


def test_format_floats():
    """Verify that floats inside nested dicts/lists convert to Decimal."""
    sample_data = {
        "score": -0.85,
        "nested": {"subjectivity": 0.42},
        "tags": [0.1, 0.2],
        "label": "NEGATIVE",
    }
    formatted = _format_floats(sample_data)

    assert isinstance(formatted["score"], Decimal)
    assert formatted["score"] == Decimal("-0.85")
    assert isinstance(formatted["nested"]["subjectivity"], Decimal)
    assert isinstance(formatted["tags"][0], Decimal)
    assert formatted["label"] == "NEGATIVE"


@patch("db_writer.boto3.resource")
def test_save_articles_to_dynamodb_success(mock_boto_resource):
    """Verify that save_articles_to_dynamodb invokes batch_writer properly."""
    # Setup mock boto3 objects
    mock_dynamodb = MagicMock()
    mock_table = MagicMock()
    mock_batch = MagicMock()

    mock_boto_resource.return_value = mock_dynamodb
    mock_dynamodb.Table.return_value = mock_table
    mock_table.batch_writer.return_value.__enter__.return_value = mock_batch

    # Call the function with sample data
    test_articles = [
        {
            "article_id": "art_1",
            "title": "Celebrity Drama",
            "sentiment_score": -0.75,
            "outlet": "BBC",
        }
    ]

    written_count = save_articles_to_dynamodb(test_articles)

    # Assertions: verify the exact mock calls
    assert written_count == 1
    mock_boto_resource.assert_called_once_with(
        "dynamodb", region_name="eu-west-2")
    mock_dynamodb.Table.assert_called_once_with(
        "c25-mamaragan-media-outlets-articles")
    mock_batch.put_item.assert_called_once()


def test_save_articles_empty_list():
    """Ensure saving an empty list returns 0 without calling AWS."""
    written_count = save_articles_to_dynamodb([])
    assert written_count == 0
