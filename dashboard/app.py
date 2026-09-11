"""Main entrypoint for the Media Outlets Streamlit Dashboard."""

import os
import pandas as pd
import streamlit as st
from src.charts import (
    plot_entity_sentiment_ranking,
    plot_outlet_volume_and_sentiment,
    plot_sentiment_and_volume_timeline,
    plot_entity_keyword_frequency,
)
from src.data import load_data
from dotenv import load_dotenv

load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="Otranto Development Media Coverage Intelligence",
    page_icon="📰",
    layout="wide",
)

# Password Protection


def check_password() -> bool:
    """Returns True if the user is authenticated, otherwise renders password input."""
    if st.session_state.get("authenticated", False):
        return True

    # Render input box
    password_input = st.text_input(
        "Password", type="password", key="password_field")

    # Evaluate when the user types something and submits
    if password_input:
        if password_input == os.environ.get("DASHBOARD_PASSWORD", "media2026"):
            st.session_state["authenticated"] = True
            st.rerun()  # Refresh immediately to load the dashboard
        else:
            st.error("Incorrect password")

    return False


if not check_password():
    st.stop()


# Data Loading
df = load_data()

# Global Sidebar Controls
st.sidebar.title("🕹️ Global Filters")

# Multi-Select Entity Filter
if not df.empty and "entities" in df.columns:
    raw_entities = set()
    for entities_list in df["entities"]:
        if isinstance(entities_list, list):
            for entity in entities_list:
                if isinstance(entity, dict):
                    text = entity.get("text", "").strip()
                    label = entity.get("label", "")
                    if (
                        text
                        and not text.isdigit()
                        and label != "DATE"
                        and len(text) > 2
                    ):
                        raw_entities.add(text)
    all_entities = sorted(list(raw_entities))
else:
    all_entities = []

# Multi-select
selected_entities = st.sidebar.multiselect(
    "Filter by Entities / Clients:",
    options=all_entities,
    default=[],  # Empty by default means show all entities
    help="Select one or multiple entities to narrow down coverage across all charts.",
)

# Outlet Filter
if not df.empty and "outlet" in df.columns:
    all_outlets = sorted(df["outlet"].dropna().unique().tolist())
else:
    all_outlets = []

selected_outlet = st.sidebar.selectbox(
    "Filter by Media Outlet:",
    options=["All Outlets"] + all_outlets,
    help="Type to search and filter dashboard data for a single news publisher.",
)

# Neutral Sentiment Checkbox
show_neutral_articles = st.sidebar.checkbox(
    "Include Neutral Sentiment",
    value=True,
    help="Uncheck to hide neutral coverage (-0.1 to 0.1 sentiment) across all charts.",
)

# Apply Global Filters to DataFrame
filtered_df = df.copy()

# Multi-select entity matching logic
if selected_entities and not filtered_df.empty:
    filtered_df = filtered_df[
        filtered_df["entities"].apply(
            lambda x: any(e.get("text") in selected_entities for e in x)
            if isinstance(x, list)
            else False
        )
    ]

if selected_outlet != "All Outlets" and not filtered_df.empty:
    filtered_df = filtered_df[filtered_df["outlet"] == selected_outlet]

if not show_neutral_articles and not filtered_df.empty:
    filtered_df = filtered_df[
        (filtered_df["sentiment_score"] < -0.1)
        | (filtered_df["sentiment_score"] > 0.1)
    ]


