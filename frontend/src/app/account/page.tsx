"use client";
import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { usersApi } from "@/lib/api/users";
import type { UserUpdateRequest } from "@/types/api";
export default function AccountPage() { const client = useQueryClient(); const query = useQuery({ queryKey: ["profile"], queryFn: usersApi.profile }); const form = useForm<UserUpdateRequest>(); useEffect(() => { if (query.data) form.reset({ full_name: query.data.full_name, phone: query.data.phone }); }, [query.data, form]); const mutation = useMutation({ mutationFn: usersApi.update, onSuccess: (user) => client.setQueryData(["profile"], user) }); if (query.isLoading) return <LoadingSpinner />; if (query.error) return <ErrorMessage message={query.error.message} retry={() => void query.refetch()} />; if (!query.data) return <EmptyState title="Profil topilmadi" />; return <Card className="animate-fade-in"><CardHeader><CardTitle>Profil sozlamalari</CardTitle></CardHeader><CardContent><form className="max-w-xl space-y-4" onSubmit={form.handleSubmit((data) => mutation.mutate(data))}>{mutation.error && <ErrorMessage message={mutation.error.message} />}<label className="block text-sm font-medium">Email<Input value={query.data.email} disabled /></label><label className="block text-sm font-medium">To‘liq ism<Input {...form.register("full_name")} /></label><label className="block text-sm font-medium">Telefon<Input {...form.register("phone")} /></label><Button disabled={mutation.isPending}>{mutation.isPending ? "Saqlanmoqda..." : "Saqlash"}</Button></form></CardContent></Card>; }
