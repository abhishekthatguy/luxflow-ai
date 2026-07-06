"use client";

import type { AuditLogEntry } from "@lexflow/shared";
import { useEffect, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { apiFetchList, useAuth } from "@/lib/auth";

export default function AuditPage() {
  const { user } = useAuth();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  const canView = user?.roles.some((r) =>
    ["ManagingPartner", "SystemAdministrator"].includes(r),
  );

  useEffect(() => {
    if (!canView) return;
    apiFetchList<AuditLogEntry>("/api/v1/audit/logs?pageSize=50")
      .then(({ items }) => setLogs(items))
      .catch((e: Error) => setError(e.message));
  }, [canView]);

  return (
    <DashboardShell>
      <h1 className="text-2xl font-semibold">Audit log</h1>
      {!canView && (
        <p className="mt-4 text-sm text-slate-600">
          Audit log access requires Managing Partner or System Administrator role.
        </p>
      )}
      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
      {canView && (
        <table className="mt-6 w-full text-left text-sm">
          <thead>
            <tr className="border-b text-slate-500">
              <th className="py-2 pr-4">Time</th>
              <th className="py-2 pr-4">Action</th>
              <th className="py-2 pr-4">Resource</th>
              <th className="py-2 pr-4">Actor</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id} className="border-b border-slate-100">
                <td className="py-2 pr-4 text-slate-600">
                  {new Date(log.createdAt).toLocaleString()}
                </td>
                <td className="py-2 pr-4">{log.action}</td>
                <td className="py-2 pr-4">
                  {log.resourceType}
                  {log.resourceId ? ` · ${log.resourceId.slice(0, 8)}…` : ""}
                </td>
                <td className="py-2 pr-4 text-slate-600">{log.actorId?.slice(0, 8) ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </DashboardShell>
  );
}
