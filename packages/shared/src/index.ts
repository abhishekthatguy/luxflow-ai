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
  permissions: string[];
}

export interface AdminUserSummary {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  status: string;
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

export interface NotificationDispatchSummary {
  emailQueued?: number;
  slackQueued?: number;
  teamsQueued?: number;
  inAppCount?: number;
  correlationId?: string | null;
}

export interface AISummary {
  id: string;
  caseId: string;
  summaryType: string;
  content?: string | null;
  status: string;
  model: string;
  createdAt: string;
  notificationDispatch?: NotificationDispatchSummary | null;
}

export interface WorkflowExecution {
  id: string;
  caseId?: string | null;
  workflowSlug?: string | null;
  workflowName?: string | null;
  status: string;
  correlationId: string;
  startedAt?: string | null;
  completedAt?: string | null;
  errorMessage?: string | null;
  createdAt: string;
}

export interface AuditLogEntry {
  id: string;
  firmId: string;
  actorId?: string | null;
  action: string;
  resourceType: string;
  resourceId?: string | null;
  details: Record<string, unknown>;
  createdAt: string;
}

export interface NotificationItem {
  id: string;
  userId: string;
  caseId?: string | null;
  firmId: string;
  channel: string;
  title: string;
  body: string;
  description?: string | null;
  status: string;
  readAt?: string | null;
  sentAt?: string | null;
  eventType?: string | null;
  workflowSlug?: string | null;
  priority?: string | null;
  actionUrl?: string | null;
  correlationId?: string | null;
  metadata: Record<string, unknown>;
  createdAt: string;
}

export function isApiHealthy(response: ApiHealthResponse): boolean {
  return response.status === "ok" && response.service === "api";
}

/** Supported case practice areas — keep in sync with API domain/practice_areas.py */
export const PRACTICE_AREAS = [
  { value: "litigation", label: "Litigation" },
  { value: "corporate", label: "Corporate & Transactional" },
  { value: "ip", label: "Intellectual Property" },
  { value: "regulatory", label: "Regulatory & Compliance" },
  { value: "employment", label: "Employment & Labor" },
  { value: "real_estate", label: "Real Estate" },
  { value: "family", label: "Family Law" },
  { value: "immigration", label: "Immigration" },
  { value: "criminal", label: "Criminal Defense" },
  { value: "other", label: "Other" },
] as const;

export type PracticeAreaValue = (typeof PRACTICE_AREAS)[number]["value"];
