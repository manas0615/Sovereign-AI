import React, { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';
import { 
  ChatResponse, CitationItem, DocumentDetailResponse, 
  CodeExecutionResult, ArtifactMetadataResponse, TrustManifestResponse 
} from '../types/api';
import { 
  Send, Bot, User, Sparkles, FileText, ChevronDown, ChevronUp, 
  Play, Terminal, Copy, Check, Shield, Download, AlertCircle, 
  Clock, Search, X, CheckCircle2, Cpu, FileSpreadsheet, Presentation
} from 'lucide-react';
import clsx from 'clsx';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: CitationItem[];
  codeExecution?: CodeExecutionResult | null;
  artifacts?: ArtifactMetadataResponse[];
  timestamp: string;
}

const SAMPLE_PROMPTS = [
  {
    icon: '🔍',
    title: 'V-204 Inspection Seal Wear',
    prompt: 'According to the uploaded vessel inspection SOP, what is the allowable seal wear tolerance, and does inspection V-204 exceed it?',
    badge: 'RAG Grounding'
  },
  {
    icon: '📊',
    title: 'Pipeline P-102 Ultrasonic Survey',
    prompt: 'Analyze ultrasonic wall thickness measurements for Pipeline P-102 and evaluate ASME B31.3 corrosion allowance (3.2mm).',
    badge: 'Corrosion Survey'
  },
  {
    icon: '💻',
    title: 'Degradation Rate Python Script',
    prompt: 'Write a Python script that parses this inspection CSV, calculates the thickness degradation rate, and generates a summary report.',
    badge: 'Python Script'
  },
  {
    icon: '⚡',
    title: 'Turbine T-501 Vibration Telemetry',
    prompt: 'Evaluate ISO 10816-3 Zone C boundary violations and bearing temperature drift for Turbine T-501.',
    badge: 'Telemetry Analysis'
  }
];

