"""Document parser abstraction."""

from abc import ABC, abstractmethod
from typing import List, BinaryIO
from sovereign.core.knowledge.models import DocumentBlock, Document

class DocumentParser(ABC):
    @abstractmethod
    def parse(self, document: Document, file_stream: BinaryIO) -> List[DocumentBlock]:
        """
        Parses a document stream into structured blocks.
        May raise exceptions (e.g. OCRRequiredError).
        """
        pass

class OCRRequiredError(Exception):
    """Raised when a document requires OCR but only text extraction is available."""
    pass
