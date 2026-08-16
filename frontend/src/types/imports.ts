export type ImportBatch = {
  id: string;
  department_id: string;
  project_id: string;
  created_by: string;
  kind: "sales" | "inventory";
  original_name: string;
  sha256: string;
  size_bytes: number;
  mapping: Record<string, string>;
  status: string;
  total_rows: number;
  success_rows: number;
  failed_rows: number;
  created_at: string;
  confirmed_at: string | null;
  completed_at: string | null;
  error_message: string | null;
};

export type ImportIssue = {
  row_number: number;
  field_name: string | null;
  error_code: string;
  message: string;
};

export type ImportPreview = {
  batch: ImportBatch;
  rows: Array<Record<string, string | number | null>>;
  errors: ImportIssue[];
  detected_headers?: string[];
};
