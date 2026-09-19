# SOVEREIGN AI — SIH 2026 VIDEO DEMONSTRATION RUNBOOK

This runbook details the exact steps, prompts, and observables to record an evidence-driven demonstration video of the Sovereign AI prototype.

---

## 1. Prerequisites & Services Startup

### 1.1 Start the Python Backend
Open a terminal in the project root (`c:\Users\Dell\Desktop\Sovereign AI`):
```powershell
python run_server.py
```
* **Endpoint:** `http://127.0.0.1:8000`
* **Log Confirmation:** Uvicorn running on `127.0.0.1:8000`, SQLite repository initialized.

### 1.2 Start the Vite Frontend
Open a second terminal in the `frontend` directory:
```powershell
cd frontend
npm run dev
```
* **Browser URL:** `http://localhost:5173`

---

## 2. Step-by-Step Video Demonstration Sequence

### Scene 1: Conversational Workbench & Model Runtime (0:00 - 0:30)
* **Screen:** `http://localhost:5173/`
* **Visuals:** Full-viewport dark layout with left sidebar showing 7 workspaces: Assistant Chat, Coding Studio, Knowledge Library, Artifacts Library, Governed Tasks, Passports & Authority, and Architecture & Invariants. Status footer shows `Model Runtime (P01): ONLINE (127.0.0.1)` and `Execution Boundary: Subprocess Sandbox (P04)`.
* **Narration:** *"Welcome to Sovereign AI, a local, on-premise agentic AI workbench designed for sensitive industrial knowledge work—refineries, power plants, and defense facilities where cloud AI and external data exfiltration are prohibited."*

### Scene 2: Knowledge Library & Deduplicated Ingestion (0:30 - 1:00)
* **Action:** Click **Knowledge Library** in the sidebar (`/knowledge`).
* **Visuals:** Show canonical document cards deduplicated by filename with chunk counts, OCR status, and ingestion timestamps.
* **Interaction:** Type `v204` into the search bar. Expand `v204_scanned_inspection.pdf`. Click **Chunks** to view raw OCR text blocks and their SHA-256 chunk hashes in the modal.
* **Narration:** *"The Knowledge Library ingests scanned PDFs, OCR records, and standards locally into a SQLite FTS5 database with cryptographic hash tracking. Duplicate uploads are transparently grouped without losing provenance."*

### Scene 3: Grounded Conversational RAG (1:00 - 2:00)
* **Action:** Return to **Assistant Chat** (`/`).
* **Interaction:** Click the preset prompt or enter:
  > *"According to the uploaded vessel inspection SOP, what is the allowable seal wear tolerance, and does inspection V-204 exceed it?"*
* **Observable Result:**
  * Grounded factual synthesis citing retrieved evidence: Allowable tolerance is **0.10 mm**, V-204 recorded wear is **0.15 mm**, exceeding the limit by **+0.05 mm (+50%)**. Recommendation: Replace main flange seal immediately before resuming operation.
  * Expand the **Grounded Source Evidence** drawer to show the cited chunks from `v204_scanned_inspection.pdf`.
* **Narration:** *"The assistant queries local FTS5 BM25 indexed chunks, grounding its reasoning in actual OCR text. It cites exact chunk IDs and SHA-256 digests, anchoring findings in retrieved evidence."*

### Scene 4: Automated Governed Coding & Trusted Verification (2:00 - 2:45)
* **Action:** Click **Coding Studio** (`/coding`).
* **Interaction:** In the **Natural-Language Coding Prompt** box, submit:
  > *"Write a Python function is_valid_email(email) that validates simple email format. Include tests for valid and invalid examples. Run the tests and explain the result."*
* **Action:** Click **Submit to Local LLM**.
* **Observable Result:**
  * **Capability Routing:** Routed deterministically to `AutomatedCoding_v1` and authorized against the qualified `Llama-3.2-3B-Instruct` passport.
  * **Code Generation:** Local LLM outputs the structured Python implementation and dispatches tool action `execute_python`.
  * **Governed P04 Execution:** Executes inside the restricted task workspace (`ExecutionBoundary`) with a 10s timeout.
  * **Trusted Verification Telemetry:** System independent test harness evaluates the generated function against 8 acceptance test cases (standard emails, subdomains, tags, invalid syntax, spaces, consecutive dots).
  * **Status Semantics:** Displays `Generated: Yes`, `Execution Status: Executed (P04)`, `Verification Status: Verification Passed` (8/8 checks passed), and `Retry Count: 1/3 max`.
* **Narration:** *"For engineering and custom validation logic, the local model automatically generates Python code and submits it to the P04 execution boundary. Crucially, the system does not rely on model self-assertions or stdout print markers—an independent trusted verification harness evaluates the code against strict acceptance criteria before marking the task verified. Restricted subprocess execution with configured limits; no OS-level isolation is provided."*

### Scene 5: Artifacts Library & Deliverable Verification (2:45 - 3:30)
* **Action:** Click **Artifacts Library** in the sidebar (`/artifacts`).
* **Visuals:** Filter deliverables across DOCX, XLSX, PPTX, PDF, Markdown, and JSON.
* **Interaction:** Click **View Details** on a DOCX or PDF deliverable to display its SHA-256 hash, task reference, and rendered sections.
* **Action:** Click **Download** and show the downloaded Word or PDF file opening cleanly in the local office viewer.
* **Narration:** *"The Artifacts Library allows users to discover, inspect, and download generated deliverables. Every file provides a SHA-256 byte digest allowing users to verify they match the exact generated byte stream. This digest does not independently prove the file's engineering conclusions are truthful or correct."*

### Scene 6: Passports, Authority & Architecture Invariants (3:30 - 4:15)
* **Action:** Click **Passports & Authority** (`/passports`) to show empirical qualification scores and capability contracts (`general_reasoning:v1`, `document_ocr:v1`).
* **Action:** Click **Architecture & Invariants** (`/moon`) to review the 7-step execution chain and core principle: *Configuration ≠ Qualification ≠ Authority*.
* **Narration:** *"Every model deployment must be empirically benchmarked to earn a Capability Passport before receiving task-scoped execution permits."*

### Scene 7: Network Sovereignty Verification (4:15 - 4:45)
* **Action:** Run the network monitor script in terminal:
  ```powershell
  python scratch/monitor_network.py
  ```
* **Observable Result:** Socket observation utility confirms that established and listening sockets for backend (`python.exe`) and frontend (`node.exe`) are bound to loopback. 
* **Narration:** *"During the observation window, the utility detected no non-loopback connections among the monitored processes. This does not rule out brief, blocked, or unobserved network activity."*

---

## 3. Disclosures & Operating Boundaries
* **Inference Latency:** Running on CPU-only local hardware yields ~2-4s per response.
* **Vision / Ingestion:** Scanned-document OCR is supported. Genuine vision-model interpretation of raw images, handwriting, or visual diagrams is not supported in this prototype.
* **Physical Isolation:** While process-level socket monitoring confirms local-only connections, host machine network interfaces should be disconnected for an absolute physical air-gap demonstration.
