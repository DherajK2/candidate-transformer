"""
Text Parser utility.
Parses candidate entities from clean unstructured text content via regex patterns and heuristic section scanning.
"""

from datetime import datetime
import re
from typing import List, Dict, Any, Optional

from src.models import (
    CandidateProfile, Location, Links, SkillEntry,
    ExperienceEntry, EducationEntry, ProvenanceEntry
)
from src.utils.logger import get_logger

logger = get_logger("parsers.text")


class TextParser:
    """Extracts candidate profile fields from plain text using regex and heuristics."""

    def parse_text(self, text: str, source_name: str) -> CandidateProfile:
        """
        Parses raw text representation. Uses section splitting and regexes.
        """
        logger.info(f"Parsing unstructured text from source: {source_name}")
        lines = [line.strip() for line in text.split("\n")]
        non_empty_lines = [line for line in lines if line]

        if not non_empty_lines:
            raise ValueError("Empty text content")

        # 1. Extract Name (Heuristic: usually the first non-empty line, if it contains words and not email/phone)
        name = ""
        for line in non_empty_lines[:4]:
            # Skip lines containing email, phone, or obvious sections
            if "@" in line or any(c in line for c in ["+", "(", ")"]) or len(line.split()) > 4:
                continue
            if re.search(r"(education|experience|skills|summary|contact|profile|links|github|linkedin)", line, re.I):
                continue
            # Must look like a name (capitalized words)
            if re.match(r"^[A-Z][a-zA-Z]*(\s+[A-Z][a-zA-Z]*)+$", line):
                name = line
                break
        
        # Fallback to first line if nothing matched
        if not name and non_empty_lines:
            name = non_empty_lines[0]

        # 2. Extract Emails
        email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        emails = re.findall(email_pattern, text)
        emails = list(dict.fromkeys([e.strip() for e in emails])) # Deduplicate preserving order

        # 3. Extract Phones
        # Matches formats containing 10 to 15 digits separated by spaces, hyphens, dots, or parens
        phone_pattern = r"\+?[-.\s()]*\d(?:[-.\s()]*\d){9,14}"
        phones = re.findall(phone_pattern, text)
        phones = list(dict.fromkeys([p.strip() for p in phones]))

        # 4. Links
        linkedin = None
        github = None
        portfolio = None
        other_links = []

        # Extract URLs (both with protocol e.g. https:// and scheme-less e.g. github.com/username)
        # Exclude email addresses by ensuring no '@' exists before the domain
        url_pattern = r"(?:https?://)?(?:www\.)?[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,4}(?:/[^\s()<>|]*)*"
        urls = re.findall(url_pattern, text)
        for url in urls:
            if "@" in url:
                continue
            url_lower = url.lower()
            if "linkedin.com" in url_lower:
                if not linkedin:
                    linkedin = url
            elif "github.com" in url_lower:
                if not github:
                    github = url
            elif any(domain in url_lower for domain in ["portfolio", "personal", "website", "me."]):
                if not portfolio:
                    portfolio = url
            else:
                if not any(x in url_lower for x in ["gmail.com", "email.com"]):
                    other_links.append(url)
        other_links = list(dict.fromkeys(other_links))

        links = Links(linkedin=linkedin, github=github, portfolio=portfolio, other=other_links)

        # 5. Extract Skills (Check for presence of tech words)
        tech_keywords = [
            "React", "ReactJS", "React.js", "JavaScript", "JS", "TypeScript", "TS",
            "Python", "Java", "C++", "C#", "Go", "Golang", "Rust", "Node.js", "NodeJS", "Node",
            "Express", "Express.js", "Spring", "WebFlux", "Redis", "MongoDB", "MySQL", "Git",
            "GitHub Actions", "Docker", "Kubernetes", "Prometheus", "Grafana", "n8n", "WebSockets",
            "AWS", "PostgreSQL", "Postgres", "HTML", "CSS", "Django", "Flask", "Spark", "Hadoop", "Pandas", "NumPy"
        ]
        skills_found = []
        for tech in tech_keywords:
            # Word boundary check, escaping ++ and #
            escaped_tech = re.escape(tech)
            # Standard word boundaries don't work well on trailing ++ or #, handle separately
            if tech.endswith("++") or tech.endswith("#"):
                pattern = rf"\b{escaped_tech}"
            else:
                pattern = rf"\b{escaped_tech}\b"
            if re.search(pattern, text, re.I):
                skills_found.append(SkillEntry(name=tech, confidence=0.65, sources=[source_name]))

        # 6. Extract Location
        # Looks for "Location: City, Country" or matches "City, State, Country"
        city, region, country = None, None, None
        loc_match = re.search(r"(?:location|address|based\s+in):\s*([A-Za-z\s]+),\s*([A-Za-z\s]+)(?:,\s*([A-Za-z\s]+))?", text, re.I)
        if loc_match:
            g1 = loc_match.group(1).strip()
            g2 = loc_match.group(2).strip()
            g3 = loc_match.group(3)
            if g3:
                city, region, country = g1, g2, g3.strip()
            else:
                city, country = g1, g2
        else:
            # Simple keyword search for country aliases in text
            countries_list = ["India", "USA", "United States", "Canada", "UK", "Germany", "Singapore"]
            for c in countries_list:
                if re.search(rf"\b{c}\b", text, re.I):
                    country = c
                    break

        location = Location(city=city, region=region, country=country)

        # 7. Extract Headline
        headline = None
        head_match = re.search(r"(?:headline|summary|about\s+me|profile):\s*(.+)", text, re.I)
        if head_match:
            headline = head_match.group(1).strip()
        else:
            # Heuristic: the line after the name, if it looks like a designation
            if len(non_empty_lines) > 1 and name in non_empty_lines[0]:
                second_line = non_empty_lines[1]
                if len(second_line.split()) <= 5 and not any(c in second_line for c in ["@", "+", "/"]):
                    headline = second_line

        # 8. Experience Years
        years_experience = None
        exp_yr_match = re.search(r"(\d+(?:\.\d+)?)\+?\s*years?\s+(?:of\s+)?experience", text, re.I)
        if exp_yr_match:
            try:
                years_experience = float(exp_yr_match.group(1))
            except ValueError:
                pass

        # 9. Extract Section: Experience & Education (Heuristic split)
        experience = []
        education = []

        # Find section offsets
        sections = {"experience": -1, "education": -1}
        for i, line in enumerate(lines):
            l_lower = line.lower()
            if re.match(r"^(work\s+)?experience(s)?\b", l_lower) or re.match(r"^employment\b", l_lower) or re.match(r"^professional\s+history\b", l_lower):
                sections["experience"] = i
            elif re.match(r"^education\b", l_lower) or re.match(r"^academic\b", l_lower) or re.match(r"^studies\b", l_lower):
                sections["education"] = i

        # Parse Experience Section
        if sections["experience"] != -1:
            end_idx = len(lines)
            if sections["education"] > sections["experience"]:
                end_idx = sections["education"]
            
            exp_text_lines = lines[sections["experience"]+1:end_idx]
            # Simple heuristic: Look for lines with dates or company patterns
            # e.g., "Microsoft - Software Engineer (Jan 2020 - Present)"
            current_entry: Optional[Dict[str, Any]] = None
            for exp_line in exp_text_lines:
                if not exp_line:
                    continue
                
                # Check if it looks like a header: "Company, Role, Date"
                # Match year ranges: e.g. 2020 - 2023 or Jan 2020 - Present
                date_range_match = re.search(
                    r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{1,2}/\d{4}|\d{4})\s*[-–to\s]+\s*(?:present|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{1,2}/\d{4}|\d{4}))",
                    exp_line, re.I
                )
                if date_range_match:
                    # Save old
                    if current_entry:
                        experience.append(ExperienceEntry(**current_entry))
                    
                    # Split date out
                    raw_date_range = date_range_match.group(1)
                    header_part = exp_line.replace(raw_date_range, "").strip(" -–,()[]")
                    
                    # Heuristic company vs title
                    header_parts = [p.strip() for p in re.split(r"[,–|:-]", header_part) if p.strip()]
                    comp = header_parts[0] if len(header_parts) > 0 else "Unknown"
                    title = header_parts[1] if len(header_parts) > 1 else "Software Engineer"
                    
                    # Split dates
                    date_parts = re.split(r"[-–to]+", raw_date_range)
                    start_date = date_parts[0].strip() if len(date_parts) > 0 else None
                    end_date = date_parts[1].strip() if len(date_parts) > 1 else "Present"

                    current_entry = {
                        "company": comp,
                        "title": title,
                        "start": start_date,
                        "end": end_date,
                        "summary": ""
                    }
                else:
                    if current_entry:
                        current_entry["summary"] = (current_entry["summary"] + " " + exp_line).strip()
            
            if current_entry:
                experience.append(ExperienceEntry(**current_entry))

        # Parse Education Section
        if sections["education"] != -1:
            end_idx = len(lines)
            if sections["experience"] > sections["education"]:
                end_idx = sections["experience"]
            
            edu_text_lines = lines[sections["education"]+1:end_idx]
            for edu_line in edu_text_lines:
                if not edu_line:
                    continue
                # Look for degree/institution keyword
                if any(keyword in edu_line.lower() for keyword in ["university", "college", "school", "institute", "bachelor", "master", "phd", "b.s", "m.s", "b.tech", "m.tech"]):
                    # Extract year
                    yr_match = re.search(r"\b(19\d{2}|20\d{2})\b", edu_line)
                    end_yr = yr_match.group(1) if yr_match else None
                    
                    line_no_yr = edu_line.replace(end_yr, "") if end_yr else edu_line
                    parts = [p.strip() for p in re.split(r"[,–|-]", line_no_yr) if p.strip()]
                    
                    inst = parts[0] if len(parts) > 0 else "University"
                    deg = parts[1] if len(parts) > 1 else None
                    fld = parts[2] if len(parts) > 2 else None
                    
                    education.append(
                        EducationEntry(
                            institution=inst,
                            degree=deg,
                            field=fld,
                            end_year=end_yr
                        )
                    )

        # 10. Trace Provenance
        timestamp = datetime.now().isoformat()
        provenance = []
        fields_parsed = [
            ("full_name", name), ("emails", emails), ("phones", phones),
            ("location", location.city or location.country), ("links", links.linkedin or links.github),
            ("headline", headline), ("years_experience", years_experience),
            ("skills", skills_found), ("experience", experience), ("education", education)
        ]
        for field_name, val in fields_parsed:
            if val:
                provenance.append(
                    ProvenanceEntry(
                        field=field_name,
                        source=source_name,
                        method="regex_heuristics",
                        timestamp=timestamp,
                        confidence=0.65
                    )
                )

        return CandidateProfile(
            candidate_id=f"cand_txt_{hash(name + ''.join(emails)) & 0xffffffff:08x}",
            full_name=name,
            emails=emails,
            phones=phones,
            location=location,
            links=links,
            headline=headline,
            years_experience=years_experience,
            skills=skills_found,
            experience=experience,
            education=education,
            provenance=provenance,
            overall_confidence=0.65
        )
