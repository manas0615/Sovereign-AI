"""Deterministic renderers for artifacts."""

from typing import List, Dict, Any, Type
import json
from pydantic import BaseModel, Field
from datetime import datetime

from sovereign.core.artifacts.models import ArtifactRequest, ArtifactSourceReference
from sovereign.core.artifacts.engine import ArtifactRenderer
from sovereign.core.state.models import Task, StateItem, EvidenceReference, Finding, Decision, UnresolvedQuestion

class MarkdownRenderer(ArtifactRenderer):
    """Renders structured state deterministically into Markdown."""
    
    def render(self, task: Task, state_items: List[StateItem], evidence: List[EvidenceReference], request: ArtifactRequest) -> str:
        lines = []
        
        # Pre-process state items
        findings = [i for i in state_items if i.item_type == "finding"]
        decisions = [i for i in state_items if i.item_type == "decision"]
        questions = [i for i in state_items if i.item_type == "question"]
        
        # Build evidence map
        ev_map = {e.evidence_id: e for e in evidence}
        
        # Helper to render sections if they exist in request
        sections_to_render = request.requested_sections
        
        lines.append(f"# {request.title}")
        lines.append(f"Task: {task.title}")
        lines.append("")
        
        if "executive_summary" in sections_to_render:
            lines.append("## Executive Summary")
            lines.append(f"Goal: {task.goal}")
            lines.append(f"Status: {task.status.value}")
            lines.append("")
            
        if "findings" in sections_to_render:
            lines.append("## Findings")
            if findings:
                for f in findings:
                    assert isinstance(f, Finding)
                    confidence = getattr(f, "confidence", "unknown")
                    lines.append(f"- **{confidence.upper()}**: {f.statement}")
                    # add provenance if exists
                    if f.evidence_refs:
                        refs = []
                        for ref_id in f.evidence_refs:
                            if ref_id in ev_map:
                                e = ev_map[ref_id]
                                refs.append(f"[{e.source_id}:{e.locator}]")
                        if refs:
                            lines.append(f"  *Sources: {', '.join(refs)}*")
            else:
                lines.append("*No findings recorded.*")
            lines.append("")
            
        if "evidence" in sections_to_render:
            lines.append("## Evidence")
            if evidence:
                for e in evidence:
                    lines.append(f"- **{e.source_id}** (Locator: {e.locator})")
            else:
                lines.append("*No evidence recorded.*")
            lines.append("")
            
        if "unresolved_questions" in sections_to_render:
            lines.append("## Unresolved Questions")
            if questions:
                for q in questions:
                    assert isinstance(q, UnresolvedQuestion)
                    lines.append(f"- {q.question} ({q.status})")
            else:
                lines.append("*No unresolved questions.*")
            lines.append("")
            
        if "decisions" in sections_to_render:
            lines.append("## Decisions")
            if decisions:
                for d in decisions:
                    assert isinstance(d, Decision)
                    lines.append(f"- **Decision:** {d.decision}")
                    lines.append(f"  *Rationale:* {d.rationale}")
            else:
                lines.append("*No decisions recorded.*")
            lines.append("")
            
        if "limitations" in sections_to_render:
            lines.append("## Limitations")
            lines.append("*No explicit limitations recorded in state.*")
            lines.append("")
            
        return "\n".join(lines).strip() + "\n"


# Explicit public JSON schema to prevent dumping internal states
class PublicFinding(BaseModel):
    statement: str
    confidence: str
    sources: List[ArtifactSourceReference]

class PublicDecision(BaseModel):
    decision: str
    rationale: str

class PublicQuestion(BaseModel):
    question: str
    status: str

class PublicArtifactData(BaseModel):
    task_id: str
    title: str
    goal: str
    task_status: str
    generated_at: str
    findings: List[PublicFinding]
    decisions: List[PublicDecision]
    questions: List[PublicQuestion]

