"use client";
import Link from "next/link";
import { Menu, UserRound } from "lucide-react";
import { CartDrawer } from "@/components/cart/cart-drawer";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { config } from "@/lib/config";
import { useAuthStore } from "@/lib/stores/auth.store";

interface NavLink { href: string; label: string }
const links: NavLink[] = [
  { href: "/", label: "Bosh sahifa" },
  { href: "/products", label: "Mahsulotlar" },
];

export function Header() {
  const user = useAuthStore((s) => s.user);
  return (
    <header className="sticky top-0 z-40 border-b bg-background/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="md:hidden" aria-label="Menyuni ochish">
                <Menu className="size-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left">
              <SheetTitle>Menyu</SheetTitle>
              <nav className="mt-6 flex flex-col gap-4">
                {links.map((link) => <Link key={link.href} href={link.href}>{link.label}</Link>)}
              </nav>
            </SheetContent>
          </Sheet>
          <Link href="/" className="text-lg font-black tracking-tight">{config.appName}</Link>
          <nav className="hidden gap-5 text-sm font-medium md:flex">
            {links.map((link) => <Link key={link.href} href={link.href} className="hover:text-primary">{link.label}</Link>)}
          </nav>
        </div>
        <div className="flex items-center gap-1">
          <CartDrawer />
          <Button asChild variant="ghost" size="icon" aria-label={user ? "Kabinet" : "Kirish"}>
            <Link href={user ? "/account" : "/login"}>
              <UserRound className="size-5" />
            </Link>
          </Button>
        </div>
      </div>
    </header>
  );
}