"use client";
import type { Route } from "next";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { ErrorMessage } from "@/components/common/error-message";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/lib/stores/auth.store";
import { dashboardPath } from "@/lib/auth/roles";

const schema = z.object({
  email: z.email("Email noto‘g‘ri"),
  password: z.string().min(8, "Kamida 8 belgi"),
});
type FormData = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const loading = useAuthStore((s) => s.isLoading);
  const error = useAuthStore((s) => s.error);
  const clearError = useAuthStore((s) => s.clearError);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [failedAttempts, setFailedAttempts] = useState(0);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  // Очищаем общую ошибку store при каждом рендере формы
  useEffect(() => {
    clearError();
  }, [clearError]);

  const submit = async (data: FormData) => {
    setSubmitError(null);
    try {
      await login({ email: data.email, password: data.password });
      const role = useAuthStore.getState().user?.role ?? null;
      const next = new URLSearchParams(window.location.search).get("next");
      const target = next && next.startsWith("/") ? next : dashboardPath(role);
      router.replace(target as Route);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Login xatosi. Iltimos qayta urinib ko'ring.";

      setSubmitError(msg);
      setFailedAttempts((n) => n + 1);
    }
  };

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-md items-center px-4 py-12 animate-fade-in">
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Kirish</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit(submit)}>
            {(error || submitError) && (
              <ErrorMessage
                message={submitError ?? error!}
                retry={() => {
                  setSubmitError(null);
                }}
              />
            )}
            <label className="block text-sm font-medium">
              Email
              <Input
                type="email"
                autoComplete="email"
                {...register("email")}
                disabled={loading}
              />
            </label>
            {errors.email && (
              <p className="text-sm text-destructive">{errors.email.message}</p>
            )}
            <label className="block text-sm font-medium">
              Parol
              <Input
                type="password"
                autoComplete="current-password"
                {...register("password")}
                disabled={loading}
              />
            </label>
            {errors.password && (
              <p className="text-sm text-destructive">
                {errors.password.message}
              </p>
            )}
            <Button
              className="w-full"
              disabled={loading || failedAttempts >= 5}
            >
              {loading
                ? "Kirilmoqda..."
                : failedAttempts >= 5
                  ? "Ko'p urinishlar. Iltimos keyinroq qayting."
                  : "Kirish"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Hisob yo‘qmi?{" "}
              <Link className="font-semibold text-primary" href="/register">
                Ro‘yxatdan o‘ting
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
