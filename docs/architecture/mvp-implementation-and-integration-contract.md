# `11-mvp-implementation-and-integration-contract.md`

````markdown
# Sovereign AI Workbench
## MVP Implementation & Integration Contract

**Project:** Sovereign AI — SIH 2026 Prototype  
**Document:** MVP Implementation & Integration Contract  
**Document ID:** SAI-DOC-011  
**Status:** FROZEN — IMPLEMENTATION BASELINE  
**Version:** 1.0

---

# 1. Purpose

This document converts the previously defined architecture into an implementation contract.

It exists to prevent implementation drift.

The implementation agent MUST treat the architecture documents as authoritative and MUST NOT redesign the system merely because another implementation approach appears convenient.

The prototype is being developed incrementally:

```text
Architecture
    ↓
Repository scaffold
    ↓
Subsystem implementation
    ↓
Package validation
    ↓
Integration
    ↓
End-to-end validation
````

The implementation agent must preserve this order.

---

# 2. Core Implementation Principle

The prototype is NOT:

> "A chatbot with some tools."

It is:

> **A local agentic AI workbench that maintains persistent task state, retrieves private knowledge, invokes governed local tools, uses local open-weight models, verifies outputs, and produces traceable artifacts.**

---

# 3. Hardware Target

The primary development machine is:

```text
CPU:
Intel Core i7-9850H
6 cores / 12 logical processors

RAM:
16 GB system RAM

GPU:
NVIDIA Quadro T1000
4 GB VRAM available to CUDA/Vulkan runtime

Docker:
approximately 7.44 GB RAM allocated

OS:
Windows

Local inference:
llama.cpp

Primary prototype model:
Qwen3-8B Q4_K_M
```

Important:

The architecture MUST NOT assume access to a 120B-class model.

The prototype must remain functional on the available hardware.

---

# 4. Current Inference Reality

Validated locally with llama.cpp:

```text
Model:
Qwen3-8B Q4_K_M

Model file:
approximately 4.68 GiB

Parameters:
approximately 8.19B
```

Observed benchmark:

```text
Context: 4096
GPU layers: 20

Prompt processing:
~119.6 tokens/s

Generation:
~5.39 tokens/s
```

Observed:

```text
Context: 8192
GPU layers: 20

Prompt processing:
~104.3 tokens/s

Generation:
~4.39 tokens/s
```

Observed:

```text
Context: 16384
GPU layers: 10

Prompt processing:
~81.2 tokens/s

Generation:
~3.77 tokens/s
```

At:

```text
Context: 16384
GPU layers: 20
```

the Quadro T1000 ran out of device memory.

Therefore the MVP MUST NOT assume that a full 16K context with high GPU offload is practical on this machine.

---

# 5. Critical Context Architecture

The system MUST NOT attempt to solve large-document processing by continuously increasing model context.

The fundamental strategy is:

```text
Large Task
    ↓
Persistent Task State
    +
Local Knowledge Retrieval
    +
Targeted Context Assembly
    +
Iterative Model Calls
```

The model's context is a temporary working space.

Persistent state is the long-term task state.

The local knowledge base is the searchable organizational information layer.

These MUST remain separate concepts.

---

# 6. Context Contract

The model context MUST contain only information relevant to the current model invocation.

Typical invocation:

```text
System instructions
+
Current task objective
+
Relevant task state
+
Retrieved evidence
+
Relevant tool results
+
Current step instructions
```

It MUST NOT automatically contain:

```text
entire conversation
entire source document
entire task history
all previous tool outputs
all retrieved chunks
all artifacts
```

---

# 7. Context Budget

The Agent Host MUST maintain an explicit context budget.

Example conceptual budget:

```text
System instructions       ~800 tokens
Task state                ~800 tokens
Retrieved evidence        ~3,000 tokens
Tool results              ~1,000 tokens
Current instruction       ~500 tokens
Generation reserve        ~1,000 tokens
------------------------------------------------
Total                     ~7,100 tokens
```

These are implementation targets, not hardcoded universal values.

The context manager must calculate actual token usage.

---

# 8. Context Overflow Policy

If the next invocation would exceed the configured context budget:

```text
DO NOT:
    blindly send the request

INSTEAD:
    reduce retrieved evidence
    summarize state
    remove redundant tool output
    retrieve more selectively
    start a new model invocation