export function ChatWorkbench() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [availableDocs, setAvailableDocs] = useState<DocumentDetailResponse[]>([]);
  const [isDocModalOpen, setIsDocModalOpen] = useState(false);
  const [docSearchQuery, setDocSearchQuery] = useState('');
  const [mode, setMode] = useState<'chat' | 'coding'>('chat');
  const [copiedCodeId, setCopiedCodeId] = useState<string | null>(null);
  
  // Trust Manifest Modal
  const [activeManifestArtifactId, setActiveManifestArtifactId] = useState<string | null>(null);
  const [manifestData, setManifestData] = useState<TrustManifestResponse | null>(null);
  const [manifestLoading, setManifestLoading] = useState(false);
  
  // Citations expanded state map
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    // Load documents for search
    api.getDocuments()
      .then((docs) => setAvailableDocs(docs))
      .catch((err) => console.error('Failed to load documents:', err));

    // Listen for new chat event from sidebar
    const handleReset = () => {
      setMessages([]);
      setInput('');
      setSelectedDocId(null);
    };
    window.addEventListener('sovereign-new-chat', handleReset);
    return () => window.removeEventListener('sovereign-new-chat', handleReset);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (customPrompt?: string) => {
    const textToSend = customPrompt || input;
    if (!textToSend.trim() || loading) return;

    const userMessage: Message = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: textToSend.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!customPrompt) setInput('');
    setLoading(true);

    try {
      const response = await api.chat({
        message: textToSend.trim(),
        document_id: selectedDocId || undefined,
        mode: mode,
        execute_code: mode === 'coding' || textToSend.toLowerCase().includes('run') || textToSend.toLowerCase().includes('execute')
      });

      const assistantMessage: Message = {
        id: response.message_id,
        role: 'assistant',
        content: response.content,
        citations: response.citations,
        codeExecution: response.code_execution,
        artifacts: response.artifacts,
        timestamp: new Date(response.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: Message = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `**Execution Error:** ${err.message || 'An error occurred while processing the request.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleCitations = (msgId: string) => {
    setExpandedCitations((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const handleCopyCode = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCodeId(id);
    setTimeout(() => setCopiedCodeId(null), 2000);
  };

  const handleRunCodeSnippet = async (code: string) => {
    setLoading(true);
    try {
      const res = await api.executeCode({ code });
      const execMessage: Message = {
        id: `exec-${Date.now()}`,
        role: 'assistant',
        content: `**Sandbox Code Execution Completed (Exit Code: ${res.exit_code}):**`,
        codeExecution: {
          code: code,
          stdout: res.stdout,
          stderr: res.stderr,
          exit_code: res.exit_code,
          duration_ms: res.duration_ms,
          success: res.success,
          security_mode: res.security_mode,
          error: res.error
        },
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, execMessage]);
    } catch (err: any) {
      console.error('Code execution failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenManifest = async (artifactId: string) => {
    setActiveManifestArtifactId(artifactId);
    setManifestLoading(true);
    try {
      const manifest = await api.getTrustManifest(artifactId);
      setManifestData(manifest);
    } catch (err) {
      console.error('Failed to load trust manifest:', err);
    } finally {
      setManifestLoading(false);
    }
  };

  const selectedDoc = availableDocs.find((d) => d.document_id === selectedDocId);
  const filteredDocs = availableDocs.filter((d) => 
    d.filename.toLowerCase().includes(docSearchQuery.toLowerCase()) ||
    d.document_id.toLowerCase().includes(docSearchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full w-full bg-slate-950 text-slate-100 overflow-hidden select-text">
      {/* Top Application Bar */}
      <div className="h-14 flex items-center justify-between px-6 border-b border-slate-800/80 bg-slate-900/60 backdrop-blur flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-xs font-medium text-cyan-300">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>Llama-3.2-3B-Instruct</span>
            <span className="text-[10px] text-emerald-400 font-mono">QUALIFIED</span>
          </div>

          <div className="h-4 w-px bg-slate-800" />

          {/* Document Scope Selector Button */}
          <button
            onClick={() => setIsDocModalOpen(true)}
            className={clsx(
              "flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border cursor-pointer",
              selectedDoc
                ? "bg-cyan-950/40 text-cyan-300 border-cyan-500/40 hover:bg-cyan-900/50"
                : "bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200"
            )}
          >
            <FileText className="w-3.5 h-3.5 text-cyan-400" />
            <span className="truncate max-w-[200px]">
              {selectedDoc ? `Scope: ${selectedDoc.filename}` : "Scope: Global Knowledge Base"}
            </span>
            <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
          </button>

          {selectedDoc && (
            <button
              onClick={() => setSelectedDocId(null)}
              className="p-1 text-slate-500 hover:text-slate-300 rounded transition-colors"
              title="Clear Document Scope"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Mode Switcher */}
        <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
          <button
            onClick={() => setMode('chat')}
            className={clsx(
              "px-3 py-1 rounded-md font-medium transition-colors cursor-pointer",
              mode === 'chat' ? "bg-cyan-600 text-white shadow-sm" : "text-slate-400 hover:text-slate-200"
            )}
          >
            💬 RAG Chat
          </button>
          <button
            onClick={() => setMode('coding')}
            className={clsx(
              "px-3 py-1 rounded-md font-medium transition-colors cursor-pointer",
              mode === 'coding' ? "bg-cyan-600 text-white shadow-sm" : "text-slate-400 hover:text-slate-200"
            )}
          >
            💻 Coding Mode
          </button>
        </div>
      </div>

      {/* Main Conversation Feed */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-slate-800">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center max-w-3xl mx-auto text-center px-4 py-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/30 flex items-center justify-center mb-5 shadow-lg shadow-cyan-950/40">
              <Bot className="w-7 h-7 text-cyan-400" />
            </div>
            
            <h2 className="text-2xl font-bold text-white tracking-tight mb-2">
              Sovereign AI Conversational Workbench
            </h2>
            <p className="text-sm text-slate-400 max-w-xl mb-8 leading-relaxed">
              Ask natural-language questions grounded in local industrial inspection reports, execute bounded telemetry analysis scripts, and inspect cryptographic receipts.
            </p>

            {/* Example Prompt Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 w-full text-left">
              {SAMPLE_PROMPTS.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(item.prompt)}
                  className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/90 hover:border-cyan-500/50 hover:bg-slate-850 transition-all text-left group shadow-sm cursor-pointer"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-base">{item.icon}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                      {item.badge}
                    </span>
                  </div>
                  <h4 className="text-sm font-semibold text-slate-200 group-hover:text-cyan-300 transition-colors mb-1">
                    {item.title}
                  </h4>
                  <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                    {item.prompt}
                  </p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={clsx(
                  "flex gap-4 p-5 rounded-2xl transition-colors",
                  msg.role === 'user'
                    ? "bg-slate-900/60 border border-slate-800/80 ml-8"
                    : "bg-slate-900/90 border border-slate-800 mr-8 shadow-sm"
                )}
              >
                <div className="flex-shrink-0">
                  {msg.role === 'user' ? (
                    <div className="w-8 h-8 rounded-lg bg-cyan-600/30 border border-cyan-500/40 flex items-center justify-center text-cyan-300 font-semibold text-xs">
                      <User className="w-4 h-4" />
                    </div>
                  ) : (
                    <div className="w-8 h-8 rounded-lg bg-emerald-600/30 border border-emerald-500/40 flex items-center justify-center text-emerald-300 font-semibold text-xs">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}
                </div>

                <div className="flex-1 space-y-3.5 min-w-0">
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span className="font-semibold text-slate-300">
                      {msg.role === 'user' ? 'You' : 'Sovereign AI Assistant'}
                    </span>
                    <span className="font-mono text-[11px] text-slate-500">{msg.timestamp}</span>
                  </div>

                  {/* Message Content */}
                  <div className="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed space-y-2">
                    {msg.content}
                  </div>

                  {/* Supporting Evidence / Citations Accordion */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-slate-800">
                      <button
                        onClick={() => toggleCitations(msg.id)}
                        className="flex items-center justify-between w-full p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 text-xs text-cyan-400 hover:text-cyan-300 hover:border-cyan-500/40 transition-all"
                      >
                        <div className="flex items-center gap-2 font-medium">
                          <Shield className="w-4 h-4 text-cyan-400" />
                          <span>Grounded Source Evidence ({msg.citations.length} cited knowledge chunk{msg.citations.length > 1 ? 's' : ''})</span>
                        </div>
                        {expandedCitations[msg.id] ? (
                          <ChevronUp className="w-4 h-4 text-slate-400" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-slate-400" />
                        )}
                      </button>

                      {expandedCitations[msg.id] && (
                        <div className="mt-2.5 space-y-2">
                          {msg.citations.map((c, idx) => (
                            <div key={idx} className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-1.5 text-xs">
                              <div className="flex items-center justify-between">
                                <span className="font-semibold text-slate-200">{c.filename}</span>
                                <span className="font-mono text-[10px] text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-500/30">
                                  Score: {Math.round(c.score * 100) / 100}
                                </span>
                              </div>
                              <p className="text-slate-300 italic bg-slate-900/60 p-2.5 rounded border border-slate-800/60 text-xs">
                                "{c.text.trim()}"
                              </p>
                              <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                                <span>Chunk: {c.chunk_id.substring(0, 12)}...</span>
                                {c.content_hash && <span>SHA: {c.content_hash.substring(0, 12)}...</span>}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Code Execution Result Console */}
                  {msg.codeExecution && (
                    <div className="mt-4 rounded-xl bg-slate-950 border border-slate-800 overflow-hidden text-xs font-mono">
                      <div className="px-4 py-2 bg-slate-900 border-b border-slate-800 flex items-center justify-between text-slate-400">
                        <div className="flex items-center gap-2">
                          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                          <span className="font-semibold text-slate-300">Governed Sandbox Execution (P04)</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                            Exit Code: {msg.codeExecution.exit_code}
                          </span>
                          <span>{msg.codeExecution.duration_ms}ms</span>
                        </div>
                      </div>

                      {msg.codeExecution.stdout && (
                        <div className="p-4 bg-slate-950 text-emerald-400 whitespace-pre-wrap">
                          {msg.codeExecution.stdout}
                        </div>
                      )}

                      {msg.codeExecution.stderr && (
                        <div className="p-4 bg-red-950/20 text-red-400 border-t border-slate-800 whitespace-pre-wrap">
                          {msg.codeExecution.stderr}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Deliverables Card */}
                  {msg.artifacts && msg.artifacts.length > 0 && (
                    <div className="mt-4 p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                          Generated Deliverables ({msg.artifacts.length})
                        </h4>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                        {msg.artifacts.map((art) => (
                          <div
                            key={art.artifact_id}
                            className="p-3 bg-slate-900 border border-slate-800 rounded-lg flex items-center justify-between gap-3"
                          >
                            <div className="truncate flex-1">
                              <p className="text-xs font-medium text-white truncate">{art.title}</p>
                              <p className="text-[10px] text-slate-400 uppercase font-mono">{art.type}</p>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <button
                                onClick={() => handleOpenManifest(art.artifact_id)}
                                className="px-2 py-1 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 text-[11px] rounded border border-cyan-500/30 transition-colors"
                              >
                                Receipt
                              </button>
                              <a
                                href={api.getArtifactDownloadUrl(art.artifact_id)}
                                download
                                className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded transition-colors"
                                title="Download File"
                              >
                                <Download className="w-3.5 h-3.5" />
                              </a>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-3 p-4 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 text-xs font-mono mr-8">
                <div className="w-3 h-3 rounded-full bg-cyan-400 animate-ping" />
                <span>Characterizing intent (P05) → Evaluating qualification (P08) → Retrieving evidence (P03)...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Message Composer */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-900/60 backdrop-blur flex-shrink-0">
        <div className="max-w-4xl mx-auto relative">
          <div className="bg-slate-900 border border-slate-700/80 rounded-2xl shadow-xl overflow-hidden focus-within:border-cyan-500/70 focus-within:ring-2 focus-within:ring-cyan-500/20 transition-all">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                mode === 'coding'
                  ? "Describe the analysis or Python script to generate and execute..."
                  : "Ask a question about uploaded inspection reports, tolerances, or specifications..."
              }
              rows={2}
              className="w-full bg-transparent px-4 py-3 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none resize-none"
            />

            <div className="px-3 py-2 bg-slate-950/60 border-t border-slate-800/60 flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
                <span>Enter to send • Shift+Enter for newline</span>
                {selectedDoc && (
                  <span className="text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-500/30">
                    Bound: {selectedDoc.filename}
                  </span>
                )}
              </div>

              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || loading}
                className="flex items-center gap-2 px-4 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer shadow-sm"
              >
                <span>Send</span>
                <Send className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Compact Document Scope Selection Modal */}
      {isDocModalOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-xl w-full max-h-[80vh] overflow-hidden shadow-2xl flex flex-col">
            <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-semibold text-white">Select Grounding Knowledge Scope</h3>
              </div>
              <button
                onClick={() => setIsDocModalOpen(false)}
                className="p-1 text-slate-400 hover:text-white rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 border-b border-slate-800 bg-slate-950">
              <div className="relative">
                <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="text"
                  value={docSearchQuery}
                  onChange={(e) => setDocSearchQuery(e.target.value)}
                  placeholder="Search indexed documents by filename or ID..."
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              <button
                onClick={() => {
                  setSelectedDocId(null);
                  setIsDocModalOpen(false);
                }}
                className={clsx(
                  "w-full text-left p-3 rounded-lg border transition-all flex items-center justify-between text-xs",
                  selectedDocId === null
                    ? "bg-cyan-500/15 border-cyan-500/40 text-cyan-300 font-semibold"
                    : "bg-slate-950 border-slate-800 text-slate-300 hover:bg-slate-800"
                )}
              >
                <div className="flex items-center gap-2.5">
                  <Sparkles className="w-4 h-4 text-cyan-400" />
                  <div>
                    <p className="font-medium">Global Knowledge Base (All Documents)</p>
                    <p className="text-[11px] text-slate-500 font-normal">FTS5 full-text index across all indexed knowledge</p>
                  </div>
                </div>
                {selectedDocId === null && <Check className="w-4 h-4 text-cyan-400" />}
              </button>

              {filteredDocs.map((doc) => {
                const isSelected = selectedDocId === doc.document_id;
                return (
                  <button
                    key={doc.document_id}
                    onClick={() => {
                      setSelectedDocId(doc.document_id);
                      setIsDocModalOpen(false);
                    }}
                    className={clsx(
                      "w-full text-left p-3 rounded-lg border transition-all flex items-center justify-between text-xs",
                      isSelected
                        ? "bg-cyan-500/15 border-cyan-500/40 text-cyan-300 font-semibold"
                        : "bg-slate-950 border-slate-800 text-slate-300 hover:bg-slate-800"
                    )}
                  >
                    <div className="flex items-center gap-2.5 truncate">
                      <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      <div className="truncate">
                        <p className="font-medium truncate">{doc.filename}</p>
                        <p className="text-[10px] text-slate-500 font-mono">
                          ID: {doc.document_id} • {(doc.file_size / 1024).toFixed(1)} KB • {doc.document_type.toUpperCase()}
                        </p>
                      </div>
                    </div>
                    {isSelected && <Check className="w-4 h-4 text-cyan-400 flex-shrink-0" />}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Trust Manifest Receipt Modal */}
      {activeManifestArtifactId && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto shadow-2xl flex flex-col p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-cyan-400" />
                <h3 className="text-base font-semibold text-white">Cryptographic Trust Receipt</h3>
              </div>
              <button
                onClick={() => setActiveManifestArtifactId(null)}
                className="p-1 text-slate-400 hover:text-white rounded transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {manifestLoading ? (
              <div className="py-12 text-center text-sm text-slate-400">Loading receipt...</div>
            ) : manifestData ? (
              <div className="space-y-4 text-xs font-mono">
                <div className="p-3 bg-emerald-950/30 border border-emerald-500/40 rounded-xl flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="text-emerald-300 font-semibold">Byte Integrity Verified</span>
                    <p className="text-slate-300 font-sans mt-0.5">
                      SHA-256 digest allows comparison against recorded local execution state.
                    </p>
                  </div>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                  <div>
                    <span className="text-slate-500">Deliverable Content Hash (SHA-256):</span>
                    <p className="text-cyan-300 break-all">{manifestData.artifact?.content_hash || manifestData.content_hash || 'N/A'}</p>
                  </div>
                  <div className="flex justify-between pt-2 border-t border-slate-800">
                    <span className="text-slate-500">Passport:</span>
                    <span className="text-slate-300">{manifestData.qualification?.passport_id || manifestData.authorizing_passport_id || 'psp-qualified'}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-slate-800">
                    <span className="text-slate-500">Capability</span>
                    <span className="text-slate-300">{manifestData.capability?.name || manifestData.capability_contract || 'Unknown'}</span>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
