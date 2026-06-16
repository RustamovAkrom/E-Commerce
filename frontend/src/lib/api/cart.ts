import { fetchJson } from "@/lib/api/client";
import type { Cart, CartItemRequest, MessageResponse } from "@/types/api";
export const cartApi = {
  get: () => fetchJson<Cart>("/cart"),
  add: (data: CartItemRequest) => fetchJson<Cart>("/cart/items", { method: "POST", body: JSON.stringify(data) }),
  update: (data: CartItemRequest) => fetchJson<Cart>("/cart/items", { method: "PUT", body: JSON.stringify(data) }),
  remove: (productId: string) => fetchJson<Cart>(`/cart/items/${productId}`, { method: "DELETE" }),
  clear: () => fetchJson<MessageResponse>("/cart", { method: "DELETE" }),
};
