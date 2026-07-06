"use client";

import type { CaseSummary, TimelineEvent } from "@lexflow/shared";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetch, apiFetchList } from "@/lib/auth";

export default function CaseOverviewPage() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;
  const [caseData, setCaseData] = useState<CaseSummary | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!caseId) return;
    Promise.all([
      apiFetch<CaseSummary>(`/api/v1/cases/${caseId}`),
      apiFetchList<TimelineEvent>(`/api/v1/cases/${caseId}/timeline?pageSize=5`),
    ])
      .then(([c, t]) => {
        setCaseData(c);
        setTimeline(t.items);
      })
      .catch((e: Error) => setError(e.message));
  }, [caseId]);

  if (error) {
    return (
      <DashboardShell>
        <p className="text-red-600">{error === "Not Found" ? "Case not found (matter wall)" : error}</p>
      </DashboardShell>
    );
  }

  if (!caseData) {
    return (
      <DashboardShell>
        <p className="text-slate-500">Loading case…</p>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-slate-500">{caseData.caseNumber}</p>
          <h1 className="text-2xl font-semibold">{caseData.title}</h1>
          <p className="mt-1 capitalize text-slate-600">
            {caseData.status.replace("_", " ")} · {caseData.priority}
          </p>
        </div>
        <nav className="flex gap-2 text-sm">
          <Link href={`/cases/${caseId}/overview`} className="font-medium text-slate-900">
            Overview
          </Link>
          <Link href={`/cases/${caseId}/timeline`} className="text-blue-700 hover:underline">
            Timeline
          </Link>
          <Link href={`/cases/${caseId}/tasks`} className="text-blue-700 hover:underline">
            Tasks
          </Link>
        </nav>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200 p-4">
          <p className="text-xs uppercase text-slate-500">Status</p>
          <p className="mt-1 text-lg capitalize">{caseData.status.replace("_", " ")}</p>
        </div>
        <div className="rounded-lg border border-slate-200 p-4">
          <p className="text-xs uppercase text-slate-500">Practice area</p>
          <p className="mt-1 text-lg">{caseData.practiceArea ?? "—"}</p>
        </div>
        <div className="rounded-lg border border-slate-200 p-4">
          <p className="text-xs uppercase text-slate-500">Version</p>
          <p className="mt-1 text-lg">{caseData.version}</p>
        </div>
      </div>

      <section className="mt-8">
        <h2 className="text-lg font-medium">Recent activity</h2>
        <ul className="mt-3 space-y-2">
          {timeline.map((ev) => (
            <li key={ev.id} className="rounded-md border border-slate-100 px-3 py-2 text-sm">
              <span className="font-medium">{ev.title}</span>
              <span className="ml-2 text-slate-500">{new Date(ev.occurredAt).toLocaleString()}</span>
            </li>
          ))}
          {timeline.length === 0 && <li className="text-slate-500">No timeline events yet.</li>}
        </ul>
      </section>
    </DashboardShell>
  );
}
