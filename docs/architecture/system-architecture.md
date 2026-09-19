# `02-system-architecture.md`

````markdown
# Sovereign AI Workbench
## System Architecture Specification

**Project:** Sovereign AI — SIH 2026 Prototype  
**Document:** System Architecture  
**Document ID:** SAI-DOC-002  
**Status:** FROZEN — BASELINE ARCHITECTURE  
**Version:** 1.0  
**Depends On:** `01-project-charter.md`

---

# 1. Purpose

This document defines the authoritative high-level architecture of the Sovereign AI Workbench.

It establishes:

- Major system components
- Component responsibilities
- Component boundaries
- Communication paths
- Data flow
- Control flow
- Dependency relationships
- Extensibility boundaries
- Runtime boundaries
- Prototype architecture

This document intentionally does NOT define every implementation detail.

Detailed implementation contracts are defined in Documents 05–11.

No subsystem may silently introduce an architectural responsibility that conflicts with this document.

---

# 2. Architectural Objective

The architecture must support the following fundamental capability:

> A user provides a goal involving confidential organizational information, and the system can locally understand the goal, retrieve authorized evidence, select an appropriate local AI capability, execute governed tools, maintain persistent task state, verify results, generate a real deliverable, and record provenance and audit information without requiring external AI services.

The architecture must remain:

- Sovereign
- Model-agnostic
- Agentic
- Extensible
- Resource-aware
- Auditable
- Security-conscious
- Suitable for constrained prototype hardware

---

# 3. Architectural Style

The system follows a modular, service-oriented architecture with explicit capability boundaries.

The architecture is:

```text
User Interface
      │
      ▼
API / Application Boundary
      │
      ▼
Agent Host
      │
      ├──────────────► Model Gateway
      │
      ├──────────────► Context / Memory Layer
      │
      ├──────────────► Knowledge MCP
      │
      ├──────────────► Tools MCP
      │
      ├──────────────► Artifact Engine
      │
      ├──────────────► Verification
      │
      └──────────────► Audit / Provenance
````

The system is NOT architected as:

```text
UI
 ↓
LLM
 ↓
Answer
```

The LLM is one component of the system, not the system itself.

---

# 4. High-Level Architecture

The canonical architecture is:

```text
┌─────────────────────────────────────────────────────────────┐
│                     SOVEREIGN AI WORKBENCH                  │
│                                                             │
│  ┌───────────────────────┐                                  │
│  │    Sovereign UI       │                                  │
│  │                       │                                  │
│  │ Chat / Tasks           │                                  │
│  │ Files / Artifacts      │                                  │
│  │ Execution Status       │                                  │
│  │ Audit / Sources        │                                  │
│  └───────────┬───────────┘                                  │
│              │                                              │
│              ▼                                              │
│  ┌───────────────────────┐                                  │
│  │ API / Application      │                                  │
│  │ Boundary               │                                  │
│  │                       │                                  │
│  │ Authentication         │                                  │
│  │ Authorization           │                                  │
│  │ Request Validation      │                                  │
│  └───────────┬───────────┘                                  │
│              │                                              │
│              ▼                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    AGENT HOST                         │  │
│  │                                                       │  │
│  │ Planner                                               │  │
│  │ Orchestrator                                          │  │
│  │ Task State Manager                                    │  │
│  │ Context Manager                                      │  │
│  │ Model Selection                                       │  │
│  │ Tool Policy                                           │  │
│  │ Verification Control                                  │  │
│  │ Recovery / Retry                                      │  │
│  └───────┬──────────────┬──────────────┬─────────────────┘  │
│          │              │              │                    │
│          ▼              ▼              ▼                    │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐  │
│  │ Model        │ │ Knowledge    │ │ Tools              │  │
│  │ Gateway      │ │ MCP          │ │ MCP                │  │
│  └──────┬───────┘ └──────┬───────┘ └─────────┬──────────┘  │
│         │                │                   │             │
│         ▼                ▼                   ▼             │
│  Local Inference   Local Knowledge      Sandboxed Tools   │
│  Runtime           / Documents                              │
│         │                │                   │             │
│         ▼                ▼                   ▼             │
│  Open-Weight        OCR / Parser /       Python           │
│  Models             Retriever             Files            │
│                                            Excel           │
│                                            Calculations    │
│                                                             │
│  ┌────────────────┐ ┌────────────────┐ ┌─────────────────┐ │
│  │ Artifact       │ │ Verification   │ │ Audit &         │ │
│  │ Engine         │ │ Engine         │ │ Provenance      │ │
│  └────────────────┘ └────────────────┘ └─────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

All components shown inside the Sovereign AI boundary are intended to operate locally.

---

# 5. Major Components

The system consists of the following architectural components.

## 5.1 Sovereign UI

Responsible for:

* User interaction
* Task creation
* File upload
* Task status
* Tool activity visibility
* Artifact access
* Evidence/source display
* Audit visibility

The UI MUST NOT contain agent orchestration logic.

---

## 5.2 API / Application Boundary

Responsible for:

* Receiving requests from the UI
* Authentication
* Authorization
* Request validation
* Task creation
* File handling
* Returning task state/results

The API layer MUST NOT directly execute arbitrary model-generated commands.

---

## 5.3 Agent Host

The Agent Host is the central orchestration component.

It is responsible for:

* Understanding the task
* Creating execution plans
* Managing execution state
* Requesting relevant context
* Selecting model capabilities
* Calling MCP servers
* Applying tool policies
* Handling tool results
* Iterating
* Triggering verification
* Requesting artifact generation
* Handling failures
* Completing or escalating tasks

The Agent Host owns the **control loop**.

The Agent Host is NOT itself the language model.

---

## 5.4 Model Gateway

The Model Gateway provides a stable interface between the Agent Host and local AI models.

Responsibilities include:

* Model discovery
* Model registration
* Model capability metadata
* Model selection
* Inference profile selection
* Request construction
* Runtime abstraction
* Model health
* Resource-aware routing

Conceptually:

```text
Agent Host
    │
    ▼
Model Gateway
    │
    ▼
Model Adapter
    │
    ▼
Inference Runtime
    │
    ▼
Local Model
```

The Agent Host MUST NOT depend directly on llama.cpp-specific APIs or command-line details.

---

## 5.5 Context / Memory Layer

This architectural area manages information supplied to model invocations.

It consists conceptually of:

```text
┌──────────────────────────────┐
│ Context / Memory Layer       │
│                              │
│ Context Manager              │
│ Persistent Task State        │
│ Persistent Memory            │
│ Context Budgeting            │
│ Evidence Selection           │
│ Conversation State           │
└──────────────────────────────┘
```

Its purpose is to prevent the LLM context from becoming the storage mechanism for the entire task.

The system MUST construct each model invocation from a bounded working set.

---

## 5.6 Knowledge MCP

Knowledge MCP provides controlled access to organizational knowledge.

Examples:

* SOPs
* Manuals
* Inspection reports
* Policies
* Engineering documents
* Correspondence
* Historical records
* Scanned documents
* Drawings

The Knowledge MCP is responsible for exposing knowledge capabilities to the Agent Host.

The Agent Host decides when knowledge is needed.

The model MUST NOT directly access the underlying document store.

---

## 5.7 Tools MCP

Tools MCP exposes controlled local capabilities.

Potential capabilities include:

```text
read_file
write_file
execute_python
calculate
read_excel
write_excel
create_docx
create_pptx
create_xlsx
```

Tools are capabilities, not arbitrary shell access.

Every tool invocation MUST pass through the defined authorization/policy mechanism.

---

## 5.8 Sandbox

The sandbox provides isolation for operations that may execute generated code.

Conceptually:

```text
Agent
  ↓
Tool Manager
  ↓
Policy
  ↓
Sandbox
  ↓
Execution
  ↓
Result
```

The sandbox MUST be treated as a security boundary.

Generated code MUST NOT receive unrestricted host access.

---

## 5.9 Artifact Engine

The Artifact Engine creates actual business deliverables.

Potential formats:

* DOCX
* XLSX
* PPTX
* PDF
* Source code
* Structured data

The Artifact Engine MUST receive structured inputs rather than relying on uncontrolled model-generated filesystem commands.

Artifacts MUST have provenance metadata where applicable.

---

## 5.10 Verification Engine

The Verification Engine checks results independently where possible.

Examples:

```text
Generated calculation
        ↓
Deterministic calculation
        ↓
Comparison
        ↓
Verification status
```

and:

```text
Generated code
        ↓
Sandbox
        ↓
Tests
        ↓
Observed result
```

Verification MUST NOT be reduced to:

> "Ask the same LLM whether its answer is correct."

LLM-based critique may supplement verification, but it MUST NOT automatically be considered authoritative verification for deterministic tasks.

---

## 5.11 Audit and Provenance Layer

Records execution history and evidence relationships.

The system should be able to associate:

```text
Task
 ↓
Plan
 ↓
Evidence
 ↓
Model invocation
 ↓
Tool invocation
 ↓
Tool result
 ↓
Verification
 ↓
Artifact
```

This layer is essential to the sovereign enterprise proposition.

---

# 6. Agent Host Internal Architecture

The Agent Host should be internally modular.

Canonical structure:

```text
┌────────────────────────────────────────────┐
│                  AGENT HOST                │
│                                            │
│  ┌────────────┐       ┌─────────────────┐ │
│  │ Planner    │──────► │ Orchestrator   │ │
│  └────────────┘       └────────┬────────┘ │
│                                │          │
│         ┌──────────────────────┼───────┐  │
│         ▼                      ▼       ▼  │
│  Context Manager          Tool Policy  │  │
│         │                              │  │
│         ▼                              ▼  │
│  Model Gateway                    Tools MCP│
│         │                              │  │
│         ▼                              │  │
│  Local Models                       │  │
│                                        │  │
│  ┌────────────────────────────────────┐ │  │
│  │ Task State / Memory                │ │  │
│  └────────────────────────────────────┘ │  │
│                                        │  │
│  ┌────────────────────────────────────┐ │  │
│  │ Verification Controller            │ │  │
│  └────────────────────────────────────┘ │  │
└────────────────────────────────────────────┘
```

The exact class/module decomposition is defined during implementation.

---

# 7. Agent Execution Loop

The canonical execution loop is:

```text
1. Receive goal
       ↓
2. Create task
       ↓
3. Establish initial state
       ↓
4. Plan
       ↓
5. Determine required evidence/tools
       ↓
6. Retrieve context
       ↓
7. Construct bounded model request
       ↓
8. Invoke local model
       ↓
9. Interpret model decision
       ↓
10. Execute approved tool if required
       ↓
11. Record observation
       ↓
12. Update persistent task state
       ↓
13. Determine next step
       ↓
14. Verify where required
       ↓
15. Repeat until completion
       ↓
16. Generate artifact
       ↓
17. Record provenance/audit
       ↓
18. Return result
```

The Agent Host MUST own this loop.

The model provides reasoning/decision assistance but does not directly control the host system.

---

# 8. Control Plane vs Data Plane

The architecture should distinguish between control and data.

## Control Plane

Contains:

* Agent orchestration
* Task state
* Policies
* Model routing
* Tool authorization
* Verification decisions
* Audit events

## Data Plane

Contains:

* Documents
* Images
* Retrieved evidence
* Model inputs/outputs
* Tool inputs/outputs
* Generated artifacts

This separation is important for security and maintainability.

---

# 9. Model Interaction Boundary

All model requests MUST pass through the Model Gateway.

Conceptually:

```text
Agent Host
    │
    │ structured inference request
    ▼
Model Gateway
    │
    │ select model/profile
    ▼
Inference Adapter
    │
    ▼
Local Runtime
    │
    ▼
Model
    │
    ▼
Structured inference result
    │
    ▼
Model Gateway
    │
    ▼
Agent Host
```

The model output MUST NOT directly invoke host operations.

---

# 10. Model Routing Architecture

The system must support multiple model roles.

Example:

```text
                    Model Gateway
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Reasoning        Coding         Vision
       Model            Model          Model
          │              │              │
          ▼              ▼              ▼
      Local LLM       Local LLM      Local Model
```

The current laptop may use the same model for multiple roles when necessary.

The architecture MUST NOT assume that every role requires a separate model process.

---

# 11. Resource-Aware Model Profiles

Model selection MUST be separable from inference configuration.

Example:

```text
Qwen3-8B Q4_K_M
        │
        ├── FAST
        │    ├── 20 GPU layers
        │    └── 8K context
        │
        └── LONG
             ├── 10 GPU layers
             └── 16K context
```

The Model Gateway SHOULD select an appropriate profile based on:

* Task requirements
* Context requirement
* Available memory
* GPU availability
* Model capability
* Latency requirements

The architecture must permit future profiles to be added.

---

# 12. Context Construction Architecture

A model request should conceptually be constructed as:

```text
Task Goal
   +
Relevant Task State
   +
Relevant Memory
   +
Retrieved Evidence
   +
Tool Results
   +
Current Plan Step
   +
System / Policy Instructions
   ↓
Context Manager
   ↓
Token Budget
   ↓
Model Request
```