```

Context overflow must be handled by the Agent Host.

It must not be left to the model server.

---

# 9. Persistent Task State

Every task must have persistent state independent of the model context.

Conceptually:

```text
TaskState
├── objective
├── plan
├── completed_steps
├── findings
├── evidence_refs
├── unresolved_questions
├── tool_results
├── calculations
├── verification_results
├── artifacts
└── current_step
```

The actual storage technology may be SQLite for the MVP.

---

# 10. SQLite as MVP State Store

The MVP SHOULD use SQLite unless an existing project dependency makes another local database substantially simpler.

Reasons:

```text
Local
Portable
No external service
Low resource usage
Persistent
Easy backup
Easy inspection
```

A future enterprise deployment may replace this with PostgreSQL or another governed datastore.

The Agent Host must not depend on SQLite-specific behavior beyond the persistence interface.

---

# 11. Knowledge Storage

The local Knowledge subsystem is separate from Task State.

Conceptually:

```text
Task State
    ≠
Knowledge Base
```

Task State answers:

> What has this agent already done?

Knowledge Base answers:

> What does the organization's stored information say?

---

# 12. MVP Knowledge Architecture

The prototype should support:

```text
Document
 ↓
Extraction/OCR
 ↓
Chunking
 ↓
Metadata
 ↓
Embedding/indexing
 ↓
Local retrieval
 ↓
Evidence
```

The implementation should remain modular.

The exact vector database may be selected based on simplicity and local resource usage.

---

# 13. DataHub

DataHub MCP is present on the developer's laptop.

However:

**DataHub is OUT OF THE CORE MVP EXECUTION PATH.**

It should remain an architectural extension point.

The MVP must not become dependent on DataHub availability.

Future architecture:

```text
Agent
 ├── Knowledge MCP
 └── DataHub MCP
```

MVP:

```text
Agent
 └── Knowledge MCP
```

---

# 14. MCP Principle

MCP is the integration contract between the Agent Host and capabilities/context providers.

The Agent Host SHOULD NOT contain hardcoded knowledge-base or tool implementation logic where an MCP boundary has already been defined.

Conceptually:

```text
Agent Host
   │
   ├── Knowledge MCP
   └── Tools MCP
```

---

# 15. Tool Boundary

The Agent Host must never execute arbitrary operating-system commands directly on behalf of the model.

Correct:

```text
Agent
 ↓
Tool Manager
 ↓
Policy Check
 ↓
Sandbox
 ↓
Tool
```

Incorrect:

```text
LLM
 ↓
os.system(...)
```

---

# 16. MVP Tool Set

The initial implementation should prioritize:

```text
read_file
write_file
calculate
execute_python
create_docx
create_xlsx
create_pptx
```

Additional tools may exist internally but are not required for the first end-to-end milestone.

---

# 17. Sandbox Contract

Python/code execution must occur inside a controlled environment.

At minimum:

```text
restricted filesystem
resource limits
execution timeout
no external network access
isolated working directory
```

The exact sandbox mechanism is implementation-specific.

---

# 18. Model Gateway

The Agent Host MUST NOT directly depend on a particular model implementation.

Conceptually:

```text
Agent Host
    ↓
Model Gateway
    ↓
Model Adapter
    ↓
llama.cpp
    ↓
Local GGUF model
```

This enables future model replacement.

---

# 19. Model Adapter Contract

The Agent Host should interact with an abstract interface such as:

```text
generate()
stream()
health()
model_info()
```

The exact interface may differ, but model-specific API details must remain behind the gateway.

---

# 20. Current Model Strategy

For the laptop MVP:

```text
Primary reasoning model:
Qwen3-8B Q4_K_M
```

Do not create unnecessary multi-model infrastructure before the single-model path is stable.

However, the gateway MUST preserve the ability to add:

```text
Reasoning model
Coding model
Vision model
```

later.

---

# 21. Model Routing MVP

Full sophisticated model routing is NOT required initially.

The MVP may implement:

```text
Task classification
      ↓
model capability selection
      ↓
local model
```

If only one model is installed:

```text
All supported tasks
      ↓
Qwen3-8B
```

The routing interface should still exist.

---

# 22. Vision Strategy

The current Qwen3-8B GGUF test is text-only.

Therefore the MVP should NOT falsely claim that this exact model performs multimodal understanding.

Multimodal support should be implemented through a separate local vision/OCR pipeline.

Conceptually:

```text
Scanned PDF/image
      ↓
