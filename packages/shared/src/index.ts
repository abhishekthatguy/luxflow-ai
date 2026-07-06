export interface ApiHealthResponse {
  status: string;
  service: string;
}

export function isApiHealthy(response: ApiHealthResponse): boolean {
  return response.status === "ok" && response.service === "api";
}
