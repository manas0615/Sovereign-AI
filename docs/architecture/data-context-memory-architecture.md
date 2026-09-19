Next is **`04-data-context-memory-architecture.md`**.

This is one of the most important documents for our prototype because it formally solves the exact problem we were just testing with the **8K-context Qwen3-8B**: a 100-page document, persistent task state, retrieval, evidence, memory, and bounded model prompts.

````markdown
# Sovereign AI Workbench
## Data, Context, Memory & Knowledge Architecture Specification

**Project:** Sovereign AI — SIH 2026 Prototype  
**Document:** Data, Context, Memory & Knowledge Architecture  
**Document ID:** SAI-DOC-004  
**Status:** FROZEN — BASELINE CONTEXT ARCHITECTURE  
**Version:** 1.0  
**Depends On:** `01-project-charter.md`, `02-system-architecture.md`, `03-security-and-sovereignty.md`

---

# 1. Purpose

This document defines how the Sovereign AI Workbench manages information that is too large, persistent, sensitive, or structurally unsuitable to place directly into an LLM's working context.

It defines the boundaries between:

- Model context
- Conversation history
- Persistent task state
- Persistent memory
- Local organizational knowledge
- Document storage
- Retrieval
- Evidence
- Context construction
- Context budgeting
- Provenance

The central architectural principle is:

> **The model context is a bounded working space, not the system's memory or knowledge store.**

The system MUST NOT depend on placing an entire enterprise document, conversation, or task history into every model invocation.

---

# 2. The Fundamental Problem

Open-weight models running locally still have finite context windows.

For example, the prototype may use an approximately 8K-token working context.

Therefore:

```text
100-page document
        ↓
cannot be placed entirely
into one 8K-token prompt
````

The system must instead use:

```text
Large information
      ↓
Persistent local storage
      ↓
Index / structured state
      ↓
Retrieval
      ↓
Relevant evidence
      ↓
Context construction
      ↓
Bounded model invocation
```

This architecture is mandatory.

---

# 3. Three Core Concepts

The system MUST clearly distinguish:

## 3.1 Model Context

Model context is the information supplied to one model invocation.

It is:

* Bounded
* Temporary
* Task-specific
* Consumed by inference
* Limited by the model/runtime configuration

Conceptually:

```text
Current Goal
+
Relevant Instructions
+
Relevant Evidence
+
Relevant State
+
Current Tool Results
+
Current Plan Step
        ↓
     CONTEXT
        ↓
      MODEL
```

The context is the model's **working desk**.

It is not the organization's database.

---

# 4. Persistent Task State

Persistent task state represents the structured state of an ongoing task.

It may contain:

```text
Task ID
Goal
Plan
Current Step
Completed Steps
Findings
Unresolved Questions
Evidence References
Tool Results
Verification Results
Artifact References
Errors
Status
```

Example:

```text
Task:
Review inspection report and prepare approval note

State:
- 18 findings extracted
- 5 critical findings
- 3 unresolved questions
- SOP-17 retrieved
- Calculation X verified
- Draft artifact created
- Finding #7 requires additional evidence
```

The complete state does NOT need to be placed into every model invocation.

The Context Manager selects the relevant subset.

---

# 5. Persistent Memory

Persistent memory contains information intended to remain useful beyond the current task or session.

Examples may include:

```text
User preferences
Workflow preferences
Repeated organizational conventions
Previously established task conventions
Approved reusable instructions
```

Memory MUST NOT automatically become a dumping ground for every conversation.

Memory should have explicit:

* Scope
* Owner
* Source
* Classification
* Timestamp
* Provenance
* Lifecycle

---

# 6. Local Knowledge Base

The local knowledge base contains authoritative or reference organizational information.

Examples:

```text
SOPs
Manuals
Policies
Engineering standards
Inspection reports
Historical documents
Correspondence
Drawings
Scanned documents
```

The knowledge base differs fundamentally from memory.

Knowledge represents:

> **Information the organization has.**

Memory represents:

> **Information the system intentionally retains for future interaction/task continuity.**

---

# 7. Document Storage

Original documents must remain available independently of:

* LLM context
* Embeddings
* Summaries
* Memory
* Extracted findings

The original document is the authoritative source artifact unless another authoritative source explicitly supersedes it.

Conceptually:

```text
Original Document
       │
       ├──► Parsed Representation
       ├──► OCR Representation
       ├──► Chunks
       ├──► Embeddings
       ├──► Metadata
       └──► Evidence References
