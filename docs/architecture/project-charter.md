# `01-project-charter.md`

````markdown
# Sovereign AI Workbench
## Project Charter & System Definition

**Project:** Sovereign AI — SIH 2026 Prototype  
**Document:** Project Charter & System Definition  
**Document ID:** SAI-DOC-001  
**Status:** FROZEN — BASELINE  
**Version:** 1.0  
**Last Updated:** 2026-08-25  

---

# 1. Purpose

This document defines the authoritative purpose, scope, objectives, boundaries, terminology, and engineering principles of the Sovereign AI Workbench prototype.

All subsequent architecture specifications, subsystem specifications, implementation plans, tests, and engineering decisions MUST conform to this document.

If a later implementation requirement conflicts with this document, the conflict MUST be explicitly identified and resolved before implementation proceeds.

The system described here is a prototype for the Smart India Hackathon (SIH) 2026 problem statement:

> **Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work**

The prototype is intended to demonstrate that useful agentic AI workflows can be executed entirely within an organization's local infrastructure without requiring confidential data to be sent to cloud AI providers.

---

# 2. Problem Definition

Industrial organizations, PSUs, defence-linked manufacturing organizations, refineries, engineering organizations, and government offices routinely process sensitive information such as:

- Engineering documents
- Piping & Instrumentation Diagrams (P&IDs)
- Inspection reports
- Maintenance records
- Internal correspondence
- Standard Operating Procedures (SOPs)
- Technical manuals
- Financial information
- Vendor negotiations
- Internal software/code
- Unreleased designs
- Business strategies
- Scanned documents
- Photographs
- Engineering drawings

This information may be confidential and subject to organizational policies that prevent it from being transmitted to external cloud AI systems.

At the same time, these organizations perform large amounts of repetitive knowledge work involving:

- Reading and understanding documents
- Extracting findings
- Comparing information against procedures
- Performing calculations
- Writing approval notes
- Preparing reports and presentations
- Writing and testing internal code
- Searching organizational knowledge
- Reviewing scanned material
- Converting information into business deliverables

The central problem is therefore:

> **How can an organization obtain the productivity benefits of modern agentic AI while keeping sensitive information, models, tools, intermediate state, and generated artifacts inside its own security boundary?**

Sovereign AI addresses this problem by bringing the AI execution environment to the organization's data rather than sending the organization's data to an external AI service.

---

# 3. Core System Proposition

Sovereign AI is a:

> **Self-hosted, model-agnostic, agentic AI workbench that operates within an organization's infrastructure and can reason over private enterprise knowledge, use governed local tools, verify its work, and produce auditable business deliverables without requiring external AI services.**

The system is NOT intended to be merely:

- A local chatbot
- A local LLM interface
- A basic RAG application
- A document summarizer
- A collection of unrelated AI utilities

The central objective is to demonstrate a **private AI worker** capable of executing multi-step work.

---

# 4. Core Product Principle

The system follows the following fundamental workflow:

```text
User Goal
    ↓
Understand / Plan
    ↓
Retrieve Private Evidence
    ↓
Construct Bounded Working Context
    ↓
Select Appropriate Local Model / Inference Profile
    ↓
Reason
    ↓
Use Governed Local Tools
    ↓
Observe Results
    ↓
Update Persistent Task State
    ↓
Verify
    ↓
Generate Work Product
    ↓
Record Provenance + Audit Trail
````

The system must be designed around **execution**, not merely conversation.

---

# 5. Sovereignty Principle

Sovereignty is a system property, not a marketing statement.

For the prototype, confidential task data MUST remain inside the local execution environment.

The architecture MUST NOT require:

* Cloud LLM APIs
* External inference APIs
* Cloud-hosted embeddings
* External OCR APIs
* External document-processing APIs
* External agent services
* External tool execution services
* External telemetry for normal operation

The prototype MUST provide a demonstrable mechanism for showing that no external network communication is required during normal AI execution.

The eventual demonstration should include visible evidence such as:

* Network monitoring
* Egress logs
* Local service inspection
* Firewall/egress controls
* Audit records

The exact mechanism will be defined in the security specifications.

---

# 6. Prototype Objective

The prototype must demonstrate a coherent end-to-end sovereign AI workflow on constrained local hardware.

The prototype is NOT required to reproduce the infrastructure of a production enterprise deployment.

Instead, it must prove that the architecture and core workflow are technically feasible.

The prototype must demonstrate:

1. Local open-weight model inference.
2. Model abstraction through a Model Gateway.
3. Hardware/resource-aware inference configuration.
4. Bounded context management.
5. Persistent task state outside the model.
6. Local organizational knowledge retrieval.
7. Agentic multi-step execution.
8. Governed local tool execution.
9. Sandboxed code execution.
10. Deterministic calculation/verification where applicable.
11. Multimodal/scanned-document processing.
12. Generation of real business artifacts.
13. Source/evidence provenance.
14. Audit logging.
15. Demonstrable absence of required external AI/network calls.

---

# 7. Current Laptop Development Profile

The prototype is being developed initially on constrained hardware.

Current measured development hardware:

```text
CPU:
Intel Core i7-9850H
6 physical cores / 12 logical processors