class JsonRenderer(ArtifactRenderer):
    """Renders structured state into an explicitly typed JSON artifact."""
    
    def render(self, task: Task, state_items: List[StateItem], evidence: List[EvidenceReference], request: ArtifactRequest) -> str:
        # Build evidence map
        ev_map = {e.evidence_id: e for e in evidence}
        
        public_findings = []
        public_decisions = []
        public_questions = []
        
        for item in state_items:
            if item.item_type == "finding":
                assert isinstance(item, Finding)
                sources = []
                for ref_id in item.evidence_refs:
                    if ref_id in ev_map:
                        e = ev_map[ref_id]
                        sources.append(ArtifactSourceReference(
                            source_id=e.source_id,
                            locator=e.locator,
                            metadata=e.metadata
                        ))
                public_findings.append(PublicFinding(
                    statement=item.statement,
                    confidence=getattr(item, "confidence", "unknown"),
                    sources=sources
                ))
            elif item.item_type == "decision":
                assert isinstance(item, Decision)
                public_decisions.append(PublicDecision(
                    decision=item.decision,
                    rationale=item.rationale
                ))
            elif item.item_type == "question":
                assert isinstance(item, UnresolvedQuestion)
                public_questions.append(PublicQuestion(
                    question=item.question,
                    status=getattr(item, "status", "open")
                ))
                
        data = PublicArtifactData(
            task_id=task.task_id,
            title=task.title,
            goal=task.goal,
            task_status=task.status.value,
            generated_at=datetime.utcnow().isoformat(),
            findings=public_findings,
            decisions=public_decisions,
            questions=public_questions
        )
        
        # Dump using pydantic JSON to ensure strong types and UTF-8 safe output
        return data.model_dump_json(indent=2)


