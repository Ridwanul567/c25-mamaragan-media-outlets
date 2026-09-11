"""Unit tests for dashboard data loading and datetime normalisation."""

from unittest.mock import MagicMock, patch
import pandas as pd
from src.data import load_data


@patch("boto3.resource")
def test_load_data_success(mock_boto_resource):
    """Test loading items from DynamoDB and converting GMT datetimes correctly."""
    load_data.clear()  # Clear Streamlit cache

    mock_table = MagicMock()
    mock_boto_resource.return_value.Table.return_value = mock_table
    mock_table.scan.return_value = {
        "Items": [
            {
                "article_id": "101",
                "outlet": "BBC News",
                "published_date": "Thu, 10 Sep 2026 10:00:00 GMT",
                "sentiment_score": 0.5,
                "entities": [{"text": "BBC", "label": "ORG"}],
            }
        ]
    }

    df = load_data()

    assert not df.empty
    assert len(df) == 1
    assert "published_date" in df.columns
    assert isinstance(df["published_date"].dtype, pd.DatetimeTZDtype)


@patch("boto3.resource")
def test_load_data_empty_response(mock_boto_resource):
    """Test load_data returns an empty DataFrame when DynamoDB returns no items."""
    load_data.clear()  # Clear Streamlit cache

    mock_table = MagicMock()
    mock_boto_resource.return_value.Table.return_value = mock_table
    mock_table.scan.return_value = {"Items": []}

    df = load_data()

    assert isinstance(df, pd.DataFrame)
    assert df.empty


@patch("boto3.resource")
def test_load_data_published_date_alias(mock_boto_resource):
    """Test load_data handles published_date column alias gracefully."""
    load_data.clear()  # Clear Streamlit cache

    mock_table = MagicMock()
    mock_boto_resource.return_value.Table.return_value = mock_table
    mock_table.scan.return_value = {
        "Items": [
            {
                "article_id": "102",
                "published_date": "2026-09-10T12:00:00 GMT",
                "sentiment_score": -0.2,
            }
        ]
    }

    df = load_data()

    assert "published_date" in df.columns
    assert isinstance(df["published_date"].dtype, pd.DatetimeTZDtype)
