import { useCallback, useEffect, useState } from "react";

import {
  createImageVersion,
  fetchImageAssets,
  fetchImageVersions,
  imageContentUrl,
  retryImageVersion,
  uploadImageAsset,
} from "../api/images";
import type { DemoUser, Project } from "../types/domain";
import type { ImageAsset, ImageVersion } from "../types/images";

type ArtworkPanelProps = {
  project: Project;
  currentUser: DemoUser;
  conversationId: string;
};

export function ArtworkPanel({ project, currentUser, conversationId }: ArtworkPanelProps) {
  const [assets, setAssets] = useState<ImageAsset[]>([]);
  const [versions, setVersions] = useState<ImageVersion[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [sourceId, setSourceId] = useState("");
  const [parentVersionId, setParentVersionId] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("提亮商品主体，增强对比度，保持结构与比例不变。");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");

  const reload = useCallback(async () => {
    if (!conversationId) return;
    const [nextAssets, nextVersions] = await Promise.all([
      fetchImageAssets(conversationId, currentUser.id),
      fetchImageVersions(conversationId, currentUser.id),
    ]);
    setAssets(nextAssets);
    setVersions(nextVersions);
    setSourceId((existing) => existing || nextAssets[0]?.id || "");
  }, [conversationId, currentUser.id]);

  useEffect(() => {
    setAssets([]);
    setVersions([]);
    setSourceId("");
    setParentVersionId(null);
    void reload().catch((reason: unknown) => {
      setNotice(reason instanceof Error ? reason.message : "图片历史加载失败");
    });
  }, [reload]);

  async function handleUpload(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setNotice("");
    try {
      const created = await uploadImageAsset({
        projectId: project.id,
        conversationId,
        userId: currentUser.id,
        file,
      });
      setSourceId(created.id);
      setParentVersionId(null);
      setFile(null);
      await reload();
      setNotice("原图已安全保存，后续编辑不会覆盖该文件。");
    } catch (reason) {
      setNotice(reason instanceof Error ? reason.message : "原图上传失败");
    } finally {
      setBusy(false);
    }
  }

  async function handleEdit(event: React.FormEvent) {
    event.preventDefault();
    if (!sourceId || !prompt.trim()) return;
    setBusy(true);
    setNotice("");
    try {
      const version = await createImageVersion({
        conversationId,
        userId: currentUser.id,
        sourceAttachmentId: sourceId,
        parentVersionId,
        prompt: prompt.trim(),
      });
      await reload();
      setParentVersionId(version.status === "completed" ? version.id : parentVersionId);
      setNotice(
        version.status === "completed"
          ? "新版本已生成并保存。"
          : `生成失败，请重试：${version.error_message ?? "未知错误"}`,
      );
    } catch (reason) {
      setNotice(reason instanceof Error ? reason.message : "图片编辑请求失败");
    } finally {
      setBusy(false);
    }
  }

  async function handleRetry(version: ImageVersion) {
    setBusy(true);
    try {
      const result = await retryImageVersion(version.id, currentUser.id);
      await reload();
      setNotice(result.status === "completed" ? "重试成功，新版本已保存。" : "重试仍失败。");
    } catch (reason) {
      setNotice(reason instanceof Error ? reason.message : "重试失败");
    } finally {
      setBusy(false);
    }
  }

  if (!conversationId) {
    return <div className="empty-state"><strong>请先新建聊天</strong><p>图片与版本将归属于当前独立聊天。</p></div>;
  }

  return (
    <section className="import-workspace artwork-workspace">
      <header className="import-heading">
        <div>
          <p className="kicker">VERSIONED IMAGE WORKFLOW</p>
          <h1>商品图编辑</h1>
          <p>上传原图 → 输入要求 → 生成 → 继续修改 → 下载版本</p>
        </div>
        <span className="batch-status">MOCK PROVIDER</span>
      </header>

      <form className="upload-zone image-upload" onSubmit={handleUpload}>
        <label className="file-picker">
          <span>{file?.name ?? "选择 JPEG / PNG / WEBP 原图"}</span>
          <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        </label>
        <button type="submit" disabled={!file || busy}>{busy ? "处理中…" : "上传原图"}</button>
      </form>

      {notice && <div className="inline-notice">{notice}</div>}

      {assets.length > 0 && (
        <div className="image-flow">
          <aside className="source-gallery">
            <span>原图（不可覆盖）</span>
            {assets.map((asset) => (
              <button
                type="button"
                className={asset.id === sourceId ? "active" : ""}
                key={asset.id}
                onClick={() => { setSourceId(asset.id); setParentVersionId(null); }}
              >
                <img src={imageContentUrl(asset.id, currentUser.id)} alt={asset.original_name} />
                <small>{asset.original_name}</small>
              </button>
            ))}
          </aside>
          <div className="edit-column">
            <form className="image-prompt" onSubmit={handleEdit}>
              <label>
                修改要求
                <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} />
              </label>
              <div>
                <span>{parentVersionId ? `基于版本 ${parentVersionId.slice(0, 8)} 继续修改` : "基于原图生成"}</span>
                {parentVersionId && <button type="button" onClick={() => setParentVersionId(null)}>改用原图</button>}
                <button type="submit" disabled={busy || !prompt.trim()}>{busy ? "生成中…" : "生成并保存版本"}</button>
              </div>
            </form>

            <div className="version-grid">
              {versions.filter((version) => version.source_attachment_id === sourceId).map((version) => (
                <article key={version.id} className={version.status}>
                  {version.output_attachment_id ? (
                    <img src={imageContentUrl(version.output_attachment_id, currentUser.id)} alt={`生成版本 ${version.id.slice(0, 8)}`} />
                  ) : <div className="failed-preview">生成失败</div>}
                  <div>
                    <span>v-{version.id.slice(0, 8)} · {version.model_name}</span>
                    <p>{version.prompt}</p>
                    <small>{version.status} · 尝试 {version.retry_count} 次</small>
                  </div>
                  <footer>
                    {version.status === "completed" && version.output_attachment_id && (
                      <>
                        <button type="button" onClick={() => { setSourceId(version.source_attachment_id); setParentVersionId(version.id); }}>基于此版继续</button>
                        <a href={imageContentUrl(version.output_attachment_id, currentUser.id, true)}>下载</a>
                      </>
                    )}
                    {version.status === "failed" && <button type="button" disabled={busy} onClick={() => void handleRetry(version)}>重试</button>}
                  </footer>
                </article>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
