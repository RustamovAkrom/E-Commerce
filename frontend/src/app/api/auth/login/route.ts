import { cookies } from "next/headers";
import {
  backendAuth,
  authCookie,
  cookieOptions,
  proxyResponse,
} from "@/lib/api/server-auth";
import type { AuthResult, LoginRequest } from "@/types/api";
export async function POST(request: Request) {
  const data = (await request.json()) as LoginRequest;
  const form = new URLSearchParams({
    username: data.email,
    password: data.password,
  });
  const response = await backendAuth("/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form,
  });
  if (!response.ok) return proxyResponse(response);
  const result = (await response.json()) as AuthResult;
  const store = await cookies();
  store.set(authCookie.refresh, result.tokens.refresh_token, cookieOptions);
  store.set(authCookie.role, result.user.role, cookieOptions);
  return Response.json({
    ...result,
    tokens: { ...result.tokens, refresh_token: "" },
  });
}
