from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from media_articles import get_latest_articles, parse_published_date


def make_article(published_date, article_id="some-id"):
    return {
        "article_id": article_id,
        "published_date": published_date,
        "sentiment_score": 0.1,
        "outlet": "The Independent",
    }


def test_parse_published_date_converts_string_to_datetime():
    result = parse_published_date("Wed, 09 Sep 2026 18:48:53 GMT")
    assert result == datetime(2026, 9, 9, 18, 48, 53, tzinfo=timezone.utc)


def test_get_latest_articles_includes_recent_article():
    now = datetime.now(timezone.utc)
    recent = now - timedelta(hours=2)
    recent_str = recent.strftime("%a, %d %b %Y %H:%M:%S GMT")

    table = MagicMock()
    table.scan.return_value = {"Items": [make_article(recent_str)]}

    result = get_latest_articles(table)

    assert len(result) == 1


def test_get_latest_articles_excludes_old_article():
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=3)
    old_str = old.strftime("%a, %d %b %Y %H:%M:%S GMT")

    table = MagicMock()
    table.scan.return_value = {"Items": [make_article(old_str)]}

    result = get_latest_articles(table)

    assert len(result) == 0


def test_get_latest_articles_returns_empty_list_when_no_items():
    table = MagicMock()
    table.scan.return_value = {"Items": []}

    result = get_latest_articles(table)

    assert result == []