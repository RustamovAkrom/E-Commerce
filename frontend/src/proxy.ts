import { NextRequest, NextResponse } from "next/server";
import { authCookie } from "@/lib/api/server-auth";
import { dashboardPath } from "@/lib/auth/roles";
import type { UserRole } from "@/types/api";

/** Which roles may enter each dashboard root. */
const ROUTE_ROLES: { prefix: string; roles: UserRole[] }[] = [
  { prefix: "/admin", roles: ["admin", "superadmin"] },
  { prefix: "/operator", roles: ["operator", "admin", "superadmin"] },
  { prefix: "/vendor", roles: ["vendor"] },
  { prefix: "/courier", roles: ["courier"] },
];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasSession = Boolean(request.cookies.get(authCookie.refresh)?.value);
  const role = request.cookies.get(authCookie.role)?.value as
    | UserRole
    | undefined;

  // Not logged in → bounce to login, remembering where they wanted to go.
  if (!hasSession) {
    const login = new URL("/login", request.url);
    login.searchParams.set("next", pathname);
    return NextResponse.redirect(login);
  }

  // Logged in but wrong role for this dashboard → send to their own dashboard.
  const rule = ROUTE_ROLES.find(
    (r) => pathname === r.prefix || pathname.startsWith(`${r.prefix}/`),
  );
  if (rule && role && !rule.roles.includes(role)) {
    return NextResponse.redirect(new URL(dashboardPath(role), request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/account/:path*",
    "/admin/:path*",
    "/operator/:path*",
    "/vendor/:path*",
    "/courier/:path*",
    "/checkout/:path*",
  ],
};
