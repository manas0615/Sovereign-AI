# `10-ui-api-and-user-workspace.md`

````markdown
# Sovereign AI Workbench
## UI, API & User Workspace Specification

**Project:** Sovereign AI — SIH 2026 Prototype  
**Document:** UI, API & User Workspace  
**Document ID:** SAI-DOC-010  
**Status:** FROZEN — BASELINE USER EXPERIENCE ARCHITECTURE  
**Version:** 1.0

**Depends On:**
- 01-project-charter.md
- 02-system-architecture.md
- 03-security-and-sovereignty.md
- 04-data-context-memory-architecture.md
- 05-model-gateway-and-routing.md
- 06-agent-host-and-orchestration.md
- 07-knowledge-retrieval-and-document-intelligence.md
- 08-tool-execution-and-sandbox.md
- 09-artifact-engine-and-verification.md

---

# 1. Purpose

This document defines the user-facing interface and API boundary of the Sovereign AI Workbench.

The UI must not look like a generic chatbot.

It must communicate the actual system model:

> User gives a goal → Agent plans → retrieves private knowledge → uses governed tools → verifies its work → produces an artifact → records the operation.

The UI is therefore a **workbench**, not merely a conversation screen.

---

# 2. Primary UX Principle

The user should be able to understand what the system is doing without needing to understand the underlying architecture.

The experience should expose:

```text
Goal
 ↓
Plan
 ↓
Evidence
 ↓
Actions
 ↓
Verification
 ↓
Deliverable
````

while keeping implementation details behind expandable views.

---

# 3. Prototype UI Scope

The MVP should contain five primary areas:

```text
┌─────────────────────────────────────────────────────────┐
│ Sovereign AI Workbench                                  │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│ Navigation   │              Main Workspace              │
│              │                                          │
│ New Task     │                                          │
│ Tasks        │                                          │
│ Files        │                                          │
│ Artifacts    │                                          │
│ Audit        │                                          │
│              │                                          │
└──────────────┴──────────────────────────────────────────┘
```

The exact visual design is implementation-specific.

---

# 4. Main Navigation

The prototype should expose:

```text
New Task
Tasks
Files
Artifacts
Audit
Settings
```

Optional:

```text
Models
Knowledge
System Status
```

---

# 5. New Task

The primary entry point is:

```text
+ New Task
```

The user should be able to:

* describe a goal
* attach files
* optionally specify output requirements
* start the task

Example:

> Review the attached inspection report, compare the findings against the applicable SOP, calculate the relevant values, and prepare an approval note.

---

# 6. Task-Centric Design

The primary unit of work is a **Task**, not a chat message.

Conceptually:

```text
Task
├── User request
├── Inputs
├── Plan
├── Agent steps
├── Evidence
├── Tool calls
├── Verification
├── Artifacts
└── Audit events
```

This allows long-running agentic work without depending on a single conversation context.

---

# 7. Why Tasks Instead of Only Chat

A normal chatbot assumes:

```text
message
 ↓
response
```

The Sovereign Workbench requires:

```text
task
 ↓
multiple model invocations
 ↓
multiple tool calls
 ↓
persistent state
 ↓
artifact
```

Therefore the task must exist independently from an individual model context.

---

# 8. Task Creation

A task should receive:

```text
task_id
created_at
user_id
title
status
```

The user-facing title may be generated from the request but must remain editable.

Example:

```text
Review Inspection Report — P-101
```

---

# 9. Task Status

The UI should expose a high-level status.

Recommended states:

```text
QUEUED
PLANNING
RETRIEVING
EXECUTING
VERIFYING
WAITING_FOR_USER
COMPLETED
FAILED
CANCELLED
```

---

# 10. Status Must Reflect Reality

The UI must not display:

> "Thinking..."

for the entire duration of a multi-step workflow.

Instead show meaningful states:

```text
Reading inspection report
Retrieving applicable SOP
Analyzing findings
Running calculation
Verifying calculation
Generating approval note
Validating document
```

This makes the agentic workflow visible.

---

# 11. Task Workspace

Each task gets a logical workspace.

Conceptually:

```text
Task
├── Inputs
├── Working Data
├── Evidence
├── Tool Activity
├── Verification
└── Outputs
```

The user should be able to inspect these categories.

---

# 12. Chat / Instruction Panel

The UI should retain a conversational interaction area.

However, conversation is subordinate to the task.

The user can:

```text
ask a question
provide clarification
change an instruction
request revision
request another artifact
```

without losing the underlying task state.

---

# 13. Context Continuity

A follow-up such as:

> "Use the same findings but make the approval note shorter."

must not require the system to replay the entire inspection report.

Instead:

```text
Existing Task State
      ↓
