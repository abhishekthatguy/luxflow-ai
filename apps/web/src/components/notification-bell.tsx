"use client";

import type { NotificationItem } from "@lexflow/shared";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { apiFetch, apiFetchList } from "@/lib/auth";

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
      "/api/v1/notifications?pageSize=10&unreadOnly=true",
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
        <div className="absolute right-0 z-40 mt-1 w-80 rounded-md border bg-white shadow-lg">
          <div className="border-b px-3 py-2 text-xs font-medium text-slate-500">Notifications</div>
          {items.length === 0 ? (
            <p className="px-3 py-4 text-sm text-slate-500">No unread notifications</p>
          ) : (
            <ul className="max-h-72 overflow-y-auto">
              {items.map((n) => (
                <li key={n.id} className="border-b border-slate-100 px-3 py-2 text-sm">
                  <p className="font-medium">{n.title}</p>
                  <p className="text-slate-600">{n.body}</p>
                  <div className="mt-1 flex gap-2">
                    {n.caseId && (
                      <Link
                        href={`/cases/${n.caseId}/overview`}
                        className="text-xs text-blue-700 hover:underline"
                        onClick={() => setOpen(false)}
                      >
                        View case
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
