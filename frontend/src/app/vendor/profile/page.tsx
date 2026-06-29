"use client";
import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { ErrorMessage } from "@/components/common/error-message";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { vendorsApi } from "@/lib/api/vendors";
import { toast } from "sonner";

const schema = z.object({
  name: z.string().min(1, "Do‘kon nomini kiriting"),
  description: z.string().optional(),
  contact_email: z.union([z.email("Email noto‘g‘ri"), z.literal("")]).optional(),
  contact_phone: z.string().optional(),
  logo_url: z.union([z.url("URL noto‘g‘ri"), z.literal("")]).optional(),
});
type FormData = z.infer<typeof schema>;

export default function VendorProfilePage() {
  const client = useQueryClient();
  const vendor = useQuery({
    queryKey: ["vendor-me"],
    queryFn: vendorsApi.meOrNull,
  });
  const isNew = !vendor.data;
  const form = useForm<FormData>({ resolver: zodResolver(schema) });

  useEffect(() => {
    if (vendor.data) {
      form.reset({
        name: vendor.data.name,
        description: vendor.data.description ?? "",
        contact_email: vendor.data.contact_email ?? "",
        contact_phone: vendor.data.contact_phone ?? "",
        logo_url: vendor.data.logo_url ?? "",
      });
    }
  }, [vendor.data, form]);

  const save = useMutation({
    mutationFn: (data: FormData) => {
      const payload = {
        name: data.name,
        description: data.description || null,
        contact_email: data.contact_email || null,
        contact_phone: data.contact_phone || null,
      };
      return isNew
        ? vendorsApi.apply(payload)
        : vendorsApi.updateMe({ ...payload, logo_url: data.logo_url || null });
    },
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["vendor-me"] });
      toast.success(isNew ? "Ariza yuborildi" : "Profil yangilandi");
    },
  });

  if (vendor.isLoading) return <LoadingSpinner />;
  if (vendor.error)
    return (
      <ErrorMessage
        message={vendor.error.message}
        retry={() => void vendor.refetch()}
      />
    );

  return (
    <div className="mx-auto max-w-xl space-y-4 animate-fade-in">
      <h1 className="text-2xl font-bold">
        {isNew ? "Do‘kon ochish" : "Do‘kon profili"}
      </h1>
      <Card>
        <CardHeader>
          <CardTitle>{isNew ? "Sotuvchi arizasi" : "Ma’lumotlar"}</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-3"
            onSubmit={form.handleSubmit((data) => save.mutate(data))}
          >
            {save.error && <ErrorMessage message={save.error.message} />}
            <label className="block text-sm font-medium">
              Do‘kon nomi
              <Input {...form.register("name")} />
              {form.formState.errors.name && (
                <span className="text-sm text-destructive">
                  {form.formState.errors.name.message}
                </span>
              )}
            </label>
            <label className="block text-sm font-medium">
              Tavsif
              <textarea
                className="min-h-24 w-full rounded-xl border bg-background p-3"
                {...form.register("description")}
              />
            </label>
            <label className="block text-sm font-medium">
              Aloqa email
              <Input type="email" {...form.register("contact_email")} />
            </label>
            <label className="block text-sm font-medium">
              Aloqa telefon
              <Input type="tel" {...form.register("contact_phone")} />
            </label>
            {!isNew && (
              <label className="block text-sm font-medium">
                Logo URL
                <Input {...form.register("logo_url")} />
              </label>
            )}
            <Button disabled={save.isPending}>
              {save.isPending
                ? "Saqlanmoqda..."
                : isNew
                  ? "Ariza yuborish"
                  : "Saqlash"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