Relevant state retrieval
      ↓
New instruction
      ↓
New model context
```

---

# 14. Context Indicator

The UI should expose context information where useful.

For example:

```text
Working context
5.8K / 8K tokens
```

This is optional in the initial MVP but strongly recommended for demonstrating the architecture.

The UI should make clear that:

> The context indicator represents the current model invocation, not the size of the entire task.

---

# 15. Persistent Task State Indicator

Where practical, show:

```text
Task memory:
14 findings
8 evidence references
2 calculations
1 unresolved question
```

This helps demonstrate how the system handles tasks larger than one context window.

---

# 16. Plan Panel

The UI should provide a collapsible plan.

Example:

```text
Plan

✓ Ingest report
✓ Extract findings
✓ Retrieve applicable SOP
✓ Compare findings with SOP
✓ Calculate remaining thickness
● Verify calculations
○ Generate approval note
○ Validate artifact
```

The plan should be generated/maintained by the Agent Host.

---

# 17. Plan Is Not a Promise

The plan represents the agent's current execution plan.

It may change when new information is discovered.

Example:

```text
Initial plan
 ↓
Agent discovers missing equipment data
 ↓
Plan updated
 ↓
Retrieve equipment record
```

The UI should reflect the current state rather than pretending the original plan was immutable.

---

# 18. Evidence Panel

The user should be able to inspect the evidence used by the agent.

Example:

```text
Evidence

E-014
Inspection Report
Page 37
Section: Thickness Measurements

E-022
Maintenance SOP-17
Section 4.2
```

Selecting an evidence item should reveal the relevant source information.

---

# 19. Evidence vs Model Output

The UI should visually distinguish:

```text
SOURCE EVIDENCE
```

from:

```text
AI CONCLUSION
```

Example:

```text
Source:
"Measured thickness: 6.84 mm"

AI conclusion:
"Remaining thickness is approximately 68.4%."
```

This distinction is essential for trust.

---

# 20. Source Citation

Where possible, source references should be clickable.

Example:

```text
Inspection Report — Page 37
```

The UI may open:

* document preview
* relevant page
* extracted text
* source metadata

---

# 21. Retrieval Activity

The user should optionally be able to inspect retrieval activity.

Example:

```text
Knowledge Retrieval

Query:
"minimum allowable wall thickness for P-101"

Retrieved:
SOP-17 §4.2
Inspection Manual §7
Historical Report 2025
```

The UI should not expose excessive implementation noise by default.

---

# 22. Tool Activity Panel

The UI should show tool execution at a useful level.

Example:

```text
Tool Activity

✓ read_file
✓ calculate
✓ execute_python
✓ create_docx
✓ validate_artifact
```

Each item may be expandable.

---

# 23. Tool Detail

Expanded view may show:

```text
Tool:
calculate

Purpose:
Calculate remaining wall thickness

Status:
SUCCESS

Result:
68.4%
```

Sensitive arguments should be redacted where appropriate.

---

# 24. Sandbox Indicator

For code execution:

```text
Python execution
Sandbox: ACTIVE
Network: DISABLED
Status: PASSED
```

This is valuable both for security and for the SIH demonstration.

---

# 25. Sovereignty Indicator

The UI should provide a persistent system-level indication.

Example:

```text
● SOVEREIGN MODE
Local inference
External network: BLOCKED
```

The wording must accurately reflect actual runtime state.

The UI must never claim "air-gapped" merely because the architecture intends to be air-gapped.

---

# 26. Network Status

The system should expose an actual runtime network status where possible.

Example:

```text
Network Security

External egress:
BLOCKED

External AI APIs:
NONE

