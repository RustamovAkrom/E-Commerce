import { fetchJson } from "@/lib/api/client";
import type { PaymentInitRequest, PaymentInitResponse } from "@/types/api";
export const paymentsApi = { initialize: (data: PaymentInitRequest) => fetchJson<PaymentInitResponse>("/payments/init", { method: "POST", body: JSON.stringify(data) }) };
