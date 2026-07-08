"use client";

import type { ApiEnvelope, AuthTokens, UserProfile } from "@lexflow/shared";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { formatApiError, type ProblemBody } from "@/lib/api-errors";
import {
  canAccessEnterpriseDashboard,
  canAccessPortal,
  type LoginAudience,
} from "@/lib/permissions";

const TOKEN_KEY = "lexflow_access_token";
const REFRESH_KEY = "lexflow_refresh_token";

function apiBase(): string {
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

const API_TIMEOUT_MS = 15_000;

type SessionExpiredListener = () => void;
const sessionExpiredListeners = new Set<SessionExpiredListener>();

function notifySessionExpired() {
  sessionExpiredListeners.forEach((listener) => listener());
}

export function getStoredAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

function getStoredRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

function storeTokens(tokens: AuthTokens) {
  localStorage.setItem(TOKEN_KEY, tokens.accessToken);
  localStorage.setItem(REFRESH_KEY, tokens.refreshToken);
}

function clearStoredTokens() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

async function fetchWithTimeout(
  input: string,
  init?: RequestInit,
  timeoutMs = API_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(
        "Cannot reach the API (timeout). Ensure the stack is running: make dev, then check http://localhost:8000/health",
      );
    }
    throw new Error(
      "Cannot reach the API. Start the stack with make dev and confirm http://localhost:8000/health responds.",
    );
  } finally {
    clearTimeout(timer);
  }
}

async function parseEnvelope<T>(res: Response): Promise<T> {
  const text = await res.text();
  let body: unknown = {};
  if (text) {
    try {
      body = JSON.parse(text) as ApiEnvelope<T> | ProblemBody;
    } catch {
      body = {};
    }
  }
  if (!res.ok) {
    const problem = body as ProblemBody;
    const envelope = body as ApiEnvelope<T>;
    const message = formatApiError(
      problem.detail || problem.errors ? problem : envelope,
      res.statusText || "Request failed",
    );
    throw new Error(message);
  }
  return (body as ApiEnvelope<T>).data;
}

let refreshInFlight: Promise<AuthTokens> | null = null;

