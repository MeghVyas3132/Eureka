"use client";

import { useMemo } from "react";

import { usePlanogramStore } from "@/store/planogramStore";

export default function FacingControls() {
  const planogram = usePlanogramStore((state) => state.planogram);
  const selectedSku = usePlanogramStore((state) => state.selectedProductSku);
  const updateFacings = usePlanogramStore((state) => state.updateFacings);
  const removeProduct = usePlanogramStore((state) => state.removeProduct);

  const found = useMemo(() => {
    if (!planogram || !selectedSku) return null;
    for (const shelf of planogram.planogram_json.shelves) {
      const product = shelf.products.find((p) => p.sku === selectedSku);
      if (product) {
        return { shelf, product };
      }
    }
    return null;
  }, [planogram, selectedSku]);

  if (!planogram) return null;

  if (!found) {
    return (
      <div className="rounded-2xl border border-dashed border-ink/20 bg-white/80 p-4 text-xs text-ink/60">
        Click a product on the canvas to edit facings.
      </div>
    );
  }

  const { shelf, product } = found;
  const shelfWidthCm = planogram.planogram_json.shelf_config.shelf_width_cm;
  const used = shelf.products.reduce((sum, p) => sum + p.width_cm * p.facing_count, 0);
  const occupancyPct = Math.min(100, (used / shelfWidthCm) * 100);

  const canIncrement =
    used - product.width_cm * product.facing_count + product.width_cm * (product.facing_count + 1) <=
    shelfWidthCm;

  return (
    <div className="space-y-3 rounded-2xl border border-ink/10 bg-white p-4 shadow-sm">
      <div>
        <p className="text-xs uppercase tracking-wider text-ink/50">Selected SKU</p>
        <p className="mt-1 text-sm font-semibold text-ink">{product.sku}</p>
        <p className="text-xs text-ink/70">{product.name}</p>
      </div>

      <div>
        <p className="text-xs uppercase tracking-wider text-ink/50">Facings</p>
        <div className="mt-1 flex items-center gap-3">
          <button
            type="button"
            onClick={() => updateFacings(product.sku, shelf.shelf_number, product.facing_count - 1)}
            disabled={product.facing_count <= 1}
            className="h-8 w-8 rounded-full border border-ink/20 text-base font-semibold text-ink/80 transition hover:border-ink/40 disabled:opacity-40"
          >
            −
          </button>
          <span className="min-w-[3ch] text-center text-lg font-semibold text-ink">{product.facing_count}</span>
          <button
            type="button"
            onClick={() => updateFacings(product.sku, shelf.shelf_number, product.facing_count + 1)}
            disabled={!canIncrement}
            className="h-8 w-8 rounded-full border border-ink/20 text-base font-semibold text-ink/80 transition hover:border-ink/40 disabled:opacity-40"
          >
            +
          </button>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between text-xs text-ink/60">
          <span>Shelf {shelf.shelf_number} occupancy</span>
          <span className="font-mono">{occupancyPct.toFixed(0)}%</span>
        </div>
        <div className="mt-1 h-2 overflow-hidden rounded-full bg-ink/10">
          <div
            className={`h-full ${occupancyPct >= 95 ? "bg-rose-500" : occupancyPct >= 80 ? "bg-amber-500" : "bg-pine"}`}
            style={{ width: `${occupancyPct}%` }}
          />
        </div>
      </div>

      <button
        type="button"
        onClick={() => removeProduct(product.sku, shelf.shelf_number)}
        className="w-full rounded-full border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700 transition hover:border-rose-300"
      >
        Remove from shelf
      </button>
    </div>
  );
}
