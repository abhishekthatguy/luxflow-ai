"use client";

import type { AuditLogEntry } from "@lexflow/shared";
import { useEffect, useState } from "react";

import { apiFetchList } from "@/lib/auth";

export function AuditLogView({ canView }: { canView: boolean }) {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!canView) return;
    apiFetchList<AuditLogEntry>("/api/v1/audit/logs?pageSize=50")
      .then(({ items }) => setLogs(items))
      .catch((e: Error) => setError(e.message));
  }, [canView]);

  if (!canView) {
    return (
      <p className="text-sm text-slate-600">
        Audit log access requires Managing Partner or System Administrator role.
      </p>
    );
  }

  return (
    <>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <table className="mt-4 w-full text-left text-sm">
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
    </>
  );
}