class DocxRenderer(ArtifactRenderer):
    """Renders structured task state deterministically into a Microsoft Word (.docx) deliverable."""

    def render(self, task: Task, state_items: List[StateItem], evidence: List[EvidenceReference], request: ArtifactRequest) -> bytes:
        import io
        import docx
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        doc = docx.Document()

        # Pre-process state items
        findings = [i for i in state_items if i.item_type == "finding"]
        decisions = [i for i in state_items if i.item_type == "decision"]
        questions = [i for i in state_items if i.item_type == "question"]

        ev_map = {e.evidence_id: e for e in evidence}
        sections_to_render = request.requested_sections

        # Document Header
        title_p = doc.add_paragraph()
        title_p.paragraph_format.space_after = Pt(2)
        title_run = title_p.add_run(request.title or "Industrial Analysis Report")
        title_run.font.size = Pt(22)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(15, 23, 42)  # slate-900

        subtitle_p = doc.add_paragraph()
        subtitle_p.paragraph_format.space_after = Pt(14)
        subtitle_run = subtitle_p.add_run("Sovereign AI Governed Industrial Workbench — Verifiable Deliverable")
        subtitle_run.font.size = Pt(10)
        subtitle_run.font.italic = True
        subtitle_run.font.color.rgb = RGBColor(100, 116, 139)  # slate-500

        # Metadata Table / Summary Box
        table = doc.add_table(rows=4, cols=2)
        table.style = 'Table Grid'
        
        meta_rows = [
            ("Task Title", task.title or "N/A"),
            ("Task ID", task.task_id),
            ("Operational Goal", task.goal or "N/A"),
            ("Execution Status", f"{task.status.value} (Empirically Qualified & Governed)"),
        ]
        for row_idx, (k, v) in enumerate(meta_rows):
            cell_k, cell_v = table.rows[row_idx].cells
            cell_k.width = Inches(1.8)
            cell_v.width = Inches(4.7)
            
            pk = cell_k.paragraphs[0]
            pk.paragraph_format.space_before = Pt(2)
            pk.paragraph_format.space_after = Pt(2)
            rk = pk.add_run(k)
            rk.font.bold = True
            rk.font.size = Pt(9.5)
            rk.font.color.rgb = RGBColor(51, 65, 85)
            
            pv = cell_v.paragraphs[0]
            pv.paragraph_format.space_before = Pt(2)
            pv.paragraph_format.space_after = Pt(2)
            rv = pv.add_run(v)
            rv.font.size = Pt(9.5)

        doc.add_paragraph().paragraph_format.space_after = Pt(8)

        # 1. Executive Summary
        if "executive_summary" in sections_to_render:
            h = doc.add_heading(level=1)
            h_run = h.add_run("1. Executive Summary")
            h_run.font.color.rgb = RGBColor(30, 41, 59)
            
            p = doc.add_paragraph()
            p.add_run("Goal: ").font.bold = True
            p.add_run(task.goal or "No explicit goal provided.")
            
            p2 = doc.add_paragraph()
            p2.add_run("Execution Status: ").font.bold = True
            p2.add_run(f"Task completed under status {task.status.value}. All inferences and tool interactions were bounded by task-scoped authority.")

        # 2. Technical Findings
        if "findings" in sections_to_render:
            h = doc.add_heading(level=1)
            h_run = h.add_run("2. Technical Findings")
            h_run.font.color.rgb = RGBColor(30, 41, 59)

            if findings:
                for f in findings:
                    assert isinstance(f, Finding)
                    confidence = getattr(f, "confidence", "unknown")
                    bp = doc.add_paragraph(style='List Bullet')
                    
                    c_run = bp.add_run(f"[{confidence.upper()}] ")
                    c_run.font.bold = True
                    c_run.font.color.rgb = RGBColor(14, 116, 144)  # cyan-700
                    
                    bp.add_run(f.statement or "")

                    if f.evidence_refs:
                        refs = []
                        for ref_id in f.evidence_refs:
                            if ref_id in ev_map:
                                e = ev_map[ref_id]
                                refs.append(f"{e.source_id}:{e.locator}")
                        if refs:
                            src_p = doc.add_paragraph()
                            src_p.paragraph_format.left_indent = Inches(0.4)
                            src_p.paragraph_format.space_after = Pt(4)
                            src_run = src_p.add_run(f"Grounding Evidence: {', '.join(refs)}")
                            src_run.font.italic = True
                            src_run.font.size = Pt(9)
                            src_run.font.color.rgb = RGBColor(100, 116, 139)
            else:
                p = doc.add_paragraph()
                p.add_run("No specific findings recorded in task state.").italic = True

        # 3. Grounding Evidence & Sources
        if "evidence" in sections_to_render:
            h = doc.add_heading(level=1)
            h_run = h.add_run("3. Evidence & Grounding Sources")
            h_run.font.color.rgb = RGBColor(30, 41, 59)

            if evidence:
                for e in evidence:
                    bp = doc.add_paragraph(style='List Bullet')
                    r_id = bp.add_run(f"Source Document: {e.source_id}")
                    r_id.font.bold = True
                    bp.add_run(f" (Locator / Page: {e.locator})")
                    
                    if e.metadata and "text" in e.metadata:
                        snippet = str(e.metadata["text"]).strip()
                        if snippet:
                            snip_p = doc.add_paragraph()
                            snip_p.paragraph_format.left_indent = Inches(0.4)
                            snip_p.paragraph_format.space_after = Pt(4)
                            snip_run = snip_p.add_run(f'"{snippet}"')
                            snip_run.font.size = Pt(9)
                            snip_run.font.italic = True
                            snip_run.font.color.rgb = RGBColor(71, 85, 105)
            else:
                p = doc.add_paragraph()
                p.add_run("No evidence references recorded in task state.").italic = True

        # 4. Unresolved Questions
        if "unresolved_questions" in sections_to_render:
            h = doc.add_heading(level=1)
            h_run = h.add_run("4. Unresolved Inquiries")
            h_run.font.color.rgb = RGBColor(30, 41, 59)

            if questions:
                for q in questions:
                    assert isinstance(q, UnresolvedQuestion)
                    bp = doc.add_paragraph(style='List Bullet')
                    bp.add_run(f"{q.question} ")
                    st_run = bp.add_run(f"({getattr(q, 'status', 'open')})")
                    st_run.font.italic = True
            else:
                p = doc.add_paragraph()
                p.add_run("No unresolved inquiries recorded.").italic = True

        # 5. Governance & Execution Decisions
        if "decisions" in sections_to_render:
            h = doc.add_heading(level=1)
            h_run = h.add_run("5. Governance & Execution Decisions")
            h_run.font.color.rgb = RGBColor(30, 41, 59)

            if decisions:
                for d in decisions:
                    assert isinstance(d, Decision)
                    bp = doc.add_paragraph(style='List Bullet')
                    bp.add_run("Decision: ").font.bold = True
                    bp.add_run(f"{d.decision}\n")
                    rat_run = bp.add_run(f"Rationale: {d.rationale}")
                    rat_run.font.size = Pt(9)
                    rat_run.font.color.rgb = RGBColor(100, 116, 139)
            else:
                p = doc.add_paragraph()
                p.add_run("No explicit decision items recorded.").italic = True

        # 6. Limitations & Governance Disclaimer
        if "limitations" in sections_to_render:
            h = doc.add_heading(level=1)
            h_run = h.add_run("6. Limitations & Governance Notice")
            h_run.font.color.rgb = RGBColor(30, 41, 59)

            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(4)
            p.add_run(
                "This document is an automated industrial analysis deliverable generated under Sovereign AI qualification "
                "governance and cryptographic provenance tracking. All statements are derived strictly from localized model "
                "reasoning bounded by empirical capability passports and linked evidence. This deliverable does not constitute "
                "a manual engineering sign-off or stamped approval."
            ).font.size = Pt(9.5)

        # Save to memory buffer
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()


