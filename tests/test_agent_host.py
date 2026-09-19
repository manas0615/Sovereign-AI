import pytest
import tempfile
import sqlite3
from pathlib import Path

from sovereign.core.state.models import TaskStatus, Task


from sovereign.core.agent.host import AgentHost
from sovereign.core.state.repository import TaskRepository
from sovereign.core.state.context_manager import ContextManager
from sovereign.core.runtime.gateway import ModelGateway
from sovereign.core.runtime.models import InferenceRequest, InferenceResponse
from sovereign.core.knowledge.retriever import Retriever
from sovereign.core.capabilities.executor import ToolExecutor
from sovereign.core.capabilities.registry import ToolRegistry
from sovereign.core.capabilities.policy import ToolPolicy
from sovereign.infrastructure.state.sqlite_repository import SQLiteTaskRepository
from sovereign.infrastructure.state.tokenizer import ApproximateTokenCounter
from sovereign.core.knowledge.models import RetrievalResult
from sovereign.core.capabilities.models import ToolResult

# --- FAKES ---

class FakeModelGateway(ModelGateway):
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0
        
    def generate(self, request: InferenceRequest) -> InferenceResponse:
        if self.call_count >= len(self.responses):
            return InferenceResponse(text='{"action": "FINAL", "answer": "Out of fake responses"}', usage={}, stop_reason="stop")
        resp = self.responses[self.call_count]
        self.call_count += 1
        if isinstance(resp, Exception):
            raise resp
        return InferenceResponse(text=resp, usage={}, stop_reason="stop")

class FakeRetriever(Retriever):
    def __init__(self, results, fail=False):
        self.results = results
        self.fail = fail
        
    def retrieve(self, query: str, top_k: int = 5, document_id=None):
        if self.fail:
            raise Exception("Fake retrieval failure")
        return self.results[:top_k]

class FakeToolExecutor(ToolExecutor):
    def __init__(self, results_dict, fail=False):
        self.results_dict = results_dict
        self.fail = fail
        
    def execute(self, tool_name: str, inputs: dict, timeout=None):
        if self.fail:
            raise Exception("Fake tool failure")
        return self.results_dict.get(tool_name, ToolResult(
            execution_id="123", tool_name=tool_name, success=False, error="ToolNotFound"
        ))

# --- FIXTURES ---

@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = Path(f.name)
    yield path
    path.unlink(missing_ok=True)

@pytest.fixture
def repo(temp_db):
    return SQLiteTaskRepository(db_path=temp_db)

@pytest.fixture
def context_manager(repo):
    return ContextManager(repository=repo, tokenizer=ApproximateTokenCounter())

# --- TESTS ---

def test_infinite_loop(repo, context_manager):
    # Model continually returns CONTINUE
    fake_model = FakeModelGateway(['{"action": "CONTINUE", "rationale": "Thinking..."}'] * 10)
    fake_retriever = FakeRetriever([])
    fake_tool = FakeToolExecutor({})
    
    host = AgentHost(
        model_gateway=fake_model,
        context_manager=context_manager,
        task_repository=repo,
        retriever=fake_retriever,
        tool_executor=fake_tool,
        max_iterations=3
    )
    
    task = host.create_task("Loop forever")
    host.run(task.task_id)
    
    task = repo.get_task(task.task_id)
    assert task.status == TaskStatus.FAILED
    # Ensure it stopped at max_iterations
    assert fake_model.call_count == 3
    # Look at last decision
    decisions = [i for i in repo.get_state_items(task.task_id) if i.item_type == "decision"]
    assert decisions[-1].decision == "FAIL"
    assert "Max iterations" in decisions[-1].rationale

