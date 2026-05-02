"use client";

import { FormEvent, ReactNode } from "react";

interface AuthCardProps {
  title: string;
  subtitle: string;
  ctaLabel: string;
  footer: ReactNode;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  loading: boolean;
  error: string;
  children: ReactNode;
}

export default function AuthCard({
  title,
  subtitle,
  ctaLabel,
  footer,
  onSubmit,
  loading,
  error,
  children,
}: AuthCardProps) {
  return (
    <div className="w-full max-w-md rounded-2xl border border-pink-200/80 bg-white/95 p-8 shadow-xl backdrop-blur-sm">
      <h1 className="text-2xl font-bold text-ink">{title}</h1>
      <p className="mt-2 text-sm text-ink/70">{subtitle}</p>

      <form className="mt-6 space-y-4" onSubmit={onSubmit}>
        {children}

        {error ? (
          <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        ) : null}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-pink-600 px-4 py-2 font-semibold text-white shadow-sm transition hover:bg-pink-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pink-300 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Please wait..." : ctaLabel}
        </button>
      </form>

      <div className="mt-5 text-sm text-ink/80">{footer}</div>
    </div>
  );
}
