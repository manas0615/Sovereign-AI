# `08-tool-execution-and-sandbox.md`

````markdown
# Sovereign AI Workbench
## Tool Execution & Sandbox Specification

**Project:** Sovereign AI — SIH 2026 Prototype  
**Document:** Tool Execution & Sandbox  
**Document ID:** SAI-DOC-008  
**Status:** FROZEN — BASELINE TOOL SECURITY ARCHITECTURE  
**Version:** 1.0

**Depends On:**
- 01-project-charter.md
- 02-system-architecture.md
- 03-security-and-sovereignty.md
- 04-data-context-memory-architecture.md
- 05-model-gateway-and-routing.md
- 06-agent-host-and-orchestration.md
- 07-knowledge-retrieval-and-document-intelligence.md

---

# 1. Purpose

This document defines how the Sovereign AI Workbench exposes local capabilities to the agent while preventing the model from receiving uncontrolled access to the host machine.

The tool subsystem enables the agent to perform real work:

- Read files
- Write files
- Execute Python
- Perform calculations
- Read spreadsheets
- Modify spreadsheets
- Generate DOCX
- Generate PPTX
- Generate XLSX
- Inspect task workspace
- Run tests
- Validate generated artifacts

The central security principle is:

> **The model may request an action, but it never receives authority to perform that action directly.**

---

# 2. Why Tools Are Necessary

A chatbot can produce text.

An enterprise AI worker must be able to produce work.

For example:

```text
User:
"Calculate the inspection statistics and prepare an Excel report."

Chatbot:
"Here are the calculated values."

Agentic system:

Read source data
      ↓
Calculate
      ↓
Verify
      ↓
Create XLSX
      ↓
Validate XLSX
      ↓
Deliver artifact
````

Tools are therefore a fundamental part of the agentic architecture.

---

# 3. The Critical Security Problem

A local LLM is still an untrusted software component.

The following architecture is prohibited:

```text
LLM
 ↓
OS shell
 ↓
Host machine
```

The model must never be given unrestricted:

```text
PowerShell
CMD
Bash
filesystem
network
process creation
```

access.

---

# 4. Correct Architecture

The required architecture is:

```text
                    LOCAL MODEL
                         │
                         │ Tool Request
                         ▼
                  ┌──────────────┐
                  │  AGENT HOST  │
                  └──────┬───────┘
                         │
                  Validate Request
                         │
                         ▼
                  ┌──────────────┐
                  │ POLICY ENGINE│
                  └──────┬───────┘
                         │
                  Permission Check
                         │
                         ▼
                  ┌──────────────┐
                  │   TOOLS MCP  │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │   SANDBOX    │
                  └──────┬───────┘
                         │
                         ▼
                  Controlled Action
```

The model never bypasses these layers.

---

# 5. Tool Categories

Tools should be classified by capability and risk.

Recommended initial categories:

```text
READ
CALCULATE
WRITE
CODE_EXECUTION
ARTIFACT_GENERATION
VALIDATION
```

---

# 6. Prototype Tool Set

The initial MVP should provide:

```text
read_file
list_files
write_file
calculate
execute_python
read_excel
write_excel
create_docx
create_pptx
validate_artifact
```

The exact implementation may combine some capabilities internally.

---

# 7. Tool Interface

Every tool should have a structured interface.

Conceptually:

```text
Tool {
    name
    description
    input_schema
    output_schema
    risk_level
    permissions
}
```

The model should receive only the tool description and schema required for its current role.

---

# 8. Tool Request

A model-generated tool request should conceptually look like:

```text
ToolRequest {
    tool_name
    arguments
    purpose
}
```

Example:

```text
{
    "tool_name": "calculate",
    "arguments": {
        "expression": "1250 / 25"
    },
    "purpose": "Calculate average inspection value"
}
```

The exact implementation schema is not frozen here.

---

# 9. Tool Request Validation

Every request must pass:

```text
Model Request
     ↓
Schema Validation
     ↓
Policy Validation
     ↓
Permission Validation
     ↓
