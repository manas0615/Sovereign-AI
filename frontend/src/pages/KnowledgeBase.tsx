import React, { useState, useRef, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { DocumentIngestResponse, DocumentDetailResponse, DocumentChunkResponse } from '../types/api';
import { 
  UploadCloud, CheckCircle2, AlertCircle, FileText, ArrowRight, 
  CircleDashed, Cpu, Database, RefreshCw, Search, Filter, 
  Layers, ChevronDown, ChevronRight, X, MessageSquare, Eye 
} from 'lucide-react';
import clsx from 'clsx';

export function KnowledgeBase() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [status, setStatus] = useState<'IDLE' | 'SUCCESS' | 'ERROR'>('IDLE');
  const [message, setMessage] = useState<string | null>(null);
  const [lastIngestedDoc, setLastIngestedDoc] = useState<DocumentIngestResponse | null>(null);
  const [documents, setDocuments] = useState<DocumentDetailResponse[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  
  // Search & Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});

  // Chunks Inspection Modal
  const [inspectDoc, setInspectDoc] = useState<DocumentDetailResponse | null>(null);
  const [chunks, setChunks] = useState<DocumentChunkResponse[]>([]);
  const [loadingChunks, setLoadingChunks] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    setLoadingDocs(true);
    try {
      const docs = await api.getDocuments();
      setDocuments(docs);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setStatus('IDLE');
      setMessage(null);
      setLastIngestedDoc(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setStatus('IDLE');
    setMessage(null);
    setLastIngestedDoc(null);
    
    try {
      const res = await api.uploadDocument(file);
      setStatus('SUCCESS');
      setMessage(`${file.name} successfully ingested into local SQLite Knowledge Base.`);
      setLastIngestedDoc(res);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      fetchDocuments();
    } catch (err: any) {
      setStatus('ERROR');
      setMessage(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleInspectChunks = async (doc: DocumentDetailResponse) => {
    setInspectDoc(doc);
    setLoadingChunks(true);
    try {
      const chunkData = await api.getDocumentChunks(doc.document_id);
      setChunks(chunkData);
    } catch (err) {
      console.error('Failed to load chunks:', err);
      setChunks([]);
    } finally {
      setLoadingChunks(false);
    }
  };

  const toggleGroup = (filename: string) => {
    setExpandedGroups((prev) => ({ ...prev, [filename]: !prev[filename] }));
  };

  // Group documents by filename for clean, usable deduplication view
  const groupedDocuments = useMemo(() => {
    const groups: Record<string, DocumentDetailResponse[]> = {};
    for (const doc of documents) {
      if (!groups[doc.filename]) {
        groups[doc.filename] = [];
      }
      groups[doc.filename].push(doc);
    }

    return Object.entries(groups).map(([filename, records]) => {
      // Latest record
      const latest = records[0];
      const uniqueHashes = Array.from(new Set(records.map((r) => r.content_hash)));
      return {
        filename,
        totalRecords: records.length,
        documentType: latest.document_type,
        fileSize: latest.file_size,
        latestId: latest.document_id,
        latestCreatedAt: latest.created_at,
        uniqueHashesCount: uniqueHashes.length,
        records: records
      };
    });
  }, [documents]);

  const filteredGroups = useMemo(() => {
    return groupedDocuments.filter((group) => {
      const matchesSearch = 
        group.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
        group.records.some((r) => r.document_id.toLowerCase().includes(searchQuery.toLowerCase()));
      
      const matchesType = 
        selectedType === 'ALL' || group.documentType.toUpperCase() === selectedType.toUpperCase();

      return matchesSearch && matchesType;
    });
  }, [groupedDocuments, searchQuery, selectedType]);

  return (
    <div className="flex flex-col h-full w-full bg-slate-950 text-slate-100 overflow-y-auto p-8 select-text">
      {/* Header */}
      <div className="flex items-start justify-between mb-8 pb-6 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Knowledge Base &amp; OCR Repository</h1>
          <p className="text-sm text-slate-400 mt-1">
            Grounded local documentation store with Tesseract 5.4.0 OCR and SQLite FTS5 full-text indexing.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchDocuments}
            disabled={loadingDocs}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-850 text-slate-300 text-xs font-medium transition-colors"
          >
            <RefreshCw className={clsx("w-3.5 h-3.5 text-cyan-400", loadingDocs && "animate-spin")} />
            <span>Refresh Inventory</span>
          </button>
        </div>
      </div>

      {/* Upload Dropzone Card */}
      <div className="mb-8 p-6 bg-slate-900/80 border border-slate-800/90 rounded-2xl shadow-sm">
        <div 
          className={clsx(
            "border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center transition-colors cursor-pointer",
            file ? "border-cyan-500/50 bg-cyan-500/5" : "border-slate-700 hover:border-slate-600 bg-slate-950/60"
          )}
          onClick={() => !file && fileInputRef.current?.click()}
        >
          <input 
            type="file" 
            className="hidden" 
            ref={fileInputRef} 
            onChange={handleFileChange}
            accept=".txt,.md,.pdf,.png,.jpg,.jpeg"
          />
          
          {file ? (
            <div className="flex flex-col items-center text-center">
              <div className="w-12 h-12 bg-cyan-500/20 rounded-full flex items-center justify-center mb-3">
                <FileText className="w-6 h-6 text-cyan-400" />
              </div>
              <p className="text-sm font-semibold text-slate-200 mb-0.5">{file.name}</p>
              <p className="text-xs text-slate-400 mb-4">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              
              <div className="flex items-center gap-3">
                <button 
                  onClick={(e) => { 
                    e.stopPropagation(); 
                    setFile(null); 
                    if (fileInputRef.current) fileInputRef.current.value = ''; 
                  }}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors"
                  disabled={isUploading}
                >
                  Cancel
                </button>
                <button 
                  onClick={(e) => { e.stopPropagation(); handleUpload(); }}
                  disabled={isUploading}
                  className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-500 text-white px-5 py-1.5 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
                >
                  {isUploading ? (
                    <>
                      <CircleDashed className="w-3.5 h-3.5 animate-spin" /> 
                      Ingesting &amp; Chunking...
                    </>
                  ) : (
                    <>
                      <UploadCloud className="w-3.5 h-3.5" /> 
                      Confirm Ingest
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center text-center">
              <UploadCloud className="w-8 h-8 text-cyan-400 mb-2" />
              <p className="text-sm font-medium text-slate-200">Click to upload or drag files here</p>
              <p className="text-xs text-slate-500 mt-1">Supported: Scanned/Digital PDF, TXT, MD, PNG, JPG</p>
            </div>
          )}
        </div>

        {status === 'SUCCESS' && lastIngestedDoc && (
          <div className="mt-4 p-3 bg-emerald-950/20 border border-emerald-500/30 rounded-xl flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
              <span>{message}</span>
            </div>
            <button
              onClick={() => navigate(`/?document_id=${lastIngestedDoc.document_id}`)}
              className="flex items-center gap-1.5 px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition-colors"
            >
              <span>Chat With Document</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      {/* Search & Filters Controls */}
      <div className="mb-6 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative flex-1 w-full max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search indexed documents by filename or ID..."
            className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/60"
          />
        </div>

        <div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs">
          {['ALL', 'PDF', 'TXT', 'PNG', 'MD'].map((t) => (
            <button
              key={t}
              onClick={() => setSelectedType(t)}
              className={clsx(
                "px-3 py-1 rounded-lg font-medium transition-colors cursor-pointer",
                selectedType === t ? "bg-cyan-600 text-white" : "text-slate-400 hover:text-slate-200"
              )}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Indexed Document Library (Deduplicated & Clean View) */}
      <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <Database className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-white">
              Indexed Documents ({filteredGroups.length} unique items, {documents.length} total ingestion records)
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">SQLite FTS5 Indexed</span>
        </div>

        {loadingDocs && documents.length === 0 ? (
          <div className="py-12 text-center text-sm text-slate-500">Loading document library...</div>
        ) : filteredGroups.length === 0 ? (
          <div className="py-12 text-center text-sm text-slate-500">No matching documents found.</div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {filteredGroups.map((group) => {
              const isExpanded = !!expandedGroups[group.filename];
              return (
                <div key={group.filename} className="p-4 hover:bg-slate-850/40 transition-colors">
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3.5 min-w-0 flex-1">
                      <button
                        onClick={() => toggleGroup(group.filename)}
                        className="p-1 text-slate-400 hover:text-white rounded transition-colors"
                        title={isExpanded ? "Collapse records" : "View all ingestion versions"}
                      >
                        {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                      </button>

                      <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-cyan-400">
                        <FileText className="w-5 h-5" />
                      </div>

                      <div className="truncate min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-white truncate">{group.filename}</span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 uppercase">
                            {group.documentType}
                          </span>
                          {group.totalRecords > 1 && (
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                              {group.totalRecords} records ({group.uniqueHashesCount} unique hash{group.uniqueHashesCount > 1 ? 'es' : ''})
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-3 mt-1 text-xs text-slate-500 font-mono">
                          <span>Latest ID: {group.latestId.substring(0, 16)}...</span>
                          <span>•</span>
                          <span>{(group.fileSize / 1024).toFixed(1)} KB</span>
                          <span>•</span>
                          <span>{new Date(group.latestCreatedAt).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      <button
                        onClick={() => handleInspectChunks(group.records[0])}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5 text-cyan-400" />
                        <span>Chunks</span>
                      </button>

                      <button
                        onClick={() => navigate(`/?document_id=${group.latestId}`)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-sm transition-all cursor-pointer"
                      >
                        <MessageSquare className="w-3.5 h-3.5" />
                        <span>Chat</span>
                      </button>
                    </div>
                  </div>

                  {/* Expanded Ingestion History */}
                  {isExpanded && (
                    <div className="mt-3 pl-12 pr-4 py-2 border-t border-slate-800/60 space-y-1.5 text-xs font-mono">
                      <p className="text-[10px] uppercase font-semibold text-slate-500 mb-1">
                        Ingestion Provenance Records ({group.records.length})
                      </p>
                      {group.records.map((rec) => (
                        <div key={rec.document_id} className="p-2 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
                          <div className="flex items-center gap-2 text-slate-400">
                            <span>ID: {rec.document_id}</span>
                            <span>•</span>
                            <span className="text-cyan-400">SHA: {rec.content_hash.substring(0, 12)}...</span>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-slate-500">{new Date(rec.created_at).toLocaleString()}</span>
                            <button
                              onClick={() => handleInspectChunks(rec)}
                              className="text-[11px] text-cyan-400 hover:underline"
                            >
                              Inspect
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Chunks Inspection Modal */}
      {inspectDoc && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-hidden shadow-2xl flex flex-col">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900">
              <div className="flex items-center gap-2.5">
                <FileText className="w-5 h-5 text-cyan-400" />
                <div>
                  <h3 className="text-sm font-semibold text-white">{inspectDoc.filename}</h3>
                  <p className="text-[10px] text-slate-500 font-mono">ID: {inspectDoc.document_id}</p>
                </div>
              </div>
              <button
                onClick={() => setInspectDoc(null)}
                className="p-1 text-slate-400 hover:text-white rounded transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-3">
              {loadingChunks ? (
                <div className="py-12 text-center text-sm text-slate-400">Loading document chunks...</div>
              ) : chunks.length === 0 ? (
                <div className="py-12 text-center text-sm text-slate-500">No chunks found for this document.</div>
              ) : (
                chunks.map((c) => (
                  <div key={c.chunk_id} className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2 text-xs">
                    <div className="flex items-center justify-between text-slate-400 font-mono text-[10px]">
                      <span className="text-cyan-400 font-semibold">Sequence #{c.sequence}</span>
                      <span>{c.token_estimate} tokens</span>
                    </div>
                    <p className="text-slate-200 whitespace-pre-wrap leading-relaxed font-mono text-[11px] bg-slate-900/60 p-3 rounded-lg border border-slate-800/80">
                      {c.text}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
