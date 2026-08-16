import { useEffect, useState } from "react";

import { fetchHealth } from "./api/health";
import type { HealthResponse } from "./types/health";

type HealthState =
  | { kind: "loading" }
  | { kind: "online"; data: HealthResponse }
  | { kind: "offline" };

const departments = [
  {
    code: "ART",
    name: "美工部门",
    eyebrow: "Image workflow",
    description: "保留原图，追踪每一次提示词、生成状态与图片版本。",
    feature: "千问图片编辑 · Mock 优先",
    accent: "coral",
  },
  {
    code: "SAL",
    name: "销售部门",
    eyebrow: "Sales intelligence",
    description: "从报表校验到指标分析，共用一套可审计的计算服务。",
    feature: "CSV / XLSX · 事务导入",
    accent: "blue",
  },
  {
    code: "SEL",
    name: "选品部门",
    eyebrow: "Selection agent",
    description: "结合销售与库存，用确定性规则给出补货数量与风险依据。",
    feature: "DeepSeek · 受控工具",
    accent: "lime",
  },
] as const;

const demoRoles = ["演示管理员", "美工员工 · 林然", "销售员工 · 周启", "选品员工 · 陈禾"];

function App() {
  const [health, setHealth] = useState<HealthState>({ kind: "loading" });
  const [role, setRole] = useState(demoRoles[0]);

  useEffect(() => {
    const controller = new AbortController();

    fetchHealth(controller.signal)
      .then((data) => setHealth({ kind: "online", data }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setHealth({ kind: "offline" });
      });

    return () => controller.abort();
  }, []);

  const healthLabel =
    health.kind === "loading" ? "正在连接" : health.kind === "online" ? "API 在线" : "API 未连接";

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="EcommerceMVP 首页">
          <span className="brand-mark">E</span>
          <span>
            <strong>EcommerceMVP</strong>
            <small>Internal agent workflow</small>
          </span>
        </a>

        <div className="topbar-actions">
          <span className="mode-pill">MVP · Mock mode</span>
          <label className="role-switcher">
            <span>当前角色</span>
            <select value={role} onChange={(event) => setRole(event.target.value)}>
              {demoRoles.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
        </div>
      </header>

      <section className="demo-warning" role="note">
        <span aria-hidden="true">!</span>
        <p>
          <strong>演示角色切换，不代表真实身份认证。</strong>
          当前选择仅用于 MVP 界面演示；后续所有项目归属仍由后端校验并持久化。
        </p>
      </section>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="kicker">ONE WORKSPACE · THREE TEAMS</p>
          <h1>
            让每个部门都拥有
            <span>可追踪的 Agent 工作流</span>
          </h1>
          <p className="hero-description">
            从商品图版本、销售报表到库存与补货建议，把模型、受控工具和业务规则放进同一条可审计链路。
          </p>
          <div className="hero-meta">
            <span>React</span>
            <span>FastAPI</span>
            <span>SQLite</span>
            <span>Docker Compose</span>
          </div>
        </div>

        <aside className="system-card" aria-label="系统状态">
          <div className="system-card-heading">
            <span>Foundation status</span>
            <span className={`status-dot ${health.kind}`} aria-hidden="true" />
          </div>
          <strong>{healthLabel}</strong>
          <dl>
            <div>
              <dt>API</dt>
              <dd>{health.kind === "online" ? health.data.version : "—"}</dd>
            </div>
            <div>
              <dt>SQLite</dt>
              <dd>{health.kind === "online" ? "Connected" : "—"}</dd>
            </div>
            <div>
              <dt>Provider</dt>
              <dd>{health.kind === "online" && health.data.mock_mode ? "Mock" : "—"}</dd>
            </div>
          </dl>
        </aside>
      </section>

      <section className="department-section" aria-labelledby="department-title">
        <div className="section-heading">
          <div>
            <p className="kicker">DEPARTMENT PORTALS</p>
            <h2 id="department-title">选择一个部门工作区</h2>
          </div>
          <p>项目内容会依据当前演示角色的分配关系显示。</p>
        </div>

        <div className="department-grid">
          {departments.map((department, index) => (
            <article className={`department-card ${department.accent}`} key={department.code}>
              <div className="card-index">0{index + 1}</div>
              <div className="card-title-row">
                <span className="department-code">{department.code}</span>
                <span>{department.eyebrow}</span>
              </div>
              <h3>{department.name}</h3>
              <p>{department.description}</p>
              <footer>
                <span>{department.feature}</span>
                <button type="button" disabled title="将在后续里程碑开放">
                  底座已就绪 <span aria-hidden="true">↗</span>
                </button>
              </footer>
            </article>
          ))}
        </div>
      </section>

      <footer className="page-footer">
        <span>EcommerceMVP / M0 foundation</span>
        <span>实际采购必须由人工确认，MVP 不执行真实采购。</span>
      </footer>
    </main>
  );
}

export default App;