def test_retrieval_loop_and_final(repo, context_manager):
    # Model requests RETRIEVE, then FINAL
    fake_model = FakeModelGateway([
        '{"action": "RETRIEVE", "query": "P-101"}',
        '{"action": "FINAL", "answer": "P-101 is fine"}'
    ])
    fake_retriever = FakeRetriever([
        RetrievalResult(chunk_id="c1", document_id="d1", score=1.0, text="P-101 finding", source_path="doc.txt", page="37")
    ])
    fake_tool = FakeToolExecutor({})
    
    host = AgentHost(fake_model, context_manager, repo, fake_retriever, fake_tool)
    
    task = host.create_task("Check P-101")
    host.run(task.task_id)
    
    task = repo.get_task(task.task_id)
    assert task.status == TaskStatus.COMPLETED
    
    # Check evidence was persisted
    evidence = repo.get_evidence(task.task_id)
    assert len(evidence) == 1
    assert evidence[0].locator == "37"

def test_tool_loop(repo, context_manager):
    fake_model = FakeModelGateway([
        '{"action": "TOOL", "tool_name": "local_time", "arguments": {}}',
        '{"action": "FINAL", "answer": "Time is 12:00"}'
    ])
    fake_retriever = FakeRetriever([])
    fake_tool = FakeToolExecutor({
        "local_time": ToolResult(execution_id="123", tool_name="local_time", success=True, output="12:00", metadata={})
    })
    
    host = AgentHost(fake_model, context_manager, repo, fake_retriever, fake_tool)
    
    task = host.create_task("What time is it?")
    host.run(task.task_id)
    
    task = repo.get_task(task.task_id)
    assert task.status == TaskStatus.COMPLETED
    
    findings = [i for i in repo.get_state_items(task.task_id) if i.item_type == "finding"]
    assert len(findings) == 2 # 1 for tool, 1 for final answer
    assert "local_time" in findings[0].statement

def test_unauthorized_tool(repo, context_manager):
    # Simulate ToolExecutor failing policy (success=False, error=ToolNotAllowed)
    fake_model = FakeModelGateway([
        '{"action": "TOOL", "tool_name": "unknown_tool", "arguments": {}}',
        '{"action": "FINAL", "answer": "I failed"}'
    ])
    fake_retriever = FakeRetriever([])
    fake_tool = FakeToolExecutor({
        "unknown_tool": ToolResult(execution_id="1", tool_name="unknown", success=False, error="ToolNotAllowed")
    })
    
    host = AgentHost(fake_model, context_manager, repo, fake_retriever, fake_tool)
    task = host.create_task("Run unknown")
    host.run(task.task_id)
    
    # Tool output is recorded as a failure finding, model gets it in next context, decides FINAL.
    task = repo.get_task(task.task_id)
    assert task.status == TaskStatus.COMPLETED
    findings = [i for i in repo.get_state_items(task.task_id) if i.item_type == "finding"]
    assert "ToolNotAllowed" in findings[0].statement

def test_malformed_model_output(repo, context_manager):
    fake_model = FakeModelGateway([
        '{invalid_json}'
    ])
    fake_retriever = FakeRetriever([])
    fake_tool = FakeToolExecutor({})
    
    host = AgentHost(fake_model, context_manager, repo, fake_retriever, fake_tool)
    task = host.create_task("Do it")
    host.run(task.task_id)
    
    task = repo.get_task(task.task_id)
    assert task.status == TaskStatus.FAILED
    decisions = [i for i in repo.get_state_items(task.task_id) if i.item_type == "decision"]
    assert "Malformed model output" in decisions[-1].rationale

def test_model_failure(repo, context_manager):
    fake_model = FakeModelGateway([
        Exception("LLM down")
    ])
    fake_retriever = FakeRetriever([])
    fake_tool = FakeToolExecutor({})
    
    host = AgentHost(fake_model, context_manager, repo, fake_retriever, fake_tool)
    task = host.create_task("Do it")
    host.run(task.task_id)
    
    task = repo.get_task(task.task_id)
    assert task.status == TaskStatus.FAILED
    decisions = [i for i in repo.get_state_items(task.task_id) if i.item_type == "decision"]
    assert "Model invocation failed" in decisions[-1].rationale

