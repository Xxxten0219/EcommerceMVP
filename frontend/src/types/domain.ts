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

export type Conversation = {
  id: string;
  project_id: string;
  created_by: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type ChatMessage = {
  id: string;
  conversation_id: string;
  user_id: string | null;
  role: "system" | "user" | "assistant" | "tool";
  content: string;
  metadata_json: string;
  created_at: string;
};

export type ToolCall = {
  id: string;
  tool_name: string;
  input: Record<string, unknown>;
  output_summary: Record<string, unknown> | null;
  status: "running" | "succeeded" | "failed";
  duration_ms: number;
  error_message: string | null;
  created_at: string;
};

export type AgentRun = {
  id: string;
  provider: string;
  model_name: string;
  status: "running" | "completed" | "failed";
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
  assistant_message: ChatMessage | null;
  tool_calls: ToolCall[];
};
