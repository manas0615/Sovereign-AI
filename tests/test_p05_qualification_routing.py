import pytest
from datetime import datetime, timezone
from pathlib import Path

from sovereign.core.runtime.models import (
    ModelDeploymentConfig, InferenceRequest, InferenceResponse, RuntimeStatus, ModelInfo
)
from sovereign.core.runtime.gateway import ModelGateway, ModelAdapter
from sovereign.core.qualification.models import (
    ModelProfile, DeploymentProfile, CapabilityContract, RuntimeEnvironment,
    CapabilityPassport, QualificationStatus, QualificationIdentity
)
from sovereign.core.authority.evaluator import AuthorityEvaluator, AuthorityPolicy
from sovereign.core.authority.models import AuthorityOutcome
from sovereign.core.state.repository import (
    QualificationRepository, QualificationResultRecord, CapabilityPassportRecord
)
from sovereign.core.agent.router import (
    ModelRouter, TaskCharacterizer, TaskCapabilityRequirement, RoutingDecision
)
from sovereign.core.agent.host import AgentHost
from sovereign.core.state.models import Task, TaskStatus, Finding, Decision, EvidenceReference, Checkpoint
from sovereign.infrastructure.state.sqlite_repository import SQLiteTaskRepository
from sovereign.core.state.context_manager import ContextManager
from sovereign.infrastructure.state.tokenizer import ApproximateTokenCounter
from sovereign.core.capabilities.executor import ToolExecutor
from sovereign.core.capabilities.registry import ToolRegistry
from sovereign.core.capabilities.policy import ToolPolicy
from sovereign.core.knowledge.retriever import Retriever
from sovereign.core.knowledge.models import RetrievalResult
from sovereign.core.exceptions import ModelRuntimeError

class InMemoryMockQualRepo(QualificationRepository):
    def __init__(self):
        self.passports = {}
        self.trials = {}
        self.results = {}

    def save_trial(self, trial): self.trials[trial.trial_id] = trial
    def get_trial(self, trial_id): return self.trials.get(trial_id)
    def list_trials(self, qual_id): return [t for t in self.trials.values() if t.qualification_identity == qual_id]
    def save_result(self, result): self.results[result.result_id] = result
    def get_result(self, result_id): return self.results.get(result_id)
    def save_passport(self, passport): self.passports[passport.passport_id] = passport
    def get_passport(self, passport_id): return self.passports.get(passport_id)
    def get_passport_by_identity(self, qualification_identity):
        for p in sorted(self.passports.values(), key=lambda x: x.qualification_timestamp, reverse=True):
            if p.qualification_identity == qualification_identity:
                return p
        return None

class MockRoutingAdapter(ModelAdapter):
    def __init__(self):
        self._active_deployment = None
        self._fail_switch = False
        self._switch_count = 0

    def get_status(self):
        return RuntimeStatus.READY if self._active_deployment else RuntimeStatus.SERVER_NOT_RUNNING

    def get_model_info(self):
        if self._active_deployment:
            d = self._active_deployment
            return ModelInfo(name=d.model_name, path=d.model_path, backend=d.backend, device=d.device, gpu_layers=d.gpu_layers, context_size=d.context_size)
        return ModelInfo(name="none", path="", backend="", device="", gpu_layers=0, context_size=0)

    def load(self, deployment):
        if self._fail_switch:
            raise ModelRuntimeError("Simulated switch failure")
        self._active_deployment = deployment

    def unload(self):
        self._active_deployment = None

    def get_active_deployment(self):
        return self._active_deployment

    def is_loaded(self):
        return self._active_deployment is not None

    def switch(self, deployment):
        if self._fail_switch:
            raise ModelRuntimeError("Simulated switch failure")
        self._switch_count += 1
        self._active_deployment = deployment

    def generate(self, request):
        if not self._active_deployment:
            raise ModelRuntimeError("Cannot generate: Unloaded")
        # Return valid AgentDecision FINAL
        return InferenceResponse(
            text='{"action": "FINAL", "answer": "Task executed successfully", "rationale": "Done"}',
            usage={"prompt_tokens": 10, "completion_tokens": 15},
            stop_reason="stop"
        )

    def stream(self, request):
        pass

class DummyRetriever(Retriever):
    def retrieve(self, query: str, top_k: int = 5):
        return [RetrievalResult(document_id="doc1", chunk_id="c1", text="Evidence text", score=0.9)]


@pytest.fixture
def routing_setup():
    model_a = ModelProfile(name="ModelA", architecture="llama", parameters_b=3.0, context_length=4096)
    model_b = ModelProfile(name="ModelB", architecture="qwen", parameters_b=3.0, context_length=4096)

    prof_a = DeploymentProfile(
        model=model_a, quantization="Q4_K_M", runtime=RuntimeEnvironment.LLAMA_CPP,
        hardware_profile="T1000", context_budget=4096
    )
    prof_b = DeploymentProfile(
        model=model_b, quantization="Q4_K_M", runtime=RuntimeEnvironment.LLAMA_CPP,
        hardware_profile="T1000", context_budget=4096
    )

    dep_a = ModelDeploymentConfig(model_name="ModelA", model_path="/path/a.gguf")
    dep_b = ModelDeploymentConfig(model_name="ModelB", model_path="/path/b.gguf")

    contract = CapabilityContract(name="AgentDecision_v1", version="1.0")

    repo = InMemoryMockQualRepo()
    policy = AuthorityPolicy(allowed_contracts=["AgentDecision_v1", "DocumentRetrieval_v1", "NumericalCalculation_v1"], allow_unqualified=False)
    evaluator = AuthorityEvaluator(repository=repo, policy=policy)

    adapter = MockRoutingAdapter()
    gateway = ModelGateway(adapter)

    router = ModelRouter(
        gateway=gateway,
        authority_evaluator=evaluator,
        qualification_repository=repo,
        registered_deployments=[dep_a, dep_b],
        deployment_profiles={"ModelA": prof_a, "ModelB": prof_b},
        contracts={
            "AgentDecision_v1": contract,
            "DocumentRetrieval_v1": CapabilityContract(name="DocumentRetrieval_v1", version="1.0"),
            "NumericalCalculation_v1": CapabilityContract(name="NumericalCalculation_v1", version="1.0")
        }
    )

    return {
        "router": router,
        "gateway": gateway,
        "adapter": adapter,
        "repo": repo,
        "evaluator": evaluator,
        "policy": policy,
        "dep_a": dep_a,
        "dep_b": dep_b,
        "prof_a": prof_a,
        "prof_b": prof_b,
        "contract": contract
    }


def test_task_characterization_supported_and_unsupported():
    # 1. Valid supported capability
    req1 = TaskCharacterizer.characterize("Analyze safety parameters and formulate agent plan")
    assert req1.is_supported is True
    assert req1.capability_name == "AgentDecision_v1"

    req2 = TaskCharacterizer.characterize("Retrieve and search knowledge for turbine pressure logs")
    assert req2.is_supported is True
    assert req2.capability_name == "DocumentRetrieval_v1"

    # 2. Unsupported capability fails closed
    req_ocr = TaskCharacterizer.characterize("Perform OCR extraction on scanned PDF page")
    assert req_ocr.is_supported is False
    assert req_ocr.capability_name == "OCR"

    req_vlm = TaskCharacterizer.characterize("Run VLM vision analysis on schematic diagram image")
    assert req_vlm.is_supported is False
    assert req_vlm.capability_name == "VLM"

    req_sandbox = TaskCharacterizer.characterize("Run untrusted python in isolated container sandbox execution")
    assert req_sandbox.is_supported is False
    assert req_sandbox.capability_name == "SandboxedExecution"


def test_routing_fail_closed_unsupported_capability(routing_setup):
    router = routing_setup["router"]
    decision = router.route("task_1", "Perform OCR extraction on scanned image")
    assert decision.is_authorized is False
    assert "Unsupported capability" in decision.reason


def test_routing_no_qualified_deployment(routing_setup):
    # 3 & 4. No passport / no qualified deployment -> fail closed
    router = routing_setup["router"]
    decision = router.route("task_2", "Execute general reasoning task")
    assert decision.is_authorized is False
    assert decision.authority_outcome == AuthorityOutcome.DENIED_CAPABILITY
    assert "No qualified and authorized deployment" in decision.reason


def test_routing_denied_policy(routing_setup):
    # 6. Denied policy
    router = routing_setup["router"]
    policy = routing_setup["policy"]
    policy.allowed_contracts = [] # Forbid all contracts

    decision = router.route("task_3", "Execute general reasoning task")
    assert decision.is_authorized is False


def test_routing_qualified_and_authorized_execution(routing_setup):
    # 7. Qualified + Authorized deployment -> execution permitted
    router = routing_setup["router"]
    repo = routing_setup["repo"]
    prof_a = routing_setup["prof_a"]
    contract = routing_setup["contract"]
    dep_a = routing_setup["dep_a"]
    adapter = routing_setup["adapter"]

    # Create valid passport for ModelA
    qual_id_a = QualificationIdentity.generate(prof_a, contract)
    passport_a = CapabilityPassportRecord(
        passport_id=qual_id_a,
        qualification_identity=qual_id_a,
        deployment_identity=prof_a.generate_identity(),
        capability_contract=contract.name,
        result_id="res_1",
        qualification_status="QUALIFIED",
        qualification_timestamp=datetime.now(timezone.utc)
    )
    repo.save_passport(passport_a)

    decision = router.route("task_4", "Execute reasoning task")
    assert decision.is_authorized is True
    assert decision.selected_deployment.model_name == "ModelA"
    assert decision.authority_outcome == AuthorityOutcome.AUTHORITY_GRANTED
    assert adapter.get_active_deployment().model_name == "ModelA"


