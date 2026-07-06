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

export function isApiHealthy(response: ApiHealthResponse): boolean {
  return response.status === "ok" && response.service === "api";
}
