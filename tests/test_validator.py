"""
Unit tests for schema validation in validator.py.
"""

import pytest
import jsonschema
from src.validator.validator import JSONValidator


def test_validate_canonical_profile():
    validator = JSONValidator()

    # Valid profile data structure
    valid_data = {
        "candidate_id": "cand_1",
        "full_name": "John Doe",
        "emails": ["john.doe@email.com"],
        "phones": ["+919876543210"],
        "location": {
            "city": "Hyderabad",
            "region": "Telangana",
            "country": "IN"
        },
        "links": {
            "linkedin": "https://linkedin.com/in/johndoe",
            "github": "https://github.com/johndoe",
            "portfolio": None,
            "other": []
        },
        "headline": "SDE at Microsoft",
        "years_experience": 4.5,
        "skills": [
            { "name": "React", "confidence": 0.95, "sources": ["csv"] }
        ],
        "experience": [
            { "company": "Microsoft", "title": "SDE II", "start": "2022-06", "end": "Present", "summary": "Dev" }
        ],
        "education": [
            { "institution": "IIT H", "degree": "B.Tech", "field": "CS", "end_year": "2022" }
        ],
        "provenance": [
            { "field": "full_name", "source": "csv", "method": "parse", "timestamp": "2026-07-01", "confidence": 0.85 }
        ],
        "overall_confidence": 0.9
    }

    # Should run without error
    validator.validate_canonical_profile(valid_data)

    # Invalid profile: missing required field full_name
    invalid_data = valid_data.copy()
    del invalid_data["full_name"]

    with pytest.raises(jsonschema.ValidationError):
        validator.validate_canonical_profile(invalid_data)

    # Invalid profile: country code format not 2 letters
    invalid_country = valid_data.copy()
    invalid_country["location"] = {
        "city": "Hyderabad",
        "region": "Telangana",
        "country": "IND"  # Schema requires 2 chars
    }

    with pytest.raises(jsonschema.ValidationError):
        validator.validate_canonical_profile(invalid_country)
