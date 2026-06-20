"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ordersApi } from "@/lib/api/orders";
import { formatDate, formatPrice } from "@/lib/utils";
import type { OrderStatus } from "@/types/api";
const statuses: OrderStatus[] = [
  "pending", "confirmed", "paid", "processing", "shipped", "delivered", "cancelled", "refunded",
];
const statusLabels: Record<OrderStatus, string> = {
  pending: "Kutilmoqda",
  confirmed: "Tasdiqlandi",
  paid: "To‘landi",
  processing: "Jarayonda",
  shipped: "Jo‘natildi",
  delivered: "Yetkazildi",
  cancelled: "Bekor qilindi",
  refunded: "Qaytarildi",
};
export default function AdminOrdersPage() {
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["admin-orders"],
    queryFn: () => ordersApi.adminList({ size: 100 }),
  });
  const update = useMutation({
    mutationFn: ({ id, status }: { id: string; status: OrderStatus }) =>
      ordersApi.updateStatus(id, status),
    onSuccess: () => void client.invalidateQueries({ queryKey: ["admin-orders"] }),
  });
  if (query.isLoading) return <LoadingSpinner />;
  if (query.error)
    return (
      <ErrorMessage message={query.error.message} retry={() => void query.refetch()} />
    );
  if (!query.data?.items.length) return <EmptyState title="Buyurtmalar yo‘q" />;
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Buyurtmalar boshqaruvi</h1>
      {update.error && <ErrorMessage message={update.error.message} />}
      {query.data.items.map((order) => (
        <Card key={order.id}>
          <CardContent className="grid gap-3 p-4 sm:grid-cols-4 sm:items-center">
            <div>
              <strong>#{order.id.slice(0, 8)}</strong>
              <p className="text-xs text-muted-foreground">
                {formatDate(order.created_at)}
              </p>
              {order.shipping_address && (
                <p className="text-xs text-muted-foreground">
                  {order.shipping_address.full_name}, {order.shipping_address.city}
                </p>
              )}
            </div>
            <Badge
              variant={
                order.status === "delivered" ? "success" :
                order.status === "cancelled" ? "destructive" :
                order.status === "paid" ? "default" : "secondary"
              }
            >
              {statusLabels[order.status] ?? order.status}
            </Badge>
            <strong>{formatPrice(order.total_amount, order.currency)}</strong>
            <select
              aria-label="Statusni o‘zgartirish"
              className="h-10 rounded-xl border bg-background px-2"
              value={order.status}
              disabled={update.isPending}
              onChange={(e) =>
                update.mutate({
                  id: order.id,
                  status: e.target.value as OrderStatus,
                })
              }
            >
              {statuses.map((status) => (
                <option key={status} value={status}>
                  {statusLabels[status] ?? status}
                </option>
              ))}
            </select>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