class XlsxRenderer(ArtifactRenderer):
    """Renders structured task state deterministically into a Microsoft Excel (.xlsx) workbook."""

    def render(self, task: Task, state_items: List[StateItem], evidence: List[EvidenceReference], request: ArtifactRequest) -> bytes:
        import io
        import xlsxwriter

        buf = io.BytesIO()
        wb = xlsxwriter.Workbook(buf, {'in_memory': True})

        # Formats
        header_fmt = wb.add_format({
            'bold': True,
            'bg_color': '#1E293B',
            'font_color': '#FFFFFF',
            'font_size': 11,
            'border': 1
        })
        title_fmt = wb.add_format({
            'bold': True,
            'font_size': 14,
            'font_color': '#0F172A'
        })
        meta_label_fmt = wb.add_format({
            'bold': True,
            'bg_color': '#F1F5F9',
            'font_color': '#334155',
            'border': 1
        })
        cell_fmt = wb.add_format({'border': 1, 'font_size': 10})
        badge_cyan = wb.add_format({'bold': True, 'font_color': '#0E7490', 'border': 1, 'font_size': 10})

        # --- Sheet 1: Executive Summary ---
        ws_summary = wb.add_worksheet("Summary")
        ws_summary.set_column('A:A', 22)
        ws_summary.set_column('B:B', 60)

        ws_summary.write('A1', request.title or "Industrial Analysis Report", title_fmt)
        ws_summary.write('A2', "Sovereign AI Governed Industrial Workbench — Excel Deliverable", wb.add_format({'italic': True, 'font_color': '#64748B'}))

        meta_rows = [
            ("Task Title", task.title or "N/A"),
            ("Task ID", task.task_id),
            ("Operational Goal", task.goal or "N/A"),
            ("Execution Status", task.status.value),
            ("Generated At", datetime.utcnow().isoformat() + "Z"),
            ("Governance Notice", "Automated deliverable bounded by empirical capability passports."),
        ]

        row = 4
        ws_summary.write(row, 0, "Attribute", header_fmt)
        ws_summary.write(row, 1, "Value", header_fmt)
        row += 1
        for k, v in meta_rows:
            ws_summary.write(row, 0, k, meta_label_fmt)
            ws_summary.write(row, 1, v, cell_fmt)
            row += 1

        # --- Sheet 2: Findings & Evidence ---
        findings = [i for i in state_items if i.item_type == "finding"]
        ev_map = {e.evidence_id: e for e in evidence}

        ws_findings = wb.add_worksheet("Technical Findings")
        ws_findings.set_column('A:A', 15)
        ws_findings.set_column('B:B', 50)
        ws_findings.set_column('C:C', 35)

        ws_findings.write('A1', "Confidence", header_fmt)
        ws_findings.write('B1', "Finding Statement", header_fmt)
        ws_findings.write('C1', "Grounding Sources", header_fmt)

        row = 1
        for f in findings:
            confidence = getattr(f, "confidence", "unknown")
            stmt = f.statement or ""
            refs = []
            if f.evidence_refs:
                for ref_id in f.evidence_refs:
                    if ref_id in ev_map:
                        e = ev_map[ref_id]
                        refs.append(f"{e.source_id}:{e.locator}")
            ref_str = ", ".join(refs) if refs else "N/A"

            ws_findings.write(row, 0, confidence.upper(), badge_cyan)
            ws_findings.write(row, 1, stmt, cell_fmt)
            ws_findings.write(row, 2, ref_str, cell_fmt)
            row += 1

        if not findings:
            ws_findings.write(1, 0, "N/A", cell_fmt)
            ws_findings.write(1, 1, "No technical findings recorded.", cell_fmt)
            ws_findings.write(1, 2, "N/A", cell_fmt)

        # --- Sheet 3: Decisions & Inquiries ---
        decisions = [i for i in state_items if i.item_type == "decision"]
        questions = [i for i in state_items if i.item_type == "question"]

        ws_decisions = wb.add_worksheet("Decisions & Inquiries")
        ws_decisions.set_column('A:A', 18)
        ws_decisions.set_column('B:B', 45)
        ws_decisions.set_column('C:C', 45)

        ws_decisions.write('A1', "Type", header_fmt)
        ws_decisions.write('B1', "Item / Question", header_fmt)
        ws_decisions.write('C1', "Rationale / Status", header_fmt)

        row = 1
        for d in decisions:
            ws_decisions.write(row, 0, "DECISION", meta_label_fmt)
            ws_decisions.write(row, 1, d.decision, cell_fmt)
            ws_decisions.write(row, 2, d.rationale or "N/A", cell_fmt)
            row += 1

        for q in questions:
            ws_decisions.write(row, 0, "INQUIRY", meta_label_fmt)
            ws_decisions.write(row, 1, q.question, cell_fmt)
            ws_decisions.write(row, 2, getattr(q, 'status', 'open'), cell_fmt)
            row += 1

        if not decisions and not questions:
            ws_decisions.write(1, 0, "N/A", cell_fmt)
            ws_decisions.write(1, 1, "No decisions or inquiries recorded.", cell_fmt)
            ws_decisions.write(1, 2, "N/A", cell_fmt)

        wb.close()
        return buf.getvalue()


