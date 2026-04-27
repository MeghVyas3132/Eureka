"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

type PlanTier = "admin" | "individual-plus" | "individual-pro" | "enterprise";

type PlanLimitRecord = {
  tier: PlanTier;
  annual_planogram_limit: number | null;
  is_unlimited: boolean;
};

type PlanLimitsResponse = {
  data: PlanLimitRecord[];
  message: string;
};

type PlanLimitResponse = {
  data: PlanLimitRecord;
  message: string;
};

type AdminUserRecord = {
  id: string;
  username: string;
  email: string;
  role: "admin" | "merchandiser" | "merchandiser-pro" | "enterprise";
  subscription_tier: PlanTier;
  created_at: string;
  layout_count: number;
};

type AdminUsersResponse = {
  data: AdminUserRecord[];
  message: string;
};

const PLAN_LABELS: Record<PlanTier, string> = {
  admin: "Admin",
  "individual-plus": "Individual Plus",
  "individual-pro": "Individual Pro",
  enterprise: "Enterprise",
};

export default function AdminUsersPage() {
  const router = useRouter();
  const { initializeAuth, user, logout } = useAuthStore();
  const [users, setUsers] = useState<AdminUserRecord[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [usersError, setUsersError] = useState("");

  const [planLimits, setPlanLimits] = useState<PlanLimitRecord[]>([]);
  const [loadingPlanLimits, setLoadingPlanLimits] = useState(false);
  const [planLimitsError, setPlanLimitsError] = useState("");
  const [savingTier, setSavingTier] = useState<string | null>(null);
  const [planLimitMessage, setPlanLimitMessage] = useState("");

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  useEffect(() => {
    if (!user) {
      return;
    }
    if (user.role !== "admin") {
      router.replace("/dashboard");
      return;
    }

    const fetchUsers = async () => {
      setLoadingUsers(true);
      setUsersError("");
      try {
        const response = await api.get<AdminUsersResponse>("/api/v1/admin/users");
        setUsers(response.data.data);
      } catch {
        setUsersError("Unable to fetch users.");
      } finally {
        setLoadingUsers(false);
      }
    };

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

    void fetchUsers();
    void fetchPlanLimits();
  }, [router, user?.id, user?.role]);

  const updatePlanLimitField = (tier: PlanLimitRecord["tier"], patch: Partial<PlanLimitRecord>) => {
    setPlanLimits((previous) => previous.map((record) => (record.tier === tier ? { ...record, ...patch } : record)));
  };

  const savePlanLimit = async (record: PlanLimitRecord) => {
    setSavingTier(record.tier);
    setPlanLimitsError("");
    setPlanLimitMessage("");
    try {
      const response = await api.patch<PlanLimitResponse>(`/api/v1/admin/plan-limits/${record.tier}`, {
        annual_planogram_limit: record.annual_planogram_limit,
        is_unlimited: record.is_unlimited,
      });
      const updatedRecord = response.data.data;
      updatePlanLimitField(record.tier, updatedRecord);
      setPlanLimitMessage(`Saved limit for ${record.tier}.`);
    } catch {
      setPlanLimitsError(`Unable to save limit for ${record.tier}.`);
    } finally {
      setSavingTier(null);
    }
  };

  if (!user || user.role !== "admin") {
    return null;
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-6 p-8">
      <header className="rounded-2xl border border-pine/20 bg-white/90 p-6 shadow">
        <p className="text-sm uppercase tracking-wide text-ink/60">Eureka Admin</p>
        <h1 className="mt-2 text-3xl font-bold text-ink">Welcome, {user.username}</h1>
        <p className="mt-2 text-sm text-ink/75">Plan: {PLAN_LABELS[user.subscription_tier]}</p>
        <div className="mt-4 flex gap-3">
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
        <h2 className="text-lg font-semibold">User Database</h2>
        <p className="mt-2 text-sm text-ink/75">Admin-only view of usernames, emails, plans, and total layouts built.</p>

        {usersError ? <p className="mt-3 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{usersError}</p> : null}

        {loadingUsers ? (
          <p className="mt-4 text-sm text-ink/70">Loading users...</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-ink/15 text-left">
                  <th className="px-3 py-2 font-semibold text-ink">Username</th>
                  <th className="px-3 py-2 font-semibold text-ink">Email</th>
                  <th className="px-3 py-2 font-semibold text-ink">Plan</th>
                  <th className="px-3 py-2 font-semibold text-ink">Layouts Built</th>
                </tr>
              </thead>
              <tbody>
                {users.map((record) => (
                  <tr key={record.id} className="border-b border-ink/10">
                    <td className="px-3 py-2 text-ink">{record.username}</td>
                    <td className="px-3 py-2 text-ink">{record.email}</td>
                    <td className="px-3 py-2 text-ink">{PLAN_LABELS[record.subscription_tier]}</td>
                    <td className="px-3 py-2 text-ink">{record.layout_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="rounded-2xl border border-ink/15 bg-white/90 p-6 shadow">
        <h2 className="text-lg font-semibold">Admin Plan Limits</h2>
        <p className="mt-2 text-sm text-ink/75">
          Configure annual planogram limits. Unlimited tiers ignore the numeric limit.
        </p>

        {planLimitsError ? <p className="mt-3 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{planLimitsError}</p> : null}
        {planLimitMessage ? <p className="mt-3 rounded bg-green-50 px-3 py-2 text-sm text-green-700">{planLimitMessage}</p> : null}

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
    </main>
  );
}
