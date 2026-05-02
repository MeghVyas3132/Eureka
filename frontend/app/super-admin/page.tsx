"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

type SuperAdminTab = "onboarding" | "users" | "limits";
type RequestFilter = "pending" | "approved" | "rejected" | "all";
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

type SuperAdminUserRow = {
  id: string;
  first_name: string;
  last_name: string;
  username: string;
  email: string;
  company_name: string | null;
  phone_number: string | null;
  role: "admin" | "merchandiser" | "merchandiser-pro" | "enterprise";
  subscription_tier: PlanTier;
  approval_status: "pending" | "approved" | "rejected";
  reviewed_at: string | null;
  review_note: string | null;
  created_at: string;
  layout_count: number;
};

type SuperAdminUsersResponse = {
  data: SuperAdminUserRow[];
  message: string;
};

const FILTERS: Array<{ key: RequestFilter; label: string }> = [
  { key: "pending", label: "Pending" },
  { key: "approved", label: "Approved" },
  { key: "rejected", label: "Rejected" },
  { key: "all", label: "All" },
];

const TABS: Array<{ key: SuperAdminTab; label: string }> = [
  { key: "onboarding", label: "Pilot Onboarding" },
  { key: "users", label: "Users Table" },
  { key: "limits", label: "Limits" },
];

const PLAN_LABELS: Record<PlanTier, string> = {
  admin: "Admin",
  "individual-plus": "Individual Plus",
  "individual-pro": "Individual Pro",
  enterprise: "Enterprise",
};

const ROLE_LABELS: Record<SuperAdminUserRow["role"], string> = {
  admin: "Admin",
  merchandiser: "Individual Plus",
  "merchandiser-pro": "Individual Pro",
  enterprise: "Enterprise",
};

const STATUS_STYLES: Record<SuperAdminUserRow["approval_status"], string> = {
  approved: "bg-green-100 text-green-700",
  pending: "bg-yellow-100 text-yellow-800",
  rejected: "bg-red-100 text-red-700",
};

function formatDate(value: string | null): string {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}

