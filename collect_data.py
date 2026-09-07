"""Script to collect and process RSS feed articles into a table."""

import xml.etree.ElementTree as ET
import requests
import pandas as pd


def get_rss_feed(url):
    """Fetch and parse the RSS feed from the given URL."""
    response = requests.get(url, timeout=5)
    return ET.fromstring(response.content)


def get_articles(root):
    """Extract articles information from the parsed RSS feed XML tree."""
    articles = []
    for child in root:
        for subchild in child:
            if subchild.tag == 'item':
                article = {}
                for item_child in subchild:
                    article[item_child.tag] = item_child.text
                articles.append(article)
    return articles


def convert_to_dateframe(articles: dict):
    """Convert the list of article dictionaries to a pandas DataFrame."""
    df = pd.DataFrame(articles)
    df.drop(
        columns=[r'{http://search.yahoo.com/mrss/}thumbnail', 'link'], inplace=True)
    df.rename(columns={'pubDate': 'published_date',
              'guid': 'link'}, inplace=True)
    return df


if __name__ == "__main__":
    root = get_rss_feed('https://feeds.bbci.co.uk/news/uk/rss.xml')
    articles = get_articles(root)
    articles = convert_to_dateframe(articles)
    articles.to_csv('articles.csv', index=False)
