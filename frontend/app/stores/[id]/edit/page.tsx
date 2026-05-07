"use client";

import { useParams, useRouter } from "next/navigation";

export default function StoreEditPage() {
  const router = useRouter();
  const params = useParams();
  const storeId = String(params?.id ?? "");

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_20%_0%,#f2e5c4_0%,#f6f7f8_45%,#eef2ef_100%)] px-6 py-8">
      <div className="mx-auto max-w-3xl rounded-3xl border border-ink/10 bg-white/90 p-6 shadow">
        <p className="text-xs uppercase tracking-[0.2em] text-ink/50">Store details</p>
        <h1 className="mt-2 text-3xl font-bold text-ink">Store edit flow is next</h1>
        <p className="mt-2 text-sm text-ink/70">
          Store metadata editing will be added in the next slice. You can continue by updating sales and imports for
          this store.
        </p>

        <div className="mt-5 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => router.push(`/stores/${storeId}/data`)}
            className="rounded-full bg-pine px-4 py-2 text-sm font-semibold text-white"
          >
            Open Store Data
          </button>
          <button
            type="button"
            onClick={() => router.push(`/stores/${storeId}/planogram/latest`)}
            className="rounded-full border border-ink/20 px-4 py-2 text-sm font-semibold text-ink/80"
          >
            Back to Planogram
          </button>
        </div>
      </div>
    </main>
  );
}