System RAM:
16 GB

GPU:
NVIDIA Quadro T1000

GPU VRAM:
4 GB

Inference Runtime:
llama.cpp

Backend:
Vulkan

Primary Model Candidate:
Qwen3-8B Q4_K_M

Model Parameters:
approximately 8.19B

Quantized Model Size:
approximately 4.68 GiB
```

These values represent the current development environment and MUST NOT be interpreted as the minimum production hardware requirement.

The production target is conceptually an organization's own GPU server or workstation with substantially greater resources.

The architecture MUST therefore separate:

```text
Application Architecture
        from
Hardware / Model Profile
```

The application MUST NOT be redesigned merely because the underlying model, GPU, or inference runtime changes.

---

# 8. Validated Local Inference Results

The current Qwen3-8B Q4_K_M candidate has been empirically tested using llama.cpp/Vulkan on the NVIDIA Quadro T1000.

### 4K Context Profile

```text
Model:
Qwen3-8B Q4_K_M

GPU layers:
20

Context:
4096 tokens

Prompt processing:
119.64 tok/s

Generation:
5.39 tok/s

Result:
PASS
```

### 8K Context Profile

```text
Model:
Qwen3-8B Q4_K_M

GPU layers:
20

Context:
8192 tokens

Prompt processing:
104.33 tok/s

Generation:
4.39 tok/s

Result:
PASS
```

### 16K Context — 20 GPU Layers

```text
Context:
16384 tokens

GPU layers:
20

Result:
FAIL

Reason:
GPU out-of-memory during context creation.
```

### 16K Context — 10 GPU Layers

```text
Model:
Qwen3-8B Q4_K_M

GPU layers:
10

Context:
16384 tokens

Prompt processing:
81.19 tok/s

Generation:
3.77 tok/s

Result:
PASS
```

### Current Laptop Inference Profiles

The current validated profiles are:

```text
FAST PROFILE
------------
Qwen3-8B Q4_K_M
20 GPU layers
8K context
~4.39 tok/s generation


LONG-CONTEXT PROFILE
--------------------
Qwen3-8B Q4_K_M
10 GPU layers
16K context
~3.77 tok/s generation
```

These profiles are initial empirical configurations.

They MUST be represented as configurable model/inference profiles rather than hard-coded assumptions throughout the application.

---

# 9. Context Management Principle

A major architectural requirement is that the system MUST NOT depend on placing an entire document, organization, or historical conversation into a single model context.

The model's context window is a bounded working memory.

Persistent information MUST remain outside the model.

The system therefore distinguishes between:

```text
Model Context
    ↓
Temporary bounded working set


Persistent Task State
    ↓
Long-lived state of an executing task


Persistent Memory
    ↓
Controlled reusable information from previous interactions/tasks


Knowledge Base
    ↓
Authoritative organizational documents and evidence
```

These concepts MUST NOT be conflated.

---

# 10. Large-Document Principle

A large document MUST NOT be treated as a giant prompt.

For example, a 100-page inspection report should conceptually follow:

```text
100-page document
        ↓
Local ingestion
        ↓
Parsing / OCR
        ↓
Document structure
        ↓
Chunking / indexing
        ↓
Local retrieval
        ↓
Relevant evidence
        ↓
Context Manager
        ↓
Bounded model context
        ↓