```

Derived representations must not replace the original.

---

# 8. The Information Hierarchy

The architecture should be understood as:

```text
                    ORIGINAL DATA
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Documents       Structured      Images
                       Data
          │
          ▼
       Processing
          │
    ┌─────┼──────┐
    ▼     ▼      ▼
  OCR   Parser  Metadata
    │     │      │
    └─────┼──────┘
          ▼
      Knowledge Layer
          │
     ┌────┴─────┐
     ▼          ▼
   Index      Evidence
     │          │
     └────┬─────┘
          ▼
    Retrieval Layer
          │
          ▼
    Context Manager
          │
          ▼
      Model Context
          │
          ▼
        Model
```

This hierarchy prevents the LLM from becoming the storage system.

---

# 9. Canonical Context Architecture

Every model invocation should be treated as a separate bounded computation.

Conceptually:

```text
                    Persistent World
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
 Knowledge           Task State         Memory
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                  Context Manager
                         │
                  Context Budget
                         │
                         ▼
                  Current Context
                         │
                         ▼
                       Model
                         │
                         ▼
                     Result
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        Task State Update       Evidence / Audit
```

---

# 10. Context Is Not Persistent Memory

The following distinction is mandatory:

```text
Model Context
    ≠
Persistent Memory
    ≠
Knowledge Base
    ≠
Task State
```

They may contain overlapping information, but they serve different purposes.

---

# 11. Context Lifetime

A model context exists for the current inference operation.

For example:

```text
Invocation 1
    Context A
    ↓
    Model
    ↓
    Result A

Invocation 2
    Context B
    ↓
    Model
    ↓
    Result B
```

Context B should be constructed from persistent state and relevant evidence rather than automatically replaying the entire contents of Context A.

---

# 12. Context Window

The configured model context represents a hard resource boundary.

For a prototype configuration such as:

```text
Context:
8192 tokens
```

the system must account for:

```text
System instructions
+
Agent instructions
+
Task information
+
Evidence
+
Tool results
+
Output reservation
```

Therefore:

> **8192 tokens are not necessarily available entirely for retrieved documents.**

The Context Manager must reserve space for generation and required control information.

---

# 13. Context Budget

The Context Manager should maintain an explicit budget.

Conceptually:

```text
TOTAL CONTEXT
│
├── System / Policy
│
├── Agent State
│
├── Current Task
│
├── Retrieved Evidence
│
├── Tool Results
│
└── Output Reservation
```

For example, the exact values may be configured dynamically.

The system MUST NOT blindly fill the entire context window with retrieval results.

---

# 14. Dynamic Context Construction

The Context Manager should construct each request according to the current task step.

Example:

```text
Task:
Prepare approval note

Current Step:
Evaluate corrosion finding #7

Required context:

System policy
+
Task objective
+
Finding #7
+
Relevant inspection pages
+
Relevant SOP section
+
Previous verification result
```

There is no reason to provide:

* The entire 100-page report
* All previous tool results
* All historical conversation
* All organizational memory

unless they are specifically relevant.

---

# 15. Context Priority

When context is constrained, information should be prioritized.

Recommended priority:

```text
1. Safety / policy instructions
2. Current task objective
3. Current plan step
4. Required evidence
5. Relevant tool observations
6. Relevant persistent task state
7. Relevant memory
8. Optional conversational history
```

Low-priority information should be removed before critical evidence.

---

# 16. Context Compaction

When task state grows too large, the system should compact it.

Example:

```text
Large execution history
        ↓
State extraction
        ↓
Structured summary
        ↓
Persistent task state
        ↓
Relevant subset retrieved
        ↓
New model context
```

The original evidence references must remain available.

Compaction must not destroy provenance.

---

# 17. Never Use Summary as the Only Source of Truth

A summary is a derived representation.

The system MUST retain references to the underlying evidence.

Incorrect:

```text
100-page report
   ↓
summary
   ↓
delete report
```

Preferred:

```text
100-page report
   ↓
summary
   +
source references
   +
original document
```

If a summary is later challenged, the system should be able to retrieve the underlying evidence.

---

# 18. Document Ingestion Pipeline

Documents entering the system should follow:

```text
Document
   ↓
Identification
   ↓
Classification
   ↓
Parsing
   ↓
OCR if required
   ↓
Structure extraction
   ↓
