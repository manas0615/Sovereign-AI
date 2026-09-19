# `05-model-gateway-and-routing.md`

````markdown
# Sovereign AI Workbench
## Model Gateway & Model Routing Specification

**Project:** Sovereign AI — SIH 2026 Prototype  
**Document:** Model Gateway & Routing  
**Document ID:** SAI-DOC-005  
**Status:** FROZEN — BASELINE MODEL ARCHITECTURE  
**Version:** 1.0  
**Depends On:** `01-project-charter.md`, `02-system-architecture.md`, `03-security-and-sovereignty.md`, `04-data-context-memory-architecture.md`

---

# 1. Purpose

This document defines how the Sovereign AI Workbench discovers, loads, invokes, selects, and manages local open-weight AI models.

The architecture MUST prevent the rest of the system from becoming tightly coupled to:

- Qwen
- Any specific model family
- llama.cpp
- Any specific inference backend
- A particular quantization
- A particular GPU
- A particular context size

The central principle is:

> **The Agent Host asks for an AI capability. The Model Gateway determines how that capability is provided locally.**

---

# 2. Core Objective

The Model Gateway must provide a stable abstraction:

```text
Agent Host
     │
     │ "I need a reasoning model
     │  with these requirements."
     ▼
Model Gateway
     │
     ├── Capability matching
     ├── Resource evaluation
     ├── Model selection
     ├── Runtime selection
     └── Profile selection
     │
     ▼
Local Inference Runtime
     │
     ▼
Open-Weight Model
````

The Agent Host MUST NOT need to know:

```text
llama-cli
GGUF filename
GPU layer count
Vulkan device number
quantization details
```

to perform normal inference.

---

# 3. Why a Model Gateway Is Required

A naïve implementation would be:

```text
Agent
 ↓
Qwen3-8B
```

This creates several problems.

If the project later adds:

* A better reasoning model
* A coding model
* A vision model
* A smaller fallback model
* A larger production model
* A different inference runtime

the Agent Host would need to change.

The desired architecture is:

```text
Agent
 ↓
Model Gateway
 ↓
Model A
Model B
Model C
Model D
```

The Agent Host therefore remains model-agnostic.

---

# 4. Model Gateway Responsibilities

The Model Gateway is responsible for:

1. Model registration
2. Model discovery
3. Model metadata
4. Capability matching
5. Model routing
6. Runtime abstraction
7. Inference profile selection
8. Context profile selection
9. Resource-aware decisions
10. Model health
11. Model lifecycle
12. Request validation
13. Response normalization
14. Error normalization
15. Future multi-model support

The Model Gateway is NOT responsible for:

* Task planning
* Tool authorization
* Knowledge retrieval
* Persistent task state
* Artifact generation
* Business workflow decisions

Those belong to other subsystems.

---

# 5. Model vs Runtime vs Profile

These concepts MUST remain separate.

## Model

The actual AI model.

Example:

```text
Qwen3-8B
```

## Runtime

The software executing the model.

Example:

```text
llama.cpp
```

## Model Format

Example:

```text
GGUF
```

## Quantization

Example:

```text
Q4_K_M
```

## Inference Profile

A configuration for running a model.

Example:

```text
Qwen3-8B Q4_K_M
+
8K context
+
20 GPU layers
```

Therefore:

```text
Model
  +
Runtime
  +
Format
  +
Quantization
  +
Profile
```

must not be treated as one inseparable object.

---

# 6. Prototype Runtime

The current prototype uses:

```text
Inference Runtime:
llama.cpp

Model:
Qwen3-8B

Format:
GGUF

Quantization:
Q4_K_M
```

The prototype has already demonstrated successful local inference through llama.cpp.

This is an implementation fact for the current hardware profile, not a permanent architectural dependency.

---

# 7. Validated Prototype Hardware

The current development machine has:

```text
CPU:
Intel Core i7-9850H

CPU cores:
6 physical
12 logical

System RAM:
16 GB

GPU:
NVIDIA Quadro T1000

Reported dedicated VRAM:
4 GB

