"use client";

import { AccessDenied, DashboardShell, useRequirePermission } from "@/components/dashboard-shell";
import { PERM } from "@/lib/permissions";

export default function OperationsLayout({ children }: { children: React.ReactNode }) {
  const { allowed, loading, user } = useRequirePermission(PERM.OPERATIONS);

  if (loading) {
    return (
      <DashboardShell>
        <p className="text-slate-500">Loading…</p>
      </DashboardShell>
    );
  }

  if (!allowed) {
    return (
      <DashboardShell>
        <AccessDenied message="Operations dashboard access requires Admin or Managing Partner role." />
      </DashboardShell>
    );
  }

  return (
    <DashboardShell>
      <h1 className="text-2xl font-semibold">Operations Dashboard</h1>
      <p className="mt-1 text-sm text-slate-600">
        Service health, queues, AI jobs, and platform metrics
        {user ? ` · ${user.firstName} ${user.lastName}` : ""}
      </p>
      <div className="mt-6">{children}</div>
    </DashboardShell>
  );
}