OCR / local vision subsystem
      ↓
Extracted text + visual metadata
      ↓
Knowledge / Task State
      ↓
Reasoning model
```

---

# 23. OCR Principle

OCR output should not automatically become trusted truth.

It should be treated as extracted evidence.

Example:

```text
OCR:
"6.84 mm"

Source:
Inspection Report
Page 37
```

The system should preserve the source reference.

---

# 24. Artifact Engine

Artifact generation MUST remain separate from model generation.

```text
LLM
 ↓
Structured artifact specification
 ↓
Artifact Engine
 ↓
DOCX/XLSX/PPTX
```

The model should not be responsible for manually constructing binary document formats.

---

# 25. Verification

Artifacts MUST pass through verification.

At minimum:

```text
structural validation
content requirements
evidence validation
calculation validation where applicable
```

A generated file is not automatically a verified file.

---

# 26. Artifact Status

Use explicit status values:

```text
GENERATED
VALIDATING
VERIFIED
FAILED
AWAITING_HUMAN_REVIEW
SUPERSEDED
```

---

# 27. Audit Layer

Every meaningful operation should create an audit event.

Examples:

```text
TASK_CREATED
FILE_UPLOADED
DOCUMENT_PROCESSED
RETRIEVAL_PERFORMED
MODEL_INVOKED
TOOL_EXECUTED
CALCULATION_PERFORMED
ARTIFACT_CREATED
VERIFICATION_PERFORMED
TASK_COMPLETED
TASK_FAILED
```

The audit system should avoid storing unnecessary sensitive payloads.

---

# 28. Security Principle

Security must be enforced by infrastructure and backend policy.

The frontend MUST NOT be trusted to enforce:

```text
permissions
network isolation
tool restrictions
artifact verification
```

---

# 29. Network Sovereignty

The MVP must operate without cloud AI APIs.

No automatic fallback to:

```text
OpenAI
Anthropic
Google
Cohere
Hugging Face hosted inference
cloud OCR
cloud document processing
```

is permitted during task execution.

Model downloads are a setup/development operation, not runtime inference.

---

# 30. Network Demonstration

The prototype should support an actual demonstrable sovereignty test.

Recommended:

```text
Run task
+
observe local network activity
+
show no external AI/API calls
```

Ideally combine:

```text
OS/firewall/network telemetry
+
application audit logs
```

Do not rely solely on an application-generated statement saying:

> "No external calls."

---

# 31. Configuration

All environment-specific configuration should be externalized.

Examples:

```text
MODEL_ENDPOINT
MODEL_NAME
MODEL_CONTEXT_SIZE
DATABASE_PATH
KNOWLEDGE_PATH
ARTIFACT_PATH
SANDBOX_PATH
LOG_LEVEL
```

Use `.env` or equivalent local configuration.

Do not hardcode machine-specific paths into business logic.

---

# 32. Secrets

No secrets should be committed to Git.

Use:

```text
.env
```

with:

```text
.env.example
```

containing placeholders.

---

# 33. Repository Principle

The repository must clearly separate:

```text
application code
configuration
tests
documentation
runtime data
generated artifacts
```

Generated runtime data must not accidentally become source code.

---

# 34. Recommended Repository Structure

The implementation may use a structure similar to:

```text
sovereign-ai/
│
├── docs/
│   ├── 01-project-charter.md
│   ├── 02-system-architecture.md
│   ├── 03-security-and-sovereignty.md
│   ├── 04-data-context-memory-architecture.md
│   ├── 05-model-gateway-and-routing.md
│   ├── 06-agent-host-and-orchestration.md
│   ├── 07-knowledge-retrieval-and-document-intelligence.md
│   ├── 08-tool-execution-and-sandbox.md
│   ├── 09-artifact-engine-and-verification.md
│   ├── 10-ui-api-and-user-workspace.md
│   └── 11-mvp-implementation-and-integration-contract.md
│
├── backend/
├── frontend/
├── agent/
├── model_gateway/
├── knowledge/
├── tools/
├── sandbox/
├── artifacts/
├── verification/
├── audit/
├── tests/
├── configs/
├── scripts/
└── runtime/
```

The exact package names may change during implementation only if the architecture remains unchanged.

---

# 35. Runtime Data

Runtime state should remain outside source packages.

Example:

```text
runtime/
├── database/
├── uploads/
├── knowledge/
├── workspaces/
├── artifacts/
├── logs/
└── cache/
```

Do not commit confidential test documents.

---

# 36. Docker Principle

Docker should be used where isolation or reproducibility is beneficial.

However, Docker must NOT be used merely because containerization sounds enterprise-grade.

The prototype should minimize resource overhead.

---

# 37. Laptop Resource Constraint

The machine has:

```text
16 GB RAM
4 GB discrete GPU VRAM
```

Therefore:

```text
multiple large models simultaneously
+
large Docker memory allocations
+
large vector databases
+
heavy observability stacks
```

are undesirable for the MVP.

Prefer lightweight local services.

---

# 38. Concurrency

The MVP should prioritize correctness over parallel inference throughput.

Default:

```text
one active heavy inference task
```

is acceptable.

The architecture should allow future concurrency.

Do not solve a future high-concurrency enterprise problem at the expense of making the laptop prototype unstable.

---

# 39. Model Loading

The model gateway should avoid repeatedly loading/unloading the same model for every request.

Prefer:

```text
Application
 ↓
