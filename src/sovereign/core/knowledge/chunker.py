"""Chunker abstraction."""

from abc import ABC, abstractmethod
from typing import List
from sovereign.core.knowledge.models import DocumentBlock, DocumentChunk, Document

class Chunker(ABC):
    @abstractmethod
    def chunk(self, document: Document, blocks: List[DocumentBlock]) -> List[DocumentChunk]:
        """Convert structured blocks into sizing-appropriate chunks."""
        pass
