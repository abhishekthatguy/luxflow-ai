"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/lib/auth";

const NAV = [
  { href: "/cases", label: "Cases" },
  { href: "/clients", label: "Clients" },
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center text-slate-500">
        Loading…
      </main>
    );
  }

  return (
    <div className="flex min-h-screen">
      <aside className="w-56 border-r border-slate-200 bg-slate-50 p-4">
        <p className="text-lg font-semibold text-slate-900">LexFlow AI</p>
        <p className="mt-1 text-xs text-slate-500">
          {user.firstName} {user.lastName}
        </p>
        <nav className="mt-6 flex flex-col gap-1">
          {NAV.map((item) => (
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
        <button
          type="button"
          onClick={() => {
            logout();
            router.push("/login");
          }}
          className="mt-8 text-sm text-slate-500 hover:text-slate-800"
        >
          Sign out
        </button>
      </aside>
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
