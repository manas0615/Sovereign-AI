"""Document Registry abstraction."""

from abc import ABC, abstractmethod
from typing import Optional, List
from sovereign.core.knowledge.models import Document, DocumentChunk

class DocumentRegistry(ABC):
    @abstractmethod
    def register_document(self, document: Document) -> None:
        pass
        
    @abstractmethod
    def update_document(self, document: Document) -> None:
        pass
        
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[Document]:
        pass

    @abstractmethod
    def list_documents(self) -> List[Document]:
        pass
        
    @abstractmethod
    def find_by_hash(self, content_hash: str) -> Optional[Document]:

        pass
        
    @abstractmethod
    def find_by_path(self, source_path: str) -> Optional[Document]:
        pass

class DocumentStore(ABC):
    @abstractmethod
    def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        pass
        
    @abstractmethod
    def get_chunk(self, chunk_id: str) -> Optional[DocumentChunk]:
        pass
        
    @abstractmethod
    def delete_chunks_for_document(self, document_id: str) -> None:
        pass

    @abstractmethod
    def get_chunks_for_document(self, document_id: str) -> List[DocumentChunk]:
        pass
