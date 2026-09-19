import pytest
from datetime import datetime, timezone
from sovereign.infrastructure.state.sqlite_repository import SQLiteTaskRepository
from sovereign.core.state.repository import (
    QualificationTrialRecord,
    QualificationResultRecord,
    CapabilityPassportRecord
)

@pytest.fixture
def temp_db_path(tmp_path):
    return tmp_path / "test_state.db"

@pytest.fixture
def repo(temp_db_path):
    return SQLiteTaskRepository(db_path=temp_db_path)

def test_qualification_trial_persistence(repo):
    trial = QualificationTrialRecord(
        trial_id="trial_001",
        qualification_identity="hash123",
        test_id="test_case_1",
        prompt_reference="prompt_1",
        timestamp=datetime.now(timezone.utc),
        success=True,
        validation_outcome="PASS",
        resource_metrics={"latency_ms": 150}
    )
    repo.save_trial(trial)
    
    retrieved = repo.get_trial("trial_001")
    assert retrieved is not None
    assert retrieved.trial_id == "trial_001"
    assert retrieved.qualification_identity == "hash123"
    assert retrieved.success is True
    assert retrieved.resource_metrics["latency_ms"] == 150

def test_qualification_result_persistence(repo):
    result = QualificationResultRecord(
        result_id="res_001",
        qualification_identity="hash123",
        capability_contract="AgentDecision_v1",
        deployment_identity="dep_hash_1",
        trial_counts={"passed": 1, "failed": 0},
        compliance_metrics={"pass_rate": 1.0},
        resource_stability="STABLE",
        threshold_evaluation="PASS",
        qualification_status="QUALIFIED",
        timestamp=datetime.now(timezone.utc)
    )
    repo.save_result(result)
    
    retrieved = repo.get_result("res_001")
    assert retrieved is not None
    assert retrieved.result_id == "res_001"
    assert retrieved.qualification_status == "QUALIFIED"
    assert retrieved.trial_counts["passed"] == 1

def test_capability_passport_persistence(repo):
    result = QualificationResultRecord(
        result_id="res_002",
        qualification_identity="hash456",
        capability_contract="AgentDecision_v1",
        deployment_identity="dep_hash_1",
        trial_counts={},
        compliance_metrics={},
        resource_stability="STABLE",
        threshold_evaluation="PASS",
        qualification_status="QUALIFIED",
        timestamp=datetime.now(timezone.utc)
    )
    repo.save_result(result)
    
    passport = CapabilityPassportRecord(
        passport_id="pass_001",
        qualification_identity="hash456",
        deployment_identity="dep_hash_1",
        capability_contract="AgentDecision_v1",
        result_id="res_002",
        qualification_status="QUALIFIED",
        qualification_timestamp=datetime.now(timezone.utc),
    )
    repo.save_passport(passport)
    
    retrieved = repo.get_passport("pass_001")
    assert retrieved is not None
    assert retrieved.passport_id == "pass_001"
    assert retrieved.result_id == "res_002"
    assert retrieved.qualification_status == "QUALIFIED"

def test_multiple_qualifications(repo):
    trial1 = QualificationTrialRecord(
        trial_id="trial_002",
        qualification_identity="hash_A",
        test_id="test_case_1",
        prompt_reference="prompt_1",
        timestamp=datetime.now(timezone.utc),
        success=True,
        validation_outcome="PASS"
    )
    trial2 = QualificationTrialRecord(
        trial_id="trial_003",
        qualification_identity="hash_A",
        test_id="test_case_2",
        prompt_reference="prompt_2",
        timestamp=datetime.now(timezone.utc),
        success=False,
        validation_outcome="FAIL"
    )
    repo.save_trial(trial1)
    repo.save_trial(trial2)
    
    trials = repo.list_trials("hash_A")
    assert len(trials) == 2
    
def test_persistence_across_restart(temp_db_path):
    repo1 = SQLiteTaskRepository(db_path=temp_db_path)
    result = QualificationResultRecord(
        result_id="res_003",
        qualification_identity="hash_B",
        capability_contract="AgentDecision_v1",
        deployment_identity="dep_hash_B",
        trial_counts={},
        compliance_metrics={},
        resource_stability="STABLE",
        threshold_evaluation="FAIL",
        qualification_status="UNQUALIFIED",
        timestamp=datetime.now(timezone.utc)
    )
    repo1.save_result(result)
    
    repo2 = SQLiteTaskRepository(db_path=temp_db_path)
    retrieved = repo2.get_result("res_003")
    assert retrieved is not None
    assert retrieved.qualification_status == "UNQUALIFIED"
