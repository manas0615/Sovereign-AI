with open('test_l0_bmp.py', 'r') as f:
    content = f.read()

content = content.replace('content_hash="test_bmp_hash"', 'source_path="local_data/test_inspection_sheet.bmp",\n    content_hash="test_bmp_hash"')

with open('test_l0_bmp.py', 'w') as f:
    f.write(content)
