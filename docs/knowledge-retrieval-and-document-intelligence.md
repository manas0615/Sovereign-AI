## `07-knowledge-retrieval-and-document-intelligence.md`

This is the next critical subsystem because it solves one of the biggest architectural problems we identified: **how the agent works with 100-page+ confidential documents despite an 8K working context.**

````markdown
# Sovereign AI Workbench
## Knowledge Retrieval & Document Intelligence Specification

**Project:** Sovereign AI — SIH 2026 Prototype  
**Document:** Knowledge Retrieval & Document Intelligence  
**Document ID:** SAI-DOC-007  
**Status:** FROZEN — BASELINE KNOWLEDGE ARCHITECTURE  
**Version:** 1.0  
**Depends On:**
- 01-project-charter.md
- 02-system-architecture.md
- 03-security-and-sovereignty.md
- 04-data-context-memory-architecture.md
- 05-model-gateway-and-routing.md
- 06-agent-host-and-orchestration.md

---

# 1. Purpose

This subsystem allows the Sovereign AI Workbench to work with organizational documents that are substantially larger than the context window of the local reasoning model.

It must support:

- PDFs
- scanned PDFs
- DOCX
- TXT
- spreadsheets where practical
- images
- inspection reports
- manuals
- SOPs
- engineering documentation
- correspondence
- photographs
- future multimodal documents

The system MUST NOT depend on placing an entire document into a single model prompt.

The central principle is:

> Large documents are stored and indexed externally; the model receives only the evidence required for the current reasoning step.

---

# 2. The Context Problem

The prototype's local reasoning model has a bounded working context.

For example:

```text
Model context:
8K tokens
````

A 100-page inspection report may contain:

```text
50K+
100K+
200K+
```

tokens depending on formatting, tables and images.

Therefore this is invalid:

```text
100-page report
      ↓
entire report
      ↓
8K-context model
```

Instead:

```text
100-page report
      ↓
Document Processing
      ↓
Persistent Document Representation
      ↓
Retrieval
      ↓
Relevant Evidence
      ↓
8K model context
```

---

# 3. Three Different Concepts

The architecture must distinguish:

## Model Context

Temporary working information supplied to one model invocation.

```text
Current task
+
Relevant evidence
+
Instructions
+
Tool results
```

It is bounded by the model's context window.

---

## Persistent Task State

Information maintained across model invocations.

Examples:

```text
Extracted findings
Current plan
Completed steps
Unresolved questions
Verification results
Evidence references
Artifact references
```

It allows the agent to continue a long task without replaying the entire conversation or document.

---

## Local Knowledge Base

Persistent organizational information stored independently of a model context.

Examples:

```text
SOPs
Manuals
Policies
Past reports
Engineering documents
Correspondence
```

The model accesses it through retrieval.

---

# 4. Core Architecture

```text
                    DOCUMENT
                       │
                       ▼
              ┌─────────────────┐
              │ Ingestion Layer │
              └────────┬────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Text          OCR          Vision
          │            │            │
          └────────────┼────────────┘
                       ▼
              Document Structure
                       │
                       ▼
                   Chunking
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Keyword      Embedding     Metadata
        Index          Index
          │            │            │
          └────────────┼────────────┘
                       ▼
                 Local KB Store
                       │
                       ▼
                Retrieval Engine
                       │
                  Top Candidates
                       │
                       ▼
                    Rerank
                       │
                       ▼
                  Evidence Set
                       │
                       ▼
                Context Manager
                       │
                       ▼
                     MODEL
```

---

# 5. Sovereignty Requirement

All document processing MUST remain local.

This includes:

```text
OCR
Parsing
Chunking
Embeddings
Indexing
Retrieval
Reranking
Vision processing
Storage
```

No document should be sent to:

```text
Cloud OCR
Cloud embeddings
Cloud vector database
Cloud LLM
External document processing API
```

unless a future deployment explicitly permits it.

For the SIH prototype, the default assumption is:

> No external processing.

---

# 6. Document Ingestion

Every document enters through a controlled ingestion pipeline.

```text
Input
 ↓
