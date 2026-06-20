"use client";
import Image from "next/image";
import Link from "next/link";
import { ShoppingCart } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useCartStore } from "@/lib/stores/cart.store";
import { formatPrice } from "@/lib/utils";
import type { Product } from "@/types/api";

export function ProductCard({ product }: { product: Product }) {
  const addItem = useCartStore((s) => s.addItem);
  const add = () => {
    addItem(product);
    toast.success("Mahsulot savatga qo\u0027shildi");
  };
  return (
    <Card className="group overflow-hidden transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5">
      <Link
        href={`/products/${product.slug}`}
        className="relative block aspect-square overflow-hidden bg-muted"
      >
        <Image
          src="/product-fallback.svg"
          alt={product.name}
          fill
          sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
          className="object-cover transition-transform duration-200 group-hover:scale-105"
        />
      </Link>
      <CardContent className="space-y-3 p-4">
        <div className="flex items-center justify-between gap-2">
          <Badge variant={product.stock > 0 ? "success" : "destructive"}>
            {product.stock > 0 ? "Sotuvda" : "Tugagan"}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {product.sku ?? "SKU yo\u0027q"}
          </span>
        </div>
        <Link
          href={`/products/${product.slug}`}
          className="line-clamp-2 min-h-12 font-semibold hover:text-primary"
        >
          {product.name}
        </Link>
        <div className="flex items-center justify-between gap-2">
          <strong>{formatPrice(product.price, product.currency)}</strong>
          <Button
            size="icon"
            disabled={!product.stock}
            onClick={add}
            aria-label={`${product.name}ni savatga qo\u0027shish`}
          >
            <ShoppingCart className="size-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
