import type { SelectionAnalysis } from "../types/selection";
import { apiRequest } from "./client";

export function fetchSelectionOverview(
  projectId: string,
  userId: string,
  productName: string,
): Promise<SelectionAnalysis> {
  const params = new URLSearchParams({ user_id: userId, product_name: productName });
  return apiRequest(`/projects/${projectId}/selection-overview?${params}`);
}
