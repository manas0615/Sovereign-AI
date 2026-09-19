"""Dependency-free JSON extraction and parsing for agent decisions."""

import json
import re
from sovereign.core.agent.models import AgentDecision

class ModelOutputParser:
    @staticmethod
    def parse_decision(raw_output: str) -> AgentDecision:
        """
        Parses UNTRUSTED model output into a validated AgentDecision.
        Strips markdown ticks if present.
        Raises ValueError if parsing/validation fails.
        """
        text = raw_output.strip()
        
        # Attempt to extract JSON block if wrapped in markdown
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            text = match.group(1)
        else:
            # Maybe it starts with { and ends with }
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and start < end:
                text = text[start:end+1]
                
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed JSON: {e}")
            
        try:
            decision = AgentDecision(**data)
            return decision
        except Exception as e:
            raise ValueError(f"AgentDecision schema validation failed: {e}")
