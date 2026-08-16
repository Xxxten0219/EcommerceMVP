# API 设计

## 1. 约定

- 基础路径：`/api/v1`。
- JSON 字段使用 `snake_case`；时间为 ISO 8601 UTC。
- 请求与响应使用 Pydantic 模型，前端维护对应 TypeScript 类型。
- 错误响应使用 FastAPI `detail`；前端不显示内部堆栈或 Provider 凭据。
- MVP 数据量较小，列表端点直接返回类型化数组；分页留待企业化阶段加入。
- MVP 角色由显式演示用户选择传入；后端仍校验项目成员关系，不能只依赖前端隐藏。

## 2. M0 接口

### `GET /api/v1/health`

检查 API 与 SQLite 连接，返回：

```json
{
  "status": "ok",
  "service": "ecommerce-mvp-api",
  "version": "0.1.0",
  "database": "ok",
  "mock_mode": true
}
```

数据库不可用时返回 HTTP 503，`status` 为 `degraded`。

## 3. 后续资源接口

### 管理与项目（M1）

- `GET /departments`
- `GET/POST /users`
- `GET/POST /projects`
- `POST /projects/{project_id}/members`
- `DELETE /projects/{project_id}/members/{user_id}`

### 聊天（M2）

- `GET/POST /projects/{project_id}/conversations`
- `PATCH /conversations/{conversation_id}`
- `GET /conversations/{conversation_id}/messages`
- `POST /conversations/{conversation_id}/messages`
- `POST /conversations/{conversation_id}/agent-runs`

### 销售导入（M3）

- `POST /imports`：上传 CSV/XLSX，最大 10 MB。
- `POST /imports/{batch_id}/mapping`：保存字段映射并校验。
- `GET /imports/{batch_id}/preview`
- `POST /imports/{batch_id}/confirm`
- `GET /imports/{batch_id}`
- `GET /imports/{batch_id}/errors.csv`

上传使用 `multipart/form-data`。服务端流式限制大小、计算 SHA-256，并返回重复批次引用而不是重复写入。

### 指标与选品（M4–M5）

- `GET /projects/{project_id}/selection-overview`
- `POST /conversations/{conversation_id}/agent-runs`
- `GET /agent-runs/{run_id}`
- `GET /agent-runs/{run_id}/tool-calls`

Dashboard 和 Agent Tool 均调用相同领域服务，禁止各自复制指标公式。

### 图片编辑（M6）

- `POST /image-assets`：上传不可变原图，校验项目与聊天归属。
- `GET /conversations/{conversation_id}/image-assets`：查看聊天原图。
- `POST /image-versions`：基于原图或父版本创建编辑任务。
- `GET /conversations/{conversation_id}/image-versions`：查看版本链和生成状态。
- `POST /image-versions/{version_id}/retry`
- `GET /attachments/{attachment_id}/content`：预览或下载有权访问的图片。

真实 Provider 按百炼官方 Qwen-Image-Edit 同步 HTTP 契约调用
`services/aigc/multimodal-generation/generation`；默认 Mock 模式不请求外部服务。

## 4. 受控 Tool 契约

Tool 不是公开任意执行接口。Agent Runtime 通过注册表按名称调用：

- `query_sales_metrics`
- `query_inventory_status`
- `calculate_sales_trend`
- `calculate_inventory_pressure`
- `recommend_restock`
- `get_import_batch_status`

每个 Tool 的输入必须限定站点、平台、时间、品类、SKU、聚合粒度等枚举或受约束字段。输出为结构化指标和数据范围，不返回数据库连接、SQL 或无限制明细。

## 5. 状态码

- `200/201`：成功查询/创建。
- `202`：异步模型或图片任务已接受。
- `400`：格式或状态转换不合法。
- `403`：演示用户不属于项目。
- `404`：资源不存在或不可见。
- `409`：重复文件、重复成员或并发状态冲突。
- `413`：上传超过 10 MB。
- `422`：Pydantic/业务字段校验失败。
- `503`：数据库或 Provider 暂不可用。
