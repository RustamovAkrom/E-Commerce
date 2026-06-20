"use client";
import Link from "next/link";
import { ShoppingBag } from "lucide-react";
import { CartItem } from "@/components/cart/cart-item";
import { CartSummary } from "@/components/cart/cart-summary";
import { EmptyState } from "@/components/common/empty-state";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { useCartStore } from "@/lib/stores/cart.store";
export function CartDrawer() {
  const items = useCartStore((s) => s.items);
  const total = useCartStore((s) => s.total);
  const currency = useCartStore((s) => s.currency);
  const count = items.reduce((sum, item) => sum + item.quantity, 0);
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          aria-label="Savatni ochish"
        >
          <ShoppingBag className="size-5" />
          {count > 0 && (
            <span className="absolute -right-1 -top-1 flex size-5 items-center justify-center rounded-full bg-primary text-[10px] text-primary-foreground">
              {count}
            </span>
          )}
        </Button>
      </SheetTrigger>
      <SheetContent className="overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Savat ({count})</SheetTitle>
        </SheetHeader>
        {items.length ? (
          <div className="space-y-5">
            {items.map((item) => (
              <CartItem key={item.product_id} item={item} />
            ))}
            <CartSummary total={total} currency={currency} />
            <Button asChild variant="outline" className="w-full">
              <Link href="/cart">To‘liq savat</Link>
            </Button>
          </div>
        ) : (
          <EmptyState
            title="Savat bo‘sh"
            description="Mahsulotlar katalogidan xaridni boshlang."
            action={
              <Button asChild>
                <Link href="/products">Katalogga o‘tish</Link>
              </Button>
            }
          />
        )}
      </SheetContent>
    </Sheet>
  );
}
