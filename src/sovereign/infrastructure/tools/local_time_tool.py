"""Local time tool."""

from pydantic import BaseModel
from datetime import datetime, timezone
from sovereign.core.capabilities.models import ToolDefinition, ToolImplementation, CapabilityType

class LocalTimeInput(BaseModel):
    pass
    
def local_time_handler(inputs: LocalTimeInput) -> str:
    # MVP Requirement: Return local system time, no external network calls.
    return datetime.now().astimezone().isoformat()

def get_local_time_tool() -> ToolImplementation:
    definition = ToolDefinition(
        tool_id="core-time-001",
        name="local_time",
        description="Returns the local system time in ISO 8601 format.",
        input_schema=LocalTimeInput.model_json_schema(),
        output_schema={"type": "string"},
        capability=CapabilityType.READ_ONLY
    )
    return ToolImplementation(
        definition=definition,
        handler=local_time_handler,
        input_model=LocalTimeInput
    )
