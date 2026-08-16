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

describe("App", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(healthPayload),
      }),
    );
  });

  it("renders the three department portals and demo authentication warning", async () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "选择一个部门工作区" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "美工部门" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "销售部门" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "选品部门" })).toBeInTheDocument();
    expect(screen.getByText(/演示角色切换，不代表真实身份认证/)).toBeInTheDocument();
    expect(await screen.findByText("API 在线")).toBeInTheDocument();
  });
});