Model Gateway
 ↓
Persistent llama.cpp server
```

rather than:

```text
request
 ↓
launch model
 ↓
generate
 ↓
terminate model
```

unless resource pressure requires otherwise.

---

# 40. Context vs Model Lifetime

Model lifetime and context lifetime are different.

The model can remain loaded while individual task invocations have separate contexts.

Conceptually:

```text
One loaded model
    │
    ├── Task A context
    ├── Task B context
    └── Task C context
```

Concurrency may still be limited by hardware.

---

# 41. Persistent State vs Context

Never use the model's context as the database.

Correct:

```text
Task State
   ↓
Context Builder
   ↓
Model Invocation
```

The model invocation is disposable.

The task state is persistent.

---

# 42. Context Compaction

When task state becomes large:

```text
raw events
 ↓
structured state
 ↓
compressed summary
```

The model should receive the structured state relevant to the current step.

Do not repeatedly feed historical raw events.

---

# 43. Retrieval Instead of Replay

If a prior source is needed:

```text
Task
 ↓
Evidence reference
 ↓
Knowledge retrieval
 ↓
Relevant source excerpt
```

Do not replay the entire source document.

---

# 44. Tool Results

Tool results should be persisted in structured form.

Example:

```text
CalculationResult
├── inputs
├── formula
├── output
├── units
└── verification
```

The next model invocation should receive only the relevant representation.

---

# 45. Agent Step Contract

Every agent step should have:

```text
step_id
task_id
type
status
input_refs
output_refs
started_at
completed_at
```

This allows the workflow to resume and audit execution.

---

# 46. Idempotency

Important operations should be designed to avoid accidental duplication.

For example:

```text
create artifact
```

should not create five copies merely because the UI reconnects.

Where practical, operations should use:

```text
task_id
step_id
operation_id
```

for idempotency.

---

# 47. Failure Recovery

If a process crashes:

```text
Application crash
      ↓
Restart
      ↓
Load persistent task state
      ↓
Determine last completed step
      ↓
Resume or safely fail
```

The system must not assume the entire task can simply be restarted from zero.

---

# 48. Transaction Principle

State updates associated with important transitions should be persisted atomically where practical.

For example:

```text
Tool completed
+
tool result stored
+
step marked completed
```

should not leave the task in an ambiguous state.

---

# 49. Logging

Use structured logs.

Each important log entry should contain enough information to correlate activity:

```text
timestamp
level
component
task_id
step_id
request_id
event
```

Do not log sensitive document contents by default.

---

# 50. Observability

The MVP should provide enough observability to answer:

```text
What happened?
Where did it fail?
Which model ran?
Which tool ran?
Which evidence was retrieved?
Which artifact was generated?
Why did verification fail?
```

This is more important than implementing a sophisticated metrics platform.

---

# 51. Error Boundary

Subsystem errors should be converted into structured application errors.

Example:

```text
Model Gateway
      ↓
MODEL_UNAVAILABLE

Knowledge
      ↓
RETRIEVAL_FAILED

Sandbox
      ↓
EXECUTION_TIMEOUT

Artifact Engine
      ↓
ARTIFACT_GENERATION_FAILED

Verification
      ↓
