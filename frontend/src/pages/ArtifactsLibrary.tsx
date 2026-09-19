import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { ArtifactMetadataResponse } from '../types/api';
import {
  FileText,
  Download,
  Search,
  RefreshCw,
  Eye,
  Layers,
  HardDrive,
  Clock,
  Hash,
  ShieldCheck,
  AlertCircle,
  FileSpreadsheet,
  FileCode,
  FileCheck
} from 'lucide-react';

export const ArtifactsLibrary: React.FC = () => {
  const [artifacts, setArtifacts] = useState<ArtifactMetadataResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFormat, setSelectedFormat] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'title' | 'size'>('newest');
  const [selectedArtifact, setSelectedArtifact] = useState<ArtifactMetadataResponse | null>(null);
  const [copySuccess, setCopySuccess] = useState<string | null>(null);

  const fetchArtifacts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAllArtifacts();
      setArtifacts(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load artifacts library.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArtifacts();
  }, []);

  const formatFileSize = (bytes?: number | null) => {
    if (!bytes || bytes <= 0) return 'N/A';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const getFormatBadge = (type: string, filename?: string | null) => {
    const fn = (filename || '').toLowerCase();
    const t = (type || '').toUpperCase();
    if (t === 'DOCX' || fn.endsWith('.docx')) {
      return { label: 'DOCX (Word)', color: 'bg-blue-500/10 text-blue-400 border-blue-500/30', icon: FileText };
    }
    if (t === 'XLSX' || fn.endsWith('.xlsx')) {
      return { label: 'XLSX (Excel)', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', icon: FileSpreadsheet };
    }
    if (t === 'PPTX' || fn.endsWith('.pptx')) {
      return { label: 'PPTX (PowerPoint)', color: 'bg-orange-500/10 text-orange-400 border-orange-500/30', icon: Layers };
    }
    if (t === 'PDF' || fn.endsWith('.pdf')) {
      return { label: 'PDF Report', color: 'bg-red-500/10 text-red-400 border-red-500/30', icon: FileCheck };
    }
    if (t === 'MARKDOWN' || fn.endsWith('.md')) {
      return { label: 'Markdown', color: 'bg-purple-500/10 text-purple-400 border-purple-500/30', icon: FileText };
    }
    if (t === 'JSON' || fn.endsWith('.json')) {
      return { label: 'JSON Data', color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30', icon: FileCode };
    }
    return { label: type || 'File', color: 'bg-slate-500/10 text-slate-400 border-slate-500/30', icon: FileText };
  };

  const handleCopyHash = (hash?: string | null) => {
    if (!hash) return;
    navigator.clipboard.writeText(hash);
    setCopySuccess(hash);
    setTimeout(() => setCopySuccess(null), 2000);
  };

  const filteredArtifacts = artifacts
    .filter(art => {
      const fn = (art.filename || art.title || '').toLowerCase();
      const tid = (art.task_id || '').toLowerCase();
      const q = searchQuery.toLowerCase();
      const matchesSearch = fn.includes(q) || tid.includes(q) || (art.content_hash || '').includes(q);

      if (!matchesSearch) return false;

      if (selectedFormat === 'ALL') return true;
      const t = (art.type || '').toUpperCase();
      const ext = (art.filename || '').toLowerCase();
      if (selectedFormat === 'DOCX') return t === 'DOCX' || ext.endsWith('.docx');
      if (selectedFormat === 'XLSX') return t === 'XLSX' || ext.endsWith('.xlsx');
      if (selectedFormat === 'PPTX') return t === 'PPTX' || ext.endsWith('.pptx');
      if (selectedFormat === 'PDF') return t === 'PDF' || ext.endsWith('.pdf');
      if (selectedFormat === 'MARKDOWN') return t === 'MARKDOWN' || ext.endsWith('.md');
      if (selectedFormat === 'JSON') return t === 'JSON' || ext.endsWith('.json');
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'newest') return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      if (sortBy === 'oldest') return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      if (sortBy === 'title') return (a.title || '').localeCompare(b.title || '');
      if (sortBy === 'size') return (b.size_bytes || 0) - (a.size_bytes || 0);
      return 0;
    });

  return (
    <div className="h-full flex flex-col bg-[#0c0e14] text-slate-200 overflow-hidden">
      {/* Header */}
      <div className="px-8 py-5 border-b border-slate-800/80 bg-[#10131c] flex items-center justify-between shrink-0">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <HardDrive className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
                <span>Artifacts & Deliverables Library</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700 font-mono">
                  {artifacts.length} {artifacts.length === 1 ? 'file' : 'files'}
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                Discover, inspect provenance, and securely download governed engineering reports, spreadsheets, and briefings.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchArtifacts}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Controls: Search, Format Filters, Sorting */}
      <div className="px-8 py-4 bg-[#0e111a] border-b border-slate-800/60 flex flex-wrap items-center justify-between gap-4 shrink-0">
        <div className="flex items-center space-x-3 flex-1 min-w-[300px] max-w-md">
          <div className="relative w-full">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search by filename, task ID, title, or SHA-256..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-900/90 border border-slate-700/80 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
            />
          </div>
        </div>

        {/* Format Filter Pills */}
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 text-xs">
          {[
            { id: 'ALL', label: 'All Formats' },
            { id: 'DOCX', label: 'Word (.docx)' },
            { id: 'XLSX', label: 'Excel (.xlsx)' },
            { id: 'PPTX', label: 'PowerPoint (.pptx)' },
            { id: 'PDF', label: 'PDF' },
            { id: 'MARKDOWN', label: 'Markdown (.md)' },
            { id: 'JSON', label: 'JSON' },
          ].map(fmt => (
            <button
              key={fmt.id}
              onClick={() => setSelectedFormat(fmt.id)}
              className={`px-3 py-1 rounded-md transition font-medium text-xs whitespace-nowrap ${
                selectedFormat === fmt.id
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'bg-slate-900/60 text-slate-400 hover:text-slate-300 hover:bg-slate-800 border border-slate-800'
              }`}
            >
              {fmt.label}
            </button>
          ))}
        </div>

        {/* Sort selector */}
        <div className="flex items-center space-x-2 text-xs text-slate-400 shrink-0">
          <span>Sort:</span>
          <select
            value={sortBy}
            onChange={(e: any) => setSortBy(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-md px-2 py-1 text-slate-300 text-xs focus:outline-none focus:border-cyan-500/50"
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="title">Filename / Title</option>
            <option value="size">File Size</option>
          </select>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {loading && artifacts.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center space-y-3 text-slate-400">
            <RefreshCw className="w-8 h-8 animate-spin text-cyan-400" />
            <p className="text-sm">Scanning verified artifact repository...</p>
          </div>
        ) : error ? (
          <div className="p-6 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 flex items-center space-x-3">
            <AlertCircle className="w-6 h-6 shrink-0 text-red-400" />
            <div>
              <h3 className="text-sm font-bold">Failed to load artifacts</h3>
              <p className="text-xs text-red-400/90 mt-0.5">{error}</p>
            </div>
          </div>
        ) : filteredArtifacts.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center space-y-3 text-slate-500 border border-dashed border-slate-800 rounded-xl">
            <HardDrive className="w-10 h-10 stroke-[1.5] text-slate-600" />
            <div className="text-center">
              <p className="text-sm font-medium text-slate-300">No matching deliverables found</p>
              <p className="text-xs text-slate-500 mt-1">
                {searchQuery || selectedFormat !== 'ALL'
                  ? 'Try adjusting your search query or format filter.'
                  : 'Generate approval notes, calculation workbooks, or briefings in Assistant Chat or Governed Tasks.'}
              </p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filteredArtifacts.map(art => {
              const badge = getFormatBadge(art.type, art.filename);
              const IconComp = badge.icon;
              const downloadUrl = api.getArtifactDownloadUrl(art.artifact_id);

              return (
                <div
                  key={art.artifact_id}
                  className="group bg-[#11141f] hover:bg-[#151926] border border-slate-800/80 hover:border-slate-700/90 rounded-xl p-5 transition flex flex-col justify-between shadow-sm hover:shadow-md"
                >
                  <div>
                    {/* Top row: Format Badge & Status */}
                    <div className="flex items-center justify-between mb-3">
                      <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${badge.color}`}>
                        <IconComp className="w-3.5 h-3.5" />
                        <span>{badge.label}</span>
                      </div>
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-900 text-slate-400 border border-slate-800 font-mono">
                        {formatFileSize(art.size_bytes)}
                      </span>
                    </div>

                    {/* Title & Filename */}
                    <h3 className="text-sm font-semibold text-slate-100 group-hover:text-cyan-300 transition line-clamp-2 leading-snug">
                      {art.title || art.filename || 'Untitled Deliverable'}
                    </h3>

                    {art.filename && (
                      <p className="text-xs font-mono text-slate-400 mt-1 truncate" title={art.filename}>
                        {art.filename}
                      </p>
                    )}

                    {/* Task association & timestamp */}
                    <div className="mt-3 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
                      <div className="flex items-center space-x-1 text-slate-400 hover:text-cyan-400">
                        <Layers className="w-3 h-3 text-slate-500" />
                        <span className="font-mono">{art.task_id ? art.task_id.substring(0, 16) : 'N/A'}</span>
                      </div>
                      <div className="flex items-center space-x-1 text-slate-500">
                        <Clock className="w-3 h-3" />
                        <span>{new Date(art.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                    </div>

                    {/* Hash snippet */}
                    {art.content_hash && (
                      <div className="mt-2 flex items-center justify-between bg-slate-900/80 px-2.5 py-1 rounded border border-slate-800/50 text-[11px]">
                        <div className="flex items-center space-x-1.5 text-slate-400">
                          <Hash className="w-3 h-3 text-slate-500" />
                          <span className="font-mono text-[10px] truncate max-w-[140px]">
                            {art.content_hash.substring(0, 16)}...
                          </span>
                        </div>
                        <button
                          onClick={() => handleCopyHash(art.content_hash)}
                          className="text-[10px] text-cyan-400 hover:text-cyan-300 underline"
                        >
                          {copySuccess === art.content_hash ? 'Copied!' : 'Copy'}
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Action buttons */}
                  <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center space-x-2">
                    <a
                      href={downloadUrl}
                      download={art.filename || `deliverable_${art.artifact_id}`}
                      className="flex-1 flex items-center justify-center space-x-1.5 py-1.5 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/30 font-medium text-xs transition"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download</span>
                    </a>
                    <button
                      onClick={() => setSelectedArtifact(art)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 font-medium text-xs transition flex items-center space-x-1"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Details</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Artifact Details Modal */}
      {selectedArtifact && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#11141f] border border-slate-700 rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-[#151926]">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-slate-100">Artifact Provenance & Metadata</h2>
                  <p className="text-xs text-slate-400 font-mono">{selectedArtifact.artifact_id}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedArtifact(null)}
                className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition"
              >
                ✕
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-4 text-xs">
              {/* Deliverable Title & Format */}
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Title</span>
                  <span className="font-bold text-slate-100 text-sm">{selectedArtifact.title}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Filename</span>
                  <span className="font-mono text-cyan-400">{selectedArtifact.filename || 'N/A'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Format</span>
                  <span className="font-semibold text-slate-200">{selectedArtifact.type}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Size</span>
                  <span className="font-mono text-slate-200">{formatFileSize(selectedArtifact.size_bytes)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Created</span>
                  <span className="text-slate-300">{new Date(selectedArtifact.created_at).toLocaleString()}</span>
                </div>
              </div>

              {/* SHA-256 Digest Box */}
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 font-medium flex items-center space-x-1">
                    <Hash className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Cryptographic Digest (SHA-256)</span>
                  </span>
                  <button
                    onClick={() => handleCopyHash(selectedArtifact.content_hash)}
                    className="text-cyan-400 hover:text-cyan-300 text-[11px] underline"
                  >
                    {copySuccess === selectedArtifact.content_hash ? 'Copied!' : 'Copy Hash'}
                  </button>
                </div>
                <p className="font-mono text-[11px] text-slate-300 bg-slate-950 p-2 rounded border border-slate-800/80 break-all select-all">
                  {selectedArtifact.content_hash || 'Digest computed at completion'}
                </p>
                <p className="text-[10px] text-slate-500 italic">
                  * SHA-256 digest validates byte-level storage integrity and detects unrecorded modifications.
                </p>
              </div>

              {/* Task Association */}
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                <h4 className="font-semibold text-slate-200 flex items-center space-x-1.5">
                  <Layers className="w-4 h-4 text-emerald-400" />
                  <span>Associated Task & Orchestration</span>
                </h4>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Task ID</span>
                  <span className="font-mono text-emerald-400">{selectedArtifact.task_id || 'N/A'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Governance State</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                    {selectedArtifact.status || 'COMPLETED'}
                  </span>
                </div>
              </div>

              {/* Rendered Sections */}
              {selectedArtifact.sections_rendered && selectedArtifact.sections_rendered.length > 0 && (
                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                  <h4 className="font-semibold text-slate-200">Rendered Report Sections</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedArtifact.sections_rendered.map((sec, i) => (
                      <span key={i} className="px-2 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[11px]">
                        {sec}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-slate-800 bg-[#151926] flex items-center justify-between">
              <button
                onClick={() => setSelectedArtifact(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs transition"
              >
                Close
              </button>
              <a
                href={api.getArtifactDownloadUrl(selectedArtifact.artifact_id)}
                download={selectedArtifact.filename || `deliverable_${selectedArtifact.artifact_id}`}
                className="flex items-center space-x-1.5 px-5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs shadow-lg shadow-cyan-900/30 transition"
              >
                <Download className="w-4 h-4" />
                <span>Download Deliverable</span>
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
