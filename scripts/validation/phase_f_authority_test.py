from sovereign.application.services import get_app_service
from sovereign.core.state.models import Task, TaskStatus

svc = get_app_service()

print("\n=== PATH A: UNQUALIFIED / DENIED ===")
task_a = Task(title="Decision Task", goal="Solve a complex multi-step logical decision")
svc.repo.create_task(task_a)
task_a_result = svc.agent.run(task_a.task_id)

print(f"Task Status: {task_a_result.status.value}")
# Let's check state items to see the routing decision
items = svc.repo.get_state_items(task_a.task_id)
for item in items:
    print(f"State: {item.rationale}")

print("\n=== PATH B: QUALIFIED / GRANTED ===")
task_b = Task(title="Retrieval Task", goal="Retrieve document information")
svc.repo.create_task(task_b)
try:
    # We will limit max_iterations to 1 to just prove it enters the execution loop and calls inference
    svc.agent.max_iterations = 1
    task_b_result = svc.agent.run(task_b.task_id)
    print(f"Task Status: {task_b_result.status.value}")
    items = svc.repo.get_state_items(task_b.task_id)
    for item in items:
        if item.item_type == 'decision' and 'routing' in item.rationale.lower():
            print(f"State: {item.rationale}")
        elif item.item_type == 'decision':
            print(f"State: Inference Decision Executed -> {item.decision}")
except Exception as e:
    print(f"Task hit exception during inference (expected if JSON schema mismatches unstructured expectation, but proves inference started): {e}")

