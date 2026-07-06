"use client";

import type { WorkflowExecution } from "@lexflow/shared";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { CaseNav } from "@/components/case-nav";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetch, apiFetchList } from "@/lib/auth";

export default function CaseWorkflowsPage() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!caseId) return;
    apiFetchList<WorkflowExecution>(`/api/v1/cases/${caseId}/workflows`)
      .then(({ items }) => setExecutions(items))
      .catch((e: Error) => setError(e.message));
  }, [caseId]);

  useEffect(() => {
    load();
  }, [load]);

  async function triggerWorkflow() {
    if (!caseId) return;
    setLoading(true);
    setError(null);
    try {
      await apiFetch(`/api/v1/cases/${caseId}/workflows/trigger`, {
        method: "POST",
        body: JSON.stringify({ workflowSlug: "document-upload-notify-v1" }),
      });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Trigger failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <DashboardShell>
      <div className="flex items-start justify-between gap-4">
        <h1 className="text-2xl font-semibold">Workflows</h1>
        {caseId && <CaseNav caseId={caseId} active="workflows" />}
      </div>

      <button
        type="button"
        onClick={triggerWorkflow}
        disabled={loading}
        className="mt-6 rounded-md bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50"
      >
        {loading ? "Triggering…" : "Trigger document-upload-notify-v1"}
      </button>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <ul className="mt-8 space-y-2" data-testid="workflow-executions">
        {executions.map((ex) => (
          <li key={ex.id} className="rounded-md border border-slate-200 px-4 py-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs">{ex.id.slice(0, 8)}…</span>
              <span className="rounded-full bg-slate-100 px-2 py-1 text-xs capitalize">
                {ex.status}
              </span>
            </div>
            <p className="mt-1 text-slate-500">
              {ex.startedAt ? new Date(ex.startedAt).toLocaleString() : "Queued"}
            </p>
          </li>
        ))}
        {executions.length === 0 && (
          <li className="text-slate-500">No workflow executions yet.</li>
        )}
      </ul>
    </DashboardShell>
  );
}
