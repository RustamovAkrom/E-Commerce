"use client";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { adminApi } from "@/lib/api/admin";
import { usersApi } from "@/lib/api/users";
import { toast } from "sonner";

export default function AdminCouriersPage() {
  const client = useQueryClient();
  const [userId, setUserId] = useState("");
  const [phone, setPhone] = useState("");
  const [zone, setZone] = useState("");

  const couriers = useQuery({
    queryKey: ["admin-couriers"],
    queryFn: () => adminApi.couriers({ size: 50 }),
  });
  const users = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => usersApi.list({ size: 100 }),
  });

  const invalidate = () =>
    client.invalidateQueries({ queryKey: ["admin-couriers"] });
  const create = useMutation({
    mutationFn: () =>
      adminApi.createCourier({
        user_id: userId,
        phone: phone || null,
        zone: zone || null,
      }),
    onSuccess: () => {
      setUserId("");
      setPhone("");
      setZone("");
      void invalidate();
      toast.success("Kuryer qo‘shildi");
    },
  });
  const toggleActive = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      adminApi.updateCourier(id, { is_active: isActive }),
    onSuccess: () => void invalidate(),
  });

  if (couriers.isLoading || users.isLoading) return <LoadingSpinner />;
  if (couriers.error)
    return (
      <ErrorMessage message={couriers.error.message} retry={() => void couriers.refetch()} />
    );

  const existingUserIds = new Set(couriers.data?.items.map((c) => c.user_id));
  const candidateUsers =
    users.data?.items.filter(
      (u) => u.role === "courier" && !existingUserIds.has(u.id),
    ) ?? [];

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Kuryerlar</h1>
        {!couriers.data?.items.length ? (
          <EmptyState title="Kuryerlar yo‘q" />
        ) : (
          couriers.data.items.map((c) => {
            const u = users.data?.items.find((x) => x.id === c.user_id);
            return (
              <Card key={c.id}>
                <CardContent className="flex items-center justify-between gap-3 p-4">
                  <div>
                    <strong>{u?.full_name || u?.email || c.user_id.slice(0, 8)}</strong>
                    <p className="text-xs text-muted-foreground">
                      {c.phone ?? "—"} · Zona: {c.zone ?? "—"}
                    </p>
                    <Badge variant={c.is_active ? "success" : "destructive"} className="mt-1">
                      {c.is_active ? "Faol" : "Nofaol"}
                    </Badge>
                  </div>
                  <Button
                    size="sm"
                    variant={c.is_active ? "outline" : "default"}
                    disabled={toggleActive.isPending}
                    onClick={() => toggleActive.mutate({ id: c.id, isActive: !c.is_active })}
                  >
                    {c.is_active ? "Nofaol" : "Faollashtirish"}
                  </Button>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Yangi kuryer</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {create.error && <ErrorMessage message={create.error.message} />}
          <label className="block text-sm font-medium">
            Foydalanuvchi (kuryer roli)
            <select
              className="mt-1 h-11 w-full rounded-xl border bg-background px-3"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
            >
              <option value="">Tanlang</option>
              {candidateUsers.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name || u.email}
                </option>
              ))}
            </select>
          </label>
          {candidateUsers.length === 0 && (
            <p className="text-xs text-muted-foreground">
              Avval “Foydalanuvchilar” bo‘limida kerakli userga{" "}
              <strong>Kuryer</strong> rolini bering.
            </p>
          )}
          <label className="block text-sm font-medium">
            Telefon
            <Input value={phone} onChange={(e) => setPhone(e.target.value)} />
          </label>
          <label className="block text-sm font-medium">
            Zona
            <Input value={zone} onChange={(e) => setZone(e.target.value)} />
          </label>
          <Button
            disabled={!userId || create.isPending}
            onClick={() => create.mutate()}
          >
            {create.isPending ? "Qo‘shilmoqda..." : "Qo‘shish"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
