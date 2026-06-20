"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { usersApi } from "@/lib/api/users";
import type { UserRole } from "@/types/api";

const roleLabels: Record<UserRole, string> = {
  customer: "Mijoz",
  vendor: "Sotuvchi",
  operator: "Operator",
  courier: "Kuryer",
  admin: "Admin",
  superadmin: "Superadmin",
};

export default function AdminUsersPage() {
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => usersApi.list({ size: 50 }),
  });
  const toggleStatus = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      usersApi.toggleStatus(id, isActive),
    onSuccess: () =>
      void client.invalidateQueries({ queryKey: ["admin-users"] }),
  });
  const updateRole = useMutation({
    mutationFn: ({ id, role }: { id: string; role: UserRole }) =>
      usersApi.updateRole(id, { role }),
    onSuccess: () =>
      void client.invalidateQueries({ queryKey: ["admin-users"] }),
  });

  if (query.isLoading) return <LoadingSpinner />;
  if (query.error)
    return (
      <ErrorMessage message={query.error.message} retry={() => void query.refetch()} />
    );
  if (!query.data?.items.length)
    return <EmptyState title="Foydalanuvchilar topilmadi" />;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Foydalanuvchilar boshqaruvi</h1>
      {(toggleStatus.error || updateRole.error) && (
        <ErrorMessage message="Xatolik yuz berdi" />
      )}
      {query.data.items.map((user) => (
        <Card key={user.id}>
          <CardContent className="grid gap-3 p-4 sm:grid-cols-4 sm:items-center">
            <div>
              <strong>{user.email}</strong>
              {user.full_name && (
                <p className="text-xs text-muted-foreground">{user.full_name}</p>
              )}
              <p className="text-xs text-muted-foreground">{user.created_at.slice(0, 10)}</p>
            </div>
            <Badge variant={user.is_active ? "success" : "destructive"}>
              {user.is_active ? "Faol" : "Nofaol"}
            </Badge>
            <Badge variant="secondary">{roleLabels[user.role] ?? user.role}</Badge>
            <div className="flex gap-2">
              <select
                aria-label="Rol o‘zgartirish"
                className="h-9 rounded-lg border bg-background px-2 text-sm"
                value={user.role}
                disabled={updateRole.isPending}
                onChange={(e) =>
                  updateRole.mutate({ id: user.id, role: e.target.value as UserRole })
                }
              >
                <option value="customer">Mijoz</option>
                <option value="vendor">Sotuvchi</option>
                <option value="operator">Operator</option>
                <option value="courier">Kuryer</option>
                <option value="admin">Admin</option>
              </select>
              <Button
                size="sm"
                variant={user.is_active ? "destructive" : "default"}
                disabled={toggleStatus.isPending}
                onClick={() => toggleStatus.mutate({ id: user.id, isActive: !user.is_active })}
              >
                {user.is_active ? "Nofaol" : "Faol"}
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
