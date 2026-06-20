"use client";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { productsApi } from "@/lib/api/products";
import { formatPrice } from "@/lib/utils";
import { toast } from "sonner";
import type { Product, ProductWrite } from "@/types/api";

const productSchema = z.object({
  category_id: z.string().min(1, "Kategoriya tanlang"),
  name: z.string().min(1, "Nomi kiriting"),
  slug: z.string().min(1, "Slug kiriting"),
  description: z.string().optional(),
  sku: z.string().optional(),
  price: z.number().positive("Narx musbat bo‘lishi kerak"),
  stock: z.number().int().nonnegative("Qoldiq manfiy bo‘lmasligi kerak"),
  is_active: z.boolean(),
});
type ProductFormData = z.infer<typeof productSchema>;

export default function AdminProductsPage() {
  const client = useQueryClient();
  const [editing, setEditing] = useState<Product | null>(null);
  const [search, setSearch] = useState("");
  const products = useQuery({
    queryKey: ["admin-products", search],
    queryFn: () => productsApi.list({ size: 50, search, page: 1 }),
  });
  const categories = useQuery({
    queryKey: ["categories"],
    queryFn: productsApi.categories,
  });
  const form = useForm<ProductFormData>({
    resolver: zodResolver(productSchema),
    defaultValues: { stock: 0, is_active: true },
  });
  const refresh = () =>
    client.invalidateQueries({ queryKey: ["admin-products"] });
  const save = useMutation({
    mutationFn: (data: ProductWrite) =>
      editing ? productsApi.update(editing.id, data) : productsApi.create(data),
    onSuccess: () => {
      setEditing(null);
      form.reset({
        stock: 0,
        is_active: true,
        name: "",
        slug: "",
        description: "",
        sku: "",
        price: 0,
      });
      void refresh();
      toast.success(editing ? "Mahsulot yangilandi" : "Mahsulot yaratildi");
    },
  });
  const remove = useMutation({
    mutationFn: productsApi.remove,
    onSuccess: () => {
      void refresh();
      toast.success("O‘chirildi");
    },
  });
  if (products.isLoading || categories.isLoading) return <LoadingSpinner />;
  if (products.error || categories.error)
    return (
      <ErrorMessage
        message={(products.error ?? categories.error)?.message ?? "Xatolik"}
        retry={() => void products.refetch()}
      />
    );
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold">Mahsulotlar boshqaruvi</h1>
        <Input
          placeholder="Qidirish..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-xs"
        />
      </div>
      <div className="grid gap-6 xl:grid-cols-[1fr_420px]">
        <div>
          {!products.data?.items.length ? (
            <EmptyState title="Mahsulotlar topilmadi" />
          ) : (
            <div className="space-y-3">
              {products.data.items.map((product) => (
                <Card key={product.id}>
                  <CardContent className="flex flex-col justify-between gap-3 p-4 sm:flex-row sm:items-center">
                    <div>
                      <div className="flex items-center gap-2">
                        <strong>{product.name}</strong>
                        <Badge
                          variant={product.is_active ? "success" : "destructive"}
                        >
                          {product.is_active ? "Faol" : "Nofaol"}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {formatPrice(product.price, product.currency)} ·{" "}
                        {product.stock} dona · SKU: {product.sku ?? "—"}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setEditing(product);
                          form.reset({
                            category_id: product.category_id,
                            name: product.name,
                            slug: product.slug,
                            description: product.description ?? "",
                            sku: product.sku ?? "",
                            price: Number(product.price),
                            stock: product.stock,
                            is_active: product.is_active,
                          });
                        }}
                      >
                        Tahrirlash
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        disabled={remove.isPending}
                        onClick={() => remove.mutate(product.id)}
                      >
                        O‘chirish
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
        <Card>
          <CardHeader>
            <CardTitle>
              {editing ? "Mahsulotni tahrirlash" : "Yangi mahsulot"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="space-y-3"
              onSubmit={form.handleSubmit((data) => save.mutate(data))}
            >
              {save.error && <ErrorMessage message={save.error.message} />}
              <select
                className="h-11 w-full rounded-xl border px-3"
                {...form.register("category_id")}
              >
                <option value="">Kategoriya</option>
                {categories.data?.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
              {form.formState.errors.category_id && (
                <p className="text-sm text-destructive">{form.formState.errors.category_id.message}</p>
              )}
              {[
                ["name", "Nomi", "text"],
                ["slug", "Slug", "text"],
                ["sku", "SKU", "text"],
                ["price", "Narx", "number"],
                ["stock", "Qoldiq", "number"],
              ].map(([name, label, type]) => (
                <label key={name} className="block text-sm font-medium">
                  {label}
                  <Input
                    type={type}
                    step={name === "price" ? "0.01" : undefined}
                    {...form.register(
                      name as keyof ProductFormData,
                      type === "number" ? { valueAsNumber: true } : undefined,
                    )}
                  />
                </label>
              ))}
              <label className="block text-sm font-medium">
                Valyuta
                <Input value="UZS" disabled />
              </label>
              {form.formState.errors.price && (
                <p className="text-sm text-destructive">{form.formState.errors.price.message}</p>
              )}
              <label className="block text-sm font-medium">
                Tavsif
                <textarea
                  className="min-h-24 w-full rounded-xl border bg-background p-3"
                  {...form.register("description")}
                />
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  {...form.register("is_active")}
                />
                Faol
              </label>
              <div className="flex gap-2">
                <Button disabled={save.isPending}>
                  {save.isPending ? "Saqlanmoqda..." : "Saqlash"}
                </Button>
                {editing && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setEditing(null);
                      form.reset();
                    }}
                  >
                    Bekor qilish
                  </Button>
                )}
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
