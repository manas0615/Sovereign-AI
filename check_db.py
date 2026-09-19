import json
with open("artifacts/manifest.json", "r") as f:
    manifest = json.load(f)
    print(manifest.get("art-a2287339"))
    
with open(manifest["art-a2287339"]["metadata"]["file_path"], "r") as f:
    print("\n--- CONTENT ---")
    print(f.read())
