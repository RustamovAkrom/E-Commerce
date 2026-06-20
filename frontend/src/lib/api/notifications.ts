import { fetchJson } from "@/lib/api/client";
import { toQuery } from "@/lib/api/client";
import type { Page, PaginationQuery } from "@/types/api";

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  channel: string;
  status: string;
  destination: string;
  subject: string | null;
  body: string;
  error: string | null;
  created_at: string;
}

export const notificationsApi = {
  list: (params?: PaginationQuery) =>
    fetchJson<Page<Notification>>(
      `/notifications${toQuery(params ?? {})}`,
      { auth: true },
    ),
  markRead: (id: string) =>
    fetchJson<Notification>(`/notifications/${id}/read`, {
      method: "PATCH",
      auth: true,
    }),
  markAllRead: () =>
    fetchJson<{ message: string }>("/notifications/read-all", {
      method: "POST",
      auth: true,
    }),
};
