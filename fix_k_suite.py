with open('exp_k_suite.py', 'r') as f:
    content = f.read()

content = content.replace('("v204_network_test.txt", doc_content)', '("inspection_report_V-204.txt", doc_content)')
content = content.replace('for _ in range(30):\n        time.sleep(1)', 'for _ in range(40):\n        time.sleep(2)')

with open('exp_k_suite.py', 'w') as f:
    f.write(content)