Resource Validation
     ↓
Execution
```

Invalid requests must never reach the tool implementation.

---

# 10. Schema Validation

Reject:

```text
Missing parameters
Unexpected parameters
Wrong parameter types
Invalid paths
Malformed expressions
Unsupported operations
```

Example:

```text
write_file(
    path = ../../Windows/System32/file
)
```

must be rejected before execution.

---

# 11. Path Security

File tools must never permit arbitrary filesystem traversal.

For example:

```text
../../secret.txt
C:\Users\OtherUser\
C:\Windows\
```

must not be accepted.

The agent should operate inside a controlled workspace.

---

# 12. Workspace Model

Each task should receive a controlled workspace.

Conceptually:

```text
workspace/
    task-123/
        input/
        working/
        output/
        logs/
```

The agent may access only the directories explicitly permitted for that task.

---

# 13. Workspace Isolation

The system should distinguish:

```text
INPUT
WORKING
OUTPUT
```

Example:

```text
input/
    inspection.pdf

working/
    extracted.txt
    calculations.py

output/
    Inspection_Approval_Note.docx
```

This makes task boundaries easier to enforce and audit.

---

# 14. Read File

`read_file` should:

* Accept only authorized workspace paths
* Validate file existence
* Validate file type
* Enforce size limits
* Return structured content where possible
* Record the operation

Example:

```text
Agent
 ↓
read_file("input/report.pdf")
 ↓
Tools MCP
 ↓
Document subsystem
```

---

# 15. List Files

`list_files` allows the agent to discover available task inputs.

It should return only authorized files.

Example:

```text
input/
    inspection.pdf
    equipment_data.xlsx
```

It must not expose unrelated host directories.

---

# 16. Write File

`write_file` must:

* Restrict output location
* Validate path
* Enforce size limits
* Prevent overwriting protected files
* Record provenance

The default should be:

> Write only inside the task workspace.

---

# 17. File Type Controls

Tools should know which file types they support.

Example:

```text
read_file:
    txt
    md
    csv

document reader:
    pdf
    docx

spreadsheet:
    xlsx
    csv
```

Unsupported types should fail explicitly.

---

# 18. Calculation Tool

Deterministic calculations should not unnecessarily rely on the LLM.

Example:

```text
Agent:
"Calculate average wall thickness."

       ↓

calculate

       ↓

Deterministic result

       ↓

Agent
```

The calculation result should be persisted as task evidence.

---

# 19. Calculator Security

A calculator should preferably use a restricted expression evaluator rather than arbitrary Python.

Allowed:

```text
+
-
*
/
%
()
basic mathematical functions
```

Avoid evaluating arbitrary code through a calculator interface.

---

# 20. Python Execution

Python execution is powerful and therefore high-risk.

It is required for:

```text
Data analysis
Calculations
Code generation/testing
File transformation
```

But it MUST execute in a sandbox.

---

# 21. Python Architecture

```text
Agent
 ↓
execute_python
 ↓
Policy
 ↓
Sandbox
 ↓
Python process
 ↓
stdout / stderr / files
 ↓
Agent Host
```

---

# 22. Python Sandbox

The sandbox should restrict:

```text
Filesystem
Network
Processes
Resources
Execution time
Memory
```

The exact mechanism may be:

```text
Docker container
```

or another isolated execution environment.

For the laptop prototype, Docker is the preferred practical boundary.

---

# 23. Network Restriction

Generated code must not be able to access the Internet by default.

The sandbox should operate with:

```text
network = disabled
```

This is important for the sovereign claim.

A Python program must not be able to silently execute:

```python
requests.get(...)
```

against an external service.

---

# 24. Host Filesystem Restriction

Generated Python must not receive arbitrary host filesystem access.

Instead:

```text
Sandbox
 ↓
