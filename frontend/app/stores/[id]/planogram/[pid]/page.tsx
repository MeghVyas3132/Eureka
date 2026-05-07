"use client";

import axios from "axios";
import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import ConfidenceBadge from "@/components/planogram/ConfidenceBadge";
import DataQualityBanner from "@/components/planogram/DataQualityBanner";
import ExportMenu from "@/components/planogram/ExportMenu";
import FacingControls from "@/components/planogram/FacingControls";
import ProductPanel from "@/components/planogram/ProductPanel";
import RegenerateButton from "@/components/planogram/RegenerateButton";
import VersionHistoryPanel from "@/components/layout/VersionHistoryPanel";
import { api } from "@/lib/api";
import { ensurePlanogramForStore, isUuid } from "@/lib/planogramRouting";
import { usePlanogramStore } from "@/store/planogramStore";
import type { Planogram } from "@/types/planogram";

const PlanogramCanvas = dynamic(() => import("@/components/planogram/PlanogramCanvas"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center text-sm text-ink/60">Loading canvas...</div>
  ),
});

type ErrorAction = "create-store" | null;

export default function StorePlanogramPage() {
  const router = useRouter();
  const params = useParams();

  const storeId = String(params?.id ?? "");
  const planogramIdParam = String(params?.pid ?? "");

  const planogram = usePlanogramStore((state) => state.planogram);
  const isDirty = usePlanogramStore((state) => state.isDirty);
  const isSaving = usePlanogramStore((state) => state.isSaving);
  const setPlanogram = usePlanogramStore((state) => state.setPlanogram);
  const markSaving = usePlanogramStore((state) => state.markSaving);
  const markSaved = usePlanogramStore((state) => state.markSaved);
  const clearStore = usePlanogramStore((state) => state.clear);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [errorDetail, setErrorDetail] = useState("");
  const [errorAction, setErrorAction] = useState<ErrorAction>(null);
  const [isEditingName, setIsEditingName] = useState(false);
  const [nameDraft, setNameDraft] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [historyOpen, setHistoryOpen] = useState(false);

  useEffect(() => () => clearStore(), [clearStore]);

  const handleRequestError = useCallback((err: unknown, fallbackMessage: string) => {
    setErrorDetail("");
    setErrorAction(null);

    if (!axios.isAxiosError(err)) {
      setError(fallbackMessage);
      return;
    }

    const status = err.response?.status;
    const detail = err.response?.data?.detail;

    if (status === 404) {
      setError("Store or planogram not found for this account.");
      setErrorAction("create-store");
      return;
    }

    if (status === 422) {
      setError("This planogram link is invalid. Create a store first.");
      setErrorAction("create-store");
      return;
    }

    if (status === 403 && typeof detail === "object" && detail?.error === "quota_exceeded") {
      const message = detail?.detail?.message;
      setError(message || "Annual planogram limit reached for this account.");
      return;
    }

    const suffix = status ? ` (${status})` : "";
    setError(`${fallbackMessage}${suffix}`);
    if (detail) {
      setErrorDetail(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
  }, []);

  const loadPlanogram = useCallback(async () => {
    setLoading(true);
    setError("");
    setErrorDetail("");
    setErrorAction(null);

    if (!isUuid(storeId)) {
      setError("This store link is invalid. Create a store first.");
      setErrorAction("create-store");
      setLoading(false);
      return;
    }

    try {
      if (planogramIdParam === "latest") {
        const latest = await ensurePlanogramForStore(storeId);
        setPlanogram(latest);
        setNameDraft(latest.name);
        router.replace(`/stores/${storeId}/planogram/${latest.id}`);
        return;
      }

      if (!isUuid(planogramIdParam)) {
        setError("This planogram link is invalid. Create a store first.");
        setErrorAction("create-store");
        return;
      }

      const response = await api.get<Planogram>(`/api/v1/planograms/${planogramIdParam}`);
      if (response.data.store_id !== storeId) {
        setError("This planogram does not belong to the selected store.");
        setErrorAction("create-store");
        return;
      }

      setPlanogram(response.data);
      setNameDraft(response.data.name);
    } catch (err) {
      handleRequestError(err, "Unable to load planogram.");
    } finally {
      setLoading(false);
    }
  }, [handleRequestError, planogramIdParam, router, setPlanogram, storeId]);

  useEffect(() => {
    void loadPlanogram();
  }, [loadPlanogram]);

  useEffect(() => {
    if (!statusMessage) return;
    const timer = window.setTimeout(() => setStatusMessage(""), 2000);
    return () => window.clearTimeout(timer);
  }, [statusMessage]);

  const handleSave = useCallback(async () => {
    if (!planogram) return;
    markSaving(true);
    try {
      const response = await api.put<Planogram>(`/api/v1/planograms/${planogram.id}`, {
        name: nameDraft.trim() || planogram.name,
        planogram_json: planogram.planogram_json,
      });
      setPlanogram(response.data);
      setNameDraft(response.data.name);
      markSaved();
      setStatusMessage("Saved");
    } catch (err) {
      markSaving(false);
      handleRequestError(err, "Unable to save planogram.");
    }
  }, [handleRequestError, markSaved, markSaving, nameDraft, planogram, setPlanogram]);

  const handleNameBlur = async () => {
    if (!planogram) {
      setIsEditingName(false);
      return;
    }
    const trimmed = nameDraft.trim();
    setIsEditingName(false);
    if (!trimmed || trimmed === planogram.name) {
      setNameDraft(planogram.name);
      return;
    }
    try {
      const response = await api.put<Planogram>(`/api/v1/planograms/${planogram.id}`, {
        name: trimmed,
      });
      setPlanogram(response.data);
      setNameDraft(response.data.name);
      setStatusMessage("Saved");
    } catch (err) {
      handleRequestError(err, "Unable to save planogram name.");
    }
  };

  const handleRegenerated = (next: Planogram) => {
    setPlanogram(next);
    setNameDraft(next.name);
    setStatusMessage("Regenerated");
    router.replace(`/stores/${storeId}/planogram/${next.id}`);
  };

  const planogramJson = planogram?.planogram_json;
  const warnings = useMemo(() => planogramJson?.data_quality_warnings ?? [], [planogramJson]);
  const confidence = planogramJson?.confidence ?? null;
  const totalSkuCount = useMemo(
    () =>
      planogramJson?.shelves.reduce((sum, shelf) => sum + shelf.products.length, 0) ?? 0,
    [planogramJson],
  );

  const tier = (confidence?.tier ?? "").toLowerCase();
  const lowConfidenceBanner = tier === "low";

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_15%_20%,#f2e5c4_0%,#f6f7f8_45%,#eef2ef_100%)]">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-6 py-6">
        <header className="rounded-3xl border border-ink/10 bg-white/95 p-4 shadow">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <button
                type="button"
                onClick={() => router.push("/dashboard")}
                className="rounded-full border border-ink/20 px-4 py-2 text-sm text-ink/80 transition hover:border-ink/40"
              >
                {"← Dashboard"}
              </button>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-ink/50">
                  Planogram · {planogram?.generation_level ?? "store"}
                </p>
                {isEditingName ? (
                  <input
                    value={nameDraft}
                    onChange={(event) => setNameDraft(event.target.value)}
                    onBlur={handleNameBlur}
                    autoFocus
                    className="mt-2 w-full max-w-xs rounded-lg border border-ink/20 px-3 py-2 text-lg font-semibold text-ink outline-none focus:border-pine/50 focus:ring-2 focus:ring-pine/20"
                  />
                ) : (
                  <button
                    type="button"
                    onClick={() => setIsEditingName(true)}
                    className="mt-2 text-left text-xl font-semibold text-ink transition hover:text-pine"
                  >
                    {planogram?.name ?? "Planogram"}
                  </button>
                )}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <ConfidenceBadge confidence={confidence} />
              {planogram ? (
                <RegenerateButton
                  storeId={storeId}
                  generationLevel={planogram.generation_level}
                  shelfCount={planogram.shelf_count}
                  shelfWidthCm={planogram.shelf_width_cm}
                  shelfHeightCm={planogram.shelf_height_cm}
                  isUserEdited={planogram.is_user_edited}
                  isDirty={isDirty}
                  onGenerated={handleRegenerated}
                  onError={(message) => setError(message)}
                />
              ) : null}
              {statusMessage ? <span className="text-sm font-semibold text-pine">{statusMessage}</span> : null}
              <button
                type="button"
                disabled={!isDirty || !planogram || isSaving}
                onClick={() => void handleSave()}
                className="rounded-full bg-pine px-4 py-2 text-sm font-semibold text-white transition disabled:opacity-60"
              >
                {isSaving ? "Saving..." : "Save"}
              </button>
              <ExportMenu planogramId={planogram?.id ?? null} disabled={isDirty} />
              <button
                type="button"
                onClick={() => setHistoryOpen(true)}
                disabled={!planogram}
                className="rounded-full border border-ink/20 px-4 py-2 text-sm font-semibold text-ink/80 transition hover:border-ink/40"
              >
                History
              </button>
            </div>
          </div>
        </header>

        {lowConfidenceBanner ? (
          <div className="rounded-2xl border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-900">
            <strong>Draft only.</strong> This planogram has low data quality. Improve the inputs flagged
            below before relying on it.
          </div>
        ) : null}

        {warnings.length > 0 ? <DataQualityBanner warnings={warnings} /> : null}

        {error ? (
          <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
            <p>{error}</p>
            {errorDetail ? <p className="mt-1 text-xs text-red-600">{errorDetail}</p> : null}
            {errorAction === "create-store" ? (
              <button
                type="button"
                onClick={() => router.push("/stores/new/planogram")}
                className="mt-3 rounded-full bg-pine px-3 py-1 text-xs font-semibold text-white"
              >
                Create store
              </button>
            ) : null}
          </div>
        ) : null}

        <div className="grid gap-4 lg:grid-cols-[260px_1fr_260px]">
          <aside className="flex flex-col gap-4">
            <ProductPanel />
          </aside>

          <section className="flex h-[640px] flex-col gap-3 rounded-3xl border border-ink/10 bg-white/95 p-4 shadow">
            {loading || !planogram ? (
              <div className="flex h-full items-center justify-center text-sm text-ink/60">
                Loading planogram...
              </div>
            ) : (
              <PlanogramCanvas />
            )}
          </section>

          <aside className="flex flex-col gap-4">
            <FacingControls />

            <div className="rounded-2xl border border-ink/10 bg-white p-4 text-xs text-ink/70 shadow-sm">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-ink/50">Summary</p>
              <ul className="mt-2 space-y-1">
                <li>
                  Shelves: <span className="font-semibold text-ink">{planogramJson?.shelf_config.shelf_count ?? 0}</span>
                </li>
                <li>
                  SKUs placed: <span className="font-semibold text-ink">{totalSkuCount}</span>
                </li>
                <li>
                  Method: <span className="font-semibold text-ink">{planogram?.generation_method ?? "—"}</span>
                </li>
                <li>
                  Store type:{" "}
                  <span className="font-semibold text-ink">
                    {planogramJson?.shelf_config.store_type ?? "unknown"}
                  </span>
                </li>
                {planogramJson?.assortment ? (
                  <li className="pt-1 text-[11px] text-ink/60">
                    {planogramJson.assortment.message}
                  </li>
                ) : null}
              </ul>

              <button
                type="button"
                onClick={() => router.push(`/stores/${storeId}/data`)}
                className="mt-3 w-full rounded-full border border-ink/20 px-3 py-1.5 text-[11px] font-semibold text-ink/80 transition hover:border-ink/40"
              >
                Manage Sales Data
              </button>
            </div>
          </aside>
        </div>
      </div>

      <VersionHistoryPanel
        planogramId={planogram?.id ?? null}
        isOpen={historyOpen}
        onClose={() => setHistoryOpen(false)}
        onRestored={(next) => {
          setPlanogram(next);
          setNameDraft(next.name);
          setStatusMessage("Restored");
        }}
      />
    </main>
  );
}
