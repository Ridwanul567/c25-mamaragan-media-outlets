"""Tests for Bluesky functions."""

from unittest.mock import MagicMock, patch

from bluesky_app import format_alert_post, post_positive_alerts, format_daily_summary_post, post_daily_summary, post_message


def make_entity(name="Dolly Parton", mention_count=9.0, avg_sentiment=0.70):
    return {"name": name, "mention_count": mention_count, "avg_sentiment": avg_sentiment}


def test_format_alert_post_contains_name_and_sentiment():
    entity = make_entity()
    text = format_alert_post(entity)

    assert "Dolly Parton" in text
    assert "9 mentions" in text
    assert "0.70" in text


def test_format_alert_post_has_no_emoji():
    entity = make_entity()
    text = format_alert_post(entity)

    assert text.isascii()


def test_format_alert_post_mention_count_is_whole_number_not_float():
    entity = make_entity(mention_count=9.0)
    text = format_alert_post(entity)

    assert "9 mentions" in text
    assert "9.0 mentions" not in text


@patch("bluesky_app.post_message")
def test_post_positive_alerts_posts_each_entity(mock_post_message):
    mock_post_message.return_value = "https://bsky.app/profile/x/post/1"
    alerts = [make_entity()]

    urls = post_positive_alerts(alerts, client=MagicMock())

    assert urls == ["https://bsky.app/profile/x/post/1"]
    mock_post_message.assert_called_once()


@patch("bluesky_app.post_message")
def test_post_positive_alerts_skips_failed_posts(mock_post_message):
    mock_post_message.return_value = None
    alerts = [make_entity()]

    urls = post_positive_alerts(alerts, client=MagicMock())

    assert urls == []


@patch("bluesky_app.post_message")
def test_post_positive_alerts_handles_multiple_entities(mock_post_message):
    mock_post_message.side_effect = [
        "https://bsky.app/profile/x/post/1",
        "https://bsky.app/profile/x/post/2",
    ]
    alerts = [make_entity(name="Dolly Parton"), make_entity(name="Another Star")]

    urls = post_positive_alerts(alerts, client=MagicMock())

    assert len(urls) == 2
    assert mock_post_message.call_count == 2


@patch("bluesky_app.post_message")
def test_post_positive_alerts_empty_list_returns_empty(mock_post_message):
    urls = post_positive_alerts([], client=MagicMock())

    assert urls == []
    mock_post_message.assert_not_called()


def make_metrics(top_keywords):
    return {"entities": {}, "top_keywords": top_keywords}


def test_format_daily_summary_includes_top_five_keywords():
    metrics = make_metrics([("Film", 5), ("Music", 4), ("Drama", 3), ("TV", 2), ("Radio", 2), ("Sport", 1)])
    text = format_daily_summary_post(metrics)

    assert "Film" in text
    assert "Music" in text
    assert "Sport" not in text 


def test_format_daily_summary_has_no_emoji():
    metrics = make_metrics([("Film", 5)])
    text = format_daily_summary_post(metrics)

    assert text.isascii()


@patch("bluesky_app.post_message")
def test_post_daily_summary_posts_when_keywords_exist(mock_post_message):
    mock_post_message.return_value = "https://bsky.app/profile/x/post/1"
    metrics = make_metrics([("Film", 5)])

    url = post_daily_summary(metrics, client=MagicMock())

    assert url == "https://bsky.app/profile/x/post/1"
    mock_post_message.assert_called_once()


@patch("bluesky_app.post_message")
def test_post_daily_summary_skips_when_no_keywords(mock_post_message):
    metrics = make_metrics([])

    url = post_daily_summary(metrics, client=MagicMock())

    assert url is None
    mock_post_message.assert_not_called()


def test_post_message_builds_correct_url():
    client = MagicMock()
    client.send_post.return_value.uri = "at://did:plc:abc123/app.bsky.feed.post/xyz789"

    url = post_message("hello", client)

    assert url == "https://bsky.app/profile/did:plc:abc123/post/xyz789"


def test_post_message_returns_none_on_failure():
    client = MagicMock()
    client.send_post.side_effect = Exception("network error")

    url = post_message("hello", client)

    assert url is None