The entire conversation history MUST NOT automatically be inserted into every request.

The Context Manager is responsible for selecting the relevant working set.

---

# 13. Knowledge Retrieval Boundary

The Knowledge layer should follow:

```text
User / Task
     ↓
Agent Host
     ↓
Knowledge MCP
     ↓
Retriever
     ↓
Local Index / Store
     ↓
Evidence
     ↓
Agent Host
     ↓
Context Manager
     ↓
Model
```

The model itself MUST NOT directly query the vector database, filesystem, or document repository.

The Agent Host controls when and why retrieval occurs.

---

# 14. Persistent State Boundary

Persistent task state belongs outside the model.

Conceptually:

```text
                 Task State Store
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     Plan          Findings       Tool Results
        │              │              │
        ▼              ▼              ▼
   Questions       Evidence       Verification
                       │
                       ▼
                 Context Manager
```

The state store is not the model context.

The state store contains potentially large information, while the Context Manager selects only what is needed for a particular invocation.

---

# 15. Tool Execution Boundary

The architecture MUST enforce:

```text
LLM
 │
 │ tool intent
 ▼
Agent Host
 │
 │ policy evaluation
 ▼
Tool Manager
 │
 │ authorized call
 ▼
MCP Tool
 │
 ▼
Sandbox / Controlled Runtime
 │
 ▼
Result
 │
 ▼
Agent Host
```

The model MUST NOT directly:

* Execute shell commands
* Write arbitrary host files
* Access arbitrary directories
* Open unrestricted network connections
* Install arbitrary software
* Control host processes

unless an explicitly authorized capability has been implemented through a controlled tool boundary.

---

# 16. Artifact Flow

Artifacts should follow:

```text
Agent
  ↓
Structured Artifact Request
  ↓
Artifact Engine
  ↓
Template / Generator
  ↓
Artifact
  ↓
Verification / Validation
  ↓
Provenance
  ↓
Artifact Store
```

The model should not be responsible for manually constructing binary file formats.

For example, a DOCX should be created by a deterministic document-generation component rather than by asking the LLM to manipulate ZIP/XML internals directly.

---

# 17. Verification Flow

Verification should occur as a separate phase:

```text
Candidate Result
      ↓
Determine Verification Method
      ↓
┌─────┴───────────────────┐
│                         │
▼                         ▼
Deterministic             Controlled
Verification              Execution
│                         │
▼                         ▼
Result                    Result
└──────────┬──────────────┘
           ▼
     Verification Status
           │
     ┌─────┴─────┐
     ▼           ▼
   PASS        FAIL/UNCERTAIN
     │           │
     ▼           ▼
 Continue      Retry / Escalate
```

Verification status MUST be represented explicitly.

---

# 18. Error and Recovery Architecture

Failures are expected.

The Agent Host must distinguish at least:

```text
Model Failure
Tool Failure
Retrieval Failure
Validation Failure
Verification Failure
Resource Failure
Permission Failure
Timeout
Malformed Output
Insufficient Evidence
```

The system SHOULD support controlled recovery such as:

```text
Failure
  ↓
Classify
  ↓
Retry if safe
  ↓
Alternative strategy if available
  ↓
Escalate if unresolved
```

The system MUST NOT silently continue after a critical failure.

---

# 19. Resource Constraint Architecture

The prototype must operate within constrained hardware.

The architecture must therefore avoid assuming:

* Unlimited VRAM
* Unlimited RAM
* Unlimited context
* Unlimited concurrency
* Unlimited model instances
* Unlimited inference speed

The system SHOULD prefer:

```text
Bounded concurrency
+
Bounded context
+
Resource-aware model profiles
+
Persistent state
+
Retrieval
+
Task decomposition
```

over brute-force model scaling.

---

# 20. Concurrency Model

Multiple agents do not necessarily require multiple copies of a model.

Conceptually:

```text
Agent A ─┐
Agent B ─┼──► Model Gateway ─► Local Model
Agent C ─┘
```

The Model Gateway may serialize, schedule, or batch inference depending on runtime capabilities.

Multiple model instances SHOULD only be introduced when hardware resources justify them.

The prototype does not require concurrent multi-model inference.

---

# 21. MCP Architecture

MCP provides standardized capability boundaries.

Current conceptual topology:

```text
                    Agent Host
                       │
          ┌────────────┼─────────────┐
          ▼            ▼             ▼
     Knowledge MCP  Tools MCP   DataHub MCP
          │            │             │
          ▼            ▼             ▼
      Documents      Tools        Data Context
```

