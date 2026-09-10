"""Functionality to make posts to Bluesky"""

import os

from dotenv import load_dotenv
from atproto import Client

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
    ...
