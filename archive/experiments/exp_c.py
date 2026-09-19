import hashlib
import json

with open("artifacts/manifest.json", "r") as f:
    manifest = json.load(f)
    
art_id = "art-6f4832a3"
meta = manifest[art_id]["metadata"]

with open(meta["file_path"], "rb") as f:
    content = f.read()

computed_hash = hashlib.sha256(content).hexdigest()
stored_hash = meta["content_hash"]

print(f"Computed hash: {computed_hash}")
print(f"Stored hash:   {stored_hash}")
print(f"MATCH: {computed_hash == stored_hash}")
