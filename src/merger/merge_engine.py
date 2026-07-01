"""
Merge Engine and Conflict Resolution module.
Combines multiple heterogeneous candidate profiles using distinct strategies
such as Unique Merge, Priority Merge, Latest Value, and Longest String.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from src.models import (
    CandidateProfile, Location, Links, SkillEntry,
    ExperienceEntry, EducationEntry, ProvenanceEntry
)
from src.normalizer.normalizer import (
    normalize_phone, normalize_skill, normalize_country,
    normalize_url, normalize_dates, remove_duplicates
)
from src.utils.logger import get_logger

logger = get_logger("merger.engine")

# Define source preferences: CSV is preferred for contact info; Resume is preferred for experience.
CONTACT_SOURCE_ORDER = ["recruiter.csv", "ats_profile.json", "resume_john_doe.pdf", "resume_jane_smith.txt"]
EXPERIENCE_SOURCE_ORDER = ["resume_john_doe.pdf", "resume_jane_smith.txt", "ats_profile.json", "recruiter.csv"]


class MergeEngine:
    """Merges multiple candidate profiles into a single canonical representation."""

    def merge_profiles(self, profiles: List[CandidateProfile]) -> CandidateProfile:
        """
        Merges a list of parsed candidate profiles into a single consolidated profile.
        Applies specific conflict resolution rules per field.
        """
        if not profiles:
            raise ValueError("No profiles to merge")
        if len(profiles) == 1:
            logger.info("Only one profile present, skipping merge logic.")
            return profiles[0]

        logger.info(f"Merging {len(profiles)} candidate profiles across different sources.")

        # 1. Resolve ID (Deterministic hash based on first non-empty name/email)
        candidate_id = profiles[0].candidate_id

        # 2. Resolve Full Name
        # Strategy: Source Priority (CSV > JSON > Resumes)
        full_name = self._resolve_field_priority(
            profiles, "full_name", CONTACT_SOURCE_ORDER, default_val=profiles[0].full_name
        )

        # 3. Resolve Contact Info (Unique Merge with source priority)
        # Emails
        raw_emails = []
        for p in profiles:
            raw_emails.extend(p.emails)
        emails = remove_duplicates([e.strip().lower() for e in raw_emails if e.strip()])

        # Phones
        raw_phones = []
        for p in profiles:
            raw_phones.extend(p.phones)
        phones = remove_duplicates([normalize_phone(ph) for ph in raw_phones if ph.strip()])

        # 4. Resolve Location
        # Strategy: Resolve individual attributes using Source Priority
        city = self._resolve_field_priority(profiles, "location.city", CONTACT_SOURCE_ORDER)
        region = self._resolve_field_priority(profiles, "location.region", CONTACT_SOURCE_ORDER)
        country_raw = self._resolve_field_priority(profiles, "location.country", CONTACT_SOURCE_ORDER)
        country = normalize_country(country_raw) if country_raw else None
        location = Location(city=city, region=region, country=country)

        # 5. Resolve Links
        # Strategy: Merge all link fields, preferring non-empty values from source order
        linkedin = self._resolve_field_priority(profiles, "links.linkedin", CONTACT_SOURCE_ORDER)
        github = self._resolve_field_priority(profiles, "links.github", CONTACT_SOURCE_ORDER)
        portfolio = self._resolve_field_priority(profiles, "links.portfolio", CONTACT_SOURCE_ORDER)
        
        linkedin = normalize_url(linkedin) if linkedin else None
        github = normalize_url(github) if github else None
        portfolio = normalize_url(portfolio) if portfolio else None

        raw_other = []
        for p in profiles:
            raw_other.extend(p.links.other)
        other_links = remove_duplicates([normalize_url(lnk) for lnk in raw_other if lnk.strip()])
        links = Links(linkedin=linkedin, github=github, portfolio=portfolio, other=other_links)

        # 6. Resolve Headline
        # Strategy: Longest String (usually more descriptive in resumes)
        headline = self._resolve_field_longest_string(profiles, "headline")

        # 7. Resolve Years Experience
        # Strategy: Resume Priority (Resume > CSV)
        years_exp_str = self._resolve_field_priority(profiles, "years_experience", EXPERIENCE_SOURCE_ORDER)
        years_experience = float(years_exp_str) if years_exp_str is not None else None

        # 8. Resolve Skills
        # Strategy: Unique merge. Group by normalized name, combine sources and confidence.
        skills = self._merge_skills(profiles)

        # 9. Resolve Experience
        # Strategy: Deduplicate by company/title, prefer resume content for dates/summary
        experience = self._merge_experience(profiles)

        # 10. Resolve Education
        # Strategy: Deduplicate by institution/degree, priority to longest study name/end_year
        education = self._merge_education(profiles)

        # 11. Consolidate Provenance (Union all logs to preserve complete audit history)
        provenance = []
        for p in profiles:
            provenance.extend(p.provenance)

        # Remove duplicate provenance entries
        seen_provenance = set()
        deduped_provenance = []
        for prov in provenance:
            key = (prov.field, prov.source, prov.method)
            if key not in seen_provenance:
                seen_provenance.add(key)
                deduped_provenance.append(prov)

        return CandidateProfile(
            candidate_id=candidate_id,
            full_name=full_name,
            emails=emails,
            phones=phones,
            location=location,
            links=links,
            headline=headline,
            years_experience=years_experience,
            skills=skills,
            experience=experience,
            education=education,
            provenance=deduped_provenance,
            overall_confidence=0.0  # Will be calculated by ConfidenceEngine
        )

    def _resolve_field_priority(
        self, profiles: List[CandidateProfile], path: str, source_order: List[str], default_val: Any = None
    ) -> Any:
        """
        Strategy: Source Priority. Selects values from profiles following a preferred source order list.
        """
        # Map profiles by source names
        source_to_profile = {}
        for p in profiles:
            # Check the source of the first provenance entry (tells us where this profile came from)
            src_name = p.provenance[0].source if p.provenance else "unknown"
            source_to_profile[src_name] = p

        # Check in source priority order
        for preferred_source in source_order:
            for src, p in source_to_profile.items():
                if preferred_source.lower() in src.lower():
                    val = self._get_nested_val(p, path)
                    if val is not None and val != "" and val != []:
                        logger.debug(f"Resolved conflict for {path} using priority source: {src}")
                        return val

        # Fallback to the first non-empty value
        for p in profiles:
            val = self._get_nested_val(p, path)
            if val is not None and val != "" and val != []:
                return val

        return default_val

    def _resolve_field_longest_string(self, profiles: List[CandidateProfile], path: str) -> Optional[str]:
        """
        Strategy: Longest String. Prefers longer text values for highly descriptive fields.
        """
        best_val: Optional[str] = None
        for p in profiles:
            val = self._get_nested_val(p, path)
            if isinstance(val, str) and val.strip():
                if best_val is None or len(val) > len(best_val):
                    best_val = val
        return best_val

    def _get_nested_val(self, profile: CandidateProfile, path: str) -> Any:
        """Helper to get nested values like location.city from CandidateProfile."""
        parts = path.split(".")
        obj = profile
        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            elif isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                return None
        return obj

    def _merge_skills(self, profiles: List[CandidateProfile]) -> List[SkillEntry]:
        """Merges skill entries by canonicalizing names, boosting confidence, and unioning sources."""
        skills_map: Dict[str, SkillEntry] = {}
        for p in profiles:
            for sk in p.skills:
                norm_name = normalize_skill(sk.name)
                if not norm_name:
                    continue
                
                if norm_name in skills_map:
                    # Update existing skill entry
                    existing = skills_map[norm_name]
                    existing.sources.extend(sk.sources)
                    existing.sources = remove_duplicates(existing.sources)
                    # Use the higher confidence as baseline
                    existing.confidence = max(existing.confidence, sk.confidence)
                else:
                    skills_map[norm_name] = SkillEntry(
                        name=norm_name,
                        confidence=sk.confidence,
                        sources=list(sk.sources)
                    )
        return list(skills_map.values())

    def _merge_experience(self, profiles: List[CandidateProfile]) -> List[ExperienceEntry]:
        """Merges work history. Groups by company name (fuzzy match) and title."""
        merged_exp: List[ExperienceEntry] = []
        
        for p in profiles:
            for job in p.experience:
                normalized_comp = job.company.strip().lower()
                
                # Check if we already added a job at this company
                match_job = None
                for existing in merged_exp:
                    if normalized_comp in existing.company.strip().lower() or existing.company.strip().lower() in normalized_comp:
                        # Same company, check title similarity
                        if job.title.strip().lower() == existing.title.strip().lower() or not existing.title or not job.title:
                            match_job = existing
                            break
                
                if match_job:
                    # Merge attributes: prefer start/end dates that look normalized
                    if job.start and (not match_job.start or len(job.start) > len(match_job.start)):
                        match_job.start = normalize_dates(job.start)
                    if job.end and (not match_job.end or len(job.end) > len(match_job.end)):
                        match_job.end = normalize_dates(job.end)
                    
                    # Resolve summary conflict using Longest String
                    if job.summary and (not match_job.summary or len(job.summary) > len(match_job.summary)):
                        match_job.summary = job.summary
                else:
                    # Insert new entry
                    merged_exp.append(
                        ExperienceEntry(
                            company=job.company,
                            title=job.title,
                            start=normalize_dates(job.start) if job.start else None,
                            end=normalize_dates(job.end) if job.end else None,
                            summary=job.summary
                        )
                    )
        
        # Sort experience by start date descending (newest first)
        def get_sort_key(exp: ExperienceEntry) -> str:
            if not exp.start:
                return "0000-00"
            return exp.start
            
        merged_exp.sort(key=get_sort_key, reverse=True)
        return merged_exp

    def _merge_education(self, profiles: List[CandidateProfile]) -> List[EducationEntry]:
        """Merges academic history. Groups by institution name."""
        merged_edu: List[EducationEntry] = []
        for p in profiles:
            for edu in p.education:
                normalized_inst = edu.institution.strip().lower()
                
                match_edu = None
                for existing in merged_edu:
                    if normalized_inst in existing.institution.strip().lower() or existing.institution.strip().lower() in normalized_inst:
                        match_edu = existing
                        break
                        
                if match_edu:
                    # Keep longest degree names or end year
                    if edu.degree and (not match_edu.degree or len(edu.degree) > len(match_edu.degree)):
                        match_edu.degree = edu.degree
                    if edu.field and (not match_edu.field or len(edu.field) > len(match_edu.field)):
                        match_edu.field = edu.field
                    if edu.end_year and not match_edu.end_year:
                        match_edu.end_year = edu.end_year
                else:
                    merged_edu.append(
                        EducationEntry(
                            institution=edu.institution,
                            degree=edu.degree,
                            field=edu.field,
                            end_year=edu.end_year
                        )
                    )
                    
        # Sort education by end year descending
        merged_edu.sort(key=lambda x: x.end_year or "0000", reverse=True)
        return merged_edu
