import pytest
import tempfile
import os
from pathlib import Path
from sovereign.core.knowledge.models import Document, DocumentStatus, DocumentBlock
from sovereign.infrastructure.knowledge.sqlite_knowledge import SQLiteKnowledgeBase
from sovereign.infrastructure.knowledge.parsers.text_parser import TextParser
from sovereign.infrastructure.knowledge.parsers.pdf_parser import PDFParser, OCRRequiredError
from sovereign.infrastructure.knowledge.chunkers.structure_aware_chunker import StructureAwareChunker
from sovereign.infrastructure.state.tokenizer import ApproximateTokenCounter
import pypdf

@pytest.fixture
def temp_db_path():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = Path(f.name)
    yield path
    try:
        path.unlink(missing_ok=True)
    except PermissionError:
        pass

@pytest.fixture
def knowledge_base(temp_db_path):
    kb = SQLiteKnowledgeBase(db_path=temp_db_path)
    yield kb
    # ensure any held connections are implicitly gc'd or close them if we had explicit ones

def test_document_registration_and_hashing(knowledge_base):
    content = b"This is a test document."
    content_hash = Document.compute_hash(content)
    
    doc = Document(
        filename="test.txt",
        source_path="/fake/path/test.txt",
        document_type="txt",
        file_size=len(content),
        content_hash=content_hash
    )
    
    knowledge_base.register_document(doc)
    
    retrieved = knowledge_base.get_document(doc.document_id)
    assert retrieved is not None
    assert retrieved.filename == "test.txt"
    assert retrieved.content_hash == content_hash
    
    # Duplicate hash detection
    dup = knowledge_base.find_by_hash(content_hash)
    assert dup is not None
    assert dup.document_id == doc.document_id
    
    # Update status
    doc.status = DocumentStatus.INGESTED
    knowledge_base.update_document(doc)
    
    updated = knowledge_base.get_document(doc.document_id)
    assert updated.status == DocumentStatus.INGESTED

def test_text_parser():
    parser = TextParser()
    content = b"# Section 1\n\nParagraph 1\n\nParagraph 2"
    doc = Document(filename="t.md", source_path="t.md", document_type="md", file_size=len(content), content_hash="hash")
    
    import io
    stream = io.BytesIO(content)
    blocks = parser.parse(doc, stream)
    
    assert len(blocks) == 3
    assert blocks[0].block_type == "heading"
    assert blocks[0].text == "# Section 1"
    assert blocks[0].section == "Section 1"
    
    assert blocks[1].block_type == "paragraph"
    assert blocks[1].text == "Paragraph 1"
    assert blocks[1].section == "Section 1"

def test_structure_aware_chunker():
    tokenizer = ApproximateTokenCounter()
    chunker = StructureAwareChunker(tokenizer=tokenizer, max_chunk_tokens=50)
    doc = Document(filename="t.txt", source_path="t.txt", document_type="txt", file_size=10, content_hash="h")
    
    blocks = [
        DocumentBlock(document_id=doc.document_id, page_number=1, sequence=0, text="A" * 100), # 25 tokens
        DocumentBlock(document_id=doc.document_id, page_number=1, sequence=1, text="B" * 100), # 25 tokens
        DocumentBlock(document_id=doc.document_id, page_number=2, sequence=2, text="C" * 100)  # 25 tokens
    ]
    
    chunks = chunker.chunk(doc, blocks)
    
    # 25 + 25 = 50 tokens (fits in one chunk). 3rd block goes to next chunk.
    assert len(chunks) == 2
    assert chunks[0].page_range == "1"
    assert chunks[0].text == "A" * 100 + "\n\n" + "B" * 100
    
    assert chunks[1].page_range == "2"
    assert chunks[1].text == "C" * 100

def test_pdf_extraction_and_scanned_detection():
    # Create a minimal text PDF for testing
    pdf_writer = pypdf.PdfWriter()
    pdf_writer.add_blank_page(width=72, height=72)
    # This blank page has 0 text length, simulating an image-only PDF
    
    import io
    stream = io.BytesIO()
    pdf_writer.write(stream)
    stream.seek(0)
    
    parser = PDFParser()
    doc = Document(filename="scan.pdf", source_path="scan.pdf", document_type="pdf", file_size=10, content_hash="h")
    
    with pytest.raises(OCRRequiredError):
        parser.parse(doc, stream)