Integrated GPU:
Intel UHD Graphics 630
```

The runtime detected both GPUs through Vulkan.

The relevant dedicated GPU for the prototype is:

```text
Vulkan1:
Quadro T1000
~4 GB device memory
```

The architecture MUST NOT assume that the machine has 8 GB of dedicated VRAM merely because the user's broader hardware description may refer to an 8 GB configuration.

Runtime measurements are authoritative for implementation decisions.

---

# 8. Validated Qwen3-8B Runtime

The following prototype measurements have been observed with:

```text
Model:
Qwen3-8B Q4_K_M

Model size:
~4.68 GiB

Parameters:
~8.19B

Runtime:
llama.cpp

Backend:
Vulkan

Device:
Quadro T1000

GPU layers:
20
```

Measured benchmarks included:

```text
Prompt 4096:
~119.64 tokens/sec

Generation 128:
~5.39 tokens/sec
```

At:

```text
Prompt 8192
GPU layers 20
```

the observed values were approximately:

```text
Prompt processing:
~104.33 tokens/sec

Generation:
~4.39 tokens/sec
```

At:

```text
Prompt 16384
GPU layers 10
```

the observed values were approximately:

```text
Prompt processing:
~81.19 tokens/sec

Generation:
~3.77 tokens/sec
```

These numbers are environment-specific measurements.

They MUST NOT be presented as universal Qwen3-8B performance figures.

---

# 9. Important Hardware Finding

Attempting to load the full Qwen3-8B Q4_K_M model with:

```text
-ngl 99
```

onto the Quadro T1000 failed with:

```text
ErrorOutOfDeviceMemory
```

This establishes an important design requirement:

> **The prototype cannot assume that the entire model must reside in GPU VRAM.**

Instead, llama.cpp-style hybrid CPU/GPU execution is acceptable.

---

# 10. GPU Layer Offloading

The prototype therefore supports configurations such as:

```text
Model
 │
 ├── Some layers → GPU
 │
 └── Remaining layers → CPU/RAM
```

The number of GPU layers is a runtime configuration.

It MUST NOT be hard-coded into the Agent Host.

For example:

```text
Agent Host
   ↓
Model Gateway
   ↓
Profile:
    gpu_layers = 20
```

The gateway/runtime adapter handles the actual inference configuration.

---

# 11. Resource-Aware Profiles

A single model may have multiple execution profiles.

Example:

```text
Qwen3-8B Q4_K_M
│
├── qwen8b-fast
│     context = 8K
│     gpu_layers = 20
│
├── qwen8b-long
│     context = 16K
│     gpu_layers = 10
│
└── qwen8b-safe
      conservative resource settings
```

The exact profile names and values are implementation configuration.

The important architectural principle is:

> **A model is not equivalent to one fixed runtime configuration.**

---

# 12. Context Size Is a Runtime Constraint

A model may theoretically support a particular context length, but the actual deployment must consider:

* VRAM
* RAM
* KV cache
* GPU layer configuration
* Runtime implementation
* Concurrent requests
* CPU availability
* Other running services

Therefore the Model Gateway MUST distinguish:

```text
Model-supported context
```

from:

```text
Currently feasible context
```

---

# 13. Context Capability Metadata

A model registration should contain information such as:

```text
Model:
Qwen3-8B

Modalities:
text

Maximum supported context:
model-specific

Configured profiles:
8K
16K
...

Quantization:
Q4_K_M

Capabilities:
reasoning
general_text
tool_use
```

The runtime may impose additional practical limits.

The gateway must use the active profile rather than assuming theoretical maximums.

---

# 14. Model Capability Registry

The gateway should maintain a local registry.

Conceptually:

```text
ModelRegistry
│
├── Model
│   ├── identity
│   ├── version
│   ├── format
│   ├── quantization
│   ├── capabilities
│   ├── modalities
│   ├── context limits
│   └── runtime
│
└── Profiles
    ├── resource requirements
    ├── context
    ├── GPU layers
    ├── generation settings
    └── status
```

This registry should be configuration-driven where practical.

---

# 15. Model Capability Taxonomy

The prototype should use capability labels rather than hard-coded model names.

Possible capabilities:

```text
reasoning
general_text
coding
tool_calling
structured_output
vision
ocr
embedding
reranking
summarization
long_context
```

A model can advertise multiple capabilities.

Example:

```text
Qwen3-8B:
    reasoning
    general_text
    coding
    structured_output
```

The exact capability declaration must be validated rather than blindly assumed.

---

# 16. Modality Registry

Models should also declare modalities.

Example:

```text
text
image
audio
video
```

The current Qwen3-8B prototype model is text-only.

Therefore a scanned-document workflow cannot assume Qwen3-8B itself performs visual understanding.

The multimodal architecture should instead support:

```text
Image/PDF
   ↓
Local OCR/Vision Model
   ↓
Extracted evidence
   ↓
Reasoning Model
```

---

# 17. Model Routing Request

The Agent Host should send a structured request to the gateway.

Conceptually:

```text
ModelRequest {
    task_type
    required_capabilities
    input_modality
    desired_context
    output_requirements
    latency_priority
    resource_priority
    security_classification
}
```

Example:

```text
task_type:
document_analysis

required_capabilities:
reasoning
structured_output

input_modality:
text

desired_context:
8192

security:
confidential
```

The Agent Host does not specify:

```text
llama-cli
Qwen3-8B-Q4_K_M.gguf
-ngl 20
```

---

# 18. Routing Decision

The gateway evaluates:

```text
Request
  ↓
Capability filtering
  ↓
Security filtering
  ↓
Context feasibility
  ↓
Resource feasibility
  ↓
Model ranking
  ↓
Profile selection
  ↓
Inference
```

A model that cannot satisfy the required constraints must not be selected simply because it is the default model.

---

# 19. Routing Priority

A reasonable routing priority is:

```text
1. Security compatibility
2. Required modality
3. Required capability
4. Context feasibility
5. Structured-output/tool requirements
6. Resource feasibility
7. Model quality
8. Latency
```

Security and capability requirements take precedence over convenience.

---

# 20. Model Selection Example

Suppose the registry contains:

```text
Model A:
reasoning
text
8K
low resource

Model B:
reasoning
coding
text
16K
higher resource

Model C:
vision
text
8K
medium resource
```

For:

> "Analyze this scanned inspection report."

The gateway may determine:

```text
Vision required
     ↓
Model C
```

For:

> "Write Python code to calculate inspection statistics."

It may select:

```text
Coding required
     ↓
Model B
```

For a simple summarization task:

```text
General text
     ↓
Model A
```

The exact selection mechanism is implementation-specific.

---

# 21. Rule-Based Routing for Prototype

The prototype SHOULD initially use deterministic rule-based routing rather than asking an LLM to select the model.

Example:

```text
if vision_required:
    select vision-capable model

elif coding_required:
    select coding-capable model

elif long_context_required:
    select feasible long-context profile

else:
    select default reasoning model
```

This provides:

* Predictability
* Debuggability
* Low overhead
* Easy demonstration
* No recursive model-selection problem

A learned router may be introduced later.

---

# 22. Why the Router Should Not Initially Be an LLM

Using an LLM to decide which LLM should execute a task introduces:

```text
Router model
      ↓
Target model
```

This consumes additional:

* Tokens
* Memory
* Latency
* Compute

and can introduce routing uncertainty.

For the constrained laptop prototype, deterministic routing is preferred.

The architecture remains open to intelligent routing later.

---

# 23. Context-Aware Routing

Routing must consider context requirements.

Example:

```text
Task:
Analyze 14K tokens of evidence
```

If:

```text
Model A:
8K feasible

Model B:
16K feasible
```

Model B is preferred if the task genuinely requires the larger context.

However, the gateway should first determine whether retrieval/decomposition can reduce the requirement.

The system should not automatically select larger-context models merely because they exist.

---

# 24. Retrieval Before Scaling Context

The preferred strategy is:

```text
Large task
    ↓
Retrieve relevant information
    ↓
Can it fit current context?
       /       \
     YES        NO
      ↓          ↓
 Current model  Replan / larger profile
```

This is important because larger context consumes more memory.

---

# 25. Context Feasibility Check

Before invocation:

```text
Requested context
        ↓
Profile context limit
        ↓
Available memory
        ↓
KV-cache/resource estimate
        ↓
Feasible?
```

If not feasible:

```text
NO
 ↓
Try smaller evidence set
 ↓
Try task decomposition
 ↓
Try alternate profile/model
 ↓
Fail explicitly if necessary
```

The gateway must not blindly attempt an infeasible configuration.

---

# 26. Resource-Aware Routing

The gateway should consider:

```text
Available RAM
Available VRAM
Current GPU utilization
Current model loaded
Context size
Concurrency
Expected generation length
```

For the laptop prototype, resource-awareness is especially important.

---

# 27. Single Model, Multiple Agents

The architecture does NOT require one model instance per logical agent.

Example:

```text
Planner Agent
Research Agent
Coding Agent
Verifier Agent
       │
       ▼
Model Gateway
       │
       ▼
One local model
```

Each agent may have:

* Different system instructions
* Different context
* Different tools
* Different task state

while sharing the same underlying model.

---

# 28. Concurrency

With a single local model:

```text
Agent A ─┐
Agent B ─┼──► Gateway ─► Model
Agent C ─┘
```

the gateway may:

* Serialize requests
* Queue requests
* Batch requests if supported
* Reject requests when resource limits are exceeded

The prototype should prefer controlled serialization over uncontrolled concurrency.

---

# 29. Model Lifecycle

The gateway should support states such as:

```text
REGISTERED
AVAILABLE
LOADING
READY
BUSY
UNAVAILABLE
FAILED
UNLOADING
```

Example:

```text
Model:
Qwen3-8B

State:
READY
```

If loading fails:

```text
FAILED
```

The gateway should report the failure rather than pretending inference is available.

---

# 30. Model Loading Strategy

The prototype may use lazy loading:

```text
Task
 ↓
Router
 ↓
Model required?
 ↓
Load model
 ↓
Inference
```

This reduces idle resource consumption.

Alternatively, a default model may remain loaded during development.

The architecture should support both.

---

# 31. Model Unloading

If resource pressure becomes significant:

```text
Model A
 ↓
No longer required
 ↓
Unload
 ↓
Free RAM/VRAM
 ↓
Load Model B
```

The gateway should own lifecycle management rather than allowing every subsystem to independently load models.

---

# 32. Model Warm State

For performance-sensitive tasks, keeping a frequently used model loaded may be preferable.

Example:

```text
Default reasoning model
        ↓
READY
```

while specialized models are loaded only when required.

The policy should be configurable.

---

# 33. Inference Adapter

The gateway should use an adapter abstraction.

Conceptually:

```text
ModelGateway
      │
      ▼
InferenceAdapter
      │
 ┌────┼────────────┐
 ▼    ▼            ▼
llama.cpp
Future Runtime A
Future Runtime B
```

The Agent Host should never call runtime-specific APIs directly.

---

# 34. llama.cpp Adapter

The prototype implementation should provide a llama.cpp adapter.

Its responsibility is to translate:

```text
Generic ModelRequest
```

into:

```text
llama.cpp-specific configuration
```

and normalize:

```text
llama.cpp result
```

back into a generic:

```text
ModelResponse
```

---

# 35. Generic Model Response

The gateway should expose a normalized response.

Conceptually:

```text
ModelResponse {
    request_id
    model_id
    profile_id
    content
    structured_output
    tool_calls
    usage
    finish_reason
    timing
    errors
}
```

The exact schema is implementation-specific.

The Agent Host should not need to parse llama.cpp-specific console output.

---

# 36. Tool Calling

If the model supports structured tool calling, the gateway should normalize it.

Flow:

```text
Model
 ↓
Tool Intent
 ↓
Gateway
 ↓
Normalized Tool Call
 ↓
Agent Host
 ↓
Policy
 ↓
Tool
```

The Model Gateway should not execute tools.

It only communicates model output.

---

# 37. Structured Output

Where possible, the gateway should support structured output.

Example:

```text
{
    "decision": "retrieve",
    "query": "...",
    "reason": "..."
}
```

The Agent Host validates the structure.

Malformed output should produce:

```text
STRUCTURED_OUTPUT_ERROR
```

rather than being silently interpreted.

---

# 38. Generation Parameters

Generation settings should be associated with profiles rather than scattered throughout application code.

Potential parameters include:

```text
temperature
top_p
max_tokens
context_size
GPU layers
batch size
threads
KV-cache settings
```

The exact runtime-supported parameters are adapter-specific.

---

# 39. Determinism

For verification-sensitive workflows, the system may use conservative generation settings.

For example:

```text
temperature:
low / deterministic profile
```

Creative document drafting may use a different profile.

The routing system should therefore allow task-specific inference profiles.

---

# 40. Reasoning Mode

Some models expose reasoning/thinking behavior.

The gateway should treat reasoning configuration as a model-specific capability.

The Agent Host should receive the final usable response and relevant metadata.

The architecture MUST NOT assume that every model exposes reasoning in the same way.

---

# 41. Model Versioning

Model identity should include version information.

Example:

```text
model_id:
qwen3-8b