export default function SuperAdminPage() {
  const router = useRouter();
  const { initializeAuth, user, logout } = useAuthStore();

  const [activeTab, setActiveTab] = useState<SuperAdminTab>("onboarding");
  const [requestFilter, setRequestFilter] = useState<RequestFilter>("pending");

  const [onboardingRows, setOnboardingRows] = useState<SuperAdminUserRow[]>([]);
  const [usersRows, setUsersRows] = useState<SuperAdminUserRow[]>([]);
  const [loadingRows, setLoadingRows] = useState(false);
  const [rowsError, setRowsError] = useState("");
  const [actionUserId, setActionUserId] = useState<string | null>(null);

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

    const fetchRows = async () => {
      setLoadingRows(true);
      setRowsError("");
      try {
        const [onboardingResponse, usersResponse] = await Promise.all([
          api.get<SuperAdminUsersResponse>(`/api/v1/admin/onboarding/requests?status=${requestFilter}`),
          api.get<SuperAdminUsersResponse>("/api/v1/admin/users"),
        ]);
        setOnboardingRows(onboardingResponse.data.data);
        setUsersRows(usersResponse.data.data.filter((row) => row.role !== "admin"));
      } catch {
        setRowsError("Unable to fetch super admin data.");
      } finally {
        setLoadingRows(false);
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

    void fetchRows();
    void fetchPlanLimits();
  }, [router, requestFilter, user?.id, user?.role]);

  const requestsCountLabel = useMemo(() => `${onboardingRows.length} requests`, [onboardingRows.length]);

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
      updatePlanLimitField(record.tier, response.data.data);
      setPlanLimitMessage(`Saved limit for ${record.tier}.`);
    } catch {
      setPlanLimitsError(`Unable to save limit for ${record.tier}.`);
    } finally {
      setSavingTier(null);
    }
  };

  const reviewRequest = async (row: SuperAdminUserRow, status: "approved" | "rejected") => {
    setActionUserId(row.id);
    setRowsError("");
    try {
      await api.patch(`/api/v1/admin/onboarding/requests/${row.id}`, {
        status,
        review_note: status === "approved" ? "Approved by super admin." : "Rejected by super admin.",
      });
      const refreshed = await api.get<SuperAdminUsersResponse>(`/api/v1/admin/onboarding/requests?status=${requestFilter}`);
      setOnboardingRows(refreshed.data.data);
    } catch {
      setRowsError("Unable to review request.");
    } finally {
      setActionUserId(null);
    }
  };

  if (!user || user.role !== "admin") {
    return null;
  }

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-4">
      <header className="rounded-xl border border-slate-200 bg-white px-5 py-3 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm font-semibold text-slate-700">Super Admin</p>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-500">{user.first_name} {user.last_name}</span>
            <button
              type="button"
              onClick={() => {
                logout();
                router.push("/login");
              }}
              className="rounded-md border border-red-200 bg-red-50 px-3 py-1.5 text-sm font-semibold text-red-700 hover:bg-red-100"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <section className="mt-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center gap-2">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              className={`rounded-md px-3 py-1.5 text-sm font-semibold transition ${
                activeTab === tab.key
                  ? "bg-pink-600 text-white"
                  : "border border-slate-200 bg-white text-slate-700 hover:border-pink-300 hover:text-pink-600"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </section>

      {rowsError ? <p className="mt-4 rounded-md bg-red-100 px-3 py-2 text-sm text-red-700">{rowsError}</p> : null}

      {activeTab === "onboarding" ? (
        <section className="mt-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Super Admin · Pilot Onboarding</h1>
              <p className="mt-1 text-sm text-slate-600">
                Review brand signup applications. Approve to provision workspace, reject to dismiss request.
              </p>
            </div>
            <p className="text-sm font-medium text-slate-500">{requestsCountLabel}</p>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {FILTERS.map((filter) => (
              <button
                key={filter.key}
                type="button"
                onClick={() => setRequestFilter(filter.key)}
                className={`rounded-md px-3 py-1.5 text-xs font-semibold uppercase tracking-wide ${
                  requestFilter === filter.key
                    ? "bg-slate-900 text-white"
                    : "border border-slate-200 bg-slate-50 text-slate-600 hover:border-pink-300 hover:text-pink-700"
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>

          {loadingRows ? (
            <p className="mt-4 text-sm text-slate-600">Loading requests...</p>
          ) : (
            <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200">
              <table className="min-w-full border-collapse text-sm">
                <thead className="bg-slate-50">
                  <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-3 py-2">Brand</th>
                    <th className="px-3 py-2">Applicant</th>
                    <th className="px-3 py-2">Contact</th>
                    <th className="px-3 py-2">Submitted</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {onboardingRows.map((row) => (
                    <tr key={row.id} className="border-t border-slate-100">
                      <td className="px-3 py-3">
                        <p className="font-semibold text-slate-800">{row.company_name || "No company"}</p>
                        <p className="text-xs text-slate-500">user: {row.username}</p>
                      </td>
                      <td className="px-3 py-3">
                        <p className="font-semibold text-slate-800">{row.first_name} {row.last_name}</p>
                        <p className="text-xs text-slate-500">{row.email}</p>
                      </td>
                      <td className="px-3 py-3 text-slate-700">{row.phone_number || "-"}</td>
                      <td className="px-3 py-3 text-slate-700">{formatDate(row.created_at)}</td>
                      <td className="px-3 py-3">
                        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${STATUS_STYLES[row.approval_status]}`}>
                          {row.approval_status.toUpperCase()}
                        </span>
                        <p className="mt-1 text-xs text-slate-500">reviewed {formatDate(row.reviewed_at)}</p>
                      </td>
                      <td className="px-3 py-3">
                        {row.approval_status === "pending" ? (
                          <div className="flex gap-2">
                            <button
                              type="button"
                              disabled={actionUserId === row.id}
                              onClick={() => void reviewRequest(row, "approved")}
                              className="rounded-md bg-green-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-green-700 disabled:opacity-60"
                            >
                              Approve
                            </button>
                            <button
                              type="button"
                              disabled={actionUserId === row.id}
                              onClick={() => void reviewRequest(row, "rejected")}
                              className="rounded-md bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-700 disabled:opacity-60"
                            >
                              Reject
                            </button>
                          </div>
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      ) : null}

      {activeTab === "users" ? (
        <section className="mt-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-2xl font-bold text-slate-900">Users Table</h2>
          <p className="mt-1 text-sm text-slate-600">All registered users and profile details.</p>

          {loadingRows ? (
            <p className="mt-4 text-sm text-slate-600">Loading users...</p>
          ) : (
            <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200">
              <table className="min-w-full border-collapse text-sm">
                <thead className="bg-slate-50">
                  <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-3 py-2">First Name</th>
                    <th className="px-3 py-2">Last Name</th>
                    <th className="px-3 py-2">Username</th>
                    <th className="px-3 py-2">Email</th>
                    <th className="px-3 py-2">Phone</th>
                    <th className="px-3 py-2">Company</th>
                    <th className="px-3 py-2">Role</th>
                    <th className="px-3 py-2">Plan</th>
                    <th className="px-3 py-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {usersRows.map((row) => (
                    <tr key={row.id} className="border-t border-slate-100">
                      <td className="px-3 py-2">{row.first_name}</td>
                      <td className="px-3 py-2">{row.last_name}</td>
                      <td className="px-3 py-2">{row.username}</td>
                      <td className="px-3 py-2">{row.email}</td>
                      <td className="px-3 py-2">{row.phone_number || "-"}</td>
                      <td className="px-3 py-2">{row.company_name || "-"}</td>
                      <td className="px-3 py-2">{ROLE_LABELS[row.role]}</td>
                      <td className="px-3 py-2">{PLAN_LABELS[row.subscription_tier]}</td>
                      <td className="px-3 py-2">
                        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${STATUS_STYLES[row.approval_status]}`}>
                          {row.approval_status.toUpperCase()}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      ) : null}

      {activeTab === "limits" ? (
        <section className="mt-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-2xl font-bold text-slate-900">Limits</h2>
          <p className="mt-1 text-sm text-slate-600">Configure per-plan annual layout limits.</p>

          {planLimitsError ? <p className="mt-3 rounded bg-red-100 px-3 py-2 text-sm text-red-700">{planLimitsError}</p> : null}
          {planLimitMessage ? <p className="mt-3 rounded bg-green-100 px-3 py-2 text-sm text-green-700">{planLimitMessage}</p> : null}

          {loadingPlanLimits ? (
            <p className="mt-4 text-sm text-slate-600">Loading limits...</p>
          ) : (
            <div className="mt-4 space-y-3">
              {planLimits.map((record) => (
                <div key={record.tier} className="rounded-lg border border-slate-200 p-4">
                  <p className="text-sm font-semibold text-slate-800">{PLAN_LABELS[record.tier]}</p>
                  <div className="mt-2 flex flex-col gap-3 sm:flex-row sm:items-center">
                    <label className="flex items-center gap-2 text-sm text-slate-700">
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
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none ring-pink-200 transition focus:ring sm:w-44"
                    />

                    <button
                      type="button"
                      onClick={() => void savePlanLimit(record)}
                      disabled={savingTier === record.tier}
                      className="rounded-lg bg-pink-600 px-4 py-2 text-sm font-semibold text-white hover:bg-pink-700 disabled:opacity-60"
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
    </main>
  );
}
