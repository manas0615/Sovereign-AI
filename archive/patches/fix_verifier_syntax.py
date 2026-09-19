import re
with open('src/sovereign/core/coding/verifier.py', 'r') as f:
    content = f.read()

# Fix the broken line
old_line = '            harness += "    exec(r + trusted_tests + )\\n"'
new_line = '            harness += "    exec(r\'\'\'" + trusted_tests + "\'\'\')\\n"'
content = content.replace(old_line, new_line)

with open('src/sovereign/core/coding/verifier.py', 'w') as f:
    f.write(content)
