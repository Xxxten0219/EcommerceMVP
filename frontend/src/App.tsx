import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchHealth } from "./api/health";
import { fetchDepartments, fetchProjects, fetchUsers } from "./api/organization";
import { AdminPanel } from "./components/AdminPanel";
import { Dashboard } from "./components/Dashboard";
import { DemoNotice } from "./components/DemoNotice";
import { DepartmentView } from "./components/DepartmentView";
import { ProjectWorkspace } from "./components/ProjectWorkspace";
import type { DemoUser, Department, Project } from "./types/domain";
import type { HealthResponse } from "./types/health";

type View = "dashboard" | "admin" | "department" | "project";

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [users, setUsers] = useState<DemoUser[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentUserId, setCurrentUserId] = useState("");
  const [view, setView] = useState<View>("dashboard");
  const [selectedDepartmentId, setSelectedDepartmentId] = useState("");
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const currentUser = users.find((user) => user.id === currentUserId) ?? null;
  const selectedDepartment = departments.find(
    (department) => department.id === selectedDepartmentId,
  );

  const loadReferenceData = useCallback(async () => {
    const [departmentData, userData] = await Promise.all([fetchDepartments(), fetchUsers()]);
    setDepartments(departmentData);
    setUsers(userData);
    setCurrentUserId((existing) => existing || userData[0]?.id || "");
    return userData;
  }, []);

  const loadProjects = useCallback(async (user?: DemoUser | null) => {
    const projectData = await fetchProjects(user?.role === "employee" ? user.id : undefined);
    setProjects(projectData);
  }, []);

  useEffect(() => {
    async function initialize() {
      try {
        const [healthData, userData] = await Promise.all([fetchHealth(), loadReferenceData()]);
        setHealth(healthData);
        await loadProjects(userData[0] ?? null);
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "工作台初始化失败");
      } finally {
        setLoading(false);
      }
    }
    void initialize();
  }, [loadProjects, loadReferenceData]);

  async function handleRoleChange(userId: string) {
    const user = users.find((item) => item.id === userId) ?? null;
    setCurrentUserId(userId);
    setView("dashboard");
    setSelectedProject(null);
    setError("");
    try {
      await loadProjects(user);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "项目加载失败");
    }
  }

  async function refreshAdminData() {
    const refreshedUsers = await loadReferenceData();
    const refreshedCurrent =
      refreshedUsers.find((user) => user.id === currentUserId) ?? currentUser;
    await loadProjects(refreshedCurrent);
  }

  const visibleDepartmentProjects = useMemo(
    () => projects.filter((project) => project.department_id === selectedDepartmentId),
    [projects, selectedDepartmentId],
  );

  if (loading) {
    return <div className="loading-screen">正在装载 EcommerceMVP 工作台…</div>;
  }

  return (
    <main>
      <header className="topbar">
        <button
          className="brand brand-button"
          type="button"
          onClick={() => setView("dashboard")}
        >
          <span className="brand-mark">E</span>
          <span>
            <strong>EcommerceMVP</strong>
            <small>Internal agent workflow</small>
          </span>
        </button>

        <nav className="main-nav" aria-label="主导航">
          <button
            className={view === "dashboard" ? "active" : ""}
            onClick={() => setView("dashboard")}
          >
            总工作台
          </button>
          {currentUser?.role === "admin" && (
            <button
              className={view === "admin" ? "active" : ""}
              onClick={() => setView("admin")}
            >
              管理员
            </button>
          )}
        </nav>

        <div className="topbar-actions">
          <span className={`mode-pill ${health?.status === "ok" ? "online" : ""}`}>
            {health?.status === "ok" ? "API · ONLINE" : "API · OFFLINE"}
          </span>
          <label className="role-switcher">
            <span>当前角色</span>
            <select
              value={currentUserId}
              onChange={(event) => void handleRoleChange(event.target.value)}
            >
              {users.map((user) => (
                <option value={user.id} key={user.id}>
                  {user.role === "admin" ? "管理员" : "员工"} · {user.display_name}
                </option>
              ))}
            </select>
          </label>
        </div>
      </header>

      <DemoNotice />
      {error && <div className="inline-notice error-notice">{error}</div>}

      {view === "dashboard" && (
        <Dashboard
          departments={departments}
          projects={projects}
          onOpenDepartment={(departmentId) => {
            setSelectedDepartmentId(departmentId);
            setView("department");
          }}
        />
      )}

      {view === "admin" && currentUser?.role === "admin" && (
        <AdminPanel
          admin={currentUser}
          departments={departments}
          users={users}
          projects={projects}
          onChanged={refreshAdminData}
        />
      )}

      {view === "department" && selectedDepartment && (
        <DepartmentView
          department={selectedDepartment}
          projects={visibleDepartmentProjects}
          onOpenProject={(project) => {
            setSelectedProject(project);
            setView("project");
          }}
        />
      )}

      {view === "project" && selectedProject && selectedDepartment && currentUser && (
        <ProjectWorkspace
          project={selectedProject}
          department={selectedDepartment}
          currentUser={currentUser}
          onBack={() => setView("department")}
        />
      )}

      <footer className="page-footer">
        <span>EcommerceMVP / Modular monolith</span>
        <span>实际采购必须由人工确认，MVP 不执行真实采购。</span>
      </footer>
    </main>
  );
}

export default App;
