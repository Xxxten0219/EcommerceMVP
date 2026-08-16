import type { HealthResponse } from "../types/health";
import { apiRequest } from "./client";

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return apiRequest("/health", { signal });
}
