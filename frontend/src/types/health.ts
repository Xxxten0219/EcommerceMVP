export type HealthResponse = {
  status: "ok" | "degraded";
  service: string;
  version: string;
  database: "ok" | "unavailable";
  mock_mode: boolean;
};
