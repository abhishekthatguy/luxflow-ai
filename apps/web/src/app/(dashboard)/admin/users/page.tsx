"use client";

import type { AdminUserSummary } from "@lexflow/shared";
import { useEffect, useState } from "react";

import { AccessDenied, DashboardShell, useRequirePermission } from "@/components/dashboard-shell";
import { apiFetchList } from "@/lib/auth";
import { PERM } from "@/lib/permissions";

export default function AdminUsersPage() {
  const { allowed, loading: authLoading } = useRequirePermission(PERM.MANAGE_USERS);
  const [users, setUsers] = useState<AdminUserSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!allowed) return;
    apiFetchList<AdminUserSummary>("/api/v1/admin/users")
      .then(({ items }) => setUsers(items))
      .catch((e: Error) => setError(e.message));
  }, [allowed]);

  if (authLoading) {
    return (
      <DashboardShell>
        <p className="text-slate-500">Loading…</p>
      </DashboardShell>
    );
  }

  if (!allowed) {
    return (
      <DashboardShell>
        <AccessDenied message="User management requires System Administrator role." />
      </DashboardShell>
    );
  }

  return (
    <DashboardShell>
      <h1 className="text-2xl font-semibold">Manage users</h1>
      <p className="mt-1 text-sm text-slate-600">Firm staff accounts and RBAC role assignments.</p>
      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
      <table className="mt-6 w-full text-left text-sm">
        <thead>
          <tr className="border-b text-slate-500">
            <th className="py-2 pr-4">Name</th>
            <th className="py-2 pr-4">Email</th>
            <th className="py-2 pr-4">Status</th>
            <th className="py-2 pr-4">Roles</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id} className="border-b border-slate-100">
              <td className="py-3 pr-4">
                {u.firstName} {u.lastName}
              </td>
              <td className="py-3 pr-4">{u.email}</td>
              <td className="py-3 pr-4 capitalize">{u.status}</td>
              <td className="py-3 pr-4">{u.roles.join(", ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </DashboardShell>
  );
}
