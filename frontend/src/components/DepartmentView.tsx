import type { Department, Project } from "../types/domain";

type DepartmentViewProps = {
  department: Department;
  projects: Project[];
  onOpenProject: (project: Project) => void;
};

export function DepartmentView({ department, projects, onOpenProject }: DepartmentViewProps) {
  return (
    <section className="workspace-page">
      <div className="workspace-heading">
        <div>
          <p className="kicker">{department.code.toUpperCase()} WORKSPACE</p>
          <h1>{department.name}</h1>
        </div>
        <span className="count-badge">{projects.length} 个已分配项目</span>
      </div>

      {projects.length ? (
        <div className="project-list">
          {projects.map((project) => (
            <article className="project-row" key={project.id}>
              <div>
                <span className="project-id">{project.id.slice(0, 8)}</span>
                <h2>{project.name}</h2>
                <p>{project.description || "暂无项目描述"}</p>
              </div>
              <button type="button" onClick={() => onOpenProject(project)}>
                打开项目
              </button>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <strong>当前角色在该部门暂无项目</strong>
          <p>管理员可以在项目管理页面创建项目并分配成员。</p>
        </div>
      )}
    </section>
  );
}
