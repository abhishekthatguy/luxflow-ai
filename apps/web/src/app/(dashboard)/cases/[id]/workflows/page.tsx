"use client";

import type { WorkflowExecution } from "@lexflow/shared";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { CaseNav } from "@/components/case-nav";
import { PipelineSteps } from "@/components/pipeline-steps";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetch, apiFetchList, apiFetchVoid, newIdempotencyKey, useAuth } from "@/lib/auth";
import { useCasePipeline } from "@/lib/use-case-pipeline";

type WorkflowCatalogItem = {
  slug: string;
  name: string;
  description?: string | null;
  triggerType: string;
  category: string;
  group: string;
  tags: string[];
  purpose: string;
  summary: string;
  trigger: string;
  serial: number;
  scope: string;
  allowedRoles: string[];
  automationSteps: string[];
  automatedBy: string;
  canTrigger: boolean;
  isTestTrigger: boolean;
  isActive: boolean;
};

type TriggerResult = {
  deduplicated: boolean;
  status: string;
};

const EXEC_STATUS_STYLES: Record<string, string> = {
  completed: "bg-green-100 text-green-800",
  running: "bg-blue-100 text-blue-800",
  queued: "bg-amber-100 text-amber-800",
  failed: "bg-red-100 text-red-800",
};

const ADMIN_ROLES = new Set(["ManagingPartner", "SystemAdministrator"]);

const SCOPE_LABELS: Record<string, string> = {
  case: "Case workflow",
  firm: "Firm automation",
};

function formatRole(role: string): string {
  return role.replace(/([A-Z])/g, " $1").trim();
}

function wfTag(tags: string[]): string | null {
  const tag = tags.find((t) => /^wf-/i.test(t));
  return tag ? tag.toUpperCase() : null;
}

