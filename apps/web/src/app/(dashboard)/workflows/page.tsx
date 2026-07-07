"use client";

import Link from "next/link";
import { Fragment, useCallback, useEffect, useState } from "react";

import { AccessDenied, DashboardShell, useRequirePermission } from "@/components/dashboard-shell";
import { apiFetch } from "@/lib/auth";
import { PERM } from "@/lib/permissions";

type CatalogItem = {
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
  retries: number;
  failure: string;
  owner: string;
  version: number;
  isActive: boolean;
  lastStatus?: string | null;
  lastExecutedAt?: string | null;
  executions24h: number;
  lastDurationMs?: number | null;
  lastRetryCount: number;
};

function formatRole(role: string): string {
  return role.replace(/([A-Z])/g, " $1").trim();
}

type ExecutionItem = {
  id: string;
  caseId?: string | null;
  status: string;
  inputPayload: Record<string, unknown>;
  outputPayload?: Record<string, unknown> | null;
  errorMessage?: string | null;
  retryCount: number;
  n8nExecutionId?: string | null;
  startedAt?: string | null;
  completedAt?: string | null;
  createdAt: string;
  durationMs?: number | null;
};

const GROUP_LABELS: Record<string, string> = {
  business: "Business",
  notifications: "Notifications",
  reports: "Reports",
  infra: "Infrastructure",
  test: "Test",
};

const GROUP_ORDER = ["business", "notifications", "reports", "infra", "test"];

const STATUS_BADGE: Record<string, string> = {
  completed: "bg-green-100 text-green-800",
  running: "bg-blue-100 text-blue-800",
  queued: "bg-slate-100 text-slate-700",
  failed: "bg-red-100 text-red-800",
  cancelled: "bg-amber-100 text-amber-800",
};

function catalogStatus(item: CatalogItem): { label: string; className: string } {
  if (item.triggerType === "schedule") {
    return { label: "Scheduled", className: "bg-indigo-100 text-indigo-800" };
  }
  if (item.triggerType === "manual") {
    return { label: "Manual", className: "bg-slate-100 text-slate-700" };
  }
  if (item.lastStatus === "running" || item.lastStatus === "queued") {
    return { label: "Running", className: STATUS_BADGE.running };
  }
  if (item.isActive) {
    return { label: "Active", className: "bg-green-100 text-green-800" };
  }
  return { label: "Inactive", className: "bg-slate-100 text-slate-600" };
}

