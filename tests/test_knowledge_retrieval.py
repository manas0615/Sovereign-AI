import pytest
import tempfile
from pathlib import Path
from sovereign.core.knowledge.models import Document, DocumentChunk, RetrievalResult
from sovereign.infrastructure.knowledge.sqlite_knowledge import SQLiteKnowledgeBase
from sovereign.core.state.models import EvidenceReference

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
def kb(temp_db_path):
    kb = SQLiteKnowledgeBase(db_path=temp_db_path)
    yield kb

def test_large_document_simulation_and_retrieval(kb):
    # Simulate a 100-page document
    doc = Document(
        filename="manual.txt",
        source_path="/docs/manual.txt",
        document_type="txt",
        file_size=100000,
        content_hash="h1"
    )
    kb.register_document(doc)
    
    chunks = []
    # 100 pages, 3 chunks per page
    seq = 0
    for page in range(1, 101):
        for c in range(3):
            text = f"General operational guidelines for page {page}, section {c}."
            if page == 37 and c == 1:
                text = "Pump P-101 vibration measured at 8.4 mm/s during standard operation."
                
            chunk = DocumentChunk(
                document_id=doc.document_id,
                text=text,
                sequence=seq,
                page_range=str(page),
                section=f"Section {c}",
                token_estimate=10
            )
            chunks.append(chunk)
            seq += 1
            
    kb.save_chunks(chunks)
    
    # Query for the specific fact
    results = kb.retrieve(query="Pump P-101 vibration", top_k=5)
    
    assert len(results) > 0
    # Top result should be the exact match on page 37
    top_result = results[0]
    assert top_result.page == "37"
    assert "8.4 mm/s" in top_result.text
    assert top_result.document_id == doc.document_id
    assert top_result.source_path == "/docs/manual.txt"
    
    # Verify we can seamlessly integrate with Package 02 EvidenceReference
    ev_ref = EvidenceReference(
        source_id=top_result.document_id,
        locator=f"Page {top_result.page}",
        metadata={"chunk_id": top_result.chunk_id, "excerpt": top_result.text}
    )
    assert ev_ref.source_id == doc.document_id
    assert ev_ref.locator == "Page 37"

def test_negative_retrieval(kb):
    doc = Document(
        filename="empty.txt",
        source_path="/docs/empty.txt",
        document_type="txt",
        file_size=10,
        content_hash="h2"
    )
    kb.register_document(doc)
    kb.save_chunks([
        DocumentChunk(document_id=doc.document_id, text="The sky is blue.", sequence=0)
    ])
    
    # Query for something that doesn't exist
    results = kb.retrieve("red apples", top_k=5)
    assert len(results) == 0

def test_idempotent_ingestion(kb):
    doc = Document(
        filename="idem.txt",
        source_path="/docs/idem.txt",
        document_type="txt",
        file_size=10,
        content_hash="h3"
    )
    kb.register_document(doc)
    chunk1 = DocumentChunk(document_id=doc.document_id, text="Hello world", sequence=0)
    
    kb.save_chunks([chunk1])
    
    # Re-ingesting: delete old chunks first
    kb.delete_chunks_for_document(doc.document_id)
    
    chunk2 = DocumentChunk(document_id=doc.document_id, text="Hello world", sequence=0)
    kb.save_chunks([chunk2])
    
    # Search should return exactly 1 result, not 2
    results = kb.retrieve("Hello")
    assert len(results) == 1
    assert results[0].chunk_id == chunk2.chunk_id

def test_technical_identifiers(kb):
    doc = Document(
        filename="tech.txt",
        source_path="tech.txt",
        document_type="txt",
        file_size=10,
        content_hash="h4"
    )
    kb.register_document(doc)
    kb.save_chunks([
        DocumentChunk(document_id=doc.document_id, text="Review SOP-17 and ISO-9001 compliance.", sequence=0)
    ])
    
    results = kb.retrieve("ISO-9001")
    assert len(results) == 1
    assert "ISO-9001" in results[0].text
