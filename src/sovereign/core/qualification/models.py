import hashlib
import json
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime, timezone

class RuntimeEnvironment(str, Enum):
    LLAMA_CPP = "llama_cpp"
    ONNX_RUNTIME = "onnx_runtime"
    TRT_LLM = "trt_llm"
    UNKNOWN = "unknown"

class QualificationStatus(str, Enum):
    QUALIFIED = "QUALIFIED"
    UNQUALIFIED = "UNQUALIFIED"
    PENDING = "PENDING"
    INVALIDATED = "INVALIDATED"

class ModelProfile(BaseModel):
    name: str
    architecture: str
    parameters_b: float
    context_length: int

class DeploymentProfile(BaseModel):
    model: ModelProfile
    quantization: str
    runtime: RuntimeEnvironment
    hardware_profile: str
    context_budget: int
    
    def generate_identity(self) -> str:
        data = {
            "m": self.model.name,
            "q": self.quantization,
            "r": self.runtime.value,
            "h": self.hardware_profile,
            "c": self.context_budget
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()

class CapabilityContract(BaseModel):
    name: str
    version: str
    expected_schema: Dict[str, Any] = Field(default_factory=dict)
    pass_rate_threshold: float = 0.95
    required_trials: int = 10
    timeout_ms: int = 30000

    def generate_identity(self) -> str:
        return hashlib.sha256(f"{self.name}:{self.version}".encode("utf-8")).hexdigest()

class QualificationIdentity:
    """Represents the deterministic hash of Deployment Profile x Capability Contract."""
    
    @staticmethod
    def generate(deployment: DeploymentProfile, contract: CapabilityContract) -> str:
        dep_id = deployment.generate_identity()
        contract_id = contract.generate_identity()
        return hashlib.sha256(f"{dep_id}:{contract_id}".encode("utf-8")).hexdigest()

class QualificationTrial(BaseModel):
    trial_id: str
    qualification_identity: str
    test_id: str
    prompt_reference: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool
    validation_outcome: str
    failure_category: Optional[str] = None
    resource_metrics: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class QualificationResult(BaseModel):
    result_id: str
    qualification_identity: str
    capability_contract: str
    deployment_identity: str
    trial_counts: Dict[str, int] = Field(default_factory=dict)
    compliance_metrics: Dict[str, float] = Field(default_factory=dict)
    resource_stability: str = "UNKNOWN"
    threshold_evaluation: str = "PENDING"
    qualification_status: QualificationStatus = QualificationStatus.PENDING
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CapabilityPassport(BaseModel):
    passport_id: str
    qualification_identity: str
    deployment_identity: str
    capability_contract: str
    result_id: str
    qualification_status: QualificationStatus
    qualification_timestamp: datetime
    invalidation_info: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_valid(self, current_deployment: DeploymentProfile) -> bool:
        if self.qualification_status != QualificationStatus.QUALIFIED:
            return False
            
        return self.deployment_identity == current_deployment.generate_identity()
