"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { siteConfig } from "@/content/site";

const PORTAL_NAV: { href: string; label: string; exact?: boolean }[] = [
  { href: "/portal", label: "Home", exact: true },
  { href: "/portal/login", label: "Sign in" },
];

export function PortalShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-emerald-50/80 to-slate-50">
      <header className="border-b border-emerald-100/80 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-6 py-4">
          <Link href="/portal" className="flex flex-col">
            <span className="text-lg font-semibold text-emerald-900">{siteConfig.name}</span>
            <span className="text-xs text-emerald-700/80">Client Portal</span>
          </Link>
          <nav className="flex items-center gap-1">
            {PORTAL_NAV.map((item) => {
              const active = item.exact
                ? pathname === item.href
                : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-md px-3 py-2 text-sm ${
                    active
                      ? "bg-emerald-50 font-medium text-emerald-900"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-10">{children}</main>
      <footer className="border-t border-slate-200 bg-white px-6 py-6 text-center text-xs text-slate-500">
        <p>
          Questions? Email{" "}
          <a href="mailto:clawtbot@gmail.com" className="text-emerald-700 hover:underline">
            clawtbot@gmail.com
          </a>
        </p>
        <p className="mt-2">
          <Link href="/privacy" className="hover:text-slate-700">
            Privacy
          </Link>
          {" · "}
          <Link href="/terms" className="hover:text-slate-700">
            Terms
          </Link>
        </p>
      </footer>
    </div>
  );
}
