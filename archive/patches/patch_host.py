import re

with open('src/sovereign/core/agent/host.py', 'r') as f:
    content = f.read()

# 1. Update the Finding creation to include metadata
old_finding = '''                        v_msg = f"Trusted Verification Result: [{v_report.status.value}] Passed {v_report.passed_checks}/{v_report.total_checks} checks. {v_report.failure_reason or ''}".strip()
                        self.repo.add_state_item(task.task_id, Finding(statement=v_msg, confidence="high", evidence_refs=[]))'''
new_finding = '''                        v_msg = f"Trusted Verification Result: [{v_report.status.value}] Passed {v_report.passed_checks}/{v_report.total_checks} checks. {v_report.failure_reason or ''}".strip()
                        self.repo.add_state_item(task.task_id, Finding(
                            statement=v_msg, 
                            confidence="high", 
                            evidence_refs=[], 
                            metadata={"verification_status": v_report.status.value}
                        ))'''
content = content.replace(old_finding, new_finding)

# 2. Update FINAL handling to use metadata instead of string matching
old_final_check = '''                    # Check task state items for verified status
                    current_items = self.repo.get_state_items(task.task_id)
                    verified = False
                    for item in reversed(current_items):
                        if isinstance(item, Finding) and "Trusted Verification Result: [Verification Passed]" in item.statement:
                            verified = True
                            break
                    
                    if verified:
                        task.status = TaskStatus.COMPLETED
                        self.repo.add_state_item(task.task_id, Finding(statement=f"Trusted Verification Confirmed. {decision.answer}", confidence="high"))
                    else:
                        task.status = TaskStatus.FAILED
                        self.repo.add_state_item(task.task_id, Decision(rationale="Task marked FINAL without passing independent trusted verification checks.", decision="FAIL"))'''

new_final_check = '''                    # Check task state items for structured verified status
                    current_items = self.repo.get_state_items(task.task_id)
                    verified = False
                    inconclusive = False
                    for item in reversed(current_items):
                        if isinstance(item, Finding) and "verification_status" in getattr(item, "metadata", {}):
                            status_val = item.metadata["verification_status"]
                            if status_val == "Verification Passed":
                                verified = True
                                break
                            elif status_val == "Verification Inconclusive":
                                inconclusive = True
                                break
                            elif status_val == "Verification Failed":
                                break
                        # Fallback to string matching for legacy items without metadata
                        elif isinstance(item, Finding) and "Trusted Verification Result: [" in item.statement:
                            if "[Verification Passed]" in item.statement:
                                verified = True
                                break
                            elif "[Verification Inconclusive]" in item.statement:
                                inconclusive = True
                                break
                            elif "[Verification Failed]" in item.statement:
                                break
                    
                    if verified:
                        task.status = TaskStatus.COMPLETED
                        self.repo.add_state_item(task.task_id, Finding(statement=f"Trusted Verification Confirmed. {decision.answer}", confidence="high"))
                    elif inconclusive:
                        # If inconclusive, it's not a success, but we don't treat it as a hard failure 
                        # that the agent explicitly ignored. It's just unverified.
                        task.status = TaskStatus.FAILED
                        self.repo.add_state_item(task.task_id, Decision(rationale="Task marked FINAL but verification was inconclusive. No trusted tests available.", decision="FAIL"))
                    else:
                        task.status = TaskStatus.FAILED
                        self.repo.add_state_item(task.task_id, Decision(rationale="Task marked FINAL without passing independent trusted verification checks.", decision="FAIL"))'''
content = content.replace(old_final_check, new_final_check)

with open('src/sovereign/core/agent/host.py', 'w') as f:
    f.write(content)
