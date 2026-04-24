"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import AuthCard from "@/components/auth/AuthCard";
import { useAuthStore } from "@/store/authStore";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuthStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await register(email, password, "merchandiser");
      router.push("/dashboard");
    } catch (err) {
      setError("Unable to create your account. Try a different email.");
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
