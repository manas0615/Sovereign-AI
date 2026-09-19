"""Repository interface for persistent state."""

from abc import ABC, abstractmethod
from typing import List, Optional, ContextManager
from sovereign.core.state.models import (
    Task, StateItem, EvidenceReference, Checkpoint
)

class TaskRepository(ABC):
    
    @abstractmethod
    def transaction(self) -> ContextManager:
        """Returns a context manager for atomic transactions."""
        pass

    @abstractmethod
    def create_task(self, task: Task) -> None:
        pass
        
    @abstractmethod
    def get_task(self, task_id: str) -> Optional[Task]:
        pass
        
    @abstractmethod
    def list_tasks(self) -> List[Task]:
        pass

    @abstractmethod
    def update_task(self, task: Task) -> None:
        pass

        
    @abstractmethod
    def add_state_item(self, task_id: str, item: StateItem) -> None:
        pass
        
    @abstractmethod
    def update_state_item(self, task_id: str, item: StateItem) -> None:
        pass

    @abstractmethod
    def get_state_items(self, task_id: str) -> List[StateItem]:
        pass
        
    @abstractmethod
    def add_evidence(self, task_id: str, evidence: EvidenceReference) -> None:
        pass
        
    @abstractmethod
    def get_evidence(self, task_id: str) -> List[EvidenceReference]:
        pass

    @abstractmethod
    def create_checkpoint(self, checkpoint: Checkpoint) -> None:
        pass


from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class QualificationTrialRecord(BaseModel):
    trial_id: str
    qualification_identity: str
    test_id: str
    prompt_reference: str
    timestamp: datetime
    success: bool
    validation_outcome: str
    failure_category: Optional[str] = None
    resource_metrics: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class QualificationResultRecord(BaseModel):
    result_id: str
    qualification_identity: str
    capability_contract: str
    deployment_identity: str
    trial_counts: Dict[str, int] = Field(default_factory=dict)
    compliance_metrics: Dict[str, float] = Field(default_factory=dict)
    resource_stability: str
    threshold_evaluation: str
    qualification_status: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CapabilityPassportRecord(BaseModel):
    passport_id: str
    qualification_identity: str
    deployment_identity: str
    capability_contract: str
    result_id: str
    qualification_status: str
    qualification_timestamp: datetime
    invalidation_info: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class QualificationRepository(ABC):
    @abstractmethod
    def save_trial(self, trial: QualificationTrialRecord) -> None:
        pass

    @abstractmethod
    def get_trial(self, trial_id: str) -> Optional[QualificationTrialRecord]:
        pass

    @abstractmethod
    def list_trials(self, qualification_identity: str) -> List[QualificationTrialRecord]:
        pass

    @abstractmethod
    def save_result(self, result: QualificationResultRecord) -> None:
        pass

    @abstractmethod
    def get_result(self, result_id: str) -> Optional[QualificationResultRecord]:
        pass

    @abstractmethod
    def save_passport(self, passport: CapabilityPassportRecord) -> None:
        pass

    @abstractmethod
    def get_passport(self, passport_id: str) -> Optional[CapabilityPassportRecord]:
        pass

    @abstractmethod
    def get_passport_by_identity(self, qualification_identity: str) -> Optional[CapabilityPassportRecord]:
        pass
