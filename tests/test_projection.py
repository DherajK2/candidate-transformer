"""
Unit tests for dynamic JSON output ProjectionLayer.
"""

import pytest
from src.models import CandidateProfile, Location, SkillEntry
from src.projection.projection_layer import ProjectionLayer


def test_projection_filtering_and_renaming():
    profile = CandidateProfile(
        candidate_id="cand_1",
        full_name="Alice Vance",
        emails=["alice@email.com", "alt@email.com"],
        phones=["+919999988888"],
        location=Location(city="Mumbai", country="IN"),
        skills=[
            SkillEntry(name="React", confidence=0.9, sources=["csv"]),
            SkillEntry(name="Python", confidence=0.8, sources=["csv"])
        ]
    )

    config = {
        "fields": [
            { "path": "name", "from": "full_name", "type": "string", "required": True },
            { "path": "primary_email", "from": "emails[0]", "type": "string" },
            { "path": "city", "from": "location.city", "type": "string" },
            { "path": "skills_list", "from": "skills[].name", "type": "string[]" }
        ],
        "include_confidence": False,
        "include_provenance": False,
        "on_missing": "null"
    }

    layer = ProjectionLayer()
    projected = layer.project(profile, config)

    assert projected["name"] == "Alice Vance"
    assert projected["primary_email"] == "alice@email.com"
    assert projected["city"] == "Mumbai"
    assert projected["skills_list"] == ["React", "Python"]
    
    # Check that confidence and provenance keys are excluded
    assert "overall_confidence" not in projected
    assert "provenance" not in projected
    assert "confidence" not in projected