VERIFICATION_FAILED
```

---

# 52. No Silent Fallbacks

The implementation must not silently substitute another system when a component fails.

Example:

```text
Local model unavailable
```

must not result in:

```text
cloud model call
```

unless the architecture explicitly introduces and authorizes such a mode in the future.

The MVP does not.

---

# 53. Package Implementation Order

Implementation should proceed in this order:

```text
1. Repository scaffold
2. Configuration & common contracts
3. Model Gateway
4. Persistent Task State
5. Context Manager
6. Knowledge subsystem
7. Tool Manager
8. Sandbox
9. Agent Host
10. Artifact Engine
11. Verification
12. API
13. UI
14. Audit/observability integration
15. End-to-end integration
```

Some packages may be developed in parallel after their interfaces are frozen, but integration must follow dependency order.

---

# 54. Why Model Gateway Comes Early

The entire agent depends on reliable local inference.

Therefore establish:

```text
llama.cpp
 ↓
local model
 ↓
stable API
 ↓
Model Gateway
```

before building sophisticated agent behavior.

---

# 55. Why Persistent State Comes Early

Without persistent state, the context-limit architecture cannot be properly implemented.

Therefore establish:

```text
Task
 ↓
Task State
 ↓
Context Builder
```

before building complex multi-step workflows.

---

# 56. Why Context Manager Is a First-Class Package

Context management is one of the primary technical challenges of this prototype.

It must handle:

```text
token budget
retrieval selection
state summarization
tool-result compression
context assembly
overflow prevention
```

It must NOT simply concatenate every available piece of information.

---

# 57. Agent Host Comes After Foundations

The Agent Host depends on:

```text
Model Gateway
Task State
Context Manager
Knowledge
Tools
```

Therefore it should not be implemented as a giant monolithic package first.

---

# 58. Artifact and Verification After Agent

Artifact generation depends on agent outputs.

Verification depends on artifacts and task requirements.

Therefore:

```text
Agent
 ↓
Artifact
 ↓
Verification
```

should be stabilized before final UI integration.

---

# 59. UI Comes After Backend Contracts

The UI should consume stable API contracts.

Do not build the frontend around assumptions about backend behavior that has not been implemented.

---

# 60. Package Completion Rule

A package is NOT considered complete because:

```text
code compiles
```

or:

```text
server starts
```

It is complete only when:

```text
implementation
+
unit tests
+
integration tests where applicable
+
failure tests
+
documentation
+
acceptance criteria
```

pass.

---

# 61. Package Validation Protocol

After implementing each package:

```text
1. Run formatter/linter
2. Run static checks
3. Run unit tests
4. Run package-specific integration tests
5. Test failure paths
6. Inspect logs
7. Verify interfaces
8. Update implementation report
```

Only then proceed.

---

# 62. Implementation Reports

Each completed package should produce a concise report containing:

```text
Package
Implemented functionality
Files changed
Tests performed
Tests passed
Known limitations
Integration dependencies
Deviations from specification
```

Any deviation MUST be explicitly documented.

---

# 63. Gemini/Antigravity Rule

The implementation agent MUST NOT:

* redesign the architecture without authorization
* introduce cloud APIs
* replace local inference with hosted inference
* bypass MCP boundaries
* bypass the sandbox
* put all task context into every prompt
* remove persistent task state
* silently remove verification
* silently remove auditability
* invent unsupported functionality
* create unnecessary microservices
* add dependencies without justification

---

# 64. Ambiguity Rule

If implementation details are unspecified but architecture is clear:

```text
choose the simplest implementation
```

If architecture itself is ambiguous:

```text
STOP
identify ambiguity
report it
do not silently redesign
```

---

# 65. Dependency Rule

Every new dependency must have a clear reason.

Before adding a dependency, evaluate:

```text
Does Python standard library solve it?
Does an existing dependency solve it?
Is it lightweight enough?
Does it work offline?
Does it support Windows/Docker environment?
Does it introduce cloud/network requirements?
```

---

# 66. Offline Installation Principle

Runtime operation must not require downloading packages dynamically.

Dependencies should be installed during environment setup.

The application must not perform:

```text
pip install
npm install
model download
external API discovery
```

during normal task execution.

---

# 67. Model Download Principle

Models may be downloaded during controlled setup.

Runtime inference must use locally available model files.

Example:

```text
Setup:
Internet → model download

Runtime:
Local model only
```

---

# 68. Test Data

The repository should include synthetic/non-sensitive test documents.

Do not commit real confidential enterprise material.

Example:

```text
tests/data/
    synthetic_inspection_report.pdf
    synthetic_sop.pdf
    sample_table.xlsx
