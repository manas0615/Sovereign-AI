import hashlib
import json
from fastapi.testclient import TestClient
from sovereign.application.api import app
from sovereign.application.services import get_app_service

client = TestClient(app)
svc = get_app_service()
art_id = "art-dd46d034"

res = client.get(f"/api/v1/artifacts/{art_id}/manifest")
manifest = res.json()

stored_hash = manifest['integrity']['artifact_content_hash']
meta = svc.artifact_storage.get_artifact(art_id).metadata

with open(meta.file_path, "a") as f:
    f.write("\nTAMPERED\n")

with open(meta.file_path, "rb") as f:
    tampered_content = f.read()

computed_hash = hashlib.sha256(tampered_content).hexdigest()

print(f"Tamper test for {art_id}")
print(f"Manifest Hash: {stored_hash}")
print(f"Computed Hash: {computed_hash}")
print(f"Match: {stored_hash == computed_hash}")

# Restore
with open(meta.file_path, "wb") as f:
    f.write(tampered_content[:-10])

