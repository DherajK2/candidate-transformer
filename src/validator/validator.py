"""
Validator module.
Validates canonical profile profiles and projection configurations using jsonschema.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import jsonschema

from src.utils.logger import get_logger

logger = get_logger("validator.engine")

# Schema file locations
SCHEMA_DIR = Path(__file__).parent.parent / "schema"
CANONICAL_SCHEMA_PATH = SCHEMA_DIR / "canonical_schema.json"
CONFIG_SCHEMA_PATH = SCHEMA_DIR / "projection_config_schema.json"


class JSONValidator:
    """Provides methods to validate dictionaries against canonical candidate and config JSON schemas."""

    def __init__(self) -> None:
        # Load canonical schema
        if not CANONICAL_SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Canonical schema file not found at: {CANONICAL_SCHEMA_PATH}")
        with open(CANONICAL_SCHEMA_PATH, "r", encoding="utf-8") as f:
            self.canonical_schema = json.load(f)

        # Load projection config schema
        if not CONFIG_SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Config schema file not found at: {CONFIG_SCHEMA_PATH}")
        with open(CONFIG_SCHEMA_PATH, "r", encoding="utf-8") as f:
            self.config_schema = json.load(f)

    def validate_canonical_profile(self, profile_data: Dict[str, Any]) -> None:
        """
        Validates the canonical profile dictionary against canonical_schema.json.
        Raises jsonschema.ValidationError on failure.
        """
        logger.info("Validating canonical candidate profile schema.")
        try:
            jsonschema.validate(instance=profile_data, schema=self.canonical_schema)
            logger.info("Canonical profile schema validation PASSED.")
        except jsonschema.ValidationError as e:
            logger.error(f"Canonical profile schema validation FAILED: {e.message}")
            raise e

    def validate_projection_config(self, config_data: Dict[str, Any]) -> None:
        """
        Validates the projection configuration dictionary against projection_config_schema.json.
        Raises jsonschema.ValidationError on failure.
        """
        logger.info("Validating projection configuration schema.")
        try:
            jsonschema.validate(instance=config_data, schema=self.config_schema)
            logger.info("Projection configuration schema validation PASSED.")
        except jsonschema.ValidationError as e:
            logger.error(f"Projection configuration schema validation FAILED: {e.message}")
            raise e

    def validate_projected_output(self, output_data: Dict[str, Any], schema_data: Dict[str, Any]) -> None:
        """
        Validates the final projected output dictionary against a user-supplied dynamic schema.
        Raises jsonschema.ValidationError on failure.
        """
        logger.info("Validating projected output against dynamic schema.")
        try:
            jsonschema.validate(instance=output_data, schema=schema_data)
            logger.info("Projected output validation PASSED.")
        except jsonschema.ValidationError as e:
            logger.error(f"Projected output validation FAILED: {e.message}")
            raise e
