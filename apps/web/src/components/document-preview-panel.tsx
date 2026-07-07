"use client";

import type { DocumentSummary } from "@lexflow/shared";
import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { apiFetch, getStoredAccessToken } from "@/lib/auth";

type DocumentDetail = DocumentSummary & {
  ocrText?: string | null;
};

type PreviewTab = "file" | "ocr";

function apiBase(): string {
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

function isPdf(mime: string): boolean {
  return mime === "application/pdf" || mime.endsWith("/pdf");
}

function isText(mime: string): boolean {
  return mime.startsWith("text/") || mime === "application/json";
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

type DocumentPreviewModalProps = {
  document: DocumentSummary | null;
  onClose: () => void;
};

export function DocumentPreviewModal({ document, onClose }: DocumentPreviewModalProps) {
  const [mounted, setMounted] = useState(false);
  const [tab, setTab] = useState<PreviewTab>("file");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [textContent, setTextContent] = useState<string | null>(null);
  const [detail, setDetail] = useState<DocumentDetail | null>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => setMounted(true), []);

  const handleClose = useCallback(() => {
    onClose();
  }, [onClose]);

  useEffect(() => {
    if (!document) return;

    const previousOverflow = window.document.body.style.overflow;
    window.document.body.style.overflow = "hidden";

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") handleClose();
    };
    window.addEventListener("keydown", onKeyDown);
    closeButtonRef.current?.focus();

    return () => {
      window.document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [document, handleClose]);

  useEffect(() => {
    if (!document) {
      setBlobUrl(null);
      setTextContent(null);
      setDetail(null);
      setError(null);
      return;
    }

    let active = true;
    let objectUrl: string | null = null;
    setLoading(true);
    setError(null);
    setTab("file");

    const token = getStoredAccessToken();

    Promise.all([
      fetch(`${apiBase()}/api/v1/documents/${document.id}/content`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      }),
      apiFetch<DocumentDetail>(`/api/v1/documents/${document.id}`),
    ])
      .then(async ([contentRes, docDetail]) => {
        if (!contentRes.ok) {
          const body = await contentRes.json().catch(() => ({}));
          const detailMsg =
            typeof body === "object" && body && "detail" in body
              ? String((body as { detail: string }).detail)
              : contentRes.statusText;
          throw new Error(detailMsg || `Preview failed (${contentRes.status})`);
        }
        const blob = await contentRes.blob();
        const url = URL.createObjectURL(blob);
        if (!active) {
          URL.revokeObjectURL(url);
          return;
        }
        objectUrl = url;
        setDetail(docDetail);
        setBlobUrl(url);
        if (isText(document.mimeType)) {
          setTextContent(await blob.text());
        }
      })
      .catch((err: Error) => {
        if (active) setError(err.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [document]);

  if (!document || !mounted) return null;

  const ocrText = detail?.ocrText?.trim();
  const showOcrTab = Boolean(ocrText);

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-3 sm:p-6"
      role="presentation"
      onClick={handleClose}
      data-testid="document-preview-modal"
    >
      <div
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-[2px]"
        aria-hidden="true"
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="document-preview-title"
        className="relative flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl ring-1 ring-slate-200"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex shrink-0 items-start justify-between gap-3 border-b border-slate-200 px-4 py-3 sm:px-5">
          <div className="min-w-0 pr-2">
            <h2 id="document-preview-title" className="truncate text-lg font-semibold text-slate-900">
              {document.title}
            </h2>
            <p className="mt-0.5 text-xs text-slate-500">
              {document.mimeType} · {formatBytes(document.fileSizeBytes)}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {blobUrl && (
              <a
                href={blobUrl}
                download={document.title.replace(/\s+/g, "_")}
                className="rounded-md border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
              >
                Download
              </a>
            )}
            <button
              ref={closeButtonRef}
              type="button"
              onClick={handleClose}
              className="rounded-md border border-slate-200 p-1.5 text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              aria-label="Close preview"
            >
              <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5" aria-hidden="true">
                <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
              </svg>
            </button>
          </div>
        </div>

        <div className="flex shrink-0 gap-1 border-b border-slate-100 px-4 sm:px-5">
          <button
            type="button"
            onClick={() => setTab("file")}
            className={`border-b-2 px-3 py-2.5 text-xs font-medium transition-colors ${
              tab === "file"
                ? "border-slate-900 text-slate-900"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            Original file
          </button>
          {showOcrTab && (
            <button
              type="button"
              onClick={() => setTab("ocr")}
              className={`border-b-2 px-3 py-2.5 text-xs font-medium transition-colors ${
                tab === "ocr"
                  ? "border-slate-900 text-slate-900"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              Extracted text (OCR)
            </button>
          )}
        </div>

        <div className="min-h-0 flex-1 overflow-auto p-4 sm:p-5">
          {loading && (
            <div className="flex flex-col items-center justify-center gap-3 py-20">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-slate-800" />
              <p className="text-sm text-slate-500">Loading preview…</p>
            </div>
          )}
          {error && (
            <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
              {error}
            </p>
          )}

          {!loading && !error && tab === "file" && blobUrl && (
            <>
              {isPdf(document.mimeType) && (
                <iframe
                  title={`Preview ${document.title}`}
                  src={blobUrl}
                  className="h-[min(70vh,640px)] w-full rounded-lg border border-slate-200 bg-slate-50"
                />
              )}
              {isText(document.mimeType) && textContent !== null && (
                <pre className="max-h-[min(70vh,640px)] overflow-auto rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs leading-relaxed whitespace-pre-wrap text-slate-800">
                  {textContent}
                </pre>
              )}
              {!isPdf(document.mimeType) && !isText(document.mimeType) && (
                <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
                  <p className="text-sm text-slate-600">
                    Inline preview is not available for this file type ({document.mimeType}).
                  </p>
                  <a
                    href={blobUrl}
                    download
                    className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
                  >
                    Download to view
                  </a>
                  {showOcrTab && (
                    <button
                      type="button"
                      onClick={() => setTab("ocr")}
                      className="text-sm font-medium text-blue-700 hover:underline"
                    >
                      View extracted OCR text instead
                    </button>
                  )}
                </div>
              )}
            </>
          )}

          {!loading && !error && tab === "ocr" && ocrText && (
            <pre className="max-h-[min(70vh,640px)] overflow-auto rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs leading-relaxed whitespace-pre-wrap text-slate-800">
              {ocrText}
            </pre>
          )}
        </div>

        <div className="shrink-0 border-t border-slate-100 bg-slate-50 px-4 py-2.5 text-center text-xs text-slate-500 sm:px-5">
          Press <kbd className="rounded border border-slate-200 bg-white px-1.5 py-0.5 font-mono text-[10px]">Esc</kbd>{" "}
          or click outside to close
        </div>
      </div>
    </div>,
    window.document.body,
  );
}

/** @deprecated Use DocumentPreviewModal */
export const DocumentPreviewPanel = DocumentPreviewModal;
