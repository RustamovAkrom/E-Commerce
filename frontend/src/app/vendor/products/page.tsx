"use client";
import type { Route } from "next";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { ErrorMessage } from "@/components/common/error-message";
import { EmptyState } from "@/components/common/empty-state";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { vendorsApi } from "@/lib/api/vendors";
import { productsApi } from "@/lib/api/products";
import { formatPrice } from "@/lib/utils";

export default function VendorProductsPage() {
  const vendor = useQuery({
    queryKey: ["vendor-me"],
    queryFn: vendorsApi.meOrNull,
  });
  const products = useQuery({
    queryKey: ["vendor-products", vendor.data?.id],
    queryFn: () => productsApi.list({ size: 50, page: 1, vendor_id: vendor.data!.id }),
    enabled: Boolean(vendor.data?.id),
  });

  if (vendor.isLoading) return <LoadingSpinner />;
  if (vendor.error)
    return (
      <ErrorMessage message={vendor.error.message} retry={() => void vendor.refetch()} />
    );

  if (!vendor.data)
    return (
      <EmptyState
        title="Avval do‘kon oching"
        action={
          <Button asChild>
            <Link href={"/vendor/profile" as Route}>Do‘kon ochish</Link>
          </Button>
        }
      />
    );

  return (
    <div className="space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold">Mahsulotlarim</h1>
      <p className="text-sm text-muted-foreground">
        Mahsulot qo‘shish uchun operator bilan bog‘laning — yangi mahsulotlar
        operator tomonidan katalogga kiritiladi.
      </p>

      {products.isLoading ? (
        <LoadingSpinner />
      ) : products.error ? (
        <ErrorMessage message={products.error.message} retry={() => void products.refetch()} />
      ) : !products.data?.items.length ? (
        <EmptyState title="Hozircha mahsulotlaringiz yo‘q" />
      ) : (
        <div className="space-y-3">
          {products.data.items.map((p) => (
            <Card key={p.id}>
              <CardContent className="flex items-center justify-between gap-3 p-4">
                <div>
                  <div className="flex items-center gap-2">
                    <strong>{p.name}</strong>
                    <Badge variant={p.is_active ? "success" : "destructive"}>
                      {p.is_active ? "Faol" : "Nofaol"}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {formatPrice(p.price, p.currency)} · {p.stock} dona
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
