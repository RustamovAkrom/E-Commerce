"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { adminApi } from "@/lib/api/admin";
import { formatDate, formatPrice } from "@/lib/utils";
import { toast } from "sonner";

export default function MyDeliveriesPage() {
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["my-deliveries"],
    queryFn: adminApi.myDeliveries,
  });
  const pickup = useMutation({
    mutationFn: (id: string) => adminApi.pickupDelivery(id),
    onSuccess: () => void client.invalidateQueries({ queryKey: ["my-deliveries"] }),
  });
  const delivered = useMutation({
    mutationFn: (id: string) => adminApi.markDelivered(id),
    onSuccess: () => void client.invalidateQueries({ queryKey: ["my-deliveries"] }),
  });

  if (query.isLoading) return <LoadingSpinner />;
  if (query.error)
    return (
      <ErrorMessage message={query.error.message} retry={() => void query.refetch()} />
    );

  const items = query.data ?? [];

  return (
    <div className="mx-auto max-w-3xl space-y-4 py-10 animate-fade-in">
      <h1 className="text-2xl font-bold">Mening yetkazuvlarim</h1>
      {pickup.error && <ErrorMessage message={pickup.error.message} />}
      {delivered.error && <ErrorMessage message={delivered.error.message} />}

      {items.length === 0 && (
        <EmptyState title="Kutilayotgan yetkazuvlar yo‘q" />
      )}

      {items.map((d) => (
        <Card key={d.id}>
          <CardContent className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="font-semibold">Buyurtma #{d.order_id.slice(0, 8)}</p>
              <p className="text-sm text-muted-foreground">
                {formatDate(d.created_at)}
              </p>
              <Badge variant={d.status === "picked_up" ? "default" : "secondary"}>
                {d.status}
              </Badge>
            </div>
            <div className="flex gap-2">
              {d.status !== "picked_up" && (
                <Button
                  size="sm"
                  disabled={pickup.isPending}
                  onClick={() => {
                    pickup.mutate(d.id);
                    toast.success("Yetkazuv olish tasdiqlandi");
                  }}
                >
                  Olish
                </Button>
              )}
              {d.status === "picked_up" && (
                <Button
                  size="sm"
                  variant="default"
                  disabled={delivered.isPending}
                  onClick={() => {
                    delivered.mutate(d.id);
                    toast.success("Yetkazildi deb belgilandi");
                  }}
                >
                  Yetkazildi
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
