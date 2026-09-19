/**
 * User-facing display labels and formatters for Sovereign AI.
 * Replaces cryptic internal package codes and database keys with clear,
 * understandable UI terminology while preserving internal correctness.
 */

export const PACKAGE_LABELS: Record<string, { code: string; label: string; full: string; description: string }> = {
  P01: {
    code: 'P01',
    label: 'Model Runtime',
    full: 'P01 — Model Runtime',
    description: 'Local open-weight LLM inference and sequential model swapping.'
  },
  P02: {
    code: 'P02',
    label: 'Vision & Multimodal',
    full: 'P02 — Vision & Multimodal Processing',
    description: 'Local OCR and document rasterization.'
  },
  P03: {
    code: 'P03',
    label: 'Knowledge & Document Processing',
    full: 'P03 — Knowledge & Document Processing',
    description: 'Local SQLite FTS5 BM25 knowledge indexing and document parsing.'
  },
  P04: {
    code: 'P04',
    label: 'Governed Tool Execution',
    full: 'P04 — Governed Tool Execution',
    description: 'AST-checked Python sandbox execution and math calculation tools.'
  },
  P05: {
    code: 'P05',
    label: 'Agent Orchestration',
    full: 'P05 — Agent Orchestration',
    description: 'Intent characterization, capability routing, and task decomposition.'
  },
  P06: {
    code: 'P06',
    label: 'Artifact & Audit Management',
    full: 'P06 — Artifact & Audit Management',
    description: 'Multi-format deliverable rendering (DOCX, XLSX, PPTX, PDF) and storage.'
  },
  P07: {
    code: 'P07',
    label: 'API Gateway',
    full: 'P07 — API Gateway',
    description: 'FastAPI local endpoint interface and schema validation.'
  },
  P08: {
    code: 'P08',
    label: 'Model Qualification & Authority',
    full: 'P08 — Model Qualification & Authority',
    description: 'Empirical capability passports, contract matching, and fail-closed authority.'
  },
  P09: {
    code: 'P09',
    label: 'User Interface',
    full: 'P09 — User Interface',
    description: 'Conversational workbench and governance administration frontend.'
  }
};

/**
 * Returns a user-friendly label for a package code.
 */
export function getPackageDisplay(code: string, mode: 'full' | 'short' | 'code-first' = 'full'): string {
  const pkg = PACKAGE_LABELS[code.toUpperCase()];
  if (!pkg) return code;
  if (mode === 'short') return pkg.label;
  if (mode === 'code-first') return `${pkg.code}: ${pkg.label}`;
  return pkg.full;
}

/**
 * Human-readable labels for capability contract keys.
 */
export const CAPABILITY_LABELS: Record<string, string> = {
  'general_reasoning:v1': 'General Reasoning (v1)',
  'document_extraction:v1': 'Document Extraction (v1)',
  'document_ocr:v1': 'Document OCR & Parsing (v1)',
  'code_generation:v1': 'Code Generation (v1)',
  'structured_output:v1': 'Structured Deliverables (v1)',
  'calculator:v1': 'Governed Calculation (v1)'
};

export function getCapabilityDisplay(cap: string): string {
  return CAPABILITY_LABELS[cap] || cap;
}

/**
 * Formats a document title cleanly while preserving access to the raw filename.
 */
export function formatDocumentDisplayName(filename: string): string {
  if (!filename) return 'Untitled Document';
  const clean = filename.replace(/\.(pdf|docx|xlsx|pptx|txt|md|csv)$/i, '');
  return clean
    .split(/[-_]/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
