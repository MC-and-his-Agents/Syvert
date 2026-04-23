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
  - `ExecutionControlPolicy`
  - `ExecutionControlEvent`
  - success / failed envelope
  - `runtime_result_refs`
- HTTP API 禁止：
  - 直接调用 adapter
  - 直接写 durable `TaskRecord`
  - 维护影子任务表、影子状态缓存、影子结果文件、影子控制事件流
  - 生成第二套 success/failed/result envelope
  - 把 transport 私有 retry 逻辑注入共享执行路径

## Capability Boundary

- 当前批准的 HTTP public capability 只有 `content_detail_by_url`
- 进入共享请求模型后，仍按既有兼容投影落到 adapter-facing capability family `content_detail`
- HTTP service 不得自行扩张 capability 值域，也不得把 adapter-facing family 直接暴露为新的 public contract

## Execution Control Contract

- `submit` 可显式携带可选 `execution_control_policy`
  - 该字段只能映射到共享 `ExecutionControlPolicy`
  - 若缺失，则使用共享 Core path 默认策略
  - 若形状非法、语义不在共享 contract 内，或无法通过共享 idempotency safety gate 前提，则必须在 durable `accepted` 之前 fail-closed
- pre-accepted concurrency rejection
  - 必须投影为 shared failed envelope
  - `error.category` 固定为 `invalid_input`
  - 不得创建 durable `TaskRecord`
- retryable predicate
  - 不是整个 `platform` category
  - 当前只有两类 transient failure 可进入共享 retry 判定：
    - `execution_timeout` 控制结果，正常表现为 `error.category=platform` 且 `error.details.control_code=execution_timeout`
    - `error.category=platform` 且 `error.details.retryable=true`
  - 即便命中上述条件，也仍必须通过共享 `ExecutionControlPolicy` 的 idempotency safety gate
- closeout / control-state failure
  - 必须投影为 `runtime_contract`
  - HTTP 不得把该类故障重新包装为普通平台失败
- post-accepted retry reacquire rejection
  - 只能追加 `ExecutionControlEvent` / `details` / `runtime_result_refs` 等控制事实
  - 不得改写上一已完成 attempt 的终态 `error.code` / `error.category`

## Endpoint Semantics

- `submit`
  - 成功：任务已进入 shared durable path，并返回最小 receipt：`task_id`、`status`
  - 失败：复用 shared failed envelope；若失败发生在 durable `accepted` 之前，不得伪造 task history
- `status`
  - 成功：返回 durable `TaskRecord` 的当前状态视图，最少可回映 `task_id`、`status`、`created_at`、`updated_at`、`terminal_at?`
  - 成功：若共享 truth 已持有 `ExecutionControlEvent` 或 `runtime_result_refs`，HTTP 不得吞掉这些字段
  - 失败：record 不存在、不可用、control-state truth 不可信或请求非法时，复用 shared failed envelope
- `result`
  - `record.status=succeeded`：直接返回 durable success envelope，继续包含共享字段 `raw` 与 `normalized`
  - `record.status=failed`：返回 durable failed envelope，并继续保留共享 `error.category` / `error.code` / `error.details`
  - `record.status=accepted|running`：直接返回 `result_not_ready` / `invalid_input` 的 shared failed envelope，不得伪造终态，也不得包裹成第三套 result schema
  - `task_id` 缺失：返回 `invalid_input` 的 shared failed envelope
  - `task_id` 形状非法或不满足共享任务键 contract：返回 `invalid_task_id` / `runtime_contract` 的 shared failed envelope
  - `task_id` 不存在 durable record：返回 `task_record_not_found` / `invalid_input` 的 shared failed envelope
  - store / record contract / 共享序列化不可用：返回 `task_record_unavailable` / `runtime_contract` 的 shared failed envelope
  - 若共享结果中已有 `runtime_result_refs`：HTTP 必须继续透传这些 ref

## Fail-Closed Cases

以下情况都必须视为 contract violation 或不可用分支：

- HTTP API 旁路 Core / `TaskRecord` 主路径
- `status` / `result` 消费影子 truth，而不是 durable `TaskRecord`
- 终态 success envelope 丢失 `raw` 或 `normalized`
- 终态 failed envelope 被重新包装为 API 私有错误对象
- 非终态 `accepted` / `running` 被伪造成可用终态结果
- `execution_timeout` 被重分类为 `runtime_contract`，或其 `error.details.control_code=execution_timeout` 被吞掉
- closeout/control-state failure 被误报为普通 `platform` 失败
- 整个 `platform` category 被粗暴视为 retryable
- pre-accepted concurrency rejection 被错误地创建为 durable `TaskRecord`
- post-accepted retry reacquire rejection 覆盖了上一已完成 attempt 的终态 `error.code` / `error.category`
- `runtime_result_refs`、控制事件细节或共享 `error.details.retryable` 被 transport 层裁剪
- record 不存在、record 非法、store 不可用、序列化失败时返回非结构化 transport 成功页

## Dependency Contract

- `FR-0018` 必须消费 `FR-0008` 的 durable `TaskRecord` truth
- `FR-0018` 必须消费 `FR-0009` 的 same-path query truth
- `FR-0018` 必须消费 `FR-0016` 的执行控制、retryable predicate 与控制面失败分类 truth
- `FR-0018` 必须消费 `FR-0017` 的结构化控制结果、指标与 `runtime_result_refs` truth
- HTTP transport 不得把这些上游 FR 的共享 truth 降级为 API 私有简化语义

## Explicitly Out Of Scope

- 认证
- 多租户
- RBAC
- 分布式队列
- 复杂查询 DSL
- 完整控制台
- 长轮询 / webhook / 流式返回
- framework / router / OpenAPI 生成链绑定
- transport 私有重试 DSL 或 transport 私有控制状态机
