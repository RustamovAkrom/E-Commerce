import { fetchJson } from "@/lib/api/client";
import type { Address, AddressCreate, AddressUpdate, MessageResponse } from "@/types/api";
export const shippingApi = {
  addresses: () => fetchJson<Address[]>("/shipping/addresses"),
  createAddress: (data: AddressCreate) => fetchJson<Address>("/shipping/addresses", { method: "POST", body: JSON.stringify(data) }),
  updateAddress: (id: string, data: AddressUpdate) => fetchJson<Address>(`/shipping/addresses/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteAddress: (id: string) => fetchJson<MessageResponse>(`/shipping/addresses/${id}`, { method: "DELETE" }),
};