Reasoning
```

The system MUST be capable of accessing large amounts of information without requiring the entire information set to fit inside one model invocation.

The exact retrieval, chunking, ranking, compression, and context-budgeting mechanisms are defined by later subsystem specifications.

---

# 11. Persistent State Principle

The LLM itself MUST NOT be treated as the authoritative storage mechanism for agent state.

The Agent Host MUST maintain persistent task state outside the model.

Task state may include:

* Current task
* Plan
* Completed steps
* Pending steps
* Extracted findings
* Evidence references
* Tool results
* Calculations
* Verification results
* Unresolved questions
* Generated artifacts
* Decisions
* Errors
* Recovery information

A future model invocation MUST receive only the relevant subset of this state.

The system MUST NOT continuously append the entire prior conversation to every model invocation.

---

# 12. Knowledge Principle

Organizational knowledge and agent memory are different concepts.

The Knowledge layer is responsible for organizational information such as:

* SOPs
* Manuals
* Inspection reports
* Policies
* Engineering documents
* Correspondence
* Historical records
* Scanned documents
* Drawings
* Other authorized organizational knowledge

Knowledge MUST retain source identity and provenance.

The Knowledge layer is the authoritative source for organizational facts where applicable.

Persistent agent memory MUST NOT silently override authoritative organizational evidence.

---

# 13. Evidence-First Principle

The system should prefer:

```text
Evidence
    ↓
Reasoning
    ↓
Conclusion
```

over:

```text
Model memory
    ↓
Guess
```

When evidence is unavailable, insufficient, contradictory, or outside the authorized knowledge boundary, the system SHOULD be capable of:

* Identifying the limitation
* Requesting additional evidence
* Marking uncertainty
* Escalating for human review
* Avoiding unsupported claims

The system MUST NOT claim that an answer is verified merely because an LLM generated it.

---

# 14. Verification Principle

Verification is a separate responsibility from generation.

Where deterministic verification is possible, deterministic tools SHOULD be preferred over asking another language-model call to "check" the result.

Examples:

```text
Engineering calculation
        ↓
Calculation engine / Python
        ↓
Deterministic result
        ↓
LLM explanation
```

and:

```text
Generated code
        ↓
Sandbox
        ↓
Execution
        ↓
Tests
        ↓
Observed result
```

Verification mechanisms MUST be designed independently from the model's own assertions.

---

# 15. Agentic Principle

The system qualifies as agentic only when it can execute a task through multiple controlled steps.

A representative execution pattern is:

```text
Goal
 ↓
Plan
 ↓
Retrieve
 ↓
Reason
 ↓
Tool
 ↓
Observe
 ↓
Update State
 ↓
Retrieve Again
 ↓
Reason
 ↓
Verify
 ↓
Deliver
```

The system MUST support iterative execution rather than treating every user request as a single isolated LLM response.

The Agent Host, not the LLM, owns execution control.

---

# 16. Model-Agnostic Principle

The application MUST NOT be architecturally coupled to Qwen3-8B.

Qwen3-8B Q4_K_M is the current laptop development candidate.

The architecture MUST support replacing or adding models through a model abstraction layer.

Potential future model roles include:

```text
Reasoning
Coding
Vision
OCR
Embedding
Reranking
Specialized domain models
```

The system MUST permit new local models to be introduced without redesigning the Agent Host.

---

# 17. Model Gateway Principle

The Agent Host MUST communicate with models through a Model Gateway or equivalent abstraction.

The conceptual boundary is:

```text
Agent Host
    ↓
Model Gateway
    ↓
Inference Adapter
    ↓
Inference Runtime
    ↓
Local Model
```

The Agent Host MUST NOT directly depend on llama.cpp-specific commands, flags, model file paths, or backend details.

This permits future replacement with:

* Another llama.cpp deployment
* Ollama
* vLLM
* Other local inference engines
* Enterprise GPU inference infrastructure

without changing the higher-level agent architecture.

---

# 18. Hardware-Aware Inference Principle

Model selection and inference configuration MUST consider available resources.

The system may need to select:

```text
Model
+
Quantization
+
GPU offload
+
Context budget
+
CPU threads
+
KV-cache configuration
+
Inference profile
```

rather than selecting only a model name.

For example, the current laptop has demonstrated that:

```text
20 GPU layers + 8K
```

and:

```text
10 GPU layers + 16K
```

are viable configurations for the current model candidate.

Therefore the architecture MUST allow multiple inference profiles for the same model.

---

# 19. MCP Principle

MCP is used as a standardized capability/context boundary.

The prototype architecture conceptually contains:

```text
Agent Host
    │
    ├── Knowledge MCP
    │
    ├── Tools MCP
    │
    └── DataHub MCP
