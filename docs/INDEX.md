# Sovereign AI — Master Documentation & Evidence Index

This document provides a comprehensive navigation index for the technical specifications, architectural blueprints, empirical evaluation evidence, and operational runbooks of the Sovereign AI Workbench.

---

## 1. System Architecture & Foundation (docs/architecture/)

The architectural baseline is partitioned across 10 formal package specifications (P00–P09):

| Package | Document ID | Title | Scope & Responsibility |
| :--- | :--- | :--- | :--- |
| **P00** | [SAI-DOC-001](architecture/project-charter.md) | Project Charter | Industrial mission, threat model, sovereignty principles, and non-negotiables. |
| **P00** | [SAI-DOC-002](architecture/system-architecture.md) | System Architecture | Authoritative high-level topology, component boundaries, and data flows. |
| **P01** | [SAI-DOC-005](architecture/model-gateway-and-routing.md) | Model Gateway & Runtime | `llama.cpp` serving adapter, sequential model swapping, GGUF quantization profiles. |
| **P02** | [SAI-DOC-006](architecture/data-context-memory-architecture.md) | Persistent Task State | Durable SQLite state ledger, context budgeting, token allocation, transaction rollbacks. |
| **P03** | [SAI-DOC-007](architecture/knowledge-retrieval-and-document-intelligence.md) | Knowledge & Document Intelligence | Hybrid RAG (SQLite FTS5 BM25 + ChromaDB), scanned PDF OCR, citation ledger. |
| **P04** | [SAI-DOC-008](architecture/tool-execution-and-sandbox.md) | Governed Tool Execution | Restricted execution boundary, path confinement, timeout enforcement, sanitized env. |
| **P05** | [SAI-DOC-009](architecture/agent-host-and-orchestration.md) | Agent Host & Orchestration | ReAct execution loop, task characterization, capability routing, verification gating. |
| **P06** | [SAI-DOC-010](architecture/artifact-engine-and-verification.md) | Artifact Engine & Verification | Multi-format business document generation (DOCX, XLSX, PPTX, PDF) with SHA-256 proofs. |
| **P07** | [SAI-DOC-011](architecture/ui-api-and-user-workspace.md) | API & User Workspace | FastAPI REST / SSE endpoints, React 19 TypeScript workspace, WebSocket streaming. |
| **P08** | [SAI-DOC-003](architecture/security-and-sovereignty.md) | Security & Sovereignty | In-process isolation, zero WAN socket binding, threat vectors, authority evaluator. |
| **P08** | [SAI-DOC-004](architecture/testing-validation-and-demo-protocol.md) | Testing & Validation Protocol | 177-test verification protocol, benchmark criteria, negative test gates. |
| **P08** | [SAI-DOC-012](architecture/INNOVATION_MOON_AUDIT.md) | Moonshot Innovation Audit | Technical breakdown of the Governance Triad and deployment-capability identities. |

---

## 2. Empirical Benchmark & Qualification Evidence

| Directory / File | Description | Key Findings |
| :--- | :--- | :--- |
| [`docs/evaluation/BENCHMARK_METHODOLOGY.md`](evaluation/BENCHMARK_METHODOLOGY.md) | Methodology & Protocol | Comprehensive 50-task / 150-trial benchmark design and qualification rules. |
| [`benchmarks/evaluations/llama_eval_20260919/evaluation_report.md`](../benchmarks/evaluations/llama_eval_20260919/evaluation_report.md) | Final Evaluation Report | **98.0%** Final Submission Correctness (146/149); **95.3%** First Submission Correctness (142/149). |
| [`benchmarks/evaluations/llama_eval_20260919/benchmark_metrics.json`](../benchmarks/evaluations/llama_eval_20260919/benchmark_metrics.json) | Machine-Readable Metrics | Full accounting of all 150 trials, terminal failure categories, and evaluable subsets. |
| [`benchmarks/evaluations/llama_eval_20260919/pilot_results.json`](../benchmarks/evaluations/llama_eval_20260919/pilot_results.json) | Capability Passports | Verified qualification passports for `DocumentRetrieval_v1`, `AutomatedCoding_v1`, `AgentDecision_v1`. |
| [`benchmarks/evaluations/llama_eval_20260919/resource_metrics.csv`](../benchmarks/evaluations/llama_eval_20260919/resource_metrics.csv) | Telemetry Time Series | Continuous 2-second VRAM (2115 MiB peak) and system RAM tracking. |
| [`benchmarks/evaluations/llama_eval_20260919/limitations.md`](../benchmarks/evaluations/llama_eval_20260919/limitations.md) | Scope & Constraints | Formal disclosure of schema-level qualification semantics and native Windows execution mode. |
| [`benchmarks/results_full.jsonl`](../benchmarks/results_full.jsonl) | Raw Benchmark Output | Complete per-trial logs, prompts, extracted code, and verification outcomes. |
| [`benchmarks/tasks.json`](../benchmarks/tasks.json) | 50 Industrial Tasks | Full task definitions spanning engineering calculations, telemetry parsing, and control loops. |

---

## 3. Operational Runbooks & Demonstrations (docs/runbooks/)

* [**SIH Demo Runbook**](runbooks/SOVEREIGN_AI_SIH_DEMO_RUNBOOK.md): Step-by-step presentation script for the live SIH 2026 jury evaluation.
* [**Final Validation Report**](runbooks/FINAL_VALIDATION_REPORT.md): System integration test results and automated verification sign-offs.

---

## 4. Visual Evidence & Artifact Provenance (evidence/)

* [**Master Evidence Index**](../evidence/EVIDENCE_INDEX.md): Catalog of 10 baseline UI screenshots, 6 sample multi-format business deliverables, network socket audits, and negative security logs.
* [**Sample Deliverables**](../evidence/artifacts/): Formally generated `.docx`, `.xlsx`, `.pptx`, `.pdf`, `.md`, and `.json` files with SHA-256 byte manifests.
* [**Network Socket Audit**](../evidence/logs/network_audit.json): Network monitoring confirming zero external WAN outbound sockets.
