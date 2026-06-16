import { fetchJson } from "@/lib/api/client";
import type { AuthResult, LoginRequest, MessageResponse, RegisterRequest, TokenPair, User } from "@/types/api";

export const authApi = {
  login: (data: LoginRequest) => fetchJson<AuthResult>("/api/auth/login", { method: "POST", auth: false, body: JSON.stringify(data) }),
  register: (data: RegisterRequest) => fetchJson<AuthResult>("/api/auth/register", { method: "POST", auth: false, body: JSON.stringify(data) }),
  refresh: () => fetchJson<TokenPair>("/api/auth/refresh", { method: "POST", auth: false }),
  logout: () => fetchJson<MessageResponse>("/api/auth/logout", { method: "POST", auth: false }),
  me: () => fetchJson<User>("/users/me"),
};
