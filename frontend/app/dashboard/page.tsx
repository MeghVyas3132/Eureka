"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuthStore } from "@/store/authStore";
import NewStoreModal from "@/components/stores/NewStoreModal";

const PLAN_LABELS = {
  admin: "Admin",
  "individual-plus": "Individual Plus",
  "individual-pro": "Individual Pro",
  enterprise: "Enterprise",
} as const;

export default function DashboardPage() {
  const router = useRouter();
  const { initializeAuth, user, logout } = useAuthStore();
  const [isCreateStoreOpen, setIsCreateStoreOpen] = useState(false);

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  useEffect(() => {
    if (user?.role === "admin") {
      router.replace("/super-admin");
    }
  }, [router, user?.role]);

  const planLabel = user ? PLAN_LABELS[user.subscription_tier] : "Unknown";

  return (
    return (
      <>
        <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-6 p-8">
          <header className="rounded-2xl border border-pine/20 bg-white/90 p-6 shadow">
            <p className="text-sm uppercase tracking-wide text-ink/60">Eureka MVP</p>
            <h1 className="mt-2 text-3xl font-bold text-ink">Welcome, {user?.username ?? "there"}</h1>
            <p className="mt-2 text-sm text-ink/75">Plan: {planLabel}</p>
            <p className="mt-1 text-sm text-ink/75">
              Signed in as <span className="font-semibold">{user?.email ?? "Unknown user"}</span>
            </p>
            <div className="mt-4 flex gap-3">
              <button
                type="button"
                onClick={() => setIsCreateStoreOpen(true)}
                className="rounded-lg bg-pine px-4 py-2 text-sm font-semibold text-white"
              >
                Create Layout
              </button>
              <button
                type="button"
                onClick={() => router.push("/account")}
                className="rounded-lg border border-ink/30 px-4 py-2 text-sm font-semibold text-ink"
              >
                Account
              </button>
              <button
                type="button"
                onClick={() => {
                  logout();
                  router.push("/login");
                }}
                className="rounded-lg border border-ink/30 px-4 py-2 text-sm font-semibold text-ink"
              >
                Logout
              </button>
            </div>
          </header>

          <section className="rounded-2xl border border-ink/15 bg-white/90 p-6 shadow">
            <h2 className="text-lg font-semibold">Sprint 1 Status</h2>
            <p className="mt-2 text-sm text-ink/75">
              Authentication is connected end-to-end. Store CRUD and layout builder arrive in Sprint 2.
            </p>
          </section>
        </main>
        <NewStoreModal
          isOpen={isCreateStoreOpen}
          onClose={() => setIsCreateStoreOpen(false)}
          onCreated={(store) => router.push(`/store/${store.id}/layout`)}
        />
      </>
    );
  );
}
