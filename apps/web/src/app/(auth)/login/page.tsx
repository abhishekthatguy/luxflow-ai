"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";

import { devEmailHint } from "@/lib/api-errors";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { login, user, loading } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("jane@example.com");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const emailHint = useMemo(() => devEmailHint(email), [email]);

  if (!loading && user) {
    router.replace("/cases");
    return null;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const hint = devEmailHint(email);
    if (hint) {
      setError(hint);
      setSubmitting(false);
      return;
    }

    try {
      await login(email.trim(), password);
      router.push("/cases");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed. Check email and password.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center p-8">
      <h1 className="text-2xl font-semibold">Sign in</h1>
      <div className="mt-3 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
        <p className="font-medium">Dev credentials</p>
        <p className="mt-1 font-mono text-xs">admin@example.com · jane@example.com</p>
        <p className="font-mono text-xs">password123</p>
      </div>
      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <label className="block text-sm">
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              setError(null);
            }}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            autoComplete="email"
            required
          />
        </label>
        {emailHint && !error && (
          <p className="text-sm text-amber-700">{emailHint}</p>
        )}
        <label className="block text-sm">
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            autoComplete="current-password"
            required
            minLength={8}
          />
        </label>
        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800" role="alert">
            {error}
          </div>
        )}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </main>
  );
}
