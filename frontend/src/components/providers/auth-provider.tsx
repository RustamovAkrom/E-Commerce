"use client";
import { useEffect } from "react";
import { useAuthStore } from "@/lib/stores/auth.store";
export function AuthProvider({ children }: { children: React.ReactNode }) { const initialized = useAuthStore((s) => s.initialized); const refresh = useAuthStore((s) => s.refresh); useEffect(() => { if (!initialized) void refresh(); }, [initialized, refresh]); return children; }
