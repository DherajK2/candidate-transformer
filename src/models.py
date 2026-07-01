"""
Data models representing the Canonical Candidate Schema.
Provides class representations, serialization, and deserialization routines.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class Location:
    """Represents candidate location coordinates/address fields."""
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None  # Expected format: ISO 3166-1 alpha-2 (e.g. IN)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize location details to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Location":
        """Deserialize from dictionary format."""
        return cls(
            city=data.get("city"),
            region=data.get("region"),
            country=data.get("country")
        )


@dataclass
class Links:
    """Represents external candidate link profiles."""
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    other: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize links to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Links":
        """Deserialize from dictionary format."""
        return cls(
            linkedin=data.get("linkedin"),
            github=data.get("github"),
            portfolio=data.get("portfolio"),
            other=data.get("other") or []
        )


@dataclass
class SkillEntry:
    """Represents a normalized skill with associated confidence and sources."""
    name: str
    confidence: float
    sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary format."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillEntry":
        """Deserialize from dictionary format."""
        return cls(
            name=data.get("name", ""),
            confidence=data.get("confidence", 0.0),
            sources=data.get("sources") or []
        )


@dataclass
class ExperienceEntry:
    """Represents professional candidate history."""
    company: str
    title: str
    start: Optional[str] = None  # Expected format: YYYY-MM
    end: Optional[str] = None    # Expected format: YYYY-MM or "Present"
    summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary format."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperienceEntry":
        """Deserialize from dictionary format."""
        return cls(
            company=data.get("company", ""),
            title=data.get("title", ""),
            start=data.get("start"),
            end=data.get("end"),
            summary=data.get("summary")
        )


@dataclass
class EducationEntry:
    """Represents candidate academic history."""
    institution: str
    degree: Optional[str] = None
    field: Optional[str] = None
    end_year: Optional[str] = None  # Expected format: YYYY

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary format."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EducationEntry":
        """Deserialize from dictionary format."""
        return cls(
            institution=data.get("institution", ""),
            degree=data.get("degree"),
            field=data.get("field"),
            end_year=data.get("end_year")
        )


@dataclass
class ProvenanceEntry:
    """Represents tracing information about how a canonical field was resolved."""
    field: str
    source: str
    method: str
    timestamp: str
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary format."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProvenanceEntry":
        """Deserialize from dictionary format."""
        return cls(
            field=data.get("field", ""),
            source=data.get("source", ""),
            method=data.get("method", ""),
            timestamp=data.get("timestamp", ""),
            confidence=data.get("confidence", 0.0)
        )


@dataclass
class CandidateProfile:
    """Represents the complete Canonical Candidate Profile."""
    candidate_id: str
    full_name: str
    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    location: Location = field(default_factory=Location)
    links: Links = field(default_factory=Links)
    headline: Optional[str] = None
    years_experience: Optional[float] = None
    skills: List[SkillEntry] = field(default_factory=list)
    experience: List[ExperienceEntry] = field(default_factory=list)
    education: List[EducationEntry] = field(default_factory=list)
    provenance: List[ProvenanceEntry] = field(default_factory=list)
    overall_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize complete profile to dictionary format."""
        return {
            "candidate_id": self.candidate_id,
            "full_name": self.full_name,
            "emails": self.emails,
            "phones": self.phones,
            "location": self.location.to_dict(),
            "links": self.links.to_dict(),
            "headline": self.headline,
            "years_experience": self.years_experience,
            "skills": [s.to_dict() for s in self.skills],
            "experience": [e.to_dict() for e in self.experience],
            "education": [ed.to_dict() for ed in self.education],
            "provenance": [p.to_dict() for p in self.provenance],
            "overall_confidence": self.overall_confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CandidateProfile":
        """Deserialize from canonical dictionary format."""
        return cls(
            candidate_id=data.get("candidate_id", ""),
            full_name=data.get("full_name", ""),
            emails=data.get("emails") or [],
            phones=data.get("phones") or [],
            location=Location.from_dict(data.get("location") or {}),
            links=Links.from_dict(data.get("links") or {}),
            headline=data.get("headline"),
            years_experience=data.get("years_experience"),
            skills=[SkillEntry.from_dict(s) for s in data.get("skills") or []],
            experience=[ExperienceEntry.from_dict(e) for e in data.get("experience") or []],
            education=[EducationEntry.from_dict(ed) for ed in data.get("education") or []],
            provenance=[ProvenanceEntry.from_dict(p) for p in data.get("provenance") or []],
            overall_confidence=data.get("overall_confidence", 0.0),
        )
