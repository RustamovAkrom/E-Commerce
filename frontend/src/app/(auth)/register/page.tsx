"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { ErrorMessage } from "@/components/common/error-message";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/lib/stores/auth.store";
const schema = z.object({ full_name: z.string().min(2, "Ismni kiriting"), email: z.email("Email noto‘g‘ri"), phone: z.string().min(3, "Telefonni kiriting"), password: z.string().min(8, "Kamida 8 belgi") }); type FormData = z.infer<typeof schema>;
export default function RegisterPage() { const router = useRouter(); const registerUser = useAuthStore((s) => s.register); const loading = useAuthStore((s) => s.isLoading); const error = useAuthStore((s) => s.error); const form = useForm<FormData>({ resolver: zodResolver(schema) }); const submit = async (data: FormData) => { try { await registerUser(data); router.replace("/account"); } catch {} }; return <div className="mx-auto flex min-h-[70vh] max-w-md items-center px-4 py-12 animate-fade-in"><Card className="w-full"><CardHeader><CardTitle>Ro‘yxatdan o‘tish</CardTitle></CardHeader><CardContent><form className="space-y-4" onSubmit={form.handleSubmit(submit)}>{error && <ErrorMessage message={error} />}{[["full_name","To‘liq ism","text"],["email","Email","email"],["phone","Telefon","tel"],["password","Parol","password"]].map(([name,label,type]) => <label key={name} className="block text-sm font-medium">{label}<Input type={type} {...form.register(name as keyof FormData)} />{form.formState.errors[name as keyof FormData] && <span className="text-sm text-destructive">{form.formState.errors[name as keyof FormData]?.message}</span>}</label>)}<Button className="w-full" disabled={loading}>{loading ? "Yaratilmoqda..." : "Hisob yaratish"}</Button><p className="text-center text-sm text-muted-foreground">Hisob bormi? <Link className="font-semibold text-primary" href="/login">Kiring</Link></p></form></CardContent></Card></div>; }
