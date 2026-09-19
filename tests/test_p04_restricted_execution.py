import pytest
import os
import sys
import time
from pathlib import Path

from sovereign.core.capabilities.models import CapabilityType, SecurityMode, ToolResult
from sovereign.core.capabilities.registry import ToolRegistry
from sovereign.core.capabilities.policy import ToolPolicy
from sovereign.core.capabilities.executor import ToolExecutor

from sovereign.infrastructure.tools.workspace import TaskWorkspace, WorkspaceManager
from sovereign.infrastructure.tools.execution_boundary import ExecutionBoundary
from sovereign.infrastructure.tools.file_tools import (
    get_read_file_tool,
    get_write_file_tool,
    get_create_file_tool,
    get_list_workspace_tool
)
from sovereign.infrastructure.tools.python_execution_tool import get_execute_python_tool
from sovereign.infrastructure.tools.calculation_tool import get_calculate_tool
from sovereign.infrastructure.tools.local_time_tool import get_local_time_tool
from sovereign.infrastructure.tools.file_metadata_tool import get_file_metadata_tool
from sovereign.infrastructure.tools.knowledge_search_tool import get_search_knowledge_tool

@pytest.fixture
def temp_workspace(tmp_path):
    ws = TaskWorkspace(root_path=tmp_path / "test_task_ws", max_files=10)
    yield ws
    ws.cleanup()

@pytest.fixture
def execution_boundary():
    return ExecutionBoundary()

# -------------------------------------------------------------
# 1. WORKSPACE CONFINEMENT TESTS
# -------------------------------------------------------------

def test_workspace_safe_file_lifecycle(temp_workspace):
    # Create file
    create_res = temp_workspace.create_file("report.txt", "Initial content")
    assert create_res["filepath"] == "report.txt"
    assert create_res["bytes_written"] > 0

    # Read file
    read_res = temp_workspace.read_file("report.txt")
    assert read_res["content"] == "Initial content"
    assert read_res["truncated"] is False

    # Write (append)
    write_res = temp_workspace.write_file("report.txt", "\nSecond line", mode="a")
    assert write_res["bytes_written"] > 0

    # Read updated
    read_res2 = temp_workspace.read_file("report.txt")
    assert "Initial content\nSecond line" in read_res2["content"]

    # List workspace
    listing = temp_workspace.list_files()
    names = [f["name"] for f in listing]
    assert "report.txt" in names

def test_workspace_path_traversal_blocked(temp_workspace):
    with pytest.raises(PermissionError, match="outside workspace boundary"):
        temp_workspace.resolve_safe_path("../secret.txt")

    with pytest.raises(PermissionError, match="outside workspace boundary"):
        temp_workspace.resolve_safe_path("../../Windows/System32/calc.exe")

def test_workspace_absolute_paths_blocked(temp_workspace):
    with pytest.raises(PermissionError, match="outside workspace boundary|Absolute paths"):
        temp_workspace.resolve_safe_path("C:\\Windows\\notepad.exe")

    with pytest.raises(PermissionError, match="outside workspace boundary|Absolute paths"):
        temp_workspace.resolve_safe_path("/etc/passwd")

def test_workspace_unc_paths_blocked(temp_workspace):
    with pytest.raises(PermissionError, match="UNC or network paths are forbidden"):
        temp_workspace.resolve_safe_path("\\\\server\\share\\data.txt")

def test_workspace_max_files_enforced(temp_workspace):
    for i in range(10):
        temp_workspace.create_file(f"file_{i}.txt", f"data {i}")

    with pytest.raises(RuntimeError, match="Maximum file count limit"):
        temp_workspace.create_file("file_overflow.txt", "too many")

def test_workspace_read_size_bounding(temp_workspace):
    large_content = "X" * 500
    temp_workspace.create_file("large.txt", large_content)
    read_res = temp_workspace.read_file("large.txt", max_bytes=100)
    assert read_res["truncated"] is True
    assert len(read_res["content"]) == 100

# -------------------------------------------------------------
# 2. RESTRICTED EXECUTION BOUNDARY TESTS
# -------------------------------------------------------------

def test_execution_boundary_python_success(execution_boundary, temp_workspace):
    code = """
import sys
print("Computation Complete")
"""
    res = execution_boundary.execute_python(code, temp_workspace, timeout_seconds=5.0)
    assert res["success"] is True
    assert "Computation Complete" in res["stdout"]
    assert res["exit_code"] == 0
    assert res["security_mode"] in [SecurityMode.ISOLATED.value, SecurityMode.DEGRADED.value]

def test_execution_boundary_python_error(execution_boundary, temp_workspace):
    code = """
raise ValueError("Invalid operation")
"""
    res = execution_boundary.execute_python(code, temp_workspace, timeout_seconds=5.0)
    assert res["success"] is False
    assert "ValueError: Invalid operation" in res["stderr"]
    assert res["exit_code"] != 0