# Visualisations Page
def render_visualisations_page():
    st.title("📈 Media Coverage & Sentiment Intelligence")
    st.markdown(
        "Real-time public relations tracking, coverage trends, and sentiment risk analysis."
    )

    if filtered_df.empty:
        st.warning("No media data matches the active filters.")
        return

    # Chart 1
    st.subheader("1. Sentiment & Coverage Volume Trend")

    with st.expander("💡 How to read this chart & drive PR decisions", expanded=False):
        st.write(
            "**Purpose:** *Understand the media's opinion about your client and whether coverage is turning negative.*\n\n"
            "* **Line Graph (Daily Sentiment):** Shows average sentiment on a scale from **-1.0 (Very Negative)** to **+1.0 (Very Positive)**. Any dip below **0** signals negative coverage.\n"
            "* **Bar Chart (Article Volume):** Shows how many total articles were published each day. Use bars to distinguish a **lone crank** (1 bad article) from a **coverage crisis** (40 bad articles)."
        )

    # Chart Controls
    ctrl_col1, _ = st.columns([2, 2])
    with ctrl_col1:
        chart_view_mode = st.radio(
            "Display Mode:",
            options=["Both", "Sentiment Only", "Volume Only"],
            horizontal=True,
            key="timeline_view_mode",
        )

    # Pass primary selected entity or None if multiple/none are picked
    primary_entity = selected_entities[0] if len(
        selected_entities) == 1 else None

    trend_chart = plot_sentiment_and_volume_timeline(
        filtered_df,
        selected_entity=primary_entity,
        view_mode=chart_view_mode,
    )
    st.altair_chart(trend_chart, use_container_width=True)

    st.divider()

    # Chart 2
    st.subheader("2. Outlet Tone Breakdown")

    with st.expander("💡 How to read outlet tone", expanded=False):
        st.write(
            "**Purpose:** *Identify which media outlets are driving negative coverage.*\n\n"
            "* Identifies top media outlets and breaks down their stories into Positive, Neutral, or Negative sentiment.\n"
            "* **PR Action:** Target outreach toward outlets with high volume and red (negative) bars."
        )

    ctrl_col2, _ = st.columns([2, 2])
    with ctrl_col2:
        outlet_limit = st.slider(
            "Number of Top Outlets",
            min_value=2,
            max_value=15,
            value=7,
            key="outlet_limit_slider",
        )

    outlet_chart = plot_outlet_volume_and_sentiment(
        filtered_df, top_n=outlet_limit
    )
    st.altair_chart(outlet_chart, use_container_width=True)

    st.divider()

    # Chart 3
    st.subheader("3. Entity Sentiment Leaderboard")

    with st.expander("💡 How to read entity rankings", expanded=False):
        st.write(
            "**Purpose:** *Identify who or what entity is receiving the most extreme coverage.*\n\n"
            "* **Lowest Sentiment (Risks):** Highlights topics suffering from negative sentiment requiring press response.\n"
            "* **Highest Sentiment (Wins):** Highlights success stories and positive brand associations.\n"
            "* **Both (Stacked):** Displays top wins directly stacked above top risks for a side-by-side comparative view."
        )

    # Localised toggle for Best vs Worst vs Both
    ctrl_col3, _ = st.columns([2, 2])
    with ctrl_col3:
        leaderboard_mode = st.radio(
            "Chart Rankings:",
            options=[
                "Lowest Sentiment (Risks)", "Highest Sentiment (Wins)", "Both (Stacked)"],
            horizontal=True,
            key="leaderboard_mode_toggle",
        )

    # Mode key mapping
    if "Both" in leaderboard_mode:
        mode_key = "both"
    elif "Highest" in leaderboard_mode:
        mode_key = "best"
    else:
        mode_key = "worst"

    ranking_chart = plot_entity_sentiment_ranking(filtered_df, mode=mode_key)
    st.altair_chart(ranking_chart, use_container_width=True)

    st.divider()

    # Chart 4: Entity Keyword Profiler
    st.subheader("4. Entity Keyword & Topic Deep-Dive")

    with st.expander("💡 How to use the Entity Keyword Profiler", expanded=False):
        st.write(
            "**Purpose:** *Discover the specific themes, topics, and buzzwords associated with a client or entity.*\n\n"
            "* Select an entity from the dropdown to audit every keyword extracted across its media coverage.\n"
            "* Use metric cards to instantly see total volume and overall sentiment for that specific entity."
        )

    # Single entity selector for deep-dive profiling
    profiler_col1, profiler_col2 = st.columns([2, 1])

    with profiler_col1:
        profile_entity = st.selectbox(
            "Select Entity to Profile:",
            options=all_entities,
            index=0 if all_entities else None,
            key="entity_profiler_select",
        )

    if profile_entity:
        # Isolate articles mentioning this entity
        entity_df = df[
            df["entities"].apply(
                lambda x: any(
                    (e.get("text") == profile_entity if isinstance(
                        e, dict) else e == profile_entity)
                    for e in x
                )
                if isinstance(x, list)
                else False
            )
        ]

        if not entity_df.empty:
            # Display Key Metrics summary cards for the entity
            total_articles = len(entity_df)
            avg_sentiment = entity_df["sentiment_score"].mean()

            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("Total Articles Mentioned", total_articles)
            m_col2.metric("Avg Sentiment Score", f"{avg_sentiment:.2f}")

            # Count total unique keywords extracted for this entity
            all_kw = entity_df.explode("keywords")["keywords"].dropna()
            m_col3.metric("Unique Keywords Found", len(all_kw.unique()))

            # Render keyword frequency chart
            kw_chart = plot_entity_keyword_frequency(
                df, target_entity=profile_entity, top_n=12)
            st.altair_chart(kw_chart, use_container_width=True)
        else:
            st.info(f"No articles found referencing '{profile_entity}'.")


