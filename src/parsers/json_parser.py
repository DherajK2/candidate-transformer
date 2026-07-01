"""
JSON Parser implementation.
Parses candidate records from semi-structured JSON inputs.
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.models import (
    CandidateProfile, Location, Links, SkillEntry,
    ExperienceEntry, EducationEntry, ProvenanceEntry
)
from src.parsers.base import BaseParser
from src.utils.logger import get_logger

logger = get_logger("parsers.json")


class JSONParser(BaseParser):
    """Parses candidate profiles from structured/semi-structured JSON files."""

    def parse(self, file_path: Path) -> CandidateProfile:
        """
        Parses JSON content, flattening structure to a canonical candidate profile.
        """
        logger.info(f"Parsing JSON file: {file_path}")
        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found at: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON content: {str(e)}")
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            logger.error(f"Error reading JSON file: {str(e)}")
            raise ValueError(f"Failed to read JSON: {str(e)}")

        if not data:
            raise ValueError("JSON file is empty")

        # Handle candidate data wrapper if exists
        profile_data = data.get("candidate", data) if isinstance(data, dict) else data
        if not isinstance(profile_data, dict):
            raise ValueError("Expected candidate JSON to represent an object")

        # Fuzzy helper matching
        def lookup(dict_data: Dict[str, Any], *keys: str) -> Optional[Any]:
            for key in keys:
                # Direct check
                if key in dict_data:
                    return dict_data[key]
                # Lowercase variations
                for k, v in dict_data.items():
                    if k.lower().replace("_", "").replace(" ", "") == key.lower().replace("_", "").replace(" ", ""):
                        return v
            return None

        # Extract identification
        name = lookup(profile_data, "full_name", "fullname", "name", "candidate_name") or ""
        name = str(name).strip()

        # Contact info
        emails = []
        email_val = lookup(profile_data, "email", "emails", "email_address")
        if isinstance(email_val, list):
            emails = [str(e).strip() for e in email_val if e]
        elif email_val:
            emails = [str(email_val).strip()]

        phones = []
        phone_val = lookup(profile_data, "phone", "phones", "phone_number")
        if isinstance(phone_val, list):
            phones = [str(p).strip() for p in phone_val if p]
        elif phone_val:
            phones = [str(phone_val).strip()]

        # Location details
        loc_data = lookup(profile_data, "location", "address") or {}
        city, region, country = None, None, None
        if isinstance(loc_data, dict):
            city = lookup(loc_data, "city", "town")
            region = lookup(loc_data, "region", "state", "province")
            country = lookup(loc_data, "country", "nation", "code")
        elif isinstance(loc_data, str):
            parts = [p.strip() for p in loc_data.split(",")]
            if len(parts) == 3:
                city, region, country = parts[0], parts[1], parts[2]
            elif len(parts) == 2:
                city, country = parts[0], parts[1]
            else:
                city = parts[0]

        location = Location(
            city=str(city).strip() if city else None,
            region=str(region).strip() if region else None,
            country=str(country).strip() if country else None
        )

        # Links
        links_data = lookup(profile_data, "links", "urls", "profiles") or {}
        linkedin, github, portfolio = None, None, None
        other_links = []
        if isinstance(links_data, dict):
            linkedin = lookup(links_data, "linkedin", "linkedin_url")
            github = lookup(links_data, "github", "github_url")
            portfolio = lookup(links_data, "portfolio", "personal_website", "website")
            other_links = lookup(links_data, "other", "websites") or []
        elif isinstance(links_data, list):
            other_links = [str(x).strip() for x in links_data]

        links = Links(
            linkedin=str(linkedin).strip() if linkedin else None,
            github=str(github).strip() if github else None,
            portfolio=str(portfolio).strip() if portfolio else None,
            other=[str(o).strip() for o in other_links] if isinstance(other_links, list) else []
        )

        headline = lookup(profile_data, "headline", "title", "role", "summary")
        headline = str(headline).strip() if headline else None

        years_exp = lookup(profile_data, "years_experience", "experience_years", "total_experience")
        try:
            years_experience = float(years_exp) if years_exp is not None else None
        except ValueError:
            years_experience = None

        # Skills
        skills = []
        skills_val = lookup(profile_data, "skills", "technologies", "key_skills") or []
        if isinstance(skills_val, list):
            for s in skills_val:
                if isinstance(s, dict):
                    name_s = lookup(s, "name", "skill") or ""
                    conf_s = lookup(s, "confidence", "score") or 0.85
                    if name_s:
                        skills.append(SkillEntry(name=str(name_s).strip(), confidence=float(conf_s), sources=[file_path.name]))
                elif s:
                    skills.append(SkillEntry(name=str(s).strip(), confidence=0.85, sources=[file_path.name]))
        elif isinstance(skills_val, str):
            skills = [SkillEntry(name=s.strip(), confidence=0.85, sources=[file_path.name]) for s in skills_val.split(",") if s.strip()]

        # Experience entries
        experience = []
        exp_list = lookup(profile_data, "experience", "work_history", "history") or []
        if isinstance(exp_list, list):
            for e in exp_list:
                if isinstance(e, dict):
                    comp = lookup(e, "company", "employer") or "Unknown"
                    title_e = lookup(e, "title", "role", "job_title") or "Unknown"
                    start_e = lookup(e, "start", "start_date")
                    end_e = lookup(e, "end", "end_date") or "Present"
                    sum_e = lookup(e, "summary", "description")
                    experience.append(
                        ExperienceEntry(
                            company=str(comp).strip(),
                            title=str(title_e).strip(),
                            start=str(start_e).strip() if start_e else None,
                            end=str(end_e).strip() if end_e else None,
                            summary=str(sum_e).strip() if sum_e else None
                        )
                    )

        # Education entries
        education = []
        edu_list = lookup(profile_data, "education", "studies", "academic_history") or []
        if isinstance(edu_list, list):
            for ed in edu_list:
                if isinstance(ed, dict):
                    inst = lookup(ed, "institution", "school", "university") or "Unknown"
                    deg = lookup(ed, "degree", "qualification")
                    fld = lookup(ed, "field", "field_of_study", "major")
                    yr = lookup(ed, "end_year", "graduation_year", "year")
                    education.append(
                        EducationEntry(
                            institution=str(inst).strip(),
                            degree=str(deg).strip() if deg else None,
                            field=str(fld).strip() if fld else None,
                            end_year=str(yr).strip() if yr else None
                        )
                    )

        # Provenance tracing
        timestamp = datetime.now().isoformat()
        provenance = []
        for key_name in ["full_name", "emails", "phones", "location", "links", "headline", "years_experience", "skills", "experience", "education"]:
            val_found = lookup(profile_data, key_name)
            if val_found:
                provenance.append(
                    ProvenanceEntry(
                        field=key_name,
                        source=file_path.name,
                        method="json_parsing",
                        timestamp=timestamp,
                        confidence=0.85
                    )
                )

        return CandidateProfile(
            candidate_id=f"cand_json_{hash(name + ''.join(emails)) & 0xffffffff:08x}",
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
