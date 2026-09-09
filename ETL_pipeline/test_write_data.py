"""Unit tests for db_writer.py using pytest and unittest.mock."""

from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from botocore.exceptions import ClientError

from write_data import _format_floats, save_articles_to_dynamodb

# Successful path tests


def test_format_floats():
    """Verify that floats inside nested dicts/lists convert to Decimal for DynamoDB."""
    sample_data = {
        "score": -0.85,
        "nested": {"subjectivity": 0.42},
        "tags": [0.1, 0.2],
        "label": "NEGATIVE",
        "int_val": 42,
    }
    formatted = _format_floats(sample_data)

    assert isinstance(formatted["score"], Decimal)
    assert formatted["score"] == Decimal("-0.85")
    assert isinstance(formatted["nested"]["subjectivity"], Decimal)
    assert isinstance(formatted["tags"][0], Decimal)
    assert formatted["label"] == "NEGATIVE"
    assert formatted["int_val"] == 42


@patch("write_data.boto3.resource")
def test_save_articles_to_dynamodb_success(mock_boto_resource):
    """Verify that save_articles_to_dynamodb invokes batch_writer properly."""
    mock_dynamodb = MagicMock()
    mock_table = MagicMock()
    mock_batch = MagicMock()

    mock_boto_resource.return_value = mock_dynamodb
    mock_dynamodb.Table.return_value = mock_table
    mock_table.batch_writer.return_value.__enter__.return_value = mock_batch

    test_articles = [
        {
            "article_id": "art_1",
            "title": "Celebrity Drama",
            "sentiment_score": -0.75,
            "outlet": "BBC News",
        }
    ]

    written_count = save_articles_to_dynamodb(test_articles)

    assert written_count == 1
    mock_boto_resource.assert_called_once_with(
        "dynamodb", region_name="eu-west-2")
    mock_dynamodb.Table.assert_called_once_with(
        "c25-mamaragan-media-outlets-articles")
    mock_batch.put_item.assert_called_once()


def test_save_articles_empty_list():
    """Ensure saving an empty list returns 0 without connecting to AWS."""
    written_count = save_articles_to_dynamodb([])
    assert written_count == 0


# Edge cases and failure tests

@patch("write_data.boto3.resource")
def test_save_articles_dynamodb_client_error(mock_boto_resource):
    """Ensure AWS ClientError (e.g., AccessDenied/ProvisionedThroughputExceeded) is caught gracefully."""
    mock_dynamodb = MagicMock()
    mock_table = MagicMock()

    mock_boto_resource.return_value = mock_dynamodb
    mock_dynamodb.Table.return_value = mock_table

    # Simulate DynamoDB throwing a ClientError during batch write context execution
    client_error = ClientError(
        {"Error": {"Code": "ResourceNotFoundException", "Message": "Table not found"}},
        "BatchWriteItem"
    )
    mock_table.batch_writer.side_effect = client_error

    test_articles = [{"article_id": "art_1", "title": "Test"}]

    # Should catch the exception, log the error, and return 0 items written
    written_count = save_articles_to_dynamodb(test_articles)
    assert written_count == 0


def test_format_floats_edge_cases():
    """Verify format_floats handles primitive edge cases like None or non-dict/list items."""
    assert _format_floats(None) is None
    assert _format_floats("string") == "string"
    assert _format_floats(10) == 10
