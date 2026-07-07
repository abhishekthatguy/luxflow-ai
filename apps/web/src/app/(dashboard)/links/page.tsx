"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { allResourceLinks, resourceLinkGroups } from "@/content/resource-links";
import { allRepoCommands, repoCommandGroups, type RepoCommand } from "@/content/repo-commands";
import { useAuth } from "@/lib/auth";

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard denied */
    }
  }, [text]);

  return (
    <button
      type="button"
      onClick={copy}
      className="shrink-0 rounded border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-600 hover:bg-slate-100"
    >
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function CommandRow({ command, description, notes }: RepoCommand) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <code className="block break-all rounded bg-slate-900 px-2 py-1.5 text-sm text-green-300">
            {command}
          </code>
          <p className="mt-2 text-sm text-slate-600">{description}</p>
          {notes && <p className="mt-1 text-xs text-amber-700">{notes}</p>}
        </div>
        <CopyButton text={command} />
      </div>
    </div>
  );
}

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

  const filteredCommandGroups = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return repoCommandGroups;

    return repoCommandGroups
      .map((group) => ({
        ...group,
        commands: group.commands.filter(
          (cmd) =>
            cmd.command.toLowerCase().includes(q) ||
            cmd.description.toLowerCase().includes(q) ||
            (cmd.notes?.toLowerCase().includes(q) ?? false) ||
            group.title.toLowerCase().includes(q),
        ),
      }))
      .filter((group) => group.commands.length > 0);
  }, [query]);

  const filteredLinkGroups = useMemo(() => {
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

  const totalLinks = allResourceLinks().length;
  const totalCommands = allRepoCommands().length;
  const visibleCommands = filteredCommandGroups.reduce((n, g) => n + g.commands.length, 0);
  const visibleLinks = filteredLinkGroups.reduce((n, g) => n + g.links.length, 0);
  const hasResults = visibleCommands > 0 || visibleLinks > 0;

  return (
    <DashboardShell>
      <div className="max-w-3xl">
        <h1 className="text-2xl font-semibold text-slate-900">My Tools</h1>
        <p className="mt-2 text-sm text-slate-600">
          Repo commands, local URLs, and demo docs — run commands from the project root. Signed in
          as {user?.firstName} {user?.lastName}.
        </p>

        <label className="mt-6 block text-sm">
          <span className="text-slate-700">Search commands & links</span>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. make dev, verify, e2e, swagger…"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </label>
        <p className="mt-2 text-xs text-slate-500">
          Showing {visibleCommands + visibleLinks} of {totalCommands + totalLinks} items (
          {totalCommands} commands · {totalLinks} links)
        </p>

        <div className="mt-8 space-y-10">
          {!hasResults && (
            <p className="text-sm text-slate-500">No commands or links match your search.</p>
          )}

          {filteredCommandGroups.map((group) => (
            <section key={group.id}>
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
                {group.title}
              </h2>
              {group.description && (
                <p className="mt-1 text-xs text-slate-500">{group.description}</p>
              )}
              <ul className="mt-3 space-y-3">
                {group.commands.map((cmd) => (
                  <li key={cmd.id}>
                    <CommandRow {...cmd} />
                  </li>
                ))}
              </ul>
            </section>
          ))}

          {filteredLinkGroups.length > 0 && (
            <div className="border-t border-slate-200 pt-8">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
                Links & URLs
              </h2>
              <div className="mt-6 space-y-10">
                {filteredLinkGroups.map((group) => (
                  <section key={group.id}>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                      {group.title}
                    </h3>
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
                ))}
              </div>
            </div>
          )}
        </div>

        <p className="mt-10 text-xs text-slate-400">
          Edit commands in{" "}
          <code className="rounded bg-slate-100 px-1">apps/web/src/content/repo-commands.ts</code>
          {" · "}
          Edit links in{" "}
          <code className="rounded bg-slate-100 px-1">apps/web/src/content/resource-links.ts</code>
        </p>
      </div>
    </DashboardShell>
  );
}
