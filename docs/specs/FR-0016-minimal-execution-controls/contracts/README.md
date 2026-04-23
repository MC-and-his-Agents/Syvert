# FR-0016 contracts

## ExecutionControlPolicy

`ExecutionControlPolicy` 是 Core 执行控制的 canonical carrier，聚合三类最小策略：

- `timeout`：`ExecutionTimeoutPolicy`
- `retry`：`RetryPolicy`
- `concurrency`：`ConcurrencyLimitPolicy`

调用方可以整体缺省 policy；此时 Core 必须物化完整默认 policy：`timeout.timeout_ms=30000`、`retry.max_attempts=1`、`retry.backoff_ms=0`、`concurrency.scope=global`、`concurrency.max_in_flight=1`、`concurrency.on_limit=reject`。一旦 policy 被显式传入，Core 必须按本 contract 校验；部分缺字段不得使用默认值补齐，非法 policy 不得被宽松修复为无限等待、无限重试或无限并发。

## Timeout Contract

- 字段：`timeout_ms`
- 值域：正整数毫秒
- 语义：单次 adapter execution attempt 的 deadline
- 失败 code：`execution_timeout`
- 禁止：total deadline、无限 timeout 表达、adapter 私有 timeout 替代 Core timeout

## Retry Contract

- Caller-visible 字段：`max_attempts`、`backoff_ms`
- `max_attempts`：正整数，包含首次执行；`1` 表示不重试
- `backoff_ms`：非负整数毫秒，固定等待
- Core 固定可重试 outcome：`execution_timeout` 与 `error.category=platform`；该集合不是 caller-visible policy 字段
- 禁止：指数退避、jitter、自定义 predicate、错误码 DSL、无限 retry、caller-supplied `retryable_outcomes`

## Concurrency Contract

- 字段：`scope`、`max_in_flight`、`on_limit`
- `scope`：`global`、`adapter`、`adapter_capability`
- `max_in_flight`：正整数
- `on_limit`：caller-visible required field；`v0.6.0` 固定且只允许 `reject`
- 失败 code：`concurrency_limit_exceeded`
- 禁止：缺失 `on_limit`、queue、wait、priority、fairness、distributed slot

## TaskRecord / Envelope 投影

- 同一任务的所有 attempts 共享同一 `task_id` 与同一条 TaskRecord。
- attempt 不单独创建 durable TaskRecord。
- durable `accepted` 前发生的 concurrency rejection 不创建伪造 TaskRecord。
- durable `accepted` 后发生的 retry slot reacquire rejection 必须把同一 TaskRecord 收口为 `failed`，使用 `concurrency_limit_exceeded`，且不得再继续 retry。
- timeout / retry / concurrency 失败继续复用 `FR-0005` failed envelope 顶层结构。
- 成功结果不改写 `raw` / `normalized` contract。
