"use client";
import { useQuery } from "@tanstack/react-query";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { adminApi } from "@/lib/api/admin";
import { formatPrice } from "@/lib/utils";
export default function AdminPage() {
  const query = useQuery({ queryKey: ["admin-dashboard"], queryFn: adminApi.dashboard });
  if (query.isLoading) return <LoadingSpinner />;
  if (query.error) return <ErrorMessage message={query.error.message} retry={() => void query.refetch()} />;
  if (!query.data) return <EmptyState title="Statistika topilmadi" />;
  const stats = query.data;
  const cards = [
    ["Foydalanuvchilar", stats.total_users],
    ["Mahsulotlar", stats.total_products],
    ["Buyurtmalar", stats.total_orders],
    ["Tushum", formatPrice(stats.total_revenue)],
    ["Kutilayotgan", stats.pending_orders],
    ["Kam qolgan", stats.low_stock_products],
  ];
  return (
    <div className="animate-fade-in">
      <h1 className="mb-6 text-2xl font-bold">Dashboard</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map(([label, value], i) => (
          <Card key={label} className={`animate-scale-in animate-stagger-${Math.min(i + 1, 6)}`}>
            <CardHeader>
              <CardTitle className="text-sm text-muted-foreground">{label}</CardTitle>
            </CardHeader>
            <CardContent className="text-2xl font-black">{value}</CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
