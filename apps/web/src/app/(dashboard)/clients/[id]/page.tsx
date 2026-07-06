"use client";

import type { CaseSummary, ClientDetail } from "@lexflow/shared";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetch, apiFetchList } from "@/lib/auth";

export default function ClientDetailPage() {
  const params = useParams<{ id: string }>();
  const clientId = params.id;
  const [client, setClient] = useState<ClientDetail | null>(null);
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!clientId) return;
    setLoading(true);
    setError(null);

    Promise.all([
      apiFetch<ClientDetail>(`/api/v1/clients/${clientId}`),
      apiFetchList<CaseSummary>(`/api/v1/clients/${clientId}/cases`),
    ])
      .then(([detail, caseList]) => {
        setClient(detail);
        setCases(caseList.items);
      })
      .catch((e: Error) => {
        setClient(null);
        setCases([]);
        setError(e.message);
      })
      .finally(() => setLoading(false));
  }, [clientId]);

  if (loading) {
    return (
      <DashboardShell>
        <p className="text-slate-500" data-testid="client-detail-loading">
          Loading client…
        </p>
      </DashboardShell>
    );
  }

  if (error || !client) {
    return (
      <DashboardShell>
        <Link href="/clients" className="text-sm text-blue-700 hover:underline">
          ← Back to clients
        </Link>
        <div
          className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-red-800"
          data-testid="client-not-found"
          role="alert"
        >
          <p className="font-medium">Client not found</p>
          <p className="mt-1 text-sm">{error ?? "This client does not exist or you cannot access it."}</p>
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell>
      <Link href="/clients" className="text-sm text-blue-700 hover:underline">
        ← Back to clients
      </Link>
      <div className="mt-4" data-testid="client-detail">
        <h1 className="text-2xl font-semibold">{client.name}</h1>
        <p className="mt-1 capitalize text-slate-600">{client.type}</p>
        <dl className="mt-6 grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-slate-500">Email</dt>
            <dd data-testid="client-email">{client.email ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Phone</dt>
            <dd data-testid="client-phone">{client.phone ?? "—"}</dd>
          </div>
        </dl>
      </div>

      <section className="mt-10">
        <h2 className="text-lg font-medium">Cases</h2>
        {cases.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500" data-testid="client-cases-empty">
            No cases linked to this client yet.
          </p>
        ) : (
          <ul className="mt-3 space-y-2" data-testid="client-cases-list">
            {cases.map((c) => (
              <li key={c.id} className="rounded-md border border-slate-200 px-4 py-3 text-sm">
                <Link href={`/cases/${c.id}/overview`} className="font-medium text-blue-700 hover:underline">
                  {c.caseNumber} — {c.title}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </DashboardShell>
  );
}
