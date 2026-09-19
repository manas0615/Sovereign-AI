import os
import subprocess

# Check if 7z exists
try:
    res = subprocess.run(["7z", "-h"], capture_output=True, text=True)
    print("7z found:", res.stdout[:50])
except Exception as e:
    print("7z not in PATH")

# Check where NSIS installs or if /D= parameter is needed: /S /D=C:\Tesseract-OCR