Cloud document processing:
NONE
```

This should be derived from actual system configuration/telemetry.

---

# 27. Important Sovereignty Rule

The UI must not be the source of truth for the sovereignty claim.

Correct architecture:

```text
Actual network policy
       ↓
Runtime telemetry
       ↓
UI
```

Not:

```text
UI says "Secure"
```

without technical evidence.

---

# 28. Artifact Panel

Generated files should appear separately from the conversation.

Example:

```text
Artifacts

Inspection_Approval_Note.docx
✓ Verified

Inspection_Analysis.xlsx
✓ Verified
```

---

# 29. Artifact Status

Every artifact should display:

```text
Draft
Validating
Verified
Verification Failed
Awaiting Review
Superseded
```

The user should never have to infer verification status from the filename.

---

# 30. Artifact Details

Selecting an artifact should show:

```text
Artifact:
Inspection_Approval_Note.docx

Status:
VERIFIED

Created:
Task #123

Evidence:
8 references

Verification:
7/7 checks passed

Integrity:
SHA-256 available
```

---

# 31. Verification Panel

The user should be able to inspect checks.

Example:

```text
Verification

✓ File integrity
✓ Required sections
✓ Evidence references
✓ Calculation accuracy
✓ Source availability
✓ Task requirements
✓ Artifact readability
```

If something fails:

```text
✗ Calculation accuracy
Expected: 68.4%
Found: 84%
```

---

# 32. Human Review State

If the system determines that human approval is required:

```text
WAITING FOR HUMAN REVIEW
```

The UI should explain why.

Example:

> The draft has been generated and verified against available evidence. Human approval is required before it can be treated as an operational decision.

---

# 33. User Clarification

The agent may encounter insufficient information.

Example:

> The report identifies equipment P-101 but does not contain its applicable operating limit. Please provide the equipment record or confirm whether the available SOP should be used.

The task becomes:

```text
WAITING_FOR_USER
```

The task state remains persistent.

---

# 34. Resuming a Task

When the user responds:

```text
User clarification
      ↓
Existing task state
      ↓
New model invocation
```

The entire prior conversation/document does not need to be replayed.

---

# 35. Task Cancellation

The user should be able to stop a running task.

Example:

```text
[Cancel Task]
```

Cancellation should attempt to stop:

* pending model generation
* pending tool calls
* sandbox execution

where technically possible.

---

# 36. Failed Tasks

A failed task should show:

```text
Task Failed

Stage:
Artifact validation

Reason:
Required section "Recommendation" was missing.

Actions:
[Retry]
[Modify Request]
[Inspect Details]
```

Do not show a generic:

> "Something went wrong."

when a useful failure reason is available.

---

# 37. Task History

The Tasks view should show:

```text
Recent Tasks

Inspection Approval Note
Completed
2 artifacts

Code Analysis
Completed
1 artifact

SOP Comparison
Waiting for user
```

---

# 38. Files View

The Files view should show files associated with tasks and knowledge ingestion.

For the MVP:

```text
Uploaded
Processing
Indexed
Failed
```

The UI should distinguish:

```text
Task Input
```

from:

```text
Knowledge Base Document
```

---

# 39. File Processing Status

Example:

```text
inspection.pdf

✓ Uploaded
✓ OCR completed
✓ Indexed
✓ 84 chunks
✓ Ready for retrieval
```

If processing fails:

```text
✗ OCR failed
Reason: unreadable page 17
```

---

# 40. Artifacts View

The Artifacts section provides a cross-task view.

Example:

```text
Artifact                 Task             Status
------------------------------------------------------
Approval_Note.docx       Inspection       VERIFIED
Analysis.xlsx            Inspection       VERIFIED
Report.pptx              Review           DRAFT
```

---

# 41. Audit View

The Audit interface should expose task-level events.

Example:

```text
Audit

12:41 Task created
12:41 report.pdf ingested
12:42 OCR completed
12:43 SOP retrieved
12:44 Python calculation executed
12:44 Verification passed
12:45 DOCX generated
12:45 DOCX validated
12:45 Task completed
```

---

# 42. Audit Is Not Chat History

Chat history records:

```text
User ↔ Assistant messages
```

Audit history records:

```text
System actions
Tool calls
Retrieval
Model routing
Verification
Artifact creation
Security events
```

Both are useful but serve different purposes.

---

# 43. Model Visibility

The UI may expose which local model handled a step.

Example:

```text
Reasoning:
Qwen3-8B Q4_K_M

