import re

with open('src/sovereign/core/agent/host.py', 'r') as f:
    content = f.read()

replacement = '''
            # Materialize state
            materialized_state = []
            
            all_items = self.repo.get_state_items(task.task_id)
            for item in all_items:
                if item.item_id in snapshot.selected_item_ids:
                    materialized_state.append(item.model_dump_json())
                    
            all_evs = self.repo.get_evidence(task.task_id)
            for ev in all_evs:
                if ev.evidence_id in snapshot.selected_evidence_ids:
                    materialized_state.append(ev.model_dump_json())
                    
            state_str = "\\n".join(materialized_state)

            # 2. Invoke Model
            # The prompt combines system instructions, the materialized state, and current user instruction.
            prompt = f"{self._system_prompt()}\\n\\nTask:\\n{task.goal}\\n\\nCurrent State:\\n{state_str}\\n\\nContext Snapshot:\\n{snapshot.model_dump_json(indent=2)}"
'''

# Find the specific block to replace
target = '''
            # 2. Invoke Model
            # The prompt combines system instructions, the snapshot, and current user instruction.
            prompt = f"{self._system_prompt()}\\n\\nTask:\\n{task.goal}\\n\\nCurrent State:\\n{snapshot.model_dump_json(indent=2)}"
'''

content = content.replace(target.lstrip('\\n'), replacement.lstrip('\\n'))

with open('src/sovereign/core/agent/host.py', 'w') as f:
    f.write(content)

print("Patch applied.")
