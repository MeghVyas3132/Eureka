"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import axios from "axios";

import { api } from "@/lib/api";
import VersionHistoryPanel from "@/components/layout/VersionHistoryPanel";
import { useCanvasStore, type Layout } from "@/store/canvasStore";

interface LayoutListResponse {
  data: Layout[];
  total: number;
}

export default function StoreLayoutPage() {
  const router = useRouter();
  const params = useParams();
  const storeId = params?.id as string;

  const { layout, setLayout, clearCanvas, isDirty, markDirty, markSaved } = useCanvasStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [errorDetail, setErrorDetail] = useState("");
  const [errorAction, setErrorAction] = useState<"create-store" | null>(null);
  const [isEditingName, setIsEditingName] = useState(false);
  const [nameDraft, setNameDraft] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [historyOpen, setHistoryOpen] = useState(false);

  const handleRequestError = (err: unknown, fallbackMessage: string) => {
    setErrorDetail("");
    setErrorAction(null);

    if (!axios.isAxiosError(err)) {
      setError(fallbackMessage);
      return;
    }

    const status = err.response?.status;
    const detail = err.response?.data?.detail;

    if (status === 404) {
      setError("Store not found for this account.");
      setErrorAction("create-store");
      return;
    }

    if (status === 422) {
      setError("This store link is invalid. Create a store first.");
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
  };

  const loadLayout = async () => {
    setLoading(true);
    setError("");
    setErrorDetail("");
    setErrorAction(null);
    try {
      const response = await api.get<LayoutListResponse>(`/api/v1/layouts?store_id=${storeId}`);
      if (response.data.data.length > 0) {
        setLayout(response.data.data[0]);
        setNameDraft(response.data.data[0].name);
      } else {
        const created = await api.post<Layout>("/api/v1/layouts", {
          store_id: storeId,
          name: "Untitled Layout",
        });
        setLayout(created.data);
        setNameDraft(created.data.name);
      }
    } catch (err) {
      handleRequestError(err, "Unable to load layout.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!storeId) {
      return;
    }
    const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(storeId);
    if (!isUuid) {
      clearCanvas();
      setError("This store link is invalid. Create a store first.");
      setErrorAction("create-store");
      setLoading(false);
      return;
    }
    void loadLayout();
  }, [storeId, clearCanvas]);

  useEffect(() => {
    if (layout) {
      setNameDraft(layout.name);
    }
  }, [layout?.id]);

  useEffect(() => {
    if (!statusMessage) {
      return;
    }
    const timer = window.setTimeout(() => setStatusMessage(""), 2000);
    return () => window.clearTimeout(timer);
  }, [statusMessage]);

  const handleSave = async () => {
    if (!layout) {
      return;
    }
    try {
      const response = await api.put<Layout>(`/api/v1/layouts/${layout.id}`, {
        name: nameDraft.trim() || layout.name,
      });
      setLayout(response.data);
      markSaved();
      setStatusMessage("Saved");
    } catch (err) {
      handleRequestError(err, "Unable to save layout.");
    }
  };

  const handleNameBlur = async () => {
    if (!layout) {
      setIsEditingName(false);
      return;
    }
    const trimmed = nameDraft.trim();
    setIsEditingName(false);
    if (!trimmed || trimmed === layout.name) {
      setNameDraft(layout.name);
      markSaved();
      return;
    }
    try {
      const response = await api.put<Layout>(`/api/v1/layouts/${layout.id}`, { name: trimmed });
      setLayout(response.data);
      markSaved();
      setStatusMessage("Saved");
    } catch (err) {
      handleRequestError(err, "Unable to save layout name.");
    }
  };

  const handleNameChange = (value: string) => {
    setNameDraft(value);
    if (layout && value.trim() !== layout.name) {
      markDirty();
    }
  };

  const layoutTitle = useMemo(() => layout?.name ?? "Layout", [layout?.name]);

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_15%_20%,#f2e5c4_0%,#f6f7f8_45%,#eef2ef_100%)]">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-6">
        <header className="rounded-3xl border border-ink/10 bg-white/90 p-4 shadow">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <button
                type="button"
                onClick={() => router.push("/dashboard")}
                className="rounded-full border border-ink/20 px-4 py-2 text-sm text-ink/80 transition hover:border-ink/40"
              >
                {"<- Dashboard"}
              </button>

              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-ink/50">Layout</p>
                {isEditingName ? (
                  <input
                    value={nameDraft}
                    onChange={(event) => handleNameChange(event.target.value)}
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
                    {layoutTitle}
                  </button>
                )}
              </div>
            </div>

            <div className="flex items-center gap-3">
              {statusMessage ? (
                <span className="text-sm font-semibold text-pine">{statusMessage}</span>
              ) : null}
              <button
                type="button"
                disabled={!isDirty || !layout}
                onClick={() => void handleSave()}
                className="rounded-full bg-pine px-4 py-2 text-sm font-semibold text-white transition disabled:opacity-60"
              >
                Save
              </button>
              <button
                type="button"
                onClick={() => setHistoryOpen(true)}
                disabled={!layout}
                className="rounded-full border border-ink/20 px-4 py-2 text-sm font-semibold text-ink/80 transition hover:border-ink/40"
              >
                History
              </button>
            </div>
          </div>
        </header>

        {error ? (
          <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
            <p>{error}</p>
            {errorDetail ? <p className="mt-1 text-xs text-red-600">{errorDetail}</p> : null}
            {errorAction === "create-store" ? (
              <button
                type="button"
                onClick={() => router.push("/store/new/layout")}
                className="mt-3 rounded-full bg-pine px-3 py-1 text-xs font-semibold text-white"
              >
                Create store
              </button>
            ) : null}
          </div>
        ) : null}

        <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
          <aside className="rounded-3xl border border-ink/10 bg-white/90 p-6 shadow">
            <h3 className="text-sm font-semibold text-ink">Sidebar</h3>
            <p className="mt-2 text-sm text-ink/60">Tools and zone controls arrive in Sprint 3.</p>
          </aside>

          <section className="rounded-3xl border border-ink/10 bg-white/90 p-6 shadow">
            {loading ? (
              <div className="flex h-[420px] items-center justify-center text-sm text-ink/60">
                Loading layout...
              </div>
            ) : (
              <div className="flex h-[420px] flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-ink/20 bg-canvas/40">
                <p className="text-lg font-semibold text-ink">Canvas coming in Sprint 3</p>
                <p className="text-sm text-ink/60">Zones and shelves will render here.</p>
              </div>
            )}
          </section>
        </div>
      </div>

      <VersionHistoryPanel
        layoutId={layout?.id ?? null}
        isOpen={historyOpen}
        onClose={() => setHistoryOpen(false)}
        onRestored={(nextLayout) => {
          setLayout(nextLayout);
          markSaved();
          setStatusMessage("Restored");
        }}
      />
    </main>
  );
}