Mounted task workspace
```

Only explicitly required directories should be mounted.

---

# 25. Resource Limits

Python execution should have bounded:

```text
CPU
RAM
disk
execution time
process count
```

This prevents:

```text
infinite loops
memory exhaustion
disk exhaustion
fork bombs
```

---

# 26. Execution Timeout

Every code execution should have a timeout.

Example:

```text
Maximum execution time:
configurable
```

If exceeded:

```text
PROCESS
 ↓
TIMEOUT
 ↓
TERMINATE
 ↓
CAPTURE RESULT
```

The exact default value should be configurable and tuned during implementation.

---

# 27. Output Limits

A generated program may produce enormous stdout/stderr.

Therefore output should be bounded.

Example:

```text
Maximum stdout
Maximum stderr
Maximum generated files
Maximum file size
```

Excessive output should be truncated safely and reported.

---

# 28. Generated Code Must Be Treated as Untrusted

Even though the LLM generated the code, the system must assume:

```text
Generated code = untrusted code
```

This is a mandatory security principle.

The code may contain:

* accidental destructive operations
* infinite loops
* package installation attempts
* network requests
* malicious instructions
* unexpected filesystem operations

The sandbox is therefore mandatory.

---

# 29. Package Installation

The prototype should NOT allow unrestricted:

```text
pip install
apt install
npm install
```

during task execution.

Dependencies should ideally be preinstalled in the sandbox image.

If dynamic dependencies are eventually supported, they require explicit policy.

---

# 30. Sandbox Image

The prototype should use a controlled execution environment containing only required dependencies.

Example:

```text
Python
pandas
numpy
openpyxl
matplotlib
pytest
python-docx
python-pptx
```

The exact package list should be finalized during implementation based on actual tool requirements.

---

# 31. Code Execution Result

The sandbox should return structured information.

Conceptually:

```text
ExecutionResult {
    status
    exit_code
    stdout
    stderr
    generated_files
    execution_time
}
```

Possible statuses:

```text
SUCCESS
FAILED
TIMEOUT
RESOURCE_LIMIT
POLICY_BLOCKED
```

---

# 32. Coding Agent Loop

The coding workflow should be:

```text
Requirement
    ↓
Plan
    ↓
Inspect workspace
    ↓
Generate code
    ↓
Write code
    ↓
Execute in sandbox
    ↓
Observe result
    ↓
Run tests
    ↓
Failure?
   /   \
 yes    no
  ↓      ↓
Fix    Verify
  ↓      ↓
Retry   Deliver
```

Retries must be bounded.

---

# 33. Test Execution

Generated code should be tested inside the same controlled environment.

Example:

```text
pytest
```

or a project-specific test command.

The agent receives:

```text
test result
+
stdout
+
stderr
```

and may make bounded corrections.

---

# 34. Test Verification

A successful process exit does not automatically mean correct code.

For example:

```text
exit_code = 0
```

does not prove:

```text
algorithm = correct
```

Therefore the agent should use actual test assertions wherever possible.

---

# 35. Artifact Generation

The workbench should expose controlled artifact generators.

Initial target:

```text
DOCX
XLSX
PPTX
PDF
```

The actual MVP may prioritize:

```text
DOCX
XLSX
PPTX
```

because these directly demonstrate enterprise work-product generation.

---

# 36. DOCX Generation

The agent should not manually construct binary DOCX files.

Instead:

```text
Agent
 ↓
Structured document specification
 ↓
DOCX generator
 ↓
.docx
 ↓
Validation
```

The generator should be deterministic wherever possible.

---

# 37. DOCX Validation

After generation:

```text
File exists
 ↓
DOCX opens
 ↓
Required headings exist
 ↓
Required content exists
 ↓
References exist
 ↓