Task:
Document reasoning
```

For another step:

```text
Vision:
Local vision model
```

The user should not need to know implementation details unless desired.

---

# 44. Model Routing Visibility

For the SIH demonstration, provide an optional model-routing panel.

Example:

```text
Model Routing

Task: Code analysis
Selected: Coding Model
Reason: code-generation capability

Task: Document reasoning
Selected: Reasoning Model
Reason: instruction/reasoning capability
```

This directly demonstrates the model-agnostic architecture.

---

# 45. API Architecture

The UI must not directly communicate with internal tools or models.

Correct:

```text
Browser
   ↓
API Gateway
   ↓
Agent Host
   ↓
Internal services
```

Incorrect:

```text
Browser
 ├── LLM
 ├── Tools MCP
 ├── Knowledge DB
 └── Sandbox
```

---

# 46. API Gateway Responsibilities

The API layer should handle:

```text
Authentication
Authorization
Task creation
Task retrieval
File upload
Task events
Artifact metadata
Audit access
```

It should not contain agent reasoning logic.

---

# 47. Agent Host Boundary

The Agent Host owns:

```text
Planning
Model routing
Context assembly
Tool orchestration
Task state
Verification coordination
```

The API Gateway should invoke the Agent Host rather than implementing these responsibilities itself.

---

# 48. UI → API Flow

Creating a task:

```text
UI
 ↓
POST /tasks
 ↓
API Gateway
 ↓
Agent Host
 ↓
Task created
 ↓
task_id
```

The exact endpoint naming is implementation-specific.

---

# 49. File Upload Flow

```text
UI
 ↓
Upload
 ↓
API Gateway
 ↓
Task Workspace
 ↓
Document Processing
 ↓
Status events
 ↓
UI
```

The browser should not upload directly to an external cloud storage service.

---

# 50. Task Event Stream

Long-running tasks require progress updates.

The UI should receive events such as:

```text
TASK_CREATED
PLAN_UPDATED
RETRIEVAL_STARTED
RETRIEVAL_COMPLETED
TOOL_STARTED
TOOL_COMPLETED
VERIFICATION_STARTED
VERIFICATION_COMPLETED
ARTIFACT_CREATED
TASK_COMPLETED
TASK_FAILED
```

The transport may be:

```text
WebSocket
Server-Sent Events
polling
```

The implementation should choose the simplest reliable option.

---

# 51. Streaming Model Output

Where supported, model output may stream to the UI.

However, streaming should not bypass task state.

Conceptually:

```text
Model stream
 ↓
Agent Host
 ↓
UI
```

not:

```text
UI
 ↓
direct model
```

---

# 52. Reasoning Visibility

The UI should NOT expose hidden chain-of-thought.

Instead show safe execution summaries:

```text
Analyzing retrieved evidence
Running verification
Preparing document
```

The user needs operational transparency, not private internal reasoning traces.

---

# 53. Safe Agent Trace

A task trace may contain:

```text
Step
Purpose
Tool
Evidence
Result
Status
```

without exposing hidden chain-of-thought.

Example:

```text
Step 4
Purpose: Verify calculated thickness
Tool: Python
Result: 68.4%
Status: PASS
```

---

# 54. API Security

Every API request must be authenticated in a real deployment.

The prototype may use a simplified local authentication mechanism, but the architecture must leave a clear boundary for:

```text
Authentication
RBAC
Session management
```

---

# 55. RBAC Hooks

Roles may eventually include:

```text
USER
REVIEWER
ADMIN
AUDITOR
```

Example:

```text
USER:
Create tasks and view permitted artifacts.

REVIEWER:
Review/approve selected outputs.

ADMIN:
Manage models/tools/policies.

