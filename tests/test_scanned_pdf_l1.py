"""
Phase L1 Tests: Scanned PDF Rasterization, OCR Fallback, Knowledge Indexing, and Searchability.
"""

import io
import os
import tempfile
import pytest
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import reportlab.pdfgen.canvas as canvas
import pypdf

from sovereign.core.knowledge.models import Document, DocumentBlock, DocumentStatus
from sovereign.core.knowledge.parser import OCRRequiredError
from sovereign.infrastructure.knowledge.parsers.ocr_parser import OCRParser
from sovereign.infrastructure.knowledge.parsers.pdf_parser import PDFParser
from sovereign.infrastructure.knowledge.chunkers.structure_aware_chunker import StructureAwareChunker
from sovereign.infrastructure.knowledge.sqlite_knowledge import SQLiteKnowledgeBase
from sovereign.infrastructure.state.tokenizer import ApproximateTokenCounter


def create_synthetic_scanned_pdf(output_stream: io.BytesIO, page_texts: list):
    """Helper to generate a genuinely flattened image-only PDF using ReportLab and PIL."""
    c = canvas.Canvas(output_stream, pagesize=(600, 400))
    
    for text_content in page_texts:
        img = Image.new("RGB", (1200, 800), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((60, 60), text_content, fill=(0, 0, 0), spacing=15)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
            img.save(tmp_img.name, format="PNG")
            tmp_img_path = tmp_img.name
            
        try:
            c.drawImage(tmp_img_path, 0, 0, width=600, height=400)
            c.showPage()
        finally:
            if os.path.exists(tmp_img_path):
                os.remove(tmp_img_path)
                
    c.save()
    output_stream.seek(0)


def create_mixed_pdf(output_stream: io.BytesIO, digital_text: str, scanned_text: str):
    """Helper to generate a mixed PDF: Page 1 digital text, Page 2 flattened scan."""
    c = canvas.Canvas(output_stream, pagesize=(600, 400))
    
    # Page 1: Digital text
    text_obj = c.beginText(50, 350)
    text_obj.setFont("Helvetica", 12)
    for line in digital_text.split("\n"):
        text_obj.textLine(line)
    c.drawText(text_obj)
    c.showPage()
    
    # Page 2: Flattened image scan
    img = Image.new("RGB", (1200, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((60, 60), scanned_text, fill=(0, 0, 0), spacing=15)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
        img.save(tmp_img.name, format="PNG")
        tmp_img_path = tmp_img.name
        
    try:
        c.drawImage(tmp_img_path, 0, 0, width=600, height=400)
        c.showPage()
    finally:
        if os.path.exists(tmp_img_path):
            os.remove(tmp_img_path)
            
    c.save()
    output_stream.seek(0)


@pytest.fixture
def temp_kb():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = Path(f.name)
    kb = SQLiteKnowledgeBase(db_path=path)
    yield kb
    try:
        path.unlink(missing_ok=True)
    except PermissionError:
        pass


def test_flattened_scanned_pdf_rasterization_and_ocr():
    """Test A & B: Prove flattened PDF is rasterized and OCR recovers synthetic inspection content."""
    inspection_text = (
        "INDUSTRIAL EQUIPMENT INSPECTION REPORT\n"
        "Equipment ID: V-204\n"
        "Finding: Critical seal wear detected on main flange.\n"
        "Measurement: 0.15 mm\n"
        "Threshold: 0.10 mm\n"
        "Recommendation: Immediate flange seal replacement required."
    )
    
    stream = io.BytesIO()
    create_synthetic_scanned_pdf(stream, [inspection_text])
    
    ocr_parser = OCRParser()
    pdf_parser = PDFParser(ocr_parser=ocr_parser)
    
    doc = Document(
        document_id="doc_scanned_v204",
        filename="v204_inspection_scan.pdf",
        source_path="v204_inspection_scan.pdf",
        document_type="pdf",
        file_size=stream.getbuffer().nbytes,
        content_hash="hash_scanned_v204"
    )
    
    blocks = pdf_parser.parse(doc, stream)
    
    assert len(blocks) >= 1
    extracted_text = " ".join(b.text for b in blocks)
    
    # Verify key tokens recovered with OCR normalization
    assert "V-204" in extracted_text or "v-204" in extracted_text.lower()
    assert "seal wear" in extracted_text.lower()
    assert "0.15" in extracted_text
    assert "0.10" in extracted_text
    assert blocks[0].page_number == 1
    assert blocks[0].document_id == "doc_scanned_v204"


def test_scanned_pdf_knowledge_indexing_and_searchability(temp_kb):
    """Test C & D: Prove OCR text flows through chunker, stores in SQLite KB, and is searchable."""
    inspection_text = (
        "VESSEL CONDITION LOG\n"
        "Equipment ID: V-204\n"
        "Component: High Pressure Reactor Core\n"
        "Finding: Critical seal wear detected on main flange.\n"
        "Measurement: 0.15 mm exceeds allowable threshold 0.10 mm.\n"
        "Action: Scheduled maintenance replacement."
    )
    
    stream = io.BytesIO()
    create_synthetic_scanned_pdf(stream, [inspection_text])
    
    ocr_parser = OCRParser()
    pdf_parser = PDFParser(ocr_parser=ocr_parser)
    
    doc = Document(
        document_id="doc_kb_test_v204",
        filename="reactor_v204_scan.pdf",
        source_path="reactor_v204_scan.pdf",
        document_type="pdf",
        file_size=stream.getbuffer().nbytes,
        content_hash=Document.compute_hash(stream.getvalue()),
        status=DocumentStatus.REGISTERED
    )
    temp_kb.register_document(doc)
    
    blocks = pdf_parser.parse(doc, stream)
    
    tokenizer = ApproximateTokenCounter()
    chunker = StructureAwareChunker(tokenizer=tokenizer, max_chunk_tokens=100)
    chunks = chunker.chunk(doc, blocks)
    
    assert len(chunks) >= 1
    temp_kb.save_chunks(chunks)
    
    doc.status = DocumentStatus.INGESTED
    temp_kb.update_document(doc)
    
    # Prove searchability/retrievability of OCR-derived content via Retriever
    results_id = temp_kb.retrieve("V-204")
    assert len(results_id) > 0
    assert "V-204" in results_id[0].text or "v-204" in results_id[0].text.lower()
    assert results_id[0].document_id == "doc_kb_test_v204"
    
    results_flange = temp_kb.retrieve("flange")
    assert len(results_flange) > 0
    assert "flange" in results_flange[0].text.lower()


def test_mixed_pdf_preserves_both_pages():
    """Test E: Verify mixed PDF preserves both digital text and scanned pages with correct provenance."""
    digital_p1 = (
        "PLANT SAFETY OVERVIEW CHAPTER 1\n\n"
        "This chapter outlines standard operating procedures for safety valves and flange monitoring. "
        "All sensors must undergo calibration on a quarterly schedule to prevent undetected drift."
    )
    scanned_p2 = (
        "ANOMALY INSPECTION SHEET\n"
        "Equipment ID: V-204\n"
        "Finding: Critical seal wear detected on main flange.\n"
        "Measurement: 0.15 mm"
    )
    
    stream = io.BytesIO()
    create_mixed_pdf(stream, digital_p1, scanned_p2)
    
    ocr_parser = OCRParser()
    pdf_parser = PDFParser(ocr_parser=ocr_parser)
    
    doc = Document(
        document_id="doc_mixed_p1_p2",
        filename="plant_overview_and_scan.pdf",
        source_path="plant_overview_and_scan.pdf",
        document_type="pdf",
        file_size=stream.getbuffer().nbytes,
        content_hash="hash_mixed_123"
    )
    
    blocks = pdf_parser.parse(doc, stream)
    
    assert len(blocks) >= 2
    
    # Page 1 provenance and digital content
    page1_blocks = [b for b in blocks if b.page_number == 1]
    assert len(page1_blocks) >= 1
    assert "PLANT SAFETY OVERVIEW" in page1_blocks[0].text
    assert "quarterly schedule" in page1_blocks[0].text
    
    # Page 2 provenance and OCR content
    page2_blocks = [b for b in blocks if b.page_number == 2]
    assert len(page2_blocks) >= 1
    page2_text = " ".join(b.text for b in page2_blocks)
    assert "V-204" in page2_text or "v-204" in page2_text.lower()
    assert "seal wear" in page2_text.lower()


def test_scanned_pdf_without_ocr_parser_raises_ocr_required():
    """Test G1: Prove that attempting to parse a scanned page without an OCRParser raises OCRRequiredError."""
    stream = io.BytesIO()
    create_synthetic_scanned_pdf(stream, ["Inspection report with no digital text stream."])
    
    pdf_parser = PDFParser(ocr_parser=None)
    doc = Document(
        document_id="doc_no_ocr",
        filename="unsupported_scan.pdf",
        source_path="unsupported_scan.pdf",
        document_type="pdf",
        file_size=stream.getbuffer().nbytes,
        content_hash="h"
    )
    
    with pytest.raises(OCRRequiredError) as exc_info:
        pdf_parser.parse(doc, stream)
    assert "OCR is required" in str(exc_info.value)


def test_corrupted_pdf_raises_value_error():
    """Test G2: Prove that malformed or corrupted PDF binary stream raises ValueError cleanly."""
    corrupted_stream = io.BytesIO(b"%PDF-1.4 CORRUPTED INVALID BYTES NOT A REAL PDF BODY")
    
    pdf_parser = PDFParser(ocr_parser=OCRParser())
    doc = Document(
        document_id="doc_corrupted",
        filename="corrupted.pdf",
        source_path="corrupted.pdf",
        document_type="pdf",
        file_size=48,
        content_hash="h_corrupt"
    )
    
    with pytest.raises(ValueError) as exc_info:
        pdf_parser.parse(doc, corrupted_stream)
    assert "Failed to read PDF" in str(exc_info.value)
