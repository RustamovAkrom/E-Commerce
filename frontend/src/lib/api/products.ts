import { fetchJson, toQuery } from "@/lib/api/client";
import type {
  Category,
  CategoryCreate,
  CategoryUpdate,
  Page,
  Product,
  ProductDetail,
  ProductImage,
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
  uploadImage: (
    id: string,
    file: File,
    options: { is_primary?: boolean; sort_order?: number } = {},
  ) => {
    const form = new FormData();
    form.append("file", file);
    form.append("is_primary", String(options.is_primary ?? false));
    form.append("sort_order", String(options.sort_order ?? 0));
    return fetchJson<ProductImage>(`/catalog/products/${id}/images`, {
      method: "POST",
      body: form,
    });
  },
  setPrimaryImage: (productId: string, imageId: string) =>
    fetchJson<ProductImage>(
      `/catalog/products/${productId}/images/${imageId}/primary`,
      { method: "PATCH" },
    ),
  deleteImage: (productId: string, imageId: string) =>
    fetchJson<{ message: string }>(
      `/catalog/products/${productId}/images/${imageId}`,
      { method: "DELETE" },
    ),
};
