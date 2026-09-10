"""Data loading utility for the media outlets dashboard."""

import boto3
import pandas as pd
import streamlit as st

TABLE_NAME = "c25-mamaragan-media-outlets-articles"


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load the media outlets articles directly from DynamoDB."""
    dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
    table = dynamodb.Table(TABLE_NAME)

    # Scan the full table
    response = table.scan()
    items = response.get("Items", [])

    # Handle if table grows beyond 1MB
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    if not items:
        return pd.DataFrame()

    df = pd.DataFrame(items)

    # Convert timestamp/date fields if present
    if "published_date" in df.columns:
        df["published_date"] = pd.to_datetime(df["published_date"])

    return df
