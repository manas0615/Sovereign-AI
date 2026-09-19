# SOVEREIGN AI — EMPIRICAL EVIDENCE & AUDIT ARTIFACT INDEX

This index lists all verified evidence artifacts generated and audited for the Sovereign AI prototype.

---

## 1. Browser & Visual Verification Screenshots (evidence/screenshots/)

| File Name | Page / Workflow | What It Demonstrates |
| :--- | :--- | :--- |
| `01_assistant_chat_baseline.png` | Assistant Chat (`/`) | Full-viewport conversational chat layout, model runtime online status, document scope selector, and example prompt cards. |
| `02_coding_studio_baseline.png` | Coding Studio (`/coding`) | Split-pane interactive editor and terminal console with industrial telemetry analysis presets. |
| `03_knowledge_library_baseline.png` | Knowledge Library (`/knowledge`) | Canonical document deduplication (grouped records), search filter, and chunk inspection modal. |
| `04_governed_tasks_baseline.png` | Governed Tasks (`/tasks`) | Durable SQLite task persistence, execution receipts, and artifact downloads. |
| `05_passports_authority_baseline.png` | Passports & Authority (`/passports`) | Empirical model qualification passports, benchmark scores, and deployment identities. |
| `06_architecture_invariants_baseline.png` | Architecture & Invariants (`/moon`) | P01–P09 package ownership, 7-step governed execution pipeline, and architectural invariants. |
| `07_rag_inspection_response.png` | Conversational RAG (`/`) | Grounded answer on `v204_scanned_inspection.pdf`, synthesized 0.18mm vs 0.10mm exceedance (+0.08mm / +80%), and 5 cited source chunks with SHA-256 digests. |
| `08_coding_studio_execution.png` | Governed Code Execution (`/coding`) | Execution of Pipeline P-102 ultrasonic degradation calculation in restricted subprocess execution with live stdout in 81ms. |
| `09_artifacts_library_grid.png` | Artifacts Library Grid (`/artifacts`) | Multi-format deliverables library with format filtering (DOCX, XLSX, PPTX, PDF, MD, JSON), search, and download controls. |
| `10_artifact_details_modal.png` | Artifact Provenance Modal (`/artifacts`) | Deep metadata inspection showing SHA-256 byte digest, source references, task ID, and section breakdowns. |

---

## 2. Generated Verifiable Deliverables (evidence/artifacts/)

| File Name | Format | Size | Validation Result | Content Summary |
| :--- | :--- | :--- | :--- | :--- |
| `sample_deliverable_docx.docx` | DOCX (Word) | 37.6 KB (37,605 B) | Structurally parsed via `python-docx` (15 paragraphs, 1 table) | Equipment integrity report, metadata grid, findings, and governance notice. |
| `sample_deliverable_xlsx.xlsx` | XLSX (Excel) | 7.4 KB (7,357 B) | Structurally parsed via `openpyxl`/zipfile (12 XML package members) | Multi-sheet analysis workbook with executive summary, metadata, and grounded findings table. |
| `sample_deliverable_pptx.pptx` | PPTX (PowerPoint) | 32.4 KB (32,379 B) | Structurally parsed via `python-pptx` (5 slides) | Industrial assessment briefing with executive summary, technical findings, and decisions. |
| `sample_deliverable_pdf.pdf` | PDF | 3.0 KB (3,007 B) | Structurally parsed via `pypdf` (1 page, valid `%PDF-1.4` header) | Formal approval note with title styling, table grids, and qualification disclosures. |
| `sample_deliverable_markdown.md` | Markdown | 641 B | Plaintext UTF-8 validated (20 lines) | Structured markdown report with provenance tags and section dividers. |
| `sample_deliverable_json.json` | JSON | 831 B | Validated against schema | Machine-readable task manifest with typed findings, decisions, and UTC timestamps. |

---

## 3. Automated Test & Security Logs (evidence/logs/)

| File Name | Scope | Result | Summary |
| :--- | :--- | :--- | :--- |
| `pytest_full_results.log` | Full backend test suite | **169 / 169 Passed (100%)** | Verified runtime gateway, sequential model swapping, restricted execution, SQLite FTS5 retrieval, qualification persistence, state transactions, and format renderers. |
| `network_audit.json` | Outbound socket monitoring | **0 External WAN Sockets** | Monitored `python.exe` (backend) and `node.exe` (frontend) processes. All observed connections strictly bound to localhost loopback (`127.0.0.1` and `::1`). |
| `governance_negatives.json` | Negative security & governance tests | **6 / 6 Passed** | Verified syntax error handling, execution timeout teardown, workspace path traversal rejection, unallowlisted tool rejection, unknown capability routing fail-closed, and authority policy denial. |
