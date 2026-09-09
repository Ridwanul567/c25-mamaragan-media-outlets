"""Fetch and parse media outlet RSS feeds into dictionaries."""

from curl_cffi import requests
import logging
import xml.etree.ElementTree as ET

BBC_RSS_URL = "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml"
INDEPENDENT_RSS_URL = "https://www.independent.co.uk/arts-entertainment/rss"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    )
}


def get_rss_feed(url: str) -> ET.Element:
    """Fetch and parse RSS XML."""
    response = requests.get(url, impersonate="chrome",
                            headers=HEADERS, timeout=(5, 10))
    response.raise_for_status()
    return ET.fromstring(response.content)


def extract_articles_from_xml(root: ET.Element, outlet_name: str) -> list[dict]:
    """Extract article metadata."""
    articles = []
    for item in root.findall(".//item"):
        # Safe string fallback for missing nodes
        link = (item.findtext("link") or item.findtext("guid") or "").strip()
        title = (item.findtext("title") or "Untitled Article").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = (item.findtext("description") or "").strip()

        # Skip entries without valid links
        if not link:
            logging.warning(
                "Skipping RSS item with missing URL/guid from %s", outlet_name)
            continue

        articles.append({
            "article_id": link,
            "title": title,
            "link": link,
            "published_date": pub_date,
            "description": description,
            "outlet": outlet_name,
        })
    return articles


def get_all_articles() -> list[dict]:
    """Fetch all RSS feeds."""
    all_articles = []
    feeds = [(BBC_RSS_URL, "BBC News"),
             (INDEPENDENT_RSS_URL, "The Independent")]

    for url, outlet in feeds:
        try:
            root = get_rss_feed(url)
            items = extract_articles_from_xml(root, outlet)
            all_articles.extend(items)
        except Exception as err:
            logging.error(
                "Failed to collect RSS items from %s: %s", outlet, err)

    return all_articles


if __name__ == "__main__":
    articles = get_all_articles()
    print(f"Success! Retrieved {len(articles)} articles.")
    print(articles[0])
