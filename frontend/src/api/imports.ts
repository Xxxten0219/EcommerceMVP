import type { ImportBatch, ImportPreview } from "../types/imports";
import { API_BASE_URL, apiRequest } from "./client";

export function uploadReport(payload: {
  projectId: string;
  userId: string;
  kind: "sales" | "inventory";
  file: File;
}): Promise<ImportPreview> {
  const body = new FormData();
  body.set("project_id", payload.projectId);
  body.set("user_id", payload.userId);
  body.set("kind", payload.kind);
  body.set("file", payload.file);
  return apiRequest("/imports", { method: "POST", body });
}

export function confirmReport(batchId: string, userId: string): Promise<ImportBatch> {
  return apiRequest(`/imports/${batchId}/confirm`, {
    method: "POST",
    body: JSON.stringify({ user_id: userId }),
  });
}

export function importErrorUrl(batchId: string, userId: string): string {
  return `${API_BASE_URL}/imports/${batchId}/errors.csv?user_id=${encodeURIComponent(userId)}`;
}
