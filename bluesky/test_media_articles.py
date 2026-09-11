from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
from decimal import Decimal

from media_articles import get_latest_articles, parse_published_date, analyse_article, summarise_metrics, check_condition, get_boto3_session
from unittest.mock import patch


@patch("media_articles.boto3.Session")
def test_get_boto3_session_uses_env_vars(mock_session, monkeypatch):
    monkeypatch.setenv("AWS_REGION", "eu-west-2")
    monkeypatch.setenv("ACCESS_KEY_ID", "fake-key")
    monkeypatch.setenv("SECRET_ACCESS_KEY", "fake-secret")

    get_boto3_session()

    mock_session.assert_called_once_with(
        region_name="eu-west-2",
        aws_access_key_id="fake-key",
        aws_secret_access_key="fake-secret",
    )


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

def test_converts_decimals_to_float_including_nested_entity_counts():
    article = {
        "sentiment_score": Decimal("0.2"),
        "subjectivity_score": Decimal("0.6"),
        "entities": [{"text": "Jane Doe", "label": "PERSON", "count": Decimal("2")}],
    }
    result = analyse_article(article)

    assert isinstance(result["sentiment_score"], float)
    assert isinstance(result["subjectivity_score"], float)
    assert isinstance(result["entities"][0]["count"], float)


def test_extracts_correct_values_not_just_correct_types():
    article = {
        "title": "Some title",
        "outlet": "The Independent",
        "sentiment_score": Decimal("0.2"),
        "keywords": ["Film", "Drama"],
        "entities": [{"text": "Jane Doe", "label": "PERSON", "count": Decimal("2")}],
    }
    result = analyse_article(article)

    assert result["title"] == "Some title"
    assert result["outlet"] == "The Independent"
    assert result["sentiment_score"] == 0.2
    assert result["keywords"] == ["Film", "Drama"]
    assert result["entities"][0]["text"] == "Jane Doe"
    assert result["entities"][0]["count"] == 2.0


def test_missing_fields_get_sensible_defaults():
    result = analyse_article({})

    assert result["title"] == ""
    assert result["outlet"] == "unknown"
    assert result["entities"] == []
    assert result["keywords"] == []


def test_empty_entities_list_stays_empty_no_crash():
    result = analyse_article({"entities": []})
    assert result["entities"] == []


def make_analysed_article(sentiment, entities, keywords=None):
    return {
        "sentiment_score": sentiment,
        "entities": entities,
        "keywords": keywords or [],
    }


def test_combines_same_entity_across_multiple_articles():
    articles = [
        make_analysed_article(-0.5, [{"text": "Jeremy Piven", "label": "PERSON", "count": 2.0}]),
        make_analysed_article(-0.3, [{"text": "Jeremy Piven", "label": "PERSON", "count": 1.0}]),
    ]
    result = summarise_metrics(articles)

    piven = result["entities"]["Jeremy Piven"]
    assert piven["mention_count"] == 3.0
    assert piven["article_count"] == 2


def test_average_sentiment_is_correct():
    articles = [
        make_analysed_article(-0.6, [{"text": "X", "label": "PERSON", "count": 1.0}]),
        make_analysed_article(-0.2, [{"text": "X", "label": "PERSON", "count": 1.0}]),
    ]
    result = summarise_metrics(articles)

    assert result["entities"]["X"]["avg_sentiment"] == -0.4


def test_top_keywords_ordered_by_frequency():
    articles = [
        make_analysed_article(0.1, [], keywords=["Film", "Drama"]),
        make_analysed_article(0.1, [], keywords=["Film"]),
    ]
    result = summarise_metrics(articles)

    assert result["top_keywords"][0] == ("Film", 2)


def test_empty_article_list_returns_empty_results():
    result = summarise_metrics([])

    assert result["entities"] == {}
    assert result["top_keywords"] == []


def make_stats(mention_count, avg_sentiment):
    return {"label": "PERSON", "mention_count": mention_count, "avg_sentiment": avg_sentiment}


def test_flags_strong_positive_above_threshold():
    stats = {"Star": make_stats(6, 0.75)}
    result = check_condition(stats, min_mentions=5, sentiment_threshold=0.7, direction="above")
    assert len(result) == 1
    assert result[0]["name"] == "Star"


def test_excludes_positive_below_sentiment_threshold():
    stats = {"Star": make_stats(6, 0.5)}
    result = check_condition(stats, min_mentions=5, sentiment_threshold=0.7, direction="above")
    assert result == []


def test_excludes_entity_below_min_mentions():
    stats = {"Star": make_stats(2, 0.9)}
    result = check_condition(stats, min_mentions=5, sentiment_threshold=0.7, direction="above")
    assert result == []


def test_flags_strong_negative_with_below_direction():
    stats = {"Figure": make_stats(6, -0.6)}
    result = check_condition(stats, min_mentions=5, sentiment_threshold=-0.5, direction="below")
    assert len(result) == 1