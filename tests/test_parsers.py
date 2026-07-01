"""
Unit tests for structured and unstructured source parsers.
"""

import json
from pathlib import Path
import pytest

from src.parsers.csv_parser import CSVParser
from src.parsers.json_parser import JSONParser
from src.parsers.text_parser import TextParser
from src.parsers.pdf_parser import PDFParser


@pytest.fixture
def temp_dir(tmp_path) -> Path:
    return tmp_path


def test_csv_parser(temp_dir):
    csv_file = temp_dir / "recruiter.csv"
    csv_file.write_text(
        "full_name,email,phone,current_company,title,location,skills,years_experience,linkedin,github\n"
        "John Doe,john.doe@email.com,9876543210,Microsoft,Software Engineer,\"Hyderabad, India\",\"ReactJS, Python\",4,linkedin.com/in/johndoe,github.com/johndoe\n"
    )
    
    parser = CSVParser()
    profile = parser.parse(csv_file)
    
    assert profile.full_name == "John Doe"
    assert "john.doe@email.com" in profile.emails
    assert "9876543210" in profile.phones
    assert profile.location.city == "Hyderabad"
    assert profile.location.country == "India"
    assert len(profile.skills) == 2
    assert profile.skills[0].name == "ReactJS"
    assert profile.experience[0].company == "Microsoft"


def test_json_parser(temp_dir):
    json_file = temp_dir / "ats_profile.json"
    data = {
        "candidate": {
            "name": "Jane Doe",
            "emails": ["jane.doe@email.com"],
            "phones": ["+1-123-456-7890"],
            "location": {
                "city": "Seattle",
                "region": "WA",
                "country": "US"
            },
            "skills": ["Python", "Docker"],
            "experience": [
                {
                    "company": "Amazon",
                    "title": "SDE II",
                    "start": "2020-01",
                    "end": "Present",
                    "summary": "Cloud software engineering."
                }
            ]
        }
    }
    json_file.write_text(json.dumps(data))

    parser = JSONParser()
    profile = parser.parse(json_file)

    assert profile.full_name == "Jane Doe"
    assert "jane.doe@email.com" in profile.emails
    assert "+1-123-456-7890" in profile.phones
    assert profile.location.city == "Seattle"
    assert len(profile.skills) == 2
    assert profile.experience[0].company == "Amazon"


def test_text_parser():
    resume_text = """
    Alice Vance
    alice@email.com | +91 99999 88888 | Mumbai, India
    linkedin.com/in/alicevance

    Summary:
    Developer with 3 years experience.

    Experience:
    TCS - Software Engineer (06/2021 - Present)
    Maintained java API services.

    Education:
    IIT Bombay - B.Tech (2021)

    Skills:
    Java, Python, React, SQL
    """
    
    parser = TextParser()
    profile = parser.parse_text(resume_text, "resume.txt")
    
    assert profile.full_name == "Alice Vance"
    assert "alice@email.com" in profile.emails
    assert "+91 99999 88888" in profile.phones
    assert "Java" in [s.name for s in profile.skills]
    assert "React" in [s.name for s in profile.skills]
    assert profile.experience[0].company == "TCS"
    assert profile.education[0].institution == "IIT Bombay"
