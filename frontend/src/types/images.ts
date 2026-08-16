export type ImageAsset = {
  id: string;
  original_name: string;
  mime_type: string;
  size_bytes: number;
  sha256: string;
  created_at: string;
};

export type ImageVersion = {
  id: string;
  project_id: string;
  conversation_id: string;
  source_attachment_id: string;
  parent_version_id: string | null;
  output_attachment_id: string | null;
  prompt: string;
  provider: string;
  model_name: string;
  status: "pending" | "running" | "completed" | "failed";
  retry_count: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};