Validation
 ↓
Identification
 ↓
Extraction
 ↓
Normalization
 ↓
Chunking
 ↓
Indexing
 ↓
Ready
```

The original file must remain available as the authoritative source artifact.

---

# 7. File Validation

Before processing:

```text
Check:
- file type
- file size
- readability
- integrity
- supported format
```

Unsupported or corrupt files should produce an explicit error.

The system must not silently discard them.

---

# 8. Document Identity

Every ingested document should receive a stable identifier.

Conceptually:

```text
document_id
```

The system should also preserve:

```text
original filename
file hash
file type
creation/import timestamp
source
classification
permissions
```

The exact schema is implementation-specific.

---

# 9. Source Integrity

The original document should be hashed.

Conceptually:

```text
SHA-256(document)
```

This provides a stable identity for the source artifact.

If the same file is ingested again, the system can detect duplication.

---

# 10. Document Versioning

Documents may change.

Example:

```text
SOP-17 v1
SOP-17 v2
SOP-17 v3
```

The knowledge system should preserve document/version identity rather than treating every file as interchangeable.

This is particularly important for enterprise SOPs.

---

# 11. Text Extraction

For digitally generated PDFs:

```text
PDF
 ↓
Text extraction
 ↓
Structure detection
```

Preserve where possible:

* headings
* paragraphs
* tables
* page numbers
* lists
* captions

Plain text alone is insufficient when provenance matters.

---

# 12. Scanned Document Processing

For scanned PDFs:

```text
Scanned PDF
 ↓
Page images
 ↓
Local OCR
 ↓
Extracted text
```

The system should retain the relationship:

```text
Extracted text
      ↕
Original page
```

This allows the final answer to cite:

```text
Page 37
```

rather than merely:

```text
chunk_184
```

---

# 13. OCR Is Not Ground Truth

OCR can introduce errors.

Examples:

```text
0 → O
1 → I
5 → S
```

Engineering documents are particularly sensitive to such errors.

Therefore OCR output should retain:

```text
OCR confidence
page reference
bounding information where available
```

Low-confidence content may require vision-based inspection or human review.

---

# 14. Tables

Tables should not simply be flattened into arbitrary text when avoidable.

The system should preserve:

```text
Rows
Columns
Headers
Cell relationships
Page
Table identity
```

Example:

```text
| Equipment | Pressure | Temperature |
|-----------|----------|-------------|
| P-101     | 12 bar   | 180 C       |
```

should remain structurally interpretable.

---

# 15. Images

Images embedded in documents should preserve:

```text
document_id
page
image_id
location
caption if available
```

Where appropriate, a local vision model can analyze the image.

---

# 16. Engineering Drawings

Engineering drawings are a special case.

The prototype should support:

```text
Image/PDF
 ↓
Page/image extraction
 ↓
OCR where useful
 ↓
Vision model where available
 ↓
Detected labels / visible information
 ↓
Evidence references
```

The prototype must NOT claim full engineering-grade drawing interpretation unless it has actually been validated.

---

# 17. Handwritten Notes

Handwriting may require local vision/OCR processing.

The system should distinguish:

```text
machine-readable text
OCR text
handwritten extraction
vision interpretation
```

Uncertain handwriting must not be presented as verified fact.

---

# 18. Document Structure

The ingestion system should construct a logical representation.

Conceptually:

```text
Document
├── Section
│   ├── Paragraph
│   ├── Table
│   ├── Figure
│   └── Page
├── Section
└── Section
```

This structure improves retrieval and context construction.

---

# 19. Chunking

Large documents must be divided into retrievable units.

The chunking strategy should be structure-aware.

Prefer:

```text
Heading
 ↓
Paragraph group
 ↓
