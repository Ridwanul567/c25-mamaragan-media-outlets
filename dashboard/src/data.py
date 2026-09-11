"""Data loading module for the media outlets dashboard."""

import logging
import os
import boto3
import pandas as pd
import streamlit as st
from botocore.exceptions import BotoCoreError, ClientError

# Set up logging for container monitoring
logger = logging.getLogger(__name__)


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load articles from DynamoDB with robust error handling and type normalization."""
    table_name = os.getenv(
        "TABLE_NAME", "c25-mamaragan-media-outlets-articles")
    region = os.getenv("AWS_DEFAULT_REGION", "eu-west-2")

    try:
        dynamodb = boto3.resource("dynamodb", region_name=region)
        table = dynamodb.Table(table_name)

        response = table.scan()
        items = response.get("Items", [])

        # Handle DynamoDB pagination for scans exceeding 1MB
        while "LastEvaluatedKey" in response:
            response = table.scan(
                ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))

        if not items:
            st.info("ℹ️ No articles found in the database.")
            return pd.DataFrame()

        df = pd.DataFrame(items)

        # Convert numeric object/Decimal types from DynamoDB to standard float64
        numeric_cols = ["sentiment_score", "subjectivity_score"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Safely normalize datetimes and convert explicitly to UK time (BST/GMT)
        target_col = "published_date" if "published_date" in df.columns else None

        if target_col:
            df["published_date"] = pd.to_datetime(
                df[target_col].astype(str).str.replace(
                    " GMT", " +0000", regex=False
                ),
                errors="coerce",
                utc=True,
            )
            # Converts from UTC to Europe/London (automatically BST / UTC+1 during summer)
            df["published_date"] = df["published_date"].dt.tz_convert(
                "Europe/London")

        return df

    except (ClientError, BotoCoreError) as aws_err:
        logger.error(f"AWS DynamoDB fetch error: {aws_err}")
        st.error(
            "⚠️ Unable to load data from AWS DynamoDB. Please verify network connectivity and IAM task permissions."
        )
        return pd.DataFrame()

    except Exception as err:
        logger.error(f"Unexpected error loading dashboard data: {err}")
        st.error("⚠️ An unexpected error occurred while processing article data.")
        return pd.DataFrame()