# Raw Data Page
def render_raw_data_page():
    st.title("📄 Raw Data & Export Explorer")
    st.markdown(
        "Audit individual article payloads, run keyword searches, and download CSV exports."
    )

    if filtered_df.empty:
        st.warning("No article data available to display.")
        return

    st.info(
        "💡 **Tip:** Use the search bar below to query article titles, descriptions, or entity tags. Click headers to sort table rows."
    )

    search_query = st.text_input(
        "🔍 Keyword Search:", placeholder="e.g. Trump, BBC, technology..."
    )

    display_df = filtered_df.copy()

    # Convert entity dictionary payloads to formatted strings
    if "entities" in display_df.columns:
        display_df["entities"] = display_df["entities"].apply(
            lambda x: [
                f"{e.get('text', '')} ({e.get('label', '')})"
                if isinstance(e, dict)
                else str(e)
                for e in x
            ]
            if isinstance(x, list)
            else []
        )

    # Search filter across text columns and flattened entities
    if search_query:
        query = search_query.lower()
        display_df = display_df[
            display_df["title"].astype(str).str.lower().str.contains(query)
            | display_df["description"]
            .astype(str)
            .str.lower()
            .str.contains(query)
            | display_df["entities"].apply(
                lambda x: any(query in str(item).lower() for item in x)
            )
        ]

    # CSV Export Button
    csv_data = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered CSV",
        data=csv_data,
        file_name="media_articles_export.csv",
        mime="text/csv",
    )

    st.caption(
        f"Displaying **{len(display_df)}** of **{len(filtered_df)}** articles"
    )

    # Interactive table rendering with list badges
    st.dataframe(
        display_df,
        column_config={
            "entities": st.column_config.ListColumn("Entities", width="large"),
            "keywords": st.column_config.ListColumn(
                "Keywords", width="medium"
            ),
            "link": st.column_config.LinkColumn("Full Link"),
            "sentiment_score": st.column_config.NumberColumn(
                "Sentiment", format="%.2f"
            ),
            "subjectivity_score": st.column_config.NumberColumn(
                "Subjectivity", format="%.2f"
            ),
            "published_date": st.column_config.DatetimeColumn(
                "Published (BST)", format="D MMM YYYY, HH:mm"
            ),
        },
        use_container_width=True,
        hide_index=True,
        height=550,
    )


# Page Routing
pages = [
    st.Page(render_visualisations_page, title="Visualisations", icon="📊"),
    st.Page(render_raw_data_page, title="Raw Data Explorer", icon="📄"),
]

pg = st.navigation(pages)
pg.run()
