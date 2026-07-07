"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";

import { PasswordInput } from "@/components/password-input";
import { useAuth } from "@/lib/auth";

function PortalLoginForm() {
  const { login, user, loading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const resetSuccess = searchParams.get("reset") === "success";
  const [email, setEmail] = useState(searchParams.get("email") ?? "");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!loading && user) {
    router.replace("/portal");
    return null;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(email.trim(), password);
      router.push("/portal");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed. Check your credentials.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mt-8 space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      {resetSuccess && (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900" role="status">
          Password saved. Sign in with your new password.
        </div>
      )}
      <label className="block text-sm">
        Email
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          autoComplete="email"
          required
        />
      </label>
      <PasswordInput
        id="login-password"
        label="Password"
        value={password}
        onChange={setPassword}
        autoComplete="current-password"
        required
      />
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800" role="alert">
          {error}
        </div>
      )}
      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-md bg-emerald-800 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? "Signing in…" : "Sign in"}
      </button>
      <p className="text-center text-sm text-slate-600">
        First time here or forgot your password?{" "}
        <Link href="/portal/forgot-password" className="text-emerald-800 hover:underline">
          Email me a secure link
        </Link>
      </p>
    </form>
  );
}

export default function PortalLoginPage() {
  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-2xl font-semibold text-slate-900">Client portal sign in</h1>
      <p className="mt-2 text-sm text-slate-600">
        New clients: use the <strong>Set your password</strong> button in your welcome email first.
        Already registered? Sign in below or{" "}
        <Link href="/portal/forgot-password" className="text-emerald-800 hover:underline">
          request a reset link
        </Link>
        .
      </p>
      <Suspense fallback={<p className="mt-8 text-sm text-slate-500">Loading…</p>}>
        <PortalLoginForm />
      </Suspense>
    </div>
  );
}
