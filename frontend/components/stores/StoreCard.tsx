"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

export type StoreType = "supermarket" | "convenience" | "specialty";

export interface StoreCardData {
  id: string;
  name: string;
  store_type: StoreType;
  width_m: number;
  height_m: number;
  created_at: string;
}

interface StoreCardProps {
  store: StoreCardData;
  onRename: (storeId: string, name: string) => Promise<void>;
  onDelete: (storeId: string) => Promise<void>;
}

const TYPE_LABELS: Record<StoreType, string> = {
  supermarket: "Supermarket",
  convenience: "Convenience",
  specialty: "Specialty",
};

const TYPE_STYLES: Record<StoreType, string> = {
  supermarket: "bg-pine/10 text-pine",
  convenience: "bg-amber-100 text-amber-700",
  specialty: "bg-teal-100 text-teal-700",
};

export default function StoreCard({ store, onRename, onDelete }: StoreCardProps) {
  const router = useRouter();
  const [busyAction, setBusyAction] = useState<"rename" | "delete" | null>(null);

  const createdLabel = useMemo(() => {
    const date = new Date(store.created_at);
    if (Number.isNaN(date.getTime())) {
      return "Created recently";
    }
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    }).format(date);
  }, [store.created_at]);

  const handleRename = async () => {
    const nextName = window.prompt("Rename store", store.name);
    if (!nextName || nextName.trim() === store.name) {
      return;
    }
    setBusyAction("rename");
    try {
      await onRename(store.id, nextName.trim());
    } catch {
      window.alert("Unable to rename store.");
    } finally {
      setBusyAction(null);
    }
  };

  const handleDelete = async () => {
    const shouldDelete = window.confirm("Delete this store and all its layouts?");
    if (!shouldDelete) {
      return;
    }
    setBusyAction("delete");
    try {
      await onDelete(store.id);
    } catch {
      window.alert("Unable to delete store.");
    } finally {
      setBusyAction(null);
    }
  };

  return (
    <article className="group flex h-full flex-col justify-between rounded-2xl border border-ink/10 bg-white/85 p-5 shadow-sm transition hover:-translate-y-1 hover:border-pine/30 hover:shadow-lg">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-ink/50">Store</p>
          <h3 className="mt-2 text-xl font-semibold text-ink">{store.name}</h3>
        </div>
        <details className="relative">
          <summary className="flex h-8 w-8 cursor-pointer list-none items-center justify-center rounded-full text-ink/70 transition hover:bg-ink/5">
            ...
          </summary>
          <div className="absolute right-0 z-10 mt-2 w-36 rounded-xl border border-ink/10 bg-white p-2 text-sm shadow-lg">
            <button
              type="button"
              onClick={handleRename}
              disabled={busyAction === "rename"}
              className="w-full rounded-lg px-3 py-2 text-left text-ink transition hover:bg-ink/5"
            >
              {busyAction === "rename" ? "Renaming..." : "Rename"}
            </button>
            <button
              type="button"
              onClick={handleDelete}
              disabled={busyAction === "delete"}
              className="mt-1 w-full rounded-lg px-3 py-2 text-left text-red-600 transition hover:bg-red-50"
            >
              {busyAction === "delete" ? "Deleting..." : "Delete"}
            </button>
          </div>
        </details>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${TYPE_STYLES[store.store_type]}`}>
          {TYPE_LABELS[store.store_type]}
        </span>
        <span className="text-sm text-ink/70">
          {store.width_m}m x {store.height_m}m
        </span>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-ink/60">
        <span>Created {createdLabel}</span>
        <button
          type="button"
          onClick={() => router.push(`/store/${store.id}/layout`)}
          className="font-semibold text-pine transition hover:text-pine/80"
        >
          Open Layout {"->"}
        </button>
      </div>
    </article>
  );
}
