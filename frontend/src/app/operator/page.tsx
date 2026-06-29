"use client";
import type { Route } from "next";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { ErrorMessage } from "@/components/common/error-message";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { productsApi } from "@/lib/api/products";

export default function OperatorPage() {
  const total = useQuery({
    queryKey: ["operator-products-total"],
    queryFn: () => productsApi.list({ size: 1, page: 1 }),
  });
  const active = useQuery({
    queryKey: ["operator-products-active"],
    queryFn: () => productsApi.list({ size: 1, page: 1, is_active: true }),
  });
  const categories = useQuery({
    queryKey: ["categories"],
    queryFn: productsApi.categories,
  });

  if (total.isLoading || active.isLoading || categories.isLoading)
    return <LoadingSpinner />;
  if (total.error)
    return (
      <ErrorMessage
        message={total.error.message}
        retry={() => void total.refetch()}
      />
    );

  const cards = [
    ["Jami mahsulotlar", total.data?.total ?? 0],
    ["Faol mahsulotlar", active.data?.total ?? 0],
    ["Kategoriyalar", categories.data?.length ?? 0],
  ] as const;

  return (
    <div className="space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold">Operator dashboard</h1>
      <p className="text-muted-foreground">
        Mahsulotlar va kategoriyalarni boshqaring.
      </p>

      <div className="grid gap-4 sm:grid-cols-3">
        {cards.map(([label, value], i) => (
          <Card key={label} className={`animate-scale-in animate-stagger-${i + 1}`}>
            <CardHeader>
              <CardTitle className="text-sm text-muted-foreground">{label}</CardTitle>
            </CardHeader>
            <CardContent className="text-3xl font-black">{value}</CardContent>
          </Card>
        ))}
      </div>

      <div className="flex flex-wrap gap-3">
        <Button asChild>
          <Link href={"/operator/products" as Route}>Mahsulot qo‘shish / tahrirlash</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href={"/operator/categories" as Route}>Kategoriyalarni boshqarish</Link>
        </Button>
      </div>
    </div>
  );
}
