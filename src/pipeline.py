"""
Pipeline coordinator module.
Orchestrates parsing, canonical mapping, normalization, merging,
confidence evaluation, projection, and schema validation.
"""

import json
from pathlib import Path
import re
from typing import List, Dict, Any, Optional

from src.models import CandidateProfile
from src.parsers.csv_parser import CSVParser
from src.parsers.json_parser import JSONParser
from src.parsers.pdf_parser import PDFParser
from src.parsers.text_parser import TextParser
from src.normalizer.normalizer import (
    normalize_phone, normalize_skill, normalize_country,
    normalize_url, normalize_dates
)
from src.merger.merge_engine import MergeEngine
from src.confidence.confidence_engine import ConfidenceEngine
from src.projection.projection_layer import ProjectionLayer
from src.validator.validator import JSONValidator
from src.utils.logger import get_logger

logger = get_logger("pipeline.orchestrator")


class CandidatePipeline:
    """Coordinates the end-to-end candidate data transformation pipeline."""

    def __init__(self) -> None:
        self.csv_parser = CSVParser()
        self.json_parser = JSONParser()
        self.pdf_parser = PDFParser()
        self.text_parser = TextParser()
        
        self.merge_engine = MergeEngine()
        self.confidence_engine = ConfidenceEngine()
        self.projection_layer = ProjectionLayer()
        self.validator = JSONValidator()

    def run(
        self,
        source_paths: List[Path],
        config_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Runs the complete transformation pipeline.
        
        1. Reads and parses heterogeneous input sources.
        2. Normalizes individual values.
        3. Merges duplicate profiles.
        4. Calculates field-level & overall confidence.
        5. Validates against the canonical JSON schema.
        6. Projects and reshapes outputs (if config provided).
        """
        logger.info(f"Starting pipeline run with {len(source_paths)} input sources.")
        raw_profiles: List[CandidateProfile] = []

        # Step 1: Parsing heterogenous inputs
        for path in source_paths:
            if not path.exists():
                raise FileNotFoundError(f"Input file does not exist: {path}")
            
            ext = path.suffix.lower()
            try:
                if ext == ".csv":
                    profile = self.csv_parser.parse(path)
                elif ext == ".json":
                    profile = self.json_parser.parse(path)
                elif ext == ".pdf":
                    profile = self.pdf_parser.parse(path)
                elif ext == ".txt":
                    # Read text content
                    with open(path, "r", encoding="utf-8") as f:
                        text_content = f.read()
                    profile = self.text_parser.parse_text(text_content, path.name)
                else:
                    raise ValueError(f"Unsupported file format: {ext}")
                
                raw_profiles.append(profile)
                logger.info(f"Successfully parsed source: {path.name}")
            except Exception as e:
                logger.error(f"Error parsing source {path.name}: {str(e)}")
                raise e

        if not raw_profiles:
            raise ValueError("No candidate records were parsed")

        # Step 2: Normalize individual candidate profiles before merging
        normalized_raw_profiles = [self._normalize_profile(p) for p in raw_profiles]

        # Step 3: Merge candidate profiles into one canonical profile
        merged_profile = self.merge_engine.merge_profiles(normalized_raw_profiles)

        # Step 4: Evaluate confidence scores (field and profile levels)
        final_profile = self.confidence_engine.calculate_confidence(merged_profile, normalized_raw_profiles)

        # Step 5: Validate merged profile against canonical schema
        final_dict = final_profile.to_dict()
        self.validator.validate_canonical_profile(final_dict)

        # Step 6: Output projection
        if config_path:
            if not config_path.exists():
                raise FileNotFoundError(f"Projection config not found at: {config_path}")
            
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception as e:
                raise ValueError(f"Failed to read projection config: {str(e)}")

            # Validate configuration structure itself
            self.validator.validate_projection_config(config_data)

            # Perform custom projection mapping
            projected_output = self.projection_layer.project(final_profile, config_data)
            logger.info("Pipeline run successfully completed with dynamic custom projection.")
            return projected_output

        logger.info("Pipeline run successfully completed with default canonical layout.")
        return final_dict

    def _normalize_profile(self, profile: CandidateProfile) -> CandidateProfile:
        """Helper to run the normalizers across individual profile attributes."""
        # Clean basic attributes
        profile.full_name = profile.full_name.strip()
        profile.emails = [e.strip().lower() for e in profile.emails if e.strip()]
        profile.phones = [normalize_phone(ph) for ph in profile.phones if ph.strip()]
        
        # Location
        if profile.location:
            profile.location.city = profile.location.city.strip() if profile.location.city else None
            profile.location.region = profile.location.region.strip() if profile.location.region else None
            profile.location.country = normalize_country(profile.location.country) if profile.location.country else None

        # Links
        if profile.links:
            profile.links.linkedin = normalize_url(profile.links.linkedin) if profile.links.linkedin else None
            profile.links.github = normalize_url(profile.links.github) if profile.links.github else None
            profile.links.portfolio = normalize_url(profile.links.portfolio) if profile.links.portfolio else None
            profile.links.other = [normalize_url(lnk) for lnk in profile.links.other if lnk.strip()]

        # Experience dates
        for exp in profile.experience:
            if exp.start:
                exp.start = normalize_dates(exp.start)
            if exp.end:
                exp.end = normalize_dates(exp.end)

        # Education dates
        for edu in profile.education:
            if edu.end_year:
                # Match YYYY
                match = re.search(r"\b(\d{4})\b", edu.end_year)
                if match:
                    edu.end_year = match.group(1)

        # Skills
        for sk in profile.skills:
            sk.name = normalize_skill(sk.name)

        return profile
