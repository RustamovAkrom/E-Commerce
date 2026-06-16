import { fetchJson } from "@/lib/api/client";
import type { DashboardStats } from "@/types/api";
export const adminApi = { dashboard: () => fetchJson<DashboardStats>("/admin/dashboard") };
