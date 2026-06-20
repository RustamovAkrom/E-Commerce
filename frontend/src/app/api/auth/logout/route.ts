import { cookies } from "next/headers";
import { backendAuth, authCookie } from "@/lib/api/server-auth";
export async function POST() {
  const store = await cookies();
  const refreshToken = store.get(authCookie.refresh)?.value;
  if (refreshToken)
    await backendAuth("/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  store.delete(authCookie.refresh);
  store.delete(authCookie.role);
  return Response.json({ message: "Tizimdan chiqildi." });
}
