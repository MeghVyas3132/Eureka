"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useAuthStore } from "@/store/authStore";

type PlanTier = "admin" | "individual-plus" | "individual-pro" | "enterprise";

type PlanInfo = {
  title: string;
  summary: string;
  highlights: string[];
};

const PLAN_LABELS: Record<PlanTier, string> = {
  admin: "Admin",
  "individual-plus": "Individual Plus",
  "individual-pro": "Individual Pro",
  enterprise: "Enterprise",
};

const ROLE_LABELS: Record<string, string> = {
  admin: "Admin",
  merchandiser: "Individual Plus",
  "merchandiser-pro": "Individual Pro",
  enterprise: "Enterprise",
};

const PLAN_DETAILS: Record<PlanTier, PlanInfo> = {
  admin: {
    title: "Admin Access",
    summary: "Full control of onboarding, users, and plan limits.",
    highlights: ["Manage approvals", "Configure plan limits", "Access all tenant data"],
  },
  "individual-plus": {
    title: "Individual Plus",
    summary: "Great for single stores getting started with layout and reporting.",
    highlights: ["Core layout builder", "Basic analytics", "Email support"],
  },
  "individual-pro": {
    title: "Individual Pro",
    summary: "Expanded capacity for growing retail teams and deeper reporting.",
    highlights: ["Advanced layout tools", "Priority analytics", "Faster approvals"],
  },
  enterprise: {
    title: "Enterprise",
    summary: "Tailored onboarding and higher scale for multi-site operations.",
    highlights: ["Custom onboarding", "Multi-store support", "Dedicated success"],
  },
};

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleDateString();
}

export default function AccountPage() {
  const router = useRouter();
  const { initializeAuth, user, logout } = useAuthStore();
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    initializeAuth();
    setInitialized(true);
  }, [initializeAuth]);

  const planLabel = useMemo(() => {
    if (!user) {
      return "Unknown";
    }
    return PLAN_LABELS[user.subscription_tier as PlanTier] ?? "Unknown";
  }, [user]);

  if (!initialized) {
    return null;
  }

  if (!user) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
        <section className="w-full max-w-lg rounded-2xl border border-ink/10 bg-white p-6 text-center shadow">
          <h1 className="text-2xl font-semibold text-ink">Account</h1>
          <p className="mt-2 text-sm text-ink/70">You need to sign in to view your account details.</p>
          <Link
            href="/login"
            className="mt-4 inline-flex items-center justify-center rounded-lg bg-pine px-4 py-2 text-sm font-semibold text-white"
          >
            Go to login
          </Link>
        </section>
      </main>
    );
  }

  const planInfo = PLAN_DETAILS[user.subscription_tier as PlanTier];

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-6 p-8">
      <header className="rounded-2xl border border-pine/20 bg-white/90 p-6 shadow">
        <p className="text-sm uppercase tracking-wide text-ink/60">Account</p>
        <h1 className="mt-2 text-3xl font-bold text-ink">Plan: {planLabel}</h1>
        <p className="mt-2 text-sm text-ink/75">{planInfo.summary}</p>
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => router.push("/dashboard")}
            className="rounded-lg border border-ink/30 px-4 py-2 text-sm font-semibold text-ink"
          >
            Back to dashboard
          </button>
          <button
            type="button"
            onClick={() => {
              logout();
              router.push("/login");
            }}
            className="rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-white"
          >
            Logout
          </button>
        </div>
      </header>

      <section className="grid gap-6 md:grid-cols-[1.2fr_1fr]">
        <div className="rounded-2xl border border-ink/15 bg-white/90 p-6 shadow">
          <h2 className="text-lg font-semibold text-ink">Plan highlights</h2>
          <p className="mt-1 text-sm text-ink/70">{planInfo.title}</p>
          <ul className="mt-4 space-y-2 text-sm text-ink/75">
            {planInfo.highlights.map((item) => (
              <li key={item} className="flex items-center gap-2">
                <span className="inline-flex h-1.5 w-1.5 rounded-full bg-pine" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-2xl border border-ink/15 bg-white/90 p-6 shadow">
          <h2 className="text-lg font-semibold text-ink">Your details</h2>
          <div className="mt-4 space-y-2 text-sm text-ink/75">
            <p>
              <span className="font-semibold text-ink">Name:</span> {user.first_name} {user.last_name}
            </p>
            <p>
              <span className="font-semibold text-ink">Email:</span> {user.email}
            </p>
            <p>
              <span className="font-semibold text-ink">Username:</span> {user.username}
            </p>
            <p>
              <span className="font-semibold text-ink">Company:</span> {user.company_name || "-"}
            </p>
            <p>
              <span className="font-semibold text-ink">Role:</span> {ROLE_LABELS[user.role] ?? user.role}
            </p>
            <p>
              <span className="font-semibold text-ink">Status:</span> {user.approval_status}
            </p>
            <p>
              <span className="font-semibold text-ink">Member since:</span> {formatDate(user.created_at)}
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
