"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { shippingApi } from "@/lib/api/shipping";
import type { AddressCreate } from "@/types/api";
export default function AddressesPage() {
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["addresses"],
    queryFn: shippingApi.addresses,
  });
  const form = useForm<AddressCreate>({
    defaultValues: { country: "UZ", is_default: false },
  });
  const refresh = () => client.invalidateQueries({ queryKey: ["addresses"] });
  const create = useMutation({
    mutationFn: shippingApi.createAddress,
    onSuccess: () => {
      form.reset({ country: "UZ", is_default: false });
      void refresh();
    },
  });
  const remove = useMutation({
    mutationFn: shippingApi.deleteAddress,
    onSuccess: () => void refresh(),
  });
  if (query.isLoading) return <LoadingSpinner />;
  if (query.error)
    return (
      <ErrorMessage
        message={query.error.message}
        retry={() => void query.refetch()}
      />
    );
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Saqlangan manzillar</h1>
        {!query.data?.length ? (
          <EmptyState title="Manzillar yo‘q" />
        ) : (
          query.data.map((address) => (
            <Card key={address.id}>
              <CardContent className="p-5">
                <div className="flex justify-between">
                  <strong>{address.label ?? "Manzil"}</strong>
                  {address.is_default && (
                    <Badge variant="success">Asosiy</Badge>
                  )}
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  {address.full_name}, {address.phone}
                  <br />
                  {address.city}, {address.address}
                </p>
                <Button
                  className="mt-3"
                  size="sm"
                  variant="destructive"
                  onClick={() => remove.mutate(address.id)}
                >
                  O‘chirish
                </Button>
              </CardContent>
            </Card>
          ))
        )}
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Yangi manzil</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-3"
            onSubmit={form.handleSubmit((data) => create.mutate(data))}
          >
            {create.error && <ErrorMessage message={create.error.message} />}
            {[
              ["label", "Nomi"],
              ["full_name", "To‘liq ism"],
              ["phone", "Telefon"],
              ["address", "Manzil"],
              ["city", "Shahar"],
              ["country", "Davlat"],
              ["postal_code", "Pochta indeksi"],
            ].map(([name, label]) => (
              <label key={name} className="block text-sm font-medium">
                {label}
                <Input {...form.register(name as keyof AddressCreate)} />
              </label>
            ))}
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" {...form.register("is_default")} /> Asosiy
              manzil
            </label>
            <Button disabled={create.isPending}>
              {create.isPending ? "Saqlanmoqda..." : "Qo‘shish"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
