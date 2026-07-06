export interface ApiEnvelope<T> {
  data: T;
  meta?: {
    requestId?: string;
    page?: number;
    pageSize?: number;
    total?: number;
    totalPages?: number;
  };
}

export interface ApiHealthResponse {
  status: string;
  service: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface UserProfile {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  firmId: string;
  roles: string[];
}

export interface ClientSummary {
  id: string;
  name: string;
  type: string;
  email?: string | null;
  phone?: string | null;
}

export interface ClientDetail extends ClientSummary {
  firmId: string;
  version: number;
  createdAt: string;
  updatedAt: string;
}

export interface CaseSummary {
  id: string;
  caseNumber: string;
  title: string;
  status: string;
  priority: string;
  practiceArea?: string | null;
  clientId: string;
  leadAttorneyId: string;
  version: number;
  createdAt: string;
}

export interface TimelineEvent {
  id: string;
  caseId: string;
  eventType: string;
  title: string;
  payload: Record<string, unknown>;
  occurredAt: string;
}

export interface DocumentSummary {
  id: string;
  caseId: string;
  title: string;
  documentType: string;
  status: string;
  ocrStatus: string;
  mimeType: string;
  fileSizeBytes: number;
  createdAt: string;
}

export interface JobStatus {
  id: string;
  jobType: string;
  status: string;
  progress: number;
  result?: Record<string, unknown> | null;
  error?: Record<string, unknown> | null;
}

export interface AISummary {
  id: string;
  caseId: string;
  summaryType: string;
  content?: string | null;
  status: string;
  model: string;
  createdAt: string;
}

export interface WorkflowExecution {
  id: string;
  caseId?: string | null;
  status: string;
  correlationId: string;
  startedAt?: string | null;
  completedAt?: string | null;
  createdAt: string;
}

export function isApiHealthy(response: ApiHealthResponse): boolean {
  return response.status === "ok" && response.service === "api";
}
