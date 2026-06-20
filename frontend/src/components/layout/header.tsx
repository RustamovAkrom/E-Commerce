"use client";
import type { Route } from "next";
import Link from "next/link";
import { Menu, LogOut, ShoppingCart, UserRound, Bell } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { CartDrawer } from "@/components/cart/cart-drawer";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { config } from "@/lib/config";
import { useAuthStore } from "@/lib/stores/auth.store";
import { notificationsApi } from "@/lib/api/notifications";

interface NavLink {
  href: string;
  label: string;
}

const links: NavLink[] = [
  { href: "/", label: "Bosh sahifa" },
  { href: "/products", label: "Mahsulotlar" },
];

export function Header() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const isAdmin = user?.role === "admin" || user?.role === "superadmin" || user?.role === "operator";
  const isCourier = user?.role === "courier";
  const isLoggedIn = !!user;

  const { data: notifications } = useQuery({
    queryKey: ["notifications-count"],
    queryFn: () => notificationsApi.list(),
    enabled: isLoggedIn,
    refetchInterval: 30000, // 30 soniyada yangilaydi
    staleTime: 10000,
  });

  const unreadCount = notifications?.total ?? 0;

  return (
    <header className="sticky top-0 z-40 border-b bg-background/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <Sheet>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden"
                aria-label="Menyuni ochish"
              >
                <Menu className="size-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left">
              <SheetTitle>Menyu</SheetTitle>
              <nav className="mt-6 flex flex-col gap-4">
                {links.map((link) => (
                  <Link key={link.href} href={link.href as Parameters<typeof Link>[0]["href"]}>
                    {link.label}
                  </Link>
                ))}
                {isCourier && (
                  <a href="/delivery/my-deliveries" className="block py-1">
                    Yetkazuvlarim
                  </a>
                )}
              </nav>
            </SheetContent>
          </Sheet>
          <Link href="/" className="text-lg font-black tracking-tight">
            {config.appName}
          </Link>
          <nav className="hidden gap-5 text-sm font-medium md:flex">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href as Parameters<typeof Link>[0]["href"]}
                className="hover:text-primary"
              >
                {link.label}
              </Link>
            ))}
            {isCourier && (
              <a href="/delivery/my-deliveries" className="hover:text-primary">
                Yetkazuvlarim
              </a>
            )}
          </nav>
        </div>
        <div className="flex items-center gap-1">
          <CartDrawer />
          {isLoggedIn && (
            <div className="relative">
              <a href="/account/notifications">
                <Bell className="size-5" />
              </a>
              {unreadCount > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex size-4 items-center justify-center rounded-full bg-destructive text-[10px] font-bold text-destructive-foreground">
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              )}
            </div>
          )}
          <Button
            asChild
            variant="ghost"
            size="icon"
            aria-label={user ? "Kabinet" : "Kirish"}
          >
            <Link href={user ? "/account" : "/login"}>
              <UserRound className="size-5" />
            </Link>
          </Button>
          {user && (
            <>
              {isAdmin && (
                <Button asChild variant="ghost" size="icon" title="Admin panel">
                  <Link href="/admin">
                    <ShoppingCart className="size-5" />
                  </Link>
                </Button>
              )}
              <Button
                variant="ghost"
                size="icon"
                title="Chiqish"
                onClick={() => { void logout(); }}
              >
                <LogOut className="size-5" />
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