AUDITOR:
View audit records.
```

The prototype may implement only a subset.

---

# 56. Permission Model

Authorization should apply to:

```text
Tasks
Files
Knowledge
Tools
Models
Artifacts
Audit records
```

The UI should never be considered the enforcement layer.

---

# 57. Error Model

API errors should be structured.

Example:

```text
{
    "error_code": "TASK_NOT_FOUND",
    "message": "Task does not exist.",
    "request_id": "..."
}
```

Avoid returning raw internal stack traces to the user.

---

# 58. Request IDs

Important API requests should have a request identifier.

This allows:

```text
UI error
 ↓
request_id
 ↓
audit/log search
 ↓
diagnosis
```

---

# 59. Health Status

The UI should provide a system status area.

Example:

```text
System Status

Agent Host       ● Online
Model Gateway    ● Online
Knowledge        ● Online
Tools MCP        ● Online
Sandbox          ● Online
Artifact Engine  ● Online
Network Egress   ● Blocked
```

---

# 60. Health Status Must Be Real

The UI must obtain health information from actual services.

Do not hard-code:

```text
● Online
```

for demonstration purposes.

---

# 61. Resource Status

For the laptop prototype, optionally expose:

```text
GPU memory
System memory
CPU utilization
active model
```

This can help diagnose resource bottlenecks.

It also helps explain why the prototype intentionally uses bounded concurrency.

---

# 62. Model Loading State

Local models may take time to load.

The UI should show:

```text
Loading local reasoning model...
```

rather than appearing frozen.

Example:

```text
Model:
Qwen3-8B Q4_K_M

Status:
Loading
```

---

# 63. No External Dependency UI

If a required local service is unavailable:

```text
Knowledge Service unavailable
```

the system should explain the local dependency rather than silently attempting an external fallback.

---

# 64. No Cloud Fallback

The prototype MUST NOT silently do:

```text
Local model fails
 ↓
Cloud API
```

That would violate the sovereignty architecture.

Correct:

```text
Local model fails
 ↓
Task pauses/fails
 ↓
User informed
```

---

# 65. File Privacy

The UI should avoid unnecessarily displaying sensitive documents in logs or debug panels.

For previews, show only authorized content.

---

# 66. Document Preview

For PDFs and images, the prototype may provide a local preview.

The preview should remain served from the local system.

No external document viewer should be required.

---

# 67. Evidence Preview

Selecting:

```text
Inspection Report — Page 37
```

should ideally open the relevant page or extracted content.

This creates a direct chain:

```text
AI claim
 ↓
Evidence reference
 ↓
Source page
```

---

# 68. User Trust Model

The UI should communicate four levels:

```text
SOURCE
what the organization supplied

AI ANALYSIS
what the model inferred

TOOL RESULT
what deterministic/local tools computed

VERIFICATION
what the system independently checked
```

These should not be conflated.

---

# 69. Example End-to-End UI

User opens:

```text
New Task
```

Enters:

> Review inspection report and prepare approval note.

Uploads:

```text
inspection.pdf
```

The UI displays:

```text
Task created
```

Then:

```text
✓ Report ingested
✓ OCR completed
● Retrieving relevant evidence
○ Compare against SOP
○ Calculate values
○ Verify
○ Generate approval note
```

---

# 70. Evidence Stage

The UI displays:

```text
Relevant Evidence

Inspection Report — p.37
SOP-17 — §4.2
Inspection Manual — §7
```

The user can inspect them.

---

# 71. Tool Stage

The UI displays:

```text
Tools

✓ OCR
✓ Python calculation
● Verification
```

If Python was used:

```text
Sandbox:
ACTIVE

Network:
BLOCKED
```

---

# 72. Artifact Stage

The UI displays:

```text
Generated Artifact

Inspection_Approval_Note.docx

Status:
VERIFYING
```

Then:

```text
✓ VERIFIED
```

---

# 73. Final Task State

The final screen should summarize:

```text
Task Completed

