"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import DataHealthWidget from "@/components/dashboard/DataHealthWidget";
import HierarchyTree, { type HierarchyStore } from "@/components/dashboard/HierarchyTree";
import NewStoreModal from "@/components/stores/NewStoreModal";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

const PLAN_LABELS = {
  admin: "Admin",
  "individual-plus": "Individual Plus",
  "individual-pro": "Individual Pro",
  enterprise: "Enterprise",
} as const;

interface StoreListResponse {
  data: HierarchyStore[];
  total: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const { initializeAuth, user, logout } = useAuthStore();
  const [isCreateStoreOpen, setIsCreateStoreOpen] = useState(false);
  const [isPreparingPlanogram, setIsPreparingPlanogram] = useState(false);
  const [stores, setStores] = useState<HierarchyStore[]>([]);
  const [storesLoading, setStoresLoading] = useState(false);
  const [selectedStoreId, setSelectedStoreId] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  useEffect(() => {
    if (user?.role === "admin") {
      router.replace("/super-admin");
    }
  }, [router, user?.role]);

  const loadStores = useCallback(async () => {
    setStoresLoading(true);
    setError("");
    try {
      const response = await api.get<StoreListResponse>("/api/v1/stores");
      const data = response.data.data ?? [];
      setStores(data);
      if (!selectedStoreId && data.length > 0) {
        setSelectedStoreId(data[0].id);
      }
    } catch (err) {
      setStores([]);
      setError("Unable to load stores.");
    } finally {
      setStoresLoading(false);
    }
  }, [selectedStoreId]);

  useEffect(() => {
    if (user && user.role !== "admin") {
      void loadStores();
    }
  }, [loadStores, user]);

  const handleStoreCreated = async (storeId: string) => {
    setIsPreparingPlanogram(true);
    try {
      router.push(`/stores/${storeId}`);
    } finally {
      setIsPreparingPlanogram(false);
    }
  };

  const planLabel = user ? PLAN_LABELS[user.subscription_tier] : "Unknown";

  const selectedStore = useMemo(
    () => stores.find((store) => store.id === selectedStoreId) ?? null,
    [selectedStoreId, stores],
  );

  return (
    <>
      <main className="min-h-screen bg-[radial-gradient(circle_at_15%_20%,#f2e5c4_0%,#f6f7f8_45%,#eef2ef_100%)]">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-8">
          <header className="rounded-3xl border border-ink/10 bg-white/95 p-6 shadow">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-ink/50">Dashboard</p>
                <h1 className="mt-2 text-3xl font-bold text-ink">
                  Welcome, {user?.first_name ?? user?.username ?? "there"}
                </h1>
                <p className="mt-1 text-sm text-ink/70">Plan: {planLabel}</p>
              </div>
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => router.push("/upload")}
                  className="rounded-full border border-ink/20 px-4 py-2 text-sm font-semibold text-ink/80 transition hover:border-ink/40"
                >
                  Upload Data
                </button>
                <button
                  type="button"
                  onClick={() => setIsCreateStoreOpen(true)}
                  disabled={isPreparingPlanogram}
                  className="rounded-full bg-pine px-4 py-2 text-sm font-semibold text-white"
                >
                  + New Store
                </button>
                <button
                  type="button"
                  onClick={() => router.push("/account")}
                  className="rounded-full border border-ink/20 px-4 py-2 text-sm font-semibold text-ink/80"
                >
                  Account
                </button>
                <button
                  type="button"
                  onClick={() => {
                    logout();
                    router.push("/login");
                  }}
                  className="rounded-full border border-ink/20 px-4 py-2 text-sm font-semibold text-ink/80"
                >
                  Logout
                </button>
              </div>
            </div>
          </header>

          <section className="rounded-3xl border border-ink/15 bg-white/95 p-6 shadow">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-ink">Store hierarchy</h2>
                <p className="text-xs text-ink/60">
                  Country → State → City → Locality. Click a store to open its planogram workspace.
                </p>
              </div>
              <span className="text-xs text-ink/60">
                {storesLoading
                  ? "Loading..."
                  : `${stores.length} ${stores.length === 1 ? "store" : "stores"}`}
              </span>
            </div>

            {error ? (
              <p className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                {error}
              </p>
            ) : null}

            <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(280px,1fr)_minmax(280px,1fr)]">
              <div className="max-h-[480px] overflow-y-auto">
                <HierarchyTree
                  stores={stores}
                  selectedStoreId={selectedStoreId}
                  onSelectStore={(storeId) => setSelectedStoreId(storeId)}
                />
              </div>

              <div className="space-y-3">
                {selectedStore ? (
                  <>
                    <div className="rounded-2xl border border-ink/10 bg-white p-4 shadow-sm">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="text-xs uppercase tracking-[0.2em] text-ink/50">Selected store</p>
                          <p className="mt-1 truncate text-base font-semibold text-ink">
                            {selectedStore.display_name ?? selectedStore.raw_name}
                          </p>
                          <p className="mt-1 text-xs text-ink/60">
                            {[
                              selectedStore.locality,
                              selectedStore.city,
                              selectedStore.state,
                              selectedStore.country,
                            ]
                              .filter(Boolean)
                              .join(", ") || "Location unknown"}
                          </p>
                          {selectedStore.store_type ? (
                            <p className="mt-1 text-xs text-ink/60">Type: {selectedStore.store_type}</p>
                          ) : null}
                        </div>
                        <button
                          type="button"
                          onClick={() => router.push(`/stores/${selectedStore.id}`)}
                          className="rounded-full bg-pine px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-pine/90"
                        >
                          Open store →
                        </button>
                      </div>
                    </div>

                    <DataHealthWidget
                      storeId={selectedStore.id}
                      storeName={selectedStore.display_name ?? selectedStore.raw_name}
                    />
                  </>
                ) : (
                  <div className="rounded-2xl border border-dashed border-ink/20 bg-white/60 p-6 text-sm text-ink/60">
                    Click a store in the hierarchy to see details and data health.
                  </div>
                )}
              </div>
            </div>
          </section>
        </div>
      </main>
      <NewStoreModal
        isOpen={isCreateStoreOpen}
        onClose={() => setIsCreateStoreOpen(false)}
        onCreated={(store) => void handleStoreCreated(store.id)}
      />
    </>
  );
}
