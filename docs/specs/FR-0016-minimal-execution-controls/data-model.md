# FR-0016 数据模型

## 实体清单

- 实体：`ExecutionControlPolicy`
  - 用途：Core 执行控制的 canonical carrier，聚合 timeout、retry 与 concurrency 三类最小策略
- 实体：`ExecutionTimeoutPolicy`
  - 用途：表达单个 adapter execution attempt 的最大等待时间
- 实体：`RetryPolicy`
  - 用途：表达同一 task_id 下最多执行多少次 attempt，以及 attempt 之间的固定等待
- 实体：`ConcurrencyLimitPolicy`
  - 用途：表达 Core 在执行 attempt 前如何按 scope 获取并发 slot
- 实体：`ExecutionAttemptOutcome`
  - 用途：表达单次 adapter execution attempt 的结果，供 TaskRecord 终态、结构化日志与指标消费
- 实体：`ExecutionControlEvent`
  - 用途：表达不属于单次 attempt 的控制面事实，例如 admission 阶段并发拒绝与 retry 预算耗尽聚合

## 关键字段

- `ExecutionControlPolicy`
  - `timeout`
    - 约束：必须存在；必须满足 `ExecutionTimeoutPolicy`
  - `retry`
    - 约束：必须存在；必须满足 `RetryPolicy`
  - `concurrency`
    - 约束：必须存在；必须满足 `ConcurrencyLimitPolicy`
  - 默认 policy
    - 约束：当调用方整体缺省 policy 时，Core 必须物化 `timeout.timeout_ms=30000`、`retry.max_attempts=1`、`retry.backoff_ms=0`、`concurrency.scope=global`、`concurrency.max_in_flight=1`、`concurrency.on_limit=reject`
    - 约束：部分缺字段的 policy 非法；不得把单个缺失字段宽松替换为默认值
- `ExecutionTimeoutPolicy`
  - `timeout_ms`
    - 约束：正整数毫秒；表达单次 adapter execution attempt 的 deadline
    - 禁止：`null`、缺字段、零、负数、字符串或浮点数表示 timeout
- `RetryPolicy`
  - `max_attempts`
    - 约束：正整数；包含首次执行；`1` 表示不重试
  - `backoff_ms`
    - 约束：非负整数毫秒；表达相邻 attempts 之间的固定等待
- Core 固定 retryable outcome rule
  - 约束：该规则不是 `RetryPolicy` 字段，也不是 caller-visible policy 载荷；`v0.6.0` 固定为 `execution_timeout` 与 `error.category=platform`
  - 禁止：调用方在 policy 载荷中传入 `retryable_outcomes` 或等价 predicate；若显式出现，必须按未知策略字段 fail-closed
  - 禁止：调用方提供正则、脚本、错误码 DSL 或 adapter 私有 retry 规则
- `ConcurrencyLimitPolicy`
  - `scope`
    - 约束：只允许 `global`、`adapter`、`adapter_capability`
  - `max_in_flight`
    - 约束：正整数；表达同一 scope 内同时处于 adapter execution attempt 阶段的最大数量
  - `on_limit`
    - 约束：caller-visible required field；`v0.6.0` 固定且只允许 `reject`
    - 禁止：缺失、`queue`、`wait`、`drop_oldest`、`priority` 或 `fair_share`
- `ExecutionAttemptOutcome`
  - `task_id`
    - 约束：非空字符串；同一任务的所有 attempts 必须一致
  - `attempt_index`
    - 约束：从 `1` 开始的正整数；不得超过 `retry.max_attempts`
  - `adapter_key` / `capability`
    - 约束：必须与共享请求上下文一致
  - `started_at` / `ended_at`
    - 约束：RFC3339 UTC 时间；`ended_at` 不得早于 `started_at`
  - `outcome`
    - 约束：只允许 `succeeded`、`failed`、`timeout`
  - `terminal_envelope`
    - 约束：仅当该 attempt 形成可消费 success / failed envelope 时出现；必须复用既有 Core envelope
  - `control_code`
    - 约束：仅表达当前 attempt 自身的控制面结果；当前只允许 `execution_timeout`
    - 禁止：在 attempt outcome 上承载 admission 阶段的 `concurrency_limit_exceeded` 或 task-level 聚合的 `retry_exhausted`