Artifact valid
```

A generated file should not be considered complete merely because the file was created.

---

# 38. XLSX Generation

The spreadsheet tool should support:

```text
Create workbook
Create worksheet
Write cells
Write tables
Apply formulas
Read workbook
Validate formulas/results
```

Where possible, calculations should use spreadsheet formulas or deterministic computation rather than relying solely on model arithmetic.

---

# 39. Spreadsheet Safety

Spreadsheet formulas may contain unexpected behavior.

The prototype should avoid generating formulas that intentionally invoke:

```text
external links
external data connections
macros
```

unless explicitly supported and authorized.

---

# 40. PPTX Generation

The presentation tool should support:

```text
Create presentation
Create slides
Add text
Add tables
Add charts where supported
Add images
```

Generated presentations should be validated after creation.

---

# 41. Artifact Workspace

Generated artifacts should be stored in:

```text
task/output/
```

rather than arbitrary host directories.

Example:

```text
task-001/
    input/
    working/
    output/
        Inspection_Approval_Note.docx
        Verification_Report.json
```

---

# 42. Artifact Naming

Artifact names should be:

* deterministic where possible
* human-readable
* task-associated
* safe for filesystem use

Avoid model-generated paths such as:

```text
../../important_file.docx
```

---

# 43. Artifact Provenance

Each generated artifact should have provenance.

Conceptually:

```text
artifact_id
task_id
created_at
generator
source_documents
evidence_ids
verification_status
```

This allows:

```text
Artifact
 ↓
Task
 ↓
Evidence
 ↓
Source
```

traceability.

---

# 44. Artifact Verification

Every important artifact should pass validation.

Example:

```text
Generated DOCX
      ↓
File validation
      ↓
Content validation
      ↓
Evidence validation
      ↓
Final artifact
```

---

# 45. Artifact Integrity

Generated files may also receive hashes.

Example:

```text
SHA-256(artifact)
```

This helps audit the exact file that was delivered.

---

# 46. Tool Permissions

Tools should have explicit permissions.

Example:

```text
Tool                    Permission
------------------------------------------------
read_file               READ
list_files              READ
calculate               CALCULATE
execute_python          EXECUTE
write_file              WRITE
create_docx             WRITE
create_xlsx             WRITE
create_pptx             WRITE
```

A future enterprise deployment can map these to RBAC policies.

---

# 47. Risk Levels

Example:

```text
LOW
MEDIUM
HIGH
```

Illustrative classification:

```text
read_file       LOW
calculate       LOW
write_file      MEDIUM
execute_python  HIGH
artifact_write  MEDIUM
```

The exact policy is configurable.

---

# 48. Human Confirmation

High-risk actions may require confirmation.

Example:

```text
Agent:
"Python execution is required to modify the workbook.
Proceed?"

User:
Yes
```

For the prototype, this mechanism should exist even if most safe demo operations are automatically permitted.

---

# 49. No External Side Effects

The prototype tools should not perform:

```text
email sending
external API calls
Internet uploads
external database modifications
system configuration changes
```

unless explicitly added later under controlled policy.

The initial prototype is intentionally local.

---

# 50. MCP Tool Exposure

Tools should be exposed through the Tools MCP interface.

Conceptually:

```text
Agent Host
    │
    ▼
Tools MCP
    │
    ├── read_file
    ├── write_file
    ├── execute_python
    ├── calculate
    ├── read_excel
    ├── write_excel
    ├── create_docx
    ├── create_pptx
    └── validate_artifact
```

MCP is the interface.

The underlying implementation may change.

---

# 51. Tool Discovery

The Agent Host should be able to discover available tools.

However, the model should not necessarily receive every tool on every request.

Instead:

```text
Task
 ↓
Required capabilities
 ↓
Relevant tools
 ↓
