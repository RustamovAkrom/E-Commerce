import { NextRequest, NextResponse } from "next/server";
import { authCookie } from "@/lib/api/server-auth";

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasSession = Boolean(request.cookies.get(authCookie.refresh)?.value);
  const role = request.cookies.get(authCookie.role)?.value;
  if (!hasSession) {
    const login = new URL("/login", request.url);
    login.searchParams.set("next", pathname);
    return NextResponse.redirect(login);
  }
  if (pathname.startsWith("/admin") && role !== "admin" && role !== "superadmin") return NextResponse.redirect(new URL("/account", request.url));
  return NextResponse.next();
}

export const config = { matcher: ["/account/:path*", "/admin/:path*", "/checkout/:path*"] };
