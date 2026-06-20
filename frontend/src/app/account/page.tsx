"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  LogOut,
  UserRound,
  Settings,
  Bell,
  ShoppingBag,
  Package,
  CreditCard,
  MapPin,
  Shield,
  Loader2,
  CheckCircle2,
} from "lucide-react";
import Link from "next/link";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { usersApi } from "@/lib/api/users";
import { useAuthStore } from "@/lib/stores/auth.store";
import type { UserUpdateRequest } from "@/types/api";

const passwordSchema = z
  .object({
    current_password: z.string().min(8, "Kamida 8 belgi"),
    new_password: z.string().min(8, "Kamida 8 belgi"),
    confirm_new_password: z.string().min(8, "Kamida 8 belgi"),
  })
  .refine((data) => data.new_password === data.confirm_new_password, {
    message: "Yangi parollar mos kelmadi",
    path: ["confirm_new_password"],
  });
type PasswordFormData = z.infer<typeof passwordSchema>;

const roleBadges: Record<string, { label: string; variant: "default" | "success" | "secondary" | "destructive" }> = {
  customer: { label: "Mijoz", variant: "default" },
  vendor: { label: "Sotuvchi", variant: "success" },
  operator: { label: "Operator", variant: "secondary" },
  courier: { label: "Kuryer", variant: "secondary" },
  admin: { label: "Admin", variant: "destructive" },
  superadmin: { label: "Superadmin", variant: "destructive" },
};

export default function AccountPage() {
  const router = useRouter();
  const client = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const query = useQuery({ queryKey: ["profile"], queryFn: usersApi.profile });
  const form = useForm<UserUpdateRequest>({
    defaultValues: { full_name: user?.full_name ?? "", phone: user?.phone ?? "" },
  });
  useEffect(() => {
    if (query.data)
      form.reset({ full_name: query.data.full_name, phone: query.data.phone });
  }, [query.data, form]);
  const mutation = useMutation({
    mutationFn: usersApi.update,
    onSuccess: (u) => {
      client.setQueryData(["profile"], u);
      useAuthStore.setState({ user: u });
    },
  });
  const passwordForm = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
  });
  const passwordMutation = useMutation({
    mutationFn: usersApi.changePassword,
    onSuccess: () => {
      passwordForm.reset();
    },
  });

  if (query.isLoading) return <LoadingSpinner />;
  if (query.error)
    return (
      <ErrorMessage
        message={query.error.message}
        retry={() => void query.refetch()}
      />
    );
  if (!query.data) return <EmptyState title="Profil topilmadi" />;

  const profile = query.data;
  const roleInfo = roleBadges[profile.role] ?? { label: profile.role, variant: "secondary" };
  const initials = (profile.full_name ?? profile.email)
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="mx-auto max-w-4xl space-y-6 animate-fade-in">
      {/* Profile Header */}
      <Card>
        <CardContent className="flex items-center gap-6 p-6">
          <div className="flex size-20 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-2xl font-bold">
            {initials}
          </div>
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold">
                {profile.full_name || "Foydalanuvchi"}
              </h2>
              <Badge variant={roleInfo.variant as "default" | "success" | "secondary" | "destructive"}>
                {roleInfo.label}
              </Badge>
              {profile.is_verified && (
                <Badge variant="outline" className="gap-1">
                  <CheckCircle2 className="size-3" /> Tasdiqlangan
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground">{profile.email}</p>
            {profile.phone && (
              <p className="text-sm text-muted-foreground">{profile.phone}</p>
            )}
            <p className="text-xs text-muted-foreground">
              Ro'yxatdan o'tgan: {new Date(profile.created_at).toLocaleDateString("uz-UZ")}
            </p>
          </div>
          <Button variant="outline" onClick={() => logout()} className="gap-2">
            <LogOut className="size-4" />
            Chiqish
          </Button>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Link href="/account/orders" className="group">
          <Card className="transition-shadow hover:shadow-md">
            <CardContent className="flex flex-col items-center gap-2 p-6">
              <Package className="size-8 text-muted-foreground group-hover:text-primary" />
              <span className="text-sm font-medium">Buyurtmalarim</span>
            </CardContent>
          </Card>
        </Link>
        <Link href="/account/addresses" className="group">
          <Card className="transition-shadow hover:shadow-md">
            <CardContent className="flex flex-col items-center gap-2 p-6">
              <MapPin className="size-8 text-muted-foreground group-hover:text-primary" />
              <span className="text-sm font-medium">Manzillar</span>
            </CardContent>
          </Card>
        </Link>
        <a href="/account/notifications" className="group">
          <Card className="transition-shadow hover:shadow-md">
            <CardContent className="flex flex-col items-center gap-2 p-6">
              <Bell className="size-8 text-muted-foreground group-hover:text-primary" />
              <span className="text-sm font-medium">Xabarlar</span>
            </CardContent>
          </Card>
        </a>
        <Link href="/cart" className="group">
          <Card className="transition-shadow hover:shadow-md">
            <CardContent className="flex flex-col items-center gap-2 p-6">
              <ShoppingBag className="size-8 text-muted-foreground group-hover:text-primary" />
              <span className="text-sm font-medium">Savatcha</span>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Profile Edit */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="size-5" />
            Profil ma'lumotlari
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={form.handleSubmit((data) => mutation.mutate(data))}
          >
            {mutation.error && <ErrorMessage message={mutation.error.message} />}
            <label className="block text-sm font-medium">
              Email
              <Input value={profile.email} disabled />
            </label>
            <label className="block text-sm font-medium">
              To'liq ism
              <Input {...form.register("full_name")} />
            </label>
            <label className="block text-sm font-medium">
              Telefon
              <Input {...form.register("phone")} />
            </label>
            <div className="flex items-center gap-3">
              <Badge variant={profile.is_active ? "success" : "destructive"}>
                {profile.is_active ? "Faol" : "Nofaol"}
              </Badge>
            </div>
            <Button disabled={mutation.isPending} className="gap-2">
              {mutation.isPending && <Loader2 className="size-4 animate-spin" />}
              {mutation.isPending ? "Saqlanmoqda..." : "Saqlash"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Password Change */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="size-5" />
            Parolni o'zgartirish
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={passwordForm.handleSubmit((data) =>
              passwordMutation.mutate({
                current_password: data.current_password,
                new_password: data.new_password,
              }),
            )}
          >
            {passwordMutation.error && (
              <ErrorMessage message={passwordMutation.error.message} />
            )}
            <label className="block text-sm font-medium">
              Joriy parol
              <Input type="password" {...passwordForm.register("current_password")} />
            </label>
            {passwordForm.formState.errors.current_password && (
              <p className="text-sm text-destructive">
                {passwordForm.formState.errors.current_password.message}
              </p>
            )}
            <label className="block text-sm font-medium">
              Yangi parol
              <Input type="password" {...passwordForm.register("new_password")} />
            </label>
            {passwordForm.formState.errors.new_password && (
              <p className="text-sm text-destructive">
                {passwordForm.formState.errors.new_password.message}
              </p>
            )}
            <label className="block text-sm font-medium">
              Yangi parolni tasdiqlang
              <Input type="password" {...passwordForm.register("confirm_new_password")} />
            </label>
            {passwordForm.formState.errors.confirm_new_password && (
              <p className="text-sm text-destructive">
                {passwordForm.formState.errors.confirm_new_password.message}
              </p>
            )}
            <Button disabled={passwordMutation.isPending} className="gap-2">
              {passwordMutation.isPending && <Loader2 className="size-4 animate-spin" />}
              {passwordMutation.isPending ? "O'zgartirilmoqda..." : "Parolni yangilash"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
