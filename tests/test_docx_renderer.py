"""Unit tests for DocxRenderer in Sovereign AI."""
import io
import zipfile
import pytest
import docx

from sovereign.core.state.models import Task, TaskStatus, Finding, Decision, EvidenceReference, UnresolvedQuestion
from sovereign.core.artifacts.models import ArtifactRequest, ArtifactType
from sovereign.infrastructure.artifacts.renderers import DocxRenderer


def test_docx_renderer_valid_document():
    """Verify DocxRenderer produces a valid OOXML .docx document with proper structure."""
    task = Task(title="Flange V-204 Inspection", goal="Verify seal integrity and wear", status=TaskStatus.COMPLETED)
    ev1 = EvidenceReference(source_id="doc_inspection_001", locator="Page 2", metadata={"text": "Seal wear measured at 0.15mm."})
    f1 = Finding(statement="Critical seal wear detected on main flange.", confidence="high", evidence_refs=[ev1.evidence_id])
    d1 = Decision(decision="REPLACE_SEAL", rationale="Wear exceeds 0.10mm operating limit.")
    q1 = UnresolvedQuestion(question="Is replacement gasket part in stock?", status="OPEN")

    req = ArtifactRequest(
        task_id=task.task_id,
        artifact_type=ArtifactType.DOCX,
        title="Industrial Analysis Note: Flange V-204",
        requested_sections=["executive_summary", "findings", "evidence", "unresolved_questions", "decisions", "limitations"]
    )

    renderer = DocxRenderer()
    docx_bytes = renderer.render(task, [f1, d1, q1], [ev1], req)

    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 0

    # Verify it is a valid Zip/OOXML archive
    with zipfile.ZipFile(io.BytesIO(docx_bytes)) as zf:
        assert "[Content_Types].xml" in zf.namelist()
        assert "word/document.xml" in zf.namelist()

    # Load with python-docx
    doc = docx.Document(io.BytesIO(docx_bytes))

    # Verify Title & Subtitle
    paragraphs_text = [p.text for p in doc.paragraphs if p.text]
    full_text = "\n".join(paragraphs_text)

    assert "Industrial Analysis Note: Flange V-204" in full_text
    assert "Sovereign AI Governed Industrial Workbench" in full_text
    assert "1. Executive Summary" in full_text
    assert "2. Technical Findings" in full_text
    assert "3. Evidence & Grounding Sources" in full_text
    assert "4. Unresolved Inquiries" in full_text
    assert "5. Governance & Execution Decisions" in full_text
    assert "6. Limitations & Governance Notice" in full_text

    # Verify Metadata table
    assert len(doc.tables) >= 1
    table_text = " ".join(cell.text for row in doc.tables[0].rows for cell in row.cells)
    assert "Flange V-204 Inspection" in table_text
    assert task.task_id in table_text

    # Verify Findings and citations
    assert "Critical seal wear detected on main flange." in full_text
    assert "doc_inspection_001:Page 2" in full_text

    # Verify Decisions and Inquiries
    assert "REPLACE_SEAL" in full_text
    assert "Is replacement gasket part in stock?" in full_text


def test_docx_renderer_empty_sections():
    """Verify DocxRenderer gracefully renders empty state items without error."""
    task = Task(title="Empty Analysis", goal="No items present")
    req = ArtifactRequest(
        task_id=task.task_id,
        artifact_type=ArtifactType.DOCX,
        title="Empty Report",
        requested_sections=["executive_summary", "findings", "evidence", "decisions", "unresolved_questions", "limitations"]
    )

    renderer = DocxRenderer()
    docx_bytes = renderer.render(task, [], [], req)

    doc = docx.Document(io.BytesIO(docx_bytes))
    full_text = "\n".join(p.text for p in doc.paragraphs)

    assert "No specific findings recorded in task state." in full_text
    assert "No evidence references recorded in task state." in full_text
    assert "No unresolved inquiries recorded." in full_text
    assert "No explicit decision items recorded." in full_text


def test_docx_renderer_unicode_and_special_characters():
    """Verify DocxRenderer correctly preserves Unicode symbols and industrial notation."""
    task = Task(title="Sensor Calibration — Unit #7", goal="Temperature ΔT <= 0.5°C & Pressure σ <= 2.4 MPa")
    ev = EvidenceReference(source_id="doc_sensor_alpha", locator="Section 4.2", metadata={"text": "Measured delta-T = 0.42 C."})
    f = Finding(statement="Temperature deviation delta-T = 0.42 C satisfies ISO-9001 standard.", confidence="high", evidence_refs=[ev.evidence_id])

    req = ArtifactRequest(
        task_id=task.task_id,
        artifact_type=ArtifactType.DOCX,
        title="Calibration Certificate: Unit #7",
        requested_sections=["executive_summary", "findings", "evidence"]
    )

    renderer = DocxRenderer()
    docx_bytes = renderer.render(task, [f], [ev], req)

    doc = docx.Document(io.BytesIO(docx_bytes))
    full_text = "\n".join(p.text for p in doc.paragraphs)

    assert "Calibration Certificate: Unit #7" in full_text
    assert "doc_sensor_alpha" in full_text
    assert "Section 4.2" in full_text
    assert "ISO-9001" in full_text
