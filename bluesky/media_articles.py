import json
import os
import boto3 
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

 
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

