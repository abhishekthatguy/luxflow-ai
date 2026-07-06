"use client";

import type { ClientSummary } from "@lexflow/shared";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetch, apiFetchList, useAuth } from "@/lib/auth";

export default function NewCasePage() {
  const { user } = useAuth();
  const router = useRouter();
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [clientId, setClientId] = useState("");
  const [title, setTitle] = useState("");
  const [caseNumber, setCaseNumber] = useState("");
  const [practiceArea, setPracticeArea] = useState("litigation");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetchList<ClientSummary>("/api/v1/clients").then(({ items }) => {
      setClients(items);
      if (items[0]) setClientId(items[0].id);
    });
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!user) return;
    try {
      const created = await apiFetch<{ id: string }>("/api/v1/cases", {
        method: "POST",
        body: JSON.stringify({
          clientId,
          caseNumber,
          title,
          practiceArea,
          leadAttorneyId: user.id,
        }),
      });
      router.push(`/cases/${created.id}/overview`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create case");
    }
  }

  return (
    <DashboardShell>
      <h1 className="text-2xl font-semibold">New case</h1>
      <form onSubmit={onSubmit} className="mt-6 max-w-lg space-y-4">
        <label className="block text-sm">
          Client
          <select
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            required
          >
            {clients.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          Case number
          <input
            value={caseNumber}
            onChange={(e) => setCaseNumber(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            required
          />
        </label>
        <label className="block text-sm">
          Title
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            required
          />
        </label>
        <label className="block text-sm">
          Practice area
          <input
            value={practiceArea}
            onChange={(e) => setPracticeArea(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white">
          Create case
        </button>
      </form>
    </DashboardShell>
  );
}
