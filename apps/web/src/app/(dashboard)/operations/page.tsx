"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { apiFetch, useAuth } from "@/lib/auth";
import { canViewAudit } from "@/lib/permissions";

type ComponentHealth = {
  name: string;
  status: string;
  detail?: string | null;
};

type QueueMetric = {
  name: string;
  depth: number;
  status: string;
  detail: string;
};

type JobItem = {
  id: string;
  jobType: string;
  status: string;
  progress: number;
  caseId?: string | null;
  createdAt: string;
};

type WorkflowRun = {
  id: string;
  caseId?: string | null;
  workflowSlug?: string | null;
  workflowName?: string | null;
  status: string;
  errorMessage?: string | null;
  createdAt: string;
};

type AuditEvent = {
  id: string;
  action: string;
  resourceType: string;
  resourceId?: string | null;
  actorId?: string | null;
  createdAt: string;
};

type Dashboard = {
  overview: {
    activeUsers: number;
    totalCases: number;
    processingJobs: number;
    failedJobs: number;
    workflowRuns24h: number;
    aiSummariesPending: number;
    componentsHealthy: number;
    componentsTotal: number;
  };
  health: ComponentHealth[];
  queues: QueueMetric[];
  activeAiJobs: JobItem[];
  failedWorkflows: WorkflowRun[];
  recentAuditEvents: AuditEvent[];
  processingMetrics: {
    documentsReady: number;
    aiSummariesTotal: number;
    aiSummariesApproved: number;
    workflowSuccessRate: number;
    avgJobDurationSeconds?: number | null;
  };
};

const HEALTH_STYLES: Record<string, string> = {
  healthy: "bg-green-100 text-green-800",
  degraded: "bg-amber-100 text-amber-800",
  unreachable: "bg-red-100 text-red-800",
  unknown: "bg-slate-100 text-slate-600",
};

const QUEUE_STYLES: Record<string, string> = {
  ok: "text-green-700",
  warn: "text-amber-700",
  critical: "text-red-700",
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white">
      <h2 className="border-b border-slate-100 px-4 py-3 text-sm font-semibold text-slate-800">{title}</h2>
      <div className="p-4">{children}</div>
    </section>
  );
}

