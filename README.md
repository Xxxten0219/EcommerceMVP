# EcommerceMVP

电商企业内部 Agent 工作流 MVP，覆盖美工、销售和选品三个部门。项目采用 React + FastAPI + SQLite 的模块化单体，强调可追踪聊天、受控工具、确定性业务规则和可替换 Provider。

> 当前是演示角色切换，不代表真实身份认证。任何补货建议都必须人工确认，MVP 不执行真实采购。

## 已实现

- 组织与项目：管理员创建演示员工、项目和成员分配，员工只看到已分配项目。
- 聊天与上下文：项目内多会话、重命名、独立历史、项目摘要和结构化范围持久化。
- 销售导入：CSV/XLSX、10 MB 限制、SHA-256 去重、字段映射、校验预览、事务写入、错误 CSV。
- Agent 运行时：DeepSeek/Mock Provider，六个 Pydantic 受控工具，Agent Run 与工具耗时追踪。
- 选品决策：销售趋势、环比、毛利、退款、库存覆盖和补货数量均由后端代码计算。
- 商品图编辑：不可变原图、版本链、基于历史版继续编辑、失败重试和下载；默认使用 Mock，已提供千问适配器。

## 最快启动

默认 `MOCK_MODE=true`，无需任何 API Key：

```bash
docker compose up --build -d
docker compose ps
./scripts/smoke.sh
```

- 工作台：http://localhost:8080
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/v1/health

停止容器但保留 SQLite、上传和生成数据：`docker compose down`。

## 五分钟演示

1. 使用“管理员 · 演示管理员”查看三部门，进入管理员页面创建员工/项目/分配。
2. 切换“员工 · 周启”，进入销售项目，在“报表导入”上传 `data/samples/sales_import_demo.csv`，查看坏行后确认写入。
3. 切换“员工 · 陈禾”，进入选品项目并新建聊天，输入：`以每个月为周期分析龙门架的销售和库存`。
4. 继续追问：`那么这个商品本月要不要增购？`，展开底部“运行追踪”查看工具链。
5. 切换“员工 · 林然”，进入美工项目并新建聊天。可先运行 `.venv/bin/python scripts/generate_demo_image.py`，然后在“图片编辑”上传 `data/runtime/demo-product.png`，生成、继续修改并下载。

可验证的仿真情形：龙门架增长且低库存；跑步机下降且积压；哑铃高销量但低毛利；拉力器最近退款率异常；季节性波动可复现。

## 本地开发

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
npm --prefix frontend install
.venv/bin/uvicorn app.main:app --app-dir backend --reload
```

另开终端运行 `npm --prefix frontend run dev`，访问 http://localhost:5173。Vite 会将 `/api` 代理到本地后端。

## 配置与密钥

仅需真实模型时，在本地创建不受 Git 跟踪的 `.env`，把 `MOCK_MODE` 设为 `false`，填写：

- `DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL`
- `QWEN_IMAGE_API_KEY`、`QWEN_IMAGE_BASE_URL`、`QWEN_IMAGE_MODEL`

不要把密钥发到聊天、Issue 或提交到 Git。完整字段见 [`.env.example`](.env.example)。千问地域 Key 必须与 Base URL 匹配；请按百炼当前工作空间地域配置。

## 质量检查

`./scripts/check.sh` 会运行 Ruff、后端单元/集成测试、前端测试、TypeScript 检查、生产构建与 `git diff --check`。Docker 启动后用 `./scripts/smoke.sh` 验证宿主机可访问性。

## 目录

```text
frontend/       React 工作台
backend/        FastAPI、Provider、Agent、Tool、Skill 与 Workflow
backend/tests/  后端单元和集成测试
tests/          跨服务验收测试预留目录
docs/           产品和工程设计
scripts/        校验、冒烟和固定数据脚本
data/samples/   可提交的固定种子样例
data/runtime/   SQLite/演示运行数据（不提交）
uploads/        用户上传（不提交）
generated/      生成结果（不提交）
```

## 设计文档

- [需求说明](docs/requirements.md)
- [系统架构](docs/architecture.md)
- [数据库设计](docs/database-design.md)
- [API 设计](docs/api-design.md)
- [Agent 设计](docs/agent-design.md)
- [开发计划](docs/development-plan.md)
- [验收标准](docs/acceptance-criteria.md)

仓库协作与安全规则见 [AGENTS.md](AGENTS.md)。
