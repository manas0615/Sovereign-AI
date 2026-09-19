"""Domain models for knowledge base."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timezone
import hashlib

def _now() -> datetime:
    return datetime.now(timezone.utc)

class DocumentStatus(str, Enum):
    REGISTERED = "REGISTERED"
    INGESTED = "INGESTED"
    OCR_REQUIRED = "OCR_REQUIRED"
    FAILED = "FAILED"

class Document(BaseModel):
    document_id: str = Field(default_factory=lambda: f"doc-{uuid.uuid4().hex[:8]}")
    filename: str
    source_path: str
    document_type: str
    file_size: int
    content_hash: str
    created_at: datetime = Field(default_factory=_now)
    ingested_at: Optional[datetime] = None
    status: DocumentStatus = DocumentStatus.REGISTERED
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @staticmethod
    def compute_hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

class DocumentBlock(BaseModel):
    block_id: str = Field(default_factory=lambda: f"blk-{uuid.uuid4().hex[:8]}")
    document_id: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    block_type: str = "text" # e.g., paragraph, heading, table
    sequence: int
    text: str

class DocumentChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: f"chk-{uuid.uuid4().hex[:8]}")
    document_id: str
    text: str
    sequence: int
    page_range: Optional[str] = None
    section: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    token_estimate: int = 0

class RetrievalResult(BaseModel):
    chunk_id: str
    document_id: str
    score: float
    text: str
    page: Optional[str] = None
    section: Optional[str] = None
    source_path: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
