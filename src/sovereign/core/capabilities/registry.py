"""Tool Registry."""

from typing import Dict, List, Optional
from sovereign.core.capabilities.models import ToolDefinition, ToolImplementation

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolImplementation] = {}
        
    def register(self, implementation: ToolImplementation) -> None:
        tool_name = implementation.definition.name
        if tool_name in self._tools:
            raise ValueError(f"Tool collision: A tool named '{tool_name}' is already registered.")
        self._tools[tool_name] = implementation
        
    def get(self, tool_name: str) -> Optional[ToolImplementation]:
        return self._tools.get(tool_name)
        
    def list_tools(self) -> List[ToolDefinition]:
        return [impl.definition for impl in self._tools.values() if impl.definition.enabled]
