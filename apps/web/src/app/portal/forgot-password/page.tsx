"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { apiFetch } from "@/lib/auth";

export default function PortalForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setMessage(null);
    try {
      const result = await apiFetch<{ message: string }>("/api/v1/auth/password-reset/request", {
        method: "POST",
        body: JSON.stringify({ email: email.trim() }),
      });
      setMessage(result.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed. Try again later.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-2xl font-semibold text-slate-900">Forgot password</h1>
      <p className="mt-2 text-sm text-slate-600">
        Enter your email and we&apos;ll send a secure one-time link to set or reset your portal
        password. For security, we always show the same confirmation whether or not the email is
        registered.
      </p>
      <form
        onSubmit={onSubmit}
        className="mt-8 space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
      >
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
        {message && (
          <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900" role="status">
            {message}
          </div>
        )}
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
          {submitting ? "Sending…" : "Send secure link"}
        </button>
      </form>
      <p className="mt-6 text-sm text-slate-600">
        <Link href="/portal/login" className="text-emerald-800 hover:underline">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
