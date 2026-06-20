import { fetchJson, toQuery } from "@/lib/api/client";
import type {
  Page,
  PaymentInitRequest,
  PaymentInitResponse,
  PaymentProvider,
} from "@/types/api";
export const paymentsApi = {
  initialize: (data: PaymentInitRequest) =>
    fetchJson<PaymentInitResponse>("/payments/initiate", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

export const paymentProviders: { value: PaymentProvider; label: string }[] = [
  { value: "click", label: "Click" },
  { value: "payme", label: "Payme" },
  { value: "stripe", label: "Stripe" },
];
