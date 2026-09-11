"""All non Bluesky related functions are here"""

import os
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import boto3


 
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


def analyse_article(article):
    """Pull out the relevant fields from one article, with clean types."""
    entities = [
        {**entity, "count": float(entity.get("count", 1))}
        for entity in article.get("entities", [])
    ]
    return {
        "title": article.get("title", ""),
        "outlet": article.get("outlet", "unknown"),
        "link": article.get("link", ""),
        "sentiment_score": float(article.get("sentiment_score", 0.0)),
        "subjectivity_score": float(article.get("subjectivity_score", 0.0)),
        "keywords": list(article.get("keywords", [])),
        "entities": entities,
    }


def summarise_metrics(articles):
    """Combine analysed articles into per-entity stats and top keywords."""
    entity_stats = {}
    keyword_counts = {}

    for article in articles:
        for keyword in article["keywords"]:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        seen_in_this_article = set()
        for entity in article["entities"]:
            name = entity["text"]
            if name not in entity_stats:
                entity_stats[name] = {
                    "label": entity["label"],
                    "mention_count": 0,
                    "article_count": 0,
                    "sentiments": [],
                }
            entity_stats[name]["mention_count"] += entity["count"]
            entity_stats[name]["sentiments"].append(article["sentiment_score"])
            if name not in seen_in_this_article:
                entity_stats[name]["article_count"] += 1
                seen_in_this_article.add(name)

    for stats in entity_stats.values():
        sentiments = stats.pop("sentiments")
        stats["avg_sentiment"] = sum(sentiments) / len(sentiments)

    top_keywords = sorted(keyword_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]

    return {
        "entities": entity_stats,
        "top_keywords": top_keywords,
    }


def check_condition(entity_stats, min_mentions=5, sentiment_threshold=0.7, direction="above"):
    """Return entities whose mention count and sentiment trip the given rule."""
    triggered = []
    for name, stats in entity_stats.items():
        if stats["mention_count"] < min_mentions:
            continue
        avg = stats["avg_sentiment"]
        if direction == "above" and avg >= sentiment_threshold:
            triggered.append({"name": name, **stats})
        elif direction == "below" and avg <= sentiment_threshold:
            triggered.append({"name": name, **stats})
    return triggered