"""Enrich article metadata with DOM text scraping, spaCy NER, and TextBlob sentiment."""

import logging
from bs4 import BeautifulSoup
from curl_cffi import requests
import spacy
from textblob import TextBlob

nlp = spacy.load("en_core_web_sm")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def get_html_content(url: str) -> str:
    """Fetch raw HTML bypassing Cloudflare 403 blocks on redirects."""
    response = requests.get(
        url,
        impersonate="chrome",
        headers=HEADERS,
        allow_redirects=True,
        timeout=10,
    )
    response.raise_for_status()
    return response.text


def extract_text_from_html(html_content: str) -> str:
    """Extract inner text from article DOM container."""
    soup = BeautifulSoup(html_content, "html.parser")
    article = soup.find("article")
    if article:
        return article.get_text(separator=" ", strip=True)
    return soup.get_text(separator=" ", strip=True)


def extract_entities(text: str) -> list[dict]:
    """Extract target entities (People, Organizations, Products) using spaCy."""
    doc = nlp(text)
    entities = [
        {"text": ent.text, "label": ent.label_}
        for ent in doc.ents
        if ent.label_ in ["PERSON", "ORG", "PRODUCT"]
    ]
    # Return top 5 unique entity names
    unique_entities = list({e["text"]: e for e in entities}.values())[:5]
    return unique_entities


def enrich_articles(articles: list[dict]) -> list[dict]:
    """Enrich raw article dictionaries in-memory."""
    for article in articles:
        try:
            html = get_html_content(article["link"])
            body_text = extract_text_from_html(html)
        except Exception as err:
            logging.warning(
                "Could not scrape full body for %s: %s", article["link"], err)
            body_text = f"{article['title']} {article['description']}"

        # spaCy Named Entity Recognition
        article["entities"] = extract_entities(body_text)

        # TextBlob Sentiment Analysis
        blob = TextBlob(body_text)
        article["sentiment_score"] = float(blob.sentiment.polarity)
        article["subjectivity_score"] = float(blob.sentiment.subjectivity)

    return articles


if __name__ == "__main__":
    from collect_data import get_all_articles

    print("1. Fetching live RSS feed items...")
    raw_articles = get_all_articles()

    if raw_articles:
        print(
            f"2. Testing enrichment on 1 live article from {raw_articles[0]['outlet']}...")
        sample_enriched = enrich_articles(raw_articles[:1])

        print("\n--- ENRICHMENT RESULT ---")
        print("Title:", sample_enriched[0]["title"])
        print("Link:", sample_enriched[0]["link"])
        print("Entities:", sample_enriched[0]["entities"])
        print("Sentiment Score:", sample_enriched[0]["sentiment_score"])
        print("Subjectivity Score:", sample_enriched[0]["subjectivity_score"])
    else:
        print("No articles retrieved from RSS feeds.")
