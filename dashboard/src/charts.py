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
    """Generates a horizontal bar chart ranking entities by sentiment score."""
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_text()

    working_df = df.copy()
    working_df["sentiment_score"] = pd.to_numeric(
        working_df["sentiment_score"], errors="coerce"
    )

    exploded = working_df.explode("entities").dropna(subset=["entities"])
    exploded["entity_name"] = exploded["entities"].apply(
        lambda x: x.get("text") if isinstance(x, dict) else str(x)
    )

    entity_stats = (
        exploded.groupby("entity_name")
        .agg(
            avg_sentiment=("sentiment_score", "mean"),
            article_count=("article_id", "count"),
        )
        .reset_index()
    )

    entity_stats["avg_sentiment"] = pd.to_numeric(
        entity_stats["avg_sentiment"], errors="coerce"
    )
    # Filter out low-volume noise
    entity_stats = entity_stats[entity_stats["article_count"] >= 2]

    if entity_stats.empty:
        return alt.Chart(pd.DataFrame()).mark_text()

    # Filter data based on selected view mode
    if mode == "both":
        top_best = entity_stats.nlargest(10, "avg_sentiment")
        top_worst = entity_stats.nsmallest(10, "avg_sentiment")
        chart_data = (
            pd.concat([top_best, top_worst])
            .drop_duplicates(subset=["entity_name"])
            .sort_values(by="avg_sentiment", ascending=False)
        )
        title_text = "Top Entities by Sentiment (Wins & Risks)"
    elif mode == "best":
        chart_data = entity_stats.nlargest(10, "avg_sentiment").sort_values(
            by="avg_sentiment", ascending=False
        )
        title_text = "Top 10 Highest Sentiment Entities (Wins)"
    else:  # mode == "worst"
        chart_data = entity_stats.nsmallest(10, "avg_sentiment").sort_values(
            by="avg_sentiment", ascending=True
        )
        title_text = "Top 10 Lowest Sentiment Entities (Risks)"

    # Unified chart definition with distinct bar borders and fixed row height
    chart = (
        alt.Chart(chart_data)
        .mark_bar(
            stroke="#0e1117",
            strokeWidth=2,
            height=20,  # Fixed individual bar height
        )
        .encode(
            x=alt.X(
                "avg_sentiment:Q",
                title="Average Sentiment Score",
                scale=alt.Scale(domain=[-1.0, 1.0]),
            ),
            y=alt.Y(
                "entity_name:N",
                sort="-x",
                title="Entity",
                axis=alt.Axis(labelLimit=250),
            ),
            color=alt.Color(
                "avg_sentiment:Q",
                scale=alt.Scale(
                    domain=[-0.8, 0, 0.8], scheme="redyellowgreen"
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("entity_name:N", title="Entity"),
                alt.Tooltip("avg_sentiment:Q", format=".2f",
                            title="Avg Sentiment"),
                alt.Tooltip("article_count:Q", title="Articles"),
            ],
        )
        .properties(
            title=title_text,
            # Ensures fixed 26px vertical space per row regardless of dataset length
            height=alt.Step(26),
        )
    )

    return chart


def plot_entity_keyword_frequency(
    df: pd.DataFrame, target_entity: str, top_n: int = 15
) -> alt.Chart:
    """Generates a bar chart of the most frequent keywords for a selected entity."""
    if df.empty or not target_entity:
        return alt.Chart(pd.DataFrame()).mark_text()

    # Filter for articles containing the selected entity
    entity_articles = df[
        df["entities"].apply(
            lambda x: any(
                (e.get("text") == target_entity if isinstance(
                    e, dict) else e == target_entity)
                for e in x
            )
            if isinstance(x, list)
            else False
        )
    ]

    if entity_articles.empty or "keywords" not in entity_articles.columns:
        return alt.Chart(pd.DataFrame()).mark_text()

    # Flatten the keywords column
    exploded_kw = entity_articles.explode(
        "keywords").dropna(subset=["keywords"])

    # Clean keyword strings
    exploded_kw["clean_keyword"] = exploded_kw["keywords"].apply(
        lambda x: x.get("text", "").strip().lower() if isinstance(
            x, dict) else str(x).strip().lower()
    )

    # Filter out empty or extremely short keywords
    exploded_kw = exploded_kw[exploded_kw["clean_keyword"].str.len() > 2]

    # Aggregate total occurrences
    kw_counts = (
        exploded_kw.groupby("clean_keyword")
        .size()
        .reset_index(name="count")
        .nlargest(top_n, "count")
    )

    if kw_counts.empty:
        return alt.Chart(pd.DataFrame()).mark_text()

    # Build horizontal bar chart
    chart = (
        alt.Chart(kw_counts)
        .mark_bar(color="#4F46E5")
        .encode(
            x=alt.X("count:Q", title="Total Keyword Mentions"),
            y=alt.Y("clean_keyword:N", sort="-x", title="Keyword / Topic"),
            tooltip=["clean_keyword", alt.Tooltip(
                "count:Q", title="Mentions")],
        )
        .properties(
            title=f"Top Associated Keywords for '{target_entity}'",
            height=350,
        )
    )

    return chart
