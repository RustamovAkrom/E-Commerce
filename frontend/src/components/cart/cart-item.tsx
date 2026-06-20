"use client";
import Link from "next/link";
import { Minus, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCartStore } from "@/lib/stores/cart.store";
import { formatPrice } from "@/lib/utils";
import type { CartItem as CartItemType } from "@/types/api";
export function CartItem({ item }: { item: CartItemType }) {
  const update = useCartStore((s) => s.updateQuantity);
  const remove = useCartStore((s) => s.removeItem);
  return (
    <div className="flex gap-3 border-b py-4">
      <div className="min-w-0 flex-1">
        <Link
          href={`/products/${item.slug}`}
          className="font-medium hover:text-primary"
        >
          {item.name}
        </Link>
        <p className="mt-1 text-sm text-muted-foreground">
          {formatPrice(item.unit_price, item.currency)}
        </p>
        <div className="mt-3 flex items-center gap-2">
          <Button
            size="icon"
            variant="outline"
            onClick={() => update(item.product_id, item.quantity - 1)}
            aria-label="Kamaytirish"
          >
            <Minus className="size-4" />
          </Button>
          <span className="w-8 text-center">{item.quantity}</span>
          <Button
            size="icon"
            variant="outline"
            disabled={item.quantity >= item.available_stock}
            onClick={() => update(item.product_id, item.quantity + 1)}
            aria-label="Ko‘paytirish"
          >
            <Plus className="size-4" />
          </Button>
        </div>
      </div>
      <div className="flex flex-col items-end justify-between">
        <strong>{formatPrice(item.line_total, item.currency)}</strong>
        <Button
          size="icon"
          variant="ghost"
          onClick={() => remove(item.product_id)}
          aria-label="Savatdan o‘chirish"
        >
          <Trash2 className="size-4 text-destructive" />
        </Button>
      </div>
    </div>
  );
}