```

MCP is not itself the Agent Host.

The Agent Host remains responsible for:

* Planning
* Orchestration
* State
* Context construction
* Model routing
* Tool policy
* Verification
* Execution control

MCP provides controlled interfaces to external capabilities within the local environment.

---

# 20. DataHub Scope

The existing local DataHub MCP is available in the development environment.

However, DataHub is NOT a mandatory dependency for the first local inference and core-agent implementation stages.

For the constrained laptop prototype:

```text
Knowledge MCP
    ↓
Primary organizational knowledge path

DataHub MCP
    ↓
Optional / later integration
```

The architecture MUST preserve a clean integration boundary so DataHub can be enabled later without redesigning the Agent Host.

The prototype should eventually demonstrate DataHub integration if hardware/resource constraints permit.

---

# 21. Tools Principle

The LLM MUST NOT receive unrestricted host-machine execution privileges.

The intended execution boundary is:

```text
Agent
 ↓
Tool Manager
 ↓
Policy / Permission Check
 ↓
Sandbox
 ↓
Tool
 ↓
Result
 ↓
Agent
```

Potential tools include:

* File read
* File write
* Python execution
* Calculations
* Spreadsheet operations
* DOCX generation
* PPTX generation
* XLSX generation
* Other explicitly authorized local tools

Tool capabilities MUST be explicitly registered and controlled.

---

# 22. Sandbox Principle

Generated code MUST NOT be executed directly on the host operating system by default.

The prototype MUST provide an isolated execution mechanism appropriate to the available environment.

The sandbox should restrict, as technically practical:

* Host filesystem access
* Network access
* Process privileges
* Resource consumption
* Execution duration
* Unauthorized system calls

The exact sandbox implementation is defined by the sandbox subsystem specification.

---

# 23. Multimodal Principle

The system MUST support multimodal enterprise information as part of the prototype direction.

Relevant inputs include:

* Scanned PDFs
* Images
* Photographs
* Handwritten notes
* Engineering drawings
* Inspection images

The architecture MUST therefore separate:

```text
Document/Image
      ↓
OCR / Vision Processing
      ↓
Extracted Evidence
      ↓
Knowledge / Task State
      ↓
Reasoning Model
```

The primary Qwen3-8B GGUF currently tested is text-only.

Therefore multimodal processing MUST be architecturally separable from the primary reasoning model.

A specialized local OCR/vision model may be used.

---

# 24. Artifact Principle

The system MUST produce actual work products rather than only textual chat responses.

Potential outputs include:

* DOCX approval notes
* XLSX spreadsheets
* PPTX presentations
* PDF reports
* Calculations
* Source code
* Structured datasets

Artifacts MUST be associated with:

* Task identity
* Source evidence
* Generation metadata
* Verification status where applicable
* Provenance
* Audit information

---

# 25. Auditability Principle

Important system activity MUST be auditable.

The system should record events such as:

```text
User request
    ↓
Plan
    ↓
Retrieval
    ↓
Evidence used
    ↓
Model invocation
    ↓
Tool invocation
    ↓
Tool result
    ↓
Verification
    ↓
Artifact generation
```

Audit logs MUST NOT require external telemetry services.

The exact audit schema is defined by a later subsystem specification.

---

# 26. Security Boundary

The prototype security model is:

```text
┌──────────────────────────────────────────────┐
│              LOCAL TRUST BOUNDARY            │
│                                              │
│ User                                         │
│   ↓                                          │
│ Sovereign UI                                 │
│   ↓                                          │
│ API / Agent Host                             │
│   ↓                                          │
│ Context / Memory / Knowledge                 │
│   ↓                                          │
│ Local Models                                 │
│   ↓                                          │
│ Governed Tools / Sandbox                     │
│   ↓                                          │
│ Generated Artifacts                          │
│                                              │
│ External network NOT required                │
└──────────────────────────────────────────────┘
```

The final prototype MUST demonstrate that the AI workflow does not depend on external network calls.

---

# 27. Human Oversight

The system is an assistant/worker, not an autonomous authority.

For sensitive industrial workflows, the prototype SHOULD support human review before final operational decisions.

The system MUST distinguish between:

```text
AI-generated recommendation
```

and:

```text
Human-approved operational decision
```

The system MUST NOT claim that generated approval notes constitute actual organizational approval.

---

# 28. Prototype Flagship Workflow

The primary end-to-end demonstration will be based on:

> **Review a scanned inspection report and prepare an approval note.**

Conceptual flow:

```text
User uploads scanned inspection report
            ↓
