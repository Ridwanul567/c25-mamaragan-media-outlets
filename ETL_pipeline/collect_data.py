"""Fetch and parse media outlet RSS feeds into in-memory dictionaries."""

import xml.etree.ElementTree as ET
import logging
from curl_cffi import requests

BBC_RSS_URL = "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml"
SKY_RSS_URL = "https://feeds.skynews.com/feeds/rss/entertainment.xml"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    )
}


def get_rss_feed(url: str) -> ET.Element:
    """Fetch and parse RSS feed XML."""
    response = requests.get(url, impersonate="chrome",
                            headers=HEADERS, timeout=10)
    response.raise_for_status()
    return ET.fromstring(response.content)


def extract_articles_from_xml(root: ET.Element, outlet_name: str) -> list[dict]:
    """Extract article metadata from parsed XML element tree."""
    articles = []
    for item in root.findall(".//item"):
        link = item.findtext("link", "") or item.findtext("guid", "")
        if link:
            articles.append({
                "article_id": link,
                "title": item.findtext("title", ""),
                "link": link,
                "published_date": item.findtext("pubDate", ""),
                "description": item.findtext("description", ""),
                "outlet": outlet_name,
            })
    return articles


def get_all_articles() -> list[dict]:
    """Fetch and combine articles from all configured RSS feeds."""
    all_articles = []

    for url, outlet in [(BBC_RSS_URL, "BBC News"), (SKY_RSS_URL, "Sky News")]:
        try:
            root = get_rss_feed(url)
            items = extract_articles_from_xml(root, outlet)
            all_articles.extend(items)
        except Exception as err:
            logging.error(
                "Failed to collect articles from %s: %s", outlet, err)

    return all_articles


if __name__ == "__main__":
    articles = get_all_articles()
    print(f"Success! Retrieved {len(articles)} articles.")
    print(articles[0] if articles else "No articles retrieved.")
