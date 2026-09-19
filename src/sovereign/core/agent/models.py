"""Agent models."""
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator

class AgentAction(str, Enum):
    FINAL = "FINAL"
    RETRIEVE = "RETRIEVE"
    TOOL = "TOOL"
    CLARIFY = "CLARIFY"
    CONTINUE = "CONTINUE"

class AgentStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    WAITING_FOR_MODEL = "WAITING_FOR_MODEL"
    WAITING_FOR_TOOL = "WAITING_FOR_TOOL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PAUSED_FOR_CLARIFICATION = "PAUSED_FOR_CLARIFICATION"

class AgentDecision(BaseModel):
    action: AgentAction
    rationale: Optional[str] = Field(default=None, description="Concise, safe reasoning for the action. NOT for hidden chain of thought.")
    answer: Optional[str] = None
    query: Optional[str] = None
    top_k: Optional[int] = None
    tool_name: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    question: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_action_fields(self) -> 'AgentDecision':
        if self.action == AgentAction.FINAL:
            if not self.answer:
                raise ValueError("action=FINAL requires an 'answer'.")
        elif self.action == AgentAction.RETRIEVE:
            if not self.query:
                raise ValueError("action=RETRIEVE requires a 'query'.")
            if self.top_k is None or self.top_k <= 0:
                self.top_k = 5
        elif self.action == AgentAction.TOOL:
            if not self.tool_name:
                raise ValueError("action=TOOL requires a 'tool_name'.")
            if self.arguments is None:
                self.arguments = {}
        elif self.action == AgentAction.CLARIFY:
            if not self.question:
                raise ValueError("action=CLARIFY requires a 'question'.")
        elif self.action == AgentAction.CONTINUE:
            if not self.rationale:
                raise ValueError("action=CONTINUE requires a 'rationale' to define its purpose.")
        return self

AGENT_DECISION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "oneOf": [
        {
            "properties": {
                "action": {"const": "FINAL"},
                "answer": {"type": "string", "minLength": 1},
                "rationale": {"type": ["string", "null"]}
            },
            "required": ["action", "answer"],
            "additionalProperties": True
        },
        {
            "properties": {
                "action": {"const": "RETRIEVE"},
                "query": {"type": "string", "minLength": 1},
                "top_k": {"type": ["integer", "null"]},
                "rationale": {"type": ["string", "null"]}
            },
            "required": ["action", "query"],
            "additionalProperties": True
        },
        {
            "properties": {
                "action": {"const": "TOOL"},
                "tool_name": {"type": "string", "minLength": 1},
                "arguments": {"type": ["object", "null"], "additionalProperties": True},
                "rationale": {"type": ["string", "null"]}
            },
            "required": ["action", "tool_name"],
            "additionalProperties": True
        },
        {
            "properties": {
                "action": {"const": "CLARIFY"},
                "question": {"type": "string", "minLength": 1},
                "rationale": {"type": ["string", "null"]}
            },
            "required": ["action", "question"],
            "additionalProperties": True
        },
        {
            "properties": {
                "action": {"const": "CONTINUE"},
                "rationale": {"type": "string", "minLength": 1}
            },
            "required": ["action", "rationale"],
            "additionalProperties": True
        }
    ]
}

AGENT_DECISION_RESPONSE_FORMAT: Dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "AgentDecision",
        "strict": True,
        "schema": AGENT_DECISION_SCHEMA
    }
}