Model
```

This reduces prompt size and tool confusion.

---

# 52. Tool Descriptions

Tool descriptions should be concise and precise.

Bad:

```text
"This tool does many things with files."
```

Good:

```text
"Read a UTF-8 text file from the current task workspace."
```

Precise tool schemas improve reliability.

---

# 53. Tool Argument Normalization

Before execution, arguments should be normalized.

Examples:

```text
relative path
number formats
encoding
worksheet name
timeout
```

The tool implementation must not blindly trust model-generated values.

---

# 54. Tool Output Normalization

All tools should return predictable structures.

Example:

```text
{
    "status": "success",
    "result": ...,
    "artifacts": [...],
    "errors": [...]
}
```

This makes orchestration easier.

---

# 55. Tool Errors

Errors should be structured.

Example:

```text
{
    "status": "error",
    "error_type": "FILE_NOT_FOUND",
    "message": "Input file does not exist."
}
```

The agent can then decide whether to:

```text
retry
inspect files
ask user
fail
```

---

# 56. Tool Logging

Every tool call should record:

```text
task_id
step_id
tool_name
arguments
start_time
end_time
status
result summary
error
```

Sensitive values should be redacted from logs where appropriate.

---

# 57. Sensitive Tool Arguments

Do not unnecessarily duplicate sensitive document contents into logs.

For example, instead of logging:

```text
entire confidential document
```

log:

```text
document_id
filename
hash
operation
```

This reduces unnecessary sensitive-data duplication.

---

# 58. Tool Audit Trail

The system should be able to answer:

> "What did the agent actually do?"

Example:

```text
09:31 Task created
09:31 report.pdf read
09:32 OCR completed
09:33 SOP retrieved
09:34 Python calculation executed
09:34 verification passed
09:35 DOCX created
09:35 artifact validated
```

This is valuable for the SIH demonstration.

---

# 59. Tool Sandboxing vs Application Isolation

These are different layers.

```text
Application isolation:
protects the application architecture

Sandbox:
protects the host from generated code
```

Both should exist.

---

# 60. Docker's Role

For the laptop prototype, Docker is useful for:

```text
Python execution sandbox
Tool service isolation
Dependency isolation
Resource limits
Network isolation
```

It should not be assumed that:

> "Docker automatically makes everything secure."

Container configuration still matters.

---

# 61. Docker Network Policy

For the code sandbox:

```text
Network disabled by default.
```

The prototype should demonstrate that generated code cannot simply make Internet requests.

---

# 62. Docker Filesystem Policy

Mount only:

```text
task/input
task/working
task/output
```

where required.

Do not mount:

```text
C:\
Windows directories
user profile
Docker socket
SSH keys
browser credentials
```

The Docker socket MUST NOT be exposed to generated code.

---

# 63. Docker Privilege Policy

The sandbox should not run with unnecessary privileges.

Avoid:

```text
--privileged
```

unless there is an extraordinary and explicitly justified reason.

The prototype should follow least privilege.

---

# 64. Resource Policy

Docker execution should have configurable:

```text
memory limit
CPU limit
process limit
timeout
disk/output limits
```

The laptop's constrained RAM makes this especially important.

---

# 65. Tool Concurrency

The prototype should avoid unnecessary simultaneous tool execution.

For example:

```text
10 Python jobs
```

could overwhelm a 16 GB machine.

Default behavior should favor bounded sequential execution.

Parallelism can be added later.

---

# 66. Tool Queue

If concurrent requests occur:

```text
Agent
 ↓
Tool Queue
 ↓
Controlled execution
```

This prevents resource exhaustion.

---

# 67. Model + Tool Interaction

The model should not receive massive tool outputs.

Example:

Bad:

```text
100 MB CSV
 ↓
LLM context
```

Better:

```text
CSV
 ↓
Python analysis
 ↓
Statistics
 ↓
Small structured result
 ↓
LLM
```

This principle is essential for the prototype's 8K context.

---

# 68. Tool-Assisted Context Compression

Tools should perform computation before the result reaches the model.

Example:

```text
Large spreadsheet
 ↓
Python
 ↓
"Mean=..."
"Max=..."
"5 anomalous rows"
 ↓
LLM
```

This preserves context capacity.

---

# 69. Calculation Evidence

When a tool produces a result, retain:

```text
input references
calculation method
output
tool version
timestamp
```

This makes calculations auditable.

---

# 70. Example: Inspection Calculation

```text
Agent:
"Calculate remaining wall-thickness percentage."

 ↓

Python tool:
reads authorized input

 ↓

Calculation:
remaining = measured / original * 100

 ↓

Result:
68.4%

 ↓

Verifier:
independent calculation

 ↓