revision:
approved-local-build

quantization:
Q4_K_M
```

This supports reproducibility.

A task should be able to record which model/profile produced a result.

---

# 42. Model Integrity

Production deployment should verify model artifacts before use.

Possible metadata:

```text
Model ID
Version
File hash
Quantization
Source
Approval status
```

The runtime should not dynamically replace an approved model with an unknown model.

---

# 43. Offline Model Acquisition

Model downloading should occur outside the confidential runtime.

Preferred lifecycle:

```text
Approved acquisition environment
        ↓
Download model
        ↓
Integrity verification
        ↓
Transfer into controlled environment
        ↓
Register model
        ↓
Offline runtime
```

The runtime itself should not silently access the internet to obtain a missing model.

---

# 44. Model Registry Example

A conceptual configuration could resemble:

```text
models:
  - id: qwen3-8b
    runtime: llamacpp
    format: gguf
    quantization: q4_k_m
    modalities:
      - text
    capabilities:
      - reasoning
      - coding
      - structured_output

    profiles:
      - id: qwen3-8b-8k
        context: 8192
        gpu_layers: 20

      - id: qwen3-8b-16k
        context: 16384
        gpu_layers: 10
```

This is an illustrative schema.

The implementation may use YAML, JSON, database records, or another configuration mechanism.

---

# 45. Security Filtering

Model routing MUST apply security policy before capability ranking.

Conceptually:

```text
All Models
    ↓
Approved Models
    ↓
Security-Compatible Models
    ↓
Capability-Compatible Models
    ↓
Resource-Compatible Models
    ↓
Best Candidate
```

A technically superior but unauthorized model MUST NOT be selected.

---

# 46. Model Trust Levels

The registry may support model trust metadata.

Example:

```text
APPROVED
EXPERIMENTAL
DISABLED
```

Only approved models should be selectable for sensitive workflows by default.

---

# 47. Model Health

The gateway should expose basic health information:

```text
Model loaded?
Runtime reachable?
Inference successful?
Resource available?
Profile feasible?
```

Example:

```text
Qwen3-8B
READY
GPU:
AVAILABLE
Context:
8192
```

---

# 48. Failure Handling

Potential failures include:

```text
MODEL_NOT_FOUND
MODEL_LOAD_FAILED
INSUFFICIENT_VRAM
INSUFFICIENT_RAM
CONTEXT_TOO_LARGE
RUNTIME_UNAVAILABLE
INFERENCE_TIMEOUT
MALFORMED_RESPONSE
UNSUPPORTED_CAPABILITY
MODEL_NOT_AUTHORIZED
```

Failures must be normalized before reaching the Agent Host.

---

# 49. Fallback Strategy

Fallback should be controlled.

Example:

```text
Requested:
16K context

Profile A:
16K
fails due to memory

        ↓

Try:
8K profile + task decomposition

        ↓

If possible:
continue

Otherwise:
explicit failure
```

The system must not silently switch to an external/cloud model.

---

# 50. Fallback Is Not Automatic Model Downgrading

A smaller model should only be selected if it still satisfies the task requirements.

Incorrect:

```text
Model A failed
 ↓
Use any available model
```

Correct:

```text
Model A failed
 ↓
Find another model/profile
 ↓
Check capabilities
 ↓
Check security
 ↓
Check context
 ↓
Check resource feasibility
 ↓
Select only if requirements remain satisfied
```

---

# 51. Long Context Strategy

The Model Gateway MUST NOT be treated as the primary solution to large documents.

The preferred architecture remains:

```text
Large document
 ↓
Knowledge ingestion
 ↓
Retrieval
 ↓
Context management
 ↓
