"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Pagination } from "@/components/common/pagination";
import { ProductFilters } from "@/components/product/product-filters";
import { ProductGrid } from "@/components/product/product-grid";
import { productsApi } from "@/lib/api/products";
import type { ProductQuery } from "@/types/api";
export default function ProductsPage() { const [filters, setFilters] = useState<ProductQuery>({ page: 1, size: 12, sort: "-created_at" }); const products = useQuery({ queryKey: ["products", filters], queryFn: () => productsApi.list(filters) }); const categories = useQuery({ queryKey: ["categories"], queryFn: productsApi.categories }); return <div className="mx-auto max-w-7xl space-y-6 px-4 py-10 animate-slide-up"><div><h1 className="text-3xl font-bold">Mahsulotlar</h1><p className="text-muted-foreground">Katalogdan kerakli mahsulotni toping.</p></div><ProductFilters value={filters} categories={categories.data ?? []} onChange={setFilters} />{categories.error && <p className="text-sm text-destructive">Kategoriyalar yuklanmadi: {categories.error.message}</p>}<ProductGrid products={products.data?.items} loading={products.isLoading} error={products.error?.message} retry={() => void products.refetch()} /><Pagination page={products.data?.page ?? 1} pages={products.data?.pages ?? 0} onChange={(page) => setFilters((current) => ({ ...current, page }))} /></div>; }
