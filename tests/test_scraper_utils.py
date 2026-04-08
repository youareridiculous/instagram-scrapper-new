"""Unit tests for pure scraper helpers (no Playwright)."""

import pytest

from instagram_scraper import SafeInstagramScraper, profile_matches_filters


@pytest.fixture
def scraper():
    return SafeInstagramScraper('u', 'p', headless=True)


def test_parse_count_k_m_plain(scraper):
    assert scraper._parse_count('1,234') == 1234
    assert scraper._parse_count('12.5K') == 12500
    assert scraper._parse_count('2M') == 2000000
    assert scraper._parse_count('') is None


def test_profile_matches_filters_followers():
    p = {'followers': 5000, 'following': 100, 'posts': 20, 'bio': 'founder', 'verified': False, 'account_type': 'personal'}
    f = {'min_followers': 1000, 'max_followers': 10000, 'bio_keywords': ['founder']}
    assert profile_matches_filters(p, f) is True
    assert profile_matches_filters({**p, 'followers': 500}, f) is False


def test_profile_matches_filters_bio_keywords():
    p = {'followers': 100, 'bio': 'CEO and founder'}
    f = {'bio_keywords': ['ceo']}
    assert profile_matches_filters(p, f) is True
    f2 = {'bio_keywords': ['missing']}
    assert profile_matches_filters(p, f2) is False
