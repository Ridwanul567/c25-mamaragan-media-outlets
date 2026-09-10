"""All non Bluesky related functions are here"""

import os
import boto3 
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime


 
DEFAULT_TABLE_NAME = "c25-mamaragan-media-outlets-articles"

def get_dynamodb_table(table_name: str = DEFAULT_TABLE_NAME):
    """Create and return a boto3 DynamoDB Table resource."""
 
    dynamodb = boto3.resource(
        "dynamodb",
        region_name=os.environ["AWS_REGION"],
        aws_access_key_id=os.environ["ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["SECRET_ACCESS_KEY"],
    )
    return dynamodb.Table(table_name)



def parse_published_date(raw_date):
    """Turn 'Wed, 09 Sep 2026 18:48:53 GMT' into a real datetime."""
    return parsedate_to_datetime(raw_date)



def get_latest_articles(table):
    """Scan the table and return only articles published in the last 24 hours."""
    since = datetime.now(timezone.utc) - timedelta(days=1)

    response = table.scan()
    items = response["Items"]

    latest = []
    for item in items:
        published = parse_published_date(item["published_date"])
        if published >= since:
            latest.append(item)

    return latest


