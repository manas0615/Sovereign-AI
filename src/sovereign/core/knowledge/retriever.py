"""Retriever abstraction."""

from abc import ABC, abstractmethod
from typing import List, Optional
from sovereign.core.knowledge.models import RetrievalResult

class Retriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5, document_id: Optional[str] = None) -> List[RetrievalResult]:
        """
        Retrieve relevant results based on a query.
        Returns up to top_k results.
        """
        pass