PASS
```

The final approval note can reference the verified calculation.

---

# 71. Example: Excel Workflow

```text
User:
"Analyze this inspection spreadsheet."

 ↓

read_excel

 ↓

Python:
calculate statistics

 ↓

Python:
identify anomalies

 ↓

Verifier:
check calculations

 ↓

write_excel

 ↓

validate_artifact

 ↓

deliver
```

The full spreadsheet does not need to enter the model context.

---

# 72. Example: DOCX Workflow

```text
Evidence
 ↓
Agent
 ↓
Structured document content
 ↓
create_docx
 ↓
validate_artifact
 ↓
output/approval_note.docx
```

---

# 73. Example: Coding Workflow

```text
User requirement
 ↓
Agent
 ↓
write_file
 ↓
execute_python
 ↓
pytest
 ↓
failure
 ↓
Agent
 ↓
write_file
 ↓
execute_python
 ↓
PASS
```

This is one of the strongest demonstrations of actual agentic behavior.

---

# 74. Preventing Infinite Tool Loops

The Agent Host must track:

```text
tool_call_count
step_retry_count
same_request_count
```

Example:

```text
execute_python
 ↓
failure
 ↓
execute_python
 ↓
failure
 ↓
execute_python
 ↓
failure
```

must eventually stop.

---

# 75. Tool Call Idempotency

Where possible, tools should behave predictably when retried.

For example:

```text
create_docx(task_id, artifact_id)
```

should not create unlimited copies when called twice.

---

# 76. Transaction Boundaries

For multi-operation workflows:

```text
Generate artifact
 ↓
Validate
```

If validation fails, the artifact should remain marked:

```text
INVALID
```

rather than silently being presented as final.

---

# 77. Partial Tool Results

If a tool partially succeeds:

```text
Excel:
80% processed
20% failed
```

the system should return:

```text
PARTIAL_SUCCESS
```

rather than:

```text
SUCCESS
```

---

# 78. Tool Result Trust

Tool results are stronger than model arithmetic for deterministic operations, but they are still not automatically authoritative.

The Agent Host should verify:

```text
Was the correct input used?
Was the correct tool called?
Was the execution successful?
```

---

# 79. Artifact Validation as a Tool

`validate_artifact` should be available to the Agent Host.

Example:

```text
create_docx
      ↓
validate_artifact
      ↓
PASS
```

This allows the completion contract to be machine-checkable.

---

# 80. Tool Security Invariants

The following are mandatory.

## Invariant 1

The model never receives arbitrary host shell access.

## Invariant 2

Every tool call passes schema validation.

## Invariant 3

Every tool call passes policy validation.

## Invariant 4

File paths are workspace-restricted.

## Invariant 5

Generated code runs in a sandbox.

## Invariant 6

Generated code has no network access by default.

## Invariant 7

Generated code has bounded resources.

## Invariant 8

Tool calls are logged.

## Invariant 9

Sensitive data is not unnecessarily duplicated in logs.

## Invariant 10

Tool loops are bounded.

## Invariant 11

Artifacts are validated before completion.

## Invariant 12

Tool failures are explicit.

## Invariant 13

The model cannot grant itself permissions.

## Invariant 14

The sandbox cannot access the Docker socket or arbitrary host filesystem.

---

# 81. Prototype Implementation Priority

### P0 — MUST HAVE

```text
Tool registry
Tool schemas
read_file
write_file
calculate
execute_python
Task workspace
Docker sandbox
Network-disabled execution
Execution timeout
Resource limits
Tool logging
```

### P1 — SHOULD HAVE

```text
read_excel
write_excel
create_docx
validate_docx
create_pptx
validate_pptx
Artifact provenance
Human confirmation
```

### P2 — FUTURE

```text
Advanced spreadsheet agent
PDF generation
Browser-like local automation
Enterprise application tools
SAP tools
PLM tools
EDMS tools
```

---

# 82. Laptop Prototype Strategy

The laptop has:

```text
16 GB system RAM
Quadro T1000
limited VRAM
```

Therefore tool execution should remain lightweight.

Heavy processing should be:

```text
deterministic
streamed
bounded
```

rather than loading entire datasets into the LLM.

---

# 83. Why This Helps the 8K Context Problem

Suppose the user gives a 50,000-row spreadsheet.

Do NOT:

```text
50,000 rows
 ↓