Metadata extraction
   ↓
Chunking
   ↓
Indexing
   ↓
Ready for retrieval
```

The ingestion pipeline is separate from the reasoning loop.

---

# 19. Text Document Processing

For machine-readable text:

```text
Document
   ↓
Parser
   ↓
Sections
   ↓
Paragraphs / Tables
   ↓
Semantic chunks
   ↓
Metadata
   ↓
Index
```

Chunk boundaries should preferably respect document structure.

The system should avoid arbitrary fixed-size splitting when structural boundaries are available.

---

# 20. Scanned Document Processing

For scanned PDFs:

```text
Scanned PDF
    ↓
Page extraction
    ↓
OCR / Vision
    ↓
Text + layout information
    ↓
Page / section metadata
    ↓
Chunks
    ↓
Index
```

The original page must remain associated with extracted text.

Evidence should retain:

```text
Document ID
Page
Region where available
Extracted text
```

---

# 21. Tables

Tables require special handling.

A table should not automatically be treated as ordinary paragraph text.

The system should preserve:

* Table identity
* Row/column structure where possible
* Page
* Headers
* Cell relationships

When necessary, tables should be converted into structured representations before reasoning.

---

# 22. Images and Drawings

Images may require:

```text
Image
 ↓
Local vision model
 ↓
Description / structured observations
 ↓
Evidence
```

The system should preserve the original image reference.

For engineering drawings, extracted observations should be treated as evidence rather than automatically assumed to be authoritative engineering facts.

Where visual interpretation is uncertain, the system should record uncertainty.

---

# 23. Chunking Strategy

Chunking must be designed for retrieval and evidence preservation.

A chunk should ideally contain:

```text
Chunk ID
Document ID
Section
Page
Content
Metadata
Classification
Source location
```

Chunks should not become detached from their source.

---

# 24. Chunk Size

There is no universal chunk size.

The implementation should choose chunk sizes based on:

* Document structure
* Retrieval precision
* Model context
* Embedding model behavior
* Evidence requirements

The chunking system must remain configurable.

The prototype should avoid assuming that:

> "One fixed number of tokens works for every document."

---

# 25. Chunk Overlap

Overlap may be used where necessary to preserve context between adjacent chunks.

However, excessive overlap wastes storage and retrieval context.

The implementation should measure retrieval quality rather than blindly maximizing overlap.

---

# 26. Metadata

Every indexed knowledge unit should retain metadata where available.

Recommended fields:

```text
document_id
document_version
page
section
title
source
classification
owner
timestamp
chunk_id
parent_document
```

Additional metadata may be added by the implementation.

---

# 27. Retrieval Architecture

Retrieval should be treated as a first-class subsystem.

Canonical flow:

```text
Task
 ↓
Search intent
 ↓
Retriever
 ├── Keyword search
 ├── Semantic search
 └── Metadata filtering
 ↓
Candidate evidence
 ↓
Ranking / reranking
 ↓
Permission filtering
 ↓
Evidence selection
 ↓
Context Manager
```

The exact retrieval technologies are implementation decisions.

---

# 28. Hybrid Retrieval

The prototype should support a hybrid retrieval strategy where practical:

```text
                    Query
                      │
            ┌─────────┴─────────┐
            ▼                   ▼
      Keyword Search       Semantic Search
            │                   │
            └─────────┬─────────┘
                      ▼
                   Ranking
                      │
                      ▼
                  Evidence
```

Keyword retrieval is useful for:

* Equipment IDs
* Part numbers
* SOP names
* Section numbers
* Exact terminology

Semantic retrieval is useful for:

* Conceptual questions
* Paraphrased requirements
* Similar findings

---

# 29. Retrieval Is Not Generation

The retrieval system provides evidence.

It does not decide the final answer.

```text
Retriever
   ↓
Evidence
   ↓
Model
   ↓
Reasoning
```

The model must distinguish between:

* Retrieved facts
* Inferences
* Assumptions
* Unknowns

---

# 30. Evidence Objects

Retrieved information should be represented internally as evidence objects.

Conceptually:

```text
Evidence {
    evidence_id
    document_id
    source_location
    content
    metadata
    retrieval_score
    permission_status
}
```

The exact implementation may differ.

Evidence IDs should be stable enough to support provenance.

---

# 31. Evidence Selection

The Context Manager should not blindly pass every retrieved result to the model.

Instead:

```text
Candidate Evidence
       ↓
