import pytest
import time
from pathlib import Path
from pydantic import BaseModel

from sovereign.core.capabilities.models import ToolDefinition, ToolImplementation, CapabilityType, ToolResult
from sovereign.core.capabilities.registry import ToolRegistry
from sovereign.core.capabilities.policy import ToolPolicy
from sovereign.core.capabilities.executor import ToolExecutor

from sovereign.infrastructure.tools.local_time_tool import get_local_time_tool
from sovereign.infrastructure.tools.file_metadata_tool import get_file_metadata_tool
from sovereign.infrastructure.paths import get_workspace_root

# --- DUMMY TOOLS FOR TESTING ---
class DummyInput(BaseModel):
    value: str

def dummy_handler(inputs: DummyInput) -> str:
    return f"Processed {inputs.value}"

def hanging_handler(inputs: DummyInput) -> str:
    time.sleep(2)
    return "Done"
    
def destructive_handler(inputs: DummyInput) -> str:
    return "BOOM"

def get_dummy_tool(tool_id: str, name: str, capability: CapabilityType, enabled: bool = True, handler=dummy_handler) -> ToolImplementation:
    definition = ToolDefinition(
        tool_id=tool_id,
        name=name,
        description="Dummy",
        input_schema=DummyInput.model_json_schema(),
        output_schema={"type": "string"},
        capability=capability,
        enabled=enabled
    )
    return ToolImplementation(
        definition=definition,
        handler=handler,
        input_model=DummyInput
    )

@pytest.fixture
def registry():
    r = ToolRegistry()
    r.register(get_local_time_tool())
    r.register(get_file_metadata_tool())
    return r

@pytest.fixture
def policy():
    # Only allowlist local_time and get_file_metadata explicitly
    return ToolPolicy(allowed_tools={"local_time", "get_file_metadata", "dummy_allowed"})

@pytest.fixture
def executor(registry, policy):
    return ToolExecutor(registry=registry, policy=policy, default_timeout=1.0)


# --- REGISTRATION AND POLICY TESTS ---

def test_duplicate_registration(registry):
    with pytest.raises(ValueError, match="Tool collision"):
        registry.register(get_local_time_tool())

def test_unknown_tool_denied(executor):
    result = executor.execute("unknown_tool", {})
    assert not result.success
    assert "ToolNotFound" in result.error

def test_disabled_tool_denied(registry, policy):
    registry.register(get_dummy_tool("d1", "dummy_allowed", CapabilityType.READ_ONLY, enabled=False))
    executor = ToolExecutor(registry, policy)
    result = executor.execute("dummy_allowed", {"value": "x"})
    assert not result.success
    assert "ToolNotAllowed" in result.error

def test_unallowlisted_tool_denied(registry, policy):
    # Registered, enabled, but NOT in allowlist
    registry.register(get_dummy_tool("d2", "not_in_allowlist", CapabilityType.READ_ONLY, enabled=True))
    executor = ToolExecutor(registry, policy)
    result = executor.execute("not_in_allowlist", {"value": "x"})
    assert not result.success
    assert "ToolNotAllowed" in result.error

def test_destructive_capability_denied(registry, policy):
    # In allowlist, but has DESTRUCTIVE capability
    policy.allowed_tools.add("nuke_tool")
    registry.register(get_dummy_tool("d3", "nuke_tool", CapabilityType.DESTRUCTIVE, enabled=True, handler=destructive_handler))
    executor = ToolExecutor(registry, policy)
    result = executor.execute("nuke_tool", {"value": "x"})
    assert not result.success
    assert "ToolNotAllowed" in result.error

def test_invalid_input_validation(registry, policy):
    registry.register(get_dummy_tool("d4", "dummy_allowed", CapabilityType.READ_ONLY, enabled=True))
    executor = ToolExecutor(registry, policy)
    
    # Missing required field "value"
    result = executor.execute("dummy_allowed", {})
    assert not result.success
    assert "ToolInputValidationError" in result.error

def test_tool_timeout(registry, policy):
    registry.register(get_dummy_tool("d5", "dummy_allowed", CapabilityType.READ_ONLY, enabled=True, handler=hanging_handler))
    # Timeout is 1.0, handler sleeps for 2.0
    executor = ToolExecutor(registry, policy, default_timeout=0.1)
    
    start = time.time()
    result = executor.execute("dummy_allowed", {"value": "x"})
    duration = time.time() - start
    
    assert not result.success
    assert "ToolTimeout" in result.error
    assert duration < 0.5  # The executor must return quickly

# --- FILESYSTEM SECURITY TESTS ---

def test_file_metadata_success(executor):
    # Create a safe file in workspace
    safe_file = get_workspace_root() / "test_safe.txt"
    safe_file.write_text("hello")
    try:
        result = executor.execute("get_file_metadata", {"filepath": str(safe_file)})
        assert result.success
        assert result.output["filename"] == "test_safe.txt"
        assert result.output["size_bytes"] == 5
    finally:
        safe_file.unlink(missing_ok=True)

def test_file_metadata_path_traversal(executor):
    # Attempt to traverse up out of the workspace
    # e.g., workspace_root / ../../Windows/System32/cmd.exe
    traversal_path = str(get_workspace_root() / ".." / ".." / "Windows" / "System32" / "cmd.exe")
    result = executor.execute("get_file_metadata", {"filepath": traversal_path})
    assert not result.success
    assert "ToolExecutionError" in result.error
    assert "outside allowed boundary" in result.error or "Path cannot be resolved" in result.error

def test_file_metadata_outside_root(executor):
    # Absolute path outside root
    result = executor.execute("get_file_metadata", {"filepath": "C:\\Windows\\System32\\notepad.exe"})
    assert not result.success
    assert "outside allowed boundary" in result.error or "Path cannot be resolved" in result.error

def test_file_metadata_unc_path(executor):
    # UNC path
    result = executor.execute("get_file_metadata", {"filepath": "\\\\localhost\\c$\\Windows"})
    assert not result.success
    # Either outside boundary or specifically rejected
    assert "ToolExecutionError" in result.error

# --- KNOWLEDGE SEARCH TEST ---

def test_search_knowledge_bounded(executor):
    from sovereign.infrastructure.tools.knowledge_search_tool import get_search_knowledge_tool
    executor.registry.register(get_search_knowledge_tool())
    executor.policy.allowed_tools.add("search_knowledge")
    
    # Request 1000 results
    result = executor.execute("search_knowledge", {"query": "test", "top_k": 1000})
    assert result.success
    # The tool caps it internally to 20
    assert len(result.output) <= 20