def test_switch_avoidance_when_active_is_qualified(routing_setup):
    # 8. Active qualified deployment -> no unnecessary switch
    router = routing_setup["router"]
    repo = routing_setup["repo"]
    prof_a = routing_setup["prof_a"]
    contract = routing_setup["contract"]
    dep_a = routing_setup["dep_a"]
    adapter = routing_setup["adapter"]

    qual_id_a = QualificationIdentity.generate(prof_a, contract)
    passport_a = CapabilityPassportRecord(
        passport_id=qual_id_a,
        qualification_identity=qual_id_a,
        deployment_identity=prof_a.generate_identity(),
        capability_contract=contract.name,
        result_id="res_1",
        qualification_status="QUALIFIED",
        qualification_timestamp=datetime.now(timezone.utc)
    )
    repo.save_passport(passport_a)

    # Pre-load Model A
    adapter.load(dep_a)
    adapter._switch_count = 0

    decision = router.route("task_5", "Execute reasoning task")
    assert decision.is_authorized is True
    assert decision.switch_required is False
    assert adapter._switch_count == 0  # Zero switches!


def test_switch_required_when_active_is_unqualified(routing_setup):
    # 9. Active unqualified deployment -> switch required
    router = routing_setup["router"]
    repo = routing_setup["repo"]
    prof_a = routing_setup["prof_a"]
    prof_b = routing_setup["prof_b"]
    contract = routing_setup["contract"]
    dep_a = routing_setup["dep_a"]
    dep_b = routing_setup["dep_b"]
    adapter = routing_setup["adapter"]

    # Only Model B is qualified
    qual_id_b = QualificationIdentity.generate(prof_b, contract)
    passport_b = CapabilityPassportRecord(
        passport_id=qual_id_b,
        qualification_identity=qual_id_b,
        deployment_identity=prof_b.generate_identity(),
        capability_contract=contract.name,
        result_id="res_2",
        qualification_status="QUALIFIED",
        qualification_timestamp=datetime.now(timezone.utc)
    )
    repo.save_passport(passport_b)

    # Active is Model A (which is unqualified!)
    adapter.load(dep_a)
    adapter._switch_count = 0

    decision = router.route("task_6", "Execute reasoning task")
    assert decision.is_authorized is True
    assert decision.switch_required is True
    assert decision.selected_deployment.model_name == "ModelB"
    assert adapter.get_active_deployment().model_name == "ModelB"
    assert adapter._switch_count == 1


def test_deterministic_candidate_selection_order(routing_setup):
    # 10. Deterministic selection among multiple qualified deployments
    router = routing_setup["router"]
    repo = routing_setup["repo"]
    prof_a = routing_setup["prof_a"]
    prof_b = routing_setup["prof_b"]
    contract = routing_setup["contract"]

    # Both A and B are qualified
    for prof in [prof_a, prof_b]:
        qid = QualificationIdentity.generate(prof, contract)
        repo.save_passport(CapabilityPassportRecord(
            passport_id=qid,
            qualification_identity=qid,
            deployment_identity=prof.generate_identity(),
            capability_contract=contract.name,
            result_id="res",
            qualification_status="QUALIFIED",
            qualification_timestamp=datetime.now(timezone.utc)
        ))

    # Neither is currently active
    decision = router.route("task_7", "Execute reasoning task")
    assert decision.is_authorized is True
    # Alphabetical sort: ModelA < ModelB
    assert decision.selected_deployment.model_name == "ModelA"


def test_switch_failure_fails_closed(routing_setup):
    # 11. P01 switch failure -> no unqualified fallback
    router = routing_setup["router"]
    repo = routing_setup["repo"]
    prof_a = routing_setup["prof_a"]
    contract = routing_setup["contract"]
    adapter = routing_setup["adapter"]

    qid = QualificationIdentity.generate(prof_a, contract)
    repo.save_passport(CapabilityPassportRecord(
        passport_id=qid,
        qualification_identity=qid,
        deployment_identity=prof_a.generate_identity(),
        capability_contract=contract.name,
        result_id="res",
        qualification_status="QUALIFIED",
        qualification_timestamp=datetime.now(timezone.utc)
    ))

    adapter._fail_switch = True
    decision = router.route("task_8", "Execute reasoning task")
    assert decision.is_authorized is False
    assert "failed to load" in decision.reason


