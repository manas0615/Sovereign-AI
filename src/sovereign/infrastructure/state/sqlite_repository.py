"""SQLite implementation of the TaskRepository."""

import sqlite3
import json
from contextlib import contextmanager
from typing import List, Optional, ContextManager, Any
from pathlib import Path
from datetime import datetime

from sovereign.infrastructure.config import get_settings
from sovereign.infrastructure.paths import get_data_dir
from sovereign.core.exceptions import StateError
from sovereign.core.state.repository import QualificationRepository, QualificationTrialRecord, QualificationResultRecord, CapabilityPassportRecord
from sovereign.core.state.models import (
    Task, TaskStatus, StateItem, Finding, UnresolvedQuestion, Decision,
    EvidenceReference, Checkpoint, Priority
)

class SQLiteTaskRepository(QualificationRepository):
    
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            settings = get_settings()
            db_path = get_data_dir() / settings.db_filename
        
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        # isolation_level=None enables autocommit mode, but we will manage transactions explicitly
        # We use standard isolation_level for proper transactions
        conn = sqlite3.connect(self.db_path, isolation_level="DEFERRED")
        conn.row_factory = sqlite3.Row
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        goal TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        current_checkpoint_id TEXT
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS state_items (
                        item_id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        item_type TEXT NOT NULL,
                        priority INTEGER NOT NULL,
                        payload TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY(task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS evidence_references (
                        evidence_id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        source_id TEXT NOT NULL,
                        locator TEXT NOT NULL,
                        metadata TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY(task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
                    )
                """)
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
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS checkpoints (
                        checkpoint_id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        description TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY(task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
                    )
                """)
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> ContextManager[sqlite3.Connection]:
        """Provides an active database connection within a transaction block."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise StateError(f"Transaction failed and was rolled back: {e}") from e
        finally:
            conn.close()

    def create_task(self, task: Task) -> None:
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO tasks (task_id, title, goal, status, created_at, updated_at, current_checkpoint_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (task.task_id, task.title, task.goal, task.status.value, task.created_at.isoformat(), task.updated_at.isoformat(), task.current_checkpoint_id)
            )

    def get_task(self, task_id: str) -> Optional[Task]:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            if not row:
                return None
            return Task(
                task_id=row['task_id'],
                title=row['title'],
                goal=row['goal'],
                status=TaskStatus(row['status']),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at']),
                current_checkpoint_id=row['current_checkpoint_id']
            )
        finally:
            conn.close()

    def list_tasks(self) -> List[Task]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
            tasks = []
            for row in rows:
                tasks.append(Task(
                    task_id=row['task_id'],
                    title=row['title'],
                    goal=row['goal'],
                    status=TaskStatus(row['status']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    current_checkpoint_id=row['current_checkpoint_id']
                ))
            return tasks
        finally:
            conn.close()

    def update_task(self, task: Task) -> None:

        with self.transaction() as conn:
            conn.execute(
                "UPDATE tasks SET title=?, goal=?, status=?, updated_at=?, current_checkpoint_id=? WHERE task_id=?",
                (task.title, task.goal, task.status.value, task.updated_at.isoformat(), task.current_checkpoint_id, task.task_id)
            )

    def _deserialize_item(self, row: sqlite3.Row) -> StateItem:
        payload = json.loads(row['payload'])
        item_type = row['item_type']
        
        # Build common dict
        data = {
            "item_id": row['item_id'],
            "priority": Priority(row['priority']),
            "created_at": datetime.fromisoformat(row['created_at']),
            "updated_at": datetime.fromisoformat(row['updated_at']),
            **payload
        }
        
        if item_type == "finding":
            return Finding(**data)
        elif item_type == "question":
            return UnresolvedQuestion(**data)
        elif item_type == "decision":
            return Decision(**data)
        else:
            raise StateError(f"Unknown state item type: {item_type}")

    def add_state_item(self, task_id: str, item: StateItem, conn: Optional[sqlite3.Connection] = None) -> None:
        def _execute(connection):
            # Extract payload excluding base fields
            base_keys = {"item_id", "priority", "created_at", "updated_at", "item_type"}
            payload = {k: v for k, v in item.model_dump().items() if k not in base_keys}
            
            connection.execute(
                "INSERT INTO state_items (item_id, task_id, item_type, priority, payload, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (item.item_id, task_id, item.item_type, item.priority.value, json.dumps(payload), item.created_at.isoformat(), item.updated_at.isoformat())
            )
            
        if conn:
            _execute(conn)
        else:
            with self.transaction() as c:
                _execute(c)

    def update_state_item(self, task_id: str, item: StateItem, conn: Optional[sqlite3.Connection] = None) -> None:
        def _execute(connection):
            base_keys = {"item_id", "priority", "created_at", "updated_at", "item_type"}
            payload = {k: v for k, v in item.model_dump().items() if k not in base_keys}
            
            connection.execute(
                "UPDATE state_items SET item_type=?, priority=?, payload=?, updated_at=? WHERE item_id=? AND task_id=?",
                (item.item_type, item.priority.value, json.dumps(payload), item.updated_at.isoformat(), item.item_id, task_id)
            )
            
        if conn:
            _execute(conn)
        else:
            with self.transaction() as c:
                _execute(c)

    def get_state_items(self, task_id: str) -> List[StateItem]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM state_items WHERE task_id = ?", (task_id,)).fetchall()
            return [self._deserialize_item(row) for row in rows]
        finally:
            conn.close()

    def add_evidence(self, task_id: str, evidence: EvidenceReference, conn: Optional[sqlite3.Connection] = None) -> None:
        def _execute(connection):
            connection.execute(
                "INSERT INTO evidence_references (evidence_id, task_id, source_id, locator, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (evidence.evidence_id, task_id, evidence.source_id, evidence.locator, json.dumps(evidence.metadata), evidence.created_at.isoformat())
            )
            
        if conn:
            _execute(conn)
        else:
            with self.transaction() as c:
                _execute(c)

    def get_evidence(self, task_id: str) -> List[EvidenceReference]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM evidence_references WHERE task_id = ?", (task_id,)).fetchall()
            result = []
            for row in rows:
                result.append(EvidenceReference(
                    evidence_id=row['evidence_id'],
                    source_id=row['source_id'],
                    locator=row['locator'],
                    metadata=json.loads(row['metadata']),
                    created_at=datetime.fromisoformat(row['created_at'])
                ))
            return result
        finally:
            conn.close()

    def create_checkpoint(self, checkpoint: Checkpoint) -> None:
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO checkpoints (checkpoint_id, task_id, description, created_at) VALUES (?, ?, ?, ?)",
                (checkpoint.checkpoint_id, checkpoint.task_id, checkpoint.description, checkpoint.created_at.isoformat())
            )


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

    def get_passport_by_identity(self, qualification_identity: str) -> Optional[CapabilityPassportRecord]:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM capability_passports WHERE qualification_identity = ? ORDER BY qualification_timestamp DESC", (qualification_identity,)).fetchone()
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