MCP servers MUST remain local for the sovereign prototype unless an explicitly approved future architecture states otherwise.

The Agent Host remains responsible for orchestration across MCP capabilities.

---

# 22. DataHub Integration Boundary

DataHub is an optional integration in the constrained laptop prototype.

The architecture reserves:

```text
Agent Host
     ↓
DataHub MCP
     ↓
Structured enterprise metadata
```

Possible future capabilities include:

* Dataset metadata
* Schema information
* Ownership
* Lineage
* Glossary
* Data quality
* Business context

The absence of DataHub from a particular prototype workflow MUST NOT break the core Agent Host.

---

# 23. Multimodal Architecture

Multimodal processing is separated from reasoning.

Conceptually:

```text
Scanned PDF / Image
        ↓
Local OCR / Vision
        ↓
Structured / textual evidence
        ↓
Knowledge or Task State
        ↓
Context Manager
        ↓
Reasoning Model
```

This permits different models to specialize in:

* OCR
* Vision
* Reasoning
* Coding
* Embeddings
* Reranking

The current Qwen3-8B text-only model is therefore not a blocker to the overall multimodal architecture.

---

# 24. Security Architecture Boundary

The complete application should conceptually operate within:

```text
┌─────────────────────────────────────────────────┐
│              ORGANIZATION BOUNDARY              │
│                                                 │
│ UI                                              │
│ │                                               │
│ API                                             │
│ │                                               │
│ Agent Host                                      │
│ │                                               │
│ ├── Model Gateway ──► Local Models              │
│ │                                               │
│ ├── Knowledge MCP ──► Local Knowledge           │
│ │                                               │
│ ├── Tools MCP ──────► Sandbox                   │
│ │                                               │
│ ├── Artifact Engine                             │
│ │                                               │
│ ├── Verification                                │
│ │                                               │
│ └── Audit / Provenance                          │
│                                                 │
│ External AI services NOT required               │
└─────────────────────────────────────────────────┘
```

Detailed security controls are defined in `03-security-and-sovereignty.md`.

---

# 25. Network Architecture

The sovereign prototype MUST be capable of operating without external network connectivity during normal AI execution.

The preferred demonstration architecture is:

```text
User
 ↓
Local UI
 ↓
Local API
 ↓
Local Agent Host
 ↓
Local MCP
 ↓
Local Models
 ↓
Local Tools
 ↓
Local Storage
```

No component should implicitly depend on:

* External API keys
* Cloud inference
* Cloud OCR
* Cloud embeddings
* Cloud vector databases
* External telemetry
* Internet-based model calls

Any dependency that requires network access MUST be explicitly identified and excluded or replaced for offline operation.

---

# 26. Storage Architecture

The prototype will require local storage for:

```text
Models
Documents
Indexes
Task State
Memory
Artifacts
Audit Logs
Configuration
```

These stores MUST have explicit ownership.

No subsystem should assume that another subsystem's storage can be modified directly.

Access should occur through defined interfaces.

---

# 27. Configuration Architecture

Configuration MUST be separated from application code.

Configuration may include:

* Model paths
* Model profiles
* GPU layers
* Context limits
* Runtime settings
* Storage paths
* Tool permissions
* Sandbox limits
* Retrieval settings
* Audit settings
* Security settings

Secrets MUST NOT be hard-coded into source code.

---

# 28. Dependency Direction

The architecture should follow a controlled dependency direction.

Preferred:

```text
UI
 ↓
API
 ↓
Agent Host
 ↓
Interfaces / Gateways
 ↓
Infrastructure Adapters
 ↓
Local Runtime / Storage
```

Infrastructure-specific details SHOULD NOT leak upward into the Agent Host.

For example:

```text
Agent Host
```

should know:

```text
generate_response(...)
```

rather than:

```text
subprocess.run(["llama-cli", ...])
```

---

# 29. Extensibility Model

New capabilities should be added through explicit adapters/interfaces.

Examples:

```text
New model
    ↓
Model Adapter
    ↓
Model Gateway
```

```text
New enterprise system
    ↓
MCP Server / Connector
    ↓
Agent Host
```

```text
New tool
    ↓
Tool definition
    ↓
Policy registration
    ↓
Tools MCP
```

This prevents changes to the Agent Host for every new capability.

---

# 30. Prototype vs Production Architecture

The architecture intentionally supports two deployment scales.

## Prototype

