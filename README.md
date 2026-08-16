# EcommerceMVP

电商企业内部 Agent 工作流 MVP。项目从零构建，首版规划美工、销售和选品三个部门，以可追踪的聊天、受控工具、确定性业务规则和可替换模型 Provider 为核心。

当前为 **M0 工程底座**：提供 FastAPI + SQLite 健康检查、React 工作台首页、Mock 模式配置、自动化测试和 Docker Compose。完整部门流程将在后续里程碑实现。

## 技术栈

- 前端：React 19、TypeScript、Vite
- 后端：FastAPI、Pydantic、SQLAlchemy
- 数据库：SQLite
- 容器：Docker Engine、Docker Compose、Nginx
- 模型规划：DeepSeek（销售/选品）、千问图片编辑（美工）

## 快速开始

### 1. 本地后端

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
.venv/bin/uvicorn app.main:app --app-dir backend --reload
```

健康检查：http://localhost:8000/api/v1/health
API 文档：http://localhost:8000/docs

### 2. 本地前端

另开一个终端：

```bash
cd frontend
npm install
npm run dev
```

工作台：http://localhost:5173

Vite 会把 `/api` 转发到本地后端。

### 3. Docker Compose

```bash
docker compose up --build -d
docker compose ps
```

- 工作台：http://localhost:8080
- API 健康检查：http://localhost:8000/api/v1/health

停止容器（不会删除运行数据）：

```bash
docker compose down
```

## 配置与密钥

默认 `MOCK_MODE=true`，不需要任何模型 Key。若后续测试真实 Provider，只在本地创建 `.env` 并填写：

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`
- `QWEN_IMAGE_API_KEY`
- `QWEN_IMAGE_BASE_URL`
- `QWEN_IMAGE_MODEL`

不要把密钥发送到聊天或提交到 Git。完整字段见 [`.env.example`](.env.example)。

## 测试

完成本地依赖安装后：

```bash
./scripts/check.sh
```

也可分别运行：

```bash
PYTHONPATH=backend .venv/bin/pytest -c backend/pyproject.toml backend/tests
cd frontend && npm test && npm run typecheck && npm run build
```


## 目录

```text
frontend/       React 工作台
backend/        FastAPI API、配置和数据库底座
tests/          跨服务与验收测试（后续）
docs/           产品和工程设计
scripts/        可重复执行的开发脚本
data/samples/   固定种子仿真样例（后续）
data/runtime/   SQLite 运行数据（不提交）
uploads/        用户上传（不提交）
generated/      模型生成文件（不提交）
```

## 设计与路线图

- [需求说明](docs/requirements.md)
- [系统架构](docs/architecture.md)
- [数据库设计](docs/database-design.md)
- [API 设计](docs/api-design.md)
- [Agent 设计](docs/agent-design.md)
- [开发计划](docs/development-plan.md)
- [验收标准](docs/acceptance-criteria.md)

仓库协作与安全规则见 [AGENTS.md](AGENTS.md)。

> 界面中的角色切换仅用于演示，不代表真实身份认证。任何补货建议都必须由人工确认，MVP 不执行真实采购。
