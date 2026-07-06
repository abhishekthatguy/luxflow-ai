"use client";

import type { ClientSummary } from "@lexflow/shared";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetch, apiFetchList } from "@/lib/auth";

export default function ClientsPage() {
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  function load() {
    apiFetchList<ClientSummary>("/api/v1/clients")
      .then(({ items }) => setClients(items))
      .catch((e: Error) => setError(e.message));
  }

  useEffect(() => {
    load();
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    await apiFetch<ClientSummary>("/api/v1/clients", {
      method: "POST",
      body: JSON.stringify({ name, type: "individual" }),
    });
    setName("");
    load();
  }

  return (
    <DashboardShell>
      <h1 className="text-2xl font-semibold">Clients</h1>
      <form onSubmit={onCreate} className="mt-6 flex gap-2">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Client name"
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
          required
        />
        <button type="submit" className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white">
          Add client
        </button>
      </form>
      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
      <ul className="mt-6 space-y-2">
        {clients.map((c) => (
          <li key={c.id} className="rounded-md border border-slate-200 px-4 py-3 text-sm">
            <span className="font-medium">{c.name}</span>
            <span className="ml-2 text-slate-500">{c.type}</span>
            <Link href={`/clients/${c.id}`} className="ml-4 text-blue-700 hover:underline">
              View
            </Link>
          </li>
        ))}
      </ul>
    </DashboardShell>
  );
}
