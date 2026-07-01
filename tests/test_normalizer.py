"""
Unit tests for data normalization helpers in normalizer.py.
"""

import pytest
from src.normalizer.normalizer import (
    normalize_phone, normalize_skill, normalize_country,
    normalize_url, normalize_dates, remove_duplicates
)


def test_normalize_phone():
    assert normalize_phone("9876543210") == "+919876543210"
    assert normalize_phone("+91-9876543210") == "+919876543210"
    assert normalize_phone("(+91)9876543210") == "+919876543210"
    assert normalize_phone("1234567890", default_prefix="+1") == "+11234567890"


def test_normalize_skill():
    assert normalize_skill("ReactJS") == "React"
    assert normalize_skill("React.js") == "React"
    assert normalize_skill("react") == "React"
    assert normalize_skill("nodejs") == "Node.js"
    assert normalize_skill("Python") == "Python"
    assert normalize_skill("SomeCustomSkill") == "SomeCustomSkill"


def test_normalize_country():
    assert normalize_country("India") == "IN"
    assert normalize_country("IND") == "IN"
    assert normalize_country("in") == "IN"
    assert normalize_country("United States") == "US"
    assert normalize_country("USA") == "US"
    assert normalize_country("CA") == "CA"
    assert normalize_country("UnknownCountry") == "UnknownCountry"


def test_normalize_url():
    assert normalize_url("linkedin.com/in/johndoe/") == "https://www.linkedin.com/in/johndoe"
    assert normalize_url("https://www.linkedin.com/in/johndoe") == "https://www.linkedin.com/in/johndoe"
    assert normalize_url("github.com/johndoe") == "https://github.com/johndoe"
    assert normalize_url("http://github.com/johndoe/") == "https://github.com/johndoe"
    assert normalize_url("myportfolio.com") == "https://myportfolio.com"


def test_normalize_dates():
    assert normalize_dates("Jan 2024") == "2024-01"
    assert normalize_dates("01/2024") == "2024-01"
    assert normalize_dates("2024") == "2024-01"
    assert normalize_dates("2024-05-12") == "2024-05"
    assert normalize_dates("Present") == "Present"


def test_remove_duplicates():
    assert remove_duplicates([1, 2, 2, 3, 1, 4]) == [1, 2, 3, 4]
    assert remove_duplicates(["a", "b", "a"]) == ["a", "b"]
