import { useCallback, useEffect, useState } from "react";

import {
  createConversation,
  fetchConversations,
  fetchMessages,
  renameConversation,
  sendMessage,
} from "../api/chat";
import type {
  ChatMessage,
  Conversation,
  DemoUser,
  Department,
  Project,
} from "../types/domain";
import { SalesImportPanel } from "./SalesImportPanel";

type ProjectWorkspaceProps = {
  project: Project;
  department: Department;
  currentUser: DemoUser;
  onBack: () => void;
};

export function ProjectWorkspace({
  project,
  department,
  currentUser,
  onBack,
}: ProjectWorkspaceProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [workspaceMode, setWorkspaceMode] = useState<"chat" | "import">("chat");

  const activeConversation = conversations.find(
    (conversation) => conversation.id === activeConversationId,
  );

  const loadConversationList = useCallback(async () => {
    const items = await fetchConversations(project.id, currentUser.id);
    setConversations(items);
    setActiveConversationId((existing) => existing || items[0]?.id || "");
    return items;
  }, [currentUser.id, project.id]);

  const loadMessageList = useCallback(
    async (conversationId: string) => {
      if (!conversationId) {
        setMessages([]);
        return;
      }
      setMessages(await fetchMessages(conversationId, currentUser.id));
    },
    [currentUser.id],
  );

  useEffect(() => {
    void loadConversationList().catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "聊天列表加载失败");
    });
  }, [loadConversationList]);

  useEffect(() => {
    void loadMessageList(activeConversationId).catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "消息加载失败");
    });
  }, [activeConversationId, loadMessageList]);

  async function handleNewConversation() {
    setBusy(true);
    setError("");
    try {
      const created = await createConversation(project.id, currentUser.id);
      await loadConversationList();
      setActiveConversationId(created.id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "新建聊天失败");
    } finally {
      setBusy(false);
    }
  }

  async function handleRename() {
    if (!activeConversation) return;
    const title = window.prompt("新的聊天名称", activeConversation.title)?.trim();
    if (!title || title === activeConversation.title) return;
    setBusy(true);
    try {
      await renameConversation(activeConversation.id, currentUser.id, title);
      await loadConversationList();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "重命名失败");
    } finally {
      setBusy(false);
    }
  }

  async function handleSend(event: React.FormEvent) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || !activeConversationId) return;
    setBusy(true);
    setError("");
    try {
      await sendMessage(activeConversationId, currentUser.id, content);
      setDraft("");
      await Promise.all([loadMessageList(activeConversationId), loadConversationList()]);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "消息发送失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="project-workspace">
      {department.code === "sales" && (
        <nav className="workflow-tabs" aria-label="销售项目功能">
          <button className={workspaceMode === "chat" ? "active" : ""} onClick={() => setWorkspaceMode("chat")}>项目聊天</button>
          <button className={workspaceMode === "import" ? "active" : ""} onClick={() => setWorkspaceMode("import")}>报表导入</button>
        </nav>
      )}
      {workspaceMode === "import" && department.code === "sales" ? (
        <SalesImportPanel project={project} currentUser={currentUser} />
      ) : (
      <section className="chat-shell">
      <aside className="conversation-sidebar">
        <button className="back-button" type="button" onClick={onBack}>← 返回项目</button>
        <div className="sidebar-project">
          <span>{department.name}</span>
          <strong>{project.name}</strong>
        </div>
        <button className="new-chat-button" type="button" onClick={() => void handleNewConversation()} disabled={busy}>
          ＋ 新建聊天
        </button>
        <div className="conversation-list">
          {conversations.map((conversation) => (
            <button
              type="button"
              className={conversation.id === activeConversationId ? "active" : ""}
              onClick={() => setActiveConversationId(conversation.id)}
              key={conversation.id}
            >
              <span>{conversation.title}</span>
              <small>{new Date(conversation.updated_at).toLocaleDateString("zh-CN")}</small>
            </button>
          ))}
        </div>
      </aside>

      <div className="chat-main">
        <header className="chat-header">
          <div>
            <span className="project-id">{project.id.slice(0, 8)}</span>
            <h1>{activeConversation?.title ?? "选择或新建聊天"}</h1>
          </div>
          {activeConversation && <button type="button" onClick={() => void handleRename()}>重命名</button>}
        </header>

        {error && <div className="inline-notice error-notice">{error}</div>}

        <div className="message-stream" aria-live="polite">
          {!activeConversation && (
            <div className="chat-empty">
              <span>⌁</span>
              <strong>为这个项目建立第一段对话</strong>
              <p>每个聊天拥有独立历史和上下文。</p>
            </div>
          )}
          {activeConversation && messages.length === 0 && (
            <div className="chat-empty">
              <span>⌁</span>
              <strong>开始新的项目对话</strong>
              <p>当前 M2 会先保存消息；Agent 将在后续里程碑接入。</p>
            </div>
          )}
          {messages.map((message) => (
            <article className={`message ${message.role}`} key={message.id}>
              <span>{message.role === "user" ? currentUser.display_name : message.role}</span>
              <p>{message.content}</p>
            </article>
          ))}
        </div>

        <form className="composer" onSubmit={handleSend}>
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder={activeConversation ? "输入项目问题或工作要求…" : "请先新建聊天"}
            disabled={!activeConversation || busy}
          />
          <button type="submit" disabled={!activeConversation || busy || !draft.trim()}>发送</button>
        </form>
      </div>
      </section>
      )}
    </div>
  );
}
