import { create } from "zustand";

import type {
  Planogram,
  PlanogramJson,
  PlanogramProduct,
  PlanogramShelf,
} from "@/types/planogram";

export interface CatalogueProduct {
  id: string;
  sku: string;
  name: string;
  brand: string | null;
  category: string | null;
  width_cm: number | null;
  height_cm: number | null;
  depth_cm: number | null;
  price: number | null;
  image_url: string | null;
}

interface PlanogramStoreState {
  planogram: Planogram | null;
  isDirty: boolean;
  isSaving: boolean;
  selectedProductSku: string | null;
  setPlanogram: (planogram: Planogram) => void;
  clear: () => void;
  setSelected: (sku: string | null) => void;
  moveProduct: (sku: string, fromShelf: number, toShelf: number, newPositionXCm: number) => void;
  updateFacings: (sku: string, shelfNumber: number, nextFacingCount: number) => void;
  removeProduct: (sku: string, shelfNumber: number) => void;
  addProduct: (product: CatalogueProduct, toShelf: number) => void;
  markSaving: (isSaving: boolean) => void;
  markSaved: () => void;
}

const DEFAULT_PRODUCT_WIDTH = 10;
const DEFAULT_PRODUCT_HEIGHT = 20;

const CATEGORY_COLORS: Record<string, string> = {
  dairy: "#4A90D9",
  beverages: "#7ED321",
  snacks: "#F5A623",
  "personal care": "#9B59B6",
  household: "#E74C3C",
  bakery: "#E67E22",
  frozen: "#1ABC9C",
};

const colorForCategory = (category: string | null): string => {
  if (!category) return "#95A5A6";
  return CATEGORY_COLORS[category.toLowerCase().trim()] ?? "#95A5A6";
};

const cloneJson = (planogramJson: PlanogramJson): PlanogramJson => ({
  ...planogramJson,
  shelves: planogramJson.shelves.map((shelf) => ({
    ...shelf,
    products: shelf.products.map((product) => ({ ...product })),
  })),
});

const findShelf = (planogramJson: PlanogramJson, shelfNumber: number): PlanogramShelf | undefined =>
  planogramJson.shelves.find((shelf) => shelf.shelf_number === shelfNumber);

const reflowShelf = (shelf: PlanogramShelf, shelfWidthCm: number): void => {
  shelf.products.sort((a, b) => a.position_x_cm - b.position_x_cm);
  let cursor = 0;
  for (const product of shelf.products) {
    const totalWidth = product.width_cm * product.facing_count;
    product.position_x_cm = cursor;
    product.total_width_cm = totalWidth;
    cursor += totalWidth;
  }
  shelf.remaining_width_cm = Math.max(0, shelfWidthCm - cursor);
};