function formatDuration(ms?: number | null): string {
  if (ms == null) return "—";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export default function WorkflowsCatalogPage() {
  const { allowed, loading: authLoading } = useRequirePermission(PERM.MANAGE_WORKFLOWS);
  const [catalog, setCatalog] = useState<CatalogItem[]>([]);
  const [selected, setSelected] = useState<CatalogItem | null>(null);
  const [executions, setExecutions] = useState<ExecutionItem[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadCatalog = useCallback(() => {
    if (!allowed) return;
    setLoading(true);
    apiFetch<CatalogItem[]>("/api/v1/workflows/catalog")
      .then(setCatalog)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [allowed]);

  useEffect(() => {
    loadCatalog();
  }, [loadCatalog]);

  if (authLoading) {
    return (
      <DashboardShell>
        <p className="text-slate-500">Loading…</p>
      </DashboardShell>
    );
  }

  if (!allowed) {
    return (
      <DashboardShell>
        <AccessDenied message="Workflow management requires Admin or Managing Partner role." />
      </DashboardShell>
    );
  }

  async function selectWorkflow(item: CatalogItem) {
    setSelected(item);
    setExpandedId(item.slug);
    try {
      const rows = await apiFetch<ExecutionItem[]>(
        `/api/v1/workflows/catalog/${item.slug}/executions?limit=10`
      );
      setExecutions(rows);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load executions");
    }
  }

  const grouped = GROUP_ORDER.map((gid) => ({
    id: gid,
    label: GROUP_LABELS[gid] ?? gid,
    items: catalog
      .filter((c) => (c.group || "business") === gid)
      .sort((a, b) => (a.serial || 999) - (b.serial || 999)),
  })).filter((g) => g.items.length > 0);

  return (
    <DashboardShell>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Workflows</h1>
          <p className="mt-1 text-sm text-slate-600">
            Enterprise orchestration catalog — n8n automations for case intake, documents, AI, and
            operations.
          </p>
        </div>
        <a
          href="http://localhost:5679"
          target="_blank"
          rel="noreferrer"
          className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
        >
          Open n8n editor ↗
        </a>
      </div>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <div className="mt-6 space-y-8">
        {loading && (
          <p className="rounded-lg border border-slate-200 bg-white px-4 py-8 text-center text-slate-500">
            Loading catalog…
          </p>
        )}
        {!loading &&
          grouped.map((section) => (
            <section key={section.id} className="overflow-hidden rounded-lg border border-slate-200 bg-white">
              <div className="border-b border-slate-100 bg-slate-50 px-4 py-3">
                <h2 className="text-sm font-semibold text-slate-800">{section.label}</h2>
                <p className="text-xs text-slate-500">{section.items.length} workflow(s)</p>
              </div>
              <table className="min-w-full text-sm">
                <thead className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-4 py-2 font-medium">Workflow</th>
                    <th className="px-4 py-2 font-medium">Status</th>
                    <th className="px-4 py-2 font-medium">Roles</th>
                    <th className="px-4 py-2 font-medium">Trigger</th>
                    <th className="px-4 py-2 font-medium">24h runs</th>
                    <th className="px-4 py-2 font-medium">Owner</th>
                  </tr>
                </thead>
                <tbody>
                  {section.items.map((item) => {
                    const badge = catalogStatus(item);
                    const isOpen = expandedId === item.slug;
                    return (
                      <Fragment key={item.slug}>
                        <tr
                          className="cursor-pointer border-b border-slate-100 hover:bg-slate-50"
                          onClick={() => selectWorkflow(item)}
                          data-testid={`workflow-row-${item.slug}`}
                        >
                          <td className="px-4 py-3">
                            <p className="font-medium text-slate-900">{item.name}</p>
                            <p className="text-xs text-slate-500">{item.slug}</p>
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`rounded-full px-2 py-1 text-xs font-medium ${badge.className}`}
                            >
                              {badge.label}
                            </span>
                            {item.canTrigger && (
                              <span className="ml-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-800">
                                You can trigger
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex max-w-[12rem] flex-wrap gap-1">
                              {item.allowedRoles.slice(0, 3).map((role) => (
                                <span
                                  key={role}
                                  className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600"
                                >
                                  {formatRole(role)}
                                </span>
                              ))}
                              {item.allowedRoles.length > 3 && (
                                <span className="text-xs text-slate-400">
                                  +{item.allowedRoles.length - 3}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-slate-600">{item.triggerType}</td>
                          <td className="px-4 py-3 text-slate-600">{item.executions24h}</td>
                          <td className="px-4 py-3 text-slate-600">{item.owner || "—"}</td>
                        </tr>
                        {isOpen && selected?.slug === item.slug && (
                          <tr className="bg-slate-50">
                            <td colSpan={6} className="px-4 py-4">
                              <div className="grid gap-6 lg:grid-cols-2">
                                <div className="space-y-3 text-sm">
                                  <h3 className="font-semibold text-slate-800">Documentation</h3>
                                  <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2">
                                    <dt className="text-slate-500">Group</dt>
                                    <dd>{GROUP_LABELS[item.group] ?? item.group}</dd>
                                    <dt className="text-slate-500">Scope</dt>
                                    <dd className="capitalize">{item.scope}</dd>
                                    <dt className="text-slate-500">Purpose</dt>
                                    <dd>{item.summary || item.purpose || item.description}</dd>
                                    <dt className="text-slate-500">Automated by</dt>
                                    <dd>{item.automatedBy || "—"}</dd>
                                    <dt className="text-slate-500">Allowed roles</dt>
                                    <dd className="flex flex-wrap gap-1">
                                      {item.allowedRoles.map((role) => (
                                        <span
                                          key={role}
                                          className="rounded bg-white px-2 py-0.5 text-xs ring-1 ring-slate-200"
                                        >
                                          {formatRole(role)}
                                        </span>
                                      ))}
                                    </dd>
                                    <dt className="text-slate-500">Steps</dt>
                                    <dd>
                                      {item.automationSteps.length > 0 ? (
                                        <ol className="list-inside list-decimal space-y-0.5">
                                          {item.automationSteps.map((step) => (
                                            <li key={step}>{step}</li>
                                          ))}
                                        </ol>
                                      ) : (
                                        "—"
                                      )}
                                    </dd>
                                    <dt className="text-slate-500">Trigger</dt>
                                    <dd className="font-mono text-xs">{item.trigger}</dd>
                                    <dt className="text-slate-500">Retries</dt>
                                    <dd>{item.retries}</dd>
                                    <dt className="text-slate-500">Failure</dt>
                                    <dd>{item.failure || "—"}</dd>
                                    <dt className="text-slate-500">Version</dt>
                                    <dd>v{item.version}</dd>
                                    <dt className="text-slate-500">Tags</dt>
                                    <dd className="flex flex-wrap gap-1">
                                      {item.tags.map((t) => (
                                        <span
                                          key={t}
                                          className="rounded bg-white px-2 py-0.5 text-xs text-slate-600 ring-1 ring-slate-200"
                                        >
                                          {t}
                                        </span>
                                      ))}
                                    </dd>
                                  </dl>
                                </div>
                                <div>
                                  <h3 className="font-semibold text-slate-800">Execution history</h3>
                                  {executions.length === 0 ? (
                                    <p className="mt-2 text-sm text-slate-500">No executions yet.</p>
                                  ) : (
                                    <ul className="mt-2 space-y-2">
                                      {executions.map((ex) => (
                                        <li
                                          key={ex.id}
                                          className="rounded-md border border-slate-200 bg-white px-3 py-2 text-xs"
                                        >
                                          <div className="flex items-center justify-between">
                                            <span className="font-mono">{ex.id.slice(0, 8)}…</span>
                                            <span
                                              className={`rounded-full px-2 py-0.5 capitalize ${STATUS_BADGE[ex.status] ?? "bg-slate-100"}`}
                                            >
                                              {ex.status}
                                            </span>
                                          </div>
                                          <p className="mt-1 text-slate-500">
                                            {new Date(ex.createdAt).toLocaleString()} ·{" "}
                                            {formatDuration(ex.durationMs)} · retries {ex.retryCount}
                                          </p>
                                          {ex.caseId && (
                                            <Link
                                              href={`/cases/${ex.caseId}/workflows`}
                                              className="mt-1 inline-block text-blue-700 hover:underline"
                                              onClick={(e) => e.stopPropagation()}
                                            >
                                              View case
                                            </Link>
                                          )}
                                          {ex.errorMessage && (
                                            <p className="mt-1 text-red-600">{ex.errorMessage}</p>
                                          )}
                                        </li>
                                      ))}
                                    </ul>
                                  )}
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            </section>
          ))}
      </div>

      <p className="mt-4 text-xs text-slate-500">
        Docs in <code className="rounded bg-slate-100 px-1">docs/06-workflows/workflow-groups.md</code>.
        Run <code className="rounded bg-slate-100 px-1">make n8n-import</code> after changes. n8n:{" "}
        <a href="http://localhost:5679" className="text-blue-700 hover:underline" target="_blank" rel="noreferrer">
          localhost:5679
        </a>
      </p>
    </DashboardShell>
  );
}
