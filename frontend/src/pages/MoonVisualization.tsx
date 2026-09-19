import React from 'react';
import { Award, Shield, CheckCircle2, FileCheck, Layers, Cpu, Lock, ArrowDown } from 'lucide-react';
import { Link } from 'react-router-dom';

export function MoonVisualization() {
  const steps = [
    {
      num: 1,
      title: 'Task Definition',
      subtitle: 'Industrial task submission with capability requirements',
      desc: 'User or upstream system submits task with explicit operational requirements (e.g. document extraction, classification, reasoning).',
      badge: 'Input Phase',
      icon: Layers,
    },
    {
      num: 2,
      title: 'Capability Matching',
      subtitle: 'Formal requirements contract formulation',
      desc: 'System maps task requirements to capability contracts (e.g. general_reasoning:v1, document_ocr:v1).',
      badge: 'Governance Gate',
      icon: Shield,
    },
    {
      num: 3,
      title: 'Qualified Deployment Verification',
      subtitle: 'Capability Passport empirical validation',
      desc: 'The model deployment must possess an active, valid Capability Passport generated through empirical benchmarks. Local execution is not assumed to be capable.',
      badge: 'Moon Invariant',
      icon: Cpu,
    },
    {
      num: 4,
      title: 'Runtime Authority Evaluation',
      subtitle: 'Fail-closed authority decision computation',
      desc: 'Authority evaluator computes an ephemeral, scoped Authority Decision bound strictly to the verified deployment, task context, policy boundary, and authorized tool capabilities.',
      badge: 'Authority Gate',
      icon: Lock,
    },
    {
      num: 5,
      title: 'Governed Agent Execution',
      subtitle: 'Local-first execution & governed tools',
      desc: 'Autonomous agent executes locally under policy constraints, utilizing governed tools and knowledge retrieval while recording all actions to persistent audit trails under prototype-level isolation.',
      badge: 'Local Execution',
      icon: Cpu,
    },
    {
      num: 6,
      title: 'Materialized Evidence Binding',
      subtitle: 'Retrieved chunk & document binding',
      desc: 'All knowledge chunks and external references retrieved during execution are cryptographically bound to the resulting findings.',
      badge: 'Evidence Layer',
      icon: CheckCircle2,
    },
    {
      num: 7,
      title: 'Trust Manifest Receipt',
      subtitle: 'SHA-256 byte integrity & provenance receipt',
      desc: 'A verifiable execution receipt is minted containing the artifact SHA-256 hash, authorizing passport ID, deployment identity, and evidence references for exact byte-comparison.',
      badge: 'Verifiable Output',
      icon: FileCheck,
    },
  ];

  const pillars = [
    {
      title: '1. Configuration != Qualification',
      desc: 'Having a model running locally (in llama.cpp or Ollama) is a configuration detail. Qualification requires passing repeatable, empirical task-domain benchmark suites.',
    },
    {
      title: '2. Qualification != Authority',
      desc: 'A qualified model is capable, but not universally authorized. Authority is evaluated per-task, enforcing fail-closed security and precise capability contracts.',
    },
    {
      title: '3. SHA-256 Byte Integrity != Factual Truthfulness',
      desc: 'Cryptographic hashing allows byte comparison against the recorded digest. It proves byte-level integrity and provenance, not factual correctness or automatic reproducibility without rerun.',
    },
  ];

  return (
    <div className="flex flex-col h-full bg-slate-950 p-8 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-cyan-500/10 rounded-lg text-cyan-400">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-white tracking-tight">Sovereign AI Governance Architecture</h1>
              <p className="text-sm text-slate-400 mt-0.5">Empirical qualification, authority gating, and cryptographic provenance for SIH 2026.</p>
            </div>
          </div>
        </div>
        <Link
          to="/passports"
          className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-slate-950 rounded-lg text-sm font-medium hover:bg-cyan-400 transition-colors"
        >
          <Shield className="w-4 h-4" />
          <span>View Live Passports</span>
        </Link>
      </div>

      {/* Hero Moon Principle Banner */}
      <div className="mb-10 p-8 bg-gradient-to-r from-slate-900 via-cyan-950/40 to-slate-900 border border-cyan-500/40 rounded-2xl shadow-xl">
        <div className="max-w-4xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-xs font-semibold uppercase tracking-wider mb-4">
            Core Invariant
          </div>
          <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight leading-snug">
            &ldquo;AI capability is not assumed from a locally running model; it must be empirically qualified for a specific deployment and task, authorized before inference, and carried through to an evidence-linked, integrity-verifiable work product.&rdquo;
          </h2>
          <div className="mt-6 pt-4 border-t border-cyan-500/20 flex flex-wrap items-center gap-6 text-sm text-cyan-200">
            <span className="font-semibold text-white">Guiding Tenet:</span>
            <span>&ldquo;Local is where the model runs. Qualified is why the model is allowed to act.&rdquo;</span>
          </div>
        </div>
      </div>


      {/* 3 Foundational Pillars */}
      <div className="mb-12">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <span>Three Critical Distinctions</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {pillars.map((pillar) => (
            <div key={pillar.title} className="p-5 bg-slate-900 border border-slate-800 rounded-xl">
              <h3 className="text-sm font-semibold text-cyan-400 font-mono mb-2">{pillar.title}</h3>
              <p className="text-xs text-slate-300 leading-relaxed">{pillar.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 7-Step Governed Execution Chain */}
      <div className="mb-12">
        <h2 className="text-lg font-semibold text-white mb-6">Governed Execution Pipeline (7-Step Chain)</h2>
        <div className="space-y-4 max-w-4xl">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <React.Fragment key={step.num}>
                <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl hover:border-cyan-500/30 transition-all">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-sm flex-shrink-0">
                      {step.num}
                    </div>
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
                        <div className="flex items-center gap-2">
                          <h3 className="text-base font-semibold text-white">{step.title}</h3>
                          <span className="text-xs text-slate-400">-- {step.subtitle}</span>
                        </div>
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-slate-800 text-cyan-300 border border-slate-700">
                          {step.badge}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 mt-1 leading-relaxed">{step.desc}</p>
                    </div>
                  </div>
                </div>
                {idx < steps.length - 1 && (
                  <div className="flex justify-center py-1">
                    <ArrowDown className="w-4 h-4 text-cyan-500/40" />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}
export default MoonVisualization;