Relevance
       +
Authority
       +
Permission
       +
Task requirement
       +
Context cost
       ↓
Selected Evidence
```

This is critical for small-context models.

---

# 32. Evidence Grounding

Generated conclusions should preferably reference evidence.

Example:

```text
Finding:
Valve leakage detected.

Evidence:
Inspection Report
Page 14
Finding ID IR-14-03
```

For a business deliverable:

```text
Claim
 ↓
Evidence reference
 ↓
Source document
 ↓
Location
```

---

# 33. Evidence Sufficiency

The system should be able to represent:

```text
SUFFICIENT
INSUFFICIENT
CONFLICTING
UNCERTAIN
NOT_FOUND
```

If evidence is insufficient, the model should not be forced to fabricate an answer.

The Agent Host may:

```text
Retrieve more evidence
OR
Ask a clarification
OR
Mark unresolved
```

---

# 34. Conflicting Evidence

The knowledge system may contain contradictory documents.

Example:

```text
SOP v1
    says X

SOP v2
    says Y
```

The system should preserve:

* Source
* Version
* Timestamp
* Authority metadata

The model should not silently merge conflicting claims.

When conflict cannot be resolved, it should be surfaced.

---

# 35. Persistent Task State Model

A task state should conceptually contain:

```text
TaskState
│
├── task_id
├── goal
├── status
├── plan
├── current_step
│
├── findings[]
│
├── evidence_refs[]
│
├── unresolved_questions[]
│
├── tool_results[]
│
├── verification_results[]
│
├── artifact_refs[]
│
├── errors[]
│
└── timestamps
```

This structure is intentionally independent of the LLM context.

---

# 36. State Transition

The Agent Host updates state after meaningful operations.

Example:

```text
Plan Step
   ↓
Retrieve
   ↓
Evidence
   ↓
Model reasoning
   ↓
Tool call
   ↓
Tool result
   ↓
Verification
   ↓
State update
```

The next model invocation reads the updated state.

---

# 37. The Key Context-Management Pattern

The following pattern is the primary solution to the prototype's 8K context constraint:

```text
                LARGE TASK
                    │
                    ▼
             Persistent State
                    │
          ┌─────────┼──────────┐
          ▼         ▼          ▼
       Findings   Evidence   Questions
          │         │          │
          └─────────┼──────────┘
                    ▼
              Current Step
                    │
                    ▼
             Context Manager
                    │
              Token Budget
                    │
                    ▼
              Small Context
                    │
                    ▼
                  MODEL
                    │
                    ▼
                 Result
                    │
                    ▼
              Update State
                    │
                    └──────────────► next step
```

This loop may continue for dozens or hundreds of model invocations without requiring the entire task history to be replayed.

---

# 38. Example: 100-Page Inspection Report

Suppose a user provides:

> "Review this 100-page inspection report and prepare an approval note."

The system should NOT do:

```text
100 pages
   ↓
single prompt
   ↓
8K model
```

Instead:

```text
100-page report
       ↓
Local ingestion
       ↓
OCR / parsing
       ↓
Structured chunks
       ↓
Local index
       ↓
Agent creates plan
       ↓
Retrieve relevant sections
       ↓
Analyze bounded evidence
       ↓
Persist findings
       ↓
Retrieve next required evidence
       ↓
Analyze
       ↓
Persist findings
       ↓
Verification
       ↓
Generate approval note
```

---

# 39. Example: Initial Invocation

The first model invocation may receive:

```text
SYSTEM POLICY

TASK:
Review the inspection report and prepare an approval note.

CURRENT PLAN:
1. Identify major findings.
2. Determine severity.
3. Compare findings against applicable SOP.
4. Perform required calculations.
5. Verify.
6. Draft approval note.

AVAILABLE DOCUMENT:
Inspection_Report_2026.pdf

CURRENT STATE:
No findings extracted yet.

RELEVANT EVIDENCE:
Pages 1–5.
```

The model does not receive all 100 pages.

---

# 40. Example: Persistent State After Processing

After several iterations:

```text
Task State:

Findings:
F1 — corrosion detected — page 14
F2 — leakage detected — page 21
F3 — insulation damage — page 37

Critical:
F1, F2

SOP:
SOP-17 section 4.2 retrieved

Verification:
F1 calculation verified

Unresolved:
Whether F2 requires immediate shutdown

