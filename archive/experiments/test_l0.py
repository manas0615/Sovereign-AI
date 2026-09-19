import os
import io
import subprocess
from sovereign.core.knowledge.models import Document
from sovereign.infrastructure.knowledge.parsers.ocr_parser import OCRParser

print("--- STEP 1: CLI Tesseract Verification ---")
res = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
print("Return code:", res.returncode)
print("Stdout:", res.stdout.splitlines()[0] if res.stdout else "None")

print("\n--- STEP 2: Python OCRParser Sample Image OCR Verification ---")
# Create a sample synthetic image using python to test OCR extraction
# We can create a simple BMP/PNG or use python to write an image
from PIL import Image, ImageDraw

# If PIL is not installed, we can test PIL availability or create a simple PPM/BMP
try:
    img = Image.new('RGB', (400, 100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 30), "EQUIPMENT V-204 INSPECTION PASS", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    has_pil = True
except Exception as e:
    print("PIL not installed:", e)
    has_pil = False

if has_pil:
    parser = OCRParser()
    doc = Document(
        document_id="doc-test-ocr",
        filename="test_inspection_ocr.png",
        document_type="image",
        file_size=buf.getbuffer().nbytes,
        content_hash="test_hash"
    )
    blocks = parser.parse(doc, buf)
    print(f"Extracted {len(blocks)} blocks:")
    for b in blocks:
        print(f"  Page {b.page_number} [{b.block_type}]: {b.text!r}")
        
    assert len(blocks) > 0
    assert "V-204" in blocks[0].text or "EQUIPMENT" in blocks[0].text or "INSPECTION" in blocks[0].text
    print("\nOCRParser Sample OCR: SUCCESS")
else:
    print("\nPIL not present, testing with standard test image")
