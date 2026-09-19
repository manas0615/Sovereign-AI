import json

strict_schema_corrected = {
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
