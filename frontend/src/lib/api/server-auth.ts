import type { ApiErrorBody } from "@/types/api";

export const authCookie = {
  refresh: "ecom_refresh",
  role: "ecom_role",
} as const;
export const cookieOptions = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  path: "/",
  maxAge: 60 * 60 * 24 * 30,
};

// Server-side only: use BACKEND_URL (internal Docker hostname) for SSR/API routes.
// Falls back to NEXT_PUBLIC_API_URL for local dev outside Docker.
const backendBase =
  process.env.BACKEND_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

export async function backendAuth(
  path: string,
  init: RequestInit,
): Promise<Response> {
  return fetch(`${backendBase}/api/v1/auth${path}`, {
    ...init,
    cache: "no-store",
    headers: { Accept: "application/json", ...init.headers },
  });
}

export async function proxyResponse(response: Response): Promise<Response> {
  const body = await response.text();
  return new Response(body, {
    status: response.status,
    headers: {
      "Content-Type":
        response.headers.get("Content-Type") ?? "application/json",
    },
  });
}

export async function errorMessage(response: Response): Promise<string> {
  const body = (await response.json().catch(() => undefined)) as
    | ApiErrorBody
    | undefined;
  return body?.message ?? `Auth request failed (${response.status})`;
}
