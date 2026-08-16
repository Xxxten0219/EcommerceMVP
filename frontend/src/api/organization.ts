import type { DemoUser, Department, Project } from "../types/domain";
import { apiRequest } from "./client";

export function fetchDepartments(): Promise<Department[]> {
  return apiRequest("/departments");
}

export function fetchUsers(): Promise<DemoUser[]> {
  return apiRequest("/users");
}

export function fetchProjects(userId?: string, departmentId?: string): Promise<Project[]> {
  const params = new URLSearchParams();
  if (userId) params.set("user_id", userId);
  if (departmentId) params.set("department_id", departmentId);
  const query = params.size ? `?${params.toString()}` : "";
  return apiRequest(`/projects${query}`);
}

export function createDemoUser(payload: {
  department_id: string;
  display_name: string;
}): Promise<DemoUser> {
  return apiRequest("/users", {
    method: "POST",
    body: JSON.stringify({ ...payload, role: "employee" }),
  });
}

export function createProject(payload: {
  department_id: string;
  name: string;
  description: string;
  created_by: string;
  member_ids: string[];
}): Promise<Project> {
  return apiRequest("/projects", { method: "POST", body: JSON.stringify(payload) });
}