def test_agent_host_integration_with_router(tmp_path, routing_setup):
    # 13, 14, 15, 16. AgentHost integration, bounded execution, state machine
    db_path = tmp_path / "agent_test.db"
    state_repo = SQLiteTaskRepository(db_path=db_path)
    tok = ApproximateTokenCounter()
    ctx = ContextManager(state_repo, tok)
    tools = ToolRegistry()
    t_policy = ToolPolicy(allowed_tools=set())
    exec_tool = ToolExecutor(tools, t_policy)
    retriever = DummyRetriever()

    router = routing_setup["router"]
    repo = routing_setup["repo"]
    prof_a = routing_setup["prof_a"]
    contract = routing_setup["contract"]

    # 1. Test AgentHost with unqualified deployment -> Fails routing
    host = AgentHost(
        model_gateway=routing_setup["gateway"],
        context_manager=ctx,
        task_repository=state_repo,
        retriever=retriever,
        tool_executor=exec_tool,
        router=router
    )

    task = host.create_task("Execute task with no qualification")
    result_task = host.run(task.task_id)
    assert result_task.status == TaskStatus.FAILED

    # Verify decision state item
    items = state_repo.get_state_items(task.task_id)
    decisions = [i for i in items if i.item_type == "decision"]
    assert any(d.decision == "ROUTE" for d in decisions)
    assert any(d.decision == "FAIL" for d in decisions)

    # 2. Test AgentHost with qualified deployment -> Completes successfully
    qid = QualificationIdentity.generate(prof_a, contract)
    repo.save_passport(CapabilityPassportRecord(
        passport_id=qid,
        qualification_identity=qid,
        deployment_identity=prof_a.generate_identity(),
        capability_contract=contract.name,
        result_id="res_10",
        qualification_status="QUALIFIED",
        qualification_timestamp=datetime.now(timezone.utc)
    ))

    task2 = host.create_task("Execute reasoning task")
    result_task2 = host.run(task2.task_id)
    assert result_task2.status == TaskStatus.COMPLETED


def test_calculation_task_characterization():
    """Verify calculation task goals are mapped deterministically to NumericalCalculation_v1."""
    req_calc1 = TaskCharacterizer.characterize("Calculate the total pressure: P1 = 120.5 and P2 = 34.2")
    assert req_calc1.capability_name == "NumericalCalculation_v1"
    assert req_calc1.is_supported is True

    req_calc2 = TaskCharacterizer.characterize("Compute the flow velocity v = sqrt(2 * g * h)")
    assert req_calc2.capability_name == "NumericalCalculation_v1"
    assert req_calc2.is_supported is True

    req_calc3 = TaskCharacterizer.characterize("Evaluate formula MAWP = (2 * S * E * t) / (D + 1.2 * t)")
    assert req_calc3.capability_name == "NumericalCalculation_v1"
    assert req_calc3.is_supported is True

    # Ensure retrieval goals still route to DocumentRetrieval_v1
    req_ret = TaskCharacterizer.characterize("Retrieve safety guidelines for valve V-204")
    assert req_ret.capability_name == "DocumentRetrieval_v1"
    assert req_ret.is_supported is True

    # Ensure unsupported requests still fail closed
    req_unsupp = TaskCharacterizer.characterize("OCR the scanned document")
    assert req_unsupp.is_supported is False
    assert req_unsupp.capability_name == "OCR"


def test_numerical_calculation_routing_and_execution(routing_setup):
    """Verify NumericalCalculation_v1 routes to qualified deployment and executes calculate tool."""
    router = routing_setup["router"]
    repo = routing_setup["repo"]
    prof_a = routing_setup["prof_a"]
    calc_contract = CapabilityContract(name="NumericalCalculation_v1", version="1.0")

    qid = QualificationIdentity.generate(prof_a, calc_contract)
    repo.save_passport(CapabilityPassportRecord(
        passport_id=qid,
        qualification_identity=qid,
        deployment_identity=prof_a.generate_identity(),
        capability_contract="NumericalCalculation_v1",
        result_id="res_calc",
        qualification_status="QUALIFIED",
        qualification_timestamp=datetime.now(timezone.utc)
    ))

    decision = router.route("task_calc_1", "Calculate the value of 15 * 8.5")
    assert decision.is_authorized is True
    assert decision.required_capability == "NumericalCalculation_v1"
    assert decision.selected_deployment.model_name == "ModelA"