Model
```

Larger model context is an optimization, not the fundamental architecture.

---

# 52. 8K Prototype Strategy

The current prototype should primarily target:

```text
Qwen3-8B Q4_K_M
+
8K working context
+
20 GPU layers
```

where feasible.

A 16K profile has also been experimentally demonstrated with reduced GPU offloading:

```text
Qwen3-8B Q4_K_M
+
16K context
+
10 GPU layers
```

This demonstrates that context size can be traded against resource usage.

The exact production configuration must be determined by runtime testing.

---

# 53. Model Selection and Context Manager Interaction

The two subsystems interact as follows:

```text
Agent Host
   │
   ├── Task requirements
   │
   ▼
Context Manager
   │
   ├── Estimated context requirement
   │
   ▼
Model Gateway
   │
   ├── Capability matching
   ├── Context feasibility
   └── Resource feasibility
   │
   ▼
Selected Profile
   │
   ▼
Inference
```

The gateway does not construct the evidence itself.

The Context Manager determines what must be supplied.

The gateway determines where that request can run.

---

# 54. Model Routing and Persistent State

Persistent task state should not be sent to the gateway wholesale.

The flow is:

```text
Task State
   ↓
Context Manager
   ↓
Bounded Model Request
   ↓
Model Gateway
```

The gateway receives the already-constructed inference request.

---

# 55. Model Routing and Knowledge

The Model Gateway does not directly query the knowledge base.

Correct:

```text
Agent Host
 ↓
Knowledge MCP
 ↓
Evidence
 ↓
Context Manager
 ↓
Model Request
 ↓
Model Gateway
```

Incorrect:

```text
Model Gateway
 ↓
Knowledge Database
```

This preserves separation of responsibilities.

---

# 56. Model Routing and Tools

The Model Gateway does not execute tools.

Correct:

```text
Model
 ↓
Tool call
 ↓
Agent Host
 ↓
Policy
 ↓
Tools MCP
```

The gateway only transports/normalizes model output.

---

# 57. Multi-Model Production Architecture

A future deployment may contain:

```text
                  Model Gateway
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
 Reasoning         Coding             Vision
 Model             Model              Model
       │               │                │
       ▼               ▼                ▼
 GPU Server A      GPU Server B      GPU Server C
```

The Agent Host architecture remains unchanged.

---

# 58. Multi-Model Prototype Architecture

The laptop prototype does NOT need to run multiple large models simultaneously.

Instead:

```text
                 Model Gateway
                      │
              ┌───────┴───────┐
              ▼               ▼
         Qwen3-8B         Future Model
         Current           Optional
         Default
```

The architecture can demonstrate model routing using multiple registered capabilities/profiles even if only one large model is practically active at a time.

---

# 59. Demonstrating Auto Model Selection

For SIH, the prototype should demonstrate at least two different task types.

Example:

```text
Task A:
Document reasoning
      ↓
Reasoning profile

Task B:
Coding
      ↓
Coding-capable profile/model
```

If the same underlying model is used for both during constrained laptop development, the UI should still expose the **capability/profile decision** honestly.

It must not falsely claim that two different neural models were used if only one was running.

---

# 60. Recommended Demonstration Evolution

Prototype stage:

```text
Rule-based router
+
One primary model
+
Multiple profiles
```

Enhanced prototype:

```text
Rule-based router
+
Two local models
```

Production architecture:

```text
Capability-aware dynamic router
+
Multiple approved models
+
Resource-aware scheduling
```

The architecture supports all three.

---

# 61. Observability

Every inference should produce metadata such as:

```text
request_id
task_id
model_id
profile_id
runtime
context_limit
estimated_input_tokens
output_tokens
duration
status
```

This is useful for:

* Debugging
* Performance measurement
* Audit
* SIH demonstration

---

# 62. Cost / Resource Accounting

The gateway should expose enough information to determine:

```text
Which model ran?
Which profile?
How much context?
How long?
What resources?
```

This allows future optimization.

The prototype does not need a sophisticated GPU scheduler.

---

# 63. No Hidden Model Calls

A single Agent Host action should not secretly invoke multiple models unless the architecture explicitly requires it.

For example:

```text
User request
 ↓
Router
 ↓
Qwen
```

should remain observable.

If future routing uses:

```text
Router Model
 ↓
Reasoning Model
 ↓
Verifier Model
```

those calls must be explicit in execution/audit records.

---

# 64. Model Gateway API Boundary

The internal interface should conceptually expose operations such as:

```text
list_models()
get_model(model_id)
get_capabilities(model_id)
get_profiles(model_id)
check_feasibility(request)
select_model(request)
generate(request)
health()
```

The exact programming interface is implementation-specific.

---

# 65. No Runtime Leakage

Higher-level code should not contain logic such as:

```text
if qwen:
    ...
