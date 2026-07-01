"""
PDF Parser implementation.
Uses pdfplumber or pypdf to extract text, then delegates parsing to the TextParser.
"""

from pathlib import Path
from pypdf import PdfReader
import pdfplumber

from src.models import CandidateProfile
from src.parsers.base import BaseParser
from src.parsers.text_parser import TextParser
from src.utils.logger import get_logger

logger = get_logger("parsers.pdf")


class PDFParser(BaseParser):
    """Extracts candidate profile fields from PDF documents."""

    def __init__(self) -> None:
        self.text_parser = TextParser()

    def parse(self, file_path: Path) -> CandidateProfile:
        """
        Extracts raw text layouts from PDF, falling back to pypdf if pdfplumber fails,
        then delegates to TextParser to extract entity structures.
        """
        logger.info(f"Parsing PDF file: {file_path}")
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found at: {file_path}")

        extracted_text = ""
        
        # Method 1: Try pdfplumber for high-fidelity structural text layout
        try:
            with pdfplumber.open(file_path) as pdf:
                pages_text = []
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text(layout=True) or page.extract_text() or ""
                    if page_text.strip():
                        pages_text.append(page_text)
                extracted_text = "\n".join(pages_text)
            logger.debug("Successfully extracted text via pdfplumber")
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed, attempting fallback to pypdf: {str(e)}")

        # Method 2: Fallback to pypdf if pdfplumber failed or yielded empty output
        if not extracted_text.strip():
            try:
                reader = PdfReader(file_path)
                pages_text = []
                for i, page in enumerate(reader.pages):
                    t = page.extract_text() or ""
                    if t.strip():
                        pages_text.append(t)
                extracted_text = "\n".join(pages_text)
                logger.debug("Successfully extracted text via pypdf fallback")
            except Exception as e:
                logger.error(f"pypdf fallback extraction also failed: {str(e)}")
                raise ValueError(f"Corrupt, encrypted, or invalid PDF document: {str(e)}")

        if not extracted_text.strip():
            raise ValueError("PDF document contains no extractable text content")

        # Parse extracted text contents
        profile = self.text_parser.parse_text(extracted_text, file_path.name)
        
        # Override provenance methods to indicate PDF parsing
        for p in profile.provenance:
            p.method = "pdf_text_extraction"
            
        return profile
