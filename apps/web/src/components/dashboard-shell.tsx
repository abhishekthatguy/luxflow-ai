"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { GlobalSearch } from "@/components/global-search";
import { NotificationBell } from "@/components/notification-bell";
import { useAuth } from "@/lib/auth";
import {
  canManageUsers,
  canManageWorkflows,
  canViewOperations,
  hasPermission,
} from "@/lib/permissions";

const NAV: { href: string; label: string; visible: (permissions: string[]) => boolean }[] = [
  { href: "/cases", label: "Cases", visible: () => true },
  { href: "/clients", label: "Clients", visible: () => true },
  {
    href: "/workflows",
    label: "Workflows",
    visible: (p) => canManageWorkflows(p),
  },
  {
    href: "/operations",
    label: "Operations",
    visible: (p) => canViewOperations(p),
  },
  {
    href: "/admin/users",
    label: "Users",
    visible: (p) => canManageUsers(p),
  },
  { href: "/links", label: "My Tools", visible: () => true },
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [searchOpen, setSearchOpen] = useState(false);
  const permissions = user?.permissions ?? [];

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setSearchOpen((v) => !v);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center text-slate-500">
        Loading…
      </main>
    );
  }

  const navItems = NAV.filter((item) => item.visible(permissions));

  return (
    <div className="flex min-h-screen flex-col">
      <GlobalSearch open={searchOpen} onClose={() => setSearchOpen(false)} />
      <header className="flex items-center gap-4 border-b border-slate-200 bg-white px-6 py-3">
        <p className="text-lg font-semibold text-slate-900">LexFlow AI</p>
        <button
          type="button"
          onClick={() => setSearchOpen(true)}
          className="flex flex-1 max-w-md items-center gap-2 rounded-md border border-slate-300 bg-slate-50 px-3 py-2 text-left text-sm text-slate-500 hover:border-slate-400"
          data-testid="global-search-trigger"
        >
          <span>Search</span>
          <span className="ml-auto rounded border border-slate-200 bg-white px-1.5 text-xs">⌘K</span>
        </button>
        <NotificationBell />
        <p className="hidden text-sm text-slate-600 sm:block">
          {user.firstName} {user.lastName}
        </p>
      </header>
      <div className="flex flex-1">
        <aside className="w-56 border-r border-slate-200 bg-slate-50 p-4">
          <nav className="flex flex-col gap-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-md px-3 py-2 text-sm ${
                  pathname.startsWith(item.href)
                    ? "bg-white font-medium text-slate-900 shadow-sm"
                    : "text-slate-600 hover:bg-white/60"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          {permissions.length > 0 && (
            <p className="mt-6 text-xs text-slate-400">
              Role: {user.roles.join(", ") || "—"}
            </p>
          )}
          <button
            type="button"
            onClick={() => {
              logout();
              router.push("/login");
            }}
            className="mt-4 text-sm text-slate-500 hover:text-slate-800"
          >
            Sign out
          </button>
        </aside>
        <main className="flex-1 p-8">{children}</main>
      </div>
    </div>
  );
}

export function AccessDenied({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
      <p className="font-medium">Access restricted</p>
      <p className="mt-2">{message}</p>
      <Link href="/cases" className="mt-4 inline-block text-blue-700 hover:underline">
        Back to cases
      </Link>
    </div>
  );
}

export function useRequirePermission(permission: string, redirectTo = "/cases") {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading || !user) return;
    if (!hasPermission(user.permissions, permission as never)) {
      router.replace(redirectTo);
    }
  }, [loading, user, permission, redirectTo, router]);

  return {
    allowed: user ? hasPermission(user.permissions, permission as never) : false,
    loading,
    user,
  };
}
