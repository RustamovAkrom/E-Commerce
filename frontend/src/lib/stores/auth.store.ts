"use client";

import { create } from "zustand";
import { authApi } from "@/lib/api/auth";
import { configureApiSession } from "@/lib/api/session";
import type { LoginRequest, RegisterRequest, User } from "@/types/api";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  initialized: boolean;
  error: string | null;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  refresh: () => Promise<boolean>;
  logout: () => Promise<void>;
  clearError: () => void;
}

function message(error: unknown): string { return error instanceof Error ? error.message : "Kutilmagan xatolik yuz berdi."; }

export const useAuthStore = create<AuthState>((set) => ({
  user: null, accessToken: null, isAuthenticated: false, isLoading: false, initialized: false, error: null,
  login: async (data) => { set({ isLoading: true, error: null }); try { const result = await authApi.login(data); set({ user: result.user, accessToken: result.tokens.access_token, isAuthenticated: true, isLoading: false, initialized: true }); } catch (error) { set({ error: message(error), isLoading: false }); throw error; } },
  register: async (data) => { set({ isLoading: true, error: null }); try { const result = await authApi.register(data); set({ user: result.user, accessToken: result.tokens.access_token, isAuthenticated: true, isLoading: false, initialized: true }); } catch (error) { set({ error: message(error), isLoading: false }); throw error; } },
  refresh: async () => { set({ isLoading: true }); try { const tokens = await authApi.refresh(); set({ accessToken: tokens.access_token, isAuthenticated: true }); const user = await authApi.me(); set({ user, isLoading: false, initialized: true }); return true; } catch { set({ user: null, accessToken: null, isAuthenticated: false, isLoading: false, initialized: true }); return false; } },
  logout: async () => { try { await authApi.logout(); } finally { set({ user: null, accessToken: null, isAuthenticated: false, initialized: true, error: null }); } },
  clearError: () => set({ error: null }),
}));

configureApiSession({
  getAccessToken: () => useAuthStore.getState().accessToken,
  onRefreshed: (accessToken) => useAuthStore.setState({ accessToken, isAuthenticated: true }),
  onExpired: () => useAuthStore.setState({ user: null, accessToken: null, isAuthenticated: false, initialized: true }),
});
