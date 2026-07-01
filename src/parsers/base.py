"""
Abstract Base Parser class definition.
Defines interface contracts for candidate profile parsers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from src.models import CandidateProfile


class BaseParser(ABC):
    """Base class for all candidate document source parsers."""

    @abstractmethod
    def parse(self, file_path: Path) -> CandidateProfile:
        """
        Parses candidate data from the specified path.
        Returns a CandidateProfile with initialized fields and source provenance.
        """
        pass
