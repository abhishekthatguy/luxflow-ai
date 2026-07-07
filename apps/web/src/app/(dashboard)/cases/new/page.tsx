"use client";

import { PRACTICE_AREAS, type ClientSummary } from "@lexflow/shared";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useRef, useState } from "react";

import { AccessDenied, DashboardShell } from "@/components/dashboard-shell";
import { apiFetch, apiFetchList, newIdempotencyKey, useAuth } from "@/lib/auth";
import { canCreateCase } from "@/lib/permissions";

export default function NewCasePage() {
  const { user } = useAuth();
  const router = useRouter();
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [clientId, setClientId] = useState("");
  const [title, setTitle] = useState("");
  const [practiceArea, setPracticeArea] = useState<string>("litigation");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const idempotencyRef = useRef(newIdempotencyKey());

  useEffect(() => {
    apiFetchList<ClientSummary>("/api/v1/clients").then(({ items }) => {
      setClients(items);
      if (items[0]) setClientId(items[0].id);
    });
  }, []);

  if (user && !canCreateCase(user.permissions)) {
    return (
      <DashboardShell>
        <AccessDenied message="Your role is not permitted to create cases." />
      </DashboardShell>
    );
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!user) return;
    setSubmitting(true);
    setError(null);
    try {
      const created = await apiFetch<{ id: string; caseNumber: string }>("/api/v1/cases", {
        method: "POST",
        body: JSON.stringify({
          clientId,
          title,
          practiceArea,
          leadAttorneyId: user.id,
        }),
        idempotencyKey: idempotencyRef.current,
      });
      router.push(`/cases/${created.id}/overview`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create case");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <DashboardShell>
      <h1 className="text-2xl font-semibold">New case</h1>
      <form onSubmit={onSubmit} className="mt-6 max-w-lg space-y-4" data-testid="new-case-form">
        <label className="block text-sm">
          Client
          <select
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            required
            data-testid="case-client-select"
          >
            {clients.length === 0 ? (
              <option value="">No clients — add one first</option>
            ) : (
              clients.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))
            )}
          </select>
        </label>

        <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">
          <p className="font-medium text-slate-700">Case number</p>
          <p className="mt-1" data-testid="case-number-auto-hint">
            Assigned automatically when you create the case (e.g. {new Date().getFullYear()}-00001).
          </p>
        </div>

        <label className="block text-sm">
          Title
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Brief matter description"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            required
            data-testid="case-title-input"
          />
        </label>

        <label className="block text-sm">
          Practice area
          <select
            value={practiceArea}
            onChange={(e) => setPracticeArea(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            required
            data-testid="case-practice-area-select"
          >
            {PRACTICE_AREAS.map((area) => (
              <option key={area.value} value={area.value}>
                {area.label}
              </option>
            ))}
          </select>
        </label>

        {error && (
          <p className="text-sm text-red-600" role="alert">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting || clients.length === 0}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          {submitting ? "Creating…" : "Create case"}
        </button>
      </form>
    </DashboardShell>
  );
}
