"use client";

import type { AISummary, DocumentSummary, JobStatus } from "@lexflow/shared";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { CaseNav } from "@/components/case-nav";
import { MarkdownContent } from "@/components/markdown-content";
import { PipelineSteps } from "@/components/pipeline-steps";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetch, apiFetchList, useAuth } from "@/lib/auth";
import { canApproveAi, canRequestAi } from "@/lib/permissions";
import { useCasePipeline } from "@/lib/use-case-pipeline";

type JobAccepted = { jobId: string; statusUrl: string };

const FLOW_STEPS = [
  "Upload documents on the Documents tab",
  "Wait for OCR to complete on all files",
  "Generate AI draft summary",
  "Attorney reviews and edits the draft",
  "Approve for team visibility",
  "Audit trail and notifications recorded",
];

const SUMMARY_STATUS_STYLES: Record<string, string> = {
  draft: "bg-amber-100 text-amber-900",
  generating: "bg-blue-100 text-blue-900",
  approved: "bg-green-100 text-green-900",
  rejected: "bg-red-100 text-red-900",
};

async function pollJob(statusUrl: string, maxAttempts = 120): Promise<JobStatus | null> {
  for (let i = 0; i < maxAttempts; i += 1) {
    const job = await apiFetch<JobStatus>(statusUrl);
    if (job.status === "completed" || job.status === "failed") return job;
    await new Promise((r) => setTimeout(r, 2000));
  }
  return null;
}

function formatDispatchMessage(dispatch?: AISummary["notificationDispatch"]): string {
  if (!dispatch) {
    return "Approved — notifications queued for the team.";
  }
  const parts: string[] = [];
  if ((dispatch.emailQueued ?? 0) > 0) parts.push(`${dispatch.emailQueued} email(s)`);
  if ((dispatch.slackQueued ?? 0) > 0) parts.push("Slack");
  if ((dispatch.teamsQueued ?? 0) > 0) parts.push("Teams");
  if ((dispatch.inAppCount ?? 0) > 0) parts.push(`${dispatch.inAppCount} in-app alert(s)`);
  if (parts.length === 0) {
    return "Approved — no notification channels were configured.";
  }
  return `Approved — queued: ${parts.join(", ")}.`;
}

