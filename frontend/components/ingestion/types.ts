export type FileFormat = "csv" | "excel" | "pdf";
export type ImportStatus = "completed" | "partial" | "failed";

export interface ImportError {
  row: number;
  reason: string;
}

export interface PotentialDuplicate {
  row_a?: number | null;
  sku_a: string;
  name_a: string;
  row_b: number;
  sku_b: string;
  name_b: string;
  similarity: number;
  source: "intra_file" | "cross_import" | string;
}

export interface ImportSummaryResponse {
  import_id: string;
  import_type: "product" | "sales" | "store";
  file_format: FileFormat;
  original_filename: string;
  imported_at: string;
  total_rows: number;
  success: number;
  skipped: number;
  errors: ImportError[];
  status: ImportStatus;
  period_start?: string | null;
  period_end?: string | null;
  unmatched_skus?: string[] | null;
  potential_duplicates?: PotentialDuplicate[] | null;
}

export interface ImportLogResponse {
  id: string;
  import_type: "product" | "sales" | "store";
  file_format: FileFormat;
  original_filename: string;
  file_size_bytes: number;
  total_rows: number;
  success_count: number;
  skipped_count: number;
  error_count: number;
  error_detail?: ImportError[] | null;
  status: ImportStatus;
  imported_at: string;
  period_start?: string | null;
  period_end?: string | null;
  unmatched_skus?: string[] | null;
}
