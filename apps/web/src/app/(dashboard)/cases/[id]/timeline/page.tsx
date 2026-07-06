"use client";

import type { TimelineEvent } from "@lexflow/shared";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetchList } from "@/lib/auth";

export default function CaseTimelinePage() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!caseId) return;
    apiFetchList<TimelineEvent>(`/api/v1/cases/${caseId}/timeline?pageSize=50`)
      .then(({ items }) => setEvents(items))
      .catch((e: Error) => setError(e.message));
  }, [caseId]);

  return (
    <DashboardShell>
      <Link href={`/cases/${caseId}/overview`} className="text-sm text-blue-700 hover:underline">
        ← Back to overview
      </Link>
      <h1 className="mt-4 text-2xl font-semibold">Timeline</h1>
      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
      <ul className="mt-6 space-y-3">
        {events.map((ev) => (
          <li key={ev.id} className="rounded-lg border border-slate-200 p-4">
            <p className="font-medium">{ev.title}</p>
            <p className="text-xs uppercase text-slate-500">{ev.eventType}</p>
            <p className="mt-1 text-sm text-slate-600">{new Date(ev.occurredAt).toLocaleString()}</p>
          </li>
        ))}
      </ul>
    </DashboardShell>
  );
}
