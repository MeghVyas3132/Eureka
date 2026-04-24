import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = window.localStorage.getItem("eureka_access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (typeof window !== "undefined" && error?.response?.status === 401) {
      window.localStorage.removeItem("eureka_access_token");
      window.localStorage.removeItem("eureka_refresh_token");
      window.localStorage.removeItem("eureka_user");
      document.cookie = "eureka_access_token=; Max-Age=0; Path=/; SameSite=Lax";
      window.location.href = "/login";
    }

    return Promise.reject(error);
  },
);
