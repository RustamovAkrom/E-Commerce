import { apiV1 } from "@/lib/config";
import { getApiSession } from "@/lib/api/session";
import type { ApiErrorBody, TokenPair } from "@/types/api";
import { authApi } from "@/lib/api/auth";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public body?: ApiErrorBody,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const tokens = await authApi.refreshToken(
          getApiSession().getRefreshToken() ?? "",
        );
        getApiSession().onRefreshed(tokens.access_token);
        return tokens.access_token;
      } catch {
        return null;
      } finally {
        refreshPromise = null;
      }
    })();
  }
  return refreshPromise;
}

export interface FetchJsonOptions extends RequestInit {
  auth?: boolean;
  retryAuth?: boolean;
}

export async function fetchJson<T>(
  path: string,
  options: FetchJsonOptions = {},
): Promise<T> {
  const { auth = true, retryAuth = true, headers, ...init } = options;
  const token = auth ? getApiSession().getAccessToken() : null;
  const url =
    path.startsWith("http") || path.startsWith("/api/")
      ? path
      : `${apiV1}${path}`;
  const response = await fetch(url, {
    ...init,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  if (response.status === 401 && auth && retryAuth) {
    const refreshed = await refreshAccessToken();
    if (refreshed) return fetchJson<T>(path, { ...options, retryAuth: false });
    getApiSession().onExpired();
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => undefined)) as
      | ApiErrorBody
      | undefined;
    throw new ApiError(
      response.status,
      body?.message ?? `API request failed (${response.status})`,
      body,
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function toQuery<T extends object>(params: T): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]: [string, unknown]) => {
    if (
      typeof value === "string" ||
      typeof value === "number" ||
      typeof value === "boolean"
    ) {
      if (value !== "") search.set(key, String(value));
    }
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}
