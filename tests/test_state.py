import pytest
import sqlite3
import tempfile
from pathlib import Path
from sovereign.core.state.models import (
    Task, TaskStatus, Finding, Priority, EvidenceReference, Checkpoint
)
from sovereign.infrastructure.state.sqlite_repository import SQLiteTaskRepository
from sovereign.core.exceptions import StateError

@pytest.fixture
def temp_db_path():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = Path(f.name)
    yield path
    path.unlink(missing_ok=True)

@pytest.fixture
def repo(temp_db_path):
    return SQLiteTaskRepository(db_path=temp_db_path)

def test_task_lifecycle(repo):
    task = Task(title="Test Task", goal="Testing lifecycle")
    
    # Create
    repo.create_task(task)
    
    # Retrieve
    retrieved = repo.get_task(task.task_id)
    assert retrieved is not None
    assert retrieved.title == "Test Task"
    assert retrieved.status == TaskStatus.CREATED
    
    # Update
    retrieved.status = TaskStatus.ACTIVE
    repo.update_task(retrieved)
    
    updated = repo.get_task(task.task_id)
    assert updated.status == TaskStatus.ACTIVE

def test_structured_state(repo):
    task = Task(title="State Test", goal="Testing state")
    repo.create_task(task)
    
    finding = Finding(statement="The pump is vibrating.", priority=Priority.HIGH)
    repo.add_state_item(task.task_id, finding)
    
    items = repo.get_state_items(task.task_id)
    assert len(items) == 1
    assert isinstance(items[0], Finding)
    assert items[0].statement == "The pump is vibrating."
    assert items[0].priority == Priority.HIGH
    
    items[0].statement = "The pump is vibrating severely."
    repo.update_state_item(task.task_id, items[0])
    
    updated_items = repo.get_state_items(task.task_id)
    assert updated_items[0].statement == "The pump is vibrating severely."

def test_evidence_references(repo):
    task = Task(title="Evidence Test", goal="Testing evidence")
    repo.create_task(task)
    
    ev = EvidenceReference(source_id="doc-123", locator="page 5")
    repo.add_evidence(task.task_id, ev)
    
    evidence_list = repo.get_evidence(task.task_id)
    assert len(evidence_list) == 1
    assert evidence_list[0].source_id == "doc-123"
    assert evidence_list[0].locator == "page 5"
    
    finding = Finding(statement="See page 5", evidence_refs=[ev.evidence_id])
    repo.add_state_item(task.task_id, finding)
    
    items = repo.get_state_items(task.task_id)
    assert ev.evidence_id in items[0].evidence_refs

def test_checkpoints(repo):
    task = Task(title="Checkpoint Test", goal="Testing checkpoints")
    repo.create_task(task)
    
    checkpoint = Checkpoint(task_id=task.task_id, description="Initial state")
    repo.create_checkpoint(checkpoint)
    
    task.current_checkpoint_id = checkpoint.checkpoint_id
    repo.update_task(task)
    
    updated_task = repo.get_task(task.task_id)
    assert updated_task.current_checkpoint_id == checkpoint.checkpoint_id

def test_transactions_and_rollback(repo):
    task = Task(title="Transaction Test", goal="Testing rollback")
    repo.create_task(task)
    
    try:
        with repo.transaction() as conn:
            # 1. Add finding
            finding = Finding(statement="Valid finding")
            repo.add_state_item(task.task_id, finding, conn=conn)
            
            # 2. Add invalid evidence (violates constraint because missing required field implicitly)
            # Actually we'll just simulate a crash to ensure rollback
            raise ValueError("Simulated crash")
    except StateError:
        pass
        
    items = repo.get_state_items(task.task_id)
    # Finding should be rolled back
    assert len(items) == 0

def test_restart_persistence(temp_db_path):
    repo1 = SQLiteTaskRepository(db_path=temp_db_path)
    task = Task(title="Persistence Test", goal="Testing restart")
    repo1.create_task(task)
    
    finding = Finding(statement="Will I survive?")
    repo1.add_state_item(task.task_id, finding)
    
    # Close repo1 explicitly
    # Now simulate a restart by creating a new repository instance pointing to the same file
    repo2 = SQLiteTaskRepository(db_path=temp_db_path)
    
    retrieved_task = repo2.get_task(task.task_id)
    assert retrieved_task is not None
    assert retrieved_task.title == "Persistence Test"
    
    items = repo2.get_state_items(task.task_id)
    assert len(items) == 1
    assert items[0].statement == "Will I survive?"
