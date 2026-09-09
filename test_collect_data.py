"""Unit Tests for collect_data.py"""

import xml.etree.ElementTree as ET
from unittest.mock import patch
import requests
import pytest
from collect_data import get_rss_feed, get_articles, convert_to_dataframe

SAMPLE_URL = 'https://random.co.uk/url.xml'


def test_get_rss_feed_client_error(requests_mock):
    requests_mock.get(SAMPLE_URL,
                      status_code=400)
    with pytest.raises(Exception) as exception:
        get_rss_feed(SAMPLE_URL)

    assert requests_mock.called
    assert requests_mock.call_count == 1
    assert requests_mock.last_request.method == "GET"

    assert exception.value.args[0][0:3] == "400"


def test_get_rss_feed_server_error(requests_mock):
    requests_mock.get(SAMPLE_URL,
                      status_code=500)
    with pytest.raises(Exception) as exception:
        get_rss_feed(SAMPLE_URL)

    assert requests_mock.called
    assert requests_mock.call_count == 1
    assert requests_mock.last_request.method == "GET"

    assert exception.value.args[0][0:3] == "500"


def test_get_articles_no_items_in_feed():
    empty_feed = ET.Element("rss")
    empty_channel = ET.SubElement(empty_feed, "channel")

    with pytest.raises(ValueError):
        get_articles(empty_feed, [])


def test_get_articles_valid_article():
    feed = ET.Element("rss")
    channel = ET.SubElement(feed, "channel")
    item = ET.SubElement(channel, "item")
    title = ET.SubElement(item, "title")
    title.text = "Sample Article"
    description = ET.SubElement(item, "description")
    description.text = "Sample Description"
    guid = ET.SubElement(item, "guid")
    guid.text = "https://example.com/sample-article"
    pubDate = ET.SubElement(item, "pubDate")
    pubDate.text = "Wed, 01 Jan 2025 00:00:00 GMT"

    articles = get_articles(feed, [])
    assert len(articles) == 1
    assert articles == [{
        "title": "Sample Article",
        "description": "Sample Description",
        "guid": "https://example.com/sample-article",
        "pubDate": "Wed, 01 Jan 2025 00:00:00 GMT"
    }]


def test_convert_to_dataframe():
    articles = [{
        "title": "Sample Article",
        "description": "Sample Description",
        "guid": "https://example.com/sample-article",
        "pubDate": "Wed, 01 Jan 2025 00:00:00 GMT"
    }]

    df = convert_to_dataframe(articles)
    assert not df.empty
    assert list(df.columns) == [
        "title", "description", "link", "published_date"]
    assert df.iloc[0]["title"] == "Sample Article"
    assert df.iloc[0]["description"] == "Sample Description"
    assert df.iloc[0]["link"] == "https://example.com/sample-article"
    assert df.iloc[0]["published_date"] == "Wed, 01 Jan 2025 00:00:00 GMT"
