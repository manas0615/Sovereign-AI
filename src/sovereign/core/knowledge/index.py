"""Knowledge index abstractions."""

from abc import ABC, abstractmethod
from typing import List
from sovereign.core.knowledge.models import DocumentChunk

class KnowledgeIndex(ABC):
    @abstractmethod
    def index_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add chunks to the searchable index."""
        pass
        
    @abstractmethod
    def remove_document(self, document_id: str) -> None:
        """Remove a document's chunks from the searchable index."""
        pass
