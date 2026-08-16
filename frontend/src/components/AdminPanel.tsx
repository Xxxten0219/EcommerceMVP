import { useMemo, useState } from "react";

import { createDemoUser, createProject } from "../api/organization";
import type { DemoUser, Department, Project } from "../types/domain";

type AdminPanelProps = {
  admin: DemoUser;
  departments: Department[];
  users: DemoUser[];
  projects: Project[];
  onChanged: () => Promise<void>;
};

export function AdminPanel({ admin, departments, users, projects, onChanged }: AdminPanelProps) {
  const [employeeName, setEmployeeName] = useState("");
  const [employeeDepartment, setEmployeeDepartment] = useState(departments[0]?.id ?? "");
  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [projectDepartment, setProjectDepartment] = useState(departments[0]?.id ?? "");
  const [memberId, setMemberId] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  const eligibleMembers = useMemo(
    () => users.filter((user) => user.department_id === projectDepartment),
    [projectDepartment, users],
  );

  async function handleCreateEmployee(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setNotice("");
    try {
      await createDemoUser({
        display_name: employeeName.trim(),
        department_id: employeeDepartment,
      });
      setEmployeeName("");
      setNotice("演示员工已创建");
      await onChanged();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "创建员工失败");
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateProject(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setNotice("");
    try {
      await createProject({
        department_id: projectDepartment,
        name: projectName.trim(),
        description: projectDescription.trim(),
        created_by: admin.id,
        member_ids: memberId ? [memberId] : [],
      });
      setProjectName("");
      setProjectDescription("");
      setMemberId("");
      setNotice("项目已创建并保存分配关系");
      await onChanged();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "创建项目失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="workspace-page admin-page">
      <div className="workspace-heading">
        <div>
          <p className="kicker">DEMO ADMINISTRATION</p>
          <h1>人员与项目管理</h1>
        </div>
        <span className="count-badge">{users.length} 人 · {projects.length} 个项目</span>
      </div>

      {notice && <div className="inline-notice">{notice}</div>}

      <div className="admin-grid">
        <form className="admin-card" onSubmit={handleCreateEmployee}>
          <span className="form-number">01</span>
          <h2>创建演示员工</h2>
          <label>
            员工姓名
            <input required maxLength={80} value={employeeName} onChange={(event) => setEmployeeName(event.target.value)} placeholder="例如：王晓" />
          </label>
          <label>
            所属部门
            <select value={employeeDepartment} onChange={(event) => setEmployeeDepartment(event.target.value)}>
              {departments.map((department) => <option value={department.id} key={department.id}>{department.name}</option>)}
            </select>
          </label>
          <button disabled={busy} type="submit">创建员工</button>
        </form>

        <form className="admin-card" onSubmit={handleCreateProject}>
          <span className="form-number">02</span>
          <h2>创建并分配项目</h2>
          <label>
            项目名称
            <input required maxLength={120} value={projectName} onChange={(event) => setProjectName(event.target.value)} placeholder="例如：秋季库存复盘" />
          </label>
          <label>
            项目描述
            <textarea value={projectDescription} onChange={(event) => setProjectDescription(event.target.value)} placeholder="说明项目目标与数据范围" />
          </label>
          <label>
            所属部门
            <select value={projectDepartment} onChange={(event) => { setProjectDepartment(event.target.value); setMemberId(""); }}>
              {departments.map((department) => <option value={department.id} key={department.id}>{department.name}</option>)}
            </select>
          </label>
          <label>
            分配员工
            <select value={memberId} onChange={(event) => setMemberId(event.target.value)}>
              <option value="">暂不分配</option>
              {eligibleMembers.map((user) => <option value={user.id} key={user.id}>{user.display_name}</option>)}
            </select>
          </label>
          <button disabled={busy} type="submit">创建项目</button>
        </form>
      </div>
    </section>
  );
}
