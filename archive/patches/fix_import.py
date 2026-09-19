with open('src/sovereign/infrastructure/artifacts/manifest_generator.py', 'r') as f:
    content = f.read()

content = content.replace("from sovereign.core.qualification.repository import QualificationRepository", "from sovereign.core.state.repository import QualificationRepository")

with open('src/sovereign/infrastructure/artifacts/manifest_generator.py', 'w') as f:
    f.write(content)
