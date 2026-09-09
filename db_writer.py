"""File to handle database writes to DynamoDB."""

import logging
from decimal import Decimal
from typing import Any, Dict, List
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("db_writer")

TABLE_NAME = "c25-mamaragan-media-outlets-articles"


# Helper function to format float values for DynamoDB compatibility
def _format_floats(obj: Any) -> Any:
    """Convert float values to Decimal for DynamoDB compatibility."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _format_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_format_floats(item) for item in obj]
    return obj


# Function to save articles to DynamoDB
def save_articles_to_dynamodb(
    articles: List[Dict[str, Any]], table_name: str = TABLE_NAME
) -> int:
    """Batch upload enriched articles into DynamoDB."""
    if not articles:
        logger.warning("No articles provided to save.")
        return 0

    dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
    table = dynamodb.Table(table_name)

    items_written = 0
    logger.info("Starting batch upload of %d items to %s",
                len(articles), table_name)

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