class PptxRenderer(ArtifactRenderer):
    """Renders structured task state deterministically into a Microsoft PowerPoint (.pptx) presentation."""

    def render(self, task: Task, state_items: List[StateItem], evidence: List[EvidenceReference], request: ArtifactRequest) -> bytes:
        import io
        import pptx
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor

        prs = pptx.Presentation()

        # Slide 1: Title Slide (Layout 0)
        title_slide_layout = prs.slide_layouts[0]
        slide1 = prs.slides.add_slide(title_slide_layout)
        title1 = slide1.shapes.title
        subtitle1 = slide1.placeholders[1]

        title1.text = request.title or "Industrial Analysis Report"
        subtitle1.text = f"Task: {task.title}\nGoal: {task.goal}\nSovereign AI Governed Deliverable"

        # Slide 2: Executive Summary & Task Status (Layout 1)
        bullet_layout = prs.slide_layouts[1]
        slide2 = prs.slides.add_slide(bullet_layout)
        slide2.shapes.title.text = "1. Executive Summary"
        tf2 = slide2.placeholders[1].text_frame
        tf2.word_wrap = True

        p = tf2.paragraphs[0]
        p.text = f"Operational Goal: {task.goal or 'N/A'}"
        p.font.size = Pt(16)

        p2 = tf2.add_paragraph()
        p2.text = f"Execution Status: {task.status.value} (Empirically Qualified & Governed)"
        p2.font.size = Pt(16)

        p3 = tf2.add_paragraph()
        p3.text = f"Task ID: {task.task_id}"
        p3.font.size = Pt(14)

        # Slide 3: Technical Findings & Grounding (Layout 1)
        slide3 = prs.slides.add_slide(bullet_layout)
        slide3.shapes.title.text = "2. Technical Findings"
        tf3 = slide3.placeholders[1].text_frame
        tf3.word_wrap = True

        findings = [i for i in state_items if i.item_type == "finding"]
        ev_map = {e.evidence_id: e for e in evidence}

        if findings:
            for idx, f in enumerate(findings[:5]):  # Up to 5 key findings per slide
                confidence = getattr(f, "confidence", "unknown")
                p = tf3.add_paragraph() if idx > 0 else tf3.paragraphs[0]
                p.text = f"[{confidence.upper()}] {f.statement}"
                p.font.size = Pt(14)
                p.font.bold = True

                if f.evidence_refs:
                    refs = []
                    for ref_id in f.evidence_refs:
                        if ref_id in ev_map:
                            e = ev_map[ref_id]
                            refs.append(f"{e.source_id}:{e.locator}")
                    if refs:
                        p_sub = tf3.add_paragraph()
                        p_sub.text = f"    Source Grounding: {', '.join(refs)}"
                        p_sub.font.size = Pt(11)
                        p_sub.font.italic = True
        else:
            tf3.paragraphs[0].text = "No technical findings recorded in task state."
            tf3.paragraphs[0].font.size = Pt(14)

        # Slide 4: Decisions & Inquiries (Layout 1)
        slide4 = prs.slides.add_slide(bullet_layout)
        slide4.shapes.title.text = "3. Decisions & Next Steps"
        tf4 = slide4.placeholders[1].text_frame
        tf4.word_wrap = True

        decisions = [i for i in state_items if i.item_type == "decision"]
        questions = [i for i in state_items if i.item_type == "question"]

        idx = 0
        for d in decisions[:3]:
            p = tf4.add_paragraph() if idx > 0 else tf4.paragraphs[0]
            p.text = f"Decision: {d.decision} (Rationale: {d.rationale})"
            p.font.size = Pt(14)
            idx += 1

        for q in questions[:3]:
            p = tf4.add_paragraph() if idx > 0 else tf4.paragraphs[0]
            p.text = f"Inquiry: {q.question} [{getattr(q, 'status', 'open')}]"
            p.font.size = Pt(14)
            idx += 1

        if idx == 0:
            tf4.paragraphs[0].text = "No explicit decisions or open inquiries recorded."
            tf4.paragraphs[0].font.size = Pt(14)

        # Slide 5: Governance Notice (Layout 1)
        slide5 = prs.slides.add_slide(bullet_layout)
        slide5.shapes.title.text = "4. Governance & Integrity Notice"
        tf5 = slide5.placeholders[1].text_frame
        tf5.word_wrap = True
        p_gov = tf5.paragraphs[0]
        p_gov.text = (
            "This presentation is generated under Sovereign AI qualification governance and cryptographic provenance tracking. "
            "All statements are derived strictly from localized model reasoning bounded by empirical capability passports and linked evidence."
        )
        p_gov.font.size = Pt(13)

        buf = io.BytesIO()
        prs.save(buf)
        return buf.getvalue()


