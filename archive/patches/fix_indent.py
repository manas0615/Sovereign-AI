with open('src/sovereign/application/services.py', 'r') as f:
    lines = f.readlines()
    
with open('src/sovereign/application/services.py', 'w') as f:
    for line in lines:
        if line.startswith("from sovereign.infrastructure.artifacts.manifest_generator import TrustManifestGenerator"):
            f.write("        " + line)
        else:
            f.write(line)
