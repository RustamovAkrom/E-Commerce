"use client";
import Link from "next/link";
import { CartItem } from "@/components/cart/cart-item";
import { CartSummary } from "@/components/cart/cart-summary";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Button } from "@/components/ui/button";
import { useCartStore } from "@/lib/stores/cart.store";
export default function CartPage() { const { items, total, currency, isLoading, error } = useCartStore(); if (isLoading) return <LoadingSpinner />; if (error) return <div className="mx-auto max-w-3xl p-4"><ErrorMessage message={error} /></div>; if (!items.length) return <div className="mx-auto max-w-3xl px-4 py-16"><EmptyState title="Savat bo‘sh" action={<Button asChild><Link href="/products">Mahsulotlarni ko‘rish</Link></Button>} /></div>; return <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 lg:grid-cols-[1fr_360px] animate-fade-in"><section><h1 className="mb-5 text-3xl font-bold">Savat</h1>{items.map((item) => <CartItem key={item.product_id} item={item} />)}</section><CartSummary total={total} currency={currency} /></div>; }
