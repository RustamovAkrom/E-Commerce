import { fetchJson, toQuery } from "@/lib/api/client";
import type { Order, OrderCreate, OrderDetail, OrderStatus, Page, PaginationQuery } from "@/types/api";
export const ordersApi = {
  create: (data: OrderCreate) => fetchJson<OrderDetail>("/orders", { method: "POST", body: JSON.stringify(data) }),
  list: (query: PaginationQuery = {}) => fetchJson<Page<Order>>(`/orders${toQuery(query)}`),
  detail: (id: string) => fetchJson<OrderDetail>(`/orders/${id}`),
  cancel: (id: string) => fetchJson<OrderDetail>(`/orders/${id}/cancel`, { method: "POST" }),
  adminList: (query: PaginationQuery = {}) => fetchJson<Page<Order>>(`/orders/admin/all${toQuery(query)}`),
  updateStatus: (id: string, status: OrderStatus) => fetchJson<OrderDetail>(`/orders/admin/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) }),
};