Evidence:
E14, E21, E37, E_SOP_4_2
```

This state is persisted outside the model.

---

# 41. Next Model Invocation

The next model does NOT receive the complete history.

Instead:

```text
CURRENT TASK:
Determine whether F2 requires immediate shutdown.

RELEVANT STATE:
F2 = leakage detected.
Page 21 contains evidence.
SOP-17 section 4.2 may apply.

RETRIEVED EVIDENCE:
Page 21
SOP-17 section 4.2

PREVIOUS VERIFICATION:
None for F2.

QUESTION:
Determine required action and identify missing evidence.
```

This is the central mechanism for preventing context explosion.

---

# 42. Evidence Reference vs Evidence Content

Persistent state should generally store references.

Example:

```text
evidence_ref:
    E21
    document:
        Inspection_Report_2026
    page:
        21
```

The Context Manager retrieves the actual content only when required.

This avoids storing enormous evidence payloads inside task state.

---

# 43. Context Rehydration

When an evidence reference becomes relevant:

```text
Evidence Reference
       ↓
Knowledge Store
       ↓
Original evidence
       ↓
Context Manager
       ↓
Model
```

This is called conceptually **context rehydration**.

The task state remains compact while the required evidence remains retrievable.

---

# 44. Conversation History

Conversation history should be stored separately from model context.

The system may retain:

```text
User messages
Assistant responses
Task references
```

but only relevant conversational information should be injected into a new model context.

The system should prefer structured task state over replaying large conversational transcripts.

---

# 45. Conversation Compaction

Long conversations should be compacted.

Example:

```text
100 messages
    ↓
Extract:
- decisions
- constraints
- unresolved questions
- relevant user requirements
    ↓
Persistent conversation state
    ↓
Relevant subset
    ↓
New model context
```

Original history may remain available for audit or review.

---

# 46. Memory Retrieval

Persistent memory should also use retrieval.

```text
Current Task
    ↓
Memory Query
    ↓
Relevant Memory
    ↓
Context Manager
```

Memory should not automatically be injected wholesale.

---

# 47. Memory vs Knowledge

The distinction should remain:

| Layer                | Purpose                                     |
| -------------------- | ------------------------------------------- |
| Model Context        | Current working information                 |
| Conversation History | Record of interaction                       |
| Task State           | Current execution state                     |
| Persistent Memory    | Intentionally retained reusable information |
| Knowledge Base       | Organizational source information           |
| Original Documents   | Authoritative source artifacts              |

These layers must not be collapsed into one database abstraction merely for convenience.

---

# 48. Provenance Across Layers

Information should maintain lineage.

Example:

```text
Generated Finding
       ↓
Task State
       ↓
Evidence Reference
       ↓
Knowledge Chunk
       ↓
Document
       ↓
Page
```

For memory:

```text
Memory Entry
       ↓
Source Task
       ↓
Source Evidence / User Decision
```

This allows the system to answer:

> "Why does the system believe this?"

---

# 49. Knowledge Updates

When a document is added or updated:

```text
New document
    ↓
Ingestion
    ↓
New chunks/index entries
    ↓
Version metadata
```

The system should avoid silently mixing old and new versions.

Where document versioning matters, retrieval should be version-aware.

---

# 50. Retrieval Freshness

Knowledge retrieval may consider:

* Document version
* Effective date
* Modification date
* Authority
* Classification
* User permissions

For policy/SOP workflows, the latest applicable authoritative version should normally be preferred.

The system must not simply select the semantically closest document regardless of validity.

---

# 51. Context Caching

The implementation may cache frequently reused information.

Examples:

```text
SOP section
Repeated tool schema
Task metadata
Frequently accessed document chunks
```

Caching MUST NOT bypass:

* Permissions
* Version checks
* Classification
* Provenance

---

# 52. Context Reuse

If a piece of context remains valid, it may be reused between model invocations.

However, context reuse must remain bounded and invalidated when:

* Task state changes materially
* Evidence changes
* Permissions change
* Document version changes
* Model configuration changes
* Security policy changes

---

# 53. Tokenization Awareness

The Context Manager should operate in tokens or a reliable approximation of token cost.

Character count alone is insufficient because:

```text
characters ≠ tokens
```

The implementation should use the selected model/runtime tokenizer where practical.

If exact tokenization is too expensive for a prototype, the system may use a conservative token-estimation strategy.

---

# 54. Output Reservation

The Context Manager must reserve output capacity.

For example:

```text
Context limit = 8192