def test_retrieval_failure(repo, context_manager):
    fake_model = FakeModelGateway([
        '{"action": "RETRIEVE", "query": "x"}'
    ])
    fake_retriever = FakeRetriever([], fail=True)
    fake_tool = FakeToolExecutor({})
    
    host = AgentHost(fake_model, context_manager, repo, fake_retriever, fake_tool)
    task = host.create_task("Do it")
    host.run(task.task_id)
    
    task = repo.get_task(task.task_id)
    assert task.status == TaskStatus.FAILED
    decisions = [i for i in repo.get_state_items(task.task_id) if i.item_type == "decision"]
    assert "Retrieval failed" in decisions[-1].rationale

def test_tool_executor_exception(repo, context_manager):
    fake_model = FakeModelGateway([
        '{"action": "TOOL", "tool_name": "t", "arguments": {}}'
    ])
    fake_retriever = FakeRetriever([])
    fake_tool = FakeToolExecutor({}, fail=True)
    
    host = AgentHost(fake_model, context_manager, repo, fake_retriever, fake_tool)
    task = host.create_task("Do it")
    host.run(task.task_id)
    
    task = repo.get_task(task.task_id)
    assert task.status == TaskStatus.FAILED
    decisions = [i for i in repo.get_state_items(task.task_id) if i.item_type == "decision"]
    assert "Tool executor exception" in decisions[-1].rationale

def test_restart_resume(temp_db):
    repo1 = SQLiteTaskRepository(temp_db)
    cm1 = ContextManager(repo1, ApproximateTokenCounter())
    fake_model1 = FakeModelGateway([
        '{"action": "RETRIEVE", "query": "x"}'
    ])
    fake_retriever1 = FakeRetriever([
        RetrievalResult(chunk_id="c1", document_id="d1", score=1.0, text="P-101 finding", source_path="doc.txt", page="37")
    ])
    host1 = AgentHost(fake_model1, cm1, repo1, fake_retriever1, FakeToolExecutor({}), max_iterations=1)
    
    task = host1.create_task("Do it")
    # This will do RETRIEVE, then hit max_iterations=1, so it fails, but evidence is persisted.
    host1.run(task.task_id)
    
    # Process 2
    repo2 = SQLiteTaskRepository(temp_db)
    cm2 = ContextManager(repo2, ApproximateTokenCounter())
    fake_model2 = FakeModelGateway([
        '{"action": "FINAL", "answer": "Done"}'
    ])
    host2 = AgentHost(fake_model2, cm2, repo2, FakeRetriever([]), FakeToolExecutor({}))
    
    # Manually reset status to allow resume (in real life, maybe a resume method does this)
    loaded_task = repo2.get_task(task.task_id)
    loaded_task.status = TaskStatus.ACTIVE
    repo2.update_task(loaded_task)
    
    host2.run(task.task_id)
    
    final_task = repo2.get_task(task.task_id)
    assert final_task.status == TaskStatus.COMPLETED
    assert len(repo2.get_evidence(task.task_id)) == 1

def test_context_pressure(repo, context_manager):
    # Inject 100+ findings and evidence
    task = Task(title="Pressure test", goal="Pressure test")
    repo.create_task(task)
    repo.update_task(task)
    
    from sovereign.core.state.models import Finding, EvidenceReference
    for i in range(150):
        repo.add_state_item(task.task_id, Finding(statement=f"Finding {i} " * 50, confidence="high"))
        repo.add_evidence(task.task_id, EvidenceReference(source_id="d1", locator="p1", metadata={"text": f"Evidence {i} " * 50}))
        
    fake_model = FakeModelGateway([
        '{"action": "FINAL", "answer": "ok"}'
    ])
    fake_retriever = FakeRetriever([])
    fake_tool = FakeToolExecutor({})
    
    host = AgentHost(fake_model, context_manager, repo, fake_retriever, fake_tool)
    host.run(task.task_id)
    
    # Verify the snapshot passed to the model Gateway
    # Since we don't have direct observability into prompt size easily without hooking the fake model:
    assert task.status == TaskStatus.FAILED
    # Ensure it stopped at max_iterations
    assert fake_model.call_count == 3
    # Look at last decision
    decisions = [i for i in repo.get_state_items(task.task_id) if i.item_type == "decision"]
    assert decisions[-1].decision == "FAIL"
    assert "Max iterations" in decisions[-1].rationale

