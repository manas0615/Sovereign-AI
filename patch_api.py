with open('src/sovereign/application/api.py', 'r') as f:
    content = f.read()

if "/manifest" not in content:
    method = '''
@router.get("/artifacts/{artifact_id}/manifest")
def get_trust_manifest(artifact_id: str):
    """Retrieve the Verifiable Execution Receipt for an artifact."""
    svc = get_app_service()
    manifest = svc.get_trust_manifest(artifact_id)
    if not manifest:
        raise HTTPException(status_code=404, detail="Manifest not found")
    return manifest.model_dump(mode='json')
'''
    content += method
    with open('src/sovereign/application/api.py', 'w') as f:
        f.write(content)
