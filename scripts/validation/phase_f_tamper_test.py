from sovereign.application.services import get_app_service
from sovereign.core.state.models import Task
import sqlite3

svc = get_app_service()

print("\n=== PATH C: TAMPERED PASSPORT / DENIED ===")
# Let's tamper with the passport for DocumentRetrieval_v1 to have a wrong qualification_identity
conn = sqlite3.connect(svc.repo.db_path)
c = conn.cursor()
c.execute("UPDATE capability_passports SET qualification_identity = 'tampered_hash' WHERE capability_contract = 'DocumentRetrieval_v1'")
conn.commit()
conn.close()

task_c = Task(title="Tampered Retrieval Task", goal="Retrieve document information")
svc.repo.create_task(task_c)
task_c_result = svc.agent.run(task_c.task_id)

print(f"Task Status: {task_c_result.status.value}")
items = svc.repo.get_state_items(task_c.task_id)
for item in items:
    print(f"State: {item.rationale}")

# Restore passport
conn = sqlite3.connect(svc.repo.db_path)
c = conn.cursor()
c.execute("UPDATE capability_passports SET qualification_identity = '8448996545b97949e77fd468bf7830f7054f8ade89387dd684bda30ebe88aee0' WHERE capability_contract = 'DocumentRetrieval_v1'")
conn.commit()
conn.close()

