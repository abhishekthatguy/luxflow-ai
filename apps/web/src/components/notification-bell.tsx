"use client";

import type { NotificationItem } from "@lexflow/shared";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { apiFetch, apiFetchList } from "@/lib/auth";

const PRIORITY_STYLES: Record<string, string> = {
  urgent: "bg-red-100 text-red-800",
  high: "bg-orange-100 text-orange-800",
  critical: "bg-red-100 text-red-800",
  normal: "bg-slate-100 text-slate-700",
};

function formatRolePriority(priority?: string | null): string {
  if (!priority) return "Normal";
  return priority.charAt(0).toUpperCase() + priority.slice(1);
}

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [count, setCount] = useState(0);
  const [items, setItems] = useState<NotificationItem[]>([]);

  const refresh = useCallback(async () => {
    try {
      const data = await apiFetch<{ count: number }>("/api/v1/notifications/unread-count");
      setCount(data.count);
    } catch {
      /* ignore polling errors */
    }
  }, []);

  const loadItems = useCallback(async () => {
    const { items: list } = await apiFetchList<NotificationItem>(
      "/api/v1/notifications?pageSize=15&unreadOnly=true",
    );
    setItems(list);
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 30000);
    return () => clearInterval(id);
  }, [refresh]);

  useEffect(() => {
    if (open) loadItems().catch(() => setItems([]));
  }, [open, loadItems]);

  const markRead = async (id: string) => {
    await apiFetch(`/api/v1/notifications/${id}/read`, { method: "POST" });
    await refresh();
    await loadItems();
  };

  return (
    <div className="relative">
      <button
        type="button"
        aria-label="Notifications"
        className="relative rounded-md p-2 text-slate-600 hover:bg-white/60"
        onClick={() => setOpen((v) => !v)}
      >
        🔔
        {count > 0 && (
          <span className="absolute right-0 top-0 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] text-white">
            {count > 9 ? "9+" : count}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-40 mt-1 w-96 rounded-md border bg-white shadow-lg">
          <div className="border-b px-3 py-2 text-xs font-medium text-slate-500">
            Notification Center
          </div>
          {items.length === 0 ? (
            <p className="px-3 py-4 text-sm text-slate-500">No unread notifications</p>
          ) : (
            <ul className="max-h-96 overflow-y-auto">
              {items.map((n) => (
                <li key={n.id} className="border-b border-slate-100 px-3 py-3 text-sm">
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-medium text-slate-900">{n.title}</p>
                    {n.priority && (
                      <span
                        className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${PRIORITY_STYLES[n.priority] ?? PRIORITY_STYLES.normal}`}
                      >
                        {formatRolePriority(n.priority)}
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-slate-600">{n.description ?? n.body}</p>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                    {n.workflowSlug && <span className="font-mono">{n.workflowSlug}</span>}
                    {n.eventType && <span>{n.eventType}</span>}
                    <span>{new Date(n.createdAt).toLocaleString()}</span>
                  </div>
                  <div className="mt-2 flex gap-2">
                    {(n.actionUrl || n.caseId) && (
                      <Link
                        href={n.actionUrl || `/cases/${n.caseId}/overview`}
                        className="text-xs font-medium text-blue-700 hover:underline"
                        onClick={() => setOpen(false)}
                      >
                        Open case
                      </Link>
                    )}
                    <button
                      type="button"
                      className="text-xs text-slate-500 hover:text-slate-800"
                      onClick={() => markRead(n.id)}
                    >
                      Mark read
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
