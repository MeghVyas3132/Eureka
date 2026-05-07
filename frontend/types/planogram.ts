export interface PlanogramVersionSummary {
  id: string;
  version_number: number;
  created_at: string;
}

export type PlacementTier = "top_level" | "eye_level" | "mid_level" | "low_level";

export interface PlanogramProduct {
  product_id: string;
  sku: string;
  name: string;
  brand?: string | null;
  category: string;
  position_x_cm: number;
  width_cm: number;
  height_cm: number;
  facing_count: number;
  total_width_cm: number;
  sales_score: number;
  revenue: number;
  units_sold: number;
  placement_tier: PlacementTier | string;
  color_hex: string;
}

export interface PlanogramShelf {
  shelf_number: number;
  tier: PlacementTier | string;
  remaining_width_cm: number;
  products: PlanogramProduct[];
}

export interface PlanogramConfidence {
  score: number;
  tier: "high" | "medium" | "low" | string;
  sales_coverage_pct: number;
  dimension_coverage_pct: number;
  category_coverage_pct: number;
  store_parse_confidence: number;
}

export interface PlanogramAssortment {
  total_catalogue_skus: number;
  included_skus: number;
  excluded_skus: number;
  filter_method: string;
  coverage_pct: number;
  message: string;
}

export interface PlanogramQualityWarning {
  code: string;
  severity: "high" | "medium" | "low" | string;
  message: string;
  action_label: string;
  action_url: string;
}

export interface PlanogramShelfConfig {
  shelf_count: number;
  shelf_width_cm: number;
  shelf_height_cm: number;
  shelf_depth_cm: number;
  shelf_spacing_cm: number;
  store_type: string;
  store_type_rules_applied: boolean;
}

export interface PlanogramJson {
  planogram_id: string | null;
  store_id: string;
  generation_level: string;
  generation_method: string;
  generated_at: string;
  has_sales_data: boolean;
  confidence: PlanogramConfidence;
  assortment: PlanogramAssortment;
  data_quality_warnings: PlanogramQualityWarning[];
  shelf_config: PlanogramShelfConfig;
  shelves: PlanogramShelf[];
  overflow_skus: string[];
  category_summary: Record<
    string,
    { sku_count: number; total_revenue: number; shelves: number[] }
  >;
}

export interface Planogram {
  id: string;
  store_id: string;
  name: string;
  generation_level: string;
  generation_method: string;
  shelf_count: number;
  shelf_width_cm: number;
  shelf_height_cm: number;
  planogram_json: PlanogramJson;
  is_user_edited: boolean;
  last_auto_generated_at: string | null;
  created_at: string;
  updated_at: string;
  versions: PlanogramVersionSummary[];
}

export interface PlanogramListResponse {
  data: Planogram[];
  total: number;
}

export interface PlanogramVersionListResponse {
  data: PlanogramVersionSummary[];
}
