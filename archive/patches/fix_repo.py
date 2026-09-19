with open('src/sovereign/application/services.py', 'r') as f:
    content = f.read()

content = content.replace("TrustManifestGenerator(self.repo, self.qualification_repo, self.artifact_storage)", "TrustManifestGenerator(self.repo, self.repo, self.artifact_storage)")

with open('src/sovereign/application/services.py', 'w') as f:
    f.write(content)
