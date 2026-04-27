"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import AuthCard from "@/components/auth/AuthCard";
import { getPostLoginRoute, useAuthStore } from "@/store/authStore";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuthStore();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"merchandiser" | "merchandiser-pro" | "enterprise">("merchandiser");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const createdUser = await register(username, email, password, role);
      router.push(getPostLoginRoute(createdUser));
    } catch (err) {
      setError("Unable to create your account. Try a different username or email.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <AuthCard
        title="Create Account"
        subtitle="Start building store layouts and tracking sales performance."
        ctaLabel="Register"
        footer={
          <>
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-pine underline-offset-4 hover:underline">
              Sign in
            </Link>
          </>
        }
        onSubmit={handleSubmit}
        loading={loading}
        error={error}
      >
        <div>
          <p className="mb-2 text-sm font-medium text-ink">Choose role</p>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            {[
              ["merchandiser", "Individual Plus"],
              ["merchandiser-pro", "Individual Pro"],
              ["enterprise", "Enterprise"],
            ].map(([value, label]) => {
              const active = role === value;
              return (
                <button
                  key={value}
                  type="button"
                  onClick={() => setRole(value as typeof role)}
                  className={`rounded-lg border px-3 py-2 text-sm font-semibold transition ${
                    active
                      ? "border-pine bg-pine text-white"
                      : "border-ink/20 bg-white text-ink hover:border-pine/60 hover:bg-pine/5"
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-ink" htmlFor="username">
            Username
          </label>
          <input
            id="username"
            type="text"
            required
            minLength={3}
            maxLength={64}
            pattern="^[A-Za-z0-9_]+$"
            placeholder="e.g. retail_user"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            className="w-full rounded-lg border border-ink/20 px-3 py-2 outline-none ring-pine/30 transition focus:ring"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-ink" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="w-full rounded-lg border border-ink/20 px-3 py-2 outline-none ring-pine/30 transition focus:ring"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-ink" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded-lg border border-ink/20 px-3 py-2 outline-none ring-pine/30 transition focus:ring"
          />
        </div>
      </AuthCard>
    </main>
  );
}
