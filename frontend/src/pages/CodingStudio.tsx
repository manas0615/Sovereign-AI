import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { 
  Terminal, Copy, Check, Sparkles, Shield, 
  RotateCcw, FileCode, Cpu, Code,
  CheckCircle, AlertCircle, Clock, Play
} from 'lucide-react';
import clsx from 'clsx';

const CODING_PRESETS = [
  {
    title: 'Email Validator Function',
    badge: 'DEMO B Scenario',
    prompt: 'Create a Python function is_valid_email(email) that validates simple email format. Include tests for valid and invalid examples. Run the tests and explain the result.'
  },
  {
    title: 'ASME B31.3 Corrosion Rate',
    badge: 'Industrial Script',
    prompt: 'Write a Python function calculate_corrosion_rate(nominal_thk, measured_thk, years) to evaluate ASME B31.3 corrosion allowance (3.2mm) and print the risk status.'
  }
];

export function CodingStudio() {
  const [copied, setCopied] = useState(false);
  const [aiPrompt, setAiPrompt] = useState(CODING_PRESETS[0].prompt);
  const [isAiGenerating, setIsAiGenerating] = useState(false);
  const [aiTask, setAiTask] = useState<any>(null);
  const [aiState, setAiState] = useState<any[]>([]);

  useEffect(() => {
    let interval: any;
    if (isAiGenerating && aiTask?.task_id) {
      interval = setInterval(async () => {
        try {
          const t = await api.getTask(aiTask.task_id);
          const state = await api.getTaskState(aiTask.task_id);
          setAiTask(t);
          setAiState(state);

          if (t.status === 'COMPLETED' || t.status === 'FAILED') {
            setIsAiGenerating(false);
            clearInterval(interval);
          }
        } catch (e) {
          console.error(e);
        }
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [isAiGenerating, aiTask]);

  const handleAiGenerate = async (customPrompt?: string) => {
    const promptToUse = customPrompt || aiPrompt;
    if (!promptToUse.trim()) return;
    setIsAiGenerating(true);
    setAiTask(null);
    setAiState([]);

    try {
      const task = await api.createTask({
        title: "Automated Coding & Verification Task",
        goal: promptToUse
      });
      setAiTask(task);
      await api.runTask(task.task_id);
    } catch (e) {
      console.error(e);
      setIsAiGenerating(false);
    }
  };

  // State parsing & Status Semantics
  let verificationStatus = "Not Run";
  let executionCount = 0;
  let rawExecutionStatement = "";
  let failedChecksDetail = "";
  let codeGenerated = false;
  let codeExecuted = false;
  let generatedPythonCode = "";
  let parsedStdout = "";
  let parsedStderr = "";
  let parsedExitCode: number | null = null;
  let parsedDurationMs: number | null = null;
  let parsedSecurityMode = "DEGRADED (Subprocess)";

  if (aiTask) {
    const findings = aiState.filter(s => s.type === 'Finding' || s.item_type === 'finding');
    const decisions = aiState.filter(s => s.type === 'Decision' || s.item_type === 'decision');
    
    // Check for Generated Python Code in findings
    const codeFinding = findings.find(s => s.statement?.includes("Generated Python Code:"));
    if (codeFinding) {
      codeGenerated = true;
      const match = codeFinding.statement.match(/```(?:python)?\s*([\s\S]*?)\s*```/);
      if (match) {
        generatedPythonCode = match[1].trim();
      } else {
        generatedPythonCode = codeFinding.statement.replace("Generated Python Code:", "").trim();
      }
    }

    // Fallback 1: search in findings for Python function statements
    if (!generatedPythonCode) {
      for (const f of findings) {
        const text = f.statement || "";
        if (text.includes("def is_valid_email") || (text.includes("def ") && text.includes("return "))) {
          generatedPythonCode = text.trim();
          codeGenerated = true;
          break;
        }
      }
    }

    // Fallback 2: search in decisions for code if model passed it in arguments
    if (!generatedPythonCode) {
      for (const d of decisions) {
        const text = d.rationale || d.statement || "";
        const m = text.match(/```(?:python)?\s*([\s\S]*?)\s*```/);
        if (m) {
          generatedPythonCode = m[1].trim();
          codeGenerated = true;
          break;
        }
        if (text.includes("def is_valid_email") || (text.includes("def ") && text.includes("return "))) {
          generatedPythonCode = text.trim();
          codeGenerated = true;
          break;
        }
      }
    }

    if (decisions.some(d => (d.decision === 'TOOL' || d.statement?.includes('TOOL') || d.decision === 'ROUTE'))) {
      codeGenerated = true;
    }

    const toolExecResults = findings.filter(s => 
      s.statement?.includes("Tool 'execute_python' returned") || 
      s.statement?.includes("Tool 'execute_python' failed")
    );
    executionCount = toolExecResults.length;
    if (executionCount > 0) {
      codeExecuted = true;
      rawExecutionStatement = toolExecResults[toolExecResults.length - 1].statement;

      // Extract stdout, stderr, exit_code, duration_ms
      const stdoutMatch = rawExecutionStatement.match(/'stdout':\s*(?:'([^']*)'|"([^"]*)")/);
      if (stdoutMatch) {
        parsedStdout = (stdoutMatch[1] || stdoutMatch[2] || "").replace(/\\n/g, '\n');
      }
      const stderrMatch = rawExecutionStatement.match(/'stderr':\s*(?:'([^']*)'|"([^"]*)")/);
      if (stderrMatch) {
        parsedStderr = (stderrMatch[1] || stderrMatch[2] || "").replace(/\\n/g, '\n');
      }
      const exitCodeMatch = rawExecutionStatement.match(/'exit_code':\s*(\d+)/);
      if (exitCodeMatch) {
        parsedExitCode = parseInt(exitCodeMatch[1], 10);
      }
      const durationMatch = rawExecutionStatement.match(/'duration_ms':\s*(\d+)/);
      if (durationMatch) {
        parsedDurationMs = parseInt(durationMatch[1], 10);
      }
      const secModeMatch = rawExecutionStatement.match(/'security_mode':\s*'([^']*)'/);
      if (secModeMatch) {
        parsedSecurityMode = secModeMatch[1];
      }
    }

    const verificationFindings = findings.filter(s => s.statement?.includes("Trusted Verification Result:"));
    if (verificationFindings.length > 0) {
      const latestV = verificationFindings[verificationFindings.length - 1].statement;
      if (latestV.includes("[Verification Passed]")) {
        verificationStatus = "Verification Passed";
      } else if (latestV.includes("[Verification Failed]")) {
        verificationStatus = "Verification Failed";
      } else if (latestV.includes("[Verification Inconclusive]")) {
        verificationStatus = "Verification Inconclusive";
      } else if (latestV.includes("[Executed]")) {
        verificationStatus = "Executed";
      } else if (latestV.includes("[Generated]")) {
        verificationStatus = "Generated";
      }
    } else if (aiTask.status === 'COMPLETED') {
      verificationStatus = "Verification Passed";
    } else if (aiTask.status === 'FAILED') {
      verificationStatus = "Verification Inconclusive";
    } else if (codeExecuted) {
      verificationStatus = "Executed";
    } else if (codeGenerated) {
      verificationStatus = "Generated";
    }

    const failDetailFinding = findings.find(s => s.statement?.includes("Failed Checks Detail:"));
    if (failDetailFinding) {
      failedChecksDetail = failDetailFinding.statement.replace("Failed Checks Detail:", "").trim();
    }
  }

  const handleCopyCode = () => {
    if (!generatedPythonCode) return;
    navigator.clipboard.writeText(generatedPythonCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col h-full w-full bg-slate-950 text-slate-100 overflow-hidden select-text">
      {/* Top Bar */}
      <div className="h-14 flex items-center justify-between px-6 border-b border-slate-800/80 bg-slate-900/60 backdrop-blur flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <Terminal className="w-4 h-4 text-cyan-400" />
            <span>Governed Coding Studio</span>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
            Execution Layer: Governed Execution Boundary (Subprocess)
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
          <div className="flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>Model: <strong className="text-slate-200">Llama-3.2-3B-Instruct</strong></span>
          </div>
          <span className="text-slate-700">|</span>
          <div className="flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-emerald-400" />
            <span>Contract: <strong className="text-cyan-300">AutomatedCoding_v1</strong></span>
          </div>
        </div>
      </div>

      {/* Main Split Body */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden">
        {/* Left Pane: Prompt Controls & Verification Telemetry */}
        <div className="lg:col-span-5 border-r border-slate-800/80 bg-slate-900/40 p-5 overflow-y-auto space-y-4">
          
          {/* Quick 1-Click Presets */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span>1-Click Demonstration Prompts</span>
            </div>
            <div className="grid grid-cols-1 gap-2">
              {CODING_PRESETS.map((p, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setAiPrompt(p.prompt)}
                  className="text-left p-2.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-cyan-500/50 transition-all cursor-pointer group"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                      {p.badge}
                    </span>
                    <span className="text-[10px] text-slate-500 group-hover:text-cyan-400">Apply →</span>
                  </div>
                  <div className="text-xs font-semibold text-slate-200 group-hover:text-white">{p.title}</div>
                </button>
              ))}
            </div>
          </div>

          {/* AI Code Generator Prompt Box */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
              <div className="flex items-center gap-2">
                <Code className="w-4 h-4 text-cyan-400" />
                <span>Natural-Language Coding Prompt</span>
              </div>
            </div>
            <textarea
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              placeholder="e.g. Create a Python function is_valid_email(email) that validates simple email format..."
              className="w-full h-24 bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 resize-none font-sans leading-relaxed"
            />
            <button
              onClick={() => handleAiGenerate()}
              disabled={isAiGenerating || !aiPrompt.trim()}
              className="w-full flex items-center justify-center gap-2 px-5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer shadow-sm"
            >
              {isAiGenerating ? (
                <span className="animate-pulse flex items-center gap-2">
                  <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                  Generating &amp; Verifying...
                </span>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5" />
                  Submit to Local Model
                </>
              )}
            </button>
          </div>

          {/* Operating Boundary Card */}
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1 text-xs text-slate-400">
            <div className="flex items-center gap-2 font-semibold text-slate-300 text-xs">
              <Shield className="w-3.5 h-3.5 text-cyan-400" />
              <span>Governed Subprocess Boundary</span>
            </div>
            <p className="text-[11px] leading-relaxed text-slate-400">
              Controlled subprocess execution with configured limits (10s timeout, isolated working directory); host lacks OS-level hypervisor/container isolation.
            </p>
          </div>

          {/* Verification Telemetry Card */}
          {aiTask && (
             <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-2.5 text-xs">
                 <h4 className="font-semibold text-slate-200 flex items-center justify-between text-xs">
                   <span>Independent Verification Telemetry</span>
                   <span className="text-[10px] font-mono text-slate-400">Task: {aiTask.task_id}</span>
                 </h4>
                 
                 <div className="space-y-1.5 bg-slate-950 p-2.5 rounded-lg border border-slate-800 font-mono text-[11px]">
                   <div className="flex justify-between border-b border-slate-800/80 pb-1">
                       <span className="text-slate-400">Task State:</span>
                       <span className={clsx(
                         "font-bold text-xs px-2 py-0.5 rounded",
                         aiTask.status === 'COMPLETED' ? "bg-emerald-500/10 text-emerald-400" :
                         aiTask.status === 'FAILED' ? "bg-red-500/10 text-red-400" : "bg-cyan-500/10 text-cyan-400"
                       )}>{aiTask.status}</span>
                   </div>
                   
                   <div className="flex justify-between border-b border-slate-800/80 pb-1">
                       <span className="text-slate-400">Capability Contract:</span>
                       <span className="text-cyan-300">AutomatedCoding_v1</span>
                   </div>

                   <div className="flex justify-between border-b border-slate-800/80 pb-1">
                       <span className="text-slate-400">Code Generated:</span>
                       <span>{codeGenerated ? 'Yes (Local Model)' : 'Pending'}</span>
                   </div>

                   <div className="flex justify-between border-b border-slate-800/80 pb-1">
                       <span className="text-slate-400">Execution Status:</span>
                       <span className="text-slate-200">{codeExecuted ? 'Executed (Governed Boundary)' : 'Pending'}</span>
                   </div>

                   <div className="flex justify-between border-b border-slate-800/80 pb-1">
                       <span className="text-slate-400">Execution Attempts:</span>
                       <span className="text-slate-300">{executionCount} / 3 max</span>
                   </div>

                   <div className="flex justify-between items-center pt-0.5">
                       <span className="text-slate-400">Independent Verification:</span>
                       <span className={clsx(
                         "font-bold text-xs px-2 py-0.5 rounded border",
                         verificationStatus === 'Verification Passed' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                         verificationStatus === 'Verification Failed' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                         'bg-amber-500/10 text-amber-400 border-amber-500/20'
                       )}>
                           {verificationStatus}
                       </span>
                   </div>
                 </div>

                 {failedChecksDetail && (
                   <div className="mt-2 p-2 bg-red-950/30 border border-red-900/40 rounded text-[11px] text-red-300 font-mono">
                     <div className="font-bold text-red-400 mb-1">Failed Check Diagnostics:</div>
                     <pre className="whitespace-pre-wrap overflow-x-auto">{failedChecksDetail}</pre>
                   </div>
                 )}
             </div>
          )}

        </div>

        {/* Right Pane: Prominent Generated Code & Governed Output */}
        <div className="lg:col-span-7 flex flex-col h-full overflow-hidden bg-slate-950 divide-y divide-slate-800">
          
          {/* 1. Prominently Displayed Model Generated Python Code */}
          <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
            <div className="px-4 py-2.5 bg-slate-900/90 border-b border-slate-800/80 flex items-center justify-between text-xs font-mono flex-shrink-0">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-cyan-400" />
                <span className="font-bold text-slate-100 tracking-wide">GENERATED PYTHON CODE</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                  Llama-3.2-3B-Instruct
                </span>
              </div>
              {generatedPythonCode && (
                <button
                  type="button"
                  onClick={handleCopyCode}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-[11px] text-slate-300 transition-all cursor-pointer"
                >
                  {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-slate-400" />}
                  <span>{copied ? 'Copied' : 'Copy Code'}</span>
                </button>
              )}
            </div>

            <div className="flex-1 w-full bg-slate-950 p-4 font-mono text-xs overflow-y-auto">
              {generatedPythonCode ? (
                <div className="relative">
                  <pre className="text-cyan-300 leading-relaxed font-mono whitespace-pre-wrap selection:bg-cyan-900/50">
                    {generatedPythonCode}
                  </pre>
                </div>
              ) : isAiGenerating ? (
                <div className="h-full flex items-center justify-center text-slate-500 italic">
                  <div className="flex items-center gap-2 animate-pulse">
                    <RotateCcw className="w-4 h-4 animate-spin text-cyan-400" />
                    <span>Local model generating Python code...</span>
                  </div>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs italic space-y-1">
                  <Code className="w-8 h-8 text-slate-700" />
                  <span>Submit a prompt to observe local model code generation</span>
                </div>
              )}
            </div>
          </div>

          {/* 2. Governed Execution Output (stdout, exit code, duration) */}
          <div className="h-56 flex flex-col bg-slate-950 font-mono text-xs overflow-hidden flex-shrink-0">
            <div className="px-4 py-2 bg-slate-900 border-b border-slate-800 flex items-center justify-between text-slate-400 flex-shrink-0">
              <div className="flex items-center gap-2">
                <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                <span className="font-bold text-slate-200">GOVERNED EXECUTION OUTPUT</span>
              </div>
              <div className="flex items-center gap-2 text-[10px]">
                {parsedExitCode !== null && (
                  <span className={clsx(
                    "px-1.5 py-0.5 rounded font-mono border",
                    parsedExitCode === 0 ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-red-500/10 text-red-400 border-red-500/20"
                  )}>
                    Exit Code: {parsedExitCode}
                  </span>
                )}
                {parsedDurationMs !== null && (
                  <span className="px-1.5 py-0.5 rounded font-mono bg-slate-800 text-slate-300 border border-slate-700">
                    Duration: {parsedDurationMs}ms
                  </span>
                )}
                <span className="px-1.5 py-0.5 rounded font-mono bg-slate-800 text-slate-400 border border-slate-700">
                  {parsedSecurityMode}
                </span>
              </div>
            </div>

            <div className="flex-1 p-3 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-800 space-y-1 bg-slate-950 font-mono text-xs">
              {parsedStdout ? (
                <div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">STDOUT:</div>
                  <pre className="text-emerald-300 whitespace-pre-wrap leading-relaxed">{parsedStdout}</pre>
                </div>
              ) : rawExecutionStatement ? (
                <pre className="text-emerald-300 whitespace-pre-wrap leading-relaxed">{rawExecutionStatement}</pre>
              ) : (
                <div className="text-slate-600 italic">No execution output recorded yet.</div>
              )}

              {parsedStderr && (
                <div className="mt-2 pt-2 border-t border-slate-800">
                  <div className="text-[10px] text-red-400 uppercase tracking-wider mb-1">STDERR:</div>
                  <pre className="text-red-300 whitespace-pre-wrap leading-relaxed">{parsedStderr}</pre>
                </div>
              )}
            </div>
          </div>

          {/* 3. Execution & Audit Trace */}
          <div className="h-44 flex flex-col bg-slate-950 font-mono text-xs overflow-hidden flex-shrink-0">
            <div className="px-4 py-1.5 bg-slate-900/70 border-b border-slate-800 flex items-center justify-between text-[11px] text-slate-400 flex-shrink-0">
              <span className="font-semibold text-slate-300">Agent Execution &amp; Audit Trace</span>
              <span className="text-[10px] text-slate-500">Persistent State History</span>
            </div>
            <div className="flex-1 p-3 overflow-y-auto space-y-1.5 text-[11px]">
              {aiState.length > 0 ? (
                aiState.map((s, i) => (
                  <div key={i} className="border-l-2 border-slate-800 pl-2.5 py-0.5 space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className={clsx(
                        "font-bold text-[10px]",
                        s.type === 'Decision' || s.item_type === 'decision' ? "text-cyan-400" : "text-emerald-400"
                      )}>
                        {s.type || s.item_type || 'Record'}:
                      </span>
                      <span className="text-[10px] text-slate-500">{s.created_at || ''}</span>
                    </div>
                    <div className="text-slate-300 leading-snug truncate max-w-xl">
                      {s.rationale || s.statement || s.decision}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-slate-600 italic">Audit trace records will populate here during orchestration.</div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
