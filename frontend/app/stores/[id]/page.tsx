"use client";

import axios from "axios";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { isUuid, listPlanogramsForStore } from "@/lib/planogramRouting";
import type { Planogram } from "@/types/planogram";

interface Store {
  id: string;
  raw_name: string;
  display_name: string | null;
  country: string | null;
  state: string | null;
  city: string | null;
  locality: string | null;
  store_type: string | null;
  detected_chain: string | null;
  parse_confidence: number | null;
}

interface ProductListResponse {
  data: { id: string }[];
  total: number;
}

interface SalesListResponse {
  data: unknown[];
  total: number;
}

export default function StoreLandingPage() {
  const router = useRouter();
  const params = useParams();
  const storeId = String(params?.id ?? "");

  const [store, setStore] = useState<Store | null>(null);
  const [planograms, setPlanograms] = useState<Planogram[]>([]);
  const [productCount, setProductCount] = useState<number | null>(null);
  const [salesCount, setSalesCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [errorDetail, setErrorDetail] = useState("");

  const loadAll = useCallback(async () => {
    if (!isUuid(storeId)) {
      setError("This store link is invalid.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    setErrorDetail("");
    try {
      const [storeRes, productRes, salesRes, planogramList] = await Promise.all([
        api.get<Store>(`/api/v1/stores/${storeId}`),
        api.get<ProductListResponse>("/api/v1/products"),
        api.get<SalesListResponse>(`/api/v1/sales?store_id=${storeId}`),
        listPlanogramsForStore(storeId).catch(() => [] as Planogram[]),
      ]);
      setStore(storeRes.data);
      setProductCount(productRes.data.total ?? productRes.data.data?.length ?? 0);
      setSalesCount(salesRes.data.total ?? salesRes.data.data?.length ?? 0);
      setPlanograms(planogramList);
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response?.status === 404) {
        setError("Store not found for this account.");
      } else {
        setError("Unable to load store details.");
      }
    } finally {
      setLoading(false);
    }
  }, [storeId]);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError("");
    setErrorDetail("");
    try {
      const response = await api.post<Planogram>("/api/v1/planograms/generate", {
        store_id: storeId,
        generation_level: "store",
        force: planograms.length > 0,
      });
      router.push(`/stores/${storeId}/planogram/${response.data.id}`);
    } catch (err: unknown) {
      setGenerating(false);
      if (!axios.isAxiosError(err)) {
        setError("Unable to generate planogram.");
        return;
      }
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      if (status === 403 && typeof detail === "object" && detail?.error === "quota_exceeded") {
        const message = detail?.detail?.message ?? "Annual planogram limit reached for this account.";
        setError(message);
        return;
      }
      const fallback = `Unable to generate planogram${status ? ` (${status})` : ""}.`;
      setError(fallback);
      if (detail) {
        setErrorDetail(typeof detail === "string" ? detail : JSON.stringify(detail));
      }
    }
  };

  const canGenerate = useMemo(
    () => Boolean(store) && (productCount ?? 0) > 0,
    [productCount, store],
  );

  const latestPlanogram = planograms[0] ?? null;

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_15%_20%,#f2e5c4_0%,#f6f7f8_45%,#eef2ef_100%)]">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-6 py-8">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <button
            type="button"
            onClick={() => router.push("/dashboard")}
            className="rounded-full border border-ink/20 px-4 py-2 text-sm text-ink/80 transition hover:border-ink/40"
          >
            ← Dashboard
          </button>
          <button
            type="button"
            onClick={() => router.push(`/stores/${storeId}/data`)}
            className="rounded-full border border-ink/20 px-4 py-2 text-sm text-ink/80 transition hover:border-ink/40"
          >
            Manage data for this store
          </button>
        </header>

        {loading ? (
          <div className="rounded-3xl border border-ink/10 bg-white/95 p-12 text-center text-sm text-ink/60 shadow">
            Loading store...
          </div>
        ) : !store ? (
          <div className="rounded-3xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
            {error || "Store not available."}
          </div>
        ) : (
          <>
            <section className="rounded-3xl border border-ink/10 bg-white/95 p-6 shadow">
              <p className="text-xs uppercase tracking-[0.2em] text-ink/50">Store</p>
              <h1 className="mt-2 text-3xl font-bold text-ink">
                {store.display_name ?? store.raw_name}
              </h1>
              <p className="mt-2 text-sm text-ink/70">
                {[store.locality, store.city, store.state, store.country]
                  .filter(Boolean)
                  .join(", ") || "Location not parsed yet"}
              </p>
              <div className="mt-4 flex flex-wrap gap-2 text-xs">
                {store.store_type ? (
                  <span className="rounded-full bg-canvas/60 px-3 py-1 font-semibold text-ink/70">
                    {store.store_type}
                  </span>
                ) : null}
                {store.detected_chain ? (
                  <span className="rounded-full bg-canvas/60 px-3 py-1 font-semibold text-ink/70">
                    {store.detected_chain}
                  </span>
                ) : null}
                {store.parse_confidence !== null && store.parse_confidence !== undefined ? (
                  <span className="rounded-full bg-canvas/60 px-3 py-1 font-semibold text-ink/70">
                    Parse confidence: {Math.round((store.parse_confidence || 0) * 100)}%
                  </span>
                ) : null}
              </div>
            </section>

            <section className="rounded-3xl border border-ink/10 bg-white/95 p-8 shadow">
              <div className="grid gap-6 lg:grid-cols-[1fr_auto] lg:items-center">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-ink/50">AI Planogram</p>
                  <h2 className="mt-2 text-2xl font-bold text-ink">
                    Generate a planogram from your data
                  </h2>
                  <p className="mt-2 max-w-xl text-sm text-ink/70">
                    Eureka uses your products, sales, and store metadata to auto-build a shelf layout
                    optimised for this store type. You can edit the result on the canvas and export to
                    JPEG or PowerPoint.
                  </p>

                  <ul className="mt-4 space-y-1 text-sm text-ink/80">
                    <li>
                      Products in catalogue:{" "}
                      <span className="font-semibold">{productCount ?? "—"}</span>
                    </li>
                    <li>
                      Sales rows for this store:{" "}
                      <span className="font-semibold">{salesCount ?? "—"}</span>
                    </li>
                    <li>
                      Existing planograms:{" "}
                      <span className="font-semibold">{planograms.length}</span>
                    </li>
                  </ul>

                  {productCount !== null && productCount === 0 ? (
                    <p className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                      Upload at least one product before generating a planogram.{" "}
                      <button
                        type="button"
                        onClick={() => router.push("/upload")}
                        className="font-semibold underline"
                      >
                        Upload products →
                      </button>
                    </p>
                  ) : null}

                  {error ? (
                    <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                      <p>{error}</p>
                      {errorDetail ? <p className="mt-1 text-xs text-rose-600">{errorDetail}</p> : null}
                    </div>
                  ) : null}
                </div>

                <div className="flex flex-col items-stretch gap-3 lg:items-end">
                  <button
                    type="button"
                    onClick={() => void handleGenerate()}
                    disabled={!canGenerate || generating}
                    className="rounded-full bg-pine px-6 py-3 text-base font-semibold text-white shadow transition hover:bg-pine/90 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {generating
                      ? "Generating..."
                      : planograms.length > 0
                        ? "Regenerate AI Planogram"
                        : "Generate AI Planogram"}
                  </button>
                  {latestPlanogram ? (
                    <button
                      type="button"
                      onClick={() =>
                        router.push(`/stores/${storeId}/planogram/${latestPlanogram.id}`)
                      }
                      className="rounded-full border border-ink/20 px-4 py-2 text-sm font-semibold text-ink/80 transition hover:border-ink/40"
                    >
                      Open latest planogram →
                    </button>
                  ) : null}
                </div>
              </div>
            </section>

            {planograms.length > 0 ? (
              <section className="rounded-3xl border border-ink/10 bg-white/95 p-6 shadow">
                <h3 className="text-lg font-semibold text-ink">All planograms for this store</h3>
                <div className="mt-3 overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="text-left text-xs uppercase tracking-wider text-ink/50">
                        <th className="px-3 py-2">Name</th>
                        <th className="px-3 py-2">Method</th>
                        <th className="px-3 py-2">Edited</th>
                        <th className="px-3 py-2">Updated</th>
                        <th className="px-3 py-2"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {planograms.map((planogram) => (
                        <tr key={planogram.id} className="border-t border-ink/5 text-ink/80">
                          <td className="px-3 py-2 font-medium text-ink">{planogram.name}</td>
                          <td className="px-3 py-2">{planogram.generation_method}</td>
                          <td className="px-3 py-2">
                            {planogram.is_user_edited ? "Yes" : "No"}
                          </td>
                          <td className="px-3 py-2 text-xs text-ink/60">
                            {new Date(planogram.updated_at).toLocaleString()}
                          </td>
                          <td className="px-3 py-2 text-right">
                            <button
                              type="button"
                              onClick={() =>
                                router.push(`/stores/${storeId}/planogram/${planogram.id}`)
                              }
                              className="rounded-full border border-ink/15 px-3 py-1 text-xs font-semibold text-ink/80 hover:border-ink/30"
                            >
                              Open
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            ) : null}
          </>
        )}
      </div>
    </main>
  );
}
