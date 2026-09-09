"""Test suite for enrich_data.py functions."""
import re
import pytest
from unittest.mock import MagicMock, patch
from enrich_data import (get_html_content, extract_text_from_html, find_nouns,
                         clean_nouns, sort_nouns_by_length, group_nouns, collate_nouns)

SAMPLE_URL = 'https://random.co.uk/random'


# def test_get_html_content_client_error(requests_mock):
#     requests_mock.get(SAMPLE_URL,
#                       status_code=400)
#     with pytest.raises(Exception) as exception:
#         get_html_content(SAMPLE_URL)

#     assert requests_mock.called
#     assert requests_mock.call_count == 1
#     assert requests_mock.last_request.method == "GET"

#     assert exception.value.args[0][0:3] == "400"


# def test_get_html_content_server_error(requests_mock):
#     requests_mock.get(SAMPLE_URL,
#                       status_code=500)
#     with pytest.raises(Exception) as exception:
#         get_html_content(SAMPLE_URL)

#     assert requests_mock.called
#     assert requests_mock.call_count == 1
#     assert requests_mock.last_request.method == "GET"

#     assert exception.value.args[0][0:3] == "500"


def test_extract_text_from_html_standard():
    html_content = """
    <html><head><title>Sample Page</title></head><body><p>This is a <b>sample</b> paragraph.</p>
    <p>Another paragraph with <a href="#">a link</a>.</p></body></html>
    """
    html_content = html_content.replace('\n', '')
    html_content = html_content.strip()
    expected_text = "Sample PageThis is a sample paragraph. Another paragraph with a link."
    text = extract_text_from_html(html_content)
    assert text == expected_text


def test_extract_text_from_html_with_article_tag():
    html_content = """
    <html><head><title>Sample Page</title></head><body><p>This is a <b>sample</b> paragraph.</p>
    <article><p>Another paragraph with <a href="#">a link</a>.</p></article></body></html>
    """
    html_content = html_content.replace('\n', '')
    html_content = html_content.strip()
    expected_text = "Another paragraph with a link."
    text = extract_text_from_html(html_content)
    assert text == expected_text


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


def test_clean_nouns_empty_list():
    nouns = []
    expected_cleaned_nouns = {}
    cleaned_nouns = clean_nouns(nouns)
    assert cleaned_nouns == expected_cleaned_nouns


def test_clean_nouns_single_letter():
    nouns = ["New York", "I", "a"]
    expected_cleaned_nouns = {"new york": 1}
    cleaned_nouns = clean_nouns(nouns)
    assert cleaned_nouns == expected_cleaned_nouns


def test_clean_nouns_extra_space():
    nouns = ["  New York  "]
    expected_cleaned_nouns = {"new york": 1}
    cleaned_nouns = clean_nouns(nouns)
    assert cleaned_nouns == expected_cleaned_nouns


def test_clean_nouns_multiple_capitalizations():
    nouns = ["New York", "new york", "New York"]
    expected_cleaned_nouns = {"new york": 3}
    cleaned_nouns = clean_nouns(nouns)
    assert cleaned_nouns == expected_cleaned_nouns


def test_clean_nouns_invalid_nouns():
    nouns = ["the", "an", "and", "New York", "Silver Town"]
    expected_cleaned_nouns = {"new york": 1, "silver town": 1}
    cleaned_nouns = clean_nouns(nouns)
    assert cleaned_nouns == expected_cleaned_nouns


def test_clean_nouns_apostrophe_s():
    nouns = ["Liam's", "Liam"]
    expected_cleaned_nouns = {"liam": 2}
    cleaned_nouns = clean_nouns(nouns)
    assert cleaned_nouns == expected_cleaned_nouns


def test_sort_nouns_by_length():
    noun_counts = {"new york": 2, "new york city": 1, "city": 5}
    expected_sorted_nouns = {"new york city": 1, "new york": 2, "city": 5}
    sorted_nouns = sort_nouns_by_length(noun_counts)
    assert sorted_nouns == expected_sorted_nouns


def test_group_nouns_simple():
    noun_counts = {"new york": 2, "new york city": 1, "city": 5}
    expected_grouped_nouns = {"new york city": [
        "new york", "city"], "new york": [], "city": []}
    grouped_nouns = group_nouns(noun_counts)
    assert grouped_nouns == expected_grouped_nouns


def test_group_nouns_complex():
    noun_counts = {"liam": 2, "liam's": 1, "liam gallagher": 5, "gallagher": 1}
    expected_grouped_nouns = {"liam gallagher": [
        "gallagher", "liam"], "gallagher": [], "liam's": ["liam"], "liam": []}
    grouped_nouns = group_nouns(noun_counts)
    assert grouped_nouns == expected_grouped_nouns


def test_collate_nouns_city():
    noun_counts = {"new york": 2, "new york city": 1}
    expected_collated_nouns = {"new york city": 3}
    grouped_nouns = group_nouns(noun_counts)
    collated_nouns = collate_nouns(noun_counts, grouped_nouns)
    assert collated_nouns == expected_collated_nouns


def test_collate_nouns_person():
    noun_counts = {"liam": 4, "liam's": 1, "liam gallagher": 2, "gallagher": 1}
    expected_collated_nouns = {"liam's": 1, "liam gallagher": 7}
    grouped_nouns = group_nouns(noun_counts)
    collated_nouns = collate_nouns(noun_counts, grouped_nouns)
    assert collated_nouns == expected_collated_nouns


@patch("enrich_data.requests.get")
def test_get_html_content_returns_html(mock_get):
    mock_response = MagicMock()
    mock_response.text = "<html><body>sample</body></html>"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    html_content = get_html_content(SAMPLE_URL)

    assert "<html" in html_content.lower()
    mock_get.assert_called_once()
