from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from sovereign.core.capabilities.models import ToolDefinition, ToolImplementation, CapabilityType
from sovereign.infrastructure.tools.workspace import TaskWorkspace, WorkspaceManager
from sovereign.infrastructure.tools.execution_boundary import ExecutionBoundary

class ExecutePythonInput(BaseModel):
    code: str = Field(description="The Python code to execute within the restricted task workspace.")
    timeout_seconds: float = Field(default=10.0, description="Maximum execution time in seconds (max 30.0s).")


def get_execute_python_tool(
    execution_boundary: Optional[ExecutionBoundary] = None,
    workspace: Optional[TaskWorkspace] = None
) -> ToolImplementation:
    boundary = execution_boundary or ExecutionBoundary()
    ws = workspace or WorkspaceManager().get_or_create("default")

    def handler(inputs: ExecutePythonInput) -> Dict[str, Any]:
        return boundary.execute_python(
            code=inputs.code,
            workspace=ws,
            timeout_seconds=inputs.timeout_seconds
        )

    definition = ToolDefinition(
        tool_id="core-exec-001",
        name="execute_python",
        description="Executes Python code in a restricted execution environment with hard timeout, sanitized environment, and output bounding.",
        input_schema=ExecutePythonInput.model_json_schema(),
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "stdout": {"type": "string"},
                "stderr": {"type": "string"},
                "exit_code": {"type": "integer"},
                "duration_ms": {"type": "integer"},
                "security_mode": {"type": "string"},
                "error": {"type": ["string", "null"]}
            }
        },
        capability=CapabilityType.MUTATING
    )
    return ToolImplementation(
        definition=definition,
        handler=handler,
        input_model=ExecutePythonInput
    )
