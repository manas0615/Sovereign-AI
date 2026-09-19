"""Tool Policy Engine."""

from typing import Set, Dict, Any
from sovereign.core.capabilities.models import ToolImplementation, CapabilityType
from pydantic import ValidationError

class ToolPolicy:
    def __init__(self, allowed_tools: Set[str]):
        # The exact allowlist of safe tool names
        self.allowed_tools = allowed_tools
        # Destructive tools are globally forbidden in this prototype
        self.forbidden_capabilities = {CapabilityType.DESTRUCTIVE}
        
    def is_allowed(self, tool: ToolImplementation) -> bool:
        if not tool.definition.enabled:
            return False
            
        if tool.definition.name not in self.allowed_tools:
            return False
            
        if tool.definition.capability in self.forbidden_capabilities:
            return False
            
        return True
        
    def validate_inputs(self, tool: ToolImplementation, inputs: Dict[str, Any]) -> Any:
        """Validates the raw dictionary against the tool's Pydantic schema."""
        try:
            return tool.input_model(**inputs)
        except ValidationError as e:
            # We strictly raise a validation error here before execution
            raise ValueError(f"Input validation failed: {e}")
