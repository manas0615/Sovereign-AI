import hashlib

# 1. Update models.py
with open('src/sovereign/core/artifacts/models.py', 'r') as f:
    content = f.read()

if 'content_hash: str' not in content:
    content = content.replace(
        'sections_rendered: List[str] = Field(default_factory=list)',
        'sections_rendered: List[str] = Field(default_factory=list)\n    content_hash: str = Field(default="")'
    )
    with open('src/sovereign/core/artifacts/models.py', 'w') as f:
        f.write(content)
    print("Updated models.py")

# 2. Update engine.py
with open('src/sovereign/infrastructure/artifacts/engine.py', 'r') as f:
    content = f.read()

if 'content_hash=' not in content:
    import_hashlib = "import hashlib\n"
    if "import hashlib" not in content:
        content = import_hashlib + content

    target = '''        metadata = ArtifactMetadata(
            file_path=str(target_path),
            size_bytes=len(content.encode('utf-8')),
            sections_rendered=request.requested_sections
        )'''
        
    replacement = '''        metadata = ArtifactMetadata(
            file_path=str(target_path),
            size_bytes=len(content.encode('utf-8')),
            sections_rendered=request.requested_sections,
            content_hash=hashlib.sha256(content.encode('utf-8')).hexdigest()
        )'''
        
    content = content.replace(target, replacement)
    
    with open('src/sovereign/infrastructure/artifacts/engine.py', 'w') as f:
        f.write(content)
    print("Updated engine.py")
