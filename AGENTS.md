# EcommerceMVP 仓库开发规则

## 项目范围

- 本仓库是全新的电商企业内部 Agent 工作流 MVP，不复制或修改其他项目。
- 采用模块化单体：`frontend/` 为 React，`backend/` 为 FastAPI，SQLite 为 MVP 数据库。
- 第一版包含美工、销售、选品三个部门；不接入真实采购、广告投放、ERP、Shopify、Amazon SP-API 或正式身份认证。

## 目录约定

- `frontend/`：React 页面、组件、前端 API 客户端和类型。
- `backend/app/`：API、配置、数据库、领域服务、Agent、Tool、Skill、Workflow 和 Provider。
- `backend/tests/`：后端自动化测试。
- `tests/`：跨服务、端到端和验收测试。
- `docs/`：产品与工程设计文档。
- `scripts/`：可重复执行的开发、校验和仿真数据脚本。
- `data/samples/`：可提交的固定种子样例数据；不得包含真实业务数据。
- `uploads/`、`generated/`：运行时文件目录，只提交 `.gitkeep`。

## 安全与数据规则

- 不提交 `.env`、API Key、密码、Token、SQLite 数据库、用户上传文件或模型生成图片。
- 不在日志、测试快照、Issue、Commit 或 PR 中输出真实凭据。
- 不执行危险删除、`git reset --hard`、强制推送或远程历史重写。
- 上传文件必须校验类型、大小和安全文件名；运行时目录与源码目录分离。
- Agent 不得执行任意 SQL、Python、Shell，也不得直接获得数据库连接。

## 架构一致性

- API Pydantic 模型、数据库模型与前端 TypeScript 类型必须保持一致。
- 业务指标和补货数量由可测试的后端代码计算；模型仅负责意图理解、工具选择和结果解释。
- Tool 是带明确输入输出模型的原子函数；Skill 封装业务规则；Workflow 编排可追踪步骤；Provider 适配外部模型。
- Dashboard 与 Agent 必须复用同一指标计算服务。
- 关键写入使用事务；导入失败必须回滚。

## 质量门禁

- 修改后至少运行与改动相关的单元测试、类型检查或构建检查。
- API 或数据库变更必须同步测试和文档。
- 修复缺陷时应添加能复现问题的测试。
- Mock 模式必须在没有模型密钥时可启动和演示。
- 每阶段汇报完成内容、修改文件、测试结果、遗留问题和下一步。

## Git 与 GitHub

- 默认分支为 `main`；M0 初始化提交可直接建立在 `main`。
- M1 及后续阶段使用独立的 `feat/...` 分支和 Pull Request。
- Commit 应聚焦且可审查；推送前检查 `git diff --check`、测试结果和暂存范围。
- 不自动合并 Pull Request；不得使用 `git push --force`，不得删除远程分支或历史。
- Issue 必须包含背景、范围、不包含内容、任务、验收标准、测试要求和依赖关系。
