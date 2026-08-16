import type { HealthResponse } from "../types/health";

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
  const response = await fetch(`${apiBaseUrl}/health`, { signal });

  if (!response.ok) {
    throw new Error("Health check failed");
  }

  return (await response.json()) as HealthResponse;
}
