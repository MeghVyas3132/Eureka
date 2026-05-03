"use client";

import { FormEvent, useState } from "react";

import { api } from "@/lib/api";

interface ManualSalesEntryProps {
  storeId: string;
}

export default function ManualSalesEntry({ storeId }: ManualSalesEntryProps) {
  const [sku, setSku] = useState("");
  const [unitsSold, setUnitsSold] = useState("");
  const [revenue, setRevenue] = useState("");
  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      await api.post("/api/v1/sales", {
        store_id: storeId,
        sku: sku.trim(),
        units_sold: unitsSold ? Number(unitsSold) : null,
        revenue: Number(revenue),
        period_start: periodStart,
        period_end: periodEnd,
      });
      setSuccess("Sales entry saved.");
      setSku("");
      setUnitsSold("");
      setRevenue("");
    } catch {
      setError("Unable to save sales entry. Please check the fields and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-2xl border border-ink/10 bg-white/95 p-6 shadow">
      <div>
        <p className="text-sm font-semibold text-ink">Manual sales entry</p>
        <p className="mt-1 text-xs text-ink/60">Enter a single SKU record for this store.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="text-sm text-ink/70">
          SKU
          <input
            type="text"
            required
            value={sku}
            onChange={(event) => setSku(event.target.value)}
            className="mt-2 w-full rounded-xl border border-ink/15 bg-white px-3 py-2 text-ink outline-none focus:border-pine/50 focus:ring-2 focus:ring-pine/20"
          />
        </label>
        <label className="text-sm text-ink/70">
          Units sold (optional)
          <input
            type="number"
            min={0}
            value={unitsSold}
            onChange={(event) => setUnitsSold(event.target.value)}
            className="mt-2 w-full rounded-xl border border-ink/15 bg-white px-3 py-2 text-ink outline-none focus:border-pine/50 focus:ring-2 focus:ring-pine/20"
          />
        </label>
      </div>

      <label className="text-sm text-ink/70">
        Revenue
        <input
          type="number"
          min={0}
          step="0.01"
          required
          value={revenue}
          onChange={(event) => setRevenue(event.target.value)}
          className="mt-2 w-full rounded-xl border border-ink/15 bg-white px-3 py-2 text-ink outline-none focus:border-pine/50 focus:ring-2 focus:ring-pine/20"
        />
      </label>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="text-sm text-ink/70">
          Period start
          <input
            type="date"
            required
            value={periodStart}
            onChange={(event) => setPeriodStart(event.target.value)}
            className="mt-2 w-full rounded-xl border border-ink/15 bg-white px-3 py-2 text-ink outline-none focus:border-pine/50 focus:ring-2 focus:ring-pine/20"
          />
        </label>
        <label className="text-sm text-ink/70">
          Period end
          <input
            type="date"
            required
            value={periodEnd}
            onChange={(event) => setPeriodEnd(event.target.value)}
            className="mt-2 w-full rounded-xl border border-ink/15 bg-white px-3 py-2 text-ink outline-none focus:border-pine/50 focus:ring-2 focus:ring-pine/20"
          />
        </label>
      </div>

      {error ? <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      {success ? <p className="rounded-lg bg-green-50 px-3 py-2 text-sm text-green-700">{success}</p> : null}

      <button
        type="submit"
        disabled={loading}
        className="rounded-full bg-pine px-4 py-2 text-sm font-semibold text-white transition hover:bg-pine/90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "Saving..." : "Save entry"}
      </button>
    </form>
  );
}
