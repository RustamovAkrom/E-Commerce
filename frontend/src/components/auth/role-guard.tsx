"use client";
import { useEffect } from "react";
import type { Route } from "next";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/auth.store";
import { dashboardPath } from "@/lib/auth/roles";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import type { UserRole } from "@/types/api";

/**
 * Client-side access guard for protected dashboards. This is defence-in-depth
 * on top of `proxy.ts` (the server middleware):
 *
 *  - Blocks rendering until the session is restored, so dashboard content never
 *    flashes for an unauthenticated visitor who knows the URL.
 *  - Redirects to /login when there is no session (also handles logout: the
 *    moment the store is cleared, the guard kicks the user out of the panel).
 *  - Redirects to the user's own dashboard when their role is not allowed here,
 *    so one role can never see another role's panel.
 *
 * @param allow - roles permitted on this branch. Omit to require only that the
 *                user is authenticated (e.g. the shared customer account area).
 */
export function RoleGuard({
  allow,
  children,
}: {
  allow?: UserRole[];
  children: React.ReactNode;
}) {
  const router = useRouter();
  const initialized = useAuthStore((s) => s.initialized);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const role = useAuthStore((s) => s.user?.role ?? null);

  const roleAllowed = !allow || (role ? allow.includes(role) : false);

  useEffect(() => {
    if (!initialized) return; // session still being restored — wait
    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }
    if (role && !roleAllowed) {
      router.replace(dashboardPath(role) as Route);
    }
  }, [initialized, isAuthenticated, role, roleAllowed, router]);

  // Until we are certain the user belongs here, render nothing but a spinner.
  if (!initialized || !isAuthenticated || !roleAllowed) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }
  return <>{children}</>;
}