Logical section
```

over blindly splitting every N characters.

---

# 20. Chunk Size

Chunk size must be configurable.

Do NOT hard-code:

```text
"Every document must use exactly 500 tokens."
```

Different document types require different strategies.

The prototype should use a practical configurable range and test retrieval quality empirically.

---

# 21. Chunk Overlap

Small overlap between neighboring chunks may preserve local context.

Example:

```text
Chunk A:
...paragraph 1
...paragraph 2
...paragraph 3

Chunk B:
...paragraph 3
...paragraph 4
...paragraph 5
```

However, excessive overlap wastes storage and retrieval context.

The overlap should therefore be configurable.

---

# 22. Parent-Child Chunking

Where useful, use hierarchical chunks.

```text
Document
 ↓
Section
 ↓
Subsection
 ↓
Chunk
```

A small chunk may be retrieved first, while the larger parent section can be loaded if additional context is needed.

This is particularly useful for SOPs and manuals.

---

# 23. Chunk Metadata

Every chunk should carry metadata.

Conceptually:

```text
chunk_id
document_id
document_version
page_start
page_end
section
heading
content_type
source_type
permissions
```

Optional:

```text
ocr_confidence
embedding_id
table_id
image_id
```

---

# 24. Evidence Identity

Every retrieved piece of information should have a stable evidence identifier.

Example:

```text
EVID-000184
```

The Agent Host can then reference:

```text
Finding F4
 ↓
Evidence EVID-000184
 ↓
Inspection Report page 37
```

---

# 25. Why Evidence IDs Matter

They allow the system to distinguish:

```text
What the model said
```

from:

```text
What the source actually contained
```

This is essential for enterprise trust.

---

# 26. Retrieval Architecture

The prototype should support hybrid retrieval where practical.

```text
User/Agent Query
      │
      ├──────────────► Keyword Search
      │
      └──────────────► Semantic Search
                          │
                          ▼
                    Candidate Set
                          │
                          ▼
                       Rerank
                          │
                          ▼
                    Evidence Set
```

---

# 27. Keyword Retrieval

Keyword retrieval is useful for exact enterprise terminology.

Examples:

```text
"API 510"
"PSV-101"
"corrosion allowance"
"SOP-17"
"inspection date"
```

Exact matches can be extremely valuable in technical documentation.

---

# 28. Semantic Retrieval

Semantic retrieval helps when the query and source use different wording.

Example:

Query:

```text
"equipment showing excessive wall thinning"
```

Relevant source:

```text
"localized reduction in vessel shell thickness"
```

Embedding retrieval can connect the concepts.

---

# 29. Hybrid Retrieval

The prototype should combine both where possible.

Conceptually:

```text
Hybrid Score =
keyword relevance
+
semantic relevance
+
metadata relevance
```

The exact scoring formula is implementation-specific.

---

# 30. Metadata Filtering

Before or during retrieval, apply metadata filters.

Examples:

```text
document type = SOP
equipment = P-101
department = maintenance
version = current
classification = authorized
```

This reduces irrelevant results.

---

# 31. Permissions Before Retrieval

The knowledge system MUST NOT retrieve documents the user is not authorized to access.

Correct:

```text
User
 ↓
Permission filter
 ↓
Retrieval
```

Not:

```text
Retrieve everything
 ↓
Ask LLM to hide unauthorized content
```

Authorization must occur before information enters model context.

---

# 32. Retrieval Pipeline

Recommended pipeline:

```text
Query
 ↓
Normalize
 ↓
Permission filter
 ↓
Keyword retrieval
 ↓
Semantic retrieval
 ↓
Merge candidates
 ↓
Deduplicate
 ↓
Rerank
 ↓
Select evidence
 ↓
Context budget
 ↓
Model
```

---

# 33. Top-K Is Not the Final Answer

Retrieving the top 10 chunks does not mean all 10 belong in the prompt.

The system must perform context budgeting.

Example:

```text
20 candidates
 ↓
Reranking
 ↓
8 relevant chunks
 ↓
Context budget
 ↓
4 chunks selected
 ↓
