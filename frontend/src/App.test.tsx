import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const healthPayload = {
  status: "ok",
  service: "ecommerce-mvp-api",
  version: "0.1.0",
  database: "ok",
  mock_mode: true,
};

const departments = [
  { id: "art", code: "artwork", name: "美工部门", created_at: "2026-01-01T00:00:00Z" },
  { id: "sales", code: "sales", name: "销售部门", created_at: "2026-01-01T00:00:00Z" },
  { id: "selection", code: "selection", name: "选品部门", created_at: "2026-01-01T00:00:00Z" },
];

const users = [
  {
    id: "admin",
    department_id: null,
    display_name: "演示管理员",
    role: "admin",
    is_active: true,
    created_at: "2026-01-01T00:00:00Z",
  },
];

describe("App", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        const payload = url.endsWith("/health")
          ? healthPayload
          : url.endsWith("/departments")
            ? departments
            : url.endsWith("/users")
              ? users
              : [];
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(payload) });
      }),
    );
  });

  it("renders the three department portals and demo authentication warning", async () => {
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "选择一个部门工作区" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "美工部门" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "销售部门" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "选品部门" })).toBeInTheDocument();
    expect(screen.getByText(/演示角色切换，不代表真实身份认证/)).toBeInTheDocument();
    expect(await screen.findByText("API · ONLINE")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "管理员 · 演示管理员" })).toBeInTheDocument();
  });
});
