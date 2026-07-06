"use client";

import type { CaseSummary } from "@lexflow/shared";
import Link from "next/link";
import { useEffect, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetchList } from "@/lib/auth";

export default function CasesPage() {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetchList<CaseSummary>("/api/v1/cases")
      .then(({ items }) => setCases(items))
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <DashboardShell>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Cases</h1>
        <Link
          href="/cases/new"
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white"
        >
          New case
        </Link>
      </div>
      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
      {cases.length === 0 && !error ? (
        <p className="mt-8 text-slate-500">No cases yet. Create your first matter.</p>
      ) : (
        <table className="mt-6 w-full text-left text-sm">
          <thead>
            <tr className="border-b text-slate-500">
              <th className="py-2 pr-4">Number</th>
              <th className="py-2 pr-4">Title</th>
              <th className="py-2 pr-4">Status</th>
              <th className="py-2 pr-4">Priority</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((c) => (
              <tr key={c.id} className="border-b border-slate-100">
                <td className="py-3 pr-4">
                  <Link href={`/cases/${c.id}/overview`} className="text-blue-700 hover:underline">
                    {c.caseNumber}
                  </Link>
                </td>
                <td className="py-3 pr-4">{c.title}</td>
                <td className="py-3 pr-4 capitalize">{c.status.replace("_", " ")}</td>
                <td className="py-3 pr-4 capitalize">{c.priority}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </DashboardShell>
  );
}
