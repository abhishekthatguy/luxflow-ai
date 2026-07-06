"use client";

import type { CaseSummary } from "@lexflow/shared";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetch, apiFetchList } from "@/lib/auth";

type TaskItem = {
  id: string;
  title: string;
  status: string;
  dueAt?: string | null;
};

export default function CaseTasksPage() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;
  const [caseData, setCaseData] = useState<CaseSummary | null>(null);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [title, setTitle] = useState("");

  function load() {
    if (!caseId) return;
    apiFetch<CaseSummary>(`/api/v1/cases/${caseId}`).then(setCaseData);
    apiFetchList<TaskItem>(`/api/v1/cases/${caseId}/tasks`).then(({ items }) => setTasks(items));
  }

  useEffect(() => {
    load();
  }, [caseId]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    await apiFetch(`/api/v1/cases/${caseId}/tasks`, {
      method: "POST",
      body: JSON.stringify({ title }),
    });
    setTitle("");
    load();
  }

  return (
    <DashboardShell>
      <Link href={`/cases/${caseId}/overview`} className="text-sm text-blue-700 hover:underline">
        ← {caseData?.caseNumber ?? "Case"}
      </Link>
      <h1 className="mt-4 text-2xl font-semibold">Tasks</h1>
      <form onSubmit={onCreate} className="mt-4 flex gap-2">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Task title"
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
          required
        />
        <button type="submit" className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white">
          Add
        </button>
      </form>
      <ul className="mt-6 space-y-2">
        {tasks.map((t) => (
          <li key={t.id} className="flex items-center justify-between rounded-md border px-4 py-3 text-sm">
            <span>{t.title}</span>
            <span className="capitalize text-slate-500">{t.status.replace("_", " ")}</span>
          </li>
        ))}
      </ul>
    </DashboardShell>
  );
}
