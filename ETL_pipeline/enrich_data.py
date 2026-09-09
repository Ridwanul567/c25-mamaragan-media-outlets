"""File for fetching full article text and performing NLP enrichment (NER and Sentiment)."""

import logging
import random
import time
from bs4 import BeautifulSoup
from curl_cffi import requests
import spacy
from textblob import TextBlob

nlp = spacy.load("en_core_web_sm")


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
            f"URL did not return HTML content (Content-Type: {content_type})")

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

    paragraphs = [p.get_text(separator=" ", strip=True)
                  for p in target_node.find_all("p")]
    return " ".join(paragraphs)


def extract_entities(text: str) -> list[dict]:
    """Extract Named Entities using spaCy."""
    if not text or not text.strip():
        return []

    doc = nlp(text)
    entities = []
    seen = set()

    for ent in doc.ents:
        # Filter out numbers/dates to focus on core subjects and organizations
        if ent.label_ in ["PERSON", "ORG", "GPE", "LOC", "NORP", "PRODUCT"]:
            clean_text = ent.text.strip()
            entity_key = (clean_text.lower(), ent.label_)

            if len(clean_text) > 1 and entity_key not in seen:
                seen.add(entity_key)
                entities.append({
                    "text": clean_text,
                    "label": ent.label_
                })

    return entities


def enrich_articles(articles: list[dict]) -> list[dict]:
    """Iterate through articles, fetch full text, and run NER + sentiment analysis."""
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
                    "Scrape failed for %s (%s). Using fallback.", link, err)

            # Fallback to title + description if DOM body extraction fails or is too short
            analysis_text = (
                body_text
                if len(body_text) > 100
                else f"{article.get('title', '')} {article.get('description', '')}"
            )

            # Named Entity Recognition
            try:
                article["entities"] = extract_entities(analysis_text)
            except Exception as err:
                logging.error("NER parsing failed for %s: %s", link, err)
                article["entities"] = []

            # Sentiment Evaluation
            try:
                blob = TextBlob(analysis_text)
                article["sentiment_score"] = float(blob.sentiment.polarity)
                article["subjectivity_score"] = float(
                    blob.sentiment.subjectivity)
            except Exception as err:
                logging.error(
                    "Sentiment calculation failed for %s: %s", link, err)
                article["sentiment_score"] = 0.0
                article["subjectivity_score"] = 0.0

    return articles
