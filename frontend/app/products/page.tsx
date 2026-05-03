"use client";

import ImportHistory from "@/components/ingestion/ImportHistory";
import ProductImporter from "@/components/products/ProductImporter";

export default function ProductsPage() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_20%_0%,#f2e5c4_0%,#f6f7f8_45%,#eef2ef_100%)] px-6 py-8">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <header className="rounded-3xl border border-ink/10 bg-white/90 p-6 shadow">
          <p className="text-xs uppercase tracking-[0.2em] text-ink/50">Products</p>
          <h1 className="mt-2 text-3xl font-bold text-ink">Product master data</h1>
          <p className="mt-2 text-sm text-ink/70">
            Upload product master data to keep SKU dimensions, pricing, and categories up to date.
          </p>
        </header>

        <ProductImporter />

        <ImportHistory title="Product import history" fetchUrl="/api/v1/products/import/history" />
      </div>
    </main>
  );
}
