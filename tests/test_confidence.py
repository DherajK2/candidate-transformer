"""
Unit tests for ConfidenceEngine scoring, boosts, and penalties.
"""

import pytest
from src.models import CandidateProfile, SkillEntry, ProvenanceEntry, Location
from src.confidence.confidence_engine import ConfidenceEngine


def test_confidence_calculations():
    # Setup raw profiles to simulate agreement
    raw1 = CandidateProfile(
        candidate_id="cand",
        full_name="John Doe",
        emails=["john.doe@email.com"],
        phones=["+919876543210"],
        location=Location(country="IN"),
        provenance=[
            ProvenanceEntry(field="full_name", source="recruiter.csv", method="csv", timestamp="123", confidence=0.85)
        ]
    )

    raw2 = CandidateProfile(
        candidate_id="cand",
        full_name="John Doe",  # Agreement on name!
        emails=["john.doe@email.com"], # Agreement on email!
        phones=["+919876543210"], # Agreement on phone!
        location=Location(country="IN"), # Agreement on country!
        provenance=[
            ProvenanceEntry(field="full_name", source="ats.json", method="json", timestamp="123", confidence=0.85)
        ]
    )

    # Merged profile with initial state
    merged = CandidateProfile(
        candidate_id="cand",
        full_name="John Doe",
        emails=["john.doe@email.com"],
        phones=["+919876543210"],
        location=Location(country="IN"),
        skills=[
            SkillEntry(name="React", confidence=0.85, sources=["recruiter.csv", "ats.json"]) # Agreement on skill!
        ],
        provenance=[
            ProvenanceEntry(field="full_name", source="recruiter.csv", method="csv", timestamp="123", confidence=0.85),
            ProvenanceEntry(field="phones", source="recruiter.csv", method="csv", timestamp="123", confidence=0.85)
        ]
    )

    engine = ConfidenceEngine()
    evaluated = engine.calculate_confidence(merged, [raw1, raw2])

    # Name has agreement: base (0.85) + boost (0.10) = 0.95
    name_prov = next(p for p in evaluated.provenance if p.field == "full_name")
    assert name_prov.confidence == 0.95

    # Skill has agreement (2 sources): base (0.85) + boost (0.10) = 0.95
    assert evaluated.skills[0].confidence == 0.95

    # Overall confidence should be high due to agreement
    assert evaluated.overall_confidence > 0.85
