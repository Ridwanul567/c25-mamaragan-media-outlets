"""Functionality to make posts to Bluesky"""

import os

from dotenv import load_dotenv
from atproto import Client

from media_articles import get_dynamodb_table, analyse_article, get_latest_articles, summarise_metrics

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
    print(f"Found {len(raw_articles)} recent articles\n")

    analysed = [analyse_article(article) for article in raw_articles]

    metrics = summarise_metrics(analysed)

    print("Top keywords:")
    for keyword, count in metrics["top_keywords"]:
        print(f"  {keyword}: {count}")

    print("\nEntities:")
    for name, stats in metrics["entities"].items():
        print(f"  {name} ({stats['label']}): mentioned {stats['mention_count']} times "
              f"across {stats['article_count']} article(s), avg sentiment {stats['avg_sentiment']:.2f}")