export const usePlanogramStore = create<PlanogramStoreState>((set) => ({
  planogram: null,
  isDirty: false,
  isSaving: false,
  selectedProductSku: null,

  setPlanogram: (planogram) =>
    set({ planogram, isDirty: false, isSaving: false, selectedProductSku: null }),

  clear: () => set({ planogram: null, isDirty: false, isSaving: false, selectedProductSku: null }),

  setSelected: (sku) => set({ selectedProductSku: sku }),

  moveProduct: (sku, fromShelf, toShelf, newPositionXCm) =>
    set((state) => {
      if (!state.planogram) return state;
      const planogramJson = cloneJson(state.planogram.planogram_json);
      const shelfWidthCm = planogramJson.shelf_config.shelf_width_cm;
      const source = findShelf(planogramJson, fromShelf);
      if (!source) return state;
      const productIndex = source.products.findIndex((p) => p.sku === sku);
      if (productIndex < 0) return state;
      const [product] = source.products.splice(productIndex, 1);

      const target = findShelf(planogramJson, toShelf);
      if (!target) {
        source.products.push(product);
        reflowShelf(source, shelfWidthCm);
        return { planogram: { ...state.planogram, planogram_json: planogramJson } };
      }

      product.position_x_cm = Math.max(
        0,
        Math.min(newPositionXCm, shelfWidthCm - product.width_cm * product.facing_count),
      );
      target.products.push(product);

      reflowShelf(source, shelfWidthCm);
      reflowShelf(target, shelfWidthCm);

      return {
        planogram: { ...state.planogram, planogram_json: planogramJson },
        isDirty: true,
      };
    }),

  updateFacings: (sku, shelfNumber, nextFacingCount) =>
    set((state) => {
      if (!state.planogram) return state;
      if (nextFacingCount < 1) return state;
      const planogramJson = cloneJson(state.planogram.planogram_json);
      const shelfWidthCm = planogramJson.shelf_config.shelf_width_cm;
      const shelf = findShelf(planogramJson, shelfNumber);
      if (!shelf) return state;
      const product = shelf.products.find((p) => p.sku === sku);
      if (!product) return state;

      const currentTotal = shelf.products.reduce(
        (sum, p) => sum + (p.sku === sku ? 0 : p.width_cm * p.facing_count),
        0,
      );
      const candidate = product.width_cm * nextFacingCount;
      if (currentTotal + candidate > shelfWidthCm) {
        return state;
      }
      product.facing_count = nextFacingCount;
      product.total_width_cm = candidate;
      reflowShelf(shelf, shelfWidthCm);

      return {
        planogram: { ...state.planogram, planogram_json: planogramJson },
        isDirty: true,
      };
    }),

  removeProduct: (sku, shelfNumber) =>
    set((state) => {
      if (!state.planogram) return state;
      const planogramJson = cloneJson(state.planogram.planogram_json);
      const shelfWidthCm = planogramJson.shelf_config.shelf_width_cm;
      const shelf = findShelf(planogramJson, shelfNumber);
      if (!shelf) return state;
      const before = shelf.products.length;
      shelf.products = shelf.products.filter((p) => p.sku !== sku);
      if (shelf.products.length === before) return state;
      reflowShelf(shelf, shelfWidthCm);

      return {
        planogram: { ...state.planogram, planogram_json: planogramJson },
        isDirty: true,
        selectedProductSku: state.selectedProductSku === sku ? null : state.selectedProductSku,
      };
    }),

  addProduct: (catalogueProduct, toShelf) =>
    set((state) => {
      if (!state.planogram) return state;
      const planogramJson = cloneJson(state.planogram.planogram_json);
      const shelfWidthCm = planogramJson.shelf_config.shelf_width_cm;
      const shelf = findShelf(planogramJson, toShelf);
      if (!shelf) return state;
      const exists = planogramJson.shelves.some((s) =>
        s.products.some((p) => p.sku === catalogueProduct.sku),
      );
      if (exists) return state;
      const width = catalogueProduct.width_cm ?? DEFAULT_PRODUCT_WIDTH;
      const used = shelf.products.reduce((sum, p) => sum + p.width_cm * p.facing_count, 0);
      if (used + width > shelfWidthCm) return state;

      const product: PlanogramProduct = {
        product_id: catalogueProduct.id,
        sku: catalogueProduct.sku,
        name: catalogueProduct.name,
        brand: catalogueProduct.brand,
        category: catalogueProduct.category ?? "",
        position_x_cm: used,
        width_cm: width,
        height_cm: catalogueProduct.height_cm ?? DEFAULT_PRODUCT_HEIGHT,
        facing_count: 1,
        total_width_cm: width,
        sales_score: 0,
        revenue: 0,
        units_sold: 0,
        placement_tier: shelf.tier,
        color_hex: colorForCategory(catalogueProduct.category),
      };
      shelf.products.push(product);
      reflowShelf(shelf, shelfWidthCm);

      return {
        planogram: { ...state.planogram, planogram_json: planogramJson },
        isDirty: true,
        selectedProductSku: product.sku,
      };
    }),

  markSaving: (isSaving) => set({ isSaving }),
  markSaved: () => set({ isDirty: false, isSaving: false }),
}));