Evidence used: 8
Tool calls: 6
Calculations verified: 2
Artifacts: 1
Verification: PASSED
External calls: 0
```

The exact values must come from the actual task execution.

---

# 74. Demonstration Mode

The prototype should support a presentation-friendly view.

The SIH demonstration should make these visible:

```text
1. Local model selected
2. Private document processed
3. Knowledge retrieved
4. Agent plan
5. Tool execution
6. Sandbox
7. Verification
8. Artifact generated
9. Audit trail
10. Network state
```

This is more compelling than showing only a chat response.

---

# 75. Demo Safety

Demo mode must not fake system behavior.

For example, do not display:

```text
External Calls: 0
```

unless actual network telemetry confirms it.

The demonstration should rely on real execution.

---

# 76. Minimal MVP UI

If development time becomes constrained, the minimum UI is:

```text
Task screen
 ├── User request
 ├── File upload
 ├── Agent status
 ├── Plan
 ├── Evidence
 ├── Tool activity
 ├── Verification
 └── Artifacts
```

Do not sacrifice these for cosmetic features.

---

# 77. Features Explicitly Deferred

The prototype does NOT require:

```text
Enterprise SSO
Complex multi-tenant UI
Mobile application
Advanced dashboards
Enterprise billing
Cloud deployment UI
Full admin console
Advanced collaboration
```

These can be future extensions.

---

# 78. API Principles

The API should remain:

```text
Local
Authenticated
Structured
Versionable
Observable
Model-independent
```

The API should not expose internal implementation details unnecessarily.

---

# 79. Versioning

The API should have a version boundary.

Example:

```text
/api/v1/
```

The exact path is implementation-specific.

Breaking API changes should not silently invalidate the frontend.

---

# 80. API Contract

The frontend and backend should communicate through explicit schemas.

Core objects:

```text
Task
TaskEvent
File
Evidence
ToolCall
Artifact
VerificationReport
SystemStatus
```

---

# 81. Task Object

Conceptually:

```text
Task {
    id
    title
    request
    status
    created_at
    updated_at
}
```

---

# 82. Task Event Object

Conceptually:

```text
TaskEvent {
    id
    task_id
    type
    timestamp
    status
    summary
}
```

---

# 83. Artifact Object

Conceptually:

```text
Artifact {
    id
    task_id
    name
    type
    status
    version
    hash
}
```

---

# 84. Evidence Object

Conceptually:

```text
Evidence {
    id
    task_id
    document_id
    page
    section
    excerpt
}
```

Sensitive content should be returned only when the requesting user is authorized to see it.

---

# 85. Verification Object

Conceptually:

```text
VerificationReport {
    artifact_id
    overall_status
    checks[]
}
```

---

# 86. System Status Object

Conceptually:

```text
SystemStatus {
    agent_host
    model_gateway
    knowledge
    tools
    sandbox
    artifact_engine
    network_security
}
```

---

# 87. Frontend State

The frontend should treat the backend as authoritative.

It should not invent:

```text
task status
tool success
verification status
network status
```

These values should originate from backend events/state.

---

# 88. Reconnection

If the browser disconnects during a long task:

```text
Browser disconnects
       ↓
Task continues server-side
       ↓
Browser reconnects
       ↓
Fetch current task state/events
```

The task must not depend on the browser remaining open.

This is another reason the Task object must be persistent.

---

# 89. Browser Refresh

Refreshing the page should not destroy task state.

The UI reconstructs:

```text
Task
+
current state
+
recent events
+
artifacts
```

from the backend.

---

# 90. Long-Running Tasks

The architecture should allow tasks to continue for longer than a single HTTP request.

Therefore:

```text
POST /task
```

should create/start a task rather than keep the HTTP connection open for the entire workflow.

---

# 91. Cancellation

Cancellation should propagate:

```text
UI
 ↓
API
 ↓
Agent Host
 ↓
Tool/Sandbox
```

where possible.

---

# 92. UI Security Invariants

The following are mandatory:

1. UI cannot bypass API authorization.
2. UI cannot directly invoke arbitrary tools.
3. UI cannot directly invoke arbitrary model endpoints.
4. UI cannot access unauthorized files.
5. UI cannot modify verification status.
6. UI cannot mark artifacts verified.
7. UI cannot disable security policies.
8. UI cannot claim network isolation without backend evidence.

---

# 93. Prototype Acceptance Test

A reviewer should be able to perform:

```text
1. Open Workbench.
2. Create task.
3. Upload confidential PDF.
4. Start task.
5. Observe plan.
6. Observe retrieval.
7. Inspect evidence.
8. Observe tool execution.
9. Observe sandbox status.
10. Observe verification.
11. Open generated DOCX.
12. Inspect audit trail.
13. Inspect network/security status.
```

All of this must happen locally.

---

# 94. Failure Acceptance Test

Force a controlled failure.

Example:

```text
Incorrect calculation
```

The UI should show:

```text
Verification Failed
```

Then:

```text
Agent correction
 ↓