Input budget:
    system instructions
    task state
    evidence
    tool results

Output budget:
    reserved separately
```

The system MUST NOT construct an input that consumes the entire context while expecting unrestricted generation.

---

# 55. Context Overflow Handling

If the required information exceeds the available context:

```text
Context too large
      ↓
Prioritize
      ↓
Compress state
      ↓
Reduce evidence
      ↓
Retrieve more selectively
      ↓
Split task
      ↓
Retry
```

The system should not simply truncate information arbitrarily.

If critical evidence cannot fit, the task should be decomposed.

---

# 56. Map-Reduce Style Document Processing

For very large documents, the system may use a staged approach:

```text
Document
   ↓
Chunks
   ↓
Per-chunk extraction
   ↓
Structured findings
   ↓
Aggregation
   ↓
Targeted retrieval
   ↓
Final reasoning
```

This allows large documents to be processed without requiring large context.

However, aggregation must preserve source references.

---

# 57. Hierarchical Summarization

For very large documents:

```text
Pages
 ↓
Section summaries
 ↓
Document-level structured summary
 ↓
Relevant section retrieval
 ↓
Detailed evidence retrieval
```

The document summary should be used for navigation and planning, not as a replacement for original evidence.

---

# 58. Two-Pass Reasoning

A useful strategy is:

## Pass 1 — Discovery

Identify:

* Relevant sections
* Findings
* Entities
* Questions
* Potential risks

## Pass 2 — Verification / Detailed Reasoning

Retrieve only the relevant evidence and perform:

* Detailed reasoning
* Calculations
* Cross-checking
* Artifact generation

This is preferable to attempting to fully reason over the entire document at once.

---

# 59. Context Budgeting Example

For an 8K-context prototype, a conceptual budget might be:

```text
System / policy              ~800 tokens
Task + current plan          ~700
Persistent task state        ~900
Retrieved evidence           ~3,500
Tool results                 ~700
Output reservation           ~1,600
                              -----
                              ~8,200
```

These numbers are illustrative only.

The actual implementation MUST measure the selected model/runtime and configure the budget accordingly.

The important principle is:

> **Context allocation must be explicit.**

---

# 60. Multi-Agent Context Isolation

If multiple logical agents are used:

```text
Planner
Researcher
Coder
Verifier
```

they do not need to share one giant context.

Each can receive:

```text
Own role
+
Relevant task state
+
Relevant evidence
+
Relevant tool results
```

The shared source of truth remains persistent task state.

---

# 61. Example Multi-Agent Flow

```text
User
 ↓
Planner
 ↓
Persistent Task State
 ├───────────────┐
 ▼               ▼
Researcher      Coder
 │               │
 ▼               ▼
Evidence       Code Result
 │               │
 └───────┬───────┘
         ▼
    Verification
         │
         ▼
      Artifact
```

Agents do not need to exchange complete conversation histories.

---

# 62. Context and Model Routing

The Context Manager should inform model routing.

For example:

```text
Task requires:
- long context
- vision
- coding
```

The Model Gateway may select a model/profile capable of handling the requirement.

Therefore:

```text
Task Requirements
       ↓
Context Requirements
       ↓
Model Capability Requirements
       ↓
Model Router
```

Model routing and context management remain separate responsibilities.

---

# 63. Knowledge Base Does Not Solve Context Alone

RAG does not eliminate context limits.

Retrieval reduces the amount of information entering context.

Therefore:

```text
Knowledge Base
       ↓
Retrieval
       ↓
Smaller evidence set
       ↓
Context Manager
       ↓
Model
```

The system still requires context budgeting.

---

# 64. Persistent Memory Does Not Solve Context Alone

Persistent memory does not mean the model can access unlimited information simultaneously.

Instead:

```text
Persistent Memory
       ↓
Retrieve relevant memory
       ↓
Context Manager
       ↓
Model
```

Memory is storage.

Context is working space.

---

# 65. Task State Does Not Replace Knowledge

Task state records what happened during a task.

It should not become the authoritative replacement for the source documents.

For example:

```text
Task state:
"Corrosion found on page 14."