```

---

# 69. End-to-End Demo Scenario

The MVP must support one flagship workflow.

Recommended:

> **Read a scanned inspection report, extract findings, retrieve the applicable local SOP, perform a calculation, verify the result, and generate a DOCX approval note.**

Pipeline:

```text
Upload
 ↓
OCR
 ↓
Document processing
 ↓
Knowledge retrieval
 ↓
Task planning
 ↓
Reasoning
 ↓
Calculation
 ↓
Verification
 ↓
DOCX generation
 ↓
Artifact validation
 ↓
Audit
```

---

# 70. Secondary Demo Scenario

The MVP should also support a coding workflow:

> Analyze or generate a small piece of code, execute it in the sandbox, verify the result, and return the output.

Pipeline:

```text
User request
 ↓
Agent
 ↓
Coding/model capability
 ↓
Python/tool execution
 ↓
Sandbox
 ↓
Verification
 ↓
Result/artifact
```

---

# 71. Context-Limit Demo

The system should be able to demonstrate:

```text
Input document
>
model working context
```

yet still process it.

The demonstration should show:

```text
Document
 ↓
chunk/retrieve
 ↓
persistent findings/state
 ↓
targeted model calls
 ↓
final result
```

This directly addresses one of the most likely judge questions:

> "If your local model only has 8K context, how can it handle a 100-page report?"

---

# 72. Model Routing Demo

If multiple local models are installed by demonstration time:

```text
Document task
 ↓
Reasoning model

Coding task
 ↓
Coding model
```

If only one model is available:

```text
Different task types
 ↓
same local model
```

The architecture must still expose the routing decision.

Do not fake multiple models.

---

# 73. Sovereignty Demo

The final demonstration should visibly establish:

```text
Local model
Local knowledge
Local tools
Local artifact generation
No cloud AI calls
```

A network monitor/firewall should provide independent evidence where possible.

---

# 74. Prototype Success Criteria

The prototype is successful if a judge can observe:

```text
1. User uploads private document.
2. Document stays local.
3. Agent creates a multi-step plan.
4. Relevant knowledge is retrieved locally.
5. Model processes targeted context rather than entire document.
6. Tool is invoked through a controlled interface.
7. Calculation/code runs in sandbox.
8. Result is verified.
9. Real DOCX/XLSX/PPTX artifact is generated.
10. Artifact provenance is available.
11. Task state persists.
12. Audit trail exists.
13. No external AI/API call occurs.
14. The system can explain why each major action occurred.
```

---

# 75. What the MVP Does NOT Promise

The prototype must NOT claim:

```text
perfect accuracy
fully autonomous industrial decisions
unlimited context
unlimited hardware performance
enterprise-scale concurrency
complete multimodal understanding of every document
production-grade compliance certification
complete ERP/SAP/PLM integration
```

Instead it demonstrates the architecture required to support these capabilities.

---

# 76. Enterprise Scaling Path

The MVP should have clear upgrade paths.

Laptop:

```text
Qwen3-8B
llama.cpp
SQLite
local vector/index
single sandbox
single/few concurrent tasks
```

Enterprise server:

```text
larger open-weight models
vLLM/TensorRT-LLM/etc.
PostgreSQL
enterprise vector/search infrastructure
distributed workers
multiple GPUs
multiple model instances
enterprise IAM
DataHub
EDMS
SAP
PLM
```

The Agent Host abstraction should remain conceptually stable.

---

# 77. Future DataHub Integration

Future:

```text
Agent
   │
   ├── Knowledge MCP
   │
   └── DataHub MCP
          │
          ├── schema
          ├── lineage
          ├── ownership
          └── quality
```

This must be treated as an extension, not a requirement for the laptop MVP.

---

# 78. Future Model Expansion

Future:

```text
Model Router
├── Reasoning model
├── Coding model
├── Vision model
└── Embedding/reranking models
```

The MVP should make this possible without requiring all models simultaneously.

---

# 79. Future Multi-Agent Expansion

The MVP should NOT begin with a large collection of independent agents.

First establish:

```text
one Agent Host
+
persistent state
+
tools
+
retrieval
+
verification
```

Future specialized agents can then be introduced behind the same orchestration architecture.

---

# 80. Multi-Agent Resource Rule

Multiple logical agents do not require multiple model copies.

Example:

```text
Research Agent
Coding Agent
Critic Agent
        │
        ▼
