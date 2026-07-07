"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useMemo, useState } from "react";

import { PasswordInput } from "@/components/password-input";
import { apiFetch } from "@/lib/auth";

function readTokenFromUrl(searchParams: URLSearchParams): string {
  const fromParams = searchParams.get("token");
  if (fromParams) return fromParams;
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("token") ?? "";
}

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = useMemo(() => readTokenFromUrl(searchParams), [searchParams]);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!token) {
      setError("Missing reset token. Use the link from your email or request a new one.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setSubmitting(true);
    try {
      await apiFetch<{ message: string }>("/api/v1/auth/password-reset/confirm", {
        method: "POST",
        body: JSON.stringify({ token, password }),
      });
      router.push("/portal/login?reset=success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update password.");
    } finally {
      setSubmitting(false);
    }
  }

  if (!token) {
    return (
      <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
        This page needs a valid link from your email.{" "}
        <Link href="/portal/forgot-password" className="font-medium text-emerald-800 hover:underline">
          Request a new link
        </Link>
        .
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="mt-8 space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-sm text-slate-600">
        Choose a strong password (at least 12 characters with letters and numbers).
      </p>
      <PasswordInput
        id="new-password"
        label="New password"
        value={password}
        onChange={setPassword}
        autoComplete="new-password"
        minLength={12}
        required
      />
      <PasswordInput
        id="confirm-password"
        label="Confirm password"
        value={confirm}
        onChange={setConfirm}
        autoComplete="new-password"
        minLength={12}
        required
      />
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800" role="alert">
          {error}
          {error.toLowerCase().includes("expired") || error.toLowerCase().includes("used") ? (
            <p className="mt-2">
              <Link href="/portal/forgot-password" className="font-medium text-emerald-800 hover:underline">
                Request a new secure link
              </Link>
            </p>
          ) : null}
        </div>
      )}
      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-md bg-emerald-800 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? "Saving…" : "Save password"}
      </button>
    </form>
  );
}

export default function PortalResetPasswordPage() {
  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-2xl font-semibold text-slate-900">Set your password</h1>
      <p className="mt-2 text-sm text-slate-600">
        This secure link works once and stays valid for up to 72 hours. After saving, sign in with
        your new password.
      </p>
      <Suspense fallback={<p className="mt-8 text-sm text-slate-500">Loading…</p>}>
        <ResetPasswordForm />
      </Suspense>
    </div>
  );
}
