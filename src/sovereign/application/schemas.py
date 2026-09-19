"""Data Transfer Objects for the Application Boundary (Package 07)."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List

class TaskCreateRequest(BaseModel):
    title: str = Field(..., max_length=200)
    goal: str
    document_id: Optional[str] = None

class TaskResponse(BaseModel):
    task_id: str
    title: str
    goal: str
    status: str
    created_at: datetime
    updated_at: datetime
    latest_decision: Optional[str] = None
    findings_count: int = 0
    document_id: Optional[str] = None

class ArtifactMetadataResponse(BaseModel):
    artifact_id: str
    task_id: str
    title: str
    type: str
    status: str
    created_at: datetime
    filename: Optional[str] = None
    file_path: Optional[str] = None
    size_bytes: Optional[int] = None
    content_hash: Optional[str] = None
    sections_rendered: List[str] = Field(default_factory=list)
    source_references: List[Dict[str, Any]] = Field(default_factory=list)

class DocumentIngestResponse(BaseModel):
    document_id: str
    status: str

class CapabilityPassportResponse(BaseModel):
    passport_id: str
    qualification_identity: str
    deployment_identity: str
    capability_contract: str
    result_id: str
    qualification_status: str
    qualification_timestamp: datetime
    invalidation_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class DocumentDetailResponse(BaseModel):
    document_id: str
    filename: str
    source_path: str
    document_type: str
    file_size: int
    content_hash: str
    created_at: datetime
    ingested_at: Optional[datetime] = None
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentChunkResponse(BaseModel):
    chunk_id: str
    document_id: str
    sequence: int
    page_range: Optional[str] = None
    section: Optional[str] = None
    text: str
    token_estimate: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CitationItem(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    locator: str
    text: str
    score: float
    content_hash: Optional[str] = None

class CodeExecutionResult(BaseModel):
    code: str
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    success: bool
    security_mode: str
    error: Optional[str] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    document_id: Optional[str] = None
    mode: str = Field(default="chat") # "chat" | "coding" | "governed_task"
    execute_code: bool = False

class ChatResponse(BaseModel):
    message_id: str
    conversation_id: str
    role: str = "assistant"
    content: str
    citations: List[CitationItem] = Field(default_factory=list)
    code_execution: Optional[CodeExecutionResult] = None
    authority_decision: str = "AUTHORITY_GRANTED"
    authorizing_passport_id: Optional[str] = None
    deployment_identity: Optional[str] = None
    capability_contract: Optional[str] = None
    task_id: Optional[str] = None
    artifacts: List[ArtifactMetadataResponse] = Field(default_factory=list)
    created_at: datetime

class CodeExecuteRequest(BaseModel):
    code: str = Field(..., min_length=1)
    timeout_seconds: float = Field(default=10.0, le=30.0)

class CodeExecuteResponse(BaseModel):
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    security_mode: str
    error: Optional[str] = None




