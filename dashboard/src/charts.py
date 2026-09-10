"""Chart building utilities for the media outlets dashboard."""

import altair as alt
import pandas as pd


def plot_sentiment_and_volume_timeline(
    df: pd.DataFrame,
    selected_entity: str | None = None,
    view_mode: str = "Both",
) -> alt.Chart:
    """Plot daily sentiment trend, article volume, or both layered together."""
    data = df.copy()

    if selected_entity:
        data = data[
            data["entities"].apply(
                lambda x: any(e.get("text") == selected_entity for e in x)
                if isinstance(x, list)
                else False
            )
        ]

    if data.empty:
        return alt.Chart(pd.DataFrame()).mark_text()

    # Daily aggregation
    daily_df = (
        data.groupby(data["published_date"].dt.date)
        .agg(
            avg_sentiment=("sentiment_score", "mean"),
            article_volume=("article_id", "count"),
        )
        .reset_index()
    )
    daily_df = daily_df.sort_values("published_date")
    daily_df["date_str"] = daily_df["published_date"].apply(
        lambda x: x.strftime("%d-%m"))

    date_domain = daily_df["date_str"].tolist()

    base = alt.Chart(daily_df).encode(
        x=alt.X("date_str:N",
                title="Date", scale=alt.Scale(domain=date_domain), axis=alt.Axis(labelAngle=0)))

    # 1. Volume Layer
    bars = base.mark_bar(
        opacity=0.4 if view_mode == "Both" else 0.85, color="#8e44ad", size=15
    ).encode(
        y=alt.Y("article_volume:Q", title="Article Volume"),
        tooltip=[
            "published_date",
            alt.Tooltip("article_volume:Q", title="Articles Published"),
        ],
    )

    # 2. Sentiment Layer
    line = base.mark_line(point=True, strokeWidth=3).encode(
        y=alt.Y(
            "avg_sentiment:Q",
            title="Average Sentiment Score",
            scale=alt.Scale(domain=[-1.0, 1.0]),
        ),
        color=alt.condition(
            alt.datum.avg_sentiment >= 0,
            alt.value("#2ecc71"),
            alt.value("#e74c3c"),
        ),
        tooltip=[
            "published_date:T",
            alt.Tooltip("avg_sentiment:Q",
                        title="Avg Sentiment", format=".2f"),
        ],
    )

    zero_line = (
        alt.Chart(pd.DataFrame({"y": [0]}))
        .mark_rule(color="gray", strokeDash=[4, 4])
        .encode(y="y")
    )
    sentiment_layer = line + zero_line

    if view_mode == "Volume Only":
        chart = bars
    elif view_mode == "Sentiment Only":
        chart = sentiment_layer
    else:  # "Both"
        chart = alt.layer(bars, sentiment_layer).resolve_scale(y="independent")

    return chart.properties(
        height=320,
        title=f"Coverage Trend: {selected_entity or 'All Entities'} ({view_mode})",
    )


def plot_outlet_volume_and_sentiment(
    df: pd.DataFrame, top_n: int = 7
) -> alt.Chart:
    """Plot article volume grouped by top media outlets and sentiment category."""
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_text()

    top_outlets = df["outlet"].value_counts().nlargest(top_n).index
    data = df[df["outlet"].isin(top_outlets)].copy()

    def categorize(score):
        if score < -0.1:
            return "Negative"
        if score > 0.1:
            return "Positive"
        return "Neutral"

    data["sentiment_category"] = data["sentiment_score"].apply(categorize)

    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            y=alt.Y("outlet:N", title="Media Outlet", sort="-x"),
            x=alt.X("count():Q", title="Article Count"),
            color=alt.Color(
                "sentiment_category:N",
                scale=alt.Scale(
                    domain=["Positive", "Neutral", "Negative"],
                    range=["#2ecc71", "#95a5a6", "#e74c3c"],
                ),
                title="Sentiment",
            ),
            tooltip=["outlet", "sentiment_category", "count()"],
        )
        .properties(height=300, title=f"Top {top_n} Outlets by Tone")
    )


def plot_entity_sentiment_ranking(
    df: pd.DataFrame, mode: str = "worst"
) -> alt.Chart:
    """Plot entities receiving either the lowest (worst) or highest (best) average sentiment score."""
    if df.empty or "entities" not in df.columns:
        return alt.Chart(pd.DataFrame()).mark_text()

    exploded = df.explode("entities").dropna(subset=["entities"])
    exploded["entity_name"] = exploded["entities"].apply(
        lambda e: e.get("text") if isinstance(e, dict) else None
    )

    # Calculate average sentiment per entity with at least 2 mentions
    entity_stats = (
        exploded.groupby("entity_name")
        .agg(
            avg_sentiment=("sentiment_score", "mean"),
            count=("article_id", "count"),
        )
        .query("count >= 2")
        .reset_index()
    )

    if entity_stats.empty:
        return alt.Chart(pd.DataFrame()).mark_text()

    # Sort based on toggle selection
    if mode == "best":
        entity_stats = entity_stats.sort_values(
            "avg_sentiment", ascending=False
        ).head(10)
        chart_title = "Top 10 Highest Sentiment Entities (PR Wins)"
        sort_order = "-x"  # Highest value at top of bar chart
    else:
        entity_stats = entity_stats.sort_values(
            "avg_sentiment", ascending=True
        ).head(10)
        chart_title = "Top 10 Lowest Sentiment Entities (PR Risks)"
        sort_order = "x"   # Lowest/most negative at top

    return (
        alt.Chart(entity_stats)
        .mark_bar()
        .encode(
            y=alt.Y("entity_name:N", title="Entity", sort=sort_order),
            x=alt.X(
                "avg_sentiment:Q",
                title="Avg Sentiment",
                scale=alt.Scale(domain=[-1.0, 1.0]),
            ),
            color=alt.condition(
                alt.datum.avg_sentiment >= 0,
                alt.value("#2ecc71"),  # Green for positive
                alt.value("#e74c3c"),  # Red for negative
            ),
            tooltip=[
                "entity_name",
                alt.Tooltip("avg_sentiment:Q", format=".2f",
                            title="Avg Sentiment"),
                alt.Tooltip("count:Q", title="Article Count"),
            ],
        )
        .properties(height=320, title=chart_title)
    )
