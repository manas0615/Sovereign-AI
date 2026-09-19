with open('src/sovereign/core/agent/host.py', 'r') as f:
    lines = f.readlines()
for i in range(170, 195):
    print(f"{i}: {lines[i].rstrip()}")
