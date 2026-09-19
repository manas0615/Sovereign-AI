import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { 
  MessageSquare, Terminal, BookOpen, Shield, Award, 
  Layers, Plus, Sparkles, CheckCircle2, Cpu, HardDrive
} from 'lucide-react';
import clsx from 'clsx';
import { useHealth } from '../hooks/useHealth';

const navigation = [
  { name: 'Assistant Chat', to: '/', icon: MessageSquare, badge: 'Primary' },
  { name: 'Coding Studio', to: '/coding', icon: Terminal, badge: 'Code Sandbox' },
  { name: 'Knowledge Library', to: '/knowledge', icon: BookOpen, badge: 'Knowledge & OCR' },
  { name: 'Artifacts Library', to: '/artifacts', icon: HardDrive, badge: 'Deliverables' },
  { name: 'Governed Tasks', to: '/tasks', icon: Layers, badge: 'Tasks & Receipts' },
  { name: 'Passports & Authority', to: '/passports', icon: Shield, badge: 'Qualification' },
  { name: 'Architecture & Invariants', to: '/moon', icon: Award, badge: 'System Spec' },
];

export function Layout() {
  const health = useHealth();
  const navigate = useNavigate();
  const isHealthy = health?.status?.toUpperCase() === 'HEALTHY';

  const handleNewChat = () => {
    navigate('/');
    window.dispatchEvent(new CustomEvent('sovereign-new-chat'));
  };

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
              <span className="text-[10px] text-cyan-400 font-mono font-medium">CONVERSATIONAL WORKBENCH</span>
            </div>
          </div>
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] text-emerald-400 font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>Local</span>
          </div>
        </div>

        {/* New Chat Primary Action */}
        <div className="p-3">
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

          {/* Quick Info & Governance Callout */}
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              <span>Active Model Deployment</span>
            </div>
            <p className="text-[11px] font-mono text-cyan-300 truncate">
              Llama-3.2-3B-Instruct (Vulkan)
            </p>
            <div className="text-[10px] text-slate-400 leading-relaxed border-t border-slate-800/60 pt-1.5">
              Empirical qualification validated. Task-scoped authority evaluation enforced.
            </div>
          </div>
        </div>

        {/* Footer System Status */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/40">
          <div className="flex flex-col gap-1.5 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 text-[11px]">Model Runtime (P01):</span>
              <span className={clsx("font-mono text-[11px] font-medium", isHealthy ? "text-emerald-400" : "text-red-400")}>
                {isHealthy ? "ONLINE (127.0.0.1)" : "DISCONNECTED"}
              </span>
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <div className="flex items-center gap-1.5">
                <Shield className="w-3 h-3 text-slate-500" />
                <span>Execution Boundary:</span>
              </div>
              <span className="text-cyan-400 font-mono">Subprocess Sandbox (P04)</span>
            </div>
            <div className="text-[10px] text-slate-400 font-mono mt-1 pt-1 border-t border-slate-800/60 text-center">
              Sovereign AI Prototype • SIH 2026
            </div>
          </div>
        </div>
      </aside>

      {/* Full-Viewport Main Content Area */}
      <main className="flex-1 relative flex flex-col h-full overflow-hidden bg-slate-950">
        <Outlet />
      </main>
    </div>
  );
}

