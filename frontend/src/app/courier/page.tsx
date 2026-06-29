"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MapPin, Navigation, Phone, Package, Wallet } from "lucide-react";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { courierApi } from "@/lib/api/courier";
import { formatDate, formatPrice } from "@/lib/utils";
import { toast } from "sonner";
import type { CourierDelivery } from "@/types/api";

const STATUS_LABEL: Record<string, string> = {
  pending: "Yangi — olishni kuting",
  picked_up: "Olingan — yetkazilmoqda",
};

/** Build a full, geocodable address string from the delivery snapshot. */
function fullAddress(d: CourierDelivery): string {
  return [d.address, d.city, d.country].filter(Boolean).join(", ");
}

export default function CourierDeliveriesPage() {
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["courier-deliveries"],
    queryFn: courierApi.myDeliveries,
    refetchInterval: 30000, // new assignments may arrive while on shift
  });
  const invalidate = () =>
    client.invalidateQueries({ queryKey: ["courier-deliveries"] });
  const pickup = useMutation({
    mutationFn: (id: string) => courierApi.pickup(id),
    onSuccess: () => {
      void invalidate();
      toast.success("Yetkazuv olindi");
    },
  });
  const delivered = useMutation({
    mutationFn: (id: string) => courierApi.delivered(id),
    onSuccess: () => {
      void invalidate();
      toast.success("Yetkazildi deb belgilandi");
    },
  });

  if (query.isLoading) return <LoadingSpinner />;
  if (query.error)
    return (
      <ErrorMessage message={query.error.message} retry={() => void query.refetch()} />
    );

  const items = query.data ?? [];

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Mening yetkazuvlarim</h1>
        <Badge variant="secondary" className="px-3 py-1">
          {items.length} faol
        </Badge>
      </div>
      {(pickup.error || delivered.error) && (
        <ErrorMessage message={(pickup.error ?? delivered.error)!.message} />
      )}

      {items.length === 0 && (
        <EmptyState
          title="Faol yetkazuvlar yo‘q"
          description="Sizga buyurtma biriktirilganda shu yerda ko‘rinadi."
        />
      )}

      {items.map((d) => {
        const addr = fullAddress(d);
        const mapsQuery = encodeURIComponent(addr);
        return (
          <Card key={d.id}>
            <CardContent className="space-y-4 p-5">
              {/* Header: order + status */}
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2 font-semibold">
                  <Package className="size-4 text-muted-foreground" />
                  Buyurtma #{d.order_id.slice(0, 8)}
                </div>
                <Badge variant={d.status === "picked_up" ? "default" : "secondary"}>
                  {STATUS_LABEL[d.status] ?? d.status}
                </Badge>
              </div>

              {/* Destination address */}
              <div className="flex items-start gap-2 text-sm">
                <MapPin className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                <div>
                  <p className="font-medium">{d.customer_name}</p>
                  <p className="text-muted-foreground">{addr || "Manzil ko‘rsatilmagan"}</p>
                  {d.postal_code && (
                    <p className="text-xs text-muted-foreground">Indeks: {d.postal_code}</p>
                  )}
                </div>
              </div>

              {/* Amount + date */}
              <div className="flex flex-wrap items-center gap-4 text-sm">
                <span className="inline-flex items-center gap-1 font-semibold">
                  <Wallet className="size-4 text-muted-foreground" />
                  {formatPrice(d.total_amount, d.currency)}
                </span>
                <span className="text-muted-foreground">{formatDate(d.created_at)}</span>
              </div>

              {/* Navigation + contact: deep-link to map apps and phone dialer */}
              <div className="flex flex-wrap gap-2">
                {addr && (
                  <>
                    <Button asChild size="sm" variant="outline">
                      <a
                        href={`https://yandex.com/maps/?text=${mapsQuery}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Navigation className="mr-1 size-4" />
                        Yandex Xarita
                      </a>
                    </Button>
                    <Button asChild size="sm" variant="outline">
                      <a
                        href={`https://www.google.com/maps/search/?api=1&query=${mapsQuery}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <MapPin className="mr-1 size-4" />
                        Google Xarita
                      </a>
                    </Button>
                  </>
                )}
                {d.phone && (
                  <Button asChild size="sm" variant="outline">
                    <a href={`tel:${d.phone}`}>
                      <Phone className="mr-1 size-4" />
                      Qo‘ng‘iroq
                    </a>
                  </Button>
                )}
              </div>

              {/* State transition actions */}
              <div className="flex gap-2 border-t pt-3">
                {d.status === "pending" && (
                  <Button
                    size="sm"
                    disabled={pickup.isPending}
                    onClick={() => pickup.mutate(d.id)}
                  >
                    Yetkazuvni olish
                  </Button>
                )}
                {d.status === "picked_up" && (
                  <Button
                    size="sm"
                    disabled={delivered.isPending}
                    onClick={() => delivered.mutate(d.id)}
                  >
                    Yetkazildi
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
