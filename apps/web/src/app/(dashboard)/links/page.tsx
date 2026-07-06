"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { allResourceLinks, resourceLinkGroups } from "@/content/resource-links";
import { useAuth } from "@/lib/auth";

function LinkRow({
  title,
  description,
  href,
  external,
  repoPath,
}: {
  title: string;
  description: string;
  href?: string;
  external?: boolean;
  repoPath?: string;
}) {
  const className =
    "block rounded-lg border border-slate-200 bg-white p-4 transition hover:border-slate-300 hover:shadow-sm";

  if (repoPath) {
    return (
      <div className={className}>
        <p className="font-medium text-slate-900">{title}</p>
        <p className="mt-1 text-sm text-slate-600">{description}</p>
        <p className="mt-2 font-mono text-xs text-slate-500">{repoPath}</p>
      </div>
    );
  }

  if (!href) return null;

  if (external) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className={className}>
        <p className="font-medium text-slate-900">
          {title}
          <span className="ml-2 text-xs font-normal text-slate-400">↗</span>
        </p>
        <p className="mt-1 text-sm text-slate-600">{description}</p>
        <p className="mt-2 truncate font-mono text-xs text-slate-400">{href}</p>
      </a>
    );
  }

  return (
    <Link href={href} className={className}>
      <p className="font-medium text-slate-900">{title}</p>
      <p className="mt-1 text-sm text-slate-600">{description}</p>
      <p className="mt-2 truncate font-mono text-xs text-slate-400">{href}</p>
    </Link>
  );
}

export default function LinksPage() {
  const { user } = useAuth();
  const [query, setQuery] = useState("");

  const filteredGroups = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return resourceLinkGroups;

    return resourceLinkGroups
      .map((group) => ({
        ...group,
        links: group.links.filter(
          (link) =>
            link.title.toLowerCase().includes(q) ||
            link.description.toLowerCase().includes(q) ||
            (link.href?.toLowerCase().includes(q) ?? false) ||
            (link.repoPath?.toLowerCase().includes(q) ?? false),
        ),
      }))
      .filter((group) => group.links.length > 0);
  }, [query]);

  const totalCount = allResourceLinks().length;
  const visibleCount = filteredGroups.reduce((n, g) => n + g.links.length, 0);

  return (
    <DashboardShell>
      <div className="max-w-3xl">
        <h1 className="text-2xl font-semibold text-slate-900">My Tools</h1>
        <p className="mt-2 text-sm text-slate-600">
          Quick access to API docs, local dev tools, demo materials, and app routes. Signed in as{" "}
          {user?.firstName} {user?.lastName}.
        </p>

        <label className="mt-6 block text-sm">
          <span className="text-slate-700">Search links</span>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter by name, URL, or description…"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </label>
        <p className="mt-2 text-xs text-slate-500">
          Showing {visibleCount} of {totalCount} links
        </p>

        <div className="mt-8 space-y-10">
          {filteredGroups.length === 0 ? (
            <p className="text-sm text-slate-500">No links match your search.</p>
          ) : (
            filteredGroups.map((group) => (
              <section key={group.id}>
                <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
                  {group.title}
                </h2>
                <ul className="mt-3 space-y-3">
                  {group.links.map((link) => (
                    <li key={link.id}>
                      <LinkRow
                        title={link.title}
                        description={link.description}
                        href={link.href}
                        external={link.external}
                        repoPath={link.repoPath}
                      />
                    </li>
                  ))}
                </ul>
              </section>
            ))
          )}
        </div>

        <p className="mt-10 text-xs text-slate-400">
          To add links, edit{" "}
          <code className="rounded bg-slate-100 px-1">apps/web/src/content/resource-links.ts</code>.
        </p>
      </div>
    </DashboardShell>
  );
}
