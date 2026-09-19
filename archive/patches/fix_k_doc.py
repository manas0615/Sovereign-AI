with open('exp_k_suite.py', 'r') as f:
    content = f.read()

old_doc = '''doc_content = b"CRITICAL EQUIPMENT RECORD\\nEquipment: V-204\\nStatus: Main seal wear 0.15mm.\\nAction: Replace seal immediately."'''
new_doc = '''doc_content = b"INSPECTION REPORT\\nEquipment ID: V-204\\nDate: 2026-09-13\\nObserved condition: Critical seal wear detected on main flange.\\nMeasurement: 0.15mm clearance\\nThreshold: 0.10mm max\\nFinding: Fails safety tolerance.\\nRecommended action: Replace main flange seal immediately before resuming operation."'''

content = content.replace(old_doc, new_doc)

with open('exp_k_suite.py', 'w') as f:
    f.write(content)
