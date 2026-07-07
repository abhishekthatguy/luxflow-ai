"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "@/lib/auth";

type SearchHit = {
  type: string;
  id: string;
  title: string;
  subtitle?: string | null;
  href: string;
};

type SearchResults = {
  query: string;
  hits: SearchHit[];
};

const TYPE_LABELS: Record<string, string> = {
  case: "Case",
  client: "Client",
  operations: "Operations",
};

export function GlobalSearch({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const search = useCallback(async (q: string) => {
    if (!q.trim()) {
      setHits([]);
      return;
    }
    setLoading(true);
    try {
      const data = await apiFetch<SearchResults>(`/api/v1/search?q=${encodeURIComponent(q)}`);
      setHits(data.hits);
    } catch {
      setHits([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  useEffect(() => {
    if (!open) return;
    const t = setTimeout(() => search(query), 200);
    return () => clearTimeout(t);
  }, [open, query, search]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 pt-[12vh]"
      role="presentation"
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl rounded-lg bg-white shadow-2xl"
        role="dialog"
        aria-label="Search"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 border-b px-4">
          <span className="text-slate-400">⌘K</span>
          <input
            autoFocus
            className="flex-1 py-3 text-sm outline-none"
            placeholder="Search cases, clients, operations…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            data-testid="global-search-input"
          />
        </div>
        <ul className="max-h-80 overflow-y-auto py-2 text-sm">
          {loading && <li className="px-4 py-2 text-slate-500">Searching…</li>}
          {!loading && query && hits.length === 0 && (
            <li className="px-4 py-2 text-slate-500">No results</li>
          )}
          {!query && (
            <li className="px-4 py-3 text-slate-500">
              Search cases, clients, documents, workflows, and operations screens.
            </li>
          )}
          {hits.map((hit) => (
            <li key={`${hit.type}-${hit.id}`}>
              <button
                type="button"
                className="flex w-full flex-col px-4 py-2 text-left hover:bg-slate-50"
                onClick={() => {
                  onClose();
                  router.push(hit.href);
                }}
              >
                <span className="text-xs uppercase text-slate-400">
                  {TYPE_LABELS[hit.type] ?? hit.type}
                </span>
                <span className="font-medium">{hit.title}</span>
                {hit.subtitle && <span className="text-slate-500">{hit.subtitle}</span>}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
