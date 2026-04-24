"use client";

import { create } from "zustand";

import { api } from "@/lib/api";

type UserRole = "admin" | "merchandiser" | "viewer";

export interface User {
  id: string;
  email: string;
  role: UserRole;
  created_at: string;
}

interface TokenPair {
  token_type: "bearer";
  access_token: string;
  refresh_token: string;
}

interface AuthPayload {
  user: User;
  tokens: TokenPair;
}

interface AuthApiResponse {
  data: AuthPayload;
  message: string;
}

interface RefreshRequest {
  refresh_token: string;
}

interface AuthStore {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, role?: UserRole) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  initializeAuth: () => void;
}

const ACCESS_TOKEN_KEY = "eureka_access_token";
const REFRESH_TOKEN_KEY = "eureka_refresh_token";
const USER_KEY = "eureka_user";
const ACCESS_COOKIE = "eureka_access_token";

function persistSession(payload: AuthPayload): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, payload.tokens.access_token);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, payload.tokens.refresh_token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(payload.user));
  document.cookie = `${ACCESS_COOKIE}=${payload.tokens.access_token}; Path=/; Max-Age=3600; SameSite=Lax`;
}

function clearPersistedSession(): void {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
  document.cookie = `${ACCESS_COOKIE}=; Max-Age=0; Path=/; SameSite=Lax`;
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  user: null,
  token: null,

  login: async (email: string, password: string): Promise<void> => {
    const response = await api.post<AuthApiResponse>("/api/v1/auth/login", {
      email,
      password,
    });

    const authData = response.data.data;
    persistSession(authData);

    set({
      user: authData.user,
      token: authData.tokens.access_token,
    });
  },

  register: async (email: string, password: string, role: UserRole = "merchandiser"): Promise<void> => {
    const response = await api.post<AuthApiResponse>("/api/v1/auth/register", {
      email,
      password,
      role,
    });

    const authData = response.data.data;
    persistSession(authData);

    set({
      user: authData.user,
      token: authData.tokens.access_token,
    });
  },

  logout: (): void => {
    clearPersistedSession();
    set({ user: null, token: null });
  },

  refreshToken: async (): Promise<void> => {
    const refreshToken = window.localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!refreshToken) {
      get().logout();
      return;
    }

    const response = await api.post<AuthApiResponse, { data: AuthApiResponse }, RefreshRequest>(
      "/api/v1/auth/refresh",
      { refresh_token: refreshToken },
    );

    const authData = response.data.data;
    persistSession(authData);
    set({ user: authData.user, token: authData.tokens.access_token });
  },

  initializeAuth: (): void => {
    if (typeof window === "undefined") {
      return;
    }

    const token = window.localStorage.getItem(ACCESS_TOKEN_KEY);
    const user = window.localStorage.getItem(USER_KEY);

    if (!token || !user) {
      return;
    }

    set({
      token,
      user: JSON.parse(user) as User,
    });
  },
}));
