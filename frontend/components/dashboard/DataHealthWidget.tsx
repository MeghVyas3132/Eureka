"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import type { Planogram, PlanogramListResponse } from "@/types/planogram";

interface DataHealthWidgetProps {
  storeId: string;
  storeName: string;
}

interface HealthMetrics {
  sales: number;
  dimensions: number;
  categories: number;
  tier: string;
  planogramId: string;
}

const NEEDS_ATTENTION_THRESHOLD = 50;

function HealthBar({ label, value }: { label: string; value: number }) {
  const pct = Math.max(0, Math.min(100, value));
  const color = pct >= 75 ? "bg-emerald-500" : pct >= 45 ? "bg-amber-500" : "bg-rose-500";
  return (
    <div className="flex items-center gap-2 text-[11px] text-ink/70">
      <span className="w-20 shrink-0">{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-ink/10">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-9 shrink-0 text-right font-mono">{pct.toFixed(0)}%</span>
    </div>
  );
}

export default function DataHealthWidget({ storeId, storeName }: DataHealthWidgetProps) {
  const router = useRouter();
  const [metrics, setMetrics] = useState<HealthMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const response = await api.get<PlanogramListResponse>(
          `/api/v1/planograms?store_id=${storeId}`,
        );
        if (cancelled) return;
        const latest: Planogram | undefined = response.data.data[0];
        if (!latest) {
          setMetrics(null);
          return;
        }
        const confidence = latest.planogram_json?.confidence;
        if (!confidence) {
          setMetrics(null);
          return;
        }
        setMetrics({
          sales: Number(confidence.sales_coverage_pct) || 0,
          dimensions: Number(confidence.dimension_coverage_pct) || 0,
          categories: Number(confidence.category_coverage_pct) || 0,
          tier: String(confidence.tier ?? "unknown").toLowerCase(),
          planogramId: latest.id,
        });
      } catch (err) {
        if (!cancelled) setMetrics(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [storeId]);

  const needsAttention =
    metrics &&
    (metrics.sales < NEEDS_ATTENTION_THRESHOLD ||
      metrics.dimensions < NEEDS_ATTENTION_THRESHOLD ||
      metrics.categories < NEEDS_ATTENTION_THRESHOLD);

  return (
    <div className="rounded-2xl border border-ink/10 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-ink">{storeName}</p>
          <p className="text-[11px] uppercase tracking-wider text-ink/50">Data health</p>
        </div>
        <button
          type="button"
          onClick={() => router.push(`/stores/${storeId}/planogram/latest`)}
          className="rounded-full border border-ink/15 px-2.5 py-0.5 text-[11px] font-semibold text-ink/70 transition hover:border-ink/30"
        >
          Open
        </button>
      </div>

      <div className="mt-3 space-y-1.5">
        {loading ? (
          <p className="text-[11px] text-ink/50">Checking...</p>
        ) : metrics ? (
          <>
            <HealthBar label="Sales data" value={metrics.sales} />
            <HealthBar label="Dimensions" value={metrics.dimensions} />
            <HealthBar label="Categories" value={metrics.categories} />
            <p className="pt-1 text-[10px] uppercase tracking-wider text-ink/50">
              Confidence: <span className="font-semibold text-ink/80">{metrics.tier}</span>
            </p>
          </>
        ) : (
          <p className="text-[11px] text-ink/50">No planogram generated yet.</p>
        )}
      </div>

      {needsAttention ? (
        <button
          type="button"
          onClick={() => router.push(`/stores/${storeId}/data`)}
          className="mt-3 w-full rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-[11px] font-semibold text-amber-900 transition hover:bg-amber-100"
        >
          Improve data →
        </button>
      ) : null}
    </div>
  );
}
