"use client";

import { create } from "zustand";

import { api } from "@/lib/api";

type UserRole = "admin" | "merchandiser" | "merchandiser-pro" | "enterprise";
type SubscriptionTier = "admin" | "individual-plus" | "individual-pro" | "enterprise";
type SignupRole = "merchandiser" | "merchandiser-pro" | "enterprise";
type ApprovalStatus = "pending" | "approved" | "rejected";

export interface User {
  id: string;
  first_name: string;
  last_name: string;
  username: string;
  email: string;
  company_name: string | null;
  phone_number: string | null;
  role: UserRole;
  subscription_tier: SubscriptionTier;
  approval_status: ApprovalStatus;
  created_at: string;
}

export interface RegisterPayload {
  first_name: string;
  last_name: string;
  username: string;
  email: string;
  company_name?: string;
  phone_number: string;
  password: string;
  role?: SignupRole;
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

interface RegisterResponsePayload {
  user: User;
  requires_admin_approval: boolean;
}

interface AuthApiResponse {
  data: AuthPayload;
  message: string;
}

interface RegisterApiResponse {
  data: RegisterResponsePayload;
  message: string;
}

interface RefreshRequest {
  refresh_token: string;
}

interface AuthStore {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<User>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  initializeAuth: () => void;
}

const ACCESS_TOKEN_KEY = "eureka_access_token";
const REFRESH_TOKEN_KEY = "eureka_refresh_token";
const USER_KEY = "eureka_user";
const ACCESS_COOKIE = "eureka_access_token";

export function getPostLoginRoute(user: Pick<User, "role">): "/super-admin" | "/dashboard" {
  return user.role === "admin" ? "/super-admin" : "/dashboard";
}

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

  login: async (email: string, password: string): Promise<User> => {
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

    return authData.user;
  },

  register: async (payload: RegisterPayload): Promise<void> => {
    await api.post<RegisterApiResponse>("/api/v1/auth/register", {
      ...payload,
      role: payload.role ?? "merchandiser",
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
