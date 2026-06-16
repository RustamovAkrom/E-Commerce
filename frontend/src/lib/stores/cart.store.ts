"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { cartApi } from "@/lib/api/cart";
import type { Cart, CartItem, Product } from "@/types/api";

interface CartState {
  items: CartItem[];
  total: number;
  currency: string;
  isLoading: boolean;
  error: string | null;
  addItem: (product: Product, quantity?: number) => void;
  removeItem: (productId: string) => void;
  updateQuantity: (productId: string, quantity: number) => void;
  clear: () => void;
  syncWithBackend: () => Promise<void>;
}

function subtotal(items: CartItem[]): number { return items.reduce((sum, item) => sum + Number(item.unit_price) * item.quantity, 0); }
function fromCart(cart: Cart): Pick<CartState, "items" | "total" | "currency"> { return { items: cart.items, total: Number(cart.subtotal), currency: cart.currency }; }

export const useCartStore = create<CartState>()(persist((set, get) => ({
  items: [], total: 0, currency: "UZS", isLoading: false, error: null,
  addItem: (product, quantity = 1) => set((state) => { const existing = state.items.find((item) => item.product_id === product.id); const items = existing ? state.items.map((item) => item.product_id === product.id ? { ...item, quantity: Math.min(item.quantity + quantity, product.stock), line_total: Number(item.unit_price) * Math.min(item.quantity + quantity, product.stock) } : item) : [...state.items, { product_id: product.id, name: product.name, slug: product.slug, unit_price: product.price, currency: product.currency, quantity: Math.min(quantity, product.stock), line_total: Number(product.price) * Math.min(quantity, product.stock), available_stock: product.stock }]; return { items, total: subtotal(items), currency: product.currency }; }),
  removeItem: (productId) => set((state) => { const items = state.items.filter((item) => item.product_id !== productId); return { items, total: subtotal(items) }; }),
  updateQuantity: (productId, quantity) => set((state) => { const items = quantity < 1 ? state.items.filter((item) => item.product_id !== productId) : state.items.map((item) => item.product_id === productId ? { ...item, quantity: Math.min(quantity, item.available_stock), line_total: Number(item.unit_price) * Math.min(quantity, item.available_stock) } : item); return { items, total: subtotal(items) }; }),
  clear: () => set({ items: [], total: 0, error: null }),
  syncWithBackend: async () => { set({ isLoading: true, error: null }); try { for (const item of get().items) await cartApi.add({ product_id: item.product_id, quantity: item.quantity }); const cart = await cartApi.get(); set({ ...fromCart(cart), isLoading: false }); } catch (error) { set({ isLoading: false, error: error instanceof Error ? error.message : "Savatni sinxronlashda xatolik." }); } },
}), { name: "ecommerce-cart", partialize: ({ items, total, currency }) => ({ items, total, currency }) }));
