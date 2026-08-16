import type { Department, Project } from "../types/domain";

const departmentContent = {
  artwork: {
    code: "ART",
    eyebrow: "Image workflow",
    description: "保留原图，追踪每一次提示词、生成状态与图片版本。",
    feature: "千问图片编辑 · Mock 优先",
    accent: "coral",
  },
  sales: {
    code: "SAL",
    eyebrow: "Sales intelligence",
    description: "从报表校验到指标分析，共用一套可审计的计算服务。",
    feature: "CSV / XLSX · 事务导入",
    accent: "blue",
  },
  selection: {
    code: "SEL",
    eyebrow: "Selection agent",
    description: "结合销售与库存，用确定性规则给出补货数量与风险依据。",
    feature: "DeepSeek · 受控工具",
    accent: "lime",
  },
} as const;

type DashboardProps = {
  departments: Department[];
  projects: Project[];
  onOpenDepartment: (departmentId: string) => void;
};

export function Dashboard({ departments, projects, onOpenDepartment }: DashboardProps) {
  return (
    <>
      <section className="hero compact-hero" id="top">
        <div className="hero-copy">
          <p className="kicker">ONE WORKSPACE · THREE TEAMS</p>
          <h1>
            让每个部门都拥有
            <span>可追踪的 Agent 工作流</span>
          </h1>
          <p className="hero-description">
            从商品图版本、销售报表到库存与补货建议，把模型、受控工具和业务规则放进同一条可审计链路。
          </p>
        </div>
      </section>

      <section className="department-section" aria-labelledby="department-title">
        <div className="section-heading">
          <div>
            <p className="kicker">DEPARTMENT PORTALS</p>
            <h2 id="department-title">选择一个部门工作区</h2>
          </div>
          <p>项目数量来自当前演示角色的后端分配结果。</p>
        </div>

        <div className="department-grid">
          {departments.map((department, index) => {
            const content = departmentContent[department.code];
            const projectCount = projects.filter(
              (project) => project.department_id === department.id,
            ).length;
            return (
              <article className={`department-card ${content.accent}`} key={department.id}>
                <div className="card-index">0{index + 1}</div>
                <div className="card-title-row">
                  <span className="department-code">{content.code}</span>
                  <span>{content.eyebrow}</span>
                </div>
                <h3>{department.name}</h3>
                <p>{content.description}</p>
                <footer>
                  <span>
                    {content.feature}
                    <br />
                    当前可见 {projectCount} 个项目
                  </span>
                  <button type="button" onClick={() => onOpenDepartment(department.id)}>
                    进入工作区 <span aria-hidden="true">↗</span>
                  </button>
                </footer>
              </article>
            );
          })}
        </div>
      </section>
    </>
  );
}
