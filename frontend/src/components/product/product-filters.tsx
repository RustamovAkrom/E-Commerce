"use client";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import type { Category, ProductQuery } from "@/types/api";
export function ProductFilters({
  value,
  categories,
  onChange,
}: {
  value: ProductQuery;
  categories: Category[];
  onChange: (value: ProductQuery) => void;
}) {
  return (
    <div className="grid gap-3 rounded-2xl border bg-card p-4 sm:grid-cols-2 lg:grid-cols-4">
      <label className="relative sm:col-span-2">
        <span className="sr-only">Qidirish</span>
        <Search className="absolute left-3 top-3.5 size-4 text-muted-foreground" />
        <Input
          value={value.search ?? ""}
          onChange={(e) =>
            onChange({ ...value, search: e.target.value, page: 1 })
          }
          className="pl-9"
          placeholder="Mahsulot qidirish"
        />
      </label>
      <select
        aria-label="Kategoriya"
        className="h-11 rounded-xl border bg-background px-3 text-sm"
        value={value.category_id ?? ""}
        onChange={(e) =>
          onChange({
            ...value,
            category_id: e.target.value || undefined,
            page: 1,
          })
        }
      >
        <option value="">Barcha kategoriyalar</option>
        {categories.map((category) => (
          <option key={category.id} value={category.id}>
            {category.name}
          </option>
        ))}
      </select>
      <select
        aria-label="Saralash"
        className="h-11 rounded-xl border bg-background px-3 text-sm"
        value={value.sort ?? "-created_at"}
        onChange={(e) =>
          onChange({
            ...value,
            sort: e.target.value as ProductQuery["sort"],
            page: 1,
          })
        }
      >
        <option value="-created_at">Eng yangi</option>
        <option value="price">Narx: arzon</option>
        <option value="-price">Narx: qimmat</option>
        <option value="name">Nomi bo‘yicha</option>
      </select>
    </div>
  );
}
