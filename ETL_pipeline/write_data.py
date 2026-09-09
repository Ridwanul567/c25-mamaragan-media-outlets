"""File to handle database writes to DynamoDB."""

from botocore.exceptions import ClientError
import boto3
from typing import Any, Dict, List
import logging
from decimal import Decimal

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("db_writer")

TABLE_NAME = "c25-mamaragan-media-outlets-articles"


def _format_floats(obj: Any) -> Any:
    """Recursively convert float values to Decimal for DynamoDB compatibility."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _format_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_format_floats(item) for item in obj]
    return obj


def save_articles_to_dynamodb(articles: List[Dict[str, Any]], table_name: str = TABLE_NAME) -> int:
    """Batch upload enriched articles into DynamoDB."""
    if not articles:
        logger.warning("No articles provided to save.")
        return 0

    dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
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
