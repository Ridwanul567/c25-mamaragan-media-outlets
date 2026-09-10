"""Data loading module for the media outlets dashboard."""

import boto3
import pandas as pd
import streamlit as st

TABLE_NAME = "c25-mamaragan-media-outlets-articles"


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load articles from DynamoDB and safely normalize datetimes."""
    dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
    table = dynamodb.Table(TABLE_NAME)

    response = table.scan()
    items = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    if not items:
        return pd.DataFrame()

    df = pd.DataFrame(items)

    # Safely strip GMT string suffixes and convert to UTC datetime
    target_col = "published_date" if "published_date" in df.columns else None

    if target_col:
        df["published_date"] = pd.to_datetime(
            df[target_col].astype(str).str.replace(
                " GMT", " +0000", regex=False),
            errors="coerce",
            utc=True,
        )

    return df
