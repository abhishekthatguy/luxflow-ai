"use client";

import type { DocumentSummary } from "@lexflow/shared";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { CaseNav } from "@/components/case-nav";
import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetch, apiFetchList } from "@/lib/auth";

type InitiateResponse = {
  id: string;
  uploadUrl: string;
  s3Key: string;
};

export default function CaseDocumentsPage() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

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

  async function onUpload(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const fileInput = form.elements.namedItem("file") as HTMLInputElement;
    const file = fileInput.files?.[0];
    if (!file || !caseId) return;

    setUploading(true);
    setError(null);
    setMessage(null);

    try {
      const buffer = await file.arrayBuffer();
      const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
      const checksum = Array.from(new Uint8Array(hashBuffer))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");

      const initiated = await apiFetch<InitiateResponse>(`/api/v1/cases/${caseId}/documents`, {
        method: "POST",
        body: JSON.stringify({
          title: file.name,
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
      if (!putRes.ok) throw new Error(`S3 upload failed (${putRes.status})`);

      await apiFetch(`/api/v1/documents/${initiated.id}/confirm`, {
        method: "POST",
        body: JSON.stringify({ checksumSha256: checksum }),
      });

      setMessage(`Uploaded ${file.name} — OCR processing started.`);
      fileInput.value = "";
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <DashboardShell>
      <div className="flex items-start justify-between gap-4">
        <h1 className="text-2xl font-semibold">Documents</h1>
        {caseId && <CaseNav caseId={caseId} active="documents" />}
      </div>

      <form onSubmit={onUpload} className="mt-6 rounded-lg border border-dashed border-slate-300 p-6">
        <label className="block text-sm font-medium">
          Upload document
          <input
            name="file"
            type="file"
            accept=".pdf,.txt,application/pdf,text/plain"
            className="mt-2 block w-full text-sm"
            required
          />
        </label>
        <button
          type="submit"
          disabled={uploading}
          className="mt-4 rounded-md bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          {uploading ? "Uploading…" : "Upload"}
        </button>
      </form>

      {message && <p className="mt-4 text-sm text-green-700">{message}</p>}
      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <ul className="mt-8 space-y-2" data-testid="documents-list">
        {documents.map((doc) => (
          <li key={doc.id} className="rounded-md border border-slate-200 px-4 py-3 text-sm">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="font-medium">{doc.title}</p>
                <p className="text-slate-500 capitalize">
                  {doc.status.replace("_", " ")} · OCR {doc.ocrStatus}
                </p>
              </div>
              <span className="rounded-full bg-slate-100 px-2 py-1 text-xs capitalize">
                {doc.documentType}
              </span>
            </div>
          </li>
        ))}
        {documents.length === 0 && (
          <li className="text-slate-500">No documents yet. Upload a PDF or text file.</li>
        )}
      </ul>
    </DashboardShell>
  );
}
