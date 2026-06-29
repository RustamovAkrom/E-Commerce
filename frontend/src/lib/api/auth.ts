import { fetchJson } from "@/lib/api/client";
import { apiV1 } from "@/lib/config";
import type {
  AuthResult,
  LoginRequest,
  MessageResponse,
  RegisterRequest,
  TokenPair,
  User,
} from "@/types/api";

export const authApi = {
  login: (data: LoginRequest) =>
    fetchJson<AuthResult>("/api/auth/login", {
      method: "POST",
      auth: false,
      body: JSON.stringify(data),
    }),
  register: (data: RegisterRequest) =>
    fetchJson<AuthResult>("/api/auth/register", {
      method: "POST",
      auth: false,
      body: JSON.stringify(data),
    }),
  telegramLogin: (telegramId: number, fullName: string | null) =>
    fetchJson<AuthResult>("/api/auth/telegram", {
      method: "POST",
      auth: false,
      body: JSON.stringify({
        telegram_id: telegramId,
        full_name: fullName,
        auth_secret: process.env.NEXT_PUBLIC_TELEGRAM_AUTH_SECRET ?? "",
      }),
    }),
  refresh: async (): Promise<TokenPair> => {
    // The refresh token is an httpOnly cookie; the Next.js route reads it and
    // exchanges it with the backend, returning a fresh access token.
    const res = await fetch("/api/auth/refresh", {
      method: "POST",
      credentials: "include",
    });
    if (!res.ok) throw new Error("Token refresh failed");
    return res.json() as Promise<TokenPair>;
  },
  refreshToken: (refreshToken: string) =>
    fetchJson<TokenPair>(
      `${apiV1}/auth/refresh`,
      {
        method: "POST",
        auth: false,
        body: JSON.stringify({ refresh_token: refreshToken }),
      },
    ),
  logout: () =>
    fetchJson<MessageResponse>("/api/auth/logout", {
      method: "POST",
      auth: false,
    }),
  me: () => fetchJson<User>("/users/me"),
};