- `ExecutionControlEvent`
  - `task_id`
    - 约束：非空字符串；pre-accepted admission rejection 可使用 fallback task id，但不得声称存在 durable TaskRecord
  - `event_type`
    - 约束：只允许 `admission_concurrency_rejected`、`retry_concurrency_rejected`、`retry_exhausted`
  - `adapter_key` / `capability`
    - 约束：必须与请求上下文一致；无法恢复时必须使用共享 failed envelope 已批准的空值 / fallback 语义
  - `attempt_count`
    - 约束：`admission_concurrency_rejected` 必须为 `0`；`retry_concurrency_rejected` 必须等于已经完成的 attempt 数且至少为 `1`；`retry_exhausted` 必须为正整数且不超过 `retry.max_attempts`
  - `control_code`
    - 约束：`admission_concurrency_rejected -> concurrency_limit_exceeded`；`retry_concurrency_rejected -> concurrency_limit_exceeded`；`retry_exhausted -> retry_exhausted`
  - `task_record_ref`
    - 约束：pre-accepted admission concurrency rejection 必须为 `none`；retry concurrency rejection 与 retry exhausted 必须引用同一 `task_id` 的 TaskRecord
  - `occurred_at`
    - 约束：RFC3339 UTC 时间

## 状态与生命周期

- 创建：
  - Core 在共享 admission 通过、进入 adapter execution attempt 前，根据 `ExecutionControlPolicy` 创建 attempt 控制上下文
  - 并发 slot 必须在 attempt 进入 adapter 前获取；首次获取失败时本次请求 fail-fast，不创建 durable accepted TaskRecord
  - 已 accepted 任务的 retry attempt 重新获取 slot 失败时，创建 `ExecutionControlEvent(event_type=retry_concurrency_rejected)`，并把同一 TaskRecord 收口为 failed
- 更新：
  - 每次 attempt 只能产生一个 outcome
  - timeout、adapter failure 或 success 都必须结束当前 attempt 并释放 concurrency slot
  - 若 outcome 属于 Core 固定 retryable outcome rule，且 `attempt_index < max_attempts`，Core 必须等待 `retry.backoff_ms` 后进入下一个 attempt；只有 success、不可重试失败、retry 预算耗尽或 retry slot reacquire 被拒绝可以终止同一 TaskRecord
- 失效/归档：
  - attempt outcome 不单独成为 durable task truth；它只能作为 TaskRecord 日志、failed envelope details、结构化日志或指标的输入
  - 若 late completion 在 timeout 后到达，它不得重新激活 attempt，也不得改写 TaskRecord 终态

## 错误口径投影

- `execution_timeout`
  - 触发条件：attempt deadline 已过，Core 未得到可信成功或失败结果
  - 错误分类：复用 `FR-0005` 的闭集，默认投影为 `runtime_contract`
- `concurrency_limit_exceeded`
  - 触发条件：目标 scope 已达到 `max_in_flight`，且 `on_limit=reject`
  - 载体：pre-accepted 拒绝必须作为 `ExecutionControlEvent(event_type=admission_concurrency_rejected)` 或 failed envelope details 出现且 `task_record_ref=none`；post-accepted retry reacquire 拒绝必须作为 `ExecutionControlEvent(event_type=retry_concurrency_rejected)` 出现并引用同一 TaskRecord
  - 错误分类：复用 `FR-0005` 的闭集，默认投影为 `runtime_contract`
- `retry_exhausted`
  - 触发条件：retry controller 已用尽 `max_attempts` 且未获得 success
  - 载体：必须作为 `ExecutionControlEvent(event_type=retry_exhausted)` 或 failed envelope details 中的 task-level 聚合事实出现，不得序列化为单次 attempt outcome
  - 错误分类：复用最终失败 attempt 的分类；若需要聚合 code，必须保留 `last_error`，不得丢失最终失败原因