Model Gateway
        │
        ▼
Local Model
```

Hardware limitations may require sequential execution.

This is acceptable for the MVP.

---

# 81. No Artificial Complexity

Do not create:

```text
20 microservices
```

when:

```text
5 well-separated local packages
```

are sufficient.

The architectural boundaries matter more than the number of processes.

---

# 82. MVP Architectural Boundary

The MVP should conceptually contain:

```text
┌────────────────────────────────────────────┐
│                    UI                      │
└──────────────────────┬─────────────────────┘
                       │
┌──────────────────────▼─────────────────────┐
│                API Gateway                 │
└──────────────────────┬─────────────────────┘
                       │
┌──────────────────────▼─────────────────────┐
│                 Agent Host                 │
│                                            │
│ Planner / Context / Router / State         │
└───────┬──────────────┬─────────────┬───────┘
        │              │             │
        ▼              ▼             ▼
  Model Gateway   Knowledge MCP   Tools MCP
        │              │             │
        ▼              ▼             ▼
    llama.cpp       Local KB       Sandbox
                                      │
                                      ▼
                               Artifact Engine
                                      │
                                      ▼
                                 Verification
                                      │
                                      ▼
                                   Audit
```

---

# 83. Integration Rule

Each subsystem must communicate through defined interfaces.

Avoid:

```text
package A imports package B's internal implementation
```

when an interface should exist.

Prefer:

```text
Agent Host
 ↓
interface
 ↓
implementation
```

---

# 84. No Circular Dependencies

The architecture must avoid circular dependency chains.

For example:

```text
Agent → Knowledge
Knowledge → Agent
```

should not occur.

The Knowledge subsystem provides information.

The Agent Host consumes it.

---

# 85. Domain Model Principle

Shared domain objects should live in a stable/common layer.

Examples:

```text
Task
TaskState
Evidence
ToolCall
Artifact
VerificationResult
ModelRequest
ModelResponse
```

Avoid duplicating these definitions across packages.

---

# 86. Schema Evolution

Schemas should be versionable.

If:

```text
TaskState v1
```

changes, migration must be considered.

Do not silently break existing task state.

---

# 87. Configuration Hierarchy

Configuration should follow:

```text
defaults
 ↓
environment configuration
 ↓
runtime configuration
```

Secrets remain outside source control.

---

# 88. Localhost Principle

For the MVP, services should communicate over:

```text
localhost
```

or an isolated Docker network.

Do not expose unnecessary services to the LAN.

---

# 89. Port Exposure

Only required interfaces should be exposed.

Example:

```text
UI/API → user-accessible port
Internal services → localhost/private Docker network
```

Model servers and tool services should not be unnecessarily exposed externally.

---

# 90. Security-by-Default

Default behavior should be:

```text
deny
```

for:

```text
network access
tool access
filesystem access
unauthorized files
```

Capabilities must be explicitly granted.

---

# 91. Final Integration Test

The complete system must pass:

```text
Test:
Synthetic scanned inspection report
```

Expected:

```text
Upload
 ↓
OCR
 ↓
Chunk/index
 ↓
Retrieve
 ↓
Plan
 ↓
Analyze
 ↓
Calculate
 ↓
Verify
 ↓
Generate DOCX
 ↓
Validate
 ↓
Audit
```

---

# 92. Full Failure Test

At least one deliberate failure should be injected.

Example:

```text
Expected calculation:
68.4%

Generated:
84%
```

Expected:

```text
Verification failure
 ↓
Agent receives failure
 ↓
Correction
 ↓
Recalculation
 ↓
Verification pass
```

---

# 93. Context Failure Test

Provide a document larger than the model context.

Expected:

```text
No context overflow crash.

System:
retrieves relevant portions
+
maintains persistent state
+
uses multiple model invocations.
```

---

# 94. Network Failure Test

Block external network.

Expected:

```text
System continues operating.
```

Then verify that the application did not attempt cloud fallback.

---

# 95. Model Failure Test

Stop the local model server.

Expected:

```text
Clear MODEL_UNAVAILABLE state
```

Not:

```text
silent cloud fallback
```

---

# 96. Sandbox Failure Test

Force execution timeout.

Expected:

```text
EXECUTION_TIMEOUT
```

The Agent Host should receive a structured failure and decide whether to retry or terminate.

---

# 97. Artifact Failure Test

Provide invalid/missing required artifact content.

Expected:

```text
Verification failure
```

The artifact must not be marked verified.

---

# 98. Persistence Failure Test

Restart the backend during/after a task.

Expected:

```text
Persistent state remains recoverable.
```

Where recovery of an in-progress operation is unsafe, the system should mark it failed rather than falsely marking it complete.

---

# 99. Implementation Discipline

For every package:

```text
READ SPEC
 ↓
