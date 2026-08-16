import { useMemo, useState } from "react";

import { confirmReport, importErrorUrl, uploadReport } from "../api/imports";
import type { DemoUser, Project } from "../types/domain";
import type { ImportPreview } from "../types/imports";

type SalesImportPanelProps = {
  project: Project;
  currentUser: DemoUser;
};

export function SalesImportPanel({ project, currentUser }: SalesImportPanelProps) {
  const [file, setFile] = useState<File | null>(null);
  const [kind, setKind] = useState<"sales" | "inventory">("sales");
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");

  const columns = useMemo(
    () => (preview?.rows[0] ? Object.keys(preview.rows[0]).filter((key) => key !== "source_row_number") : []),
    [preview],
  );

  async function handleUpload(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setNotice("");
    try {
      const result = await uploadReport({
        projectId: project.id,
        userId: currentUser.id,
        kind,
        file,
      });
      setPreview(result);
      setNotice("文件已完成哈希、字段映射和数据校验，请确认预览后写入。" );
    } catch (reason) {
      setNotice(reason instanceof Error ? reason.message : "文件上传失败");
    } finally {
      setBusy(false);
    }
  }

  async function handleConfirm() {
    if (!preview) return;
    setBusy(true);
    try {
      const batch = await confirmReport(preview.batch.id, currentUser.id);
      setPreview({ ...preview, batch });
      setNotice(`事务写入完成：${batch.success_rows} 行成功，${batch.failed_rows} 行未写入。`);
    } catch (reason) {
      setNotice(reason instanceof Error ? reason.message : "确认导入失败，事务已回滚");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="import-workspace">
      <header className="import-heading">
        <div>
          <p className="kicker">CONTROLLED DATA IMPORT</p>
          <h1>销售与库存报表导入</h1>
          <p>CSV / XLSX · 最大 10 MB · SHA-256 去重 · 确认后事务写入</p>
        </div>
        {preview && <span className={`batch-status ${preview.batch.status}`}>{preview.batch.status}</span>}
      </header>

      <form className="upload-zone" onSubmit={handleUpload}>
        <label>
          数据类型
          <select value={kind} onChange={(event) => setKind(event.target.value as "sales" | "inventory")}>
            <option value="sales">销售数据</option>
            <option value="inventory">库存快照</option>
          </select>
        </label>
        <label className="file-picker">
          <span>{file ? file.name : "选择 CSV 或 XLSX 文件"}</span>
          <input
            type="file"
            accept=".csv,.xlsx"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </label>
        <button type="submit" disabled={!file || busy}>{busy ? "处理中…" : "上传并校验"}</button>
      </form>

      {notice && <div className="inline-notice">{notice}</div>}

      {preview && (
        <>
          <div className="import-stats">
            <div><span>总行数</span><strong>{preview.batch.total_rows}</strong></div>
            <div><span>可写入</span><strong>{preview.batch.success_rows}</strong></div>
            <div><span>错误行</span><strong>{preview.batch.failed_rows}</strong></div>
            <div><span>SHA-256</span><strong>{preview.batch.sha256.slice(0, 12)}…</strong></div>
          </div>

          <div className="mapping-strip">
            {Object.entries(preview.batch.mapping).map(([target, source]) => (
              <span key={target}>{source} <b>→</b> {target}</span>
            ))}
          </div>

          {preview.rows.length > 0 && (
            <div className="table-wrap">
              <table>
                <thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
                <tbody>
                  {preview.rows.slice(0, 8).map((row, index) => (
                    <tr key={String(row.source_row_number ?? index)}>
                      {columns.map((column) => <td key={column}>{String(row[column] ?? "")}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {preview.errors.length > 0 && (
            <div className="error-list">
              <div><strong>校验错误</strong><a href={importErrorUrl(preview.batch.id, currentUser.id)}>下载错误 CSV</a></div>
              {preview.errors.slice(0, 6).map((issue, index) => (
                <p key={`${issue.row_number}-${issue.field_name}-${index}`}>
                  第 {issue.row_number} 行 · {issue.field_name ?? "记录"} · {issue.message}
                </p>
              ))}
            </div>
          )}

          <button
            className="confirm-import"
            type="button"
            disabled={busy || preview.batch.success_rows === 0 || preview.batch.status === "completed"}
            onClick={() => void handleConfirm()}
          >
            {preview.batch.status === "completed" ? "已写入 SQLite" : "确认并事务写入"}
          </button>
        </>
      )}
    </section>
  );
}
