"use client";

import type { CaseSummary, ClientDetail } from "@lexflow/shared";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetch, apiFetchList } from "@/lib/auth";

type ClientType = "individual" | "organization";

type EditForm = {
  name: string;
  type: ClientType;
  email: string;
  phone: string;
};

function toEditForm(client: ClientDetail): EditForm {
  return {
    name: client.name,
    type: (client.type as ClientType) || "individual",
    email: client.email ?? "",
    phone: client.phone ?? "",
  };
}

export default function ClientDetailPage() {
  const params = useParams<{ id: string }>();
  const clientId = params.id;
  const [client, setClient] = useState<ClientDetail | null>(null);
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<EditForm | null>(null);
  const [saving, setSaving] = useState(false);

  function loadClient() {
    if (!clientId) return;
    setLoading(true);
    setError(null);

    Promise.all([
      apiFetch<ClientDetail>(`/api/v1/clients/${clientId}`),
      apiFetchList<CaseSummary>(`/api/v1/clients/${clientId}/cases`),
    ])
      .then(([detail, caseList]) => {
        setClient(detail);
        setForm(toEditForm(detail));
        setCases(caseList.items);
      })
      .catch((e: Error) => {
        setClient(null);
        setCases([]);
        setError(e.message);
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadClient();
  }, [clientId]);

  async function onSave(e: FormEvent) {
    e.preventDefault();
    if (!client || !form) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await apiFetch<ClientDetail>(`/api/v1/clients/${client.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          name: form.name.trim(),
          type: form.type,
          email: form.email.trim() || null,
          phone: form.phone.trim() || null,
          version: client.version,
        }),
      });
      setClient(updated);
      setForm(toEditForm(updated));
      setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update client");
    } finally {
      setSaving(false);
    }
  }

  function onCancelEdit() {
    if (client) setForm(toEditForm(client));
    setEditing(false);
    setError(null);
  }

  if (loading) {
    return (
      <DashboardShell>
        <p className="text-slate-500" data-testid="client-detail-loading">
          Loading client…
        </p>
      </DashboardShell>
    );
  }

  if (error && !client) {
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

  if (!client || !form) {
    return null;
  }

  return (
    <DashboardShell>
      <Link href="/clients" className="text-sm text-blue-700 hover:underline">
        ← Back to clients
      </Link>

      <div className="mt-4 flex items-start justify-between gap-4" data-testid="client-detail">
        {editing ? (
          <form onSubmit={onSave} className="max-w-xl flex-1 space-y-4">
            <h1 className="text-2xl font-semibold">Edit client</h1>
            <label className="block text-sm">
              Name
              <input
                value={form.name}
                onChange={(e) => setForm((f) => (f ? { ...f, name: e.target.value } : f))}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                required
                data-testid="client-edit-name"
              />
            </label>
            <label className="block text-sm">
              Type
              <select
                value={form.type}
                onChange={(e) =>
                  setForm((f) => (f ? { ...f, type: e.target.value as ClientType } : f))
                }
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                data-testid="client-edit-type"
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
                onChange={(e) => setForm((f) => (f ? { ...f, email: e.target.value } : f))}
                placeholder="client@example.com"
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                data-testid="client-edit-email"
              />
            </label>
            <label className="block text-sm">
              Phone
              <input
                type="tel"
                value={form.phone}
                onChange={(e) => setForm((f) => (f ? { ...f, phone: e.target.value } : f))}
                placeholder="+1 (555) 123-4567"
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                data-testid="client-edit-phone"
              />
            </label>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={saving}
                className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50"
              >
                {saving ? "Saving…" : "Save changes"}
              </button>
              <button
                type="button"
                onClick={onCancelEdit}
                className="rounded-md border border-slate-300 px-4 py-2 text-sm"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <div>
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
        )}

        {!editing && (
          <button
            type="button"
            onClick={() => setEditing(true)}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
            data-testid="client-edit-button"
          >
            Edit
          </button>
        )}
      </div>

      {error && client && (
        <p className="mt-4 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}

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
