"use client";
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

const schema = z
  .object({
    email: z.email("Email noto‘g‘ri"),
    phone: z.string().optional().or(z.literal("")),
    password: z.string().min(8, "Kamida 8 belgi"),
    confirmPassword: z.string().min(8, "Kamida 8 belgi"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Parollar mos kelmadi",
    path: ["confirmPassword"],
  });
type FormData = z.infer<typeof schema>;

export default function RegisterPage() {
  const router = useRouter();
  const registerUser = useAuthStore((s) => s.register);
  const loading = useAuthStore((s) => s.isLoading);
  const error = useAuthStore((s) => s.error);
  const clearError = useAuthStore((s) => s.clearError);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  useEffect(() => {
    clearError();
  }, [clearError]);

  const submit = async (data: FormData) => {
    setSubmitError(null);
    try {
      await registerUser(data);
      router.replace("/account");
    } catch (err: unknown) {
      setSubmitError(
        err instanceof Error
          ? err.message
          : "Ro'yxatdan o'tishda xatolik. Qayta urinib ko'ring.",
      );
    }
  };

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-md items-center px-4 py-12 animate-fade-in">
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Ro‘yxatdan o‘tish</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit(submit)}>
            {(error || submitError) && (
              <ErrorMessage message={submitError ?? error!} />
            )}
            {[
              ["email", "Email", "email"],
              ["phone", "Telefon (ixtiyoriy)", "tel"],
              ["password", "Parol", "password"],
              ["confirmPassword", "Parolni tasdiqlang", "password"],
            ].map(([name, label, type]) => (
              <label key={name} className="block text-sm font-medium">
                {label}
                <Input
                  type={type}
                  {...register(name as keyof FormData)}
                  disabled={loading}
                />
                {errors[name as keyof FormData] && (
                  <span className="text-sm text-destructive">
                    {errors[name as keyof FormData]?.message}
                  </span>
                )}
              </label>
            ))}
            <Button className="w-full" disabled={loading}>
              {loading ? "Yaratilmoqda..." : "Hisob yaratish"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Hisob bormi?{" "}
              <Link className="font-semibold text-primary" href="/login">
                Kiring
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
