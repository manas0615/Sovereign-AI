import re

with open('src/sovereign/core/agent/host.py', 'r') as f:
    content = f.read()

# Replace the FINAL logic
old_logic = '''                    for item in reversed(current_items):
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
                                break'''

new_logic = '''                    for item in reversed(current_items):
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
                            # Any other status is treated as failure. Break to prevent older results from authorising.
                            break
                        # Spoofable string fallback removed to ensure model-generated text cannot forge success.'''

content = content.replace(old_logic, new_logic)

with open('src/sovereign/core/agent/host.py', 'w') as f:
    f.write(content)
