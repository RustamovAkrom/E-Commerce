"use client";

import { create } from "zustand";
import { authApi } from "@/lib/api/auth";
import { configureApiSession } from "@/lib/api/session";
import type { LoginRequest, RegisterRequest, User } from "@/types/api";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
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

function message(error: unknown): string {
  if (error instanceof Error) {
    const text = error.message.toLowerCase();
    // API error
    if (text.includes("401") || text.includes("unauthorized")) {
      return "Email yoki parol noto‘g‘ri. Iltimos tekshirib qayta kiriting.";
    }
    if (text.includes("403") || text.includes("forbidden")) {
      return "Hisobingiz bloklangan. Administrator bilan bog‘laning.";
    }
    if (text.includes("429") || text.includes("too many")) {
      return "Juda ko‘p urinish. Iltimos 1 daqi kutib qayta urinib ko'ring.";
    }
    if (text.includes("404") || text.includes("not found")) {
      return "Bunday foydalanuvchi topilmadi. Ro'yxatdan o'ting.";
    }
    if (text.includes("network") || text.includes("fetch")) {
      return "Serverga ulanishda xatolik. Internetni tekshiring.";
    }
    return error.message;
  }
  return "Kutilmagan xatolik yuz berdi. Qayta urinib ko'ring.";
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: false,
  initialized: false,
  error: null,
  login: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const result = await authApi.login(data);
      set({
        user: result.user,
        accessToken: result.tokens.access_token,
        refreshToken: result.tokens.refresh_token,
        isAuthenticated: true,
        isLoading: false,
        initialized: true,
      });
    } catch (error) {
      set({ error: message(error), isLoading: false });
      throw error;
    }
  },
  register: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const result = await authApi.register({
        email: data.email,
        password: data.password,
        ...(data.full_name && { full_name: data.full_name }),
        ...(data.phone && { phone: data.phone }),
      });
      set({
        user: result.user,
        accessToken: result.tokens.access_token,
        refreshToken: result.tokens.refresh_token,
        isAuthenticated: true,
        isLoading: false,
        initialized: true,
      });
    } catch (error) {
      set({ error: message(error), isLoading: false });
      throw error;
    }
  },
  refresh: async () => {
    const currentRefresh = get().refreshToken;
    if (!currentRefresh) {
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        initialized: true,
      });
      return false;
    }
    set({ isLoading: true });
    try {
      const tokens = await authApi.refreshToken(currentRefresh);
      set({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        isAuthenticated: true,
        isLoading: false,
      });
      return true;
    } catch {
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        initialized: true,
      });
      return false;
    }
  },
  logout: async () => {
    try {
      await authApi.logout();
    } finally {
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        initialized: true,
        error: null,
      });
    }
  },
  clearError: () => set({ error: null }),
}));

configureApiSession({
  getAccessToken: () => useAuthStore.getState().accessToken,
  getRefreshToken: () => useAuthStore.getState().refreshToken,
  onRefreshed: (accessToken) =>
    useAuthStore.setState({ accessToken, isAuthenticated: true }),
  onExpired: () =>
    useAuthStore.setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      initialized: true,
    }),
});
