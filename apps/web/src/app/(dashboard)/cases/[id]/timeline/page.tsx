"use client";

import type { TimelineEvent } from "@lexflow/shared";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { CaseNav } from "@/components/case-nav";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetchList } from "@/lib/auth";

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function friendlyTitle(ev: TimelineEvent): string {
  const map: Record<string, string> = {
    CaseCreated: "Case created",
    "document.uploaded": "Document uploaded",
    "document.virus_scan.passed": "Virus scan passed",
    "document.ocr.completed": "OCR complete",
    "document.chunking.completed": "Chunking complete",
    "ai.summary.ready": "AI summary ready",
    AiSummaryApproved: "Attorney approved",
    "notification.sent": "Client notification sent",
    "workflow.started": "Workflow started",
    "workflow.completed": "Workflow completed",
  };
  return map[ev.eventType] ?? ev.title;
}

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
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link href={`/cases/${caseId}/overview`} className="text-sm text-blue-700 hover:underline">
            ← Back to overview
          </Link>
          <h1 className="mt-2 text-2xl font-semibold">Case timeline</h1>
          <p className="text-sm text-slate-600">Processing and approval events (newest first)</p>
        </div>
        {caseId && <CaseNav caseId={caseId} active="timeline" />}
      </div>
      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
      <ol className="relative mt-8 border-l border-slate-200 pl-6" data-testid="case-timeline">
        {[...events].reverse().map((ev) => (
          <li key={ev.id} className="mb-6 ml-2">
            <span className="absolute -left-[0.45rem] mt-1.5 h-3 w-3 rounded-full bg-slate-900" />
            <p className="font-mono text-sm font-semibold text-slate-900">{formatTime(ev.occurredAt)}</p>
            <p className="font-medium">{friendlyTitle(ev)}</p>
            {ev.title !== friendlyTitle(ev) && (
              <p className="text-sm text-slate-600">{ev.title}</p>
            )}
            <p className="text-xs uppercase text-slate-400">{ev.eventType}</p>
          </li>
        ))}
        {events.length === 0 && !error && (
          <li className="text-slate-500">No timeline events yet. Upload documents to begin.</li>
        )}
      </ol>
    </DashboardShell>
  );
}
