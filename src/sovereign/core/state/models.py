"""Domain models for persistent task state."""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timezone

def _now() -> datetime:
    return datetime.now(timezone.utc)

class TaskStatus(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class Priority(int, Enum):
    # Higher value = higher priority
    LOW = 1
    NORMAL = 2
    HIGH = 3
    REQUIRED = 4

class EvidenceReference(BaseModel):
    """Reference to evidence, NOT the parsed document itself."""
    evidence_id: str = Field(default_factory=lambda: f"ev-{uuid.uuid4().hex[:8]}")
    source_id: str
    locator: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)

class StateItemBase(BaseModel):
    item_id: str = Field(default_factory=lambda: f"item-{uuid.uuid4().hex[:8]}")
    priority: Priority = Priority.NORMAL
    evidence_refs: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

class Finding(StateItemBase):
    item_type: str = "finding"
    statement: str
    confidence: str = "unknown"
    status: str = "active"

class UnresolvedQuestion(StateItemBase):
    item_type: str = "question"
    question: str
    status: str = "open"

class Decision(StateItemBase):
    item_type: str = "decision"
    rationale: str
    decision: str

# Union for persistence typing
StateItem = Union[Finding, UnresolvedQuestion, Decision]

class Checkpoint(BaseModel):
    checkpoint_id: str = Field(default_factory=lambda: f"cp-{uuid.uuid4().hex[:8]}")
    task_id: str
    description: str
    created_at: datetime = Field(default_factory=_now)

class Task(BaseModel):
    task_id: str = Field(default_factory=lambda: f"task-{uuid.uuid4().hex[:8]}")
    title: str
    goal: str
    status: TaskStatus = TaskStatus.CREATED
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    current_checkpoint_id: Optional[str] = None

class ContextSnapshot(BaseModel):
    """Record of what the Context Manager chose to provide."""
    task_id: str
    current_instruction: str
    selected_item_ids: List[str]
    omitted_item_ids: List[str]
    selected_evidence_ids: List[str]
    token_estimate: int
    available_budget: int
    required_items_count: int
    omitted_priorities: List[str]
    created_at: datetime = Field(default_factory=_now)
