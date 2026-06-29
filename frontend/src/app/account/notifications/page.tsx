"use client";
import { useQuery } from "@tanstack/react-query";
import { Bell, CheckCheck, Package, AlertCircle, ShoppingBag } from "lucide-react";
import { EmptyState } from "@/components/common/empty-state";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { notificationsApi } from "@/lib/api/notifications";
import type { Notification } from "@/lib/api/notifications";
import { useAuthStore } from "@/lib/stores/auth.store";

const typeIcons: Record<string, typeof Bell> = {
  order: Package,
  payment: ShoppingBag,
  shipping: Package,
  system: AlertCircle,
  generic: Bell,
};

const typeLabels: Record<string, string> = {
  order: "Buyurtma",
  payment: "To'lov",
  shipping: "Yetkazuv",
  system: "Tizim",
  generic: "Xabar",
};

const statusColors: Record<string, string> = {
  sent: "bg-green-100 text-green-800",
  pending: "bg-yellow-100 text-yellow-800",
  failed: "bg-red-100 text-red-800",
};

function formatRelative(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Hozir";
  if (mins < 60) return `${mins} daq oldin`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} soat oldin`;
  const days = Math.floor(hrs / 24);
  return `${days} kun oldin`;
}

export default function NotificationsPage() {
  // Wait until the session is restored (token rehydrated after a reload) before
  // querying — otherwise the request fires unauthenticated and 401s.
  const initialized = useAuthStore((s) => s.initialized);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => notificationsApi.list(),
    enabled: initialized && isAuthenticated,
  });

  if (!initialized || isLoading) return <LoadingSpinner />;
  if (error)
    return (
      <EmptyState
        title="Xatolik"
        description={error.message}
        action={<Button onClick={() => void refetch()}>Qayta urinish</Button>}
      />
    );

  const items = data?.items ?? [];

  return (
    <div className="mx-auto max-w-3xl space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Bildirishnomalar</h1>
        {items.length > 0 && (
          <p className="text-sm text-muted-foreground">
            {items.length} ta yangi xabar
          </p>
        )}
      </div>

      {items.length === 0 ? (
        <EmptyState title="Yangi bildirishnomalar yo'q" description="Bu yerda buyurtma va tizim xabarlari ko'rinadi." />
      ) : (
        <Card>
          <CardContent className="p-0">
            {items.map((n: Notification) => {
              const Icon = typeIcons[n.type] ?? Bell;
              return (
                <div
                  key={n.id}
                  className="flex items-start gap-4 border-b last:border-b-0 p-4"
                >
                  <div
                    className={`mt-1 flex size-10 shrink-0 items-center justify-center rounded-full ${
                      n.status === "sent"
                        ? "bg-green-100"
                        : n.status === "failed"
                          ? "bg-red-100"
                          : "bg-yellow-100"
                    }`}
                  >
                    <Icon className="size-5 text-muted-foreground" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">
                        {typeLabels[n.type] ?? n.type}
                      </span>
                      <Badge
                        variant="outline"
                        className={statusColors[n.status] ?? ""}
                      >
                        {n.status}
                      </Badge>
                    </div>
                    {n.subject && (
                      <p className="text-sm font-medium">{n.subject}</p>
                    )}
                    <p className="text-sm text-muted-foreground">{n.body}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatRelative(n.created_at)}
                    </p>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
