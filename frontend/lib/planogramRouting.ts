import { api } from "@/lib/api";
import type { Planogram, PlanogramListResponse } from "@/types/planogram";

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function isUuid(value: string): boolean {
  return UUID_REGEX.test(value);
}

export async function listPlanogramsForStore(storeId: string): Promise<Planogram[]> {
  const response = await api.get<PlanogramListResponse>(`/api/v1/planograms?store_id=${storeId}`);
  return response.data.data;
}

export async function ensurePlanogramForStore(storeId: string): Promise<Planogram> {
  const existing = await listPlanogramsForStore(storeId);
  if (existing.length > 0) {
    return existing[0];
  }

  const generated = await api.post<Planogram>("/api/v1/planograms/generate", {
    store_id: storeId,
    generation_level: "store",
  });

  return generated.data;
}

export async function openPlanogramForStore(storeId: string): Promise<string> {
  const planogram = await ensurePlanogramForStore(storeId);
  return `/stores/${storeId}/planogram/${planogram.id}`;
}
