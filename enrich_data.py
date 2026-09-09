"""Python script for enriching article data with keywords and sentiment analysis."""

import re
import pandas as pd
from bs4 import BeautifulSoup
from textblob import TextBlob
from curl_cffi import requests


def load_articles() -> pd.DataFrame:
    """Load articles from the CSV file and return as a DataFrame."""
    return pd.read_csv("articles.csv")


def get_html_content(url: str) -> str:
    """Fetch and return the HTML content of the given URL."""
    params = {"random": "try"}
    response = requests.get(url, impersonate="chrome",
                            params=params, timeout=5)
    response.raise_for_status()
    return response.text


def extract_text_from_html(html_content: str) -> str:
    """Extract and return the text content from the article HTML tags."""
    soup = BeautifulSoup(html_content, "html.parser")
    article = soup.find("article")
    if article:
        return article.get_text()
    return soup.get_text()


def find_nouns(text: str) -> list:
    """Find and return all noun phrases in the given text."""
    regex_pattern = r'\b[A-Z][a-z]*(?:\'[A-Z][a-z]*|\'s)*(?:[ \n-][A-Z][a-z]*(?:\'[A-Z][a-z]*|\'s)*)*'
    return re.findall(regex_pattern, text)


def clean_nouns(nouns: list) -> list:
    """Clean the list of nouns, filtering out invalid nouns."""
    noun_counts = {}
    invalid_nouns = {"the", "an", "and", "or", "but", "we",
                     "is", "are", "was", "were", "has", "have",
                     "had", "it", "i'm", "my", "me", "my sounds",
                     "he", "she", "they", "so", "this", "in",
                     "getty images", "your", "image"}
    for noun in nouns:
        noun = noun.strip().lower()
        if len(noun) > 1:
            if noun not in invalid_nouns:
                if noun[-2:] == "'s":
                    noun = noun[:-2]
                if not noun_counts.get(noun):
                    noun_counts[noun] = 1
                else:
                    noun_counts[noun] += 1
    return noun_counts


def sort_nouns_by_length(noun_counts: dict) -> dict:
    """Sort nouns by their length in descending order."""
    return dict(sorted(noun_counts.items(), key=lambda item: len(item[0]), reverse=True))


def group_nouns(noun_counts: dict) -> dict:
    """Collate nouns of similar form."""
    sorted_nouns = sort_nouns_by_length(noun_counts)
    noun_groups = {}
    for noun in list(sorted_nouns.keys()):
        noun_groups[noun] = []
        for other_noun in list(sorted_nouns.keys()):
            if noun != other_noun and other_noun in noun:
                noun_groups[noun].append(other_noun)

    return noun_groups


def collate_nouns(noun_counts: dict, grouped_nouns: dict) -> dict:
    """Collate nouns based on their grouped forms."""
    for noun, group in grouped_nouns.items():
        if noun not in noun_counts:
            continue
        for other_noun in group:
            if other_noun in noun_counts:
                noun_counts[noun] += noun_counts.pop(other_noun)
    return noun_counts


def find_keywords(noun_counts: dict, top_n: int = 3) -> list:
    """Return the top N most popular nouns based on their counts."""
    sorted_nouns = sorted(noun_counts.items(),
                          key=lambda item: item[1], reverse=True)
    return [noun for noun, count in sorted_nouns[:top_n]]


def get_article_sentiment(text: str) -> tuple:
    """Return the polarity and subjectivity of the given article."""
    blob = TextBlob(text)
    return blob.sentiment.polarity, blob.sentiment.subjectivity


def load_keywords(url: str) -> list:
    """Load and return the top keywords from the article at the given URL."""
    try:
        html_content = get_html_content(url)
        text = extract_text_from_html(html_content)
    except Exception as e:
        print(f"Error loading HTML content from {url}: {e}")
        return None
    nouns = find_nouns(text)
    noun_counts = clean_nouns(nouns)
    grouped_nouns = group_nouns(noun_counts)
    collated_nouns = collate_nouns(noun_counts, grouped_nouns)
    keywords = find_keywords(collated_nouns)
    return keywords


def create_article_keywords(articles: pd.DataFrame) -> pd.DataFrame:
    """Add a 'keywords' column to the articles DataFrame based on the article links."""
    articles['keywords'] = articles['link'].apply(load_keywords)
    return articles


def load_sentiment(url: str) -> tuple:
    """Load and return the sentiment (polarity, subjectivity) of the article at the given URL."""
    try:
        html_content = get_html_content(url)
        text = extract_text_from_html(html_content)
    except Exception as e:
        print(f"Error loading HTML content from {url}: {e}")
        return (None, None)
    sentiment = get_article_sentiment(text)
    return sentiment


def create_article_sentiment(articles: pd.DataFrame) -> pd.DataFrame:
    """Add 'polarity' and 'subjectivity' columns to the articles DataFrame based on the article links."""
    sentiment = articles['link'].apply(load_sentiment)
    articles['polarity'] = sentiment.apply(lambda x: x[0])
    articles['subjectivity'] = sentiment.apply(lambda x: x[1])
    return articles


if __name__ == "__main__":
    articles = load_articles()
    articles = create_article_keywords(articles)
    articles = create_article_sentiment(articles)
    articles.to_csv('enriched_articles.csv', index=False)
