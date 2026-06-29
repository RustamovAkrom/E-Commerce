import { fetchJson, toQuery } from "@/lib/api/client";
import type {
  MessageResponse,
  Page,
  PaginationQuery,
  ProductRatingSummary,
  Review,
  ReviewCreate,
  ReviewModerate,
  ReviewUpdate,
} from "@/types/api";

// NOTE: the reviews router is mounted at the API root (/api/v1), NOT under
// /catalog. Paths are /products/{id}/reviews and /reviews/{id}.
export const reviewsApi = {
  // Public endpoints
  listProductReviews: (productId: string, query: PaginationQuery = {}) =>
    fetchJson<Page<Review>>(
      `/products/${productId}/reviews${toQuery(query)}`,
      { auth: false },
    ),

  productRatingSummary: (productId: string) =>
    fetchJson<ProductRatingSummary>(
      `/products/${productId}/reviews/summary`,
      { auth: false },
    ),

  // Customer endpoints
  createReview: (productId: string, data: ReviewCreate) =>
    fetchJson<Review>(`/products/${productId}/reviews`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateReview: (reviewId: string, data: ReviewUpdate) =>
    fetchJson<Review>(`/reviews/${reviewId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteReview: (reviewId: string) =>
    fetchJson<MessageResponse>(`/reviews/${reviewId}`, {
      method: "DELETE",
    }),

  // Admin endpoints
  listAllReviews: (query: PaginationQuery = {}) =>
    fetchJson<Page<Review>>(`/reviews${toQuery(query)}`),

  moderateReview: (reviewId: string, data: ReviewModerate) =>
    fetchJson<Review>(`/reviews/${reviewId}/moderate`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  adminDeleteReview: (reviewId: string) =>
    fetchJson<MessageResponse>(`/reviews/${reviewId}/admin`, {
      method: "DELETE",
    }),
};
