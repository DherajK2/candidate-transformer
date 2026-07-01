"""
Projection Layer module.
Reshapes, renames, and filters the canonical profile based on a dynamic runtime JSON configuration,
toggling confidence scores, provenance metadata, and specifying missing value policies.
"""

import json
from pathlib import Path
import re
from typing import Dict, Any, List, Optional

from src.models import CandidateProfile
from src.utils.logger import get_logger

logger = get_logger("projection.layer")


class ProjectionLayer:
    """Projects a canonical CandidateProfile into a customized output format using JSON configs."""

    def project(self, profile: CandidateProfile, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforms the CandidateProfile dataclass into a dictionary
        shaped by the rules in config_data.
        """
        logger.info("Projecting candidate profile based on configuration rules.")
        
        # Build canonical dict as initial source
        profile_dict = profile.to_dict()
        
        projected: Dict[str, Any] = {}
        fields_config = config_data.get("fields", [])
        on_missing_strategy = config_data.get("on_missing", "null")  # "null", "omit", "error"

        # Process each field in projection configuration
        for field_cfg in fields_config:
            dest_path = field_cfg.get("path")
            source_path = field_cfg.get("from", dest_path)
            is_required = field_cfg.get("required", False)

            # Resolve source value
            val = self._resolve_source_value(profile_dict, source_path)

            # Handle missing value
            if val is None or val == "" or val == []:
                if is_required:
                    if on_missing_strategy == "error":
                        raise ValueError(f"Required field '{dest_path}' (from '{source_path}') is missing or empty")
                    elif on_missing_strategy == "omit":
                        # Skip adding this field entirely
                        continue
                    else:
                        # "null" strategy
                        projected[dest_path] = None
                else:
                    if on_missing_strategy == "omit":
                        continue
                    else:
                        projected[dest_path] = None
            else:
                projected[dest_path] = val

        # Handle global confidence and provenance flags if they were not explicitly projected
        include_confidence = config_data.get("include_confidence", True)
        include_provenance = config_data.get("include_provenance", True)

        if include_confidence and "overall_confidence" not in projected:
            projected["overall_confidence"] = profile_dict.get("overall_confidence")
        elif not include_confidence:
            # Strip confidence keys from anywhere in the projected dict (e.g. nested lists)
            projected = self._strip_keys(projected, ["confidence", "overall_confidence"])

        if include_provenance and "provenance" not in projected:
            projected["provenance"] = profile_dict.get("provenance")
        elif not include_provenance:
            projected = self._strip_keys(projected, ["provenance"])

        return projected

    def _resolve_source_value(self, data: Dict[str, Any], path: str) -> Any:
        """
        Resolves nested expressions like:
        - 'full_name'
        - 'location.city'
        - 'emails[0]'
        - 'skills[].name'
        """
        # 1. Handle arrays with attribute mapping like 'skills[].name'
        if "[]" in path:
            base_path, attr = path.split("[].")
            items = self._get_value_by_path(data, base_path)
            if isinstance(items, list):
                result = []
                for item in items:
                    if isinstance(item, dict) and attr in item:
                        result.append(item[attr])
                return result if result else None
            return None

        # 2. Handle specific indices like 'emails[0]'
        index_match = re.search(r"([^\[]+)\[(\d+)\]", path)
        if index_match:
            base_path = index_match.group(1)
            idx = int(index_match.group(2))
            items = self._get_value_by_path(data, base_path)
            if isinstance(items, list) and idx < len(items):
                return items[idx]
            return None

        # 3. Simple dotted or direct paths
        return self._get_value_by_path(data, path)

    def _get_value_by_path(self, data: Dict[str, Any], path: str) -> Any:
        """Traverses a dictionary using dot notation (e.g. location.city)."""
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def _strip_keys(self, data: Any, keys_to_remove: List[str]) -> Any:
        """Recursively strips keys from dictionaries or lists of dictionaries."""
        if isinstance(data, dict):
            return {
                k: self._strip_keys(v, keys_to_remove)
                for k, v in data.items()
                if k not in keys_to_remove
            }
        elif isinstance(data, list):
            return [self._strip_keys(item, keys_to_remove) for item in data]
        return data
