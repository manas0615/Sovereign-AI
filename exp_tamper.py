import hashlib
import json

with open("artifacts/manifest.json", "r") as f:
    manifest = json.load(f)
    
art_id = "art-6f4832a3"
meta = manifest[art_id]["metadata"]
path = meta["file_path"]

# Tamper with the file
with open(path, "a") as f:
    f.write("\nTAMPERED CONTENT\n")

# Re-check hash
with open(path, "rb") as f:
    content = f.read()
    
computed_hash = hashlib.sha256(content).hexdigest()
stored_hash = meta["content_hash"]

print("--- TAMPER TEST ---")
print(f"Computed hash: {computed_hash}")
print(f"Stored hash:   {stored_hash}")
print(f"DETECTED: {computed_hash != stored_hash}")

# Restore
with open(path, "wb") as f:
    f.write(content[:-18])
