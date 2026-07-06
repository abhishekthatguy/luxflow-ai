"use client";

import type { CaseSummary } from "@lexflow/shared";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { apiFetchList } from "@/lib/auth";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const search = useCallback(async (q: string) => {
    if (!q.trim()) {
      setCases([]);
      return;
    }
    setLoading(true);
    try {
      const { items } = await apiFetchList<CaseSummary>(
        `/api/v1/cases?search=${encodeURIComponent(q)}&pageSize=8`,
      );
      setCases(items);
    } catch {
      setCases([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    const t = setTimeout(() => search(query), 200);
    return () => clearTimeout(t);
  }, [open, query, search]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 pt-[15vh]"
      role="presentation"
      onClick={() => setOpen(false)}
    >
      <div
        className="w-full max-w-lg rounded-lg bg-white shadow-xl"
        role="dialog"
        aria-label="Command palette"
        onClick={(e) => e.stopPropagation()}
      >
        <input
          autoFocus
          className="w-full border-b px-4 py-3 text-sm outline-none"
          placeholder="Search cases… (⌘K)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <ul className="max-h-64 overflow-y-auto py-2 text-sm">
          {loading && <li className="px-4 py-2 text-slate-500">Searching…</li>}
          {!loading && query && cases.length === 0 && (
            <li className="px-4 py-2 text-slate-500">No cases found</li>
          )}
          {cases.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                className="w-full px-4 py-2 text-left hover:bg-slate-50"
                onClick={() => {
                  setOpen(false);
                  router.push(`/cases/${c.id}/overview`);
                }}
              >
                <span className="font-medium">{c.caseNumber}</span>
                <span className="ml-2 text-slate-500">{c.title}</span>
              </button>
            </li>
          ))}
          {!query && (
            <li className="px-4 py-2 text-slate-500">Type to search cases, or navigate via sidebar.</li>
          )}
        </ul>
      </div>
    </div>
  );
}
