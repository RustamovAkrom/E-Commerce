import { fetchJson } from "@/lib/api/client";
import type { CourierDelivery, DeliveryAssignment } from "@/types/api";

/** Courier self-service: own active deliveries and their state transitions. */
export const courierApi = {
  myDeliveries: () =>
    fetchJson<CourierDelivery[]>("/delivery/courier/my-deliveries"),
  pickup: (assignmentId: string) =>
    fetchJson<DeliveryAssignment>(`/delivery/courier/${assignmentId}/pickup`, {
      method: "POST",
    }),
  delivered: (assignmentId: string) =>
    fetchJson<DeliveryAssignment>(
      `/delivery/courier/${assignmentId}/delivered`,
      { method: "POST" },
    ),
};
