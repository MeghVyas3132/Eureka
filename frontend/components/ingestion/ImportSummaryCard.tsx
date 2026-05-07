"use client";

import { useMemo, useState } from "react";

import type { ImportSummaryResponse } from "./types";

interface ImportSummaryCardProps {
  summary: ImportSummaryResponse;
  onDismiss: () => void;
  onViewErrors?: () => void;
}

const STATUS_STYLES: Record<ImportSummaryResponse["status"], string> = {
  completed: "bg-green-100 text-green-700",
  partial: "bg-yellow-100 text-yellow-800",
  failed: "bg-red-100 text-red-700",
};

export default function ImportSummaryCard({ summary, onDismiss, onViewErrors }: ImportSummaryCardProps) {
  const [showErrors, setShowErrors] = useState(false);
  const [showDuplicates, setShowDuplicates] = useState(false);

  const statusLabel = useMemo(() => {
    if (summary.status === "completed") {
      return "Completed";
    }
    if (summary.status === "partial") {
      return "Partial";
    }
    return "Failed";
  }, [summary.status]);

  const handleToggleErrors = () => {
    const next = !showErrors;
    setShowErrors(next);
    if (next && onViewErrors) {
      onViewErrors();
    }
  };

  return (
    <section className="rounded-2xl border border-ink/10 bg-white/95 p-6 shadow">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-ink/50">Import summary</p>
          <h3 className="mt-2 text-xl font-semibold text-ink">{summary.original_filename}</h3>
          <p className="mt-1 text-xs text-ink/60">Format: {summary.file_format.toUpperCase()}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`rounded-full px-3 py-1 text-xs font-semibold ${STATUS_STYLES[summary.status]}`}>
            {statusLabel}
          </span>
          <button
            type="button"
            onClick={onDismiss}
            className="rounded-full border border-ink/15 px-3 py-1 text-xs text-ink/70 hover:border-ink/30"
          >
            Dismiss
          </button>
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-ink/10 bg-ink/5 p-3">
          <p className="text-xs text-ink/60">Total rows</p>
          <p className="text-lg font-semibold text-ink">{summary.total_rows}</p>
        </div>
        <div className="rounded-xl border border-ink/10 bg-ink/5 p-3">
          <p className="text-xs text-ink/60">Imported</p>
          <p className="text-lg font-semibold text-ink">{summary.success}</p>
        </div>
        <div className="rounded-xl border border-ink/10 bg-ink/5 p-3">
          <p className="text-xs text-ink/60">Errors</p>
          <p className="text-lg font-semibold text-ink">{summary.errors.length}</p>
        </div>
      </div>

      {summary.period_start && summary.period_end ? (
        <div className="mt-4 rounded-xl border border-ink/10 bg-white px-4 py-3 text-sm text-ink/70">
          Period: {summary.period_start} to {summary.period_end}
        </div>
      ) : null}

      {summary.unmatched_skus && summary.unmatched_skus.length > 0 ? (
        <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {summary.unmatched_skus.length} SKUs did not match your product catalog. Sales data was imported but
          will not appear in planogram analytics until products are added.
        </div>
      ) : null}

      {summary.potential_duplicates && summary.potential_duplicates.length > 0 ? (
        <div className="mt-4 rounded-xl border border-yellow-300 bg-yellow-50 px-4 py-3 text-sm text-yellow-900">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="font-semibold">
              Possible Duplicate Products Detected ({summary.potential_duplicates.length})
            </p>
            <button
              type="button"
              onClick={() => setShowDuplicates((prev) => !prev)}
              className="text-xs font-semibold text-yellow-900 underline decoration-yellow-700 underline-offset-2"
            >
              {showDuplicates ? "Hide details" : "Review details"}
            </button>
          </div>
          <p className="mt-1 text-xs text-yellow-800">
            These SKUs may refer to the same product. Review manually before downstream planning.
          </p>
          {showDuplicates ? (
            <div className="mt-3 max-h-64 overflow-auto rounded-xl border border-yellow-200 bg-white">
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 bg-yellow-100 text-xs uppercase tracking-widest text-yellow-800">
                  <tr>
                    <th className="px-3 py-2">Existing</th>
                    <th className="px-3 py-2">Imported</th>
                    <th className="px-3 py-2">Match %</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.potential_duplicates.map((duplicate) => (
                    <tr
                      key={`${duplicate.sku_a}-${duplicate.sku_b}-${duplicate.row_b}`}
                      className="border-t border-yellow-100"
                    >
                      <td className="px-3 py-2 text-ink/80">
                        {duplicate.name_a} ({duplicate.sku_a})
                      </td>
                      <td className="px-3 py-2 text-ink/80">
                        {duplicate.name_b} ({duplicate.sku_b})
                      </td>
                      <td className="px-3 py-2 text-ink/80">{Math.round(duplicate.similarity)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </div>
      ) : null}

      {summary.errors.length > 0 ? (
        <div className="mt-4">
          <button
            type="button"
            onClick={handleToggleErrors}
            className="text-sm font-semibold text-pine hover:text-pine/80"
          >
            {showErrors ? "Hide errors" : "View errors"}
          </button>
          {showErrors ? (
            <div className="mt-3 max-h-64 overflow-auto rounded-xl border border-ink/10 bg-white">
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 bg-ink/5 text-xs uppercase tracking-widest text-ink/60">
                  <tr>
                    <th className="px-3 py-2">Row</th>
                    <th className="px-3 py-2">Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.errors.map((error) => (
                    <tr key={`${error.row}-${error.reason}`} className="border-t border-ink/10">
                      <td className="px-3 py-2 text-ink/70">{error.row}</td>
                      <td className="px-3 py-2 text-ink/80">{error.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