Model
```

---

# 34. Context Budgeting

The Context Manager must reserve space for:

```text
System instructions
Task state
User request
Evidence
Tool results
Model output
```

Therefore:

```text
8K model context
```

does NOT mean:

```text
8K tokens of documents
```

The usable evidence budget is smaller.

---

# 35. Example 8K Context

Conceptually:

```text
8,192 tokens total

System instructions      ~800
Task state                ~700
User request              ~200
Evidence                 ~4,500
Tool results              ~700
Output allowance         ~1,292
--------------------------------
Total                    ~8,192
```

Actual allocation must be configurable.

The numbers above are illustrative, not fixed requirements.

---

# 36. Retrieval Is Iterative

The agent does not need to retrieve everything in advance.

Example:

```text
Question
 ↓
Retrieve initial evidence
 ↓
Reason
 ↓
Discover missing information
 ↓
Retrieve targeted evidence
 ↓
Reason again
```

This is particularly important with small context windows.

---

# 37. Multi-Hop Retrieval

Some questions require multiple retrieval steps.

Example:

```text
Inspection finding
 ↓
Equipment identifier
 ↓
Equipment manual
 ↓
Applicable SOP
 ↓
Maintenance requirement
```

The Agent Host should be able to perform this as a sequence.

---

# 38. Query Refinement

If retrieval quality is poor, the agent may reformulate the query.

Example:

```text
Query 1:
"corrosion issue"

Poor results

Query 2:
"localized shell thickness reduction"

Better results
```

Query refinement must be bounded to prevent loops.

---

# 39. Retrieval Failure

Possible outcomes:

```text
FOUND
PARTIAL
NOT_FOUND
CONFLICTING
UNAUTHORIZED
ERROR
```

The system should preserve the distinction.

`NOT_FOUND` does not mean:

> "The fact does not exist."

It means:

> "The current authorized knowledge sources did not provide sufficient evidence."

---

# 40. Hallucination Control

The model must be instructed:

```text
If evidence is insufficient:
- say so
- do not invent
- identify what is missing
```

The system should support an explicit:

```text
UNKNOWN / INSUFFICIENT_EVIDENCE
```

state.

---

# 41. Source Grounding

Answers based on organizational knowledge should provide source references where appropriate.

Example:

```text
Finding:
Localized wall thinning detected.

Evidence:
Inspection Report, page 37.

Requirement:
SOP-17, Section 4.2.
```

This allows the user to inspect the underlying source.

---

# 42. Evidence vs Summary

A generated summary is not itself evidence.

For example:

```text
Model:
"The vessel requires immediate maintenance."
```

is a conclusion.

Evidence might be:

```text
Inspection report:
Measured thickness = X mm
Required minimum = Y mm
```

The architecture should preserve this distinction.

---

# 43. Evidence Chain

A final conclusion should ideally be traceable:

```text
Conclusion
   ↓
Finding
   ↓
Evidence
   ↓
Source
   ↓
Page / section
```

Example:

```text
Approval Recommendation
 ↓
Finding F4
 ↓
Evidence E21
 ↓
Inspection Report
 ↓
Page 37
```

---

# 44. Conflicting Sources

Enterprise knowledge may contain conflicting information.

Example:

```text
SOP v2:
Minimum thickness = X

