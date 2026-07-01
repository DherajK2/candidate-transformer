"""
Confidence Engine module.
Evaluates base source confidences, boosts values on cross-source consensus,
applies penalties on normalization failures, and computes overall profile score.
"""

from typing import List, Dict, Any, Set
from src.models import CandidateProfile, SkillEntry, ProvenanceEntry
from src.normalizer.normalizer import normalize_phone, normalize_country
from src.utils.logger import get_logger

logger = get_logger("confidence.engine")


class ConfidenceEngine:
    """Calculates field-level and overall candidate profile confidence scores."""

    def calculate_confidence(self, merged_profile: CandidateProfile, raw_profiles: List[CandidateProfile]) -> CandidateProfile:
        """
        Updates the field-level confidence in the provenance logs and skill entries
        based on source agreement and normalization checks. Computes overall profile confidence.
        """
        logger.info("Evaluating profile confidence scores.")
        
        # Mapping of field -> list of source values
        field_values: Dict[str, List[Any]] = {
            "full_name": [],
            "emails": [],
            "phones": [],
            "location.country": [],
            "years_experience": [],
        }

        # Collect raw values for consensus checking
        for rp in raw_profiles:
            if rp.full_name:
                field_values["full_name"].append(rp.full_name.strip().lower())
            for e in rp.emails:
                field_values["emails"].append(e.strip().lower())
            for p in rp.phones:
                field_values["phones"].append(normalize_phone(p))
            if rp.location and rp.location.country:
                field_values["location.country"].append(normalize_country(rp.location.country))
            if rp.years_experience is not None:
                field_values["years_experience"].append(rp.years_experience)

        # 1. Update Provenance Entry Confidence
        updated_provenance: List[ProvenanceEntry] = []
        field_confidences: List[float] = []

        for prov in merged_profile.provenance:
            base_conf = prov.confidence
            field_name = prov.field
            
            # Check for consensus boost
            boost = 0.0
            if field_name in field_values:
                vals = field_values[field_name]
                # Find matching value in merged profile to check consensus count
                merged_val = None
                if field_name == "full_name":
                    merged_val = merged_profile.full_name.strip().lower()
                elif field_name == "emails" and merged_profile.emails:
                    merged_val = merged_profile.emails[0].strip().lower()  # check primary email
                elif field_name == "phones" and merged_profile.phones:
                    merged_val = merged_profile.phones[0]  # check primary phone
                elif field_name == "location" and merged_profile.location.country:
                    merged_val = normalize_country(merged_profile.location.country)
                elif field_name == "years_experience" and merged_profile.years_experience is not None:
                    merged_val = merged_profile.years_experience

                if merged_val is not None:
                    # Number of agreeing profiles (value matches)
                    matches = sum(1 for v in vals if v == merged_val)
                    if matches > 1:
                        boost = (matches - 1) * 0.10
                        logger.debug(f"Consensus boost of +{boost:.2f} applied to field: {field_name}")

            # Check for normalization penalties
            penalty = 0.0
            if field_name == "phones":
                for ph in merged_profile.phones:
                    if not ph.startswith("+") or len(ph) < 10:
                        penalty = 0.15
                        logger.warning(f"Normalization penalty of -0.15 applied to field: {field_name} (invalid E.164: {ph})")
                        break
            elif field_name == "location":
                country = merged_profile.location.country
                if country and (len(country) != 2 or not country.isupper()):
                    penalty = 0.15
                    logger.warning(f"Normalization penalty of -0.15 applied to field: {field_name} (invalid ISO country: {country})")

            # Calculate final field confidence
            final_conf = min(1.0, max(0.0, base_conf + boost - penalty))
            prov.confidence = round(final_conf, 2)
            updated_provenance.append(prov)
            field_confidences.append(final_conf)

        # 2. Update Skill Entries Confidence (Boost based on number of sources mentioning the skill)
        updated_skills: List[SkillEntry] = []
        for sk in merged_profile.skills:
            base_sk_conf = sk.confidence
            sources_count = len(sk.sources)
            boost = (sources_count - 1) * 0.10 if sources_count > 1 else 0.0
            
            # Penalty check (empty skill name shouldn't happen, but safeguard)
            penalty = 0.15 if not sk.name else 0.0
            
            final_sk_conf = min(1.0, max(0.0, base_sk_conf + boost - penalty))
            sk.confidence = round(final_sk_conf, 2)
            updated_skills.append(sk)
            field_confidences.append(final_sk_conf)

        # 3. Overall Profile Confidence Score (Average of all fields, fallback to source base if no fields)
        if field_confidences:
            overall_confidence = sum(field_confidences) / len(field_confidences)
        else:
            overall_confidence = 0.65

        merged_profile.provenance = updated_provenance
        merged_profile.skills = updated_skills
        merged_profile.overall_confidence = round(overall_confidence, 2)
        
        logger.info(f"Overall candidate profile confidence calculated: {merged_profile.overall_confidence}")
        return merged_profile
