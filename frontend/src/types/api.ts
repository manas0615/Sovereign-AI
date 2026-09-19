export interface TaskCreateRequest {
  title: string;
  goal: string;
  document_id?: string;
}

export interface TaskResponse {
  task_id: string;
  title: string;
  goal: string;
  status: 'PENDING' | 'ACTIVE' | 'COMPLETED' | 'FAILED' | 'PAUSED';
  created_at: string;
  updated_at: string;
  latest_decision?: string;
  findings_count: number;
  document_id?: string;
}

export interface ArtifactMetadataResponse {
  artifact_id: string;
  task_id: string;
  title: string;
  type: string;
  status: string;
  created_at: string;
  filename?: string | null;
  file_path?: string | null;
  size_bytes?: number | null;
  content_hash?: string | null;
  sections_rendered?: string[];
  source_references?: Array<Record<string, any>>;
}

export interface DocumentIngestResponse {
  document_id: string;
  status: string;
}

export interface DocumentDetailResponse {
  document_id: string;
  filename: string;
  source_path: string;
  document_type: string;
  file_size: number;
  content_hash: string;
  created_at: string;
  ingested_at?: string | null;
  status: string;
  metadata: Record<string, any>;
}

export interface DocumentChunkResponse {
  chunk_id: string;
  document_id: string;
  sequence: number;
  page_range?: string | null;
  section?: string | null;
  text: string;
  token_estimate: number;
  metadata: Record<string, any>;
}

export interface CitationItem {
  chunk_id: string;
  document_id: string;
  filename: string;
  locator: string;
  text: string;
  score: number;
  content_hash?: string | null;
}

export interface CodeExecutionResult {
  code: string;
  stdout: string;
  stderr: string;
  exit_code: number;
  duration_ms: number;
  success: boolean;
  security_mode: string;
  error?: string | null;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  document_id?: string;
  mode?: 'chat' | 'coding' | 'governed_task';
  execute_code?: boolean;
}

export interface ChatResponse {
  message_id: string;
  conversation_id: string;
  role: 'assistant' | 'user';
  content: string;
  citations: CitationItem[];
  code_execution?: CodeExecutionResult | null;
  authority_decision: string;
  authorizing_passport_id?: string | null;
  deployment_identity?: string | null;
  capability_contract?: string | null;
  task_id?: string | null;
  artifacts?: ArtifactMetadataResponse[];
  created_at: string;
}

export interface CodeExecuteRequest {
  code: string;
  timeout_seconds?: number;
}

export interface CodeExecuteResponse {
  success: boolean;
  stdout: string;
  stderr: string;
  exit_code: number;
  duration_ms: number;
  security_mode: string;
  error?: string | null;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  documentId?: string;
  mode?: 'chat' | 'coding';
}


export interface HealthResponse {
  status: string;
  version: string;
  uptime: number;
}

export interface CapabilityPassportResponse {
  passport_id: string;
  qualification_identity: string;
  deployment_identity: string;
  capability_contract: string;
  result_id: string;
  qualification_status: string;
  qualification_timestamp: string;
  invalidation_info?: Record<string, any> | null;
  metadata?: {
    pass_rate?: number;
    evaluated_trials?: number;
    [key: string]: any;
  } | null;
}

export interface TrustManifestEvidenceItem {
  evidence_id?: string;
  source_id: string;
  chunk_id?: string | null;
  locator: string;
  metadata?: Record<string, any>;
}

export interface TrustManifestResponse {
  manifest_version?: string;
  manifest_id?: string;
  artifact?: {
    artifact_id: string;
    content_hash: string;
    artifact_type: string;
    status: string;
  };
  task?: {
    task_id: string;
    status: string;
    goal: string;
  };
  capability?: {
    name: string;
  } | null;
  deployment?: {
    deployment_identity: string;
    model: string;
  } | null;
  qualification?: {
    qualification_identity: string;
    passport_id: string;
    status: string;
  } | null;
  authority?: {
    decision: string;
    reason: string;
  } | null;
  execution?: {
    trace_reference: string;
    state_items: any[];
  };
  evidence?: TrustManifestEvidenceItem[];
  integrity?: {
    algorithm: string;
    artifact_content_hash: string;
  };

  // Optional flat properties
  artifact_id?: string;
  task_id?: string;
  content_hash?: string;
  hash_algorithm?: string;
  generation_timestamp?: string;
  authorizing_passport_id?: string | null;
  deployment_identity?: string | null;
  capability_contract?: string | null;
  authority_decision?: string | null;
  evidence_items?: TrustManifestEvidenceItem[];
  software_boundary?: {
    local_execution: boolean;
    network_isolated: boolean;
    governed_tools_enforced: boolean;
  };
}


