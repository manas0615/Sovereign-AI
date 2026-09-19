import pytest
import io
import json
import base64
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from sovereign.core.knowledge.models import Document, DocumentBlock
from sovereign.core.knowledge.parser import OCRRequiredError
from sovereign.core.runtime.models import InferenceRequest, InferenceResponse
from sovereign.infrastructure.knowledge.parsers.ocr_parser import OCRParser, OCRDependencyError
from sovereign.infrastructure.knowledge.parsers.multimodal_parser import MultimodalParser
from sovereign.infrastructure.knowledge.parsers.pdf_parser import PDFParser
from sovereign.application.api import app

def test_ocr_parser_missing_dependency(monkeypatch):
    import subprocess
    def mock_run(*args, **kwargs):
        raise FileNotFoundError("tesseract missing")
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    parser = OCRParser()
    doc = Document(document_id="d1", filename="img.png", source_path="img.png", document_type="png", file_size=10, content_hash="h")
    
    with pytest.raises(OCRDependencyError) as excinfo:
        parser.parse(doc, io.BytesIO(b"fake_image_data"))
    assert "Tesseract OCR is not installed" in str(excinfo.value)

def test_ocr_parser_success(monkeypatch):
    import subprocess
    def mock_run(cmd, *args, **kwargs):
        if "--version" in cmd:
            return MagicMock(returncode=0)
        return MagicMock(returncode=0, stdout="Mocked OCR Text\n")
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    parser = OCRParser()
    doc = Document(document_id="d1", filename="img.png", source_path="img.png", document_type="png", file_size=10, content_hash="h", metadata={"page_number": 42})
    
    blocks = parser.parse(doc, io.BytesIO(b"fake_image_data"))
    assert len(blocks) == 1
    assert blocks[0].text == "Mocked OCR Text"
    assert blocks[0].page_number == 42
    assert blocks[0].document_id == "d1"

def test_ocr_failure_handling(monkeypatch):
    import subprocess
    def mock_run(cmd, *args, **kwargs):
        if "--version" in cmd:
            return MagicMock(returncode=0)
        return MagicMock(returncode=1, stderr="OCR Error")
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    parser = OCRParser()
    doc = Document(document_id="d1", filename="i.png", source_path="i.png", document_type="png", file_size=10, content_hash="h")
    
    with pytest.raises(ValueError, match="Tesseract failed"):
        parser.parse(doc, io.BytesIO(b"fail"))

def test_multimodal_parser_request_construction_and_provenance():
    mock_gateway = MagicMock()
    mock_gateway.generate.return_value = InferenceResponse(text="P&ID diagram showing a valve.", usage={"prompt_tokens": 10, "completion_tokens": 10}, stop_reason="stop")
    
    parser = MultimodalParser(gateway=mock_gateway)
    doc = Document(document_id="d2", filename="diagram.jpg", source_path="/path/diagram.jpg", document_type="jpg", file_size=12, content_hash="h2", metadata={"page_number": 5})
    
    img_bytes = b"fake_jpg_bytes"
    blocks = parser.parse(doc, io.BytesIO(img_bytes))
    
    mock_gateway.generate.assert_called_once()
    req = mock_gateway.generate.call_args[0][0]
    assert isinstance(req, InferenceRequest)
    assert req.images is not None
    assert len(req.images) == 1
    assert req.images[0].startswith("data:image/jpg;base64,")
    
    b64_str = base64.b64encode(img_bytes).decode('utf-8')
    assert req.images[0] == f"data:image/jpg;base64,{b64_str}"
    
    assert len(blocks) == 1
    assert blocks[0].text == "P&ID diagram showing a valve."
    assert blocks[0].page_number == 5
    assert blocks[0].document_id == "d2"
    assert blocks[0].block_type == "multimodal_interpretation"

