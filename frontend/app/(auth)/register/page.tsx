"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import AuthCard from "@/components/auth/AuthCard";
import { useAuthStore } from "@/store/authStore";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuthStore();

  type SignupRole = "merchandiser" | "merchandiser-pro" | "enterprise";

  const PLAN_OPTIONS: { id: SignupRole; label: string }[] = [
    { id: "merchandiser", label: "Individual Plus" },
    { id: "merchandiser-pro", label: "Individual Pro" },
    { id: "enterprise", label: "Enterprise" },
  ];

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [username, setUsername] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [selectedRole, setSelectedRole] = useState<SignupRole>("merchandiser");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await register({
        first_name: firstName,
        last_name: lastName,
        username,
        company_name: companyName,
        email,
        phone_number: phoneNumber,
        password,
        role: selectedRole,
      });
      router.push("/login?approval=pending");
    } catch (err) {
      setError("Unable to submit signup request. Try a different username or email.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
      <AuthCard
        title="Sign Up"
        subtitle="Register your workspace. Admin approval is required before first login."
        ctaLabel="Submit Request"
        footer={
          <>
            Already registered?{" "}
            <Link href="/login" className="font-semibold text-pink-600 underline-offset-4 hover:underline">
              Go to login
            </Link>
          </>
        }
        onSubmit={handleSubmit}
        loading={loading}
        error={error}
      >
        <div>
          <p className="text-sm font-medium text-ink">Choose role</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {PLAN_OPTIONS.map((option) => {
              const isSelected = option.id === selectedRole;
              return (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => setSelectedRole(option.id)}
                  aria-pressed={isSelected}
                  className={`rounded-lg border px-3 py-2 text-sm font-semibold transition ${
                    isSelected
                      ? "border-emerald-700 bg-emerald-700 text-white"
                      : "border-ink/20 bg-white text-ink hover:border-emerald-300"
                  }`}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-ink" htmlFor="firstName">
              First Name
            </label>
            <input
              id="firstName"
              type="text"
              required
              maxLength={80}
              value={firstName}
              onChange={(event) => setFirstName(event.target.value)}
              className="w-full rounded-lg border border-ink/20 px-3 py-2 outline-none ring-pink-200 transition focus:ring"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-ink" htmlFor="lastName">
              Last Name
            </label>
            <input
              id="lastName"
              type="text"
              required
              maxLength={80}
              value={lastName}
              onChange={(event) => setLastName(event.target.value)}
              className="w-full rounded-lg border border-ink/20 px-3 py-2 outline-none ring-pink-200 transition focus:ring"
            />
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
            className="w-full rounded-lg border border-ink/20 px-3 py-2 outline-none ring-pink-200 transition focus:ring"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-ink" htmlFor="companyName">
            Company Name
          </label>
          <input
            id="companyName"
            type="text"
            maxLength={160}
            value={companyName}
            onChange={(event) => setCompanyName(event.target.value)}
            className="w-full rounded-lg border border-ink/20 px-3 py-2 outline-none ring-pink-200 transition focus:ring"
          />
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
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
              className="w-full rounded-lg border border-ink/20 px-3 py-2 outline-none ring-pink-200 transition focus:ring"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-ink" htmlFor="phoneNumber">
              Phone Number
            </label>
            <input
              id="phoneNumber"
              type="tel"
              required
              minLength={7}
              maxLength={32}
              value={phoneNumber}
              onChange={(event) => setPhoneNumber(event.target.value)}
              className="w-full rounded-lg border border-ink/20 px-3 py-2 outline-none ring-pink-200 transition focus:ring"
            />
          </div>
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
            className="w-full rounded-lg border border-ink/20 px-3 py-2 outline-none ring-pink-200 transition focus:ring"
          />
        </div>
      </AuthCard>
    </main>
  );
}
