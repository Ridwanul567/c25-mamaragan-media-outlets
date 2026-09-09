"""File to handle database writes to DynamoDB."""
import os
from botocore.exceptions import ClientError
import boto3
from typing import Any, Dict, List
import logging
from decimal import Decimal
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("db_writer")

load_dotenv()

TABLE_NAME = "c25-mamaragan-media-outlets-articles"


def get_boto3_session() -> boto3.Session:
    """Create a boto3 session using credentials from environment variables."""
    return boto3.Session(
        aws_access_key_id=os.environ["ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["SECRET_ACCESS_KEY"],
        region_name=os.environ.get("AWS_REGION", "eu-west-2"))


def filter_new_articles(articles: list[dict], session: boto3.Session, table_name: str = TABLE_NAME) -> list[dict]:
    """Return only articles whose IDs do not already exist in DynamoDB."""
    if not articles:
        return []

    dynamodb = session.resource(
        "dynamodb", region_name="eu-west-2")
    table = dynamodb.Table(table_name)

    new_articles = []
    for article in articles:
        response = table.get_item(Key={"article_id": article["article_id"]})
        if "Item" not in response:
            new_articles.append(article)

    return new_articles


def _format_floats(obj: Any) -> Any:
    """Recursively convert float values to Decimal for DynamoDB compatibility."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _format_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_format_floats(item) for item in obj]
    return obj


def save_articles_to_dynamodb(articles: List[Dict[str, Any]], session: boto3.Session, table_name: str = TABLE_NAME) -> int:
    """Batch upload enriched articles into DynamoDB."""
    if not articles:
        logger.warning("No articles provided to save.")
        return 0

    dynamodb = session.resource(
        "dynamodb", region_name="eu-west-2")
    table = dynamodb.Table(table_name)
    items_written = 0

    try:
        with table.batch_writer() as batch:
            for article in articles:
                formatted_item = _format_floats(article)
                batch.put_item(Item=formatted_item)
                items_written += 1
        logger.info("Successfully inserted %d items into %s",
                    items_written, table_name)
    except ClientError as err:
        logger.error("Failed to write to DynamoDB: %s",
                     err.response["Error"]["Message"], exc_info=True)

    return items_written
