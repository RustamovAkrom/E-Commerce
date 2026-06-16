import { fetchJson } from "@/lib/api/client";
import type { User, UserUpdateRequest } from "@/types/api";
export const usersApi = {
  profile: () => fetchJson<User>("/users/me"),
  update: (data: UserUpdateRequest) => fetchJson<User>("/users/me", { method: "PATCH", body: JSON.stringify(data) }),
};
