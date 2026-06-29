import type { UserRole } from "@/types/api";

/**
 * Single source of truth for where each role lands after authentication and
 * which dashboard root it owns. Keep this in sync with `proxy.ts` guards.
 */
export const ROLE_HOME: Record<UserRole, string> = {
  superadmin: "/admin",
  admin: "/admin",
  operator: "/operator",
  vendor: "/vendor",
  courier: "/courier",
  customer: "/account",
};

/** Roles that may access the admin analytics panel. */
export const ADMIN_ROLES: readonly UserRole[] = ["admin", "superadmin"];

/** Human-readable role label (Uzbek) for badges and headings. */
export const ROLE_LABEL: Record<UserRole, string> = {
  superadmin: "Bosh administrator",
  admin: "Administrator",
  operator: "Operator",
  vendor: "Sotuvchi",
  courier: "Kuryer",
  customer: "Mijoz",
};

/** Resolve the dashboard path for a role; defaults to the customer account. */
export function dashboardPath(role: UserRole | null | undefined): string {
  if (!role) return "/account";
  return ROLE_HOME[role] ?? "/account";
}

/** Whether a role is a staff (back-office) role rather than a shopper. */
export function isStaffRole(role: UserRole | null | undefined): boolean {
  return role === "admin" || role === "superadmin" || role === "operator";
}
