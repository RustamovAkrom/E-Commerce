"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { adminApi } from "@/lib/api/admin";
import { toast } from "sonner";
import type { VendorStatus } from "@/types/api";

const STATUS_LABEL: Record<VendorStatus, string> = {
  pending: "Kutilmoqda",
  approved: "Tasdiqlangan",
  rejected: "Rad etilgan",
  suspended: "To‘xtatilgan",
};

export default function AdminVendorsPage() {
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["admin-vendors"],
    queryFn: () => adminApi.vendors({ size: 50 }),
  });
  const invalidate = () =>
    client.invalidateQueries({ queryKey: ["admin-vendors"] });
  const update = useMutation({
    mutationFn: ({ id, status }: { id: string; status: VendorStatus }) =>
      adminApi.updateVendor(id, { status }),
    onSuccess: () => {
      void invalidate();
      toast.success("Holat yangilandi");
    },
  });
  const toggleActive = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      adminApi.updateVendor(id, { is_active: isActive }),
    onSuccess: () => void invalidate(),
  });
  const remove = useMutation({
    mutationFn: (id: string) => adminApi.deleteVendor(id),
    onSuccess: () => {
      void invalidate();
      toast.success("Sotuvchi o‘chirildi");
    },
  });

  if (query.isLoading) return <LoadingSpinner />;
  if (query.error)
    return <ErrorMessage message={query.error.message} retry={() => void query.refetch()} />;
  if (!query.data?.items.length) return <EmptyState title="Sotuvchilar topilmadi" />;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Sotuvchilar boshqaruvi</h1>
      {(update.error || remove.error) && <ErrorMessage message="Xatolik yuz berdi" />}
      {query.data.items.map((v) => (
        <Card key={v.id}>
          <CardContent className="grid gap-3 p-4 sm:grid-cols-[1fr_auto_auto] sm:items-center">
            <div>
              <strong>{v.name}</strong>
              <p className="text-xs text-muted-foreground">
                /{v.slug} · Komissiya {v.commission_rate}%
              </p>
              <Badge variant={v.is_active ? "success" : "destructive"} className="mt-1">
                {v.is_active ? "Faol" : "Nofaol"}
              </Badge>
            </div>
            <select
              aria-label="Holat"
              className="h-9 rounded-lg border bg-background px-2 text-sm"
              value={v.status}
              disabled={update.isPending}
              onChange={(e) =>
                update.mutate({ id: v.id, status: e.target.value as VendorStatus })
              }
            >
              {(Object.keys(STATUS_LABEL) as VendorStatus[]).map((s) => (
                <option key={s} value={s}>
                  {STATUS_LABEL[s]}
                </option>
              ))}
            </select>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant={v.is_active ? "outline" : "default"}
                disabled={toggleActive.isPending}
                onClick={() => toggleActive.mutate({ id: v.id, isActive: !v.is_active })}
              >
                {v.is_active ? "Nofaol" : "Faollashtirish"}
              </Button>
              <Button
                size="sm"
                variant="destructive"
                disabled={remove.isPending}
                onClick={() => remove.mutate(v.id)}
              >
                O‘chirish
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
