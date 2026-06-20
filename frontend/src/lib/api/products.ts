import { fetchJson, toQuery } from "@/lib/api/client";
import type {
  Category,
  CategoryCreate,
  CategoryUpdate,
  Page,
  Product,
  ProductDetail,
  ProductQuery,
  ProductUpdate,
  ProductWrite,
} from "@/types/api";

export const productsApi = {
  // Categories
  categories: () =>
    fetchJson<Category[]>("/catalog/categories", { auth: false }),
  createCategory: (data: CategoryCreate) =>
    fetchJson<Category>("/catalog/categories", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateCategory: (id: string, data: CategoryUpdate) =>
    fetchJson<Category>(`/catalog/categories/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteCategory: (id: string) =>
    fetchJson<{ message: string }>(`/catalog/categories/${id}`, {
      method: "DELETE",
    }),

  // Products
  list: (query: ProductQuery = {}) =>
    fetchJson<Page<Product>>(`/catalog/products${toQuery(query)}`, {
      auth: false,
    }),
  detail: (slug: string) =>
    fetchJson<ProductDetail>(
      `/catalog/products/slug/${encodeURIComponent(slug)}`,
      { auth: false },
    ),
  detailById: (id: string) =>
    fetchJson<ProductDetail>(`/catalog/products/${id}`, { auth: false }),
  create: (data: ProductWrite) =>
    fetchJson<ProductDetail>("/catalog/products", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: string, data: ProductUpdate) =>
    fetchJson<ProductDetail>(`/catalog/products/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  remove: (id: string) =>
    fetchJson<{ message: string }>(`/catalog/products/${id}`, {
      method: "DELETE",
    }),
};
