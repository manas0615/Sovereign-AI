import io
import zipfile
import xml.etree.ElementTree as ET
import pytest

from sovereign.core.state.models import Task, TaskStatus, Finding, Decision, EvidenceReference, UnresolvedQuestion
from sovereign.core.artifacts.models import ArtifactRequest, ArtifactType
from sovereign.infrastructure.artifacts.renderers import XlsxRenderer


def test_xlsx_renderer_valid_document():
    task = Task(title='Pipeline P-102 Ultrasonic Survey', goal='Audit wall thickness against ASME standard', status=TaskStatus.COMPLETED)
    ev1 = EvidenceReference(source_id='doc_ndt_report_01', locator='Sheet A-1', metadata={'text': 'Nominal thickness 12.4mm.'})
    f1 = Finding(statement='Corrosion allowance remaining is 3.2mm.', confidence='high', evidence_refs=[ev1.evidence_id])
    d1 = Decision(decision='APPROVE_OPERATION', rationale='Thickness meets safety margins.')
    q1 = UnresolvedQuestion(question='Schedule next ultrasonic survey in Q3?', status='PENDING')

    req = ArtifactRequest(
        task_id=task.task_id,
        artifact_type=ArtifactType.XLSX,
        title='Industrial Data Sheet: Pipeline P-102',
        requested_sections=['executive_summary', 'findings', 'evidence', 'decisions', 'unresolved_questions']
    )

    renderer = XlsxRenderer()
    xlsx_bytes = renderer.render(task, [f1, d1, q1], [ev1], req)

    assert isinstance(xlsx_bytes, bytes)
    assert len(xlsx_bytes) > 0

    with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as zf:
        namelist = zf.namelist()
        assert '[Content_Types].xml' in namelist
        assert 'xl/workbook.xml' in namelist
        assert 'xl/worksheets/sheet1.xml' in namelist
        assert 'xl/worksheets/sheet2.xml' in namelist
        assert 'xl/worksheets/sheet3.xml' in namelist

        # Inspect workbook XML for sheet names
        wb_xml = zf.read('xl/workbook.xml')
        root = ET.fromstring(wb_xml)
        sheet_names = [elem.attrib.get('name') for elem in root.iter() if elem.tag.endswith('sheet')]
        assert 'Summary' in sheet_names
        assert 'Technical Findings' in sheet_names
        assert 'Decisions & Inquiries' in sheet_names

        # Check shared strings or sheet content
        if 'xl/sharedStrings.xml' in namelist:
            ss_xml = zf.read('xl/sharedStrings.xml').decode('utf-8')
            assert 'Pipeline P-102' in ss_xml
            assert 'Corrosion allowance remaining' in ss_xml
            assert 'APPROVE_OPERATION' in ss_xml


def test_xlsx_renderer_empty_sections():
    task = Task(title='Empty Data Task', goal='No items present')
    req = ArtifactRequest(
        task_id=task.task_id,
        artifact_type=ArtifactType.XLSX,
        title='Empty Sheet',
        requested_sections=['executive_summary', 'findings', 'evidence', 'decisions']
    )

    renderer = XlsxRenderer()
    xlsx_bytes = renderer.render(task, [], [], req)

    with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as zf:
        assert 'xl/workbook.xml' in zf.namelist()
        if 'xl/sharedStrings.xml' in zf.namelist():
            ss_xml = zf.read('xl/sharedStrings.xml').decode('utf-8')
            assert 'No technical findings recorded' in ss_xml
