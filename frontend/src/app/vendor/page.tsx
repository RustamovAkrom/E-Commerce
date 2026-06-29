"use client";
import type { Route } from "next";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { ErrorMessage } from "@/components/common/error-message";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { vendorsApi } from "@/lib/api/vendors";
import { productsApi } from "@/lib/api/products";
import type { VendorStatus } from "@/types/api";

const STATUS_LABEL: Record<VendorStatus, string> = {
  pending: "Ko‘rib chiqilmoqda",
  approved: "Tasdiqlangan",
  rejected: "Rad etilgan",
  suspended: "To‘xtatilgan",
};
const STATUS_VARIANT: Record<VendorStatus, "default" | "success" | "destructive" | "secondary"> = {
  pending: "secondary",
  approved: "success",
  rejected: "destructive",
  suspended: "destructive",
};

export default function VendorPage() {
  const vendor = useQuery({
    queryKey: ["vendor-me"],
    queryFn: vendorsApi.meOrNull,
  });
  const products = useQuery({
    queryKey: ["vendor-products-total", vendor.data?.id],
    queryFn: () => productsApi.list({ size: 1, page: 1, vendor_id: vendor.data!.id }),
    enabled: Boolean(vendor.data?.id),
  });

  if (vendor.isLoading) return <LoadingSpinner />;
  if (vendor.error)
    return (
      <ErrorMessage
        message={vendor.error.message}
        retry={() => void vendor.refetch()}
      />
    );

  if (!vendor.data) {
    return (
      <div className="space-y-4 animate-fade-in">
        <h1 className="text-2xl font-bold">Sotuvchi bo‘ling</h1>
        <Card>
          <CardContent className="space-y-4 p-6">
            <p className="text-muted-foreground">
              Siz hali do‘kon ochmagansiz. Marketplace’da mahsulot sotish uchun
              ariza qoldiring.
            </p>
            <Button asChild>
              <Link href={"/vendor/profile" as Route}>Do‘kon ochish</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const v = vendor.data;
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">{v.name}</h1>
        <Badge variant={STATUS_VARIANT[v.status]}>{STATUS_LABEL[v.status]}</Badge>
      </div>

      {v.status === "pending" && (
        <Card>
          <CardContent className="p-5 text-sm text-muted-foreground">
            Arizangiz ko‘rib chiqilmoqda. Tasdiqlangach mahsulotlaringiz
            marketplace’da ko‘rinadi.
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Mahsulotlarim</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-black">
            {products.data?.total ?? 0}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Komissiya</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-black">{v.commission_rate}%</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Holat</CardTitle>
          </CardHeader>
          <CardContent className="text-lg font-semibold">
            {v.is_active ? "Faol" : "Nofaol"}
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-wrap gap-3">
        <Button asChild>
          <Link href={"/vendor/products" as Route}>Mahsulotlarim</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href={"/vendor/profile" as Route}>Profilni tahrirlash</Link>
        </Button>
      </div>
    </div>
  );
}
