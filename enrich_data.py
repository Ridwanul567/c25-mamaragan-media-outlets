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
    """Extract and return the text content from the given HTML string."""
    soup = BeautifulSoup(html_content, "html.parser")
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
                     "he", "she", "they", "so"}
    for noun in nouns:
        noun = noun.strip().lower()
        if len(noun) > 1:
            if noun not in invalid_nouns:
                if not noun_counts.get(noun):
                    noun_counts[noun] = 1
                else:
                    noun_counts[noun] += 1
    noun_counts = {noun: count for noun,
                   count in noun_counts.items() if count > 2}
    return noun_counts


if __name__ == "__main__":
    articles = load_articles()
    links = articles["link"]
    url = links.iloc[0]
    html_content = get_html_content(url)
    text_content = extract_text_from_html(html_content)
    nouns = find_nouns(text_content)
    noun_counts = clean_nouns(nouns)
    print(noun_counts)

    blob = TextBlob(text_content)
    print(blob.sentiment)


def spacy_keywords(text_content: str):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text_content)

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
