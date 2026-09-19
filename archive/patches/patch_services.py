# Insert into services.py
with open('src/sovereign/application/services.py', 'r') as f:
    content = f.read()

import_statement = "from sovereign.infrastructure.artifacts.manifest_generator import TrustManifestGenerator\n"
if "TrustManifestGenerator" not in content:
    content = content.replace("from sovereign.infrastructure.artifacts.engine import LocalArtifactEngine", "from sovereign.infrastructure.artifacts.engine import LocalArtifactEngine\n" + import_statement)
    
if "self.manifest_generator =" not in content:
    init_hook = "self.artifact_engine = LocalArtifactEngine(self.repo, self.artifact_storage)"
    content = content.replace(init_hook, init_hook + "\n        self.manifest_generator = TrustManifestGenerator(self.repo, self.qualification_repo, self.artifact_storage)")

if "def get_trust_manifest" not in content:
    method = '''
    def get_trust_manifest(self, artifact_id: str):
        return self.manifest_generator.generate(artifact_id)
'''
    content += method
    
with open('src/sovereign/application/services.py', 'w') as f:
    f.write(content)
