"""Unit tests for Trusted Code Verification and failure modes.

Validates:
1. Generated code prints 'VERIFICATION_PASSED' but fails trusted tests -> Verification Failed.
2. Generated code exits 0 but does not satisfy acceptance criteria -> Verification Failed.
3. Generated code raises an exception -> Execution/Verification Failed.
4. Generated code passes trusted checks -> Verification Passed.
5. Inconclusive code without verifiable acceptance criteria -> Verification Inconclusive.
6. P04 tool policy denies unauthorized tool execution -> ToolNotAllowed.
7. Retry limit enforcement in AgentHost -> Task FAILED.
"""

import pytest
import tempfile
from pathlib import Path

from sovereign.core.coding.verifier import (
    TrustedCodeVerifier,
    CodeVerificationStatus,
    TrustedVerificationReport
)
from sovereign.infrastructure.tools.execution_boundary import ExecutionBoundary
from sovereign.infrastructure.tools.workspace import TaskWorkspace, WorkspaceManager
from sovereign.core.capabilities.models import ToolDefinition, ToolImplementation, CapabilityType
from sovereign.core.capabilities.registry import ToolRegistry
from sovereign.core.capabilities.policy import ToolPolicy
from sovereign.core.capabilities.executor import ToolExecutor


@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = TaskWorkspace("test_task", Path(tmpdir))
        yield ws


@pytest.fixture
def execution_boundary():
    return ExecutionBoundary()


def test_untrusted_print_marker_fails_when_logic_is_wrong(temp_workspace, execution_boundary):
    """
    Generated code prints 'VERIFICATION_PASSED' to stdout, but the actual email
    validation function is buggy (returns True for invalid email).
    Trusted verifier MUST report Verification Failed.
    """
    buggy_code = """
def is_valid_email(email):
    # Buggy: returns True for everything
    return True

print("VERIFICATION_PASSED")
"""
    report = TrustedCodeVerifier.verify_submission(
        code=buggy_code,
        task_goal="Write a python function is_valid_email that validates simple email format",
        workspace=temp_workspace,
        boundary=execution_boundary
    )

    assert report.status == CodeVerificationStatus.VERIFICATION_FAILED
    assert report.failed_checks > 0
    assert report.passed_checks < report.total_checks
    # Confirm untrusted print is in raw stdout but ignored by status
    assert "VERIFICATION_PASSED" in report.raw_stdout


def test_zero_exit_code_without_acceptance_criteria_does_not_pass(temp_workspace, execution_boundary):
    """
    Generated code exits with code 0 (no exceptions), but does not implement
    the required function. Trusted verifier MUST report Verification Failed.
    """
    empty_code = """
# Just a comment and empty pass
x = 42
"""
    report = TrustedCodeVerifier.verify_submission(
        code=empty_code,
        task_goal="Write a Python function is_valid_email(email) for validation",
        workspace=temp_workspace,
        boundary=execution_boundary
    )

    assert report.status == CodeVerificationStatus.VERIFICATION_FAILED
    assert report.execution_exit_code == 1 # Harness exits with 1 when checks fail
    assert any(c.check_name == "function_existence" and not c.passed for c in report.check_results)


def test_syntax_error_fails_immediately(temp_workspace, execution_boundary):
    """
    Generated code has invalid Python syntax.
    Trusted verifier MUST report Verification Failed with syntax error details.
    """
    syntax_error_code = "def is_valid_email(email) return True"
    report = TrustedCodeVerifier.verify_submission(
        code=syntax_error_code,
        task_goal="Write a Python function is_valid_email",
        workspace=temp_workspace,
        boundary=execution_boundary
    )

    assert report.status == CodeVerificationStatus.VERIFICATION_FAILED
    assert report.failed_checks == 1
    assert "SyntaxError" in (report.failure_reason or "")


def test_runtime_exception_fails_verification(temp_workspace, execution_boundary):
    """
    Generated code raises an unhandled ZeroDivisionError or Exception at runtime.
    Trusted verifier MUST report Verification Failed.
    """
    crasher_code = """
def is_valid_email(email):
    return 1 / 0
"""
    report = TrustedCodeVerifier.verify_submission(
        code=crasher_code,
        task_goal="Write a Python function is_valid_email to check emails",
        workspace=temp_workspace,
        boundary=execution_boundary
    )

    assert report.status == CodeVerificationStatus.VERIFICATION_FAILED
    assert report.failed_checks > 0
    assert any("ZeroDivisionError" in str(c.error) for c in report.check_results)


