import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { CapabilityPassportResponse } from '../types/api';
import { Shield, CheckCircle2, XCircle, AlertTriangle, RefreshCw, Cpu, Award } from 'lucide-react';
import clsx from 'clsx';
import { getCapabilityDisplay } from '../utils/labels';

export function Passports() {
  const [passports, setPassports] = useState<CapabilityPassportResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPassports = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getPassports();
      setPassports(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch capability passports');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPassports();
  }, []);

  return (
    <div className="flex flex-col h-full bg-slate-950 p-8 overflow-y-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-cyan-500/10 rounded-lg text-cyan-400">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-white tracking-tight">Capability Passports</h1>
              <p className="text-sm text-slate-400 mt-0.5">Empirical qualification records for active model deployments (P08 Qualification Engine).</p>
            </div>
          </div>
        </div>
        <button
          onClick={fetchPassports}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-300 hover:text-white hover:border-slate-700 transition-colors disabled:opacity-50 cursor-pointer"
        >
          <RefreshCw className={clsx("w-4 h-4", loading && "animate-spin")} />
          Refresh
        </button>
      </div>

      {/* Moon Principle Banner */}
      <div className="mb-8 p-5 bg-gradient-to-r from-cyan-950/40 via-slate-900 to-slate-900 border border-cyan-500/30 rounded-xl">
        <div className="flex items-start gap-4">
          <div className="p-2 bg-cyan-500/20 rounded-lg text-cyan-300 mt-0.5">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-cyan-200 uppercase tracking-wider">
              Core Architectural Invariant: Configuration ≠ Qualification ≠ Authority
            </h3>
            <p className="text-sm text-slate-300 mt-1">
              "Local is where the model runs. Qualified is why the model is allowed to act."
            </p>
            <p className="text-xs text-slate-400 mt-2">
              A Capability Passport provides verifiable evidence of empirical trial results. It does not confer execution authority until evaluated against the task's specific policy boundary.
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center p-16 text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mr-3 text-cyan-400" />
          <span>Loading capability passports from persistence...</span>
        </div>
      ) : passports.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center">
          <Shield className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-1">No Passports Registered</h3>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            No qualification passports are currently stored in SQLite persistence. Run a qualification trial to evaluate and issue passports.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {passports.map((passport) => {
            const isQualified = passport.qualification_status === 'QUALIFIED';
            const passRate = passport.metadata?.pass_rate !== undefined 
              ? `${Math.round(passport.metadata.pass_rate * 100)}%`
              : 'N/A';
            const trials = passport.metadata?.evaluated_trials !== undefined
              ? `${passport.metadata.evaluated_trials} trials`
              : '';

            return (
              <div 
                key={passport.passport_id}
                className={clsx(
                  "bg-slate-900 border rounded-xl p-6 shadow-sm flex flex-col justify-between transition-all",
                  isQualified ? "border-slate-800 hover:border-cyan-500/40" : "border-red-500/30 bg-red-950/10"
                )}
              >
                <div>
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <span className="text-xs font-mono text-slate-500">{passport.passport_id}</span>
                      <h3 className="text-lg font-semibold text-white mt-0.5">{getCapabilityDisplay(passport.capability_contract)}</h3>
                      <p className="text-xs font-mono text-slate-400">{passport.capability_contract}</p>
                    </div>
                    <div className={clsx(
                      "flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border",
                      isQualified 
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" 
                        : "bg-red-500/10 text-red-400 border-red-500/30"
                    )}>
                      {isQualified ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                      {passport.qualification_status}
                    </div>
                  </div>

                  <div className="space-y-3 text-xs">
                    <div className="flex items-center justify-between py-1.5 border-b border-slate-800/60">
                      <span className="text-slate-400">Pass Rate / Performance:</span>
                      <span className={clsx("font-semibold", isQualified ? "text-cyan-300" : "text-red-400")}>
                        {passRate} {trials && <span className="text-slate-500 font-normal">({trials})</span>}
                      </span>
                    </div>

                    <div className="flex items-start justify-between py-1.5 border-b border-slate-800/60">
                      <span className="text-slate-400">Deployment Identity:</span>
                      <span className="font-mono text-slate-300 truncate max-w-[200px]" title={passport.deployment_identity}>
                        {passport.deployment_identity}
                      </span>
                    </div>

                    <div className="flex items-start justify-between py-1.5 border-b border-slate-800/60">
                      <span className="text-slate-400">Qualification Identity:</span>
                      <span className="font-mono text-slate-300 truncate max-w-[200px]" title={passport.qualification_identity}>
                        {passport.qualification_identity}
                      </span>
                    </div>

                    <div className="flex items-center justify-between py-1.5">
                      <span className="text-slate-400">Evaluated Timestamp:</span>
                      <span className="text-slate-300">
                        {new Date(passport.qualification_timestamp).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
                  <span className="flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5 text-slate-400" />
                    Runtime: llama.cpp / Vulkan
                  </span>
                  <span>Result ID: {passport.result_id}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
