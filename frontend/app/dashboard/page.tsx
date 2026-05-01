"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import NewStoreModal, { StoreRecord } from "@/components/stores/NewStoreModal";
import StoreCard, { StoreCardData } from "@/components/stores/StoreCard";

type PlanLimitRecord = {
  tier: "admin" | "individual-plus" | "individual-pro" | "enterprise";
  annual_planogram_limit: number | null;
  is_unlimited: boolean;
};

type PlanLimitsResponse = {
  data: PlanLimitRecord[];
  message: string;
};

type StoreListResponse = {
  data: StoreCardData[];
  total: number;
};

export default function DashboardPage() {
  const router = useRouter();
  const { initializeAuth, user, logout } = useAuthStore();
  const [planLimits, setPlanLimits] = useState<PlanLimitRecord[]>([]);
  const [loadingPlanLimits, setLoadingPlanLimits] = useState(false);
  const [planLimitsError, setPlanLimitsError] = useState("");
  const [savingTier, setSavingTier] = useState<string | null>(null);
  const [planLimitMessage, setPlanLimitMessage] = useState("");

  const [stores, setStores] = useState<StoreCardData[]>([]);
  const [loadingStores, setLoadingStores] = useState(false);
  const [storeError, setStoreError] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState("");

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  const showToast = (message: string) => {
    setToastMessage(message);
  };

  useEffect(() => {
    if (!toastMessage) {
      return;
    }
    const timer = window.setTimeout(() => setToastMessage(""), 3000);
    return () => window.clearTimeout(timer);
  }, [toastMessage]);

  const fetchStores = async () => {
    setLoadingStores(true);
    setStoreError("");
    try {
      const response = await api.get<StoreListResponse>("/api/v1/stores");
      setStores(response.data.data);
    } catch {
      setStoreError("Unable to load stores.");
    } finally {
      setLoadingStores(false);
    }
  };

  useEffect(() => {
    void fetchStores();
  }, []);

  useEffect(() => {
    if (user?.role !== "admin") {
      return;
    }

    const fetchPlanLimits = async () => {
      setLoadingPlanLimits(true);
      setPlanLimitsError("");
      try {
        const response = await api.get<PlanLimitsResponse>("/api/v1/admin/plan-limits");
        setPlanLimits(response.data.data);
      } catch {
        setPlanLimitsError("Unable to fetch plan limits.");
      } finally {
        setLoadingPlanLimits(false);
      }
    };

    void fetchPlanLimits();
  }, [user?.role]);

  const updatePlanLimitField = (tier: PlanLimitRecord["tier"], patch: Partial<PlanLimitRecord>) => {
    setPlanLimits((previous) => previous.map((record) => (record.tier === tier ? { ...record, ...patch } : record)));
  };

  const savePlanLimit = async (record: PlanLimitRecord) => {
    setSavingTier(record.tier);
    setPlanLimitsError("");
    setPlanLimitMessage("");
    try {
      const response = await api.patch<PlanLimitsResponse>(`/api/v1/admin/plan-limits/${record.tier}`, {
        annual_planogram_limit: record.annual_planogram_limit,
        is_unlimited: record.is_unlimited,
      });
      const updatedRecord = response.data.data as unknown as PlanLimitRecord;
      updatePlanLimitField(record.tier, updatedRecord);
      setPlanLimitMessage(`Saved limit for ${record.tier}.`);
    } catch {
      setPlanLimitsError(`Unable to save limit for ${record.tier}.`);
    } finally {
      setSavingTier(null);
    }
  };

  const handleStoreCreated = (store: StoreRecord) => {
    setStores((previous) => [store, ...previous]);
    showToast("Store created.");
  };

  const handleRename = async (storeId: string, name: string) => {
    const response = await api.put<StoreCardData>(`/api/v1/stores/${storeId}`, { name });
    setStores((previous) => previous.map((store) => (store.id === storeId ? response.data : store)));
    showToast("Store renamed.");
  };

  const handleDelete = async (storeId: string) => {
    await api.delete(`/api/v1/stores/${storeId}`);
    setStores((previous) => previous.filter((store) => store.id !== storeId));
    showToast("Store deleted.");
  };

  const storeCountLabel = useMemo(() => {
    if (stores.length === 0) {
      return "No stores yet";
    }
    return `${stores.length} store${stores.length === 1 ? "" : "s"}`;
  }, [stores.length]);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-6 p-8">
      <header className="rounded-3xl border border-pine/20 bg-white/90 p-6 shadow">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-ink/60">Eureka MVP</p>
            <h1 className="mt-3 text-3xl font-bold text-ink">Dashboard</h1>
            <p className="mt-2 text-sm text-ink/75">
              Signed in as <span className="font-semibold">{user?.email ?? "Unknown user"}</span>
            </p>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="rounded-xl bg-pine px-4 py-2 text-sm font-semibold text-white"
            >
              New Store
            </button>
            <button
              type="button"
              onClick={() => {
                logout();
                router.push("/login");
              }}
              className="rounded-xl border border-ink/30 px-4 py-2 text-sm font-semibold text-ink"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {toastMessage ? (
        <div className="rounded-2xl border border-pine/20 bg-white/90 px-4 py-3 text-sm text-pine shadow">
          {toastMessage}
        </div>
      ) : null}

      <section className="rounded-3xl border border-ink/10 bg-white/90 p-6 shadow">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-ink">Your stores</h2>
            <p className="mt-1 text-sm text-ink/60">{storeCountLabel}</p>
          </div>
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className="rounded-full border border-pine/30 px-4 py-2 text-sm font-semibold text-pine transition hover:bg-pine/10"
          >
            Create store
          </button>
        </div>

        {storeError ? <p className="mt-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{storeError}</p> : null}

        {loadingStores ? (
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map((item) => (
              <div key={item} className="h-44 animate-pulse rounded-2xl border border-ink/10 bg-ink/5" />
            ))}
          </div>
        ) : stores.length === 0 ? (
          <div className="mt-6 flex flex-col items-center justify-center rounded-2xl border border-dashed border-ink/20 bg-sand/40 px-6 py-12 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white shadow">
              <span className="text-2xl text-pine">+</span>
            </div>
            <h3 className="mt-4 text-lg font-semibold text-ink">Create your first store</h3>
            <p className="mt-2 text-sm text-ink/70">
              Add your store dimensions and type to start building layouts.
            </p>
            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="mt-4 rounded-xl bg-pine px-5 py-2 text-sm font-semibold text-white"
            >
              Create store
            </button>
          </div>
        ) : (
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {stores.map((store) => (
              <StoreCard
                key={store.id}
                store={store}
                onRename={handleRename}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </section>

      {user?.role === "admin" ? (
        <section className="rounded-3xl border border-ink/15 bg-white/90 p-6 shadow">
          <h2 className="text-lg font-semibold">Admin Plan Limits</h2>
          <p className="mt-2 text-sm text-ink/75">
            Configure annual planogram limits. Unlimited tiers ignore the numeric limit.
          </p>

          {planLimitsError ? <p className="mt-3 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{planLimitsError}</p> : null}
          {planLimitMessage ? (
            <p className="mt-3 rounded bg-green-50 px-3 py-2 text-sm text-green-700">{planLimitMessage}</p>
          ) : null}

          {loadingPlanLimits ? (
            <p className="mt-4 text-sm text-ink/70">Loading plan limits...</p>
          ) : (
            <div className="mt-4 space-y-3">
              {planLimits.map((record) => (
                <div key={record.tier} className="rounded-lg border border-ink/15 p-4">
                  <p className="text-sm font-semibold text-ink">{record.tier}</p>
                  <div className="mt-2 flex flex-col gap-3 sm:flex-row sm:items-center">
                    <label className="flex items-center gap-2 text-sm text-ink/80">
                      <input
                        type="checkbox"
                        checked={record.is_unlimited}
                        onChange={(event) =>
                          updatePlanLimitField(record.tier, {
                            is_unlimited: event.target.checked,
                            annual_planogram_limit: event.target.checked ? null : record.annual_planogram_limit ?? 1,
                          })
                        }
                      />
                      Unlimited
                    </label>

                    <input
                      aria-label={`${record.tier}-annual-limit`}
                      type="number"
                      min={1}
                      disabled={record.is_unlimited}
                      value={record.annual_planogram_limit ?? ""}
                      onChange={(event) => {
                        const parsed = Number.parseInt(event.target.value, 10);
                        updatePlanLimitField(record.tier, {
                          annual_planogram_limit: Number.isFinite(parsed) ? parsed : null,
                        });
                      }}
                      className="w-full rounded-lg border border-ink/20 px-3 py-2 text-sm outline-none ring-pine/30 transition focus:ring sm:w-44"
                    />

                    <button
                      type="button"
                      onClick={() => void savePlanLimit(record)}
                      disabled={savingTier === record.tier}
                      className="rounded-lg bg-pine px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
                    >
                      {savingTier === record.tier ? "Saving..." : "Save"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      ) : null}

      <NewStoreModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreated={handleStoreCreated}
      />
    </main>
  );
}
