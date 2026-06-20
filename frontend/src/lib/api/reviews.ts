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

export const reviewsApi = {
  // Public endpoints
  listProductReviews: (productId: string, query: PaginationQuery = {}) =>
    fetchJson<Page<Review>>(
      `/catalog/products/${productId}/reviews${toQuery(query)}`,
      { auth: false },
    ),

  productRatingSummary: (productId: string) =>
    fetchJson<ProductRatingSummary>(
      `/catalog/products/${productId}/reviews/summary`,
      { auth: false },
    ),

  // Customer endpoints
  createReview: (productId: string, data: ReviewCreate) =>
    fetchJson<Review>(`/catalog/products/${productId}/reviews`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateReview: (reviewId: string, data: ReviewUpdate) =>
    fetchJson<Review>(`/catalog/reviews/${reviewId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteReview: (reviewId: string) =>
    fetchJson<MessageResponse>(`/catalog/reviews/${reviewId}`, {
      method: "DELETE",
    }),

  // Admin endpoints
  listAllReviews: (query: PaginationQuery = {}) =>
    fetchJson<Page<Review>>(`/catalog/reviews${toQuery(query)}`),

  moderateReview: (reviewId: string, data: ReviewModerate) =>
    fetchJson<Review>(`/catalog/reviews/${reviewId}/moderate`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  adminDeleteReview: (reviewId: string) =>
    fetchJson<MessageResponse>(`/catalog/reviews/${reviewId}/admin`, {
      method: "DELETE",
    }),
};
