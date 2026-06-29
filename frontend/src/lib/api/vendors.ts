import { ApiError, fetchJson, toQuery } from "@/lib/api/client";
import type {
  Page,
  VendorApplyRequest,
  VendorPublic,
  VendorResponse,
  VendorUpdateRequest,
} from "@/types/api";

export const vendorsApi = {
  // Public storefront
  list: (query: { page?: number; size?: number } = {}) =>
    fetchJson<Page<VendorPublic>>(`/vendors${toQuery(query)}`, { auth: false }),
  bySlug: (slug: string) =>
    fetchJson<VendorPublic>(`/vendors/slug/${encodeURIComponent(slug)}`, {
      auth: false,
    }),

  // Vendor self-service
  me: () => fetchJson<VendorResponse>("/vendors/me"),
  /** Returns null instead of throwing when the user has no vendor profile yet. */
  meOrNull: async (): Promise<VendorResponse | null> => {
    try {
      return await fetchJson<VendorResponse>("/vendors/me");
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) return null;
      throw error;
    }
  },
  apply: (data: VendorApplyRequest) =>
    fetchJson<VendorResponse>("/vendors/apply", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateMe: (data: VendorUpdateRequest) =>
    fetchJson<VendorResponse>("/vendors/me", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
};
