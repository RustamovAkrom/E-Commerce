"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { CartSummary } from "@/components/cart/cart-summary";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ordersApi } from "@/lib/api/orders";
import { paymentsApi, paymentProviders } from "@/lib/api/payments";
import { shippingApi } from "@/lib/api/shipping";
import { useCartStore } from "@/lib/stores/cart.store";
import type { PaymentProvider, ShippingAddressInput } from "@/types/api";
const schema = z.object({
  full_name: z.string().min(1),
  phone: z.string().min(3),
  address: z.string().min(1),
  city: z.string().min(1),
  country: z.string().min(2),
  postal_code: z.string().optional(),
  note: z.string().max(1024).optional(),
});
type FormData = z.infer<typeof schema>;
export default function CheckoutPage() {
  const router = useRouter();
  const cart = useCartStore();
  const [step, setStep] = useState(1);
  const [provider, setProvider] = useState<PaymentProvider>("click");
  const addresses = useQuery({
    queryKey: ["addresses"],
    queryFn: shippingApi.addresses,
  });
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { country: "UZ" },
  });
  const order = useMutation({
    mutationFn: async (data: FormData) => {
      const shipping_address: ShippingAddressInput = {
        ...data,
        postal_code: data.postal_code || null,
      };
      const created = await ordersApi.create({
        shipping_address,
        note: data.note || null,
      });
      const payment = await paymentsApi.initialize({
        order_id: created.id,
        provider,
        return_url: `${window.location.origin}/success?order=${created.id}`,
      });
      return { created, payment };
    },
    onSuccess: ({ created, payment }) => {
      cart.clear();
      if (payment.checkout_url) window.location.assign(payment.checkout_url);
      else router.push(`/success?order=${created.id}`);
    },
  });
  if (!cart.items.length)
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <EmptyState
          title="Checkout uchun savat bo‘sh"
          description="Avval savatga mahsulot qo‘shing."
        />
      </div>
    );
  if (addresses.isLoading) return <LoadingSpinner />;
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 animate-fade-in">
      <div className="mb-8 flex gap-2">
        {["Manzil", "To‘lov", "Tasdiq"].map((label, index) => (
          <Badge
            key={label}
            variant={step === index + 1 ? "default" : "secondary"}
          >
            {index + 1}. {label}
          </Badge>
        ))}
      </div>
      <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
        <Card>
          <CardHeader>
            <CardTitle>
              {step === 1
                ? "Yetkazish manzili"
                : step === 2
                  ? "To‘lov usuli"
                  : "Buyurtmani tasdiqlang"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {addresses.error && (
              <ErrorMessage
                message={addresses.error.message}
                retry={() => void addresses.refetch()}
              />
            )}
            {order.error && <ErrorMessage message={order.error.message} />}
            {step === 1 && (
              <form
                className="grid gap-4 sm:grid-cols-2"
                onSubmit={form.handleSubmit(() => setStep(2))}
              >
                {addresses.data && addresses.data.length > 0 && (
                  <select
                    className="h-11 rounded-xl border px-3 sm:col-span-2"
                    defaultValue=""
                    onChange={(e) => {
                      const item = addresses.data.find(
                        (a) => a.id === e.target.value,
                      );
                      if (item)
                        Object.entries(item).forEach(([key, value]) => {
                          if (
                            [
                              "full_name",
                              "phone",
                              "address",
                              "city",
                              "country",
                              "postal_code",
                            ].includes(key)
                          )
                            form.setValue(key as keyof FormData, value ?? "");
                        });
                    }}
                  >
                    <option value="">Saqlangan manzilni tanlang</option>
                    {addresses.data.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.label ?? a.city}: {a.address}
                      </option>
                    ))}
                  </select>
                )}
                {[
                  ["full_name", "To‘liq ism"],
                  ["phone", "Telefon"],
                  ["address", "Manzil"],
                  ["city", "Shahar"],
                  ["country", "Davlat"],
                  ["postal_code", "Pochta indeksi"],
                ].map(([name, label]) => (
                  <label key={name} className="text-sm font-medium">
                    {label}
                    <Input {...form.register(name as keyof FormData)} />
                  </label>
                ))}
                <label className="text-sm font-medium sm:col-span-2">
                  Izoh
                  <Input {...form.register("note")} />
                </label>
                <Button className="sm:col-span-2">To‘lovga o‘tish</Button>
              </form>
            )}
            {step === 2 && (
              <div className="space-y-4">
                {paymentProviders.map((item) => (
                  <label
                    key={item.value}
                    className="flex cursor-pointer items-center gap-3 rounded-xl border p-4"
                  >
                    <input
                      type="radio"
                      checked={provider === item.value}
                      onChange={() => setProvider(item.value)}
                    />
                    <span className="font-semibold uppercase">{item.label}</span>
                  </label>
                ))}
                <div className="flex gap-3">
                  <Button variant="outline" onClick={() => setStep(1)}>
                    Orqaga
                  </Button>
                  <Button onClick={() => setStep(3)}>Davom etish</Button>
                </div>
              </div>
            )}
            {step === 3 && (
              <div className="space-y-5">
                <p>
                  {cart.items.length} turdagi mahsulot, jami{" "}
                  {cart.items.reduce((sum, i) => sum + i.quantity, 0)} dona.
                </p>
                <p>
                  To‘lov: <strong className="uppercase">{provider}</strong>
                </p>
                <div className="flex gap-3">
                  <Button variant="outline" onClick={() => setStep(2)}>
                    Orqaga
                  </Button>
                  <Button
                    disabled={order.isPending}
                    onClick={form.handleSubmit((data) => order.mutate(data))}
                  >
                    {order.isPending ? "Yaratilmoqda..." : "Buyurtma berish"}
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        <CartSummary
          total={cart.total}
          currency={cart.currency}
          checkout={false}
        />
      </div>
    </div>
  );
}