Local OCR / Vision
            ↓
Document understanding
            ↓
Agent Planner
            ↓
Retrieve relevant SOP / manual
            ↓
Retrieve authorized organizational evidence
            ↓
Construct bounded context
            ↓
Local reasoning model
            ↓
Identify findings
            ↓
Perform required calculations
            ↓
Deterministic verification
            ↓
Resolve / flag uncertainties
            ↓
Generate approval-note.docx
            ↓
Attach source references
            ↓
Record provenance
            ↓
Audit execution
```

This workflow is the primary integration target.

---

# 29. Secondary Demonstrations

The prototype should also demonstrate:

## Coding Workflow

```text
User coding request
      ↓
Local reasoning model
      ↓
Generate code
      ↓
Sandbox execution
      ↓
Tests
      ↓
Observed results
      ↓
Fix / iterate
      ↓
Final code
```

## Multimodal Workflow

```text
Scanned image / document
      ↓
Local OCR / Vision
      ↓
Extract structured evidence
      ↓
Reasoning
      ↓
Result
```

## Knowledge Workflow

```text
Question
   ↓
Knowledge MCP
   ↓
Relevant organizational sources
   ↓
Evidence-grounded answer
   ↓
Source references
```

---

# 30. Non-Goals for the Laptop Prototype

The following are explicitly OUT OF SCOPE unless later approved:

1. Training a foundation model from scratch.
2. Fine-tuning large models.
3. Running 120B-class models on the laptop.
4. Deploying a large distributed inference cluster.
5. Kubernetes-based production orchestration.
6. Full enterprise SSO implementation.
7. Full production-grade multi-tenancy.
8. SAP integration.
9. PLM integration.
10. SCADA integration.
11. Full enterprise EDMS integration.
12. Production financial systems integration.
13. Production operational control systems.
14. Automatic real-world approval authority.
15. Unrestricted host command execution.
16. Dependence on cloud AI APIs.
17. Building a generic replacement for every enterprise system.
18. Supporting every open-weight model from day one.
19. Maximizing benchmark performance at the expense of reliability.
20. Treating the prototype laptop configuration as the production deployment specification.

These may be future expansion areas.

---

# 31. Production Expansion Direction

The prototype architecture MUST be designed so that it can conceptually scale from:

```text
Development Laptop
16 GB RAM
4 GB VRAM
```

to:

```text
Enterprise On-Prem GPU Server
Higher RAM
Higher VRAM
Multiple / larger models
```

without redesigning the fundamental application architecture.

Future deployments may support:

* Larger reasoning models
* Dedicated coding models
* Dedicated vision models
* Larger context windows
* Higher concurrency
* Multiple GPU workers
* Enterprise identity systems
* DataHub
* EDMS
* SAP
* PLM
* Internal databases
* Internal applications
* Additional MCP servers

These are architectural extension points, not current laptop prototype requirements.

---

# 32. Critical Architectural Rule

The system MUST separate:

```text
Application Logic
Model Capability
Inference Runtime
Hardware Profile
```

For example:

```text
Agent Host
    ↓
Model Gateway
    ↓
Inference Adapter
    ↓
llama.cpp
    ↓
Qwen3-8B Q4_K_M
    ↓
T1000
```

may later become:

```text
Agent Host
    ↓
Model Gateway
    ↓
Inference Adapter
    ↓
vLLM
    ↓
Larger Open-Weight Model
    ↓
Enterprise GPU Server
```

The Agent Host SHOULD NOT need to change merely because the underlying model or inference infrastructure changes.

---

# 33. Engineering Quality Requirements

The prototype is expected to be engineered as a real software system rather than a collection of demonstration scripts.

The implementation SHOULD include:

* Clear package boundaries
* Typed interfaces
* Configuration management
* Structured logging
* Automated tests
* Integration tests
* Error handling
* Validation
* Security controls
* Deterministic behavior where possible
* Reproducible setup
* Documentation
* Health checks
* Explicit failure states

A feature is not considered complete merely because a happy-path demo works.

---

# 34. Failure Philosophy

The system MUST prefer explicit failure over silent fabrication.

Examples:

```text
Evidence unavailable
        ↓
