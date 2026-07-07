"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS: { href: string; label: string; roles?: string[] }[] = [
  { href: "/operations", label: "Overview" },
  { href: "/operations/health", label: "Health" },
  { href: "/operations/queues", label: "Queues" },
  { href: "/operations/workers", label: "Workers" },
  { href: "/operations/jobs", label: "AI Jobs" },
  { href: "/operations/workflows", label: "Workflow Runs" },
  { href: "/operations/audit", label: "Audit", roles: ["ManagingPartner", "SystemAdministrator"] },
  { href: "/operations/metrics", label: "Metrics" },
];

export function OperationsNav({ roles }: { roles: string[] }) {
  const pathname = usePathname();
  return (
    <nav className="mb-6 flex flex-wrap gap-2 border-b border-slate-200 pb-4 text-sm">
      {LINKS.filter(
        (item) => !item.roles || item.roles.some((r) => roles.includes(r)),
      ).map((item) => {
        const active =
          item.href === "/operations"
            ? pathname === "/operations"
            : pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`rounded-md px-3 py-1.5 ${
              active
                ? "bg-slate-900 font-medium text-white"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