LLM
```

Instead:

```text
Spreadsheet
 ↓
Python
 ↓
statistics/anomalies/filtered rows
 ↓
small structured result
 ↓
LLM
```

The same principle applies to:

```text
PDFs
CSV files
Excel
logs
large codebases
```

---

# 84. Agent Tool Selection

The Agent Host should decide:

```text
Can this be done deterministically?
```

If yes:

```text
Use tool.
```

If reasoning is required:

```text
Use model.
```

If both are required:

```text
Model
 ↓
Tool
 ↓
Model
```

This minimizes unnecessary LLM computation.

---

# 85. Tool Use Principle

> **Use the model for judgment; use deterministic tools for deterministic work.**

Examples:

```text
Summarization → Model
Classification → Model
Arithmetic → Calculator/Python
Sorting → Python
File creation → Artifact engine
Testing → Sandbox
Source retrieval → Knowledge system
```

---

# 86. End-to-End Example

User:

> "Review the inspection report and generate an approval note."

Tool execution sequence:

```text
1. read_file(report.pdf)

2. document processing / OCR

3. knowledge retrieval

4. reasoning

5. calculate(...)

6. verify calculation

7. create_docx(...)

8. validate_artifact(...)

9. persist final artifact

10. complete task
```

Every operation is controlled and auditable.

---

# 87. Definition of Done

The Tool Execution subsystem is complete when it can:

1. Register tools.
2. Expose structured schemas.
3. Validate model tool requests.
4. Restrict file access to task workspaces.
5. Read authorized files.
6. Write authorized files.
7. Perform deterministic calculations.
8. Execute Python inside Docker.
9. Disable sandbox network access.
10. Enforce execution timeouts.
11. Enforce resource limits.
12. Capture stdout/stderr.
13. Run generated tests.
14. Generate DOCX artifacts.
15. Generate XLSX artifacts.
16. Generate PPTX artifacts.
17. Validate generated artifacts.
18. Record tool execution logs.
19. Preserve artifact provenance.
20. Prevent arbitrary host command execution.
21. Prevent arbitrary filesystem access.
22. Prevent unrestricted network access.
23. Bound retries and execution loops.
24. Return structured failures.
25. Integrate cleanly with the Agent Host through the tool interface.

---

# 88. Final Architecture

```text
                         LOCAL LLM
                            │
                            │
                     Structured Request
                            │
                            ▼
                     ┌─────────────┐
                     │ AGENT HOST  │
                     └──────┬──────┘
                            │
                       TOOL REQUEST
                            │
                            ▼
                     ┌─────────────┐
                     │    POLICY   │
                     └──────┬──────┘
                            │
                       PERMISSION
                            │
                            ▼
                     ┌─────────────┐
                     │  TOOLS MCP  │
                     └──────┬──────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
          File Tools    Calculator     Sandbox
                                            │
                                      ┌─────┴─────┐
                                      │   Python  │
                                      │   Tests   │
                                      │  Analysis │
                                      └─────┬─────┘
                                            │
                                            ▼
                                      Tool Result
                                            │
                                            ▼
                                       AGENT HOST
                                            │
                                            ▼
                                      Verification
                                            │
                                            ▼
                                         State
                                            │
                                            ▼
                                        Artifact
```

---

# 89. Final Principle

The purpose of the tool layer is not merely to give the LLM more capabilities.

It is to give the **agent controlled, auditable capabilities**.

The architectural rule is:

> **The model proposes. The Agent Host authorizes. The tool executes. The sandbox contains. The verifier checks. The audit layer records.**

This separation is mandatory for the Sovereign AI Workbench.

**Status: FROZEN — BASELINE TOOL EXECUTION & SANDBOX ARCHITECTURE**

```
```
