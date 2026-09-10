"""Functionality to make posts to Bluesky"""

import os

from dotenv import load_dotenv
from atproto import Client

from media_articles import get_dynamodb_table, analyse_article, get_latest_articles, summarise_metrics, check_condition

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

if __name__ == "__main__":
    table = get_dynamodb_table()

    raw_articles = get_latest_articles(table)
    analysed = [analyse_article(article) for article in raw_articles]
    metrics = summarise_metrics(analysed)

    positive_alerts = check_condition(
        metrics["entities"], min_mentions=5, sentiment_threshold=0.7, direction="above"
    )
    negative_watchlist = check_condition(
        metrics["entities"], min_mentions=5, sentiment_threshold=-0.5, direction="below"
    )

    print(f"Positive alerts (would be posted): {len(positive_alerts)}")
    for entity in positive_alerts:
        print(f"  {entity['name']}: {entity['mention_count']} mentions, "
              f"avg sentiment {entity['avg_sentiment']:.2f}")

    print(f"\nNegative watchlist: {len(negative_watchlist)}")
    for entity in negative_watchlist:
        print(f"  {entity['name']}: {entity['mention_count']} mentions, "
              f"avg sentiment {entity['avg_sentiment']:.2f}")