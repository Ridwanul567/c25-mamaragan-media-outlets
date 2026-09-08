"""Script to collect and process RSS feed articles into a table."""

import xml.etree.ElementTree as ET
import requests
import pandas as pd

BBC_RSS_URL = 'https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml'
SKY_RSS_URL = 'https://feeds.skynews.com/feeds/rss/entertainment.xml'


def get_rss_feed(url) -> ET.Element:
    """Fetch and parse the RSS feed from the given URL."""
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return ET.fromstring(response.content)


def get_articles(root: ET.Element, articles: list) -> list:
    """Extract articles information from the parsed RSS feed XML tree."""
    for child in root:
        for subchild in child:
            if subchild.tag == 'item':
                article = {}
                for item_child in subchild:
                    article[item_child.tag] = item_child.text
                articles.append(article)
    if articles == []:
        raise ValueError("No articles found in the RSS feed.")
    return articles


def convert_to_dataframe(articles: list) -> pd.DataFrame:
    """Convert the list of article dictionaries to a pandas DataFrame."""
    df = pd.DataFrame(articles)
    df.drop(
        columns=[r'{http://search.yahoo.com/mrss/}thumbnail',
                 'link', 'enclosure', r'{http://search.yahoo.com/mrss/}content',
                 r'{http://search.yahoo.com/mrss/}description'], inplace=True, errors='ignore')
    df.rename(columns={'pubDate': 'published_date',
              'guid': 'link'}, inplace=True)
    return df


if __name__ == "__main__":
    articles = []

    bbc_root = get_rss_feed(BBC_RSS_URL)
    articles = get_articles(bbc_root, articles)

    sky_root = get_rss_feed(SKY_RSS_URL)
    articles = get_articles(sky_root, articles)

    articles = convert_to_dataframe(articles)
    articles.to_csv('articles.csv', index=False)
