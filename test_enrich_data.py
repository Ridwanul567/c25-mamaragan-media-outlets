"""Test suite for enrich_data.py functions."""
import re
import pytest
from enrich_data import find_nouns


def test_find_nouns_simple():
    text = "Sir Paul Smith went to New York City."
    expected_nouns = ["Sir Paul Smith", "New York City"]
    nouns = find_nouns(text)
    assert nouns == expected_nouns


def test_find_nouns_complex():
    text = """Sir Paul O'Smith went to New York 
    where he had lunch next to St Alley's Shopping Mall. 
    His best friend John-Doe Deer also came along. The Record Breaking Event occurred."""
    expected_nouns = ["Sir Paul O'Smith", "New York",
                      "St Alley's Shopping Mall", "His", "John-Doe Deer", "The Record Breaking Event"]
    nouns = find_nouns(text)
    assert nouns == expected_nouns
