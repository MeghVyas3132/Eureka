"use client";

interface DataFreshnessIndicatorProps {
  lastUpdated: string | null;
  onRefresh?: () => void;
}

export default function DataFreshnessIndicator({ lastUpdated, onRefresh }: DataFreshnessIndicatorProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-ink/10 bg-white/90 p-4 shadow">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] text-ink/50">Sales data freshness</p>
        <p className="mt-2 text-sm text-ink/70">
          {lastUpdated ? `Last updated: ${lastUpdated}` : "No sales data uploaded yet."}
        </p>
        <p className="mt-1 text-xs text-ink/50">Data is static until you import or enter new sales records.</p>
      </div>
      {onRefresh ? (
        <button
          type="button"
          onClick={onRefresh}
          className="rounded-full border border-ink/20 px-4 py-2 text-xs font-semibold text-ink transition hover:border-ink/40"
        >
          Refresh
        </button>
      ) : null}
    </div>
  );
}
