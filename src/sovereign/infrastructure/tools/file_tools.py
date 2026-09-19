from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from sovereign.core.capabilities.models import ToolDefinition, ToolImplementation, CapabilityType
from sovereign.infrastructure.tools.workspace import TaskWorkspace, WorkspaceManager

class ReadFileInput(BaseModel):
    filepath: str = Field(description="Relative path of the file to read within the workspace.")
    max_bytes: int = Field(default=100000, description="Maximum bytes to read (capped at 5MB).")

class WriteFileInput(BaseModel):
    filepath: str = Field(description="Relative path of the file to write within the workspace.")
    content: str = Field(description="Text content to write.")
    mode: str = Field(default="w", description="Write mode: 'w' for overwrite, 'a' for append.")

class CreateFileInput(BaseModel):
    filepath: str = Field(description="Relative path of the new file to create within the workspace.")
    content: str = Field(default="", description="Initial content.")

class ListWorkspaceInput(BaseModel):
    subpath: str = Field(default="", description="Optional subfolder within the workspace to list.")


def get_read_file_tool(workspace: Optional[TaskWorkspace] = None) -> ToolImplementation:
    ws = workspace or WorkspaceManager().get_or_create("default")

    def handler(inputs: ReadFileInput) -> Dict[str, Any]:
        return ws.read_file(inputs.filepath, max_bytes=inputs.max_bytes)

    definition = ToolDefinition(
        tool_id="core-fs-002",
        name="read_file",
        description="Reads text content from a permitted file strictly within the task workspace.",
        input_schema=ReadFileInput.model_json_schema(),
        output_schema={
            "type": "object",
            "properties": {
                "filepath": {"type": "string"},
                "content": {"type": "string"},
                "size_bytes": {"type": "integer"},
                "truncated": {"type": "boolean"}
            }
        },
        capability=CapabilityType.READ_ONLY
    )
    return ToolImplementation(
        definition=definition,
        handler=handler,
        input_model=ReadFileInput
    )


def get_write_file_tool(workspace: Optional[TaskWorkspace] = None) -> ToolImplementation:
    ws = workspace or WorkspaceManager().get_or_create("default")

    def handler(inputs: WriteFileInput) -> Dict[str, Any]:
        return ws.write_file(inputs.filepath, inputs.content, mode=inputs.mode)

    definition = ToolDefinition(
        tool_id="core-fs-003",
        name="write_file",
        description="Writes text content to a permitted file strictly within the task workspace.",
        input_schema=WriteFileInput.model_json_schema(),
        output_schema={
            "type": "object",
            "properties": {
                "filepath": {"type": "string"},
                "bytes_written": {"type": "integer"}
            }
        },
        capability=CapabilityType.MUTATING
    )
    return ToolImplementation(
        definition=definition,
        handler=handler,
        input_model=WriteFileInput
    )


def get_create_file_tool(workspace: Optional[TaskWorkspace] = None) -> ToolImplementation:
    ws = workspace or WorkspaceManager().get_or_create("default")

    def handler(inputs: CreateFileInput) -> Dict[str, Any]:
        return ws.create_file(inputs.filepath, inputs.content)

    definition = ToolDefinition(
        tool_id="core-fs-004",
        name="create_file",
        description="Creates a new file strictly within the task workspace.",
        input_schema=CreateFileInput.model_json_schema(),
        output_schema={
            "type": "object",
            "properties": {
                "filepath": {"type": "string"},
                "bytes_written": {"type": "integer"}
            }
        },
        capability=CapabilityType.MUTATING
    )
    return ToolImplementation(
        definition=definition,
        handler=handler,
        input_model=CreateFileInput
    )


def get_list_workspace_tool(workspace: Optional[TaskWorkspace] = None) -> ToolImplementation:
    ws = workspace or WorkspaceManager().get_or_create("default")

    def handler(inputs: ListWorkspaceInput) -> List[Dict[str, Any]]:
        return ws.list_files(inputs.subpath)

    definition = ToolDefinition(
        tool_id="core-fs-005",
        name="list_workspace",
        description="Lists files and subdirectories located within the task workspace.",
        input_schema=ListWorkspaceInput.model_json_schema(),
        output_schema={"type": "array"},
        capability=CapabilityType.READ_ONLY
    )
    return ToolImplementation(
        definition=definition,
        handler=handler,
        input_model=ListWorkspaceInput
    )
