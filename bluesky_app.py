from dotenv import load_dotenv
import os
from atproto import Client

load_dotenv()


client = Client()
HANDLE = os.environ["HANDLE"]
PASSWORD = os.environ["PASSWORD"]


client.login(HANDLE, PASSWORD)

def post_message(message: str):
    """Posts a given message to the Bluesky bot account"""

    try:
        post = client.send_post(message)
        rkey = post.uri.split('/')[-1]
        did = post.uri.split('/')[2]  # the DID is embedded in the URI itself
        url = f"https://bsky.app/profile/{did}/post/{rkey}"
        return url
    
    except Exception as e:
        print(f"Failed to post: {e}")
        return None
    

    
if __name__ == "__main__":
    print(post_message("Hello!"))
