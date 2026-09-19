from sovereign.infrastructure.state.sqlite_repository import SQLiteTaskRepository
repo = SQLiteTaskRepository()
trials = repo.list_trials("60449a86c18dc60abe0b4fbe456f0927872836459f726396e35fce8a977329d0")
for t in trials:
    print(f"Llama Decision -> {t.test_id}: {t.success}, {t.validation_outcome}, {t.failure_category}")

trials = repo.list_trials("2c9e2b245b899fc97d41884f274844758feb1997e1e79212faaef58b7ede14f2")
for t in trials:
    print(f"Llama Reasoning -> {t.test_id}: {t.success}, {t.validation_outcome}, {t.failure_category}")

trials = repo.list_trials("7cccb629054fd59b4772d104aee87e4caaf4c92c85eac1f3c8612ba1f910b8cf")
for t in trials:
    print(f"Qwen Decision -> {t.test_id}: {t.success}, {t.validation_outcome}, {t.failure_category}")

trials = repo.list_trials("628598fffec23296367ae12fd03907405f06d46af1903af7c6cc8db851549e6f")
for t in trials:
    print(f"Qwen Reasoning -> {t.test_id}: {t.success}, {t.validation_outcome}, {t.failure_category}")