Do not invent evidence
        ↓
Report insufficient evidence
```

```text
Calculation failed
        ↓
Do not present unverified result
        ↓
Report calculation failure
```

```text
Tool execution failed
        ↓
Record failure
        ↓
Retry if policy permits
        ↓
Otherwise escalate
```

```text
Conflicting authoritative documents
        ↓
Do not silently choose one
        ↓
Apply defined authority/revision policy
        ↓
If unresolved, flag conflict
```

---

# 35. Definition of "Sovereign"

For this project, "sovereign" means that the organization retains control over:

* Where models execute
* Where data is stored
* Where inference occurs
* Which tools can execute
* Which documents can be accessed
* Which users can access capabilities
* Which models can process information
* What network communication is permitted
* What artifacts are generated
* What execution history is recorded

Sovereignty therefore encompasses:

```text
Data
+
Models
+
Inference
+
Tools
+
Knowledge
+
Execution
+
Network
+
Audit
```

---

# 36. Core USP

The project should not be positioned as:

> "A chatbot that runs locally."

The primary proposition is:

> **A sovereign AI worker that understands private enterprise evidence, chooses appropriate local AI capabilities, acts through governed local tools, verifies its work, and produces auditable deliverables without sending confidential work to external AI services.**

A concise positioning statement is:

> **Don't send the work to AI. Bring AI to the work.**

---

# 37. Governing Design Principles

All subsequent engineering work MUST preserve the following principles:

1. **Sovereign by design**
2. **Local-first execution**
3. **Model-agnostic architecture**
4. **Bounded model context**
5. **Persistent state outside the model**
6. **Evidence-first reasoning**
7. **Governed tool execution**
8. **Sandboxed code execution**
9. **Independent verification**
10. **Source provenance**
11. **Auditable execution**
12. **Hardware-aware inference**
13. **MCP-based extensibility**
14. **Human oversight for sensitive decisions**
15. **Explicit failure instead of fabrication**
16. **Production-oriented engineering discipline**

---

# 38. Architectural Decision Authority

This document establishes the baseline project definition.

Subsequent specifications may refine implementation details, but they MUST NOT silently alter:

* Sovereignty requirements
* Model-agnostic architecture
* Persistent state principle
* Context-management principle
* Evidence-first principle
* Tool governance
* Sandbox requirement
* Verification requirement
* Auditability requirement
* Core flagship workflow
* Prototype non-goals

If a later subsystem discovers that a requirement is technically infeasible, it MUST document:

1. The conflict
2. The reason
3. The affected components
4. Proposed alternatives
5. Impact on the SIH demonstration
6. Required architectural change

The architecture should then be explicitly reviewed before implementation continues.

---

# 39. Definition of Prototype Completion

The prototype is considered complete only when the following end-to-end capability can be demonstrated locally:

```text
Confidential input
        ↓
Local multimodal/document understanding
        ↓
Agent planning
        ↓
Local organizational knowledge retrieval
        ↓
Bounded context construction
        ↓
Appropriate local model selection
        ↓
Multi-step reasoning
        ↓
Governed tool use
        ↓
Sandboxed computation/code execution
        ↓
Independent verification
        ↓
Real business artifact generation
        ↓
Evidence + provenance
        ↓
Audit trail
        ↓
Demonstrable absence of required external AI/network calls
```

The system must work as an integrated workflow, not merely as isolated subsystem demonstrations.

---

# 40. Status

This document is the **baseline project charter**.

Any implementation work MUST treat this document as the source of truth for:

* Project purpose
* Prototype scope
* Core architecture principles
* Hardware assumptions
* Model assumptions
* Security philosophy
* Agentic behavior
* Context strategy
* Persistent state strategy
* Non-goals
* Definition of completion

**Status: FROZEN**

```

**File 01 is complete.**

I am intentionally stopping here. When you say **“next”**, we'll create **File 02**, continuing from this exact baseline without reworking or mixing the scope.
```
