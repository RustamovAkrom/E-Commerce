"use client";
import { useQuery } from "@tanstack/react-query";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ordersApi } from "@/lib/api/orders";
import { formatDate, formatPrice } from "@/lib/utils";
export default function OrdersPage() {
  const query = useQuery({
    queryKey: ["orders"],
    queryFn: () => ordersApi.list({ size: 50 }),
  });
  if (query.isLoading) return <LoadingSpinner />;
  if (query.error)
    return (
      <ErrorMessage
        message={query.error.message}
        retry={() => void query.refetch()}
      />
    );
  if (!query.data?.items.length)
    return (
      <EmptyState
        title="Buyurtmalar yo‘q"
        description="Birinchi buyurtmangiz bu yerda ko‘rinadi."
      />
    );
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Buyurtmalar</h1>
      {query.data.items.map((order) => (
        <Card key={order.id}>
          <CardContent className="flex flex-col justify-between gap-3 p-5 sm:flex-row sm:items-center">
            <div>
              <p className="font-semibold">#{order.id.slice(0, 8)}</p>
              <p className="text-sm text-muted-foreground">
                {formatDate(order.created_at)}
              </p>
            </div>
            <Badge
              variant={
                order.status === "delivered"
                  ? "success"
                  : order.status === "cancelled"
                    ? "destructive"
                    : "secondary"
              }
            >
              {order.status}
            </Badge>
            <strong>{formatPrice(order.total_amount, order.currency)}</strong>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