def test_correct_implementation_passes_trusted_checks(temp_workspace, execution_boundary):
    """
    Generated code implements correct regex email validation logic.
    Trusted verifier MUST report Verification Passed with all checks passing.
    """
    correct_code = """
import re

def is_valid_email(email: str) -> bool:
    if not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(pattern, email):
        return False
    if '..' in email or ' ' in email:
        return False
    return True
"""
    report = TrustedCodeVerifier.verify_submission(
        code=correct_code,
        task_goal="Write a Python function is_valid_email to check emails",
        workspace=temp_workspace,
        boundary=execution_boundary
    )

    assert report.status == CodeVerificationStatus.VERIFICATION_PASSED
    assert report.total_checks >= 6
    assert report.passed_checks == report.total_checks
    assert report.failed_checks == 0
    assert report.execution_exit_code == 0
    assert report.failure_reason is None


def test_inconclusive_task_without_acceptance_criteria(temp_workspace, execution_boundary):
    """
    Arbitrary script without recognizable benchmark goal or assertions.
    Status should be Verification Inconclusive, NOT Verification Passed.
    """
    arbitrary_code = """
import sys
print("System info:", sys.version)
"""
    report = TrustedCodeVerifier.verify_submission(
        code=arbitrary_code,
        task_goal="Print the current python system version string",
        workspace=temp_workspace,
        boundary=execution_boundary
    )

    assert report.status == CodeVerificationStatus.VERIFICATION_INCONCLUSIVE
    assert report.total_checks == 0
    assert "acceptance criteria" in (report.failure_reason or "").lower()


def test_p04_tool_policy_denies_unauthorized_execution(temp_workspace):
    """
    Verifies that ToolPolicy denies unauthorized tool names fail-closed.
    """
    registry = ToolRegistry()
    policy = ToolPolicy(allowed_tools={"calculate"}) # execute_python NOT in allowed set
    executor = ToolExecutor(registry, policy)

    res = executor.execute("execute_python", {"code": "print('exploit')"})
    assert res.success is False
    assert "ToolNotFound" in str(res.error) or "ToolNotAllowed" in str(res.error)


def test_agent_host_fails_closed_when_verification_fails():
    """
    Verifies that AgentHost marks task FAILED if FINAL action is called without
    passing trusted verification.
    """
    from sovereign.core.agent.host import AgentHost
    from sovereign.core.agent.models import AgentDecision, AgentAction
    from sovereign.core.state.models import Task, TaskStatus, Finding, Decision
    from sovereign.infrastructure.state.sqlite_repository import SQLiteTaskRepository
    from unittest.mock import MagicMock

    repo = SQLiteTaskRepository()
    task = Task(title="Test Coding", goal="Write python code for email validation")
    repo.create_task(task)

    # State has only a failed verification finding
    repo.add_state_item(task.task_id, Finding(statement="Trusted Verification Result: [Verification Failed] Passed 2/8 checks."))

    # Mock gateway returning FINAL
    mock_gateway = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"action": "FINAL", "answer": "I completed the code."}'
    mock_gateway.generate.return_value = mock_response

    mock_context = MagicMock()
    mock_snapshot = MagicMock()
    mock_snapshot.selected_item_ids = []
    mock_snapshot.selected_evidence_ids = []
    mock_snapshot.model_dump_json.return_value = "{}"
    mock_context.assemble_context.return_value = mock_snapshot

    mock_router = MagicMock()
    mock_routing = MagicMock()
    mock_routing.is_authorized = True
    mock_routing.required_capability = "AutomatedCoding_v1"
    mock_routing.reason = "Authorized"
    mock_router.route.return_value = mock_routing

    host = AgentHost(
        model_gateway=mock_gateway,
        context_manager=mock_context,
        task_repository=repo,
        retriever=MagicMock(),
        tool_executor=MagicMock(),
        router=mock_router
    )

    completed_task = host.run(task.task_id)
    # MUST be FAILED because verification was not passed
    assert completed_task.status == TaskStatus.FAILED
    decisions = [s for s in repo.get_state_items(task.task_id) if isinstance(s, Decision)]
    assert any(d.decision == "FAIL" and "trusted verification" in d.rationale for d in decisions)