def test_retrieval_loop_and_final(repo, context_manager):
    # Model requests RETRIEVE, then FINAL
    fake_model = FakeModelGateway([
        '{"action": "RETRIEVE", "query": "P-101"}',
        '{"action": "FINAL", "answer": "P-101 is fine"}'
    ])
    fake_retriever = FakeRetriever([
        RetrievalResult(chunk_id="c1", document_id="d1", score=1.0, text="P-101 finding", source_path="doc.txt", page="37")
    ])
    fake_tool = FakeToolExecutor({})
    
    host = AgentHost(fake_model, context_manager, repo, fake_retriever, fake_tool)
    
    task = host.create_task("Check P-101")
    host.run(task.task_id)
    
    task = repo.get_task(task.task_id)
    assert task.status == TaskStatus.COMPLETED
    
    # Check evidence was persisted
    evidence = repo.get_evidence(task.task_id)
    assert len(evidence) == 1
    assert evidence[0].locator == "37"

def test_tool_loop(repo, context_manager):
    fake_model = FakeModelGateway([
        '{"action": "TOOL", "tool_name": "local_time", "arguments": {}}',
        '{"action": "FINAL", "answer": "Time is 12:00"}'
    ])
    fake_retriever = FakeRetriever([])
    fake_tool = FakeToolExecutor({
        "local_time": ToolResult(execution_id="123", tool_name="local_time", success=True, output="12:00", metadata={})
    })
    
    host = AgentHost(fake_model, context_manager, repo, fake_retriever, fake_tool)
    
    task = host.create_task("What time is it?")
    host.run(task.task_id)
    
    task = repo.get_task(task.task_id)
    assert task.status == TaskStatus.COMPLETED
    
    findings = [i for i in repo.get_state_items(task.task_id) if i.item_type == "finding"]
    assert len(findings) == 2 # 1 for tool, 1 for final answer
    assert "local_time" in findings[0].statement

def test_unauthorized_tool(repo, context_manager):
    # Simulate ToolExecutor failing policy (success=False, error=ToolNotAllowed)
    fake_model = FakeModelGateway([
        '{"action": "TOOL", "tool_name": "unknown_tool", "arguments": {}}',
        '{"action": "FINAL", "answer": "I failed"}'
    ])
    fake_retriever = FakeRetriever([])
    fake_tool = FakeToolExecutor({
        "unknown_tool": ToolResult(execution_id="1", tool_name="unknown", success=False, error="ToolNotAllowed")
    })
    
    host = AgentHost(fake_model, context_manager, repo, fake_retriever, fake_tool)
    task = host.create_task("Run unknown")
    host.run(task.task_id)
    
    # Tool output is recorded as a failure finding, model gets it in next context, decides FINAL.
    task = repo.get_task(task.task_id)
    assert task.status == TaskStatus.COMPLETED
    findings = [i for i in repo.get_state_items(task.task_id) if i.item_type == "finding"]
    assert "ToolNotAllowed" in findings[0].statement

def test_malformed_model_output(repo, context_manager):
    fake_model = FakeModelGateway([
        '{invalid_json}'
    ])
    fake_retriever = FakeRetriever([])
    fake_tool = FakeToolExecutor({})
    
    host = AgentHost(fake_model, context_manager, repo, fake_retriever, fake_tool)
    task = host.create_task("Do it")
    host.run(task.task_id)
    
    task = repo.get_task(task.task_id)
    assert task.status == TaskStatus.FAILED
    decisions = [i for i in repo.get_state_items(task.task_id) if i.item_type == "decision"]
    assert "Malformed model output" in decisions[-1].rationale