SOP v3:
Minimum thickness = Y
```

The system must not silently choose one.

It should use metadata such as:

```text
version
effective date
document status
authority
```

and flag conflicts when unresolved.

---

# 45. Current vs Historical Knowledge

The knowledge layer should distinguish:

```text
CURRENT
HISTORICAL
ARCHIVED
SUPERSEDED
UNKNOWN
```

The Agent Host should prefer authoritative current documents for operational decisions unless the user explicitly requests historical information.

---

# 46. Knowledge Freshness

The system should retain document metadata such as:

```text
effective_date
version
last_updated
status
```

A stale document should not automatically outrank a current authorized document.

---

# 47. Persistent Storage

The knowledge subsystem requires persistent storage for:

```text
Original documents
Extracted text
Document metadata
Chunks
Embeddings
Indexes
Evidence metadata
```

The exact database/vector store is an implementation decision.

The architecture must remain storage-provider agnostic.

---

# 48. Prototype Storage

For the laptop MVP, prefer a lightweight local architecture that is:

* easy to run
* easy to back up
* deterministic
* offline-capable
* low memory
* replaceable later

Do NOT introduce a heavyweight distributed knowledge platform unless it is required for the prototype.

---

# 49. Embedding Model

Embeddings should be generated locally.

The embedding model should be independently configurable from the reasoning model.

This is important because:

```text
Reasoning model
≠
Embedding model
```

They serve different purposes.

---

# 50. Embedding Model Failure

If the embedding service is unavailable, the system should still be able to use keyword retrieval where possible.

Therefore:

```text
Semantic retrieval unavailable
        ↓
Keyword fallback
```

should be possible.

---

# 51. Reranking

Reranking improves retrieval quality after candidate generation.

Conceptually:

```text
100 candidates
 ↓
Reranker
 ↓
10 best candidates
```

A local reranker should be preferred for sovereign deployments.

However, the prototype may initially omit a dedicated reranker if resource constraints make it impractical.

The architecture must leave a clear extension point.

---

# 52. Multimodal Retrieval

The knowledge architecture should eventually support:

```text
Text
Images
Tables
Scanned pages
Drawings
```

For the prototype, implementation may prioritize:

```text
Text + scanned PDF
```

while keeping the multimodal interfaces extensible.

---

# 53. Vision Evidence

If a vision model identifies information in an image, the evidence should retain:

```text
document
page
image
region if available
model/source
confidence if available
```

The system should distinguish:

```text
direct OCR
```

from:

```text
vision interpretation
```

---

# 54. Large Document Processing Strategy

For a 100-page report:

```text
100-page PDF
      ↓
Parse/OCR
      ↓
Page/section representation
      ↓
Chunks
      ↓
Indexes
      ↓
Persist
```

The model is NOT called once with the entire report.

Instead:

```text
Task
 ↓
Retrieve relevant chunks
 ↓
Reason
 ↓
Persist findings
 ↓
Retrieve more if required
 ↓
Verify
```

---

# 55. Example: 100-Page Inspection Report

User:

> "Review this inspection report and prepare an approval note."

The system should NOT do:

```text
100 pages
 ↓
LLM
```

It should do:

```text
1. Ingest report.

2. Build searchable representation.

3. Identify relevant sections.

4. Retrieve initial evidence.

5. Extract findings.

6. Persist findings in task state.

7. Identify missing information.

8. Retrieve targeted evidence.

9. Retrieve applicable SOP.

10. Compare findings with SOP.

11. Perform calculations if required.

12. Verify.

13. Generate approval note.
```

At no point is the entire 100-page report required in one model context.

---

# 56. Progressive Summarization

For extremely large documents, the system may create structured summaries at different levels.

```text
Document
 ↓
Section summaries
 ↓
Finding summaries
 ↓
Task-specific evidence
```

However, summaries MUST NOT replace source evidence.

The original source remains authoritative.

---

# 57. Hierarchical Context

A model invocation may receive:

```text
Document-level summary
+
Relevant section summary
+
Exact source excerpts
```

This can provide broad orientation without loading the entire document.

Example:

```text
Report overview
     +
Section 7 summary
     +
Page 37 exact evidence
```

---

# 58. Summary Drift

Generated summaries can contain errors.

Therefore summaries should carry provenance.

Example:

```text
Summary S12
derived_from:
  page 30-38
```

If the summary conflicts with source evidence, the source evidence wins.

---

# 59. Knowledge Base vs Task Workspace

The system must distinguish:

## Knowledge Base

Long-lived organizational information.

```text
SOPs
Manuals
Policies
Past reports
```

## Task Workspace

Temporary/task-specific information.

```text
Current report
Extracted findings
Intermediate calculations
Draft artifact
```

Do not automatically insert task artifacts into the organizational knowledge base.

---

# 60. Document Lifecycle

```text
UPLOADED
 ↓
