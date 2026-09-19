"""Domain models for Artifacts."""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timezone

def _now() -> datetime:
    return datetime.now(timezone.utc)

class ArtifactType(str, Enum):
    MARKDOWN = "MARKDOWN"
    JSON = "JSON"
    DOCX = "DOCX"
    XLSX = "XLSX"
    PPTX = "PPTX"
    PDF = "PDF"


class ArtifactStatus(str, Enum):
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ArtifactSourceReference(BaseModel):
    """Derived provenance mapping representing where facts originated."""
    source_id: str
    locator: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ArtifactMetadata(BaseModel):
    """File and structural metadata for an artifact."""
    file_path: str
    size_bytes: int
    sections_rendered: List[str] = Field(default_factory=list)
    content_hash: str = Field(default="")

class Artifact(BaseModel):
    """Durable representation of a generated Artifact."""
    artifact_id: str = Field(default_factory=lambda: f"art-{uuid.uuid4().hex[:8]}")
    task_id: str
    title: str
    type: ArtifactType
    status: ArtifactStatus
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    source_references: List[ArtifactSourceReference] = Field(default_factory=list)
    metadata: Optional[ArtifactMetadata] = None

class ArtifactRequest(BaseModel):
    """Request to generate a new artifact."""
    task_id: str
    artifact_type: ArtifactType
    title: str
    requested_sections: List[str] = Field(default_factory=lambda: ["executive_summary", "findings", "evidence", "decisions", "unresolved_questions"])
    
    # Simple validation against known sections
    def validate_sections(self):
        allowed = {"executive_summary", "findings", "evidence", "decisions", "unresolved_questions", "limitations"}
        for sec in self.requested_sections:
            if sec not in allowed:
                raise ValueError(f"Unknown section requested: {sec}")
