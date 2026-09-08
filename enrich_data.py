import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from textblob import TextBlob
import spacy


def load_articles() -> pd.DataFrame:
    """Load articles from the CSV file and return as a DataFrame."""
    return pd.read_csv("articles.csv")


def get_html_content(url: str) -> str:
    """Fetch and return the HTML content of the given URL."""
    response = requests.get(url, timeout=5)
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
                     "had", "it", "I'm", "my", "me", "my sounds",
                     "he", "she", "they", "so", "this", "in"}
    for noun in nouns:
        noun = noun.strip().lower()
        if len(noun) > 1:
            if noun not in invalid_nouns:
                if not noun_counts.get(noun):
                    noun_counts[noun] = 1
                else:
                    noun_counts[noun] += 1
    noun_counts = {noun: count for noun,
                   count in noun_counts.items() if count > 1}
    return noun_counts


def collate_nouns(noun_counts: dict) -> dict:
    """Collate nouns of similar form."""
    for noun in list(noun_counts.keys()):
        for other_noun in list(noun_counts.keys()):
            if noun != other_noun and noun in other_noun:
                noun_counts[other_noun] += noun_counts.pop(noun)
    return noun_counts


def find_keywords(noun_counts: dict, top_n: int = 3) -> list:
    """Return the top N most popular nouns based on their counts."""
    sorted_nouns = sorted(noun_counts.items(),
                          key=lambda item: item[1], reverse=True)
    return [noun for noun, count in sorted_nouns[:top_n]]


def identify_keywords(text: str):
    nlp = spacy.load("en_core_web_sm")

    doc = nlp(text)

    companies = set()
    people = set()
    actions = set()

    # Extract specific entities (Organizations and People)
    for ent in doc.ents:
        if ent.label_ == "ORG":  # Companies / Organizations
            companies.add(ent.text)
        elif ent.label_ == "PERSON":  # People
            people.add(ent.text)

    # Extract main actions (using verbs that drive the sentences)
    for token in doc:
        if token.pos_ == "VERB" and not token.is_stop:
            # Get the base form of the verb (lemma) to clean up duplicates
            actions.add(token.lemma_.lower())

    print("--- 📊 ARTICLE ANALYSIS REPORT ---")
    print("\n🏢 Main Companies/Organizations Identified:")
    print(", ".join(companies) if companies else "None found")

    print("\n👤 Main People Identified:")
    print(", ".join(people) if people else "None found")

    print("\n🎬 Key Actions occurring (Top Verbs):")
    # Display the first 10 unique actions found
    print(", ".join(list(actions)[:10]) if actions else "None found")


def get_article_sentiment(text: str):
    blob = TextBlob(text)
    return blob.sentiment.polarity, blob.sentiment.subjectivity


if __name__ == "__main__":
    articles = load_articles()
    links = articles["link"]
    url = links.iloc[3]
    print(url)
    html_content = get_html_content(url)
    text_content = extract_text_from_html(html_content)
    nouns = find_nouns(text_content)
    noun_counts = clean_nouns(nouns)
    print(noun_counts)
    noun_counts = collate_nouns(noun_counts)
    keywords = find_keywords(noun_counts)
    print(keywords)
    # identify_keywords(text_content)

    polarity, subjectivity = get_article_sentiment(text_content)
    print(f"Polarity: {polarity}")
    print(f"Subjectivity: {subjectivity}")


# If link does not work. need to try except .. not raise
# Nouns should be collated to larger noun groups e.g. Liam -> Liam Callaghan but not Oasis -> Oasis'
# General collate_nouns needs work - easy to fail
