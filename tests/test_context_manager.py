import pytest
from sovereign.core.state.models import Task, Finding, EvidenceReference, Priority
from sovereign.core.state.context_manager import ContextManager
from sovereign.infrastructure.state.tokenizer import ApproximateTokenCounter
from sovereign.core.exceptions import ContextBudgetExceeded

class MockRepo:
    def __init__(self):
        self.task = None
        self.items = []
        self.evidence = []
        
    def get_task(self, task_id):
        return self.task
        
    def get_state_items(self, task_id):
        return self.items
        
    def get_evidence(self, task_id):
        return self.evidence

@pytest.fixture
def mock_repo():
    return MockRepo()

@pytest.fixture
def context_manager(mock_repo):
    tokenizer = ApproximateTokenCounter()
    return ContextManager(repository=mock_repo, tokenizer=tokenizer)

def test_budget_calculation(context_manager, monkeypatch):
    import sovereign.infrastructure.config as config
    class MockSettings:
        context_size = 8192
        reserved_system_tokens = 1000
        reserved_output_tokens = 1000
    
    monkeypatch.setattr(context_manager, "_settings", MockSettings())
    budget = context_manager._calculate_working_budget()
    assert budget == 6192

def test_context_prioritization_and_truncation(context_manager, mock_repo, monkeypatch):
    import sovereign.infrastructure.config as config
    class MockSettings:
        context_size = 500  # Extremely small budget to force truncation
        reserved_system_tokens = 100
        reserved_output_tokens = 100
    
    monkeypatch.setattr(context_manager, "_settings", MockSettings())
    
    # Working budget = 300
    task = Task(title="Test", goal="Test context") # base tokens approx ~10
    mock_repo.task = task
    
    # Create items
    # Each finding will be roughly 100 characters serialized -> 25 tokens.
    req_item = Finding(statement="This is required.", priority=Priority.REQUIRED)
    high_item = Finding(statement="This is high.", priority=Priority.HIGH)
    normal_item = Finding(statement="This is normal.", priority=Priority.NORMAL)
    
    # Let's add many low items to exceed budget
    low_items = [Finding(statement=f"This is low {i}.", priority=Priority.LOW) for i in range(20)]
    
    mock_repo.items = [req_item, high_item, normal_item] + low_items
    
    snapshot = context_manager.assemble_context(task.task_id, "Summarize.")
    
    # Required, high, and normal should be included
    assert req_item.item_id in snapshot.selected_item_ids
    assert high_item.item_id in snapshot.selected_item_ids
    assert normal_item.item_id in snapshot.selected_item_ids
    
    # Some low items should be omitted
    assert len(snapshot.omitted_item_ids) > 0
    assert Priority.LOW.name in snapshot.omitted_priorities
    assert snapshot.token_estimate <= snapshot.available_budget
    assert snapshot.required_items_count == 1

def test_context_overflow(context_manager, mock_repo, monkeypatch):
    import sovereign.infrastructure.config as config
    class MockSettings:
        context_size = 200 # tiny budget
        reserved_system_tokens = 100
        reserved_output_tokens = 100
        # Working budget = 0
    
    monkeypatch.setattr(context_manager, "_settings", MockSettings())
    
    task = Task(title="Test", goal="Test overflow")
    mock_repo.task = task
    
    # Add a required item
    req_item = Finding(statement="This is REQUIRED and very long... " * 100, priority=Priority.REQUIRED)
    mock_repo.items = [req_item]
    
    with pytest.raises(ContextBudgetExceeded):
        context_manager.assemble_context(task.task_id, "Do it.")

def test_large_task_simulation(context_manager, mock_repo, monkeypatch):
    import sovereign.infrastructure.config as config
    class MockSettings:
        context_size = 8192
        reserved_system_tokens = 1024
        reserved_output_tokens = 1024
    
    monkeypatch.setattr(context_manager, "_settings", MockSettings())
    
    task = Task(title="Large Report", goal="Analyze 100 page report.")
    mock_repo.task = task
    
    # 100 findings, 100 evidence refs
    findings = []
    evidence = []
    for i in range(100):
        ev = EvidenceReference(source_id=f"doc-{i}", locator=f"page {i}")
        evidence.append(ev)
        
        # 10 required, 20 high, 70 low
        priority = Priority.LOW
        if i < 10:
            priority = Priority.REQUIRED
        elif i < 30:
            priority = Priority.HIGH
            
        finding = Finding(
            statement=f"Simulated finding number {i} from the report with extensive detail to simulate payload size. " * 5,
            priority=priority,
            evidence_refs=[ev.evidence_id]
        )
        findings.append(finding)
        
    mock_repo.items = findings
    mock_repo.evidence = evidence
    
    snapshot = context_manager.assemble_context(task.task_id, "What are the most critical findings?")
    
    # Assert budget respected
    assert snapshot.token_estimate <= snapshot.available_budget
    
    # Assert all 10 required items are present
    assert snapshot.required_items_count == 10
    for i in range(10):
        assert findings[i].item_id in snapshot.selected_item_ids
        
    # Assert some items were omitted due to budget constraints (100 findings + 100 evidence is large)
    assert len(snapshot.omitted_item_ids) > 0
    
    # Because required/high were added first, omitted items must be from the low priority end
    omitted_priorities_set = set(snapshot.omitted_priorities)
    assert Priority.REQUIRED.name not in omitted_priorities_set
