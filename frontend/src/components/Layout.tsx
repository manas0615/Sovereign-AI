import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { 
  MessageSquare, Terminal, BookOpen, Shield, Award, 
  Layers, Plus, Sparkles, CheckCircle2, Cpu, HardDrive,
  Activity, RefreshCw, Info, X, AlertTriangle
} from 'lucide-react';
import clsx from 'clsx';
import { useHealth } from '../hooks/useHealth';
import { api } from '../api/client';
import { NetworkTelemetryResponse } from '../types/api';

const navigation = [
  { name: 'Assistant Chat', to: '/', icon: MessageSquare, badge: 'Conversational' },
  { name: 'Coding Studio', to: '/coding', icon: Terminal, badge: 'Governed Execution' },
  { name: 'Knowledge Library', to: '/knowledge', icon: BookOpen, badge: 'OCR & Knowledge' },
  { name: 'Artifacts Library', to: '/artifacts', icon: HardDrive, badge: 'Deliverables' },
  { name: 'Governed Tasks', to: '/tasks', icon: Layers, badge: 'Tasks & Receipts' },
  { name: 'Passports & Authority', to: '/passports', icon: Shield, badge: 'Qualification' },
  { name: 'Architecture & Invariants', to: '/moon', icon: Award, badge: 'System Spec' },
];

