# Sovereign AI — Benchmark and Qualification Evaluation Report

**Date:** 2026-09-20
**Environment:** Native Windows, Intel i7, 16GB RAM, NVIDIA Quadro T1000 (4GB VRAM)
**Target Model:** Llama-3.2-3B-Instruct (Q4_K_M, Vulkan backend, 8192 context)

## 1. Methodology and Objectives
This evaluation encompasses two phases of testing on the Sovereign AI platform:
1. **Static Analysis of 150-Trial Coding Benchmark:** Analysis of previously generated raw benchmark results (`results_full.jsonl`) to properly distinguish algorithmic correctness from infrastructure enforcement.
2. **Empirical Model Qualification (Phase 3 Pilot):** A strictly isolated, multi-case qualification pilot evaluating the local `Llama-3.2-3B-Instruct` model against three core capability contracts.

## 2. Benchmark Results (Recalculated)
Analysis of the 150-trial coding benchmark (`benchmarks/results_full.jsonl`) established the following metrics from raw records:
- **Total Trials:** 150
- **Evaluable Trials:** 149
- **Final Captured Submission Correctness:** 98.0% (146 / 149 evaluable trials passed hidden test cases)
- **First Captured Submission Correctness:** 95.3% (142 / 149 evaluable trials passed hidden test cases)
- **End-to-End Workflow Success:** 0.0% (0 / 150)
- **First Model Generation Passed:** UNAVAILABLE (Raw step-by-step reasoning ledger is not serialized).

**Causality for Workflow Failure (150 Total):**
Despite generating correct algorithms (98.0%), no task was successfully completed due to the infrastructure's fail-closed verification. The 150 failures are causally grouped by their terminal reasons:
- **126 trials** exhausted the tool retry limit because the `TrustedCodeVerifier` operated in a `DEGRADED` security mode (lacking native Windows sandboxing), returning `Verification Inconclusive`.
- **22 trials** were forcibly terminated because the agent attempted to output `FINAL` without having passed the independent trusted verification checks.
- **2 trials** crashed due to `Malformed model output: Malformed JSON: Unterminated string starting at: line 1 column 111 (char 110)`. (One of these trials was evaluable from a prior turn; the other was the sole non-evaluable trial).

## 3. Pilot Qualification Results
The Phase 3 qualification pilot was executed within a strictly isolated run directory, injecting a dedicated SQLite instance to preserve the primary database.

| Contract | Case ID | Result | Passport ID |
| :--- | :--- | :--- | :--- |
| `DocumentRetrieval_v1` | `t_doc` | QUALIFIED | a128d7aa-a09a-466d-a703-e77272375589 |
| `AutomatedCoding_v1` | `t_code` | QUALIFIED | 8727790d-0deb-49c8-b3c9-5a6b135e6284 |
| `AgentDecision_v1` | `t_doc` | QUALIFIED | bcee3d91-65d6-4d72-9491-e409b6cab092 |

*See `pilot_results.json` for exact timestamps, deployment profiles, and metadata. NOTE: `AgentDecision_v1` strictly reproduces the original script's use of `t_doc`, meaning it assesses JSON document retrieval formatting, not complex multi-step reasoning.*

## 4. Resource Utilization
An independent PowerShell monitor logged system-level metrics every 2 seconds during the pilot.
- **Peak VRAM Observed:** 2115 MiB. *Limitation: This is a system-observed value representing the maximum recorded snapshot across 2-second intervals, not an exact per-trial peak.*
- **System RAM Available:** Remained stable between 3.7 - 6.4 GB.
- **Process Attribution (Ambiguous):** The `llama-server.exe` Working Set metric overflowed (reporting as negative) due to 32-bit signed integer limits in PowerShell's `Get-Process` WorkingSet mapping. Additionally, the monitor aggregates all processes named `llama-server`; it cannot definitively isolate the pilot's subprocess if other servers are running globally on the host OS.

## 5. Limitations
This report must be read in conjunction with `limitations.md`. 
Specifically, the `AutomatedCoding_v1` qualification evaluates JSON API format adherence and does NOT evaluate code correctness, sandboxing, or untrusted code execution.
