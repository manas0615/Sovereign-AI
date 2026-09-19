import re

with open('src/sovereign/infrastructure/state/sqlite_repository.py', 'r') as f:
    content = f.read()

# Make SqliteRepository inherit from both
content = content.replace(
    "class SqliteRepository(TaskRepository):",
    "from sovereign.core.state.repository import QualificationRepository, QualificationTrialRecord, QualificationResultRecord, CapabilityPassportRecord\n\nclass SqliteRepository(TaskRepository, QualificationRepository):"
)

# Insert table creations
init_db_insertion = \"\"\"
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS qualification_trials (
                        trial_id TEXT PRIMARY KEY,
                        qualification_identity TEXT NOT NULL,
                        test_id TEXT NOT NULL,
                        prompt_reference TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        success INTEGER NOT NULL,
                        validation_outcome TEXT NOT NULL,
                        failure_category TEXT,
                        resource_metrics TEXT NOT NULL,
                        metadata TEXT NOT NULL
                    )
                ''')
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS qualification_results (
                        result_id TEXT PRIMARY KEY,
                        qualification_identity TEXT NOT NULL,
                        capability_contract TEXT NOT NULL,
                        deployment_identity TEXT NOT NULL,
                        trial_counts TEXT NOT NULL,
                        compliance_metrics TEXT NOT NULL,
                        resource_stability TEXT NOT NULL,
                        threshold_evaluation TEXT NOT NULL,
                        qualification_status TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        metadata TEXT NOT NULL
                    )
                ''')
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS capability_passports (
                        passport_id TEXT PRIMARY KEY,
                        qualification_identity TEXT NOT NULL,
                        deployment_identity TEXT NOT NULL,
                        capability_contract TEXT NOT NULL,
                        result_id TEXT NOT NULL,
                        qualification_status TEXT NOT NULL,
                        qualification_timestamp TEXT NOT NULL,
                        invalidation_info TEXT NOT NULL,
                        metadata TEXT NOT NULL,
                        FOREIGN KEY(result_id) REFERENCES qualification_results(result_id)
                    )
                ''')
\"\"\"
content = content.replace("CREATE TABLE IF NOT EXISTS checkpoints", init_db_insertion + "\n                    CREATE TABLE IF NOT EXISTS checkpoints")

# Add the methods at the end
new_methods = \"\"\"
    def save_trial(self, trial: QualificationTrialRecord) -> None:
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO qualification_trials (trial_id, qualification_identity, test_id, prompt_reference, timestamp, success, validation_outcome, failure_category, resource_metrics, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (trial.trial_id, trial.qualification_identity, trial.test_id, trial.prompt_reference, trial.timestamp.isoformat(), 1 if trial.success else 0, trial.validation_outcome, trial.failure_category, json.dumps(trial.resource_metrics), json.dumps(trial.metadata))
            )

    def get_trial(self, trial_id: str) -> Optional[QualificationTrialRecord]:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM qualification_trials WHERE trial_id = ?", (trial_id,)).fetchone()
            if not row:
                return None
            return QualificationTrialRecord(
                trial_id=row['trial_id'],
                qualification_identity=row['qualification_identity'],
                test_id=row['test_id'],
                prompt_reference=row['prompt_reference'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                success=bool(row['success']),
                validation_outcome=row['validation_outcome'],
                failure_category=row['failure_category'],
                resource_metrics=json.loads(row['resource_metrics']),
                metadata=json.loads(row['metadata'])
            )
        finally:
            conn.close()

    def list_trials(self, qualification_identity: str) -> List[QualificationTrialRecord]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM qualification_trials WHERE qualification_identity = ?", (qualification_identity,)).fetchall()
            return [QualificationTrialRecord(
                trial_id=row['trial_id'],
                qualification_identity=row['qualification_identity'],
                test_id=row['test_id'],
                prompt_reference=row['prompt_reference'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                success=bool(row['success']),
                validation_outcome=row['validation_outcome'],
                failure_category=row['failure_category'],
                resource_metrics=json.loads(row['resource_metrics']),
                metadata=json.loads(row['metadata'])
            ) for row in rows]
        finally:
            conn.close()

    def save_result(self, result: QualificationResultRecord) -> None:
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO qualification_results (result_id, qualification_identity, capability_contract, deployment_identity, trial_counts, compliance_metrics, resource_stability, threshold_evaluation, qualification_status, timestamp, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (result.result_id, result.qualification_identity, result.capability_contract, result.deployment_identity, json.dumps(result.trial_counts), json.dumps(result.compliance_metrics), result.resource_stability, result.threshold_evaluation, result.qualification_status, result.timestamp.isoformat(), json.dumps(result.metadata))
            )

    def get_result(self, result_id: str) -> Optional[QualificationResultRecord]:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM qualification_results WHERE result_id = ?", (result_id,)).fetchone()
            if not row:
                return None
            return QualificationResultRecord(
                result_id=row['result_id'],
                qualification_identity=row['qualification_identity'],
                capability_contract=row['capability_contract'],
                deployment_identity=row['deployment_identity'],
                trial_counts=json.loads(row['trial_counts']),
                compliance_metrics=json.loads(row['compliance_metrics']),
                resource_stability=row['resource_stability'],
                threshold_evaluation=row['threshold_evaluation'],
                qualification_status=row['qualification_status'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                metadata=json.loads(row['metadata'])
            )
        finally:
            conn.close()

    def save_passport(self, passport: CapabilityPassportRecord) -> None:
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO capability_passports (passport_id, qualification_identity, deployment_identity, capability_contract, result_id, qualification_status, qualification_timestamp, invalidation_info, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (passport.passport_id, passport.qualification_identity, passport.deployment_identity, passport.capability_contract, passport.result_id, passport.qualification_status, passport.qualification_timestamp.isoformat(), json.dumps(passport.invalidation_info), json.dumps(passport.metadata))
            )

    def get_passport(self, passport_id: str) -> Optional[CapabilityPassportRecord]:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM capability_passports WHERE passport_id = ?", (passport_id,)).fetchone()
            if not row:
                return None
            return CapabilityPassportRecord(
                passport_id=row['passport_id'],
                qualification_identity=row['qualification_identity'],
                deployment_identity=row['deployment_identity'],
                capability_contract=row['capability_contract'],
                result_id=row['result_id'],
                qualification_status=row['qualification_status'],
                qualification_timestamp=datetime.fromisoformat(row['qualification_timestamp']),
                invalidation_info=json.loads(row['invalidation_info']),
                metadata=json.loads(row['metadata'])
            )
        finally:
            conn.close()
\"\"\"

content = content + \"\\n\" + new_methods

with open('src/sovereign/infrastructure/state/sqlite_repository.py', 'w') as f:
    f.write(content)
