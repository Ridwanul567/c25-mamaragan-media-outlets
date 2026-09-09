"""File for fetching full article text and performing NLP enrichment (OpenAI API)."""

import logging
import random
import time
from bs4 import BeautifulSoup
from curl_cffi import requests
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()


class Entity(BaseModel):
    text: str
    label: str
    count: int


class ArticleAnalysis(BaseModel):
    entities: list[Entity]
    keywords: list[str]
    sentiment_score: float
    subjectivity_score: float


def get_html_content(url: str, session: requests.Session) -> str:
    """Fetch raw HTML with curl_cffi imitating browser behavior."""
    response = session.get(
        url,
        allow_redirects=True,
        timeout=(5, 10),
    )
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        raise ValueError(
            f"URL did not return HTML content (Content-Type: {content_type})"
        )

    return response.text


def extract_text_from_html(html: str) -> str:
    """Parse HTML and extract cleaned paragraph body text."""
    soup = BeautifulSoup(html, "html.parser")

    # Strip non-visible elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    article_tag = soup.find("article")
    target_node = article_tag if article_tag else soup.find("body")

    if not target_node:
        return ""

    paragraphs = [
        p.get_text(separator=" ", strip=True) for p in target_node.find_all("p")
    ]
    return " ".join(paragraphs)


def analyse_text_with_openai(text: str) -> dict:
    """Send text to LLM service using the official OpenAI SDK."""

    # Automatically checks OPENAI_API_KEY (or LUNA_API_KEY fallback)
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LUNA_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("LUNA_BASE_URL")

    # If base_url is None, the SDK defaults to https://api.openai.com/v1
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    prompt = f"""
    Analyze the following article text:
    1. Extract named entities (PERSON, ORG, GPE, LOC, NORP, PRODUCT).
    2. Normalize name variations (e.g., combine 'Trump', 'Donald Trump', and 'President Trump' into 'Donald Trump') and sum total mention counts.
    3. Extract 3-5 high-level topic keywords/keyphrases summarizing the core subject.
    4. Compute sentiment_score (-1.0 to 1.0) and subjectivity_score (0.0 to 1.0).

    Text:
    {text[:4000]}
    """

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a precise data enrichment assistant.",
            },
            {"role": "user", "content": prompt},
        ],
        response_format=ArticleAnalysis,
    )

    return response.choices[0].message.parsed.model_dump()


def enrich_articles(articles: list[dict]) -> list[dict]:
    """Iterate through articles, fetch full text, and run OpenAI enrichment."""
    with requests.Session(impersonate="chrome124") as session:
        try:
            session.get("https://news.sky.com", timeout=5)
            time.sleep(1.0)
        except Exception as err:
            logging.debug("Sky News session warmup ping failed: %s", err)

        # Iterate and enrich articles
        for article in articles:
            body_text = ""
            link = article.get("link") or article.get("article_id")

            try:
                # Randomise pauses between requests
                time.sleep(random.uniform(1.0, 2.0))

                html = get_html_content(link, session=session)
                body_text = extract_text_from_html(html)
            except Exception as err:
                logging.warning(
                    "Scrape failed for %s (%s). Using fallback.", link, err
                )

            # Fallback to title + description if DOM body extraction fails or is too short
            analysis_text = (
                body_text
                if len(body_text) > 100
                else f"{article.get('title', '')} {article.get('description', '')}"
            )

            # OpenAI Analysis (Entities, Keywords, Sentiment)
            try:
                analysis = analyse_text_with_openai(analysis_text)
                article.update(analysis)
            except Exception as err:
                logging.error(
                    "OpenAI enrichment failed for %s: %s", link, err
                )
                article["entities"] = []
                article["keywords"] = []
                article["sentiment_score"] = 0.0
                article["subjectivity_score"] = 0.0

    return articles


if __name__ == "__main__":
    sample_article = [{
        "article_id": "https://www.bbc.co.uk/news/articles/c4gd4z8p4y0o",
        "link": "https://www.bbc.co.uk/news/articles/c4gd4z8p4y0o",
        "title": "Donald Trump speaks at campaign event",
        "description": "Trump spoke alongside President Donald Trump's advisors today.",
        "outlet": "BBC News",
    }]

    print("\n--- Testing Live LLM Enrichment ---")
    results = enrich_articles(sample_article)

    import json
    print(json.dumps(results, indent=2))
