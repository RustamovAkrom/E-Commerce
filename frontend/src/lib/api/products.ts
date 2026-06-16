import { fetchJson, toQuery } from "@/lib/api/client";
import type { Category, Page, Product, ProductDetail, ProductQuery, ProductUpdate, ProductWrite } from "@/types/api";

export const productsApi = {
  categories: () => fetchJson<Category[]>("/catalog/categories", { auth: false }),
  list: (query: ProductQuery = {}) => fetchJson<Page<Product>>(`/catalog/products${toQuery(query)}`, { auth: false }),
  search: (search: string, query: ProductQuery = {}) => fetchJson<Page<Product>>(`/catalog/products${toQuery({ ...query, search })}`, { auth: false }),
  detail: (slug: string) => fetchJson<ProductDetail>(`/catalog/products/slug/${encodeURIComponent(slug)}`, { auth: false }),
  create: (data: ProductWrite) => fetchJson<ProductDetail>("/catalog/products", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: ProductUpdate) => fetchJson<ProductDetail>(`/catalog/products/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  remove: (id: string) => fetchJson<{ message: string }>(`/catalog/products/${id}`, { method: "DELETE" }),
};
