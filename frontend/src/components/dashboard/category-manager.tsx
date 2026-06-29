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
import { toast } from "sonner";
import type { Category, CategoryCreate } from "@/types/api";

const schema = z.object({
  name: z.string().min(1, "Nomi kiriting"),
  description: z.string().optional(),
  sort_order: z.number().int().nonnegative(),
  is_active: z.boolean(),
});
type FormData = z.infer<typeof schema>;

/** Category CRUD surface, shared by admin and operator dashboards. */
export function CategoryManager() {
  const client = useQueryClient();
  const [editing, setEditing] = useState<Category | null>(null);
  const categories = useQuery({
    queryKey: ["categories"],
    queryFn: productsApi.categories,
  });
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { sort_order: 0, is_active: true },
  });
  const refresh = () => client.invalidateQueries({ queryKey: ["categories"] });
  const save = useMutation({
    mutationFn: (data: CategoryCreate) =>
      editing
        ? productsApi.updateCategory(editing.id, data)
        : productsApi.createCategory(data),
    onSuccess: () => {
      setEditing(null);
      form.reset({ sort_order: 0, is_active: true, name: "", description: "" });
      void refresh();
      toast.success(editing ? "Kategoriya yangilandi" : "Kategoriya yaratildi");
    },
  });
  const remove = useMutation({
    mutationFn: productsApi.deleteCategory,
    onSuccess: () => {
      void refresh();
      toast.success("O‘chirildi");
    },
  });

  if (categories.isLoading) return <LoadingSpinner />;
  if (categories.error)
    return (
      <ErrorMessage
        message={categories.error.message}
        retry={() => void categories.refetch()}
      />
    );

  return (
    <div className="space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold">Kategoriyalar</h1>
      <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
        <div className="space-y-3">
          {!categories.data?.length ? (
            <EmptyState title="Kategoriyalar yo‘q" />
          ) : (
            categories.data.map((c) => (
              <Card key={c.id}>
                <CardContent className="flex items-center justify-between gap-3 p-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <strong>{c.name}</strong>
                      <Badge variant={c.is_active ? "success" : "destructive"}>
                        {c.is_active ? "Faol" : "Nofaol"}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">/{c.slug}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setEditing(c);
                        form.reset({
                          name: c.name,
                          description: c.description ?? "",
                          sort_order: c.sort_order,
                          is_active: c.is_active,
                        });
                      }}
                    >
                      Tahrirlash
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      disabled={remove.isPending}
                      onClick={() => remove.mutate(c.id)}
                    >
                      O‘chirish
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
        <Card>
          <CardHeader>
            <CardTitle>
              {editing ? "Kategoriyani tahrirlash" : "Yangi kategoriya"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="space-y-3"
              onSubmit={form.handleSubmit((data) => save.mutate(data))}
            >
              {save.error && <ErrorMessage message={save.error.message} />}
              {/* Slug is generated automatically on the backend from the name —
                  never exposed to users (avoids invalid/duplicate slugs). */}
              {[
                ["name", "Nomi", "text"],
                ["sort_order", "Tartib raqami", "number"],
              ].map(([name, label, type]) => (
                <label key={name} className="block text-sm font-medium">
                  {label}
                  <Input
                    type={type}
                    {...form.register(
                      name as keyof FormData,
                      type === "number" ? { valueAsNumber: true } : undefined,
                    )}
                  />
                </label>
              ))}
              {form.formState.errors.name && (
                <p className="text-sm text-destructive">{form.formState.errors.name.message}</p>
              )}
              <label className="block text-sm font-medium">
                Tavsif
                <textarea
                  className="min-h-20 w-full rounded-xl border bg-background p-3"
                  {...form.register("description")}
                />
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" {...form.register("is_active")} />
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
                      form.reset({ sort_order: 0, is_active: true });
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
