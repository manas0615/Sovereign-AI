import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { CodeExecuteResponse } from '../types/api';
import { 
  Play, Terminal, Copy, Check, Sparkles, Shield, 
  RotateCcw, CheckCircle2, AlertCircle, FileCode, Layers, Cpu, Code,
  CheckCircle, XCircle, HelpCircle
} from 'lucide-react';
import clsx from 'clsx';

export function CodingStudio() {
  const [code, setCode] = useState("");
  const [executionResult, setExecutionResult] = useState<CodeExecuteResponse | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [copied, setCopied] = useState(false);

  const [aiPrompt, setAiPrompt] = useState("");
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
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [isAiGenerating, aiTask]);

  const handleAiGenerate = async () => {
    if (!aiPrompt.trim()) return;
    setIsAiGenerating(true);
    setAiTask(null);
    setAiState([]);
    setCode("Waiting for local LLM to generate implementation...");
    setExecutionResult(null);

    try {
      const task = await api.createTask({
        title: "Automated Coding Task",
        goal: aiPrompt
      });
      setAiTask(task);
      await api.runTask(task.task_id);
    } catch (e) {
      console.error(e);
      setIsAiGenerating(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // State parsing & Status Semantics
  let verificationStatus = "Not Run";
  let executionCount = 0;
  let lastOutput = "";
  let failedChecksDetail = "";
  let codeGenerated = false;
  let codeExecuted = false;

  if (aiTask) {
    const findings = aiState.filter(s => s.type === 'Finding' || s.item_type === 'finding');
    const decisions = aiState.filter(s => s.type === 'Decision' || s.item_type === 'decision');
    
    if (decisions.some(d => (d.decision === 'TOOL' || d.statement?.includes('TOOL')))) {
      codeGenerated = true;
    }

    const toolExecResults = findings.filter(s => 
      s.statement?.includes("Tool 'execute_python' returned") || 
      s.statement?.includes("Tool 'execute_python' failed")
    );
    executionCount = toolExecResults.length;
    if (executionCount > 0) {
      codeExecuted = true;
      lastOutput = toolExecResults[toolExecResults.length - 1].statement;
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
    } else if (aiTask.status === 'FAILED') {
      verificationStatus = "Verification Failed";
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

  return (
    <div className="flex flex-col h-full w-full bg-slate-950 text-slate-100 overflow-hidden select-text">
      {/* Top Bar */}
      <div className="h-14 flex items-center justify-between px-6 border-b border-slate-800/80 bg-slate-900/60 backdrop-blur flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <Terminal className="w-4 h-4 text-cyan-400" />
            <span>Governed Coding Studio (P04)</span>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
            Execution Boundary: Restricted Subprocess (No OS-level isolation)
          </span>
        </div>
      </div>

      {/* Main Split Body */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden">
        {/* Left Pane */}
        <div className="lg:col-span-4 border-r border-slate-800/80 bg-slate-900/40 p-5 overflow-y-auto space-y-6">
          
          {/* AI Code Generator Prompt */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <span>Natural-Language Coding Prompt</span>
            </div>
            <textarea
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              placeholder="e.g. Write a Python function is_valid_email(email) that validates simple email format. Include tests for valid and invalid examples. Run the tests and explain the result."
              className="w-full h-28 bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 resize-none font-sans leading-relaxed"
            />
            <button
              onClick={handleAiGenerate}
              disabled={isAiGenerating || !aiPrompt.trim()}
              className="w-full flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer shadow-sm"
            >
              {isAiGenerating ? <span className="animate-pulse">LLM Generating & Verifying...</span> : <> <Code className="w-4 h-4"/> Submit to Local LLM</>}
            </button>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2 text-xs text-slate-400">
            <div className="flex items-center gap-2 font-semibold text-slate-300">
              <Shield className="w-3.5 h-3.5 text-cyan-400" />
              <span>Restricted Subprocess Execution</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              Restricted subprocess execution with configured limits; no OS-level isolation is provided.
            </p>
          </div>

          {/* Trusted Verification Telemetry Card */}
          {aiTask && (
             <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3 text-xs">
                 <h4 className="font-semibold text-slate-200 flex items-center justify-between">
                   <span>Verification Telemetry</span>
                   <span className="text-[10px] font-mono text-slate-400">Task: {aiTask.task_id}</span>
                 </h4>
                 
                 <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                     <span className="text-slate-400">Task State</span>
                     <span className={clsx(
                       "font-mono font-bold text-xs px-2 py-0.5 rounded",
                       aiTask.status === 'COMPLETED' ? "bg-emerald-500/10 text-emerald-400" :
                       aiTask.status === 'FAILED' ? "bg-red-500/10 text-red-400" : "bg-cyan-500/10 text-cyan-400"
                     )}>{aiTask.status}</span>
                 </div>
                 
                 <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                     <span className="text-slate-400">Code Generated</span>
                     <span className="font-mono">{codeGenerated ? 'Yes (Local LLM)' : 'Pending'}</span>
                 </div>

                 <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                     <span className="text-slate-400">P04 Execution Status</span>
                     <span className="font-mono">{codeExecuted ? 'Executed (P04)' : 'Pending'}</span>
                 </div>

                 <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                     <span className="text-slate-400">Retry Attempts</span>
                     <span className="font-mono text-slate-300">{executionCount} / 3 max</span>
                 </div>

                 <div className="flex justify-between items-center pt-1">
                     <span className="text-slate-400">Trusted Verification</span>
                     <span className={clsx(
                       "font-bold font-mono text-xs px-2 py-0.5 rounded border",
                       verificationStatus === 'Verification Passed' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                       verificationStatus === 'Verification Failed' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                       'bg-amber-500/10 text-amber-400 border-amber-500/20'
                     )}>
                         {verificationStatus}
                     </span>
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

        {/* Right Pane: Code / Trace & Execution Console Output */}
        <div className="lg:col-span-8 flex flex-col h-full overflow-hidden bg-slate-950">
          {/* Action Trace Area */}
          <div className="flex-1 flex flex-col min-h-0 border-b border-slate-800">
            <div className="px-4 py-2 bg-slate-900/80 border-b border-slate-800/80 flex items-center justify-between text-xs text-slate-400 font-mono">
              <div className="flex items-center gap-2">
                <FileCode className="w-3.5 h-3.5 text-cyan-400" />
                <span>Agent Execution & Verification Trace</span>
              </div>
              <span>P05 Agent Host</span>
            </div>
            <div className="flex-1 w-full bg-slate-950 p-4 font-mono text-xs text-slate-200 overflow-y-auto whitespace-pre-wrap">
               {aiState.length > 0 ? aiState.map((s, i) => (
                   <div key={i} className="mb-2.5 border-l-2 border-slate-800 pl-3 text-[11px] space-y-0.5">
                     <div className="flex items-center gap-2">
                       <span className={clsx(
                         "font-bold",
                         s.type === 'Decision' || s.item_type === 'decision' ? "text-cyan-400" : "text-emerald-400"
                       )}>
                         {s.type || s.item_type || 'Record'}:
                       </span>
                       <span className="text-[10px] text-slate-500 font-mono">{s.created_at || ''}</span>
                     </div>
                     <div className="text-slate-300 leading-relaxed">
                       {s.rationale || s.statement || s.decision}
                     </div>
                   </div>
               )) : <span className="text-slate-600">Submit a natural-language prompt to observe local model generation and trusted verification...</span>}
            </div>
          </div>

          {/* Execution Console Area */}
          <div className="h-64 flex flex-col bg-slate-950 font-mono text-xs overflow-hidden">
            <div className="px-4 py-2 bg-slate-900 border-b border-slate-800 flex items-center justify-between text-slate-400 flex-shrink-0">
              <div className="flex items-center gap-2">
                <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                <span className="font-semibold text-slate-300">P04 Execution Output</span>
              </div>
            </div>

            <div className="flex-1 p-4 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-800 space-y-2">
                <pre className="text-emerald-300 whitespace-pre-wrap leading-relaxed text-xs">
                  {lastOutput || "No tool execution output recorded yet."}
                </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
