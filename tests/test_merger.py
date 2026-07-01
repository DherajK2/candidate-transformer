"""
Unit tests for MergeEngine and conflict resolution rules.
"""

import pytest
from src.models import CandidateProfile, Location, Links, ExperienceEntry, ProvenanceEntry
from src.merger.merge_engine import MergeEngine


def test_merge_conflict_resolution():
    # Profile 1 (CSV source) - Preferred for contact info
    p_csv = CandidateProfile(
        candidate_id="cand_1",
        full_name="John Doe",
        emails=["john.doe@email.com"],
        phones=["+919876543210"],
        location=Location(city="Hyderabad", country="IN"),
        headline="Software Engineer",
        years_experience=4.0,
        provenance=[
            ProvenanceEntry(
                field="full_name", source="recruiter.csv", method="csv_parsing", timestamp="2026-07-01", confidence=0.85
            )
        ]
    )

    # Profile 2 (Resume PDF source) - Preferred for experience descriptions, summary, and longest string fields
    p_resume = CandidateProfile(
        candidate_id="cand_1",
        full_name="John R. Doe",
        emails=["john.alternate@email.com"],
        phones=["+911111122222"],
        location=Location(city="Cyberabad", country="India"),
        headline="Senior Full Stack Engineer at Microsoft Corporation",
        years_experience=4.5,
        experience=[
            ExperienceEntry(
                company="Microsoft India",
                title="Software Engineer II",
                start="2022-06",
                end="Present",
                summary="Detailed summary of building core candidate search algorithms."
            )
        ],
        provenance=[
            ProvenanceEntry(
                field="full_name", source="resume_john_doe.pdf", method="pdf_extraction", timestamp="2026-07-01", confidence=0.65
            )
        ]
    )

    merger = MergeEngine()
    merged = merger.merge_profiles([p_csv, p_resume])

    # Contact info: recruiter.csv > resume_john_doe.pdf
    assert merged.full_name == "John Doe"
    # Emails should union
    assert "john.doe@email.com" in merged.emails
    assert "john.alternate@email.com" in merged.emails
    
    # Location: recruiter.csv values are preferred
    assert merged.location.city == "Hyderabad"
    
    # Headline: uses longest string
    assert merged.headline == "Senior Full Stack Engineer at Microsoft Corporation"
    
    # Experience: resume_john_doe.pdf values are preferred
    assert merged.years_experience == 4.5
    assert merged.experience[0].company == "Microsoft India"
    assert "Detailed summary" in merged.experience[0].summary