export default function CaseAIPage() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;
  const { user } = useAuth();
  const canRequest = canRequestAi(user?.permissions);
  const canApprove = canApproveAi(user?.permissions);
  const { stages: pipelineStages, currentStage } = useCasePipeline(caseId);
  const [summaries, setSummaries] = useState<AISummary[]>([]);
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [pendingJob, setPendingJob] = useState(false);
  const [info, setInfo] = useState<string | null>(null);

  const ocrReady = useMemo(() => {
    if (documents.length === 0) return false;
    return documents.every(
      (d) => d.ocrStatus === "completed" || d.ocrStatus === "skipped"
    );
  }, [documents]);

  const hasGenerating = summaries.some((s) => s.status === "generating");

  const load = useCallback(() => {
    if (!caseId) return;
    Promise.all([
      apiFetchList<AISummary>(`/api/v1/cases/${caseId}/ai/summaries`),
      apiFetchList<DocumentSummary>(`/api/v1/cases/${caseId}/documents`),
    ])
      .then(([summariesRes, docsRes]) => {
        setSummaries(summariesRes.items);
        setDocuments(docsRes.items);
      })
      .catch((e: Error) => setError(e.message));
  }, [caseId]);

  useEffect(() => {
    load();
    const interval = hasGenerating || pendingJob || !ocrReady ? 3000 : 10000;
    const timer = setInterval(load, interval);
    return () => clearInterval(timer);
  }, [load, hasGenerating, pendingJob, ocrReady]);

  useEffect(() => {
    if (!pendingJob) return;
    const draft = summaries.find((s) => s.status === "draft" || s.status === "generating");
    if (draft?.status === "draft") {
      setPendingJob(false);
      setInfo(null);
      setError(null);
    }
  }, [summaries, pendingJob]);

  async function requestSummary() {
    if (!caseId) return;
    if (!ocrReady) {
      setError("All documents must finish OCR before generating a summary.");
      return;
    }
    setLoading(true);
    setError(null);
    setInfo(null);
    try {
      const accepted = await apiFetch<JobAccepted>(`/api/v1/cases/${caseId}/ai/summarize`, {
        method: "POST",
        body: JSON.stringify({ summaryType: "case_overview" }),
      });
      setPendingJob(true);
      load();
      const job = await pollJob(accepted.statusUrl);
      if (job?.status === "failed") {
        throw new Error(
          typeof job.result?.error === "string" ? job.result.error : "Summary generation failed"
        );
      }
      if (job?.status === "completed") {
        setPendingJob(false);
        load();
        return;
      }
      setInfo(
        "Summary is still generating in the background. This page will refresh automatically when the draft is ready."
      );
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Summary request failed");
      setPendingJob(false);
      load();
    } finally {
      setLoading(false);
    }
  }

  function startEdit(summary: AISummary) {
    setEditingId(summary.id);
    setEditContent(summary.content ?? "");
  }

  function cancelEdit() {
    setEditingId(null);
    setEditContent("");
  }

  async function saveEdit(summaryId: string) {
    setSaving(true);
    setError(null);
    try {
      await apiFetch(`/api/v1/ai/summaries/${summaryId}`, {
        method: "PATCH",
        body: JSON.stringify({ content: editContent }),
      });
      setEditingId(null);
      setEditContent("");
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save edits");
    } finally {
      setSaving(false);
    }
  }

  async function approve(summaryId: string) {
    setError(null);
    setInfo(null);
    try {
      const updated = await apiFetch<AISummary>(`/api/v1/ai/summaries/${summaryId}/approve`, {
        method: "POST",
      });
      setEditingId(null);
      setSummaries((prev) =>
        prev.map((s) => (s.id === summaryId ? { ...s, ...updated, status: "approved" } : s))
      );
      setInfo(formatDispatchMessage(updated.notificationDispatch));
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Approval failed");
    }
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
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">AI Summaries</h1>
          <p className="mt-1 text-sm text-slate-500">
            Document-grounded drafts with mandatory attorney approval.
          </p>
        </div>
        {caseId && <CaseNav caseId={caseId} active="ai" />}
      </div>

      <div className="mt-6 grid gap-8 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <p className="text-sm font-medium text-slate-900">Case intelligence flow</p>
            <ol className="mt-3 list-decimal space-y-1.5 pl-5 text-sm text-slate-600">
              {FLOW_STEPS.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
            {caseId && (
              <p className="mt-3 text-sm text-slate-600">
                <Link href={`/cases/${caseId}/documents`} className="font-medium text-blue-700 hover:underline">
                  Documents tab
                </Link>{" "}
                — upload sample files from{" "}
                <code className="rounded bg-slate-100 px-1 text-xs">docs/sample-cases-test/documents/</code>
              </p>
            )}
          </div>

          {!ocrReady && documents.length > 0 && (
            <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
              {documents.some((d) => d.ocrStatus === "failed")
                ? "Some documents failed OCR — retry on the Documents tab before generating a summary."
                : "Waiting for OCR to finish on all uploaded documents…"}
            </p>
          )}

          <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            AI drafts require attorney review and approval before the team is notified.
          </div>

          {canRequest ? (
            <button
              type="button"
              onClick={requestSummary}
              disabled={loading || pendingJob || hasGenerating || !ocrReady || documents.length === 0}
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
              data-testid="request-case-summary"
            >
              {loading || pendingJob || hasGenerating
                ? "Generating…"
                : "Generate case summary from documents"}
            </button>
          ) : (
            <p className="text-sm text-slate-500">
              AI summary requests require Attorney, Associate, Partner, or Managing Partner role.
            </p>
          )}

          {info && (
            <p className="rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-800">
              {info}
            </p>
          )}

          {error && (
            <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
              {error}
            </p>
          )}

          <ul className="space-y-4" data-testid="ai-summaries-list">
            {summaries.map((s) => (
              <li key={s.id} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-medium capitalize text-slate-900">
                    {s.summaryType.replace(/_/g, " ")}
                  </span>
                  <span
                    className={`rounded-full px-2.5 py-1 text-xs font-medium capitalize ${
                      SUMMARY_STATUS_STYLES[s.status] ?? "bg-slate-100 text-slate-700"
                    }`}
                    data-testid={`summary-status-${s.id}`}
                  >
                    {s.status}
                    {s.status === "generating" && "…"}
                  </span>
                </div>
                {s.model && s.status !== "generating" && (
                  <p className="mt-1 text-xs text-slate-500">
                    Generated by{" "}
                    <code className="rounded bg-slate-100 px-1 py-0.5">{s.model}</code>
                    {s.model.startsWith("stub") && " — Ollama unavailable; using fallback"}
                  </p>
                )}

                {s.status === "generating" && (
                  <p className="mt-3 text-sm text-blue-700">Generating summary from document text…</p>
                )}

                {editingId === s.id ? (
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    rows={16}
                    className="mt-4 w-full rounded-lg border border-slate-300 p-3 font-mono text-xs"
                    data-testid="summary-edit-textarea"
                  />
                ) : (
                  s.content && (
                    <div className="mt-4" data-testid="summary-content">
                      <MarkdownContent content={s.content} />
                    </div>
                  )
                )}

                {s.status === "draft" && canApprove && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {editingId === s.id ? (
                      <>
                        <button
                          type="button"
                          onClick={() => saveEdit(s.id)}
                          disabled={saving}
                          className="rounded-md bg-slate-900 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
                          data-testid="summary-save-edits"
                        >
                          {saving ? "Saving…" : "Save edits"}
                        </button>
                        <button
                          type="button"
                          onClick={cancelEdit}
                          className="rounded-md border border-slate-300 px-3 py-1.5 text-xs"
                        >
                          Cancel
                        </button>
                      </>
                    ) : (
                      <button
                        type="button"
                        onClick={() => startEdit(s)}
                        className="rounded-md border border-slate-300 px-3 py-1.5 text-xs"
                        data-testid="summary-edit-button"
                      >
                        Edit draft
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => approve(s.id)}
                      className="rounded-md bg-green-700 px-3 py-1.5 text-xs font-medium text-white"
                      data-testid="summary-approve-button"
                    >
                      Approve
                    </button>
                    <button
                      type="button"
                      onClick={() => reject(s.id)}
                      className="rounded-md bg-red-700 px-3 py-1.5 text-xs font-medium text-white"
                    >
                      Reject
                    </button>
                  </div>
                )}

                {s.status === "approved" && (
                  <p className="mt-3 text-xs font-medium text-green-700">
                    {formatDispatchMessage(s.notificationDispatch)}
                  </p>
                )}
              </li>
            ))}
            {summaries.length === 0 && (
              <li className="rounded-lg border border-dashed border-slate-200 px-4 py-8 text-center text-sm text-slate-500">
                No AI summaries yet. Upload documents and wait for OCR, then generate.
              </li>
            )}
          </ul>
        </div>
        <div>
          <PipelineSteps
            stages={pipelineStages}
            currentStage={currentStage}
            title="Processing timeline"
            emptyMessage="Upload documents on the Documents tab to start the pipeline."
          />
        </div>
      </div>
    </DashboardShell>
  );
}