Recalculation
 ↓
Verification
 ↓
PASS
```

This demonstrates that the system can recover rather than merely produce a happy-path demo.

---

# 95. Context-Limit Acceptance Test

Use a document significantly larger than the model context.

Example:

```text
100-page report
```

The UI should demonstrate:

```text
Document size > model context
```

while the task still succeeds through:

```text
retrieval
+
persistent state
+
iterative reasoning
```

This is a core architectural demonstration.

---

# 96. Sovereignty Acceptance Test

Disable external network access.

Then perform:

```text
Upload
 ↓
OCR
 ↓
Retrieval
 ↓
Reasoning
 ↓
Tool execution
 ↓
Artifact generation
 ↓
Verification
```

The task should continue working.

---

# 97. API Security Acceptance Test

Attempt to access:

```text
unauthorized file
```

Expected:

```text
ACCESS_DENIED
```

Attempt:

```text
arbitrary tool call
```

Expected:

```text
POLICY_BLOCKED
```

---

# 98. Final UI Architecture

```text
                         USER
                           │
                           ▼
                  ┌─────────────────┐
                  │ Sovereign UI    │
                  │                 │
                  │ Tasks           │
                  │ Files           │
                  │ Evidence        │
                  │ Tools           │
                  │ Verification    │
                  │ Artifacts       │
                  │ Audit           │
                  └────────┬────────┘
                           │
                         HTTPS
                           │
                           ▼
                  ┌─────────────────┐
                  │   API Gateway   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   Agent Host    │
                  └────────┬────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
       Model Gateway   Knowledge       Tools
            │             │              │
            ▼             ▼              ▼
        Local LLM       Local KB       Sandbox
                           │
                           ▼
                     Verification
                           │
                           ▼
                       Artifacts
```

---

# 99. Final Design Principle

The UI must answer the user's most important questions without requiring them to understand the implementation:

> **What is the agent doing?**

Plan and task status.

> **What information is it using?**

Evidence panel.

> **What actions did it take?**

Tool activity.

> **Did it verify the result?**

Verification panel.

> **What did it produce?**

Artifact panel.

> **Did anything leave the organization?**

Actual network/security telemetry.

> **Can I trace the result back to the source?**

Evidence and provenance.

That is the purpose of the Sovereign AI Workbench UI.

---

# 100. Definition of Done

The UI/API subsystem is complete when it can:

1. Create persistent tasks.
2. Upload task files.
3. Display task status.
4. Display agent execution progress.
5. Display the current plan.
6. Display retrieved evidence.
7. Display tool activity.
8. Display sandbox status.
9. Display verification results.
10. Display generated artifacts.
11. Allow artifact inspection/download through the local system.
12. Display audit events.
13. Display actual system health.
14. Display actual network security state.
15. Resume tasks after browser refresh/reconnection.
16. Handle waiting-for-user states.
17. Handle task cancellation.
18. Handle structured failures.
19. Expose model routing information where appropriate.
20. Maintain strict API boundaries.
21. Prevent direct UI access to internal tools/models.
22. Preserve authorization boundaries.
23. Demonstrate the complete agentic workflow.
24. Demonstrate the context-limit strategy.
25. Demonstrate the sovereign/no-external-call property without relying on UI claims alone.

---

# 101. Final Principle

The Sovereign AI Workbench should feel like:

> **a private AI employee's workspace**

rather than:

> **a private ChatGPT clone.**

The interface therefore centers around:

```text
TASK
 ↓
PLAN
 ↓
EVIDENCE
 ↓
ACTION
 ↓
VERIFICATION
 ↓
ARTIFACT
 ↓
AUDIT
```

not merely:

```text
CHAT
 ↓
ANSWER
```

**Status: FROZEN — BASELINE UI, API & USER WORKSPACE ARCHITECTURE**

```
```
