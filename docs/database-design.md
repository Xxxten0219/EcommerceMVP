# 数据库设计

## 1. 设计原则

- SQLite 为 MVP 唯一结构化存储，SQLAlchemy 管理模型和事务。
- 使用字符串 UUID 作为业务主键，时间统一存 UTC。
- 归属关系显式保存，不依赖聊天文本推断。
- 文件内容不进入数据库，只保存相对路径、哈希、MIME、大小等元数据。
- 业务事实和执行追踪分离，Tool/Agent 运行可审计。

## 2. 核心关系

`departments → users/projects → project_members → conversations → messages`

每个项目属于一个部门；员工可属于一个部门；`project_members` 负责多对多分配。会话属于项目并记录创建人，消息属于会话并保留发送角色和可选用户。

## 3. 表设计

### 组织与项目

- `departments`：`id`、`code`、`name`、`created_at`。
- `users`：`id`、`department_id`、`display_name`、`role`、`is_active`、`created_at`。
- `projects`：`id`、`department_id`、`name`、`description`、`summary`、`structured_scope_json`、`created_by`、`created_at`、`updated_at`。
- `project_members`：`project_id`、`user_id`、`assigned_by`、`assigned_at`；复合唯一键防止重复分配。

### 聊天与附件

- `conversations`：`id`、`project_id`、`created_by`、`title`、`created_at`、`updated_at`。
- `messages`：`id`、`conversation_id`、`user_id`、`role`、`content`、`metadata_json`、`created_at`；角色限制为 system/user/assistant/tool。
- `attachments`：`id`、`department_id`、`user_id`、`project_id`、`conversation_id`、`message_id`、`kind`、`original_name`、`storage_path`、`mime_type`、`size_bytes`、`sha256`、`created_at`。

### 图片版本

- `image_versions`：`id`、`project_id`、`conversation_id`、`source_attachment_id`、`parent_version_id`、`output_attachment_id`、`prompt`、`provider`、`model_name`、`status`、`error_message`、`created_by`、`created_at`。
- 原图以 attachment 保存；生成版本通过父版本形成不可变链。

### 商品、销售与库存

- `products`：`id`、`sku`、`name`、`category`、`site`、`platform`、`unit_cost`、`is_active`；`sku + site + platform` 唯一。
- `sales_facts`：`id`、`product_id`、`sale_date`、`units_sold`、`revenue`、`cost`、`refund_units`、`import_batch_id`、`source_row_number`。
- `inventory_snapshots`：`id`、`product_id`、`snapshot_date`、`on_hand`、`reserved`、`inbound`、`import_batch_id`。
- 金额使用定点 Decimal 映射，禁止浮点累计。

### 导入

- `import_batches`：`id`、`department_id`、`project_id`、`created_by`、`kind`、`original_name`、`storage_path`、`sha256`、`size_bytes`、`mapping_json`、`status`、`total_rows`、`success_rows`、`failed_rows`、`created_at`、`confirmed_at`、`completed_at`、`error_message`。
- `import_errors`：`id`、`batch_id`、`row_number`、`field_name`、`error_code`、`message`、`raw_row_json`。
- 文件哈希和导入类型建立唯一约束/幂等检查；确认写入使用单事务。

### Agent 追踪

- `agent_runs`：`id`、`department_id`、`user_id`、`project_id`、`conversation_id`、`provider`、`model_name`、`status`、`input_summary`、`output_summary`、`started_at`、`completed_at`、`error_message`。
- `tool_calls`：`id`、`agent_run_id`、`conversation_id`、`tool_name`、`input_json`、`output_summary_json`、`status`、`duration_ms`、`error_message`、`created_at`。

## 4. 关键索引

- 项目成员：`(user_id, project_id)`。
- 会话：`(project_id, updated_at)`；消息：`(conversation_id, created_at)`。
- 销售：`(product_id, sale_date)`；库存：`(product_id, snapshot_date)`。
- 产品查询：`(site, platform, category)` 和唯一 SKU 组合。
- 导入：`(sha256, kind)`、`(project_id, created_at)`。
- Tool 追踪：`(agent_run_id, created_at)`、`(tool_name, status)`。

## 5. 数据生命周期

- `data/runtime/*.db*`、`uploads/*`、`generated/*` 均为运行数据并由 `.gitignore` 排除。
- 样例数据只放在 `data/samples/`，固定种子且不得包含真实企业数据。
- 删除项目等破坏性能力不进入 MVP；默认采用停用或状态变更，避免级联误删审计信息。
