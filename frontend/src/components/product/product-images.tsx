"use client";
import Image from "next/image";
import { useState } from "react";
import type { ProductImage } from "@/types/api";
export function ProductImages({
  images,
  name,
}: {
  images: ProductImage[];
  name: string;
}) {
  const sorted = [...images].sort(
    (a, b) =>
      Number(b.is_primary) - Number(a.is_primary) ||
      a.sort_order - b.sort_order,
  );
  const [selected, setSelected] = useState(
    sorted[0]?.url ?? "/product-fallback.svg",
  );
  return (
    <div className="space-y-3">
      <div className="relative aspect-square overflow-hidden rounded-2xl bg-muted">
        <Image
          src={selected}
          alt={name}
          fill
          priority
          sizes="(max-width: 768px) 100vw, 50vw"
          className="object-cover"
        />
      </div>
      {sorted.length > 1 && (
        <div className="flex gap-2 overflow-x-auto">
          {sorted.map((image) => (
            <button
              key={image.id}
              aria-label={`${name} rasmi`}
              onClick={() => setSelected(image.url)}
              className="relative size-20 shrink-0 overflow-hidden rounded-xl border"
            >
              <Image
                src={image.url}
                alt=""
                fill
                sizes="80px"
                className="object-cover"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
