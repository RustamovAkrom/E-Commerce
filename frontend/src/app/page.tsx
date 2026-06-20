"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, ShieldCheck, Truck, WalletCards } from "lucide-react";
import { ProductGrid } from "@/components/product/product-grid";
import { Button } from "@/components/ui/button";
import { productsApi } from "@/lib/api/products";
export default function HomePage() {
  const query = useQuery({
    queryKey: ["products", "featured"],
    queryFn: () =>
      productsApi.list({
        page: 1,
        size: 8,
        in_stock: true,
        sort: "-created_at",
      }),
  });
  return (
    <div>
      <section className="bg-gradient-to-br from-slate-950 via-blue-950 to-blue-700 text-white">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 py-16 md:grid-cols-2 md:py-24">
          <div className="space-y-6">
            <p className="text-sm font-semibold uppercase tracking-[.2em] text-blue-200">
              Yangi avlod savdosi
            </p>
            <h1 className="text-4xl font-black tracking-tight sm:text-5xl lg:text-6xl">
              Kerakli mahsulotlar, qulay xarid
            </h1>
            <p className="max-w-xl text-blue-100">
              Tanlang, xavfsiz to‘lang va buyurtmangizni kuzating.
            </p>
            <Button asChild size="lg" variant="secondary">
              <Link href="/products">
                Xaridni boshlash <ArrowRight className="size-4" />
              </Link>
            </Button>
          </div>
          <div className="grid grid-cols-1 gap-3 self-end sm:grid-cols-3 md:grid-cols-1 lg:grid-cols-3">
            {[
              [Truck, "Tez yetkazish"],
              [ShieldCheck, "Xavfsiz xarid"],
              [WalletCards, "Qulay to‘lov"],
            ].map(([Icon, label]) => (
              <div
                key={label as string}
                className="rounded-2xl border border-white/20 bg-white/10 p-4 backdrop-blur"
              >
                <Icon className="mb-3 size-6" />
                <p className="font-semibold">{label as string}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
      <section className="mx-auto max-w-7xl space-y-6 px-4 py-12">
        <div className="flex items-end justify-between">
          <div>
            <p className="text-sm font-semibold text-primary">Tanlanganlar</p>
            <h2 className="text-2xl font-bold sm:text-3xl">
              Yangi mahsulotlar
            </h2>
          </div>
          <Link href="/products" className="text-sm font-semibold text-primary">
            Barchasi
          </Link>
        </div>
        <ProductGrid
          products={query.data?.items}
          loading={query.isLoading}
          error={query.error?.message}
          retry={() => void query.refetch()}
        />
      </section>
    </div>
  );
}
