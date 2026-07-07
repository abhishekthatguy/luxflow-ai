"use client";

import type { ClientSummary } from "@lexflow/shared";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetch, apiFetchList } from "@/lib/auth";

type ClientType = "individual" | "organization";

const emptyForm = {
  name: "",
  type: "individual" as ClientType,
  email: "",
  phone: "",
};

export default function ClientsPage() {
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

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
    setSubmitting(true);
    setError(null);
    try {
      await apiFetch<ClientSummary>("/api/v1/clients", {
        method: "POST",
        body: JSON.stringify({
          name: form.name.trim(),
          type: form.type,
          email: form.email.trim() || null,
          phone: form.phone.trim() || null,
        }),
      });
      setForm(emptyForm);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create client");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <DashboardShell>
      <h1 className="text-2xl font-semibold">Clients</h1>

      <form
        onSubmit={onCreate}
        className="mt-6 max-w-xl space-y-4 rounded-md border border-slate-200 bg-slate-50 p-4"
        data-testid="client-create-form"
      >
        <h2 className="text-sm font-medium text-slate-700">Add client</h2>
        <label className="block text-sm">
          Name
          <input
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            placeholder="Client or company name"
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2"
            required
            data-testid="client-name-input"
          />
        </label>
        <label className="block text-sm">
          Type
          <select
            value={form.type}
            onChange={(e) => setForm((f) => ({ ...f, type: e.target.value as ClientType }))}
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2"
            data-testid="client-type-select"
          >
            <option value="individual">Individual</option>
            <option value="organization">Organization</option>
          </select>
        </label>
        <label className="block text-sm">
          Email
          <input
            type="email"
            value={form.email}
            onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            placeholder="client@example.com"
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2"
            data-testid="client-email-input"
          />
        </label>
        <label className="block text-sm">
          Phone
          <input
            type="tel"
            value={form.phone}
            onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
            placeholder="+1 (555) 123-4567"
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2"
            data-testid="client-phone-input"
          />
        </label>
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          {submitting ? "Adding…" : "Add client"}
        </button>
      </form>

      {error && (
        <p className="mt-4 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}

      <ul className="mt-6 space-y-2">
        {clients.map((c) => (
          <li key={c.id} className="rounded-md border border-slate-200 px-4 py-3 text-sm">
            <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
              <span className="font-medium">{c.name}</span>
              <span className="text-slate-500 capitalize">{c.type}</span>
              {c.email && <span className="text-slate-500">{c.email}</span>}
              {c.phone && <span className="text-slate-500">{c.phone}</span>}
              <Link href={`/clients/${c.id}`} className="ml-auto text-blue-700 hover:underline">
                View
              </Link>
            </div>
          </li>
        ))}
      </ul>
    </DashboardShell>
  );
}