PROCESSING
 ↓
INDEXED
 ↓
AVAILABLE
 ↓
UPDATED / SUPERSEDED
 ↓
ARCHIVED
```

Failed processing:

```text
PROCESSING
 ↓
FAILED
```

The system should expose the failure reason.

---

# 61. Re-indexing

If a document changes:

```text
Document version changes
 ↓
New processing
 ↓
New chunks/index entries
```

The old version remains identifiable if required for historical traceability.

---

# 62. Duplicate Documents

Use file hashing and metadata to detect likely duplicates.

Example:

```text
Same SHA-256
 ↓
Potential duplicate
```

Do not create unnecessary duplicate embeddings and indexes.

---

# 63. Security Classification

Documents may carry classifications such as:

```text
PUBLIC
INTERNAL
CONFIDENTIAL
RESTRICTED
```

The exact organization-specific classification system is deployment-dependent.

The knowledge system must support metadata-based access controls.

---

# 64. Data Minimization

Only relevant evidence should enter the model context.

This provides two benefits:

```text
Security
+
Context efficiency
```

Even within an air-gapped environment, unnecessary exposure of sensitive data to a model should be minimized.

---

# 65. Locality Guarantee

The document intelligence pipeline must have no hidden external dependency.

The prototype should be capable of operating with:

```text
Network disabled
```

after required models/packages are installed.

---

# 66. Offline Validation

A critical prototype test:

```text
Disable network
 ↓
Upload confidential document
 ↓
Process
 ↓
Retrieve
 ↓
Reason
 ↓
Generate artifact
```

The workflow should continue functioning.

---

# 67. Network Sovereignty

The system should not rely on:

```text
Hugging Face API
OpenAI API
Anthropic API
Google API
Cloud OCR
Cloud embeddings
```

during normal operation.

Model downloads are a provisioning activity, not runtime dependencies.

---

# 68. Retrieval Audit

Every retrieval should record:

```text
query
timestamp
task_id
user
retrieved document IDs
retrieved chunk IDs
ranking information where available
```

This allows investigation of why a model received particular evidence.

---

# 69. Evidence Provenance

Every evidence object should retain:

```text
source document
version
page
section
chunk
processing method
```

Potentially:

```text
OCR confidence
vision model
embedding model
```

---

# 70. Retrieval Evaluation

The retrieval system must be evaluated separately from the LLM.

Important questions:

```text
Did the correct document get retrieved?
Did the correct section get retrieved?
Was the relevant page included?
Was irrelevant information ranked higher?
```

A strong model cannot compensate for consistently poor retrieval.

---

# 71. Retrieval Test Set

The prototype should maintain a small local test set.

Example:

```text
Question
Expected document
Expected section
Expected evidence
```

Then measure:

```text
Recall@K
Precision@K
Evidence correctness
```

Exact metrics may be expanded later.

---

# 72. OCR Evaluation

Test:

```text
Printed text
Tables
Numbers
Units
Dates
Engineering identifiers
```

Numbers and identifiers deserve special attention because OCR errors can change meaning.

---

# 73. Retrieval + Context Evaluation

A successful retrieval test is:

```text
Correct evidence retrieved
 ↓
Fits context budget
 ↓
Model receives evidence
 ↓
