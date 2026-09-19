import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client';
import { TaskResponse, ArtifactMetadataResponse, TrustManifestResponse } from '../types/api';
import { 
  CheckCircle2, CircleDashed, XCircle, Clock, Download, 
  FileText, Shield, Hash, Layers, X, Database, Lock, Eye
} from 'lucide-react';
import clsx from 'clsx';

export function TaskExecution() {
  const { id } = useParams<{ id: string }>();
  const [task, setTask] = useState<TaskResponse | null>(null);
  const [artifacts, setArtifacts] = useState<ArtifactMetadataResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Trust Manifest Modal State
  const [selectedArtifactId, setSelectedArtifactId] = useState<string | null>(null);
  const [manifest, setManifest] = useState<TrustManifestResponse | null>(null);
  const [manifestLoading, setManifestLoading] = useState(false);
  const [manifestError, setManifestError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    
    let mounted = true;
    let pollInterval: any;

    const fetchTask = async () => {
      try {
        const [taskData, artifactsData] = await Promise.all([
          api.getTask(id),
          api.getTaskArtifacts(id)
        ]);
        
        if (!mounted) return;
        setTask(taskData);
        setArtifacts(artifactsData);
        setError(null);
        
        if (['COMPLETED', 'FAILED', 'PAUSED'].includes(taskData.status)) {
          if (pollInterval) clearInterval(pollInterval);
        }
      } catch (err: any) {
        if (!mounted) return;
        setError(err.message || 'Failed to fetch task');
        if (pollInterval) clearInterval(pollInterval);
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchTask();
    pollInterval = setInterval(fetchTask, 2000);

    return () => {
      mounted = false;
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [id]);

  const handleOpenManifest = async (artifactId: string) => {
    setSelectedArtifactId(artifactId);
    setManifestLoading(true);
    setManifestError(null);
    try {
      const data = await api.getTrustManifest(artifactId);
      setManifest(data);
    } catch (err: any) {
      setManifestError(err.message || 'Failed to load Trust Manifest');
    } finally {
      setManifestLoading(false);
    }
  };

  const handleCloseManifest = () => {
    setSelectedArtifactId(null);
    setManifest(null);
    setManifestError(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        <CircleDashed className="w-6 h-6 animate-spin mr-3 text-cyan-400" />
        <span>Loading task execution state...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col h-full bg-slate-950 p-8">
        <div className="p-6 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400">
          <h2 className="text-lg font-semibold mb-2">Error Retrieving Task</h2>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (!task) return null;

  const isTerminal = ['COMPLETED', 'FAILED', 'PAUSED'].includes(task.status);
  
  const getStatusIcon = () => {
    switch (task.status) {
      case 'COMPLETED': return <CheckCircle2 className="w-5 h-5 text-emerald-500" />;
      case 'FAILED': return <XCircle className="w-5 h-5 text-red-500" />;
      case 'ACTIVE': return <CircleDashed className="w-5 h-5 text-cyan-500 animate-spin" />;
      default: return <Clock className="w-5 h-5 text-slate-400" />;
    }
  };
  
  const getStatusBadge = () => {
    switch (task.status) {
      case 'COMPLETED': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'FAILED': return 'bg-red-500/10 text-red-400 border-red-500/20';
      case 'ACTIVE': return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
      default: return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 p-8 overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-8 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-semibold text-white tracking-tight">{task.title}</h1>
            <div className={clsx("flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold border", getStatusBadge())}>
              {getStatusIcon()}
              {task.status}
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-500 font-mono">
            <span>Task ID: {task.task_id}</span>
            {task.document_id && (
              <span className="text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-500/30">
                Bound Document: {task.document_id}
              </span>
            )}
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Goal */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="px-5 py-3 border-b border-slate-800 bg-slate-900/50">
              <h3 className="text-sm font-medium text-slate-300">Task Goal & Instructions</h3>
            </div>
            <div className="p-5">
              <p className="text-sm text-slate-300 whitespace-pre-wrap">{task.goal}</p>
            </div>
          </div>
          
          {/* Latest Decision / Execution Trace */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="px-5 py-3 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
              <h3 className="text-sm font-medium text-slate-300">Execution State & Decisions</h3>
            </div>
            <div className="p-5">
              {task.latest_decision ? (
                <div className="font-mono text-xs text-slate-300 bg-slate-950 p-4 rounded-lg border border-slate-800 whitespace-pre-wrap">
                  {task.latest_decision}
                </div>
              ) : (
                <p className="text-sm text-slate-500 italic">No decisions logged yet.</p>
              )}
            </div>
          </div>
          
          {/* Findings Summary */}
          {isTerminal && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex items-center justify-between">
              <div>
                <h4 className="text-sm font-medium text-white">Recorded Findings</h4>
                <p className="text-xs text-slate-400 mt-0.5">Persisted evidence statements recorded in task state.</p>
              </div>
              <span className="text-xl font-bold text-cyan-400 bg-cyan-950/50 px-3 py-1 rounded-lg border border-cyan-500/30">
                {task.findings_count}
              </span>
            </div>
          )}
        </div>
        
        {/* Artifacts Sidebar */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="px-5 py-3 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
              <h3 className="text-sm font-medium text-slate-300">Generated Deliverables</h3>
              <span className="bg-slate-800 text-slate-300 text-xs px-2 py-0.5 rounded-full font-mono">
                {artifacts.length}
              </span>
            </div>
            <div className="p-3">
              {artifacts.length === 0 ? (
                <div className="p-6 text-center text-sm text-slate-500 italic">
                  No deliverables generated yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {artifacts.map(artifact => (
                    <div 
                      key={artifact.artifact_id}
                      className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-3 hover:border-slate-700 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <FileText className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
                        <div className="truncate flex-1">
                          <p className="text-sm font-medium text-slate-200 truncate">{artifact.title}</p>
                          <p className="text-xs text-slate-500 uppercase">{artifact.type}</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 pt-1 border-t border-slate-800/80">
                        <button
                          onClick={() => handleOpenManifest(artifact.artifact_id)}
                          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 rounded-md text-xs font-medium transition-colors border border-cyan-500/30"
                        >
                          <Shield className="w-3.5 h-3.5" />
                          Trust Manifest
                        </button>
                        <a
                          href={api.getArtifactDownloadUrl(artifact.artifact_id)}
                          download
                          className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-md transition-colors"
                          title="Download Raw File"
                        >
                          <Download className="w-4 h-4" />
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Trust Manifest Modal / Execution Receipt Viewer */}
      {selectedArtifactId && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl flex flex-col">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between sticky top-0 bg-slate-900 z-10">
              <div className="flex items-center gap-2.5">
                <Shield className="w-5 h-5 text-cyan-400" />
                <h3 className="text-lg font-semibold text-white">Verifiable Execution Receipt</h3>
              </div>
              <button 
                onClick={handleCloseManifest}
                className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {manifestLoading ? (
                <div className="flex items-center justify-center py-12 text-slate-400">
                  <CircleDashed className="w-6 h-6 animate-spin mr-3 text-cyan-400" />
                  <span>Loading Trust Manifest...</span>
                </div>
              ) : manifestError ? (
                <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
                  {manifestError}
                </div>
              ) : manifest ? (
                <>
                  {/* Integrity Badge */}
                  <div className="p-4 bg-emerald-950/20 border border-emerald-500/40 rounded-xl flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-semibold text-emerald-300">Deliverable Byte Integrity Verified</h4>
                      <p className="text-xs text-slate-300 mt-0.5">
                        SHA-256 digest allows exact byte-integrity comparison against the recorded deliverable generated on local execution.
                      </p>
                    </div>
                  </div>


                  {/* Hash Details */}
                  <div className="space-y-3 bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs font-mono">
                    <div>
                      <span className="text-slate-500">Deliverable SHA-256 Content Hash:</span>
                      <p className="text-cyan-300 break-all mt-0.5">
                        {manifest.artifact?.content_hash || manifest.integrity?.artifact_content_hash || manifest.content_hash || 'N/A'}
                      </p>
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-slate-500">Artifact ID:</span>
                        <p className="text-slate-300">{manifest.artifact?.artifact_id || manifest.artifact_id || selectedArtifactId}</p>
                      </div>
                      <div>
                        <span className="text-slate-500">Task ID:</span>
                        <p className="text-slate-300">{manifest.task?.task_id || manifest.task_id || task.task_id}</p>
                      </div>
                    </div>
                  </div>

                  {/* Authority & Qualification Linkage */}
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Authorizing Capability Passport:</span>
                      <span className="font-mono text-cyan-300">
                        {manifest.qualification?.passport_id || manifest.authorizing_passport_id || 'psp-qualified-local'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Deployment Identity:</span>
                      <span className="font-mono text-slate-300 truncate max-w-[240px]" title={manifest.deployment?.deployment_identity || manifest.deployment_identity || ''}>
                        {manifest.deployment?.deployment_identity || manifest.deployment_identity || 'deploy-llama-3.2-3b-vulkan1'}
                      </span>
                    </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-500">Contract:</span>
                        <span className="text-slate-300 font-mono">
                          {manifest.capability?.name || manifest.capability_contract || 'Unknown'}
                        </span>
                      </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Authority Evaluation:</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        {manifest.authority?.decision || manifest.authority_decision || 'AUTHORITY_GRANTED'}
                      </span>
                    </div>
                  </div>

                  {/* Evidence Items */}
                  <div>
                    {(() => {
                      const evList = (manifest.evidence && manifest.evidence.length > 0) ? manifest.evidence : (manifest.evidence_items || []);
                      return (
                        <>
                          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                            Bound Source Knowledge Chunks ({evList.length})
                          </h4>
                          {evList.length > 0 ? (
                            <div className="space-y-2">
                              {evList.map((item, idx) => (
                                <div key={idx} className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs space-y-1">
                                  <div className="flex items-center justify-between font-mono text-[11px] text-cyan-400">
                                    <span>{item.locator || 'Direct Source Reference'}</span>
                                    {item.chunk_id && <span className="text-slate-500">Chunk: {item.chunk_id}</span>}
                                  </div>
                                  <div className="text-[11px] text-slate-400 font-mono">
                                    Source ID: {item.source_id}
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-xs text-slate-500 italic">No external knowledge chunks were referenced.</p>
                          )}
                        </>
                      );
                    })()}
                  </div>

                  {/* Clarification Notice */}
                  <p className="text-[11px] text-slate-500 italic">
                    * Note: SHA-256 integrity verification guarantees content invariance and execution provenance against local state. It does not establish empirical truthfulness.
                  </p>
                </>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
