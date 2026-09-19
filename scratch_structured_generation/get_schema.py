import json
import sys
import os

# Add src to pythonpath
sys.path.append(os.path.abspath('src'))
from sovereign.core.agent.models import AgentDecision

schema = AgentDecision.model_json_schema()
print(json.dumps(schema, indent=2))
