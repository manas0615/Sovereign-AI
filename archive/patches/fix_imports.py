with open('src/sovereign/infrastructure/state/sqlite_repository.py', 'r') as f:
    content = f.read()

import_statement = "from sovereign.core.state.repository import QualificationRepository, QualificationTrialRecord, QualificationResultRecord, CapabilityPassportRecord\n"

if "QualificationTrialRecord" not in content[:1000]:
    content = content.replace("from sovereign.core.state.models import (", import_statement + "from sovereign.core.state.models import (")
    content = content.replace("class SQLiteTaskRepository:", "class SQLiteTaskRepository(QualificationRepository):")

with open('src/sovereign/infrastructure/state/sqlite_repository.py', 'w') as f:
    f.write(content)
