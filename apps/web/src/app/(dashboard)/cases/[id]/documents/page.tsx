"use client";

import type { DocumentSummary } from "@lexflow/shared";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { CaseNav } from "@/components/case-nav";
import { DocumentPreviewModal } from "@/components/document-preview-panel";
import { DocumentStatusBadge } from "@/components/document-status-badge";
import { PipelineSteps } from "@/components/pipeline-steps";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetch, apiFetchList } from "@/lib/auth";
import { useCasePipeline } from "@/lib/use-case-pipeline";

type InitiateResponse = {
  id: string;
  uploadUrl: string;
  s3Key: string;
};

const SAMPLE_FILES = [
  "police_report.txt",
  "medical_report.txt",
  "insurance_letter.txt",
] as const;

export default function CaseDocumentsPage() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;
  const { stages: pipelineStages, currentStage, reload: reloadPipeline } = useCasePipeline(caseId);
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [uploading, setUploading] = useState(false);
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [previewDoc, setPreviewDoc] = useState<DocumentSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [ocrReadyHint, setOcrReadyHint] = useState(false);
  const prevOcrReady = useRef(false);

  const ocrSummary = useMemo(() => {
    const failed = documents.filter((d) => d.ocrStatus === "failed" || d.status === "failed");
    const pending = documents.filter(
      (d) => d.ocrStatus === "pending" || d.ocrStatus === "processing"
    );
    const ready = documents.filter(
      (d) => d.ocrStatus === "completed" || d.ocrStatus === "skipped"
    );
    return { failed, pending, ready };
  }, [documents]);

  const allOcrReady =
    documents.length > 0 &&
    documents.every((d) => d.ocrStatus === "completed" || d.ocrStatus === "skipped");

  const load = useCallback(() => {
    if (!caseId) return;
    apiFetchList<DocumentSummary>(`/api/v1/cases/${caseId}/documents`)
      .then(({ items }) => setDocuments(items))
      .catch((e: Error) => setError(e.message));
  }, [caseId]);

  useEffect(() => {
    load();
    const timer = setInterval(load, 5000);
    return () => clearInterval(timer);
  }, [load]);

  useEffect(() => {
    if (allOcrReady && !prevOcrReady.current && documents.length > 0) {
      setOcrReadyHint(true);
    }
    prevOcrReady.current = allOcrReady;
  }, [allOcrReady, documents.length]);

  async function onUpload(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const fileInput = form.elements.namedItem("file") as HTMLInputElement;
    const file = fileInput.files?.[0];
    if (!file || !caseId) return;

    setUploading(true);
    setError(null);
    setMessage(null);
    setOcrReadyHint(false);

    try {
      const buffer = await file.arrayBuffer();
      const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
      const checksum = Array.from(new Uint8Array(hashBuffer))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");

      const initiated = await apiFetch<InitiateResponse>(`/api/v1/cases/${caseId}/documents`, {
        method: "POST",
        body: JSON.stringify({
          title: file.name.replace(/\.[^.]+$/, "").replace(/_/g, " "),
          documentType: "evidence",
          filename: file.name,
          mimeType: file.type || "application/octet-stream",
          fileSizeBytes: file.size,
          checksumSha256: checksum,
        }),
      });

      const putRes = await fetch(initiated.uploadUrl, {
        method: "PUT",
        body: file,
        headers: { "Content-Type": file.type || "application/octet-stream" },
      });
      if (!putRes.ok) throw new Error(`Storage upload failed (${putRes.status})`);

      await apiFetch(`/api/v1/documents/${initiated.id}/confirm`, {
        method: "POST",
        body: JSON.stringify({ checksumSha256: checksum }),
      });

      setMessage(`${file.name} uploaded successfully. OCR is running in the background.`);
      fileInput.value = "";
      load();
      reloadPipeline();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function retryOcr(documentId: string) {
    setRetryingId(documentId);
    setError(null);
    try {
      await apiFetch(`/api/v1/documents/${documentId}/retry-ocr`, { method: "POST" });
      setMessage("OCR retry queued.");
      load();
      reloadPipeline();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Retry failed");
    } finally {
      setRetryingId(null);
    }
  }

  function togglePreview(doc: DocumentSummary) {
    setPreviewDoc((current) => (current?.id === doc.id ? null : doc));
  }

  return (
    <DashboardShell>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Documents</h1>
          <p className="mt-1 text-sm text-slate-500">
            Upload case files for virus scan, OCR, and AI summarization.
          </p>
        </div>
        {caseId && <CaseNav caseId={caseId} active="documents" />}
      </div>

      {documents.length > 0 && (
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Ready</p>
            <p className="mt-1 text-2xl font-semibold text-green-700">{ocrSummary.ready.length}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Processing</p>
            <p className="mt-1 text-2xl font-semibold text-blue-700">{ocrSummary.pending.length}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Failed</p>
            <p className="mt-1 text-2xl font-semibold text-red-700">{ocrSummary.failed.length}</p>
          </div>
        </div>
      )}

      <form
        onSubmit={onUpload}
        className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50/50 p-6"
      >
        <p className="text-sm text-slate-600">
          <span className="font-medium text-slate-800">Demo files:</span>{" "}
          {SAMPLE_FILES.map((f) => (
            <code key={f} className="mx-0.5 rounded bg-white px-1.5 py-0.5 text-xs ring-1 ring-slate-200">
              {f}
            </code>
          ))}{" "}
          from <code className="rounded bg-white px-1.5 py-0.5 text-xs ring-1 ring-slate-200">docs/sample-cases-test/documents/</code>
        </p>
        <label className="mt-4 block text-sm font-medium text-slate-700">
          Choose file
          <input
            name="file"
            type="file"
            accept=".pdf,.txt,.zip,application/pdf,text/plain,application/zip"
            className="mt-2 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-1.5 file:text-sm"
            required
          />
        </label>
        <button
          type="submit"
          disabled={uploading}
          className="mt-4 rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          {uploading ? "Uploading…" : "Upload document"}
        </button>
      </form>

      {message && (
        <div className="mt-4 rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
          <p>{message}</p>
          {caseId && (
            <p className="mt-2 text-green-900">
              When OCR finishes, you can optionally{" "}
              <Link href={`/cases/${caseId}/ai`} className="font-medium underline hover:text-green-950">
                open the AI tab
              </Link>{" "}
              to generate a case summary.
            </p>
          )}
        </div>
      )}

      {ocrReadyHint && caseId && (
        <div className="mt-4 rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-900">
          All documents are OCR-ready.{" "}
          <Link href={`/cases/${caseId}/ai`} className="font-medium underline hover:text-blue-950">
            Go to AI tab →
          </Link>{" "}
          to generate and approve a summary (optional).
        </div>
      )}

      {error && (
        <p className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}

      <div className="mt-8 grid gap-8 lg:grid-cols-3">
        <ul className="space-y-3 lg:col-span-2" data-testid="documents-list">
          {documents.map((doc) => (
            <li
              key={doc.id}
              className={`rounded-lg border bg-white px-4 py-4 shadow-sm ${
                previewDoc?.id === doc.id
                  ? "border-blue-300 ring-1 ring-blue-200"
                  : "border-slate-200"
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-slate-900">{doc.title}</p>
                  <div className="mt-2">
                    <DocumentStatusBadge status={doc.status} ocrStatus={doc.ocrStatus} />
                  </div>
                </div>
                <span className="shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium capitalize text-slate-600">
                  {doc.documentType}
                </span>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => togglePreview(doc)}
                  className={`rounded-md border px-3 py-1.5 text-xs font-medium ${
                    previewDoc?.id === doc.id
                      ? "border-blue-300 bg-blue-50 text-blue-800"
                      : "border-slate-200 bg-white text-slate-800 hover:bg-slate-50"
                  }`}
                  data-testid={`preview-${doc.id}`}
                  aria-pressed={previewDoc?.id === doc.id}
                >
                  {previewDoc?.id === doc.id ? "Viewing…" : "Preview"}
                </button>
              </div>
              {(doc.ocrStatus === "failed" || doc.status === "failed") && (
                <button
                  type="button"
                  onClick={() => retryOcr(doc.id)}
                  disabled={retryingId === doc.id}
                  className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-medium text-red-800 hover:bg-red-100 disabled:opacity-50"
                >
                  {retryingId === doc.id ? "Retrying OCR…" : "Retry OCR"}
                </button>
              )}
            </li>
          ))}
          {documents.length === 0 && (
            <li className="rounded-lg border border-dashed border-slate-200 px-4 py-8 text-center text-sm text-slate-500">
              No documents yet. Upload PDF or text files to start the pipeline.
            </li>
          )}
        </ul>
        <PipelineSteps
          stages={pipelineStages}
          currentStage={currentStage}
          title="Processing timeline"
          emptyMessage="Upload a document to begin virus scan, OCR, and AI summarization."
        />
      </div>

      <DocumentPreviewModal document={previewDoc} onClose={() => setPreviewDoc(null)} />
    </DashboardShell>
  );
}