def test_model_failure(repo, context_manager):
    fake_model = FakeModelGateway([
        Exception("LLM down")
    ])
    fake_retriever = FakeRetriever([])
    fake_tool = FakeToolExecutor({})
    
    host = AgentHost(fake_model, context_manager, repo, fake_retriever, fake_tool)
    task = host.create_task("Do it")
    host.run(task.task_id)
    
    task = repo.get_task(task.task_id)
    assert task.status == TaskStatus.FAILED
    decisions = [i for i in repo.get_state_items(task.task_id) if i.item_type == "decision"]
    assert "Model invocation failed" in decisions[-1].rationale

def test_retrieval_failure(repo, context_manager):
    fake_model = FakeModelGateway([
        '{"action": "RETRIEVE", "query": "x"}'
    ])
    fake_retriever = FakeRetriever([], fail=True)
    fake_tool = FakeToolExecutor({})
    
    host = AgentHost(fake_model, context_manager, repo, fake_retriever, fake_tool)
    task = host.create_task("Do it")
    host.run(task.task_id)
    
    task = repo.get_task(task.task_id)
    assert task.status == TaskStatus.FAILED
    decisions = [i for i in repo.get_state_items(task.task_id) if i.item_type == "decision"]
    assert "Retrieval failed" in decisions[-1].rationale

def test_tool_executor_exception(repo, context_manager):
    fake_model = FakeModelGateway([
        '{"action": "TOOL", "tool_name": "t", "arguments": {}}'
    ])
    fake_retriever = FakeRetriever([])
    fake_tool = FakeToolExecutor({}, fail=True)
    
    host = AgentHost(fake_model, context_manager, repo, fake_retriever, fake_tool)
    task = host.create_task("Do it")
    host.run(task.task_id)
    
    task = repo.get_task(task.task_id)
    assert task.status == TaskStatus.FAILED
    decisions = [i for i in repo.get_state_items(task.task_id) if i.item_type == "decision"]
    assert "Tool executor exception" in decisions[-1].rationale

def test_restart_resume(temp_db):
    repo1 = SQLiteTaskRepository(temp_db)
    cm1 = ContextManager(repo1, ApproximateTokenCounter())
    fake_model1 = FakeModelGateway([
        '{"action": "RETRIEVE", "query": "x"}'
    ])
    fake_retriever1 = FakeRetriever([
        RetrievalResult(chunk_id="c1", document_id="d1", score=1.0, text="P-101 finding", source_path="doc.txt", page="37")
    ])
    host1 = AgentHost(fake_model1, cm1, repo1, fake_retriever1, FakeToolExecutor({}), max_iterations=1)
    
    task = host1.create_task("Do it")
    # This will do RETRIEVE, then hit max_iterations=1, so it fails, but evidence is persisted.
    host1.run(task.task_id)
    
    # Process 2
    repo2 = SQLiteTaskRepository(temp_db)
    cm2 = ContextManager(repo2, ApproximateTokenCounter())
    fake_model2 = FakeModelGateway([
        '{"action": "FINAL", "answer": "Done"}'
    ])
    host2 = AgentHost(fake_model2, cm2, repo2, FakeRetriever([]), FakeToolExecutor({}))
    
    # Manually reset status to allow resume (in real life, maybe a resume method does this)
    loaded_task = repo2.get_task(task.task_id)
    loaded_task.status = TaskStatus.ACTIVE
    repo2.update_task(loaded_task)
    
    host2.run(task.task_id)
    
    final_task = repo2.get_task(task.task_id)
    assert final_task.status == TaskStatus.COMPLETED
    assert len(repo2.get_evidence(task.task_id)) == 1

