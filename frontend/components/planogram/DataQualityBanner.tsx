"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import type { PlanogramQualityWarning } from "@/types/planogram";

interface DataQualityBannerProps {
  warnings: PlanogramQualityWarning[];
}

const SEVERITY_RANK: Record<string, number> = { high: 0, medium: 1, low: 2 };

const SEVERITY_STYLES: Record<string, { container: string; chip: string; label: string }> = {
  high: {
    container: "border-rose-300 bg-rose-50",
    chip: "bg-rose-200 text-rose-900",
    label: "Action Required",
  },
  medium: {
    container: "border-amber-300 bg-amber-50",
    chip: "bg-amber-200 text-amber-900",
    label: "Heads Up",
  },
  low: {
    container: "border-slate-200 bg-slate-50",
    chip: "bg-slate-200 text-slate-700",
    label: "FYI",
  },
};

export default function DataQualityBanner({ warnings }: DataQualityBannerProps) {
  const router = useRouter();
  const [dismissedCodes, setDismissedCodes] = useState<Set<string>>(() => new Set());

  const sorted = useMemo(
    () =>
      [...warnings].sort(
        (a, b) =>
          (SEVERITY_RANK[a.severity?.toLowerCase()] ?? 9) -
          (SEVERITY_RANK[b.severity?.toLowerCase()] ?? 9),
      ),
    [warnings],
  );

  const visible = useMemo(
    () =>
      sorted.filter((warning) => {
        const severity = (warning.severity || "low").toLowerCase();
        if (severity === "high") {
          return true;
        }
        return !dismissedCodes.has(warning.code);
      }),
    [sorted, dismissedCodes],
  );

  if (visible.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      {visible.map((warning) => {
        const severity = (warning.severity || "low").toLowerCase();
        const styles = SEVERITY_STYLES[severity] ?? SEVERITY_STYLES.low;
        const dismissible = severity !== "high";

        return (
          <div
            key={`${warning.code}-${warning.action_url}`}
            className={`flex items-start gap-3 rounded-2xl border px-4 py-3 ${styles.container}`}
          >
            <span
              className={`mt-0.5 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${styles.chip}`}
            >
              {styles.label}
            </span>
            <p className="flex-1 text-sm text-ink/90">{warning.message}</p>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => router.push(warning.action_url)}
                className="rounded-full border border-ink/20 bg-white px-3 py-1 text-xs font-semibold text-ink transition hover:border-ink/40"
              >
                {warning.action_label || "Fix"}
              </button>
              {dismissible ? (
                <button
                  type="button"
                  onClick={() =>
                    setDismissedCodes((prev) => {
                      const next = new Set(prev);
                      next.add(warning.code);
                      return next;
                    })
                  }
                  className="text-xs text-ink/50 hover:text-ink"
                  aria-label="Dismiss"
                >
                  ✕
                </button>
              ) : null}
            </div>
          </div>
        );
      })}
    </div>
  );
}
