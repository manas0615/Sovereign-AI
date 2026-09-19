import re

# Update host.py
f1 = 'src/sovereign/core/agent/host.py'
content1 = open(f1, 'r').read()
content1 = content1.replace('self.repo.save_task(', 'self.repo.update_task(')
content1 = content1.replace('self.repo.add_decision(', 'self.repo.add_state_item(')
content1 = content1.replace('self.repo.add_finding(', 'self.repo.add_state_item(')
content1 = content1.replace('self.repo.add_unresolved_question(', 'self.repo.add_state_item(')

content1 = re.sub(
    r'self\.repo\.checkpoint\(([^,]+),\s*(\"[^\"]+\")\)',
    r'self.repo.create_checkpoint(Checkpoint(task_id=\1, description=\2))',
    content1
)
content1 = content1.replace('from sovereign.core.state.models import Task, TaskStatus, Finding, Decision, EvidenceReference, UnresolvedQuestion, ContextSnapshot', 'from sovereign.core.state.models import Task, TaskStatus, Finding, Decision, EvidenceReference, UnresolvedQuestion, ContextSnapshot, Checkpoint')

open(f1, 'w').write(content1)

# Update test_agent_host.py
f2 = 'tests/test_agent_host.py'
content2 = open(f2, 'r').read()
content2 = content2.replace('repo.save_task(', 'repo.update_task(')
content2 = content2.replace('repo.add_decision(', 'repo.add_state_item(')
content2 = content2.replace('repo.add_finding(', 'repo.add_state_item(')
content2 = content2.replace('repo.add_unresolved_question(', 'repo.add_state_item(')

# Fix get_decisions and get_findings
content2 = re.sub(
    r'repo\.get_decisions\(([^)]+)\)',
    r'[i for i in repo.get_state_items(\1) if i.item_type == "decision"]',
    content2
)
content2 = re.sub(
    r'repo\.get_findings\(([^)]+)\)',
    r'[i for i in repo.get_state_items(\1) if i.item_type == "finding"]',
    content2
)

# Fix repo.create_task("...")
content2 = re.sub(
    r'repo\.create_task\("([^"]+)"\)',
    r'Task(title="\1", goal="\1")\n    repo.create_task(task)',
    content2
)
# Wait, this regex will double output task if it was task = repo.create_task(...)
content2 = re.sub(
    r'task\s*=\s*repo\.create_task\("([^"]+)"\)',
    r'task = Task(title="\1", goal="\1")\n    repo.create_task(task)',
    content2
)

# test_context_pressure task = repo.create_task("Pressure test")
content2 = content2.replace('from sovereign.core.state.models import TaskStatus', 'from sovereign.core.state.models import TaskStatus, Task')

open(f2, 'w').write(content2)
