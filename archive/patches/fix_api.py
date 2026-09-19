with open('src/sovereign/application/services.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.strip().startswith("def get_trust_manifest"):
        skip = True
    if not skip:
        new_lines.append(line)
    if skip and line.strip().startswith("return self.manifest_generator"):
        skip = False

# Now find where to insert it, before _app_service = None
insert_idx = len(new_lines)
for i, line in enumerate(new_lines):
    if line.startswith("_app_service = None"):
        insert_idx = i
        break

method = '''
    def get_trust_manifest(self, artifact_id: str):
        return self.manifest_generator.generate(artifact_id)
'''

new_lines.insert(insert_idx, method)

with open('src/sovereign/application/services.py', 'w') as f:
    f.writelines(new_lines)
