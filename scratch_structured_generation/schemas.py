import json
from sovereign.core.agent.models import AgentAction

loose_schema = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": [e.value for e in AgentAction]},
        "rationale": {"type": ["string", "null"]},
        "answer": {"type": ["string", "null"]},
        "query": {"type": ["string", "null"]},
        "top_k": {"type": ["integer", "null"]},
        "tool_name": {"type": ["string", "null"]},
        "arguments": {"type": ["object", "null"]},
        "question": {"type": ["string", "null"]}
    },
    "required": ["action"],
    "additionalProperties": True
}

strict_schema = {
    "type": "object",
    "oneOf": [
        {
            "properties": {
                "action": {"const": "FINAL"},
                "answer": {"type": "string"},
                "rationale": {"type": "string"},
                "query": {"type": "null"},
                "top_k": {"type": "null"},
                "tool_name": {"type": "null"},
                "arguments": {"type": "null"},
                "question": {"type": "null"}
            },
            "required": ["action", "answer"],
            "additionalProperties": False
        },
        {
            "properties": {
                "action": {"const": "RETRIEVE"},
                "query": {"type": "string"},
                "top_k": {"type": "integer"},
                "rationale": {"type": "string"},
                "answer": {"type": "null"},
                "tool_name": {"type": "null"},
                "arguments": {"type": "null"},
                "question": {"type": "null"}
            },
            "required": ["action", "query"],
            "additionalProperties": False
        },
        {
            "properties": {
                "action": {"const": "TOOL"},
                "tool_name": {"type": "string"},
                "arguments": {"type": "object", "additionalProperties": True},
                "rationale": {"type": "string"},
                "answer": {"type": "null"},
                "query": {"type": "null"},
                "top_k": {"type": "null"},
                "question": {"type": "null"}
            },
            "required": ["action", "tool_name"],
            "additionalProperties": False
        },
        {
            "properties": {
                "action": {"const": "CLARIFY"},
                "question": {"type": "string"},
                "rationale": {"type": "string"},
                "answer": {"type": "null"},
                "query": {"type": "null"},
                "top_k": {"type": "null"},
                "tool_name": {"type": "null"},
                "arguments": {"type": "null"}
            },
            "required": ["action", "question"],
            "additionalProperties": False
        },
        {
            "properties": {
                "action": {"const": "CONTINUE"},
                "rationale": {"type": "string"},
                "answer": {"type": "null"},
                "query": {"type": "null"},
                "top_k": {"type": "null"},
                "tool_name": {"type": "null"},
                "arguments": {"type": "null"},
                "question": {"type": "null"}
            },
            "required": ["action", "rationale"],
            "additionalProperties": False
        }
    ]
}
