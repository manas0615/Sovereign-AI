"""Context Manager for assembling working memory from persistent state."""

from typing import List, Dict, Optional, Any
import json

from sovereign.infrastructure.config import get_settings
from sovereign.core.exceptions import ContextBudgetExceeded
from sovereign.core.state.models import (
    Task, StateItem, EvidenceReference, ContextSnapshot, Priority
)
from sovereign.core.state.repository import TaskRepository
from sovereign.infrastructure.state.tokenizer import TokenCounter

class ContextManager:
    
    def __init__(self, repository: TaskRepository, tokenizer: TokenCounter):
        self._repo = repository
        self._tokenizer = tokenizer
        self._settings = get_settings()
        
    def _calculate_working_budget(self) -> int:
        """Calculates the effective working budget available for task state."""
        return (
            self._settings.context_size 
            - self._settings.reserved_system_tokens 
            - self._settings.reserved_output_tokens
        )
        
    def _estimate_item_tokens(self, item: StateItem) -> int:
        # A simple serialization to estimate tokens
        text_rep = json.dumps(item.model_dump(mode='json'), default=str)
        return self._tokenizer.count_tokens(text_rep)

    def _estimate_evidence_tokens(self, ev: EvidenceReference) -> int:
        text_rep = json.dumps(ev.model_dump(mode='json'), default=str)
        return self._tokenizer.count_tokens(text_rep)
        
    def _estimate_base_tokens(self, task: Task, instruction: str) -> int:
        text = f"Goal: {task.goal}\nInstruction: {instruction}"
        return self._tokenizer.count_tokens(text)
        
    def assemble_context(self, task_id: str, current_instruction: str) -> ContextSnapshot:
        task = self._repo.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")
            
        working_budget = self._calculate_working_budget()
        base_tokens = self._estimate_base_tokens(task, current_instruction)
        
        available_budget = working_budget - base_tokens
        if available_budget <= 0:
            raise ContextBudgetExceeded("Base task goal and instruction exceed the working budget.")
            
        items = self._repo.get_state_items(task_id)
        evidence = {ev.evidence_id: ev for ev in self._repo.get_evidence(task_id)}
        
        # Deterministic sorting: priority descending, then created_at ascending (oldest first)
        items.sort(key=lambda x: (x.priority.value, -x.created_at.timestamp()), reverse=True)
        
        selected_item_ids = []
        omitted_item_ids = []
        selected_evidence_ids = set()
        omitted_priorities = set()
        
        current_tokens = 0
        required_items_count = sum(1 for item in items if item.priority == Priority.REQUIRED)
        
        for item in items:
            item_tokens = self._estimate_item_tokens(item)
            
            # Calculate evidence tokens for this item
            ev_tokens = 0
            item_evs = []
            for ev_id in item.evidence_refs:
                if ev_id in evidence and ev_id not in selected_evidence_ids:
                    ev_tokens += self._estimate_evidence_tokens(evidence[ev_id])
                    item_evs.append(ev_id)
                    
            total_cost = item_tokens + ev_tokens
            
            if current_tokens + total_cost <= available_budget:
                current_tokens += total_cost
                selected_item_ids.append(item.item_id)
                selected_evidence_ids.update(item_evs)
            else:
                if item.priority == Priority.REQUIRED:
                    raise ContextBudgetExceeded(
                        f"REQUIRED state item {item.item_id} exceeds available context budget. "
                        f"Available: {available_budget - current_tokens}, Required: {total_cost}"
                    )
                else:
                    omitted_item_ids.append(item.item_id)
                    omitted_priorities.add(item.priority.name)
                    
        snapshot = ContextSnapshot(
            task_id=task_id,
            current_instruction=current_instruction,
            selected_item_ids=selected_item_ids,
            omitted_item_ids=omitted_item_ids,
            selected_evidence_ids=list(selected_evidence_ids),
            token_estimate=base_tokens + current_tokens,
            available_budget=working_budget,
            required_items_count=required_items_count,
            omitted_priorities=list(omitted_priorities)
        )
        
        return snapshot
