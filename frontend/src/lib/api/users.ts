import { fetchJson, toQuery } from "@/lib/api/client";
import type {
  Page,
  PasswordChangeRequest,
  User,
  UserAdminUpdateRequest,
  UserUpdateRequest,
} from "@/types/api";

export const usersApi = {
  profile: () => fetchJson<User>("/users/me"),
  update: (data: UserUpdateRequest) =>
    fetchJson<User>("/users/me", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  changePassword: (data: PasswordChangeRequest) =>
    fetchJson<{ message: string }>("/users/me/password", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  // Admin endpoints
  list: (query: { page?: number; size?: number } = {}) =>
    fetchJson<Page<User>>(`/users${toQuery(query)}`),
  get: (id: string) => fetchJson<User>(`/users/${id}`),
  adminUpdate: (id: string, data: UserAdminUpdateRequest) =>
    fetchJson<User>(`/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  updateRole: (id: string, data: UserAdminUpdateRequest) =>
    fetchJson<User>(`/users/${id}/role`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  toggleStatus: (id: string, isActive: boolean) =>
    fetchJson<User>(`/users/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive }),
    }),
};
