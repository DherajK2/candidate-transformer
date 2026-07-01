"""
Normalizer module to standardize inputs such as phone numbers, dates,
skills, countries, URLs, and array lists according to the canonical format.
"""

import re
from typing import Dict, List, Any, Optional

# Pre-compiled mapping configs for skills and countries
SKILL_MAP: Dict[str, str] = {
    "reactjs": "React",
    "react.js": "React",
    "react": "React",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "python": "Python",
    "py": "Python",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "aws": "Amazon Web Services",
    "amazon web services": "Amazon Web Services",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "golang": "Go",
    "go lang": "Go",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "html": "HTML",
    "css": "CSS",
    "c++": "C++",
    "java": "Java",
    "django": "Django",
    "flask": "Flask",
    "express": "Express",
    "express.js": "Express",
    "spring": "Spring",
    "webflux": "Spring WebFlux",
    "redis": "Redis",
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    "n8n": "n8n",
    "websockets": "WebSockets",
    "websocket": "WebSockets",
    "github actions": "GitHub Actions",
    "git": "Git",
}

COUNTRY_MAP: Dict[str, str] = {
    "india": "IN",
    "ind": "IN",
    "in": "IN",
    "united states": "US",
    "united states of america": "US",
    "usa": "US",
    "us": "US",
    "united kingdom": "GB",
    "uk": "GB",
    "great britain": "GB",
    "gbr": "GB",
    "canada": "CA",
    "can": "CA",
    "ca": "CA",
    "germany": "DE",
    "de": "DE",
    "singapore": "SG",
    "sgp": "SG",
    "sg": "SG",
}

MONTH_MAP: Dict[str, str] = {
    "jan": "01", "january": "01",
    "feb": "02", "february": "02",
    "mar": "03", "march": "03",
    "apr": "04", "april": "04",
    "may": "05",
    "jun": "06", "june": "06",
    "jul": "07", "july": "07",
    "aug": "08", "august": "08",
    "sep": "09", "september": "09",
    "oct": "10", "october": "10",
    "nov": "11", "november": "11",
    "dec": "12", "december": "12"
}


def normalize_phone(phone: str, default_prefix: str = "+91") -> str:
    """
    Normalizes phone numbers to E.164 standard (e.g. +919876543210).
    Strips non-digits/non-plus and prepends standard prefix if needed.
    """
    if not phone:
        return ""
    # Strip everything except digits and plus sign
    cleaned = re.sub(r"[^\d+]", "", phone)
    
    # If it starts with '+', it's already got a country code
    if cleaned.startswith("+"):
        return cleaned
        
    # If 10 digits, prepend default prefix
    if len(cleaned) == 10:
        return f"{default_prefix}{cleaned}"
        
    # If starts with country code without '+' (e.g. 919876543210)
    if cleaned.startswith("91") and len(cleaned) == 12:
        return f"+{cleaned}"
    if cleaned.startswith("1") and len(cleaned) == 11:
        return f"+{cleaned}"

    # Return clean digits with a prepended + if not already
    return f"+{cleaned}" if not cleaned.startswith("+") else cleaned


def normalize_skill(skill: str) -> str:
    """
    Normalizes technology skills to a canonical representation.
    e.g. ReactJS / React.js -> React.
    """
    if not skill:
        return ""
    cleaned = skill.strip().lower()
    # Check map
    if cleaned in SKILL_MAP:
        return SKILL_MAP[cleaned]
    # Fallback to Title Cased clean string
    return skill.strip()


def normalize_country(country: str) -> str:
    """
    Normalizes a country name or alias to ISO-3166-1 alpha-2.
    """
    if not country:
        return ""
    cleaned = country.strip().lower()
    if cleaned in COUNTRY_MAP:
        return COUNTRY_MAP[cleaned]
    
    # Fallback checking 2 letter codes
    if len(cleaned) == 2:
        return country.strip().upper()
        
    return country.strip()  # Return as-is if unrecognized


def normalize_url(url: str) -> str:
    """
    Normalizes profiles URLs (LinkedIn, GitHub, Portfolio).
    Strips query arguments, http schemas, prefixes, and standardizes format.
    """
    if not url:
        return ""
    cleaned = url.strip().lower()
    
    # Strip scheme
    cleaned = re.sub(r"^https?://(www\.)?", "", cleaned)
    cleaned = cleaned.rstrip("/")
    
    # Identify type
    if "linkedin.com" in cleaned:
        # e.g. linkedin.com/in/johndoe/details -> linkedin.com/in/johndoe
        match = re.search(r"linkedin\.com/in/([^/]+)", cleaned)
        if match:
            return f"https://www.linkedin.com/in/{match.group(1)}"
        return f"https://{cleaned}"
    elif "github.com" in cleaned:
        match = re.search(r"github\.com/([^/]+)", cleaned)
        if match:
            return f"https://github.com/{match.group(1)}"
        return f"https://{cleaned}"
    
    return f"https://{cleaned}"


def normalize_dates(date_str: str) -> str:
    """
    Normalizes input date representations to YYYY-MM.
    Handles 'Jan 2024', '01/2024', '2024', '2024-01-15', and 'Present'.
    """
    if not date_str:
        return ""
    
    cleaned = date_str.strip().lower()
    if cleaned == "present":
        return "Present"
        
    # Match YYYY-MM-DD or YYYY-MM
    match_ymd = re.match(r"^(\d{4})[-/](\d{2})", cleaned)
    if match_ymd:
        return f"{match_ymd.group(1)}-{match_ymd.group(2)}"
        
    # Match MM/YYYY or MM-YYYY
    match_my = re.match(r"^(\d{2})[-/](\d{4})$", cleaned)
    if match_my:
        return f"{match_my.group(2)}-{match_my.group(1)}"
        
    # Match Month YYYY (e.g., Jan 2024, January 2024)
    match_m_y = re.match(r"^([a-z]+)\s+(\d{4})$", cleaned)
    if match_m_y:
        mon = match_m_y.group(1)
        yr = match_m_y.group(2)
        month_num = MONTH_MAP.get(mon, "01")
        return f"{yr}-{month_num}"
        
    # Match YYYY Month (e.g. 2024 Jan)
    match_y_m = re.match(r"^(\d{4})\s+([a-z]+)$", cleaned)
    if match_y_m:
        yr = match_y_m.group(1)
        mon = match_y_m.group(2)
        month_num = MONTH_MAP.get(mon, "01")
        return f"{yr}-{month_num}"

    # Match YYYY only
    match_y = re.match(r"^(\d{4})$", cleaned)
    if match_y:
        return f"{match_y.group(1)}-01"  # Default to January
        
    return date_str.strip()  # Return unmodified if parsing fails


def remove_duplicates(items: List[Any]) -> List[Any]:
    """Removes duplicates from a list while maintaining insertion order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
