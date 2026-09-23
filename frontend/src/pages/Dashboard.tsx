import React, { useEffect, useState } from 'react';
import { useHealth } from '../hooks/useHealth';
import { Link } from 'react-router-dom';
import { PlusSquare, BookOpen, Activity, Shield, Award, ArrowRight, CheckCircle2, Clock, XCircle, FileText, ChevronRight } from 'lucide-react';
import { api } from '../api/client';
import { CapabilityPassportResponse, TaskResponse, DocumentDetailResponse } from '../types/api';
import clsx from 'clsx';

export function Dashboard() {
  const health = useHealth();
  const isHealthy = health?.status?.toUpperCase() === 'HEALTHY';
  const [passports, setPassports] = useState<CapabilityPassportResponse[]>([]);
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [documents, setDocuments] = useState<DocumentDetailResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [passportsData, tasksData, docsData] = await Promise.all([
          api.getPassports().catch(() => []),
          api.getTasks().catch(() => []),
          api.getDocuments().catch(() => [])
        ]);
        setPassports(passportsData);
        setTasks(tasksData);
        setDocuments(docsData);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'ACTIVE': return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
      case 'FAILED': return 'bg-red-500/10 text-red-400 border-red-500/20';
      default: return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 p-8 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Sovereign AI Governance Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1">Local-first, qualification-gated agentic AI workbench for confidential industrial work.</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800">
          <span className="text-xs text-slate-400">Environment:</span>
          <span className="text-xs font-medium text-emerald-400">Localhost (Offline Bounded)</span>
        </div>
      </div>

      {/* Core Principle Banner */}
      <div className="mb-8 p-6 bg-gradient-to-r from-slate-900 via-cyan-950/30 to-slate-900 border border-cyan-500/30 rounded-2xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-xs font-medium mb-3">
              <Award className="w-3.5 h-3.5" />
              <span>Core Architectural Invariant: Configuration ≠ Qualification ≠ Authority</span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              &ldquo;Local is where the model runs. Qualified is why the model is allowed to act.&rdquo;
            </h2>
            <p className="text-sm text-slate-300 mt-2 max-w-3xl leading-relaxed">
              Capability is never assumed from local weights. Deployments undergo empirical capability testing to receive a Capability Passport before being granted task-scoped execution authority.
            </p>
          </div>
          <Link
            to="/moon"
            className="flex-shrink-0 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500 text-slate-950 font-medium text-sm hover:bg-cyan-400 transition-colors"
          >
            <span>Explore Architecture</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <Activity className="w-5 h-5 text-slate-400" />
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider">Runtime Status</h3>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-2.5 h-2.5 rounded-full ${isHealthy ? 'bg-emerald-500' : 'bg-red-500'}`} />
            <span className={`text-lg font-bold ${isHealthy ? 'text-white' : 'text-red-400'}`}>
              {health ? health.status : 'Connecting...'}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Model Runtime (P01)</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <Shield className="w-5 h-5 text-cyan-400" />
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider">Passports</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-white">
              {loading ? '...' : passports.length}
            </span>
            <span className="text-xs text-slate-400">qualified contracts</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Qualification &amp; Authority</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <Clock className="w-5 h-5 text-indigo-400" />
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider">Governed Tasks</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-white">
              {loading ? '...' : tasks.length}
            </span>
            <span className="text-xs text-slate-400">persisted tasks</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Controlled Orchestration</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <BookOpen className="w-5 h-5 text-emerald-400" />
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider">Knowledge Base</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-white">
              {loading ? '...' : documents.length}
            </span>
            <span className="text-xs text-slate-400">indexed documents</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">OCR &amp; SQLite FTS5</p>
        </div>
      </div>

      {/* Recent Governed Tasks Section */}
      <div className="mb-8 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-3">
            <Clock className="w-5 h-5 text-cyan-400" />
            <h2 className="text-base font-semibold text-white">Recent Governed Tasks</h2>
          </div>
          <Link to="/tasks/new" className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-medium">
            <span>+ Create New Task</span>
          </Link>
        </div>

        <div className="p-4">
          {loading ? (
            <div className="py-8 text-center text-sm text-slate-500">Loading tasks...</div>
          ) : tasks.length === 0 ? (
            <div className="py-8 text-center space-y-3">
              <p className="text-sm text-slate-400">No governed tasks created yet.</p>
              <Link
                to="/tasks/new"
                className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-lg transition-colors"
              >
                <PlusSquare className="w-4 h-4" />
                Launch Flagship Demo Task
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {tasks.slice(0, 5).map((t) => (
                <div key={t.task_id} className="py-3 px-2 flex items-center justify-between hover:bg-slate-800/40 rounded-lg transition-colors">
                  <div className="flex items-start gap-3 min-w-0">
                    <FileText className="w-4 h-4 text-slate-400 mt-1 flex-shrink-0" />
                    <div className="truncate">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-white truncate">{t.title}</span>
                        <span className={clsx("px-2 py-0.5 rounded text-[10px] font-semibold border", getStatusBadge(t.status))}>
                          {t.status}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
                        <span className="font-mono text-[11px]">ID: {t.task_id}</span>
                        {t.document_id && <span className="text-cyan-400">Doc: {t.document_id}</span>}
                        <span>Findings: {t.findings_count}</span>
                      </div>
                    </div>
                  </div>
                  <Link
                    to={`/tasks/${t.task_id}`}
                    className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs font-medium rounded-md transition-colors ml-4 border border-slate-700"
                  >
                    <span>View Execution &amp; Deliverables</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Ingested Documents & Qualified Deployments Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Ingested Documents Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
            <div className="flex items-center gap-3">
              <BookOpen className="w-5 h-5 text-emerald-400" />
              <h2 className="text-base font-semibold text-white">Ingested Knowledge Documents</h2>
            </div>
            <Link to="/knowledge" className="text-xs text-emerald-400 hover:text-emerald-300 font-medium">
              + Ingest File
            </Link>
          </div>
          <div className="p-4">
            {documents.length === 0 ? (
              <div className="py-6 text-center text-sm text-slate-500">
                No documents uploaded yet. Upload a scanned inspection PDF in the Knowledge Base.
              </div>
            ) : (
              <div className="space-y-2.5">
                {documents.slice(0, 4).map((doc) => (
                  <div key={doc.document_id} className="p-3 bg-slate-950 border border-slate-800/80 rounded-lg flex items-center justify-between">
                    <div className="truncate">
                      <p className="text-sm font-medium text-slate-200 truncate">{doc.filename}</p>
                      <div className="flex items-center gap-2 text-[11px] text-slate-500 font-mono mt-0.5">
                        <span>ID: {doc.document_id}</span>
                        <span>•</span>
                        <span className="uppercase">{doc.document_type}</span>
                        <span>•</span>
                        <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
                      </div>
                    </div>
                    <Link
                      to={`/tasks/new?document_id=${doc.document_id}&title=${encodeURIComponent('Analysis of ' + doc.filename)}`}
                      className="flex-shrink-0 px-2.5 py-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 text-xs font-semibold rounded border border-emerald-500/30 transition-colors ml-3"
                    >
                      Run Task
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Qualified Deployments Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
            <div className="flex items-center gap-3">
              <Shield className="w-5 h-5 text-cyan-400" />
              <h2 className="text-base font-semibold text-white">Active Capability Passports</h2>
            </div>
            <Link to="/passports" className="text-xs text-cyan-400 hover:text-cyan-300 font-medium">
              View All
            </Link>
          </div>
          <div className="p-4">
            {passports.length === 0 ? (
              <div className="py-6 text-center text-sm text-slate-500">
                No capability passports found.
              </div>
            ) : (
              <div className="space-y-2.5">
                {passports.slice(0, 4).map((p) => {
                  const isQualified = p.qualification_status === 'QUALIFIED';
                  return (
                    <div key={p.passport_id} className="p-3 bg-slate-950 border border-slate-800/80 rounded-lg flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm text-white">{p.capability_contract}</span>
                          <span className={clsx(
                            "px-2 py-0.5 rounded text-[10px] font-semibold border",
                            isQualified ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-red-500/10 text-red-400 border-red-500/20"
                          )}>
                            {p.qualification_status}
                          </span>
                        </div>
                        <p className="text-[11px] font-mono text-slate-400 mt-0.5 truncate max-w-[240px]">
                          {p.deployment_identity}
                        </p>
                      </div>
                      <span className="text-xs font-mono text-cyan-400 flex-shrink-0 ml-2">
                        {p.passport_id.substring(0, 10)}...
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Action Cards */}
      <h2 className="text-lg font-medium text-white mb-4">Workbench Workflows</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link to="/tasks/new" className="group flex items-start gap-4 p-5 bg-slate-900 border border-slate-800 rounded-xl hover:border-cyan-500/50 transition-colors">
          <div className="p-3 bg-cyan-500/10 rounded-lg group-hover:bg-cyan-500/20 transition-colors">
            <PlusSquare className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <h3 className="text-base font-medium text-white mb-1">Create Governed Task</h3>
            <p className="text-xs text-slate-400">Match task capabilities, issue authority decision, and execute fail-closed with deliverable generation.</p>
          </div>
        </Link>
        
        <Link to="/knowledge" className="group flex items-start gap-4 p-5 bg-slate-900 border border-slate-800 rounded-xl hover:border-cyan-500/50 transition-colors">
          <div className="p-3 bg-cyan-500/10 rounded-lg group-hover:bg-cyan-500/20 transition-colors">
            <BookOpen className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <h3 className="text-base font-medium text-white mb-1">Knowledge &amp; OCR Ingestion</h3>
            <p className="text-xs text-slate-400">Upload technical docs, scanned PDFs with local Tesseract OCR rasterization and FTS5 indexing.</p>
          </div>
        </Link>

        <Link to="/passports" className="group flex items-start gap-4 p-5 bg-slate-900 border border-slate-800 rounded-xl hover:border-cyan-500/50 transition-colors">
          <div className="p-3 bg-cyan-500/10 rounded-lg group-hover:bg-cyan-500/20 transition-colors">
            <Shield className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <h3 className="text-base font-medium text-white mb-1">Capability Passports</h3>
            <p className="text-xs text-slate-400">Audit empirical trial benchmarks, deployment identities, and pass rates.</p>
          </div>
        </Link>
      </div>
    </div>
  );
}


