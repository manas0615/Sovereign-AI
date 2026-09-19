# Sovereign AI — Evidence & Scope Limitations

The findings in this evaluation report are subject to strict methodological boundaries. Claims must not be generalized beyond these limitations.

## 1. AutomatedCoding_v1 Does Not Prove Correctness or Security
The `AutomatedCoding_v1` qualification criteria exclusively evaluate JSON API formatting (schema adherence) by asserting `d.get("action") in ["TOOL", "FINAL"]`. It **does not** execute the generated Python code, it does not invoke `TrustedCodeVerifier`, and it does not validate sandbox security. Qualification confirms only that the model speaks the Sovereign AI tool dialect.

## 2. AgentDecision_v1 Does Not Evaluate Agentic Planning
The original qualification script, and this pilot which reproduces it, evaluates `AgentDecision_v1` by passing the `t_doc` test case (which requests document retrieval). This tests the model's ability to format a retrieval tool call. It **does not** test multi-step reasoning, error recovery, or complex planning.

## 3. Workflow Success vs. Algorithmic Correctness
The 150-trial coding benchmark showed 98% correctness on independent hidden evaluation tests (`final_captured_submission_passed`). However, the end-to-end agent workflow success was 0%. This was intentionally caused by the fail-closed `ExecutionBoundary` operating in `DEGRADED` mode (native Windows), which refused to execute arbitrary code and returned `Verification Inconclusive`, preventing the agent from finalizing the task.

## 4. Resource Metric Limitations
- **Peak VRAM Tracking:** The monitor polls `nvidia-smi` every two seconds. The recorded peak VRAM of 2115 MiB represents the maximum observed value across samples, not a guaranteed exact peak, as micro-spikes between samples are invisible.
- **Process Memory Ambiguity:** The `LlamaServer_WorkingSet_MB` column reports negative values due to PowerShell 32-bit signed integer overflow when measuring >2GB allocations. Furthermore, `Get-Process` aggregates all processes named `llama-server`. The metrics cannot definitively isolate the pilot's subprocess if other servers are running globally on the host OS.
- **Trial-level Mapping:** Timestamps can be manually correlated between the Python logs and the CSV, but the CSV does not contain intrinsic trial boundaries.
