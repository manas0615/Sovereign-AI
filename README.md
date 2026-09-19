# Sovereign AI Workbench

> **Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work**  
> *Smart India Hackathon (SIH) 2026 Prototype*

---

## 1. Overview

**Sovereign AI** is a self-hosted, model-agnostic agentic AI workbench designed for confidential industrial environments—such as public sector undertakings (PSUs), defence manufacturing, refineries, and critical infrastructure facilities. 

In these settings, sensitive intellectual property (engineering drawings, P&IDs, equipment inspection sheets, maintenance logs, proprietary code, and SOPs) cannot be transmitted to external cloud AI APIs due to strict data residency and security mandates.

Sovereign AI brings the AI execution environment directly to the enterprise's private infrastructure:
* **Native Windows Turnkey Runtime:** Operates locally on standard enterprise Windows workstations without Docker or hypervisor virtualization overhead.
* **Local Open-Weight Inference:** Powered by `llama.cpp` running quantized GGUF models (`Llama-3.2`, `Qwen2.5-Coder`, `Mistral-7B`, `DeepSeek-R1-Distill`) with CPU/GPU offloading.
* **The Governance Triad ($\text{Configuration} \neq \text{Qualification} \neq \text{Authority}$):** Replaces blind model trust with empirical capability benchmarks (`Model Passports`). Models must pass verified task evaluation suites before being granted tool execution permits.
* **Local Hybrid Knowledge Engine:** Ingests technical manuals, P&IDs, and scanned PDF inspection records using SQLite FTS5 BM25 lexical search, ChromaDB vector embeddings, and an OCR text extraction pipeline.
* **Governed In-Process Tool Execution:** Restricted subprocess execution boundary with timeout enforcement, path confinement, and sanitized environments.
* **Independent Trusted Verification:** Programmatic test harnesses evaluate generated engineering code against acceptance criteria without relying on model self-assertions.
* **Verifiable Business Artifacts:** Generates production-ready Word (`.docx`), Excel (`.xlsx`), PowerPoint (`.pptx`), and PDF (`.pdf`) deliverables accompanied by immutable SHA-256 byte manifests and complete source citations.

---

## 2. System Architecture

```text
                      [ React 18 / TypeScript Web Workspace ]
                                         │
                                         ▼  (REST / SSE)
                        [ FastAPI Application Gateway ]
                                         │
                                         ▼
                             [ Agent Host Orchestrator ]
                     (SQLite Durable Task State & Checkpoints)
                                         │
       ┌────────────────────────┬────────┴────────┬────────────────────────┐
       ▼                        ▼                 ▼                        ▼
[Model Gateway & Router] [Hybrid Knowledge RAG] [Governed Tool Boundary] [Artifact Engine]
  • llama.cpp Serving      • SQLite FTS5 BM25     • Subprocess Sandbox     • DOCX, XLSX, PPTX, PDF
  • Capability Contracts   • ChromaDB Embeddings  • Timeout / Path Limits  • SHA-256 Proofs
  • Model Passports Gate   • Scanned PDF OCR      • Programmatic Verifier  • Provenance Ledger
```

---

## 3. Repository Structure

```
.
├── src/sovereign/               # Core backend package
│   ├── core/                    # Domain models, agent host, router, qualification, authority
│   ├── application/             # FastAPI routes, services, request/response schemas
│   └── infrastructure/          # llama.cpp adapter, SQLite repos, tool executor, renderers
│
├── frontend/                    # React 18 + TypeScript + Vite single-page application
│   └── src/                     # 7 Workspaces: Chat, Coding, Knowledge, Artifacts, Tasks, Passports, Invariants
│
├── benchmarks/                  # Evaluation suites, task definitions, and benchmark harnesses
│   ├── coding/                  # Full automated coding benchmark runner
│   ├── qualification/           # Empirical model qualification test scripts
│   └── results/                 # Verified benchmark results & evaluation summaries
│
├── docs/                        # Authoritative documentation and specifications
│   ├── architecture/            # Baseline architecture specifications (P00-P11)
│   ├── runbooks/                # Video demonstration and operational runbooks
│   └── presentations/           # SIH 2026 presentation decks and slide previews
│
├── evidence/                    # Curated empirical evidence & audit artifacts
│   ├── artifacts/               # Sample validated multi-format deliverables
│   ├── logs/                    # Test logs, socket network audits, negative governance logs
│   ├── screenshots/             # Baseline UI screenshots
│   └── EVIDENCE_INDEX.md        # Master evidence index
│
├── scripts/                     # Developer tooling & diagnostics
│   ├── setup/                   # Environment setup and hardware validation scripts
│   ├── diagnostics/             # Database, host, and network inspection utilities
│   └── validation/              # Automated testing and validation phase runners
│
├── tests/                       # Automated Pytest suite (177 unit & integration tests)
├── archive/                     # Historical one-off experiments and patches
│
├── run_server.py                # Primary backend entrypoint
├── requirements.txt             # Core dependencies
├── requirements-dev.txt         # Development & test dependencies
├── pytest.ini                   # Pytest test configuration
├── .env.example                 # Environment configuration template
└── .gitignore                   # Git exclusion rules
```

---

## 4. Quickstart Guide

### Prerequisites
* Windows 10/11 (64-bit)
* Python 3.11+
* Node.js 18+ (for frontend workspace)
* `llama-server.exe` (from llama.cpp release) and quantized GGUF weights

### 4.1 Backend Setup

```powershell
# 1. Create virtual environment and install dependencies
.\scripts\setup\setup.ps1 -InstallDev

# 2. Configure local environment
Copy-Item .env.example .env
# Edit .env with your local llama_server_path and model_path

# 3. Launch backend server (http://127.0.0.1:8000)
python run_server.py
```

### 4.2 Frontend Setup

```powershell
# In a separate terminal
cd frontend
npm install
npm run dev
# Open browser at http://localhost:5173
```

---

## 5. Testing & Verification

```powershell
# Run the automated test suite (177 tests)
pytest -v

# Or use the validation runner script
.\scripts\validation\test.ps1

# Run frontend production build validation
cd frontend
npm run build
```

---

## 6. Operating Disclosures & Boundaries

* **Localhost Operation:** Process-level socket monitoring confirms backend and frontend communicate over loopback (`127.0.0.1`). Full physical air-gapping requires disconnecting host network interfaces.
* **Execution Boundary:** Code execution runs in a governed subprocess with environment sanitization, execution timeouts, and path restrictions; OS-level container isolation is planned for future hardening.
* **Document Processing:** Scanned documents and inspection sheets are processed via a local OCR pipeline prior to LLM reasoning.
* **Qualification Scope:** Models earn capability contracts strictly for benchmarked task types; models are not blindly trusted for arbitrary tasks.
