"""Unit tests for Altair chart generator functions in the media dashboard."""

import altair as alt
import pandas as pd
import pytest
from charts import (
    plot_entity_sentiment_ranking,
    plot_outlet_volume_and_sentiment,
    plot_sentiment_and_volume_timeline,
)


@pytest.fixture
def sample_media_df() -> pd.DataFrame:
    """Provide a mock DataFrame matching the enriched media dataset schema."""
    return pd.DataFrame(
        [
            {
                "article_id": "1",
                "published_date": pd.to_datetime("2026-09-08 10:00:00", utc=True),
                "outlet": "BBC News",
                "sentiment_score": 0.6,
                "entities": [{"text": "Apple", "label": "ORG"}],
            },
            {
                "article_id": "2",
                "published_date": pd.to_datetime("2026-09-09 11:00:00", utc=True),
                "outlet": "BBC News",
                "sentiment_score": -0.8,
                "entities": [
                    {"text": "Apple", "label": "ORG"},
                    {"text": "Tim Cook", "label": "PERSON"},
                ],
            },
            {
                "article_id": "3",
                "published_date": pd.to_datetime("2026-09-09 14:00:00", utc=True),
                "outlet": "The Guardian",
                "sentiment_score": -0.5,
                "entities": [{"text": "Tim Cook", "label": "PERSON"}],
            },
        ]
    )


def test_plot_sentiment_and_volume_timeline_modes(sample_media_df):
    """Test timeline chart generation across all view modes and with entity filter."""
    # Test 'Both' mode (LayerChart)
    chart_both = plot_sentiment_and_volume_timeline(
        sample_media_df, selected_entity="Apple", view_mode="Both"
    )
    assert isinstance(chart_both, (alt.Chart, alt.LayerChart))

    # Test 'Sentiment Only' mode
    chart_sentiment = plot_sentiment_and_volume_timeline(
        sample_media_df, view_mode="Sentiment Only"
    )
    assert isinstance(chart_sentiment, (alt.Chart, alt.LayerChart))

    # Test 'Volume Only' mode
    chart_volume = plot_sentiment_and_volume_timeline(
        sample_media_df, view_mode="Volume Only"
    )
    assert isinstance(chart_volume, alt.Chart)


def test_plot_outlet_volume_and_sentiment(sample_media_df):
    """Test outlet volume bar chart generation with top_n limit."""
    chart = plot_outlet_volume_and_sentiment(sample_media_df, top_n=5)
    assert isinstance(chart, alt.Chart)


def test_plot_entity_sentiment_ranking_perspective(sample_media_df):
    """Test entity leaderboard sorting for both 'worst' (risks) and 'best' (wins) modes."""
    # Test worst (risks) mode
    chart_worst = plot_entity_sentiment_ranking(sample_media_df, mode="worst")
    assert isinstance(chart_worst, alt.Chart)

    # Test best (wins) mode
    chart_best = plot_entity_sentiment_ranking(sample_media_df, mode="best")
    assert isinstance(chart_best, alt.Chart)


def test_charts_empty_dataframe_guards():
    """Verify that all chart functions gracefully handle empty DataFrames without throwing errors."""
    empty_df = pd.DataFrame()

    chart_timeline = plot_sentiment_and_volume_timeline(empty_df)
    chart_outlet = plot_outlet_volume_and_sentiment(empty_df)
    chart_ranking = plot_entity_sentiment_ranking(empty_df)

    assert isinstance(chart_timeline, alt.Chart)
    assert isinstance(chart_outlet, alt.Chart)
    assert isinstance(chart_ranking, alt.Chart)