Source:
Inspection Report, page 14.
```

The source remains retrievable.

---

# 66. Knowledge Base Does Not Replace Task State

The knowledge base contains organizational information.

It should not be used to store the entire execution history of an agent task.

Task state belongs to the task.

Knowledge belongs to the organization's information layer.

---

# 67. Security Requirements

All context construction must respect:

* User authorization
* Document permissions
* Classification
* Task isolation
* Model permissions

Unauthorized evidence MUST NOT enter the context.

The Context Manager must operate after authorization filtering.

---

# 68. Sensitive Data Handling

The system should minimize sensitive information passed between components.

Where possible:

```text
Reference
+
Required excerpt
```

should be preferred over:

```text
Entire document
```

Internal components still operate inside the sovereignty boundary, but data minimization remains important for defense in depth.

---

# 69. Context Auditability

The system should be able to record enough metadata to understand what evidence influenced a model invocation.

For example:

```text
Invocation ID
Task ID
Model
Context profile
Evidence IDs
Task state version
Timestamp
```

Storing complete prompts may be configurable because prompts can themselves contain sensitive information.

---

# 70. Context Versioning

Persistent task state should have versions.

Example:

```text
Task State v1
Task State v2
Task State v3
```

A model invocation should be associated with the state version used to construct its context.

This improves reproducibility and auditability.

---

# 71. State Consistency

When multiple operations update task state, the system should avoid inconsistent writes.

At minimum, the prototype should ensure that:

* Tool results are associated with the correct task.
* Verification results reference the correct candidate result.
* Evidence references remain valid.
* Artifact references belong to the correct task.

---

# 72. Knowledge Integrity

The system should preserve the relationship:

```text
Derived information
        ↓
Source information
```

If an extracted finding is modified, the source reference should remain available.

---

# 73. Uncertainty

The system should represent uncertainty explicitly.

Examples:

```text
confidence:
HIGH

confidence:
MEDIUM

confidence:
LOW

status:
UNRESOLVED
```

The exact representation is implementation-specific.

The model should not be forced to produce a definitive answer when evidence is insufficient.

---

# 74. Hallucination Mitigation

The architecture should reduce hallucination through:

```text
Retrieval
+
Evidence grounding
+
Persistent state
+
Structured outputs
+
Verification
+
Source references
+
Explicit uncertainty
```

However:

> No architecture can guarantee that an LLM will never hallucinate.

The prototype should therefore demonstrate **risk reduction and detection**, not claim perfect factual accuracy.

---

# 75. Accuracy Strategy

Accuracy should be improved through layered controls:

```text
1. Retrieve authoritative evidence
2. Provide relevant evidence to model
3. Require source references
4. Separate facts from inference
5. Perform deterministic verification where possible
6. Use independent checks
7. Surface uncertainty
8. Require human review for consequential decisions
```

The model itself should not be treated as the sole source of truth.

---

# 76. Flagship Inspection Workflow

The complete context architecture should support:

```text
100-page report
       ↓
Local ingestion
       ↓
OCR / parsing
       ↓
Index
       ↓
Planner
       ↓
Persistent task state
       ↓
Targeted retrieval
       ↓
Bounded model context
       ↓
Findings
       ↓
Persistent state
       ↓
Further retrieval
       ↓
Verification
       ↓
Approval-note generation
```

The model may therefore perform many bounded reasoning steps while never receiving all 100 pages simultaneously.

---

# 77. Why This Scales Beyond 8K

The architecture is not fundamentally tied to 8K.

If the available model provides:

```text
8K
16K
32K
128K
```

the system can adjust the context budget.

The underlying architecture remains:

```text
Persistent Information
        ↓
Retrieval
        ↓
Context Construction
        ↓
Bounded Model Invocation
```

A larger context improves flexibility but does not eliminate the need for retrieval and persistent state.

---

# 78. Prototype Implementation Priorities

For the laptop prototype, priority should be:

### Priority 1

Persistent task state.

### Priority 2

Context budgeting.

### Priority 3

Local document ingestion.

### Priority 4

Chunking and metadata.

### Priority 5

Local retrieval.

### Priority 6

Evidence references.

### Priority 7

Context compaction.

### Priority 8

Provenance.

Advanced long-context optimizations are secondary.

---

# 79. Prototype Simplifications

The prototype may initially use:

* SQLite for task state.
* Local filesystem for documents/artifacts.
* Lightweight local vector/keyword indexes.
* Simple metadata.
* Single-user task scope.
* Basic memory records.
* Conservative token budgeting.

These choices are implementation decisions, not architectural requirements.

The architecture MUST remain replaceable.

---

# 80. Anti-Patterns

The following patterns are prohibited.

## Anti-pattern 1

```text
Entire 100-page document
        ↓