async function refreshAccessToken(): Promise<AuthTokens> {
  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    const refreshToken = getStoredRefreshToken();
    if (!refreshToken) {
      throw new Error("Session expired. Please sign in again.");
    }
    const res = await fetchWithTimeout(`${apiBase()}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refreshToken }),
    });
    const tokens = await parseEnvelope<AuthTokens>(res);
    storeTokens(tokens);
    return tokens;
  })();

  try {
    return await refreshInFlight;
  } finally {
    refreshInFlight = null;
  }
}

function shouldAttemptRefresh(path: string, res: Response, hadToken: boolean): boolean {
  return (
    hadToken &&
    res.status === 401 &&
    !path.includes("/auth/refresh") &&
    !path.includes("/auth/login")
  );
}

async function authorizedFetch(
  path: string,
  options: RequestInit & { idempotencyKey?: string } = {},
  token?: string | null,
  allowRefresh = true,
): Promise<Response> {
  const { idempotencyKey, ...fetchOptions } = options;
  const headers = new Headers(fetchOptions.headers);
  if (!headers.has("Content-Type") && fetchOptions.body) {
    headers.set("Content-Type", "application/json");
  }
  if (idempotencyKey) {
    headers.set("Idempotency-Key", idempotencyKey);
  }
  const access = token !== undefined ? token : getStoredAccessToken();
  const hadToken = Boolean(access);
  if (access) {
    headers.set("Authorization", `Bearer ${access}`);
  }

  let res = await fetchWithTimeout(`${apiBase()}${path}`, { ...fetchOptions, headers });
  if (allowRefresh && shouldAttemptRefresh(path, res, hadToken)) {
    try {
      const tokens = await refreshAccessToken();
      headers.set("Authorization", `Bearer ${tokens.accessToken}`);
      res = await fetchWithTimeout(`${apiBase()}${path}`, { ...fetchOptions, headers });
    } catch {
      clearStoredTokens();
      notifySessionExpired();
    }
  }
  if (res.status === 401 && allowRefresh && hadToken) {
    clearStoredTokens();
    notifySessionExpired();
  }
  return res;
}

export function newIdempotencyKey(): string {
  return crypto.randomUUID();
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { idempotencyKey?: string } = {},
  token?: string | null,
): Promise<T> {
  const res = await authorizedFetch(path, options, token);
  return parseEnvelope<T>(res);
}

export async function apiFetchVoid(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<void> {
  const res = await authorizedFetch(path, options, token);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(formatApiError(body, res.statusText));
  }
}

export async function apiFetchList<T>(
  path: string,
  token?: string | null,
): Promise<{ items: T[]; meta: ApiEnvelope<T[]>["meta"] }> {
  const res = await authorizedFetch(path, {}, token);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(formatApiError(body, res.statusText));
  }
  const json = (await res.json()) as ApiEnvelope<T[]>;
  return { items: json.data, meta: json.meta };
}

type AuthContextValue = {
  user: UserProfile | null;
  loading: boolean;
  login: (email: string, password: string, audience?: LoginAudience) => Promise<UserProfile>;
  logout: () => void;
  refreshProfile: () => Promise<UserProfile | null>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function redirectToLogin() {
  if (typeof window === "undefined") return;
  const path = window.location.pathname;
  if (path.startsWith("/login") || path.startsWith("/portal/login")) return;
  const target = path.startsWith("/portal") ? "/portal/login?session=expired" : "/login?session=expired";
  window.location.assign(target);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    clearStoredTokens();
    setUser(null);
  }, []);

  const refreshProfile = useCallback(async () => {
    const token = getStoredAccessToken();
    if (!token) {
      setUser(null);
      return null;
    }
    const profile = await apiFetch<UserProfile>("/api/v1/auth/me", {}, token);
    setUser(profile);
    return profile;
  }, []);

  const login = useCallback(
    async (email: string, password: string, audience: LoginAudience = "enterprise") => {
      const tokens = await apiFetch<AuthTokens>(
        "/api/v1/auth/login",
        {
          method: "POST",
          body: JSON.stringify({ email, password, audience }),
        },
        null,
      );
      storeTokens(tokens);
      const profile = await apiFetch<UserProfile>("/api/v1/auth/me", {}, tokens.accessToken);
      setUser(profile);
      return profile;
    },
    [],
  );

  useEffect(() => {
    const onExpired = () => {
      setUser(null);
      redirectToLogin();
    };
    sessionExpiredListeners.add(onExpired);
    return () => {
      sessionExpiredListeners.delete(onExpired);
    };
  }, []);

  useEffect(() => {
    async function bootstrap() {
      const access = getStoredAccessToken();
      const refresh = getStoredRefreshToken();
      if (!access && !refresh) {
        setLoading(false);
        return;
      }
      try {
        if (access) {
          const profile = await apiFetch<UserProfile>("/api/v1/auth/me", {}, access);
          setUser(profile);
          return;
        }
      } catch {
        // fall through to refresh
      }
      if (refresh) {
        try {
          await refreshAccessToken();
          const profile = await apiFetch<UserProfile>("/api/v1/auth/me");
          setUser(profile);
          return;
        } catch {
          logout();
        }
      } else {
        logout();
      }
    }

    bootstrap().finally(() => setLoading(false));
  }, [logout]);

  const value = useMemo(
    () => ({ user, loading, login, logout, refreshProfile }),
    [user, loading, login, logout, refreshProfile],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function useEnterpriseAccess() {
  const { user, loading } = useAuth();
  return {
    loading,
    user,
    allowed: user ? canAccessEnterpriseDashboard(user.permissions) : false,
  };
}

export function usePortalAccess() {
  const { user, loading } = useAuth();
  return {
    loading,
    user,
    allowed: user ? canAccessPortal(user.permissions) : false,
  };
}
