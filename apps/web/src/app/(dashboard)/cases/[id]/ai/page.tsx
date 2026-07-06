"use client";

import type { AISummary, JobStatus } from "@lexflow/shared";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { CaseNav } from "@/components/case-nav";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetch, apiFetchList } from "@/lib/auth";

type JobAccepted = { jobId: string; statusUrl: string };

async function pollJob(statusUrl: string, maxAttempts = 30): Promise<JobStatus> {
  for (let i = 0; i < maxAttempts; i += 1) {
    const job = await apiFetch<JobStatus>(statusUrl);
    if (job.status === "completed" || job.status === "failed") return job;
    await new Promise((r) => setTimeout(r, 2000));
  }
  throw new Error("Job timed out");
}

export default function CaseAIPage() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;
  const [summaries, setSummaries] = useState<AISummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!caseId) return;
    apiFetchList<AISummary>(`/api/v1/cases/${caseId}/ai/summaries`)
      .then(({ items }) => setSummaries(items))
      .catch((e: Error) => setError(e.message));
  }, [caseId]);

  useEffect(() => {
    load();
  }, [load]);

  async function requestSummary() {
    if (!caseId) return;
    setLoading(true);
    setError(null);
    try {
      const accepted = await apiFetch<JobAccepted>(`/api/v1/cases/${caseId}/ai/summarize`, {
        method: "POST",
        body: JSON.stringify({ summaryType: "case_overview" }),
      });
      await pollJob(accepted.statusUrl);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Summary request failed");
    } finally {
      setLoading(false);
    }
  }

  async function approve(summaryId: string) {
    await apiFetch(`/api/v1/ai/summaries/${summaryId}/approve`, { method: "POST" });
    load();
  }

  async function reject(summaryId: string) {
    const reason = window.prompt("Rejection reason?") ?? "Needs revision";
    await apiFetch(`/api/v1/ai/summaries/${summaryId}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
    load();
  }

  return (
    <DashboardShell>
      <div className="flex items-start justify-between gap-4">
        <h1 className="text-2xl font-semibold">AI Summaries</h1>
        {caseId && <CaseNav caseId={caseId} active="ai" />}
      </div>

      <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
        AI-generated drafts require attorney approval before team visibility.
      </div>

      <button
        type="button"
        onClick={requestSummary}
        disabled={loading}
        className="mt-6 rounded-md bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50"
      >
        {loading ? "Generating…" : "Request case summary"}
      </button>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <ul className="mt-8 space-y-4" data-testid="ai-summaries-list">
        {summaries.map((s) => (
          <li key={s.id} className="rounded-md border border-slate-200 p-4 text-sm">
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium capitalize">{s.summaryType.replace("_", " ")}</span>
              <span className="rounded-full bg-slate-100 px-2 py-1 text-xs capitalize">
                {s.status}
              </span>
            </div>
            {s.content && (
              <pre className="mt-3 whitespace-pre-wrap rounded bg-slate-50 p-3 text-xs">
                {s.content}
              </pre>
            )}
            {s.status === "draft" && (
              <div className="mt-3 flex gap-2">
                <button
                  type="button"
                  onClick={() => approve(s.id)}
                  className="rounded bg-green-700 px-3 py-1 text-xs text-white"
                >
                  Approve
                </button>
                <button
                  type="button"
                  onClick={() => reject(s.id)}
                  className="rounded bg-red-700 px-3 py-1 text-xs text-white"
                >
                  Reject
                </button>
              </div>
            )}
          </li>
        ))}
        {summaries.length === 0 && (
          <li className="text-slate-500">No AI summaries yet.</li>
        )}
      </ul>
    </DashboardShell>
  );
}
