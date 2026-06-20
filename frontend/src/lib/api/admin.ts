import { fetchJson, toQuery } from "@/lib/api/client";
import type {
  Courier,
  CourierCreate,
  CourierUpdate,
  DashboardStats,
  DeliveryAssignment,
  OrderStatusBreakdown,
  Page,
  SalesOverview,
  User,
  VendorResponse,
  VendorAdminUpdateRequest,
  VendorUpdateRequest,
} from "@/types/api";

export const adminApi = {
  dashboard: () => fetchJson<DashboardStats>("/admin/dashboard"),
  orderStatusBreakdown: () =>
    fetchJson<OrderStatusBreakdown[]>("/admin/orders/status-breakdown"),
  salesOverview: (days = 30) =>
    fetchJson<SalesOverview>(`/admin/sales/overview${toQuery({ days })}`),

  // Users
  users: (query: { page?: number; size?: number } = {}) =>
    fetchJson<Page<User>>(`/users${toQuery(query)}`),

  // Vendors
  vendors: (query: { page?: number; size?: number } = {}) =>
    fetchJson<Page<VendorResponse>>(`/vendors/admin/all${toQuery(query)}`),
  updateVendor: (id: string, data: VendorAdminUpdateRequest) =>
    fetchJson<VendorResponse>(`/vendors/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteVendor: (id: string) =>
    fetchJson<{ message: string }>(`/vendors/${id}`, { method: "DELETE" }),

  // Couriers
  couriers: (query: { page?: number; size?: number } = {}) =>
    fetchJson<Page<Courier>>(`/delivery/couriers${toQuery(query)}`),
  createCourier: (data: CourierCreate) =>
    fetchJson<Courier>("/delivery/couriers", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateCourier: (id: string, data: CourierUpdate) =>
    fetchJson<Courier>(`/delivery/couriers/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  // Delivery
  myDeliveries: () =>
    fetchJson<DeliveryAssignment[]>("/delivery/courier/my-deliveries"),
  pickupDelivery: (assignmentId: string) =>
    fetchJson<DeliveryAssignment>(
      `/delivery/courier/${assignmentId}/pickup`,
      { method: "POST" },
    ),
  markDelivered: (assignmentId: string) =>
    fetchJson<DeliveryAssignment>(
      `/delivery/courier/${assignmentId}/delivered`,
      { method: "POST" },
    ),
};
