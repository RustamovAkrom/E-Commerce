import type { Metadata } from "next";
import { AuthProvider } from "@/components/providers/auth-provider";
import { QueryProvider } from "@/components/providers/query-provider";
import { Footer } from "@/components/layout/footer";
import { Header } from "@/components/layout/header";
import { Toaster } from "@/components/ui/toaster";
import { config } from "@/lib/config";
import "./globals.css";
export const metadata: Metadata = { title: { default: config.appName, template: `%s | ${config.appName}` }, description: "Zamonaviy va ishonchli e-commerce platformasi" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="uz"><body className="flex min-h-screen flex-col bg-background font-sans text-foreground antialiased"><QueryProvider><AuthProvider><Header /><main className="flex-1">{children}</main><Footer /><Toaster /></AuthProvider></QueryProvider></body></html>; }
