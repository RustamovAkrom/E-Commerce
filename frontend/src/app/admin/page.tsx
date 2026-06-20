"use client";
import { useQuery } from "@tanstack/react-query";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { adminApi } from "@/lib/api/admin";
import { formatPrice } from "@/lib/utils";
import Link from "next/link";

export default function AdminPage() {
  const dashboard = useQuery({
    queryKey: ["admin-dashboard"],
    queryFn: adminApi.dashboard,
  });
  const sales = useQuery({
    queryKey: ["sales-overview"],
    queryFn: () => adminApi.salesOverview(30),
  });
  const breakdown = useQuery({
    queryKey: ["order-status-breakdown"],
    queryFn: () => adminApi.orderStatusBreakdown(),
  });

  if (dashboard.isLoading || sales.isLoading || breakdown.isLoading)
    return <LoadingSpinner />;
  if (dashboard.error)
    return (
      <ErrorMessage
        message={dashboard.error.message}
        retry={() => void dashboard.refetch()}
      />
    );
  if (!dashboard.data) return <EmptyState title="Statistika topilmadi" />;

  const stats = dashboard.data;
  const cards = [
    ["Foydalanuvchilar", stats.total_users, "/admin"],
    ["Mahsulotlar", stats.total_products, "/admin"],
    ["Buyurtmalar", stats.total_orders, "/admin/orders"],
    ["Tushum", formatPrice(stats.total_revenue), "/admin"],
    ["Kutilayotgan", stats.pending_orders, "/admin"],
    ["Kam qolgan", stats.low_stock_products, "/admin"],
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map(([label, value], i) => (
          <Card
            key={label}
            className={`animate-scale-in animate-stagger-${Math.min(i + 1, 6)}`}
          >
            <CardHeader>
              <CardTitle className="text-sm text-muted-foreground">
                {label}
              </CardTitle>
            </CardHeader>
            <CardContent className="text-2xl font-black">{value}</CardContent>
          </Card>
        ))}
      </div>

      {breakdown.data && breakdown.data.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Buyurtmalar holat bo‘yicha</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {breakdown.data.map((b) => (
                <Badge key={b.status} variant="secondary" className="px-3 py-1">
                  {b.status}: {b.count}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {sales.data && sales.data.points.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Savdo ko‘rsatkichlari ({sales.data.period_days} kun)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end gap-1 h-40">
              {sales.data.points.map((p, i) => {
                const maxRev = Math.max(
                  ...sales.data!.points.map((pp) => Number(pp.revenue)),
                  1,
                );
                const heightPct = (Number(p.revenue) / maxRev) * 100;
                return (
                  <div
                    key={i}
                    className="flex-1 rounded-t bg-primary/20 hover:bg-primary/40 transition-colors relative group"
                    style={{ height: `${Math.max(heightPct, 4)}%` }}
                  >
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block whitespace-nowrap rounded bg-popover px-2 py-1 text-xs shadow">
                      {p.date}: {formatPrice(p.revenue)}
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Jami tushum: </span>
                <strong>{formatPrice(sales.data.total_revenue)}</strong>
              </div>
              <div>
                <span className="text-muted-foreground">Buyurtmalar: </span>
                <strong>{sales.data.order_count}</strong>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
