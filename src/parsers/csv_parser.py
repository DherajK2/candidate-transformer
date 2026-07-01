"""
CSV Parser implementation.
Parses candidate records from structured CSV files.
"""

from datetime import datetime
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any, Optional

from src.models import (
    CandidateProfile, Location, Links, SkillEntry,
    ExperienceEntry, EducationEntry, ProvenanceEntry
)
from src.parsers.base import BaseParser
from src.utils.logger import get_logger

logger = get_logger("parsers.csv")


class CSVParser(BaseParser):
    """Parses candidate profiles from structured CSV inputs."""

    def parse(self, file_path: Path) -> CandidateProfile:
        """
        Parses the first candidate entry found in the CSV.
        Maps common column variations to canonical representation.
        """
        logger.info(f"Parsing CSV file: {file_path}")
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found at: {file_path}")

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            logger.error(f"Failed to read CSV file: {str(e)}")
            raise ValueError(f"Malformed or corrupt CSV file: {str(e)}")

        if df.empty:
            raise ValueError("CSV file is empty")

        # Get first row as a dictionary
        row = df.iloc[0].to_dict()
        # Normalize keys for fuzzy match (strip spaces, lowercase, remove underscores)
        normalized_row = {
            str(k).strip().lower().replace("_", "").replace(" ", ""): v
            for k, v in row.items()
        }

        # Fuzzy header matching helper
        def get_value(*aliases: str) -> Optional[Any]:
            for alias in aliases:
                norm_alias = alias.lower().replace("_", "").replace(" ", "")
                if norm_alias in normalized_row:
                    val = normalized_row[norm_alias]
                    # Handle pandas NaN
                    if pd.isna(val):
                        return None
                    return val
            return None

        # Extract name
        name = get_value("full_name", "fullname", "name", "candidate_name") or ""
        name = str(name).strip() if name else ""

        # Extract contact
        email = get_value("email", "email_address", "emails")
        emails = [str(email).strip()] if email else []

        phone = get_value("phone", "phone_number", "phones", "contact")
        phones = [str(phone).strip()] if phone else []

        # Extract location
        loc_str = get_value("location", "city", "address")
        city, region, country = None, None, None
        if loc_str:
            parts = [p.strip() for p in str(loc_str).split(",")]
            if len(parts) == 3:
                city, region, country = parts[0], parts[1], parts[2]
            elif len(parts) == 2:
                city, country = parts[0], parts[1]
            else:
                city = parts[0]

        # Override country/region if explicitly in columns
        country_val = get_value("country", "nation")
        if country_val:
            country = str(country_val).strip()
        region_val = get_value("region", "state")
        if region_val:
            region = str(region_val).strip()

        location = Location(city=city, region=region, country=country)

        # Extract links
        linkedin = get_value("linkedin", "linkedin_url", "linkedin_profile")
        github = get_value("github", "github_url", "github_profile")
        portfolio = get_value("portfolio", "website", "portfolio_url")
        other_links = []
        other_val = get_value("other_links", "links", "urls")
        if other_val:
            other_links = [str(x).strip() for x in str(other_val).split(",") if x.strip()]
        
        links = Links(
            linkedin=str(linkedin).strip() if linkedin else None,
            github=str(github).strip() if github else None,
            portfolio=str(portfolio).strip() if portfolio else None,
            other=other_links
        )

        headline = get_value("headline", "title", "designation", "role")
        headline = str(headline).strip() if headline else None

        years_exp = get_value("years_experience", "yearsofexperience", "experience_years", "exp")
        try:
            years_experience = float(years_exp) if years_exp is not None else None
        except ValueError:
            years_experience = None

        # Extract skills
        skills_val = get_value("skills", "technologies", "keywords")
        skills = []
        if skills_val:
            raw_skills = [s.strip() for s in str(skills_val).split(",") if s.strip()]
            for r_skill in raw_skills:
                skills.append(SkillEntry(name=r_skill, confidence=0.85, sources=[file_path.name]))

        # Experience entries
        experience = []
        company = get_value("company", "current_company", "organization")
        title = get_value("job_title", "title", "current_title")
        exp_summary = get_value("experience_summary", "summary", "description")
        
        if company or title:
            experience.append(
                ExperienceEntry(
                    company=str(company or "Unknown").strip(),
                    title=str(title or "Unknown").strip(),
                    start=get_value("start_date", "start"),
                    end=get_value("end_date", "end", "enddate") or "Present",
                    summary=str(exp_summary).strip() if exp_summary else None
                )
            )

        # Education entries
        education = []
        institution = get_value("institution", "university", "college", "school")
        degree = get_value("degree", "education", "qualification")
        field_of_study = get_value("field_of_study", "major", "field")
        end_year = get_value("graduation_year", "end_year", "year")
        
        if institution:
            education.append(
                EducationEntry(
                    institution=str(institution).strip(),
                    degree=str(degree).strip() if degree else None,
                    field=str(field_of_study).strip() if field_of_study else None,
                    end_year=str(end_year).strip() if end_year else None
                )
            )

        # Generate local provenance
        timestamp = datetime.now().isoformat()
        provenance = []
        
        # Add entry per non-empty extracted field
        fields_parsed = [
            ("full_name", name), ("emails", emails), ("phones", phones),
            ("location", location.city or location.country), ("links", links.linkedin or links.github),
            ("headline", headline), ("years_experience", years_experience),
            ("skills", skills), ("experience", experience), ("education", education)
        ]
        for field_name, value in fields_parsed:
            if value:
                provenance.append(
                    ProvenanceEntry(
                        field=field_name,
                        source=file_path.name,
                        method="csv_parsing",
                        timestamp=timestamp,
                        confidence=0.85
                    )
                )

        return CandidateProfile(
            candidate_id=f"cand_csv_{hash(name + ''.join(emails)) & 0xffffffff:08x}",
            full_name=name,
            emails=emails,
            phones=phones,
            location=location,
            links=links,
            headline=headline,
            years_experience=years_experience,
            skills=skills,
            experience=experience,
            education=education,
            provenance=provenance,
            overall_confidence=0.85
        )
