import pytest
from datetime import datetime, timezone
from sovereign.core.qualification.models import (
    ModelProfile, DeploymentProfile, CapabilityContract, RuntimeEnvironment,
    QualificationIdentity, CapabilityPassport, QualificationStatus
)
from sovereign.core.authority.evaluator import AuthorityEvaluator, AuthorityPolicy
from sovereign.core.authority.models import AuthorityOutcome
from sovereign.core.qualification.engine import QualificationEngine, QualificationTestCase
from sovereign.core.state.repository import QualificationRepository, QualificationResultRecord
from sovereign.core.runtime.gateway import ModelGateway, ModelAdapter
from sovereign.core.runtime.models import InferenceResponse, RuntimeStatus, ModelInfo

def test_qualification_identity_determinism():
    model = ModelProfile(name="test_model", architecture="llama", parameters_b=8.0, context_length=4096)
    dep1 = DeploymentProfile(
        model=model,
        quantization="Q4_K_M",
        runtime=RuntimeEnvironment.LLAMA_CPP,
        hardware_profile="RTX_4090",
        context_budget=2048
    )
    dep2 = DeploymentProfile(
        model=model,
        quantization="Q4_K_M",
        runtime=RuntimeEnvironment.LLAMA_CPP,
        hardware_profile="RTX_4090",
        context_budget=2048
    )
    assert dep1.generate_identity() == dep2.generate_identity()
    
    contract1 = CapabilityContract(name="AgentDecision_v1", version="1.0")
    contract2 = CapabilityContract(name="AgentDecision_v1", version="1.0")
    assert contract1.generate_identity() == contract2.generate_identity()
    
    assert QualificationIdentity.generate(dep1, contract1) == QualificationIdentity.generate(dep2, contract2)
    
    # Changing context budget invalidates deployment identity
    dep3 = DeploymentProfile(
        model=model,
        quantization="Q4_K_M",
        runtime=RuntimeEnvironment.LLAMA_CPP,
        hardware_profile="RTX_4090",
        context_budget=4096
    )
    assert dep1.generate_identity() != dep3.generate_identity()
    assert QualificationIdentity.generate(dep1, contract1) != QualificationIdentity.generate(dep3, contract1)

def test_passport_validation():
    model = ModelProfile(name="test_model", architecture="llama", parameters_b=8.0, context_length=4096)
    dep = DeploymentProfile(
        model=model, quantization="Q4_K_M", runtime=RuntimeEnvironment.LLAMA_CPP, 
        hardware_profile="RTX", context_budget=2048
    )
    dep_id = dep.generate_identity()
    
    passport = CapabilityPassport(
        passport_id="123",
        qualification_identity="hash",
        deployment_identity=dep_id,
        capability_contract="AgentDecision_v1",
        result_id="res",
        qualification_status=QualificationStatus.QUALIFIED,
        qualification_timestamp=datetime.now(timezone.utc)
    )
    
    # Valid for exact same deployment
    assert passport.is_valid(dep)
    
    # Invalid if deployment changes
    dep_changed = DeploymentProfile(
        model=model, quantization="Q4_K_M", runtime=RuntimeEnvironment.LLAMA_CPP, 
        hardware_profile="RTX", context_budget=4096
    )
    assert not passport.is_valid(dep_changed)
    
    # Invalid if not QUALIFIED
    passport.qualification_status = QualificationStatus.UNQUALIFIED
    assert not passport.is_valid(dep)

class MockRepo(QualificationRepository):
    def save_trial(self, trial): pass
    def get_trial(self, trial_id): return None
    def list_trials(self, qual_id): return []
    def save_result(self, result): pass
    def get_result(self, result_id): return None
    def save_passport(self, passport): pass
    def get_passport(self, passport_id): return None
    def get_passport_by_identity(self, qualification_identity): return None

def test_authority_evaluator():
    policy = AuthorityPolicy(allowed_contracts=["AgentDecision_v1"], allow_unqualified=False)
    evaluator = AuthorityEvaluator(repository=MockRepo(), policy=policy)
    
    model = ModelProfile(name="test_model", architecture="llama", parameters_b=8.0, context_length=4096)
    dep = DeploymentProfile(
        model=model, quantization="Q4", runtime=RuntimeEnvironment.LLAMA_CPP, 
        hardware_profile="RTX", context_budget=2048
    )
    contract = CapabilityContract(name="AgentDecision_v1", version="1.0")
    
    # Denied Policy (Wrong Contract)
    bad_contract = CapabilityContract(name="ForbiddenContract", version="1.0")
    decision = evaluator.evaluate(dep, bad_contract, None)
    assert decision.outcome == AuthorityOutcome.DENIED_POLICY
    
    # Denied Capability (No Passport)
    decision = evaluator.evaluate(dep, contract, None)
    assert decision.outcome == AuthorityOutcome.DENIED_CAPABILITY
    
    # Granted (Valid Passport)
    passport = CapabilityPassport(
        passport_id="123",
        qualification_identity="hash",
        deployment_identity=dep.generate_identity(),
        capability_contract="AgentDecision_v1",
        result_id="res",
        qualification_status=QualificationStatus.QUALIFIED,
        qualification_timestamp=datetime.now(timezone.utc)
    )
    decision = evaluator.evaluate(dep, contract, passport)
    assert decision.outcome == AuthorityOutcome.AUTHORITY_GRANTED

class MockAdapter(ModelAdapter):
    def __init__(self, succeed: bool):
        self.succeed = succeed
    def get_status(self): return RuntimeStatus.READY
    def get_model_info(self): return ModelInfo(name="m", path="p", backend="b", device="d", gpu_layers=1, context_size=1)
    def generate(self, req):
        if self.succeed:
            return InferenceResponse(text="valid", usage={}, stop_reason="stop")
        return InferenceResponse(text="invalid", usage={}, stop_reason="stop")
    def stream(self, req): pass

def test_qualification_engine():
    repo = MockRepo()
    
    # Test Success Case
    gateway_success = ModelGateway(adapter=MockAdapter(succeed=True))
    engine = QualificationEngine(gateway=gateway_success, repository=repo)
    
    model = ModelProfile(name="m", architecture="a", parameters_b=1, context_length=1)
    dep = DeploymentProfile(model=model, quantization="q", runtime=RuntimeEnvironment.LLAMA_CPP, hardware_profile="h", context_budget=1)
    contract = CapabilityContract(name="c", version="1", required_trials=2, pass_rate_threshold=1.0)
    
    tests = [
        QualificationTestCase("t1", "p1", lambda txt, sch: txt == "valid"),
        QualificationTestCase("t2", "p2", lambda txt, sch: txt == "valid"),
    ]
    
    passport = engine.run_qualification(dep, contract, tests)
    assert passport.qualification_status == QualificationStatus.QUALIFIED
    
    # Test Failure Case
    gateway_fail = ModelGateway(adapter=MockAdapter(succeed=False))
    engine_fail = QualificationEngine(gateway=gateway_fail, repository=repo)
    passport_fail = engine_fail.run_qualification(dep, contract, tests)
    assert passport_fail.qualification_status == QualificationStatus.UNQUALIFIED