export function Layout() {
  const health = useHealth();
  const navigate = useNavigate();
  const isHealthy = health?.status?.toUpperCase() === 'HEALTHY';
  const [telemetry, setTelemetry] = useState<NetworkTelemetryResponse | null>(null);
  const [showTelemetryModal, setShowTelemetryModal] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  useEffect(() => {
    const fetchTelemetry = () => {
      api.getNetworkTelemetry()
        .then(setTelemetry)
        .catch(() => setTelemetry(null));
    };

    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleNewChat = () => {
    navigate('/');
    window.dispatchEvent(new CustomEvent('sovereign-new-chat'));
  };

  const handleResetDemo = async () => {
    if (!window.confirm('Reset demo tasks to initial clean state? (Benchmark and qualification records are preserved)')) return;
    setIsResetting(true);
    try {
      await api.resetDemoWorkspace();
      window.location.reload();
    } catch (err) {
      console.error('Failed to reset demo workspace:', err);
    } finally {
      setIsResetting(false);
    }
  };

  const getTelemetryStatusText = () => {
    if (!telemetry) return 'TELEMETRY CONNECTING...';
    if (telemetry.status === 'UNAVAILABLE') return 'TELEMETRY UNAVAILABLE';
    if (telemetry.status === 'NON_LOOPBACK_OBSERVED') {
      return `WARNING: ${telemetry.observed_non_loopback_connections} NON-LOOPBACK CONNECTION(S) OBSERVED`;
    }
    return 'LOCAL PROCESSING • 0 NON-LOOPBACK CONNECTIONS OBSERVED';
  };

  const isLocalOnly = telemetry?.status === 'LOCAL_LOOPBACK_ONLY';

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      {/* Persistent Left Sidebar */}
      <aside className="w-72 flex-shrink-0 border-r border-slate-800/80 bg-slate-900/95 flex flex-col z-20 select-none">
        {/* Header Branding */}
        <div className="h-16 flex items-center justify-between px-5 border-b border-slate-800/80">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-slate-950 text-lg shadow-sm">
              S
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-sm leading-tight text-white tracking-tight">Sovereign AI</span>
              <span className="text-[10px] text-cyan-400 font-mono font-medium">SOVEREIGN WORKBENCH</span>
            </div>
          </div>
          <button 
            onClick={() => setShowTelemetryModal(true)}
            className={clsx(
              "flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[10px] font-mono cursor-pointer transition-colors",
              isLocalOnly ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20" :
              telemetry?.status === 'UNAVAILABLE' ? "bg-amber-500/10 border-amber-500/20 text-amber-400 hover:bg-amber-500/20" :
              "bg-red-500/10 border-red-500/20 text-red-400 hover:bg-red-500/20"
            )}
            title="Click to view network observation telemetry"
          >
            <span className={clsx("w-1.5 h-1.5 rounded-full", isLocalOnly ? "bg-emerald-400 animate-pulse" : "bg-amber-400")} />
            <span>{isLocalOnly ? 'Local' : 'Audited'}</span>
          </button>
        </div>

        {/* New Chat Primary Action */}
        <div className="p-3 space-y-2">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-between px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-sm transition-all shadow-sm hover:shadow-cyan-500/20 group cursor-pointer"
          >
            <div className="flex items-center gap-2.5">
              <Plus className="w-4 h-4 text-white" />
              <span>New Conversation</span>
            </div>
            <Sparkles className="w-3.5 h-3.5 text-cyan-200 group-hover:rotate-12 transition-transform" />
          </button>
        </div>

        {/* Navigation Sections */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-6 scrollbar-thin scrollbar-thumb-slate-800">
          <div>
            <div className="px-3 pb-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              Workspaces &amp; Modes
            </div>
            <div className="space-y-1">
              {navigation.map((item) => (
                <NavLink
                  key={item.name}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all group',
                      isActive
                        ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-semibold shadow-sm'
                        : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
                    )
                  }
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <item.icon className="w-4 h-4 flex-shrink-0 text-slate-400 group-hover:text-cyan-300 transition-colors" />
                    <span className="truncate">{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-400 border border-slate-700/60">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              ))}
            </div>
          </div>

          {/* Quick Info & Model Deployment Callout */}
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              <span>Local Model Deployment</span>
            </div>
            <p className="text-[11px] font-mono text-cyan-300 truncate">
              Llama-3.2-3B-Instruct (Vulkan)
            </p>
            <div className="text-[10px] text-slate-400 leading-relaxed border-t border-slate-800/60 pt-1.5">
              Empirical qualification validated. Task-scoped authority evaluation enforced.
            </div>
          </div>
        </div>

        {/* Footer System Status & Telemetry Bar */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/40 space-y-2">
          {/* Live Network Observation Line */}
          <button
            onClick={() => setShowTelemetryModal(true)}
            className="w-full text-left p-2 rounded-lg bg-slate-900 border border-slate-800/80 hover:border-slate-700 transition-colors cursor-pointer group"
          >
            <div className="flex items-center justify-between text-[10px] font-mono mb-1">
              <span className="text-slate-400 flex items-center gap-1">
                <Activity className="w-3 h-3 text-cyan-400" />
                Network Telemetry
              </span>
              <span className="text-slate-500 group-hover:text-cyan-300">Inspect →</span>
            </div>
            <div className={clsx(
              "text-[10px] font-mono font-semibold truncate",
              isLocalOnly ? "text-emerald-400" : telemetry?.status === 'UNAVAILABLE' ? "text-amber-400" : "text-red-400"
            )}>
              {getTelemetryStatusText()}
            </div>
          </button>

          <div className="flex flex-col gap-1 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 text-[11px]">Model Runtime:</span>
              <span className={clsx("font-mono text-[11px] font-medium", isHealthy ? "text-emerald-400" : "text-red-400")}>
                {isHealthy ? "ONLINE (127.0.0.1)" : "DISCONNECTED"}
              </span>
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <div className="flex items-center gap-1.5">
                <Shield className="w-3 h-3 text-slate-500" />
                <span>Execution Layer:</span>
              </div>
              <span className="text-cyan-400 font-mono">Governed Boundary</span>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px]">
            <span className="text-slate-500 font-mono">SIH 2026</span>
            <button
              onClick={handleResetDemo}
              disabled={isResetting}
              className="text-slate-400 hover:text-cyan-300 flex items-center gap-1 font-mono transition-colors cursor-pointer"
              title="Reset tasks for clean demo repeatability"
            >
              <RefreshCw className={clsx("w-2.5 h-2.5", isResetting && "animate-spin")} />
              <span>Reset Demo State</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Full-Viewport Main Content Area */}
      <main className="flex-1 relative flex flex-col h-full overflow-hidden bg-slate-950">
        <Outlet />
      </main>

      {/* Network Observation Modal */}
      {showTelemetryModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-xl w-full max-h-[85vh] overflow-y-auto shadow-2xl flex flex-col">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between sticky top-0 bg-slate-900 z-10">
              <div className="flex items-center gap-2.5">
                <Activity className="w-5 h-5 text-cyan-400" />
                <h3 className="text-base font-semibold text-white">Live Network Observation Telemetry</h3>
              </div>
              <button 
                onClick={() => setShowTelemetryModal(false)}
                className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-5 text-xs">
              {/* Status Header */}
              <div className={clsx(
                "p-4 rounded-xl border flex items-start gap-3",
                isLocalOnly ? "bg-emerald-950/20 border-emerald-500/30 text-emerald-300" :
                telemetry?.status === 'UNAVAILABLE' ? "bg-amber-950/20 border-amber-500/30 text-amber-300" :
                "bg-red-950/20 border-red-500/30 text-red-300"
              )}>
                {isLocalOnly ? <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" /> : <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />}
                <div>
                  <div className="font-semibold text-sm">
                    {getTelemetryStatusText()}
                  </div>
                  <div className="text-[11px] text-slate-300 mt-1">
                    Active sockets inspected across {telemetry?.monitored_processes_count || 0} application process(es).
                  </div>
                </div>
              </div>

              {/* Monitored Process Telemetry */}
              <div className="space-y-2 bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-[11px]">
                <div className="flex justify-between border-b border-slate-800/80 pb-2">
                  <span className="text-slate-400">Observed Non-Loopback Sockets:</span>
                  <span className={clsx("font-bold", telemetry?.observed_non_loopback_connections === 0 ? "text-emerald-400" : "text-red-400")}>
                    {telemetry?.observed_non_loopback_connections ?? 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between border-b border-slate-800/80 pb-2">
                  <span className="text-slate-400">Observed Local / Loopback Sockets:</span>
                  <span className="text-cyan-300 font-bold">{telemetry?.observed_local_sockets ?? 'N/A'}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/80 pb-2">
                  <span className="text-slate-400">Model Runtime Endpoint:</span>
                  <span className="text-slate-200">{telemetry?.model_runtime_host || '127.0.0.1:8080'}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/80 pb-2">
                  <span className="text-slate-400">Knowledge Base:</span>
                  <span className="text-slate-200">{telemetry?.knowledge_base_type || 'SQLite (Local)'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Artifact Storage:</span>
                  <span className="text-slate-200">{telemetry?.artifact_storage_type || 'Local Storage'}</span>
                </div>
              </div>

              {/* Observed Sockets List */}
              {telemetry?.connections && telemetry.connections.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-semibold text-slate-300 uppercase tracking-wider text-[10px]">
                    Observed Socket Connections ({telemetry.connections.length})
                  </h4>
                  <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1 font-mono text-[10px]">
                    {telemetry.connections.map((c, i) => (
                      <div key={i} className="p-2 bg-slate-950 rounded border border-slate-800/80 flex items-center justify-between">
                        <div>
                          <span className="text-cyan-400">{c.process}</span>
                          <span className="text-slate-500 ml-1.5">(PID {c.pid})</span>
                          <div className="text-slate-400 text-[9px] mt-0.5">{c.laddr} → {c.raddr}</div>
                        </div>
                        <div className="text-right">
                          <span className={clsx("px-1.5 py-0.5 rounded text-[9px]", c.is_loopback ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400")}>
                            {c.is_loopback ? 'Loopback' : 'External'}
                          </span>
                          <div className="text-slate-500 text-[9px] mt-0.5">{c.status}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Required Truthfulness Disclaimer */}
              <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-lg text-[11px] text-slate-400 leading-relaxed">
                <div className="font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
                  <Info className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Observation Scope &amp; Operating Disclaimer</span>
                </div>
                <p>
                  {telemetry?.disclaimer || "Observed socket telemetry: all connections bound to loopback (127.0.0.1 / ::1). Note: Socket observation inspects active connections; it does not constitute OS kernel airgap enforcement."}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