def test_execution_boundary_timeout_teardown(execution_boundary, temp_workspace):
    code = """
import time
time.sleep(5)
print("Should not reach here")
"""
    start = time.time()
    res = execution_boundary.execute_python(code, temp_workspace, timeout_seconds=0.5)
    duration = time.time() - start

    assert res["success"] is False
    assert "ExecutionTimeout" in res["error"]
    assert duration < 3.0

def test_execution_boundary_environment_sanitization(execution_boundary, temp_workspace, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-key-12345")
    monkeypatch.setenv("SOVEREIGN_AUTH_TOKEN", "token-xyz")

    code = """
import os
print("API_KEY:", os.environ.get("OPENAI_API_KEY", "NOT_FOUND"))
print("TOKEN:", os.environ.get("SOVEREIGN_AUTH_TOKEN", "NOT_FOUND"))
print("MODE:", os.environ.get("SOVEREIGN_SANDBOX_MODE", "NOT_FOUND"))
"""
    res = execution_boundary.execute_python(code, temp_workspace, timeout_seconds=5.0)
    assert res["success"] is True
    assert "API_KEY: NOT_FOUND" in res["stdout"]
    assert "TOKEN: NOT_FOUND" in res["stdout"]
    assert "MODE: DEGRADED" in res["stdout"] or "MODE: ISOLATED" in res["stdout"]

def test_execution_boundary_output_truncation(temp_workspace):
    boundary = ExecutionBoundary(max_output_bytes=50)
    code = """
print("A" * 200)
"""
    res = boundary.execute_python(code, temp_workspace, timeout_seconds=5.0)
    assert res["success"] is True
    assert len(res["stdout"]) < 200
    assert "[Output Truncated" in res["stdout"]

# -------------------------------------------------------------
# 3. GOVERNED LOCAL TOOLS & POLICY TESTS
# -------------------------------------------------------------

def test_governed_tools_full_suite(temp_workspace, execution_boundary):
    registry = ToolRegistry()
    registry.register(get_read_file_tool(temp_workspace))
    registry.register(get_write_file_tool(temp_workspace))
    registry.register(get_create_file_tool(temp_workspace))
    registry.register(get_list_workspace_tool(temp_workspace))
    registry.register(get_execute_python_tool(execution_boundary, temp_workspace))
    registry.register(get_calculate_tool(execution_boundary, temp_workspace))
    registry.register(get_local_time_tool())
    registry.register(get_file_metadata_tool())

    policy = ToolPolicy(allowed_tools={
        "read_file", "write_file", "create_file", "list_workspace",
        "execute_python", "calculate", "local_time", "get_file_metadata"
    })

    executor = ToolExecutor(registry=registry, policy=policy, default_timeout=10.0)

    # 1. Create file
    r1 = executor.execute("create_file", {"filepath": "notes.txt", "content": "Initial notes."})
    assert r1.success is True

    # 2. Write file
    r2 = executor.execute("write_file", {"filepath": "notes.txt", "content": " Extra information.", "mode": "a"})
    assert r2.success is True

    # 3. Read file
    r3 = executor.execute("read_file", {"filepath": "notes.txt"})
    assert r3.success is True
    assert "Initial notes. Extra information." in r3.output["content"]

    # 4. List workspace
    r4 = executor.execute("list_workspace", {})
    assert r4.success is True
    assert any(f["name"] == "notes.txt" for f in r4.output)

    # 5. Execute python
    py_code = """
with open('notes.txt', 'r') as f:
    text = f.read()
print(f"WORD_COUNT:{len(text.split())}")
"""
    r5 = executor.execute("execute_python", {"code": py_code})
    assert r5.success is True
    assert "WORD_COUNT:4" in r5.output["stdout"]
    assert r5.security_mode in [SecurityMode.ISOLATED, SecurityMode.DEGRADED]

    # 6. Calculate
    r6 = executor.execute("calculate", {"expression": "sqrt(144) + 8 * 2"})
    assert r6.success is True
    assert r6.output["result"] == 28.0
    assert r6.security_mode in [SecurityMode.ISOLATED, SecurityMode.DEGRADED]

    # 7. Calculate with variables
    r7 = executor.execute("calculate", {"expression": "price * quantity * (1 - discount)", "variables": {"price": 100.0, "quantity": 3.0, "discount": 0.1}})
    assert r7.success is True
    assert round(r7.output["result"], 2) == 270.0

def test_calculate_malicious_rejections(execution_boundary, temp_workspace):
    registry = ToolRegistry()
    registry.register(get_calculate_tool(execution_boundary, temp_workspace))
    policy = ToolPolicy(allowed_tools={"calculate"})
    executor = ToolExecutor(registry=registry, policy=policy)

    malicious_exprs = [
        "__import__('os').system('echo hacked')",
        "__import__('subprocess').Popen('calc.exe')",
        "open('test.txt', 'w')",
        "eval('1+1')",
        "exec('a=1')",
        "globals()",
        "locals()",
        "getattr(math, 'pi')",
        "object.__subclasses__()",
        "(1).__class__",
        "os.system('dir')"
    ]
    
    for expr in malicious_exprs:
        res = executor.execute("calculate", {"expression": expr})
        assert res.success is True
        assert res.output["success"] is False
        err = str(res.output.get("error", ""))
        assert "not allowed" in err or "Unsupported" in err or "not defined" in err or "Only simple function calls" in err or "syntax" in err.lower()

def test_execution_boundary_process_tree_teardown(execution_boundary, temp_workspace):
    if os.name != "nt":
        pytest.skip("Process tree teardown test specific to Windows nt for this check")
        
    import subprocess
    def is_pid_alive(pid):
        try:
            out = subprocess.check_output(["tasklist", "/FI", f"PID eq {pid}"], text=True)
            return str(pid) in out
        except Exception:
            return False

    code = """
import subprocess, sys, time, os
child_script = '''
import os, time
with open("child_pid.txt", "w") as f:
    f.write(str(os.getpid()))
for _ in range(60):
    time.sleep(1)
with open("child_survived.txt", "w") as f:
    f.write("alive")
'''
with open("child.py", "w") as f:
    f.write(child_script)
subprocess.Popen([sys.executable, "child.py"])
while not os.path.exists("child_pid.txt"):
    time.sleep(0.1)
time.sleep(60)
"""
    child_pid = None
    try:
        res = execution_boundary.execute_python(code, temp_workspace, timeout_seconds=3.0)
        
        assert res["success"] is False
        assert "ExecutionTimeout" in res["error"]
        
        pid_file = temp_workspace.root_path / "child_pid.txt"
        assert pid_file.exists(), "Child did not start and write PID before timeout!"
        
        child_pid = int(pid_file.read_text().strip())
        
        assert not is_pid_alive(child_pid), f"Child process {child_pid} survived parent termination!"
        
        survived = (temp_workspace.root_path / "child_survived.txt").exists()
        assert not survived, "Child process survival marker found!"
    finally:
        if child_pid and is_pid_alive(child_pid):
            subprocess.run(["taskkill", "/F", "/PID", str(child_pid)], capture_output=True)

def test_governed_tools_policy_enforcement(temp_workspace):
    registry = ToolRegistry()
    registry.register(get_read_file_tool(temp_workspace))
    registry.register(get_write_file_tool(temp_workspace))

    policy = ToolPolicy(allowed_tools={"read_file"})
    executor = ToolExecutor(registry=registry, policy=policy)

    r1 = executor.execute("read_file", {"filepath": "non_existent.txt"})
    assert r1.success is False
    assert "File not found" in r1.error

    r2 = executor.execute("write_file", {"filepath": "test.txt", "content": "data"})
    assert r2.success is False
    assert "ToolNotAllowed" in r2.error

def test_governed_tools_path_traversal_via_executor(temp_workspace):
    registry = ToolRegistry()
    registry.register(get_read_file_tool(temp_workspace))
    policy = ToolPolicy(allowed_tools={"read_file"})
    executor = ToolExecutor(registry=registry, policy=policy)

    res = executor.execute("read_file", {"filepath": "../outside.txt"})
    assert res.success is False
    assert "ToolExecutionError" in res.error
    assert "outside workspace boundary" in res.error

def test_existing_p04_tools_preserved():
    registry = ToolRegistry()
    registry.register(get_local_time_tool())
    registry.register(get_file_metadata_tool())
    registry.register(get_search_knowledge_tool())

    policy = ToolPolicy(allowed_tools={"local_time", "get_file_metadata", "search_knowledge"})
    executor = ToolExecutor(registry=registry, policy=policy)

    res_time = executor.execute("local_time", {})
    assert res_time.success is True
    assert isinstance(res_time.output, str)
    assert len(res_time.output) > 10

    res_search = executor.execute("search_knowledge", {"query": "test query", "top_k": 5})
    assert res_search.success is True


def test_app_service_tool_policy_governance():
    """Verify AppService registers calculate and enforces policy denying execute_python."""
    from sovereign.application.services import get_app_service
    svc = get_app_service()

    # Verify calculate is registered and reachable
    res_calc = svc.tool_executor.execute("calculate", {"expression": "2 * 3.14159 * 10"})
    assert res_calc.success is True
    assert res_calc.output["success"] is True
    assert round(res_calc.output["result"], 2) == 62.83

    # Verify execute_python is now explicitly allowed and registered
    res_py = svc.tool_executor.execute("execute_python", {"code": "print(1+1)"})
    assert res_py.success is True
    assert res_py.output["stdout"].strip() == "2"
