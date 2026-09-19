with open('src/sovereign/infrastructure/artifacts/manifest_generator.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "passports = self.qual_repo.list_passports()" in line:
        continue
    new_lines.append(line)

with open('src/sovereign/infrastructure/artifacts/manifest_generator.py', 'w') as f:
    f.writelines(new_lines)