```text
Single workstation
     ↓
Local services
     ↓
Qwen3-8B
     ↓
Hybrid CPU/GPU inference
```

## Production

```text
Enterprise infrastructure
     ↓
GPU server / cluster
     ↓
Multiple local models
     ↓
Higher concurrency
     ↓
Enterprise systems
```

The logical architecture remains substantially the same.

---

# 31. Primary End-to-End Workflow

The flagship workflow should map to the architecture as follows:

```text
USER
 │
 ▼
UI
 │
 ▼
API
 │
 ▼
AGENT HOST
 │
 ├──► Knowledge MCP
 │       │
 │       ▼
 │   SOP / Manual / Report Evidence
 │
 ├──► Context Manager
 │
 ├──► Model Gateway
 │       │
 │       ▼
 │   Local Reasoning Model
 │
 ├──► Tools MCP
 │       │
 │       ▼
 │   Calculation / Python
 │
 ├──► Verification
 │
 └──► Artifact Engine
         │
         ▼
      DOCX
         │
         ▼
  Provenance + Audit
```

This workflow is the principal architectural integration test.

---

# 32. Architectural Invariants

The following MUST remain true throughout implementation:

### Invariant 1 — Local execution

Confidential AI processing does not require an external AI service.

### Invariant 2 — Model abstraction

The Agent Host does not depend directly on a specific model runtime.

### Invariant 3 — Bounded context

The system does not rely on unlimited model context.

### Invariant 4 — External state

Task state and knowledge exist outside the model context.

### Invariant 5 — Controlled tools

Model-generated actions pass through controlled tool boundaries.

### Invariant 6 — Sandboxed execution

Generated code does not receive unrestricted host execution.

### Invariant 7 — Independent verification

Where deterministic verification is possible, it is performed independently of model generation.

### Invariant 8 — Provenance

Important generated outputs can be traced to their supporting evidence and execution history.

### Invariant 9 — Extensibility

Models and enterprise capabilities can be added through defined interfaces.

### Invariant 10 — Explicit failure

The system does not silently fabricate successful completion after critical failures.

---

# 33. What This Architecture Does NOT Prescribe

This document intentionally does NOT freeze:

* Specific programming language
* Specific web framework
* Specific database engine
* Specific vector database
* Specific OCR engine
* Specific vision model
* Specific embedding model
* Specific sandbox technology
* Specific MCP SDK implementation
* Specific UI framework
* Specific production deployment platform

Those decisions must be made in the relevant subsystem specifications based on:

* Prototype constraints
* Offline operation
* Maintainability
* Security
* Performance
* Licensing
* Integration complexity

A technology choice MUST NOT be introduced merely because it is popular if it conflicts with the sovereign/offline/resource constraints.

---

# 34. Architectural Change Policy

Any proposed architectural change must identify:

1. Current architecture
2. Proposed change
3. Reason for change
4. Components affected
5. Security implications
6. Performance implications
7. Prototype implications
8. Future production implications
9. Migration requirements

No implementation agent may silently modify an architectural invariant.

If an implementation discovers a contradiction, it MUST stop at the affected boundary and report the issue.

---

# 35. Implementation Rule

The implementation agent must treat this document and the project charter as architectural constraints.

The implementation agent MUST:

* Follow defined component boundaries.
* Preserve interfaces.
* Avoid unnecessary coupling.
* Avoid introducing cloud dependencies.
* Avoid bypassing the Agent Host.
* Avoid direct model-to-host execution.
* Avoid uncontrolled tool execution.
* Avoid treating model context as persistent storage.
* Avoid silently expanding scope.

The implementation agent SHOULD:

* Prefer simple implementations for the prototype.
* Preserve future extensibility where it costs little.
* Make resource limits explicit.
* Provide tests for each architectural boundary.
* Report architectural conflicts instead of inventing solutions silently.

---

# 36. Definition of Architectural Success

The architecture is considered successfully implemented when the system can demonstrate:

```text
User Goal
   ↓
Agent Host
   ↓
Private Evidence
   ↓
Bounded Context
   ↓
Local Model
   ↓
Controlled Tools
   ↓
Persistent State
   ↓
Verification
   ↓
Artifact
   ↓
Provenance
   ↓
Audit
```

with no architectural dependency on external AI services.

---

# 37. Status

This document is the authoritative high-level architecture for the Sovereign AI prototype.

Detailed subsystem specifications MUST conform to this architecture.

**Status: FROZEN — BASELINE ARCHITECTURE**

```
```
