import {
  TaskCreateRequest,
  TaskResponse,
  ArtifactMetadataResponse,
  DocumentIngestResponse,
  DocumentDetailResponse,
  DocumentChunkResponse,
  ChatRequest,
  ChatResponse,
  CodeExecuteRequest,
  CodeExecuteResponse,
  HealthResponse,
  CapabilityPassportResponse,
  TrustManifestResponse
} from '../types/api';

const BASE_URL = '/api/v1';

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      ...(options?.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let errorMessage = 'An error occurred';
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      // Ignore
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

export const api = {
  checkHealth: () => fetchApi<HealthResponse>('/health'),
  
  getTasks: () =>
    fetchApi<TaskResponse[]>('/tasks'),

  createTask: (data: TaskCreateRequest) => 
    fetchApi<TaskResponse>('/tasks', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
    
  getTask: (taskId: string) => 
    fetchApi<TaskResponse>(`/tasks/${taskId}`),

  getTaskState: (taskId: string) =>
    fetchApi<any[]>(`/tasks/${taskId}/state`),
    
  runTask: (taskId: string) => 
    fetchApi<{status: string, task_id: string}>(`/tasks/${taskId}/run`, {
      method: 'POST'
    }),
    
  getTaskArtifacts: (taskId: string) => 
    fetchApi<ArtifactMetadataResponse[]>(`/tasks/${taskId}/artifacts`),

  getAllArtifacts: () =>
    fetchApi<ArtifactMetadataResponse[]>('/artifacts'),

  getArtifactDetails: (artifactId: string) =>
    fetchApi<ArtifactMetadataResponse>(`/artifacts/${artifactId}/details`),
    
  getArtifactDownloadUrl: (artifactId: string) => 
    `${BASE_URL}/artifacts/${artifactId}/download`,

  getTrustManifest: (artifactId: string) =>
    fetchApi<TrustManifestResponse>(`/artifacts/${artifactId}/manifest`),

  getPassports: () =>
    fetchApi<CapabilityPassportResponse[]>('/qualifications/passports'),

  getDocuments: () =>
    fetchApi<DocumentDetailResponse[]>('/knowledge/documents'),

  getDocumentChunks: (documentId: string) =>
    fetchApi<DocumentChunkResponse[]>(`/knowledge/documents/${documentId}/chunks`),

  chat: (data: ChatRequest) =>
    fetchApi<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(data)
    }),

  executeCode: (data: CodeExecuteRequest) =>
    fetchApi<CodeExecuteResponse>('/code/execute', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
    
  uploadDocument: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetchApi<DocumentIngestResponse>('/knowledge/documents', {
      method: 'POST',
      body: formData
    });
  }
};



