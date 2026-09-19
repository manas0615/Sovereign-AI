import sys
import os

# Add src to pythonpath
sys.path.append(os.path.abspath('src'))
from sovereign.core.agent.models import AgentDecision

test_cases = [
    {"action": "FINAL", "answer": "Paris"}, # Valid
    {"action": "FINAL", "rationale": "I am done"}, # Invalid (missing answer)
    {"action": "TOOL", "tool_name": "local_time", "arguments": {}}, # Valid
    {"action": "TOOL", "tool": "local_time"}, # Invalid (wrong key)
    {"action": "FINAL", "answer": "Paris", "metadata": "extra"} # Invalid (extra prop)
]

for i, tc in enumerate(test_cases):
    try:
        AgentDecision(**tc)
        print(f"Test {i}: {tc} -> VALID")
    except Exception as e:
        print(f"Test {i}: {tc} -> INVALID")