Every model invocation
```

## Anti-pattern 2

```text
Entire conversation history
        ↓
Every model invocation
```

## Anti-pattern 3

```text
Persistent memory
=
Everything the model has ever seen
```

## Anti-pattern 4

```text
Knowledge base
=
Model context
```

## Anti-pattern 5

```text
Summary
=
Original evidence
```

## Anti-pattern 6

```text
LLM
=
Database
```

## Anti-pattern 7

```text
LLM
=
Source of truth
```

---

# 81. Canonical Information Flow

The canonical information flow is:

```text
                  ORIGINAL DATA
                       │
                       ▼
                  KNOWLEDGE
                       │
                       ▼
                  RETRIEVAL
                       │
                       ▼
                   EVIDENCE
                       │
                       ▼
                 CONTEXT MANAGER
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      TASK STATE     MEMORY     CURRENT TASK
          │            │            │
          └────────────┼────────────┘
                       ▼
                 MODEL CONTEXT
                       │
                       ▼
                     MODEL
                       │
                       ▼
                    RESULT
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        TASK STATE           VERIFICATION
             │                   │
             └─────────┬─────────┘
                       ▼
                   ARTIFACT
```

---

# 82. Context Architecture Invariants

The following are mandatory.

## Invariant 1

Model context is bounded.

## Invariant 2

Persistent information exists outside model context.

## Invariant 3

The entire source document is not automatically inserted into every invocation.

## Invariant 4

Task state survives individual model invocations.

## Invariant 5

Evidence remains linked to its source.

## Invariant 6

Retrieval is permission-aware.

## Invariant 7

Summaries do not replace authoritative source documents.

## Invariant 8

Persistent memory is intentionally managed rather than automatically storing everything.

## Invariant 9

Context construction reserves space for model output.

## Invariant 10

Context overflow results in controlled reduction, retrieval, compaction, or task decomposition.

## Invariant 11

The model cannot bypass the knowledge/access-control layer.

## Invariant 12

The architecture remains functional if the model context size changes.

---

# 83. Definition of Done

The context and memory architecture is considered implemented for the prototype when the system can:

1. Accept a document larger than the model's context window.
2. Process it locally.
3. Store the original document.
4. Create searchable representations.
5. Retrieve relevant evidence.
6. Maintain persistent task state.
7. Construct bounded model contexts.
8. Continue a multi-step task across multiple model invocations.
9. Avoid replaying the entire document.
10. Preserve evidence references.
11. Preserve provenance.
12. Detect insufficient evidence.
13. Perform context compaction or task decomposition when required.
14. Generate a final artifact from accumulated verified state.

---

# 84. Implementation Rule

Implementation agents MUST treat this document as the authoritative contract for context, state, memory, and knowledge behavior.

They MUST NOT:

* Assume unlimited context.
* Replay complete documents unnecessarily.
* Use the model context as persistent storage.
* Treat summaries as authoritative source data.
* Store all conversation history in every prompt.
* Allow retrieval to bypass permissions.
* Remove source references during summarization.
* Silently truncate critical evidence.
* Claim that persistent memory eliminates context limits.

They SHOULD:

* Prefer structured state.
* Retrieve only relevant evidence.
* Maintain provenance.
* Measure token usage.
* Keep context budgets configurable.
* Make state transitions observable.
* Fail explicitly when evidence is insufficient.

If an implementation discovers that a requirement cannot fit inside the configured context budget, it MUST use retrieval, decomposition, compaction, or another controlled strategy rather than silently overflowing or truncating critical information.

---

# 85. Final Principle

The system does not attempt to make a small-context model behave as if it had infinite context.

Instead, it changes the architecture around the model:

```text
                 LARGE INFORMATION SPACE
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
        Knowledge      Task State     Memory
            │             │             │
            └─────────────┼─────────────┘
                          ▼
                      Retrieval
                          │
                          ▼
                   Context Manager
                          │
                    Small working set
                          │
                          ▼
                        MODEL
                          │
                          ▼
                     New state
                          │
                          └──────────────► next step
```

Therefore:

> **The model does not need to remember the entire task. The system remembers the task, and gives the model only what it needs to perform the next step.**

**Status: FROZEN — BASELINE CONTEXT / MEMORY ARCHITECTURE**

```
```