export default function OperationsDashboardPage() {
  const { user } = useAuth();
  const showAudit = canViewAudit(user?.permissions);
  const [data, setData] = useState<Dashboard | null>(null);
  const [refreshedAt, setRefreshedAt] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    apiFetch<Dashboard>("/api/v1/operations/dashboard")
      .then((d) => {
        setData(d);
        setRefreshedAt(new Date());
        setError(null);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, [load]);

  const overview = data?.overview;
  const metrics = data?.processingMetrics;

  return (
    <div className="space-y-6" data-testid="operations-dashboard">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-slate-500">
          Platform health, queues, and processing activity
          {refreshedAt && (
            <span className="ml-2">· refreshed {refreshedAt.toLocaleTimeString()}</span>
          )}
        </p>
        <button
          type="button"
          onClick={load}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
        >
          Refresh
        </button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {data?.health.map((c) => (
          <div key={c.name} className="rounded-lg border border-slate-200 bg-white p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium">{c.name}</span>
              <span
                className={`rounded-full px-2 py-0.5 text-xs capitalize ${HEALTH_STYLES[c.status] ?? HEALTH_STYLES.unknown}`}
              >
                {c.status}
              </span>
            </div>
            {c.detail && <p className="mt-1 text-xs text-slate-500">{c.detail}</p>}
          </div>
        )) ?? Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-20 animate-pulse rounded-lg bg-slate-100" />
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Active users", value: overview?.activeUsers },
          { label: "Total cases", value: overview?.totalCases },
          { label: "Queue depth", value: overview?.processingJobs, warn: (overview?.processingJobs ?? 0) > 20 },
          { label: "Failed jobs", value: overview?.failedJobs, warn: (overview?.failedJobs ?? 0) > 0 },
          { label: "AI pending review", value: overview?.aiSummariesPending },
          { label: "Workflow runs", value: overview?.workflowRuns24h },
          {
            label: "System health",
            value: overview ? `${overview.componentsHealthy}/${overview.componentsTotal}` : undefined,
          },
          {
            label: "Workflow success",
            value: metrics ? `${Math.round(metrics.workflowSuccessRate * 100)}%` : undefined,
          },
        ].map((card) => (
          <div
            key={card.label}
            className={`rounded-lg border p-4 ${card.warn ? "border-amber-300 bg-amber-50" : "border-slate-200 bg-white"}`}
          >
            <p className="text-xs uppercase tracking-wide text-slate-500">{card.label}</p>
            <p className="mt-2 text-2xl font-semibold">{card.value ?? "—"}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Section title="Queue depth">
          <ul className="space-y-3">
            {(data?.queues ?? []).map((q) => (
              <li key={q.name} className="flex items-center justify-between text-sm">
                <div>
                  <p className="font-medium">{q.name}</p>
                  <p className="text-xs text-slate-500">{q.detail}</p>
                </div>
                <span className={`text-lg font-semibold ${QUEUE_STYLES[q.status] ?? ""}`}>{q.depth}</span>
              </li>
            ))}
            {!data?.queues.length && <p className="text-sm text-slate-500">No queue data.</p>}
          </ul>
        </Section>

        <Section title="Processing metrics">
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-slate-500">Documents ready</dt>
              <dd className="text-2xl font-semibold">{metrics?.documentsReady ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">AI summaries</dt>
              <dd className="text-2xl font-semibold">{metrics?.aiSummariesTotal ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Approved summaries</dt>
              <dd className="text-2xl font-semibold">{metrics?.aiSummariesApproved ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Avg job duration</dt>
              <dd className="text-2xl font-semibold">
                {metrics?.avgJobDurationSeconds != null
                  ? `${metrics.avgJobDurationSeconds}s`
                  : "—"}
              </dd>
            </div>
          </dl>
        </Section>
      </div>

      <Section title="Active AI jobs">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="pb-2 pr-4">Type</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">Progress</th>
                <th className="pb-2 pr-4">Case</th>
                <th className="pb-2">Created</th>
              </tr>
            </thead>
            <tbody>
              {(data?.activeAiJobs ?? []).map((j) => (
                <tr key={j.id} className="border-t border-slate-100">
                  <td className="py-2 pr-4 font-mono text-xs">{j.jobType}</td>
                  <td className="py-2 pr-4 capitalize">{j.status}</td>
                  <td className="py-2 pr-4">{j.progress}%</td>
                  <td className="py-2 pr-4">
                    {j.caseId ? (
                      <Link href={`/cases/${j.caseId}/ai`} className="text-blue-700 hover:underline">
                        View case
                      </Link>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="py-2">{new Date(j.createdAt).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data?.activeAiJobs.length && (
            <p className="text-sm text-slate-500">No active AI jobs — workers idle.</p>
          )}
        </div>
      </Section>

      <Section title="Failed workflows (last 24h)">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="pb-2 pr-4">Workflow</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">Case</th>
                <th className="pb-2">Created</th>
              </tr>
            </thead>
            <tbody>
              {(data?.failedWorkflows ?? []).map((w) => (
                <tr key={w.id} className="border-t border-slate-100">
                  <td className="py-2 pr-4">
                    <p className="font-medium text-slate-900">
                      {w.workflowName ?? w.workflowSlug ?? "Workflow"}
                    </p>
                    {w.errorMessage && (
                      <p className="mt-0.5 text-xs text-red-600">{w.errorMessage}</p>
                    )}
                  </td>
                  <td className="py-2 pr-4 capitalize text-red-700">{w.status}</td>
                  <td className="py-2 pr-4">
                    {w.caseId ? (
                      <Link href={`/cases/${w.caseId}/workflows`} className="text-blue-700 hover:underline">
                        View case
                      </Link>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="py-2">{new Date(w.createdAt).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data?.failedWorkflows.length && (
            <p className="text-sm text-green-700">No failed workflow runs in the last 24 hours.</p>
          )}
        </div>
      </Section>

      {showAudit && (
      <Section title="Recent audit events">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="pb-2 pr-4">Time</th>
                <th className="pb-2 pr-4">Action</th>
                <th className="pb-2 pr-4">Resource</th>
                <th className="pb-2">Actor</th>
              </tr>
            </thead>
            <tbody>
              {(data?.recentAuditEvents ?? []).map((e) => (
                <tr key={e.id} className="border-t border-slate-100">
                  <td className="py-2 pr-4 text-slate-600">{new Date(e.createdAt).toLocaleString()}</td>
                  <td className="py-2 pr-4">{e.action}</td>
                  <td className="py-2 pr-4">
                    {e.resourceType}
                    {e.resourceId ? ` · ${e.resourceId.slice(0, 8)}…` : ""}
                  </td>
                  <td className="py-2 text-slate-600">{e.actorId?.slice(0, 8) ?? "system"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data?.recentAuditEvents.length && (
            <p className="text-sm text-slate-500">No audit events yet. Run seed-demo-data.</p>
          )}
        </div>
      </Section>
      )}
    </div>
  );
}