Correct grounded conclusion
```

All three stages matter.

---

# 74. Accuracy Strategy

The system should not rely on one mechanism to achieve accuracy.

Use layered controls:

```text
Better ingestion
+
Better retrieval
+
Source grounding
+
Persistent state
+
Deterministic tools
+
Verification
+
Human review when required
```

This is the appropriate enterprise approach.

---

# 75. What This System Does NOT Solve

The architecture does not guarantee:

* Perfect OCR
* Perfect retrieval
* Perfect vision interpretation
* Perfect reasoning
* Zero hallucinations
* Correctness of unknown information

Instead, it makes errors:

* more detectable
* more traceable
* less dependent on unrestricted model context
* easier to verify

---

# 76. Prototype Scope

For the laptop prototype, prioritize:

### MUST HAVE

```text
PDF ingestion
Text extraction
OCR for scanned PDFs
Chunking
Metadata
Local persistent storage
Keyword retrieval
Semantic retrieval if resources permit
Evidence references
Context budgeting
Agent integration
Offline operation
```

### SHOULD HAVE

```text
Hybrid retrieval
Reranking
Table preservation
Page-level citations
Document versioning
```

### FUTURE

```text
Advanced engineering drawing understanding
Multimodal vector retrieval
Large-scale distributed indexing
Enterprise-scale permissions
Advanced reranking models
DataHub integration
```

---

# 77. Prototype Resource Constraint

The laptop has limited resources:

```text
System RAM: ~16 GB
GPU VRAM: ~4 GB usable according to NVIDIA/Vulkan reporting
CPU: 6 cores / 12 threads
```

Therefore the knowledge subsystem must remain lightweight.

Do not introduce unnecessary heavyweight infrastructure.

---

# 78. Resource Allocation Principle

The reasoning model is the most expensive component.

Therefore:

```text
Knowledge retrieval
should reduce
model context and inference work
```

not increase it.

Efficient retrieval is therefore a core optimization, not merely a convenience.

---

# 79. Context Limit Strategy

The final architecture for the prototype is:

```text
                 LARGE DOCUMENT
                       │
                       ▼
                LOCAL KNOWLEDGE
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        Persistent State      Retrieval
             │                   │
             └─────────┬─────────┘
                       ▼
                 Context Manager
                       │
                       ▼
                  ~8K MODEL
                       │
                       ▼
                Structured Result
                       │
                       ▼
                 Persistent State
```

The 8K context is therefore a **working memory limit**, not a document-size limit.

---

# 80. Key Design Principle

The system must never attempt to solve large-context problems simply by increasing model context.

Instead:

> **Store broadly, retrieve selectively, reason locally, persist results, and verify against evidence.**

This is the core strategy that makes the prototype feasible on constrained hardware.

---

# 81. Definition of Done

The subsystem is considered implemented when it can:

1. Ingest a local PDF.
2. Detect whether text extraction is available.
3. Use local OCR when required.
4. Preserve page/source identity.
5. Chunk the document.
6. Store chunks persistently.
7. Generate local embeddings where enabled.
8. Perform keyword retrieval.
9. Perform semantic retrieval where enabled.
10. Merge and rank candidates.
11. Apply document permissions.
12. Return evidence with provenance.
13. Support iterative retrieval.
14. Fit selected evidence into a bounded model context.
15. Support a 100-page-class document without placing the entire document in one prompt.
16. Preserve source references for generated conclusions.
17. Continue operating without external runtime services.
18. Expose retrieval operations to the Agent Host.
19. Support later replacement of the storage/index implementation.
20. Provide enough metadata to audit why evidence was supplied to the model.

---

# 82. Final Architecture Principle

The Sovereign AI Workbench does not need an enormous-context model to understand enormous enterprise documents.

It needs a good information architecture.

```text
             DOCUMENTS
                 │
                 ▼
          LOCAL PROCESSING
                 │
                 ▼
       PERSISTENT KNOWLEDGE
                 │
                 ▼
          TARGETED RETRIEVAL
                 │
                 ▼
             EVIDENCE
                 │
                 ▼
          BOUNDED CONTEXT
                 │
                 ▼
          LOCAL REASONING
                 │
                 ▼
         PERSISTENT STATE
                 │
                 ▼
          VERIFICATION
```

Therefore:

> **The context window limits one reasoning operation, not the size of the organization's knowledge.**

**Status: FROZEN — BASELINE KNOWLEDGE RETRIEVAL & DOCUMENT INTELLIGENCE ARCHITECTURE**

```
```
