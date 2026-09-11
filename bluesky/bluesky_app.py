"""Functionality to make posts to Bluesky"""

import os

from dotenv import load_dotenv
from atproto import Client
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from media_articles import (get_dynamodb_table, analyse_article, get_latest_articles, 
                            summarise_metrics, check_condition, parse_published_date
                            )

load_dotenv()


def get_bluesky_client() -> Client:
    """Log in to Bluesky using credentials from the environment."""
    client = Client()
    client.login(os.environ["HANDLE"], os.environ["PASSWORD"])
    return client


def post_message(message: str, client: Client):
    """Posts a given message to the Bluesky bot account"""

    try:
        post = client.send_post(message)
        rkey = post.uri.split('/')[-1]
        did = post.uri.split('/')[2] 
        url = f"https://bsky.app/profile/{did}/post/{rkey}"
        return url
    except Exception as e:
        print(f"Failed to post: {type(e).__name__}: {e}")
        return None


def format_alert_post(entity):
    """Build the plain-text Bluesky post for a triggered positive entity."""
    return (
        f"{entity['name']}: {int(entity['mention_count'])} mentions today, "
        f"strongly positive coverage (avg sentiment {entity['avg_sentiment']:.2f})."
    )


def post_positive_alerts(positive_alerts, client):
    """Post one message per triggered positive entity, return the list of URLs."""
    urls = []
    for entity in positive_alerts:
        message = format_alert_post(entity)
        url = post_message(message, client)
        if url:
            urls.append(url)
    return urls


def format_daily_summary_post(metrics):
    """Build the plain-text daily topics post from top keywords."""
    top_five = [keyword for keyword, count in metrics["top_keywords"][:5]]
    topics = ", ".join(top_five)
    return f"Today's top entertainment topics: {topics}."

def post_daily_summary(metrics, client):
    """Post the daily topic summary to Bluesky, return the URL or None."""
    if not metrics["top_keywords"]:
        return None
    message = format_daily_summary_post(metrics)
    return post_message(message, client)


def handler(event, context):
    """AWS Lambda entry point."""
    table = get_dynamodb_table()
    client = get_bluesky_client()

    raw_articles = get_latest_articles(table, hours=3)
    analysed = [analyse_article(article) for article in raw_articles]
    metrics = summarise_metrics(analysed)

    positive_alerts = check_condition(
        metrics["entities"], min_mentions=3, sentiment_threshold=0.7, direction="above"
    )
    negative_watchlist = check_condition(
        metrics["entities"], min_mentions=3, sentiment_threshold=-0.5, direction="below"
    )

    posted_urls = post_positive_alerts(positive_alerts, client)

    summary_url = None
    uk_time = datetime.now(timezone.utc).astimezone(ZoneInfo("Europe/London"))
    if uk_time.hour == 5:
        daily_articles = get_latest_articles(table, hours=24)
        daily_analysed = [analyse_article(article) for article in daily_articles]
        daily_metrics = summarise_metrics(daily_analysed)
        summary_url = post_daily_summary(daily_metrics, client)

    return {
        "positive_alerts_posted": len(posted_urls),
        "posted_urls": posted_urls,
        "negative_watchlist_count": len(negative_watchlist),
        "daily_summary_posted": summary_url is not None,
    }


if __name__ == "__main__":
    result = handler(None, None)
    print(result)