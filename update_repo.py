import re

with open('src/sovereign/core/state/repository.py', 'r') as f:
    content = f.read()

new_content = \"\"\"
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, ContextManager
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
\"\"\"

content = content + \"\\n\" + new_content

with open('src/sovereign/core/state/repository.py', 'w') as f:
    f.write(content)