def test_multimodal_inference_failure():
    from sovereign.core.exceptions import ModelRuntimeError
    mock_gateway = MagicMock()
    mock_gateway.generate.side_effect = ModelRuntimeError("VLM Server down")
    
    parser = MultimodalParser(gateway=mock_gateway)
    doc = Document(document_id="d3", filename="t.png", source_path="t.png", document_type="png", file_size=1, content_hash="h")
    
    with pytest.raises(ModelRuntimeError):
        parser.parse(doc, io.BytesIO(b"x"))

def test_digital_pdf_path_remains_unchanged(monkeypatch):
    import pypdf
    pdf_writer = pypdf.PdfWriter()
    pdf_writer.add_blank_page(width=72, height=72)
    stream = io.BytesIO()
    pdf_writer.write(stream)
    stream.seek(0)
    
    def mock_extract_text(*args, **kwargs):
        return "Digital text content that exceeds the heuristic limit of 50 chars per page." * 2
        
    monkeypatch.setattr(pypdf.PageObject, "extract_text", mock_extract_text)
    
    parser = PDFParser()
    doc = Document(document_id="d4", filename="digital.pdf", source_path="digital.pdf", document_type="pdf", file_size=100, content_hash="h")
    
    blocks = parser.parse(doc, stream)
    assert len(blocks) > 0
    assert "Digital text content" in blocks[0].text

def test_scanned_pdf_routing(monkeypatch):
    import pypdf
    pdf_writer = pypdf.PdfWriter()
    pdf_writer.add_blank_page(width=72, height=72)
    
    stream = io.BytesIO()
    pdf_writer.write(stream)
    stream.seek(0)
    
    mock_ocr = MagicMock()
    mock_ocr.parse.return_value = [DocumentBlock(document_id="d5", page_number=1, sequence=0, text="OCR Result from Scanned PDF", block_type="paragraph")]
    
    parser = PDFParser(ocr_parser=mock_ocr)
    doc = Document(document_id="d5", filename="scan.pdf", source_path="scan.pdf", document_type="pdf", file_size=10, content_hash="h")
    
    class FakeImage:
        def __init__(self):
            self.name = "image1.png"
            self.data = b"fakeimg"
            
    monkeypatch.setattr(pypdf.PageObject, "images", [FakeImage()])
    
    blocks = parser.parse(doc, stream)
    
    assert mock_ocr.parse.called
    assert len(blocks) == 1
    assert blocks[0].text == "OCR Result from Scanned PDF"

def test_unsupported_image_handling():
    client = TestClient(app)
    response = client.post("/api/v1/knowledge/documents", files={"file": ("test.gif", b"fake gif data", "image/gif")})
    assert response.status_code == 400
    assert "Unsupported file format" in response.text

def test_image_registry_routing(monkeypatch):
    client = TestClient(app)
    
    from sovereign.core.runtime.gateway import ModelGateway
    
    def mock_generate(*args, **kwargs):
        return InferenceResponse(text="Mocked image response", usage={"prompt_tokens": 10, "completion_tokens": 10}, stop_reason="stop")
        
    monkeypatch.setattr(ModelGateway, "generate", mock_generate)
    
    from sovereign.infrastructure.knowledge.sqlite_knowledge import SQLiteKnowledgeBase
    monkeypatch.setattr(SQLiteKnowledgeBase, "register_document", lambda *a, **k: None)
    monkeypatch.setattr(SQLiteKnowledgeBase, "save_chunks", lambda *a, **k: None)
    monkeypatch.setattr(SQLiteKnowledgeBase, "update_document", lambda *a, **k: None)

    from sovereign.application.services import get_app_service
    from sovereign.core.agent.router import RoutingDecision
    svc = get_app_service()
    monkeypatch.setattr(svc.router, "route_capability", lambda *a, **k: RoutingDecision(task_id="test", required_capability="MultimodalInference_v1", is_authorized=True, reason="Mock authorized"))
    
    response = client.post("/api/v1/knowledge/documents", files={"file": ("test.png", b"fake png data", "image/png")})
    assert response.status_code == 200
    assert response.json()["status"] == "INGESTED"
