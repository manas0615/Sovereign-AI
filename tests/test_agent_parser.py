import pytest
from sovereign.core.agent.parser import ModelOutputParser
from sovereign.core.agent.models import AgentAction

def test_parse_plain_json():
    raw = '{"action": "FINAL", "answer": "42"}'
    decision = ModelOutputParser.parse_decision(raw)
    assert decision.action == AgentAction.FINAL
    assert decision.answer == "42"

def test_parse_markdown_wrapped_json():
    raw = '''Here is my decision:
```json
{"action": "RETRIEVE", "query": "pump specs", "top_k": 3}
```'''
    decision = ModelOutputParser.parse_decision(raw)
    assert decision.action == AgentAction.RETRIEVE
    assert decision.query == "pump specs"
    assert decision.top_k == 3

def test_parse_malformed_json():
    raw = '{"action": "FINAL", "answer": 42' # Missing closing brace
    with pytest.raises(ValueError, match="Malformed JSON"):
        ModelOutputParser.parse_decision(raw)

def test_parse_invalid_schema():
    raw = '{"action": "UNKNOWN", "something": 123}'
    with pytest.raises(ValueError, match="schema validation failed"):
        ModelOutputParser.parse_decision(raw)

def test_action_specific_validation():
    # FINAL without answer
    raw = '{"action": "FINAL"}'
    with pytest.raises(ValueError, match="requires an 'answer'"):
        ModelOutputParser.parse_decision(raw)
        
    # TOOL without tool_name
    raw = '{"action": "TOOL"}'
    with pytest.raises(ValueError, match="requires a 'tool_name'"):
        ModelOutputParser.parse_decision(raw)
        
    # RETRIEVE without query
    raw = '{"action": "RETRIEVE"}'
    with pytest.raises(ValueError, match="requires a 'query'"):
        ModelOutputParser.parse_decision(raw)
        
    # CLARIFY without question
    raw = '{"action": "CLARIFY"}'
    with pytest.raises(ValueError, match="requires a 'question'"):
        ModelOutputParser.parse_decision(raw)
