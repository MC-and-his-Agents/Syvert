# FR-0018 Contracts README

## Canonical Service Surface

- `submit`
  - 用途：接收 HTTP 任务提交，并把请求接到既有 Core / `TaskRecord` durable path
- `status`
  - 用途：按 `task_id` 回读 durable `TaskRecord` 当前状态 truth
- `result`
  - 用途：按 `task_id` 回读 durable `TaskRecord` 的结果语义

## Shared Path Contract

- HTTP API 只负责 transport ingress/egress
- 一旦进入 Core，以下语义必须继续复用 shared contract：
  - `task_id`
  - `adapter_key`
  - `capability`
  - `TaskRecord.status`
  - success / failed envelope
- HTTP API 禁止：
  - 直接调用 adapter
  - 直接写 durable `TaskRecord`
  - 维护影子任务表、影子状态缓存、影子结果文件
  - 生成第二套 success/failed/result envelope

## Endpoint Semantics

- `submit`
  - 成功：任务已进入 shared durable path，并返回最小 receipt：`task_id`、`status`
  - 失败：复用 shared failed envelope；若失败发生在 durable `accepted` 之前，不得伪造 task history
- `status`
  - 成功：返回 durable `TaskRecord` 的当前状态视图，最少可回映 `task_id`、`status`、`created_at`、`updated_at`、`terminal_at?`
  - 失败：record 不存在、不可用或请求非法时，复用 shared failed envelope
- `result`
  - `record.status=succeeded`：返回 durable success envelope，继续包含 `raw payload` 与 `normalized result`
  - `record.status=failed`：返回 durable failed envelope
  - `record.status=accepted|running`：返回 `result_not_ready` 的 shared failed 语义，不得伪造终态

## Fail-Closed Cases

以下情况都必须视为 contract violation 或不可用分支：

- HTTP API 旁路 Core / `TaskRecord` 主路径
- `status` / `result` 消费影子 truth，而不是 durable `TaskRecord`
- 终态 success envelope 丢失 `raw` 或 `normalized`
- 终态 failed envelope 被重新包装为 API 私有错误对象
- 非终态 `accepted` / `running` 被伪造成可用终态结果
- record 不存在、record 非法、store 不可用、序列化失败时返回非结构化 transport 成功页

## Explicitly Out Of Scope

- 认证
- 多租户
- RBAC
- 分布式队列
- 复杂查询 DSL
- 完整控制台
- 长轮询 / webhook / 流式返回
- framework / router / OpenAPI 生成链绑定
