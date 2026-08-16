export type Department = {
  id: string;
  code: "artwork" | "sales" | "selection";
  name: string;
  created_at: string;
};

export type DemoUser = {
  id: string;
  department_id: string | null;
  display_name: string;
  role: "admin" | "employee";
  is_active: boolean;
  created_at: string;
};

export type Project = {
  id: string;
  department_id: string;
  name: string;
  description: string;
  summary: string;
  created_by: string | null;
  member_ids: string[];
  created_at: string;
  updated_at: string;
};