class PdfRenderer(ArtifactRenderer):
    """Renders structured task state deterministically into a PDF (.pdf) deliverable."""

    def render(self, task: Task, state_items: List[StateItem], evidence: List[EvidenceReference], request: ArtifactRequest) -> bytes:
        import io
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=14
        )
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'DocBody',
            parent=styles['Normal'],
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor('#334155')
        )
        bold_body_style = ParagraphStyle(
            'BoldBody',
            parent=body_style,
            fontName='Helvetica-Bold'
        )

        elements = []
        elements.append(Paragraph(request.title or "Sovereign Industrial Analysis Report", title_style))
        elements.append(Paragraph("Sovereign AI Governed Industrial Workbench — Verifiable Deliverable", subtitle_style))

        # Metadata Table
        meta_data = [
            [Paragraph("Task Title", bold_body_style), Paragraph(task.title or "N/A", body_style)],
            [Paragraph("Task ID", bold_body_style), Paragraph(task.task_id, body_style)],
            [Paragraph("Operational Goal", bold_body_style), Paragraph(task.goal or "N/A", body_style)],
            [Paragraph("Execution Status", bold_body_style), Paragraph(f"{task.status.value} (Empirically Qualified & Governed)", body_style)]
        ]
        meta_table = Table(meta_data, colWidths=[130, 374])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 14))

        # Pre-process state items
        findings = [i for i in state_items if i.item_type == "finding"]
        decisions = [i for i in state_items if i.item_type == "decision"]
        questions = [i for i in state_items if i.item_type == "question"]
        ev_map = {e.evidence_id: e for e in evidence}

        # Executive Summary
        elements.append(Paragraph("1. Executive Summary", heading_style))
        elements.append(Paragraph(f"<b>Goal:</b> {task.goal or 'No explicit goal provided.'}", body_style))
        elements.append(Spacer(1, 8))

        # Technical Findings
        elements.append(Paragraph("2. Technical Findings", heading_style))
        if findings:
            for f in findings:
                conf = getattr(f, "confidence", "unknown").upper()
                elements.append(Paragraph(f"• <b>[{conf}]</b> {f.statement}", body_style))
                if f.evidence_refs:
                    refs = [f"{ev_map[r].source_id}:{ev_map[r].locator}" for r in f.evidence_refs if r in ev_map]
                    if refs:
                        elements.append(Paragraph(f"<i>&nbsp;&nbsp;&nbsp;&nbsp;Sources: {', '.join(refs)}</i>", subtitle_style))
                elements.append(Spacer(1, 4))
        else:
            elements.append(Paragraph("No technical findings recorded in task state.", body_style))
        elements.append(Spacer(1, 8))

        # Decisions & Governance
        elements.append(Paragraph("3. Governed Decisions & Authority", heading_style))
        if decisions:
            for d in decisions:
                elements.append(Paragraph(f"• <b>Decision:</b> {d.decision}<br/>&nbsp;&nbsp;<i>Rationale: {d.rationale}</i>", body_style))
                elements.append(Spacer(1, 4))
        else:
            elements.append(Paragraph("No explicit decisions recorded.", body_style))
        elements.append(Spacer(1, 14))

        # Governance Notice
        elements.append(Paragraph("4. Governance & Integrity Notice", heading_style))
        elements.append(Paragraph(
            "This deliverable is generated under Sovereign AI qualification governance and cryptographic provenance tracking. "
            "All assertions are derived from local model inference bounded by task-scoped capability passports and verifiable knowledge grounding.",
            subtitle_style
        ))

        doc.build(elements)
        return buf.getvalue()


