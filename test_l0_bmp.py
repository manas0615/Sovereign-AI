import os
import io
import struct
import subprocess
from sovereign.core.knowledge.models import Document
from sovereign.infrastructure.knowledge.parsers.ocr_parser import OCRParser

# Generate a simple 24-bit uncompressed BMP image in pure Python
def create_bmp_text():
    # 7x5 bitmap font for characters 'E', 'Q', 'U', 'I', 'P'
    font = {
        ' ': [0,0,0,0,0],
        'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
        'Q': [0x3E, 0x41, 0x51, 0x21, 0x5E],
        'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],
        'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
        'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
        'V': [0x1F, 0x20, 0x40, 0x20, 0x1F],
        '-': [0x08, 0x08, 0x08, 0x08, 0x08],
        '2': [0x42, 0x61, 0x51, 0x49, 0x46],
        '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
        '4': [0x18, 0x14, 0x12, 0x7F, 0x10],
    }
    
    text = "EQUIP V-204"
    scale = 8
    char_w = 6 * scale
    char_h = 8 * scale
    width = len(text) * char_w + 40
    height = char_h + 40
    
    # Initialize white canvas (2D array: 1 = white, 0 = black)
    grid = [[1 for _ in range(width)] for _ in range(height)]
    
    # Draw characters
    x_offset = 20
    y_offset = 20
    for char in text:
        cols = font.get(char, font[' '])
        for col_idx, col_bits in enumerate(cols):
            for row_idx in range(7):
                if (col_bits >> row_idx) & 1:
                    for dx in range(scale):
                        for dy in range(scale):
                            gx = x_offset + col_idx * scale + dx
                            gy = y_offset + row_idx * scale + dy
                            if 0 <= gy < height and 0 <= gx < width:
                                grid[gy][gx] = 0
        x_offset += char_w

    # Construct 24-bit BMP
    # Row size must be padded to a multiple of 4 bytes
    row_bytes = width * 3
    padding_size = (4 - (row_bytes % 4)) % 4
    image_data_size = (row_bytes + padding_size) * height
    file_size = 54 + image_data_size
    
    header = struct.pack('<2sIHHI', b'BM', file_size, 0, 0, 54)
    info_header = struct.pack('<IIIHHIIIIII', 40, width, height, 1, 24, 0, image_data_size, 2835, 2835, 0, 0)
    
    buf = io.BytesIO()
    buf.write(header)
    buf.write(info_header)
    
    # BMP is written bottom-up
    for y in reversed(range(height)):
        row = bytearray()
        for x in range(width):
            val = 255 if grid[y][x] == 1 else 0
            row.extend([val, val, val]) # B, G, R
        row.extend([0] * padding_size)
        buf.write(row)
        
    buf.seek(0)
    return buf

print("--- STEP 1: Generate Test Image in Memory ---")
bmp_buf = create_bmp_text()
print(f"Generated BMP image: {bmp_buf.getbuffer().nbytes} bytes")

print("\n--- STEP 2: Execute OCRParser ---")
parser = OCRParser()
doc = Document(
    document_id="doc-bmp-test",
    filename="test_inspection_sheet.bmp",
    document_type="image",
    file_size=bmp_buf.getbuffer().nbytes,
    source_path="local_data/test_inspection_sheet.bmp",
    content_hash="test_bmp_hash"
)

blocks = parser.parse(doc, bmp_buf)
print(f"\nExtracted {len(blocks)} DocumentBlock(s):")
for b in blocks:
    print(f"  Page {b.page_number} ({b.block_type}): {b.text!r}")

assert len(blocks) > 0, "No blocks extracted by OCRParser!"
assert "V-204" in blocks[0].text or "EQUIP" in blocks[0].text, f"Expected text not found in OCR output: {blocks[0].text}"
print("\n[GATE L0 PASS] Local Tesseract OCR invocation and OCRParser execution verified successfully!")