IMPLEMENT
 ↓
TEST
 ↓
REPORT
 ↓
REVIEW
 ↓
FREEZE
```

Do not implement several packages simultaneously before their predecessors are validated.

---

# 100. Change Control

Any architectural change requires:

```text
1. Identify affected specification.
2. Explain why change is necessary.
3. Identify affected packages.
4. Update documentation.
5. Revalidate dependent packages.
```

Do not allow silent architectural drift.

---

# 101. Gemini/Antigravity Instruction

When given an implementation package prompt, the implementation agent must:

```text
1. Read this document.
2. Read all listed dependency documents.
3. Inspect the current repository.
4. Inspect existing implementation.
5. Implement only the requested package.
6. Preserve existing contracts.
7. Add tests.
8. Run validation.
9. Report deviations.
10. Stop.
```

It must NOT proceed automatically to the next package.

---

# 102. Package Prompt Principle

Each implementation prompt will explicitly state:

```text
PACKAGE
OBJECTIVE
INPUT CONTRACTS
OUTPUT CONTRACTS
FILES TO CREATE/MODIFY
RESTRICTIONS
TESTS
ACCEPTANCE CRITERIA
```

This keeps implementation scope bounded.

---

# 103. Do Not Rebuild Existing Work

Before writing code, the implementation agent MUST inspect the repository.

If a required component already exists:

```text
inspect
validate
extend if appropriate
```

Do not create duplicate implementations.

---

# 104. Do Not Delete Functionality Without Approval

Existing working functionality must not be removed merely to simplify implementation.

If replacement is necessary:

```text
document
test
migrate
remove only after validation
```

---

# 105. Final MVP Boundary

The laptop prototype is therefore:

```text
LOCAL UI
    ↓
LOCAL API
    ↓
AGENT HOST
    ├── persistent task state
    ├── context manager
    ├── model gateway
    ├── local knowledge retrieval
    ├── tool manager
    └── verification orchestration
            │
            ├── llama.cpp / Qwen3-8B
            ├── local OCR
            ├── local knowledge store
            ├── sandbox
            └── artifact engine
```

DataHub is an architectural extension.

Large-scale enterprise infrastructure is an architectural extension.

The MVP must prove the core sovereign workflow.

---

# 106. Final Definition of Done

The MVP implementation baseline is satisfied when:

```text
✓ Local model works
✓ Model gateway works
✓ Task state persists
✓ Context is explicitly budgeted
✓ Large documents use retrieval/state rather than prompt replay
✓ Knowledge retrieval works locally
✓ Tools are governed
✓ Python executes in sandbox
✓ Artifacts are generated
✓ Artifacts are verified
✓ Evidence is traceable
✓ Audit events exist
✓ UI exposes task execution
✓ API boundaries are stable
✓ No cloud AI fallback exists
✓ Network sovereignty can be independently demonstrated
✓ End-to-end inspection workflow succeeds
✓ Failure/recovery paths are tested
```

---

# 107. Non-Negotiable Architecture

The following must remain true throughout development:

```text
LOCAL
MODEL-AGNOSTIC
TASK-PERSISTENT
CONTEXT-BUDGETED
MCP-NATIVE
TOOL-GOVERNED
SANDBOXED
EVIDENCE-GROUNDED
VERIFIED
AUDITABLE
NO-CLOUD-FALLBACK
```

If an implementation decision conflicts with one of these principles, stop and review the architecture before proceeding.

---

# 108. Final Engineering Principle

The prototype should not attempt to prove:

> "A small laptop can run a giant enterprise AI system."

It should prove something more important:

> **The same sovereign architecture can operate on constrained hardware today and scale to enterprise infrastructure tomorrow without changing its fundamental control model.**

The laptop is the demonstration environment.

The architecture is the product.

**Status: FROZEN — MVP IMPLEMENTATION & INTEGRATION CONTRACT**

```
```