elif llama:
    ...
```

for normal inference behavior.

Instead:

```text
gateway.generate(request)
```

should be the stable abstraction.

Runtime-specific logic belongs inside adapters.

---

# 66. Testing Requirements

The Model Gateway must eventually test:

### Registration

* Model can be registered.
* Invalid model metadata rejected.

### Routing

* Correct capability selected.
* Unauthorized model rejected.
* Infeasible profile rejected.

### Resources

* Insufficient VRAM handled.
* Insufficient RAM handled.
* Context overflow handled.

### Runtime

* llama.cpp adapter works.
* Runtime errors normalized.

### Inference

* Response returned.
* Structured output validated.

### Failure

* Model load failure handled.
* Timeout handled.
* Missing model handled.

### Sovereignty

* Runtime does not silently download models.
* No external inference endpoint is used.

---

# 67. Prototype Definition of Done

The Model Gateway is considered implemented when it can:

1. Register the local Qwen3-8B model.
2. Represent its capabilities.
3. Represent multiple runtime profiles.
4. Invoke llama.cpp through an adapter.
5. Keep llama.cpp details out of the Agent Host.
6. Select an appropriate profile for a task.
7. Check context feasibility.
8. Check resource feasibility.
9. Handle insufficient VRAM.
10. Handle model/runtime failure.
11. Return normalized model responses.
12. Record model/profile metadata.
13. Support future model registration without redesigning the Agent Host.
14. Operate without external AI services.
15. Demonstrate routing decisions visibly.

---

# 68. Architectural Invariants

The following are mandatory.

## Invariant 1

The Agent Host does not directly depend on a model runtime.

## Invariant 2

The Model Gateway does not perform task planning.

## Invariant 3

The Model Gateway does not execute tools.

## Invariant 4

The Model Gateway does not bypass security policy.

## Invariant 5

Models are selected based on capabilities and constraints, not merely availability.

## Invariant 6

The gateway distinguishes theoretical model capability from practical runtime feasibility.

## Invariant 7

Context size is treated as a resource constraint.

## Invariant 8

GPU VRAM is not assumed to be sufficient for full model offloading.

## Invariant 9

Model fallback cannot silently become cloud fallback.

## Invariant 10

New models can be introduced through registration/adapters without redesigning the Agent Host.

## Invariant 11

Model inference is observable and auditable.

## Invariant 12

The system remains functional when only one local model is available.

---

# 69. Implementation Rule

Implementation agents MUST:

* Preserve the Model Gateway boundary.
* Use an inference adapter.
* Keep model configuration outside business logic.
* Make model profiles configurable.
* Check resource feasibility.
* Normalize runtime errors.
* Record model/profile identity.
* Keep external network access out of the inference path.
* Treat model output as untrusted data.
* Preserve future multi-model extensibility.

Implementation agents MUST NOT:

* Hard-code Qwen3-8B throughout the Agent Host.
* Hard-code llama.cpp throughout the application.
* Assume full GPU offloading.
* Assume unlimited context.
* Spawn a new model process for every logical agent unnecessarily.
* Automatically download missing models during confidential runtime.
* Automatically fall back to cloud inference.
* Let the model choose its own authorization level.

If a requested feature requires violating one of these invariants, implementation MUST STOP and report the architectural conflict.

---

# 70. Final Principle

The Model Gateway exists to make the following possible:

```text
Today:

Agent
 ↓
Model Gateway
 ↓
Qwen3-8B
 ↓
llama.cpp
 ↓
Quadro T1000 / CPU
```

Tomorrow:

```text
Agent
 ↓
Model Gateway
 ├── Reasoning Model
 ├── Coding Model
 ├── Vision Model
 ├── Embedding Model
 └── Verification Model
```

The Agent Host does not need to be redesigned.

Therefore:

> **The model is replaceable infrastructure. The agent architecture is not built around one model.**

The system should be able to evolve as open-weight models improve without requiring a redesign of the sovereign enterprise workflow.

**Status: FROZEN — BASELINE MODEL GATEWAY & ROUTING ARCHITECTURE**

```
```