export default function CaseWorkflowsPage() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;
  const { user } = useAuth();
  const { stages: pipelineStages, currentStage, reload: reloadPipeline } = useCasePipeline(caseId);
  const [catalog, setCatalog] = useState<WorkflowCatalogItem[]>([]);
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [loadingSlug, setLoadingSlug] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const triggerKeys = useRef<Map<string, string>>(new Map());

  const canDelete = useMemo(
    () => user?.roles.some((r) => ADMIN_ROLES.has(r)) ?? false,
    [user?.roles],
  );

  const loadExecutions = useCallback(() => {
    if (!caseId) return;
    apiFetchList<WorkflowExecution>(`/api/v1/cases/${caseId}/workflows`)
      .then(({ items }) => setExecutions(items))
      .catch((e: Error) => setError(e.message));
  }, [caseId]);

  const loadCatalog = useCallback(() => {
    if (!caseId) return;
    apiFetch<WorkflowCatalogItem[]>(`/api/v1/cases/${caseId}/workflows/catalog`)
      .then(setCatalog)
      .catch((e: Error) => setError(e.message));
  }, [caseId]);

  useEffect(() => {
    loadCatalog();
    loadExecutions();
    const timer = setInterval(loadExecutions, 5000);
    return () => clearInterval(timer);
  }, [loadCatalog, loadExecutions]);

  async function triggerWorkflow(wf: WorkflowCatalogItem, force = false) {
    if (!caseId) return;
    setLoadingSlug(wf.slug);
    setError(null);
    setMessage(null);
    try {
      const key = triggerKeys.current.get(wf.slug) ?? newIdempotencyKey();
      if (!triggerKeys.current.has(wf.slug)) {
        triggerKeys.current.set(wf.slug, key);
      }
      const path =
        wf.scope === "firm"
          ? "/api/v1/workflows/trigger"
          : `/api/v1/cases/${caseId}/workflows/trigger`;
      const result = await apiFetch<TriggerResult>(path, {
        method: "POST",
        body: JSON.stringify({ workflowSlug: wf.slug, force }),
        idempotencyKey: force ? newIdempotencyKey() : key,
      });
      setMessage(
        result.deduplicated
          ? `"${wf.name}" already ran — showing existing execution (${result.status}).`
          : `"${wf.name}" triggered.`,
      );
      for (let i = 0; i < 6; i += 1) {
        await new Promise((r) => setTimeout(r, 1500));
        loadExecutions();
      }
      reloadPipeline();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Trigger failed");
    } finally {
      setLoadingSlug(null);
    }
  }

  async function deleteExecution(executionId: string) {
    if (!caseId || !canDelete) return;
    if (!window.confirm("Delete this workflow execution? Admin action — cannot be undone.")) return;
    try {
      await apiFetchVoid(`/api/v1/cases/${caseId}/workflows/executions/${executionId}`, {
        method: "DELETE",
      });
      setMessage("Execution deleted.");
      loadExecutions();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  }

  const caseWorkflows = catalog.filter((w) => w.scope === "case");
  const firmAutomations = catalog.filter((w) => w.scope === "firm");

  return (
    <DashboardShell>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Workflows</h1>
          <p className="mt-1 text-sm text-slate-500">
            All n8n automations — duplicate triggers are blocked unless an admin forces re-run.
          </p>
        </div>
        {caseId && <CaseNav caseId={caseId} active="workflows" />}
      </div>

      {message && (
        <p className="mt-4 rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
          {message}
        </p>
      )}
      {error && (
        <p
          className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          {error}
        </p>
      )}

      <div className="mt-6 grid gap-8 xl:grid-cols-[1.4fr_1fr]">
        <div className="space-y-8">
          <PipelineSteps
            stages={pipelineStages}
            currentStage={currentStage}
            title="Document processing pipeline"
          />

          <section>
            <h2 className="text-lg font-medium text-slate-900">Case workflows</h2>
            <ul className="mt-4 space-y-4" data-testid="case-workflow-catalog">
              {caseWorkflows.map((wf) => (
                <WorkflowCard
                  key={wf.slug}
                  wf={wf}
                  loading={loadingSlug === wf.slug}
                  canForce={canDelete}
                  onTrigger={() => triggerWorkflow(wf)}
                  onForce={() => triggerWorkflow(wf, true)}
                />
              ))}
            </ul>
          </section>

          {firmAutomations.length > 0 && (
            <section>
              <h2 className="text-lg font-medium text-slate-900">Firm-wide automations</h2>
              <p className="mt-1 text-sm text-slate-500">
                Scheduled jobs — partners/admins can run now for testing.
              </p>
              <ul className="mt-4 space-y-4">
                {firmAutomations.map((wf) => (
                  <WorkflowCard
                    key={wf.slug}
                    wf={wf}
                    loading={loadingSlug === wf.slug}
                    canForce={canDelete}
                    onTrigger={() => triggerWorkflow(wf)}
                    onForce={() => triggerWorkflow(wf, true)}
                  />
                ))}
              </ul>
            </section>
          )}
        </div>

        <div>
          <h2 className="text-lg font-medium text-slate-900">Execution history</h2>
          <ul className="mt-3 space-y-3" data-testid="workflow-executions">
            {executions.map((ex) => (
              <li key={ex.id} className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="font-medium text-slate-900">
                      {ex.workflowName ?? ex.workflowSlug ?? "Workflow"}
                    </p>
                    {ex.workflowSlug && (
                      <p className="font-mono text-xs text-slate-500">{ex.workflowSlug}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-medium capitalize ${
                        EXEC_STATUS_STYLES[ex.status] ?? "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {ex.status}
                    </span>
                    {canDelete && (
                      <button
                        type="button"
                        onClick={() => deleteExecution(ex.id)}
                        className="text-xs text-red-600 hover:underline"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  {ex.startedAt ? new Date(ex.startedAt).toLocaleString() : "Queued"}
                  {ex.completedAt && ` → ${new Date(ex.completedAt).toLocaleString()}`}
                </p>
              </li>
            ))}
            {executions.length === 0 && (
              <li className="rounded-lg border border-dashed border-slate-200 px-4 py-8 text-center text-sm text-slate-500">
                No workflow executions yet.
              </li>
            )}
          </ul>
        </div>
      </div>
    </DashboardShell>
  );
}

function WorkflowCard({
  wf,
  loading,
  canForce,
  onTrigger,
  onForce,
}: {
  wf: WorkflowCatalogItem;
  loading: boolean;
  canForce: boolean;
  onTrigger: () => void;
  onForce: () => void;
}) {
  const tag = wfTag(wf.tags);

  return (
    <li className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm" data-testid={`wf-card-${wf.slug}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            {tag && (
              <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600">
                {tag}
              </span>
            )}
            <span className="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-800">
              {SCOPE_LABELS[wf.scope] ?? wf.scope}
            </span>
            {wf.isTestTrigger && (
              <span className="rounded bg-indigo-50 px-2 py-0.5 text-xs text-indigo-800">
                Scheduled — test run available
              </span>
            )}
          </div>
          <h3 className="mt-2 font-medium text-slate-900">{wf.name}</h3>
          <p className="font-mono text-xs text-slate-500">{wf.slug}</p>
          {(wf.summary || wf.purpose) && (
            <p className="mt-2 text-sm text-slate-600">{wf.summary || wf.purpose}</p>
          )}
        </div>
        <div className="flex shrink-0 flex-col gap-2">
          {wf.canTrigger && (
            <button
              type="button"
              onClick={onTrigger}
              disabled={loading}
              className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
            >
              {loading ? "Triggering…" : wf.isTestTrigger ? "Run now (test)" : "Trigger"}
            </button>
          )}
          {canForce && wf.canTrigger && (
            <button
              type="button"
              onClick={onForce}
              disabled={loading}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50 disabled:opacity-50"
            >
              Force re-run
            </button>
          )}
        </div>
      </div>

      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Who can trigger</dt>
          <dd className="mt-1 flex flex-wrap gap-1">
            {wf.allowedRoles.map((role) => (
              <span key={role} className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700">
                {formatRole(role)}
              </span>
            ))}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">How it runs</dt>
          <dd className="mt-1 text-slate-600">{wf.automatedBy || wf.trigger}</dd>
        </div>
      </dl>

      {wf.automationSteps.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Automated steps</p>
          <ol className="mt-1 list-inside list-decimal space-y-0.5 text-sm text-slate-600">
            {wf.automationSteps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </div>
      )}
    </li>
  );
}
