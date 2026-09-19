import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import { DocumentDetailResponse } from '../types/api';
import { Play, FileText, Sparkles, Check, Layers } from 'lucide-react';

const DEMO_PRESETS = [
  {
    id: 'v204',
    name: 'Flagship V-204 Vessel Inspection',
    badge: 'Equipment Inspection',
    title: 'Executive Approval Note for V-204 Inspection',
    goal: 'Review the inspection report for Equipment V-204, verify seal wear tolerance against threshold (0.10mm), calculate wear delta, and produce an executive approval note citing exact chunk evidence and delivering docx, xlsx, pptx, and md artifacts.'
  },
  {
    id: 'p102',
    name: 'Pipeline P-102 Ultrasonic Survey',
    badge: 'Corrosion Survey',
    title: 'Pipeline P-102 Ultrasonic Thickness Degradation Analysis',
    goal: 'Analyze ultrasonic wall thickness measurements for Pipeline P-102. Compute minimum remaining wall thickness, compare with ASME B31.3 corrosion allowance (3.2mm), and synthesize risk mitigation actions.'
  },
  {
    id: 't501',
    name: 'Turbine T-501 Vibration Anomaly',
    badge: 'Telemetry & Anomaly',
    title: 'Turbine T-501 Bearing Vibration & Thermal Excursion Report',
    goal: 'Ingest turbine vibration spectra and bearing temperature telemetry. Evaluate ISO 10816-3 Zone C boundary violations, compute mean bearing temperature drift, and generate an executive engineering report.'
  }
];

export function NewTask() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [title, setTitle] = useState('');
  const [goal, setGoal] = useState('');
  const [documentId, setDocumentId] = useState('');
  const [availableDocs, setAvailableDocs] = useState<DocumentDetailResponse[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const docFromQuery = searchParams.get('document_id');
    const titleFromQuery = searchParams.get('title');
    if (docFromQuery) {
      setDocumentId(docFromQuery);
    }
    if (titleFromQuery) {
      setTitle(titleFromQuery);
    }

    setLoadingDocs(true);
    api.getDocuments()
      .then((docs) => setAvailableDocs(docs))
      .catch((err) => console.error('Failed to load documents:', err))
      .finally(() => setLoadingDocs(false));
  }, [searchParams]);

  const applyPreset = (preset: typeof DEMO_PRESETS[0]) => {
    setTitle(preset.title);
    setGoal(preset.goal);
    if (availableDocs.length > 0 && !documentId) {
      const match = availableDocs.find(d => d.filename.toLowerCase().includes(preset.id));
      if (match) {
        setDocumentId(match.document_id);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !goal.trim()) return;
    
    setIsSubmitting(true);
    setError(null);
    
    try {
      const task = await api.createTask({ 
        title: title.trim(), 
        goal: goal.trim(),
        document_id: documentId.trim() || undefined
      });
      await api.runTask(task.task_id);
      navigate(`/tasks/${task.task_id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to create task');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 p-8 overflow-y-auto max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-white tracking-tight">Create a Governed Task</h1>
        <p className="text-sm text-slate-400 mt-1">
          Submit an industrial task for characterization, qualification gating, and evidence-grounded execution.
        </p>
      </div>

      <div className="mb-8">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            1-Click Industrial Demo Presets (SIH 2026 Scenarios)
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {DEMO_PRESETS.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => applyPreset(p)}
              className="text-left p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-500/50 hover:bg-slate-800/80 transition-all group cursor-pointer"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  {p.badge}
                </span>
                <span className="text-xs text-slate-500 group-hover:text-cyan-400 transition-colors">Apply Preset →</span>
              </div>
              <h4 className="text-sm font-semibold text-slate-200 group-hover:text-white transition-colors line-clamp-1">
                {p.name}
              </h4>
              <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                {p.goal}
              </p>
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-5">
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-slate-300 mb-1.5">
              Task Title
            </label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Executive Approval Note for V-204 Inspection"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-shadow"
              required
            />
          </div>
          
          <div>
            <label htmlFor="goal" className="block text-sm font-medium text-slate-300 mb-1.5">
              Goal Description
            </label>
            <textarea
              id="goal"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="e.g. Review the inspection report for Equipment V-204, verify seal wear tolerance against threshold (0.10mm), and produce an executive approval note citing exact chunk evidence."
              rows={4}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 text-slate-200 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-shadow resize-y"
              required
            />
          </div>

          <div className="pt-2 border-t border-slate-800">
            <div className="flex items-center justify-between mb-2">
              <label htmlFor="documentId" className="block text-sm font-medium text-slate-300">
                Target Grounding Document (Optional)
              </label>
              {availableDocs.length > 0 && (
                <span className="text-xs text-slate-500">
                  {availableDocs.length} document{availableDocs.length > 1 ? 's' : ''} available in Knowledge Base
                </span>
              )}
            </div>

            {availableDocs.length > 0 && (
              <div className="mb-3 flex flex-wrap gap-2">
                {availableDocs.map((doc) => {
                  const isSelected = documentId === doc.document_id;
                  return (
                    <button
                      key={doc.document_id}
                      type="button"
                      onClick={() => setDocumentId(isSelected ? '' : doc.document_id)}
                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition-all border ${
                        isSelected
                          ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50 shadow-sm'
                          : 'bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-300'
                      }`}
                    >
                      {isSelected ? <Check className="w-3.5 h-3.5 text-cyan-400" /> : <FileText className="w-3.5 h-3.5 text-slate-500" />}
                      <span className="truncate max-w-[200px] font-sans">{doc.filename}</span>
                      {doc.metadata?.chunk_count && (
                        <span className="text-[10px] text-slate-500">({doc.metadata.chunk_count} chunks)</span>
                      )}
                    </button>
                  );
                })}
              </div>
            )}

            <div className="relative">
              <input
                id="documentId"
                type="text"
                value={documentId}
                onChange={(e) => setDocumentId(e.target.value)}
                placeholder="Select from above or enter Document UUID (e.g. doc-xxxx)"
                className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-10 pr-4 py-2.5 text-slate-200 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-shadow font-mono text-xs"
              />
              <FileText className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
            </div>
            <p className="text-xs text-slate-500 mt-1.5">
              Specifying a Document ID binds the document's chunk provenance directly into the initial task evidence state.
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="text-xs text-slate-500 flex items-center gap-2">
            <Layers className="w-4 h-4 text-slate-600" />
            <span>Executes through Characterizer (P05) → Qualification (P08) → Evidence (P03) → Artifact Engine (P06)</span>
          </div>
          <button
            type="submit"
            disabled={isSubmitting || !title.trim() || !goal.trim()}
            className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-500 text-white px-6 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {isSubmitting ? (
              <span className="animate-pulse">Submitting Task...</span>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Submit & Execute Task
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