def test_context_pressure(repo, context_manager):
    # Inject 100+ findings and evidence
    task = Task(title="Pressure test", goal="Pressure test")
    repo.create_task(task)
    repo.update_task(task)
    
    from sovereign.core.state.models import Finding, EvidenceReference
    for i in range(150):
        repo.add_state_item(task.task_id, Finding(statement=f"Finding {i} " * 50, confidence="high"))
        repo.add_evidence(task.task_id, EvidenceReference(source_id="d1", locator="p1", metadata={"text": f"Evidence {i} " * 50}))
        
    fake_model = FakeModelGateway([
        '{"action": "FINAL", "answer": "ok"}'
    ])
    fake_retriever = FakeRetriever([])
    fake_tool = FakeToolExecutor({})
    
    host = AgentHost(fake_model, context_manager, repo, fake_retriever, fake_tool)
    host.run(task.task_id)
    
    # Verify the snapshot passed to the model Gateway
    # Since we don't have direct observability into prompt size easily without hooking the fake model:
    # Let's rebuild the snapshot and assert token count.
    snapshot = context_manager.assemble_context(task.task_id, task.goal)
    token_count = context_manager._tokenizer.count_tokens(snapshot.model_dump_json(indent=2))
    assert token_count <= context_manager._calculate_working_budget()
    
    final_task = repo.get_task(task.task_id)
    assert final_task.status == TaskStatus.COMPLETED

def test_model_gateway_integration_boundary(repo, context_manager):
    # This test verifies that AgentHost properly constructs an InferenceRequest
    # and processes an InferenceResponse when using the real ModelGateway abstraction
    # backed by a compliant adapter.
    from sovereign.core.runtime.gateway import ModelAdapter
    from sovereign.core.runtime.models import InferenceRequest, InferenceResponse, RuntimeStatus, ModelInfo
    
    class FakeAdapter(ModelAdapter):
        def __init__(self):
            self.last_request = None
            
        def get_status(self):
            return RuntimeStatus.READY
            
        def get_model_info(self):
            return ModelInfo(name="fake", path="fake", backend="fake", device="cpu", gpu_layers=0, context_size=8192)
            
        def generate(self, request: InferenceRequest) -> InferenceResponse:
            self.last_request = request
            # Return a valid AgentDecision JSON string wrapped in an InferenceResponse
            return InferenceResponse(text='{"action": "FINAL", "answer": "adapter works"}', usage={"tokens": 10}, stop_reason="stop")
            
        def stream(self, request: InferenceRequest):
            pass

    adapter = FakeAdapter()
    real_gateway = ModelGateway(adapter)
    fake_retriever = FakeRetriever([])
    fake_tool = FakeToolExecutor({})
    
    host = AgentHost(real_gateway, context_manager, repo, fake_retriever, fake_tool)
    task = host.create_task("Test gateway boundary")
    host.run(task.task_id)
    
    # Verify AgentHost extracted the response correctly and parsed the AgentDecision
    final_task = repo.get_task(task.task_id)
    assert final_task.status == TaskStatus.COMPLETED
    
    # Verify the InferenceRequest was properly constructed and passed down
    assert adapter.last_request is not None
    assert isinstance(adapter.last_request, InferenceRequest)
    assert "Test gateway boundary" in adapter.last_request.prompt
    assert adapter.last_request.response_format is not None
    assert adapter.last_request.response_format["type"] == "json_schema"
    assert adapter.last_request.response_format["json_schema"]["name"] == "AgentDecision"

def test_agent_decision_schema_structure():
    from sovereign.core.agent.models import AGENT_DECISION_RESPONSE_FORMAT, AGENT_DECISION_SCHEMA
    assert AGENT_DECISION_RESPONSE_FORMAT["type"] == "json_schema"
    assert AGENT_DECISION_RESPONSE_FORMAT["json_schema"]["strict"] is True
    assert "oneOf" in AGENT_DECISION_SCHEMA
    actions = [b["properties"]["action"]["const"] for b in AGENT_DECISION_SCHEMA["oneOf"]]
    assert set(actions) == {"FINAL", "RETRIEVE", "TOOL", "CLARIFY", "CONTINUE"}

