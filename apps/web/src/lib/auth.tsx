"use client";

import type { ApiEnvelope, AuthTokens, UserProfile } from "@lexflow/shared";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { formatApiError, type ProblemBody } from "@/lib/api-errors";

const TOKEN_KEY = "lexflow_access_token";
const REFRESH_KEY = "lexflow_refresh_token";

function apiBase(): string {
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

const API_TIMEOUT_MS = 15_000;

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

export function getStoredAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
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

export function newIdempotencyKey(): string {
  return crypto.randomUUID();
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { idempotencyKey?: string } = {},
  token?: string | null,
): Promise<T> {
  const { idempotencyKey, ...fetchOptions } = options;
  const headers = new Headers(fetchOptions.headers);
  if (!headers.has("Content-Type") && fetchOptions.body) {
    headers.set("Content-Type", "application/json");
  }
  if (idempotencyKey) {
    headers.set("Idempotency-Key", idempotencyKey);
  }
  const access = token ?? getStoredAccessToken();
  if (access) {
    headers.set("Authorization", `Bearer ${access}`);
  }
  const res = await fetchWithTimeout(`${apiBase()}${path}`, { ...fetchOptions, headers });
  return parseEnvelope<T>(res);
}

export async function apiFetchVoid(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<void> {
  const headers = new Headers(options.headers);
  const access = token ?? getStoredAccessToken();
  if (access) headers.set("Authorization", `Bearer ${access}`);
  const res = await fetchWithTimeout(`${apiBase()}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(formatApiError(body, res.statusText));
  }
}

export async function apiFetchList<T>(
  path: string,
  token?: string | null,
): Promise<{ items: T[]; meta: ApiEnvelope<T[]>["meta"] }> {
  const headers = new Headers();
  const access = token ?? getStoredAccessToken();
  if (access) headers.set("Authorization", `Bearer ${access}`);
  const res = await fetchWithTimeout(`${apiBase()}${path}`, { headers });
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
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    setUser(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await apiFetch<AuthTokens>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem(TOKEN_KEY, tokens.accessToken);
    localStorage.setItem(REFRESH_KEY, tokens.refreshToken);
    const profile = await apiFetch<UserProfile>("/api/v1/auth/me", {}, tokens.accessToken);
    setUser(profile);
  }, []);

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) {
      setLoading(false);
      return;
    }
    apiFetch<UserProfile>("/api/v1/auth/me", {}, token)
      .then(setUser)
      .catch(logout)
      .finally(() => setLoading(false));
  }, [logout]);

  const value = useMemo(
    () => ({ user, loading, login, logout }),
    [user, loading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
