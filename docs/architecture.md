# 系统架构设计

## 1. 架构选择

采用前后端分离的模块化单体。单个 FastAPI 服务承载权限归属、聊天、导入、指标、Agent 编排和图片任务；React 提供内部工作台；SQLite 保存结构化数据；本地文件系统保存上传与生成文件。

这样可在 MVP 阶段保持部署和事务简单，同时通过明确模块边界为未来拆分服务保留空间。

## 2. 运行时组件

| 组件 | 职责 | 技术 |
| --- | --- | --- |
| Web | 工作台、管理员、部门、项目聊天与流程 UI | React + TypeScript + Vite |
| API | HTTP 契约、验证、错误处理、CORS | FastAPI + Pydantic |
| Domain Services | 项目、聊天、导入、指标、补货、图片版本业务规则 | Python |
| Agent Runtime | 上下文组装、模型选择、工具编排、运行追踪 | Python |
| Providers | DeepSeek、千问和 Mock 适配器 | HTTP 客户端/Mock |
| Persistence | 领域数据与执行记录 | SQLAlchemy + SQLite |
| File Storage | 原始报表、附件、原图、生成图片 | 本地挂载目录 |

## 3. 后端模块边界

- `api/`：路由和请求/响应转换，不承载业务规则。
- `core/`：环境配置、日志、错误和安全限制。
- `db/`：连接、事务、Base 与迁移。
- `models/`：持久化模型。
- `schemas/`：Pydantic API 和 Tool 契约。
- `repositories/`：限定的数据访问方法。
- `services/`：指标、导入、聊天和项目业务服务。
- `tools/`：模型可调用的受控原子操作，不暴露 Session。
- `skills/`：跨 Tool 的业务能力与确定性规则。
- `workflows/`：可恢复、可跟踪的步骤编排。
- `providers/`：外部模型 API 与 Mock Provider。
- `agents/`：系统提示词、上下文构建、工具选择与解释。

依赖方向为 `api/agents/workflows → services/tools/skills → repositories → db`。Provider 通过接口注入，不允许领域逻辑依赖具体供应商 SDK。

## 4. 请求与数据流

### 聊天分析

1. API 验证用户、部门、项目成员和会话归属。
2. 保存用户消息并创建 `agent_run`。
3. 上下文构建器加载项目摘要、结构化范围和近期消息。
4. Agent 选择白名单 Tool；Tool 再调用领域服务。
5. 领域服务通过 Repository 查询数据并由代码计算指标。
6. Tool 调用和结果持久化，模型解释结构化结果。
7. 保存助手消息并更新项目摘要/范围。

### 报表导入

文件先落入隔离上传目录并计算 SHA-256。解析、映射、校验和预览不写业务事实；用户确认后在单个事务中写入事实表和批次状态，错误明细单独持久化并支持导出。

### 图片编辑

每次编辑创建不可变任务和目标版本。Provider 输出写入 `generated/`，成功后更新版本元数据；失败保留请求和错误，重试创建新的运行记录而不覆盖原图。

## 5. 部署结构

- `frontend` 容器：构建静态资源并由 Nginx 提供服务，同时反向代理 `/api`。
- `backend` 容器：Uvicorn 运行 FastAPI。
- 持久化挂载：`./data/runtime`、`./uploads`、`./generated`。
- 健康检查：后端 `/api/v1/health`；前端根页面。

## 6. 配置与安全边界

- 所有配置来自环境变量；仓库仅提交 `.env.example`。
- 默认 `MOCK_MODE=true`，缺少模型 Key 不阻塞启动。
- 文件名由服务端生成，客户端文件名仅作元数据。
- CORS 仅允许显式配置的前端源。
- 模型只接触 Pydantic Tool 契约，不接触数据库、文件系统或执行环境。
- 日志对密钥、原始敏感内容和大体量 Tool 输出做脱敏/摘要。

## 7. 可演进方向

正式身份认证、对象存储、异步任务队列和 PostgreSQL 可在验证 MVP 后引入。领域服务、Provider 和 Workflow 接口应保持可替换，但当前不提前拆分微服务。
