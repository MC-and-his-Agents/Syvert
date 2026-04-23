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
  - 用途：表达单次 attempt 的控制结果，供 TaskRecord 终态、结构化日志与指标消费

## 关键字段

- `ExecutionControlPolicy`
  - `timeout`
    - 约束：必须存在；必须满足 `ExecutionTimeoutPolicy`
  - `retry`
    - 约束：必须存在；必须满足 `RetryPolicy`
  - `concurrency`
    - 约束：必须存在；必须满足 `ConcurrencyLimitPolicy`
- `ExecutionTimeoutPolicy`
  - `timeout_ms`
    - 约束：正整数毫秒；表达单次 adapter execution attempt 的 deadline
    - 禁止：`null`、缺字段、零、负数、字符串或浮点数表示 timeout
- `RetryPolicy`
  - `max_attempts`
    - 约束：正整数；包含首次执行；`1` 表示不重试
  - `retryable_outcomes`
    - 约束：`v0.6.0` 固定由 Core 定义，只包含 `execution_timeout` 与 `platform_failure`
    - 禁止：调用方提供自定义 predicate、正则、脚本、错误码 DSL 或 adapter 私有 retry 规则
  - `backoff_ms`
    - 约束：非负整数毫秒；表达相邻 attempts 之间的固定等待
- `ConcurrencyLimitPolicy`
  - `scope`
    - 约束：只允许 `global`、`adapter`、`adapter_capability`
  - `max_in_flight`
    - 约束：正整数；表达同一 scope 内同时处于 adapter execution attempt 阶段的最大数量
  - `on_limit`
    - 约束：`v0.6.0` 固定为 `reject`；不得出现 `queue`、`wait`、`drop_oldest`、`priority` 或 `fair_share`
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
    - 约束：控制面失败时使用；当前允许 `execution_timeout`、`concurrency_limit_exceeded`、`retry_exhausted`

## 状态与生命周期

- 创建：
  - Core 在共享 admission 通过、进入 adapter execution attempt 前，根据 `ExecutionControlPolicy` 创建 attempt 控制上下文
  - 并发 slot 必须在 attempt 进入 adapter 前获取；获取失败时本次请求 fail-fast，不创建 durable accepted TaskRecord
- 更新：
  - 每次 attempt 只能产生一个 outcome
  - timeout、adapter failure 或 success 都必须结束当前 attempt 并释放 concurrency slot
  - 若 outcome 可重试且 `attempt_index < max_attempts`，Core 可以进入下一个 attempt；否则必须收口为同一 TaskRecord 的终态
- 失效/归档：
  - attempt outcome 不单独成为 durable task truth；它只能作为 TaskRecord 日志、failed envelope details、结构化日志或指标的输入
  - 若 late completion 在 timeout 后到达，它不得重新激活 attempt，也不得改写 TaskRecord 终态

## 错误口径投影

- `execution_timeout`
  - 触发条件：attempt deadline 已过，Core 未得到可信成功或失败结果
  - 错误分类：复用 `FR-0005` 的闭集，默认投影为 `runtime_contract`
- `concurrency_limit_exceeded`
  - 触发条件：目标 scope 已达到 `max_in_flight`，且 `on_limit=reject`
  - 错误分类：复用 `FR-0005` 的闭集，默认投影为 `runtime_contract`
- `retry_exhausted`
  - 触发条件：retry controller 已用尽 `max_attempts` 且未获得 success
  - 错误分类：复用最终失败 attempt 的分类；若需要聚合 code，必须保留 `last_error`，不得丢失最终失败原因
