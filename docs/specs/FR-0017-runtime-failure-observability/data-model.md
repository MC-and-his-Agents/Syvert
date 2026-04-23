# FR-0017 数据模型

## 实体清单

- 实体：`RuntimeFailureSignal`
  - 用途：从同一次执行的 failed envelope 投影出 canonical 失败可观测信号，供 review、查询、日志与指标关联使用
- 实体：`RuntimeStructuredLogEvent`
  - 用途：表达 task-bound 的最小结构化日志事件，覆盖生命周期、失败、timeout、retry、concurrency 与 observability 自身故障
- 实体：`RuntimeExecutionMetricSample`
  - 用途：表达最小执行指标样本，用于按 task、adapter、capability、错误分类与运行时阶段进行计数或时长聚合

## 关键字段

- `RuntimeFailureSignal`
  - `signal_id`
    - 约束：非空字符串；同一 `signal_id` 重复写入时 payload 必须完全一致
  - `task_id`
    - 约束：非空字符串；必须与 failed envelope、TaskRecord 或 admission failure 上下文一致；pre-accepted admission rejection 可使用共享 fallback task id，但不得暗示存在 durable TaskRecord
  - `adapter_key`
    - 约束：非空字符串；必须与执行 envelope 保持一致
  - `capability`
    - 约束：非空字符串；必须与执行 envelope 保持一致
  - `status`
    - 约束：固定为 `failed`
  - `error_category`
    - 约束：必须等于 failed envelope 的 `error.category`；只允许 `invalid_input`、`unsupported`、`runtime_contract`、`platform`
  - `error_code`
    - 约束：必须等于 failed envelope 的 `error.code`
    - 约束：若 failed envelope 来自正常 timeout outcome，则必须保持 `execution_timeout`，并保留 `error.details.control_code=execution_timeout`
  - `failure_phase`
    - 约束：只允许 `admission`、`pre_execution`、`resource_acquire`、`adapter_execution`、`timeout`、`retry_exhausted`、`concurrency_rejected`、`persistence`、`observability`
  - `envelope_ref`
    - 约束：必须能定位同一次执行的 failed envelope；pre-accepted admission rejection 同样必须引用 shared failed envelope，不得用空引用暗示“只有 rejection event、没有 envelope”
  - `task_record_ref`
    - 约束：进入 `FR-0008` `accepted` 生命周期后必须引用同一 TaskRecord；admission 前失败允许为 `none`
  - `resource_trace_refs`
    - 约束：资源 acquire 成功后发生的失败必须引用相关 `FR-0011` trace；资源 acquire 前失败使用空集合
  - `runtime_result_refs`
    - 约束：只允许引用 `FR-0016` carrier：attempt 级结果使用 `ExecutionAttemptOutcome`，task-level control fact 使用 `ExecutionControlEvent`；无相关结果时使用空集合
  - `occurred_at`
    - 约束：RFC3339 UTC 时间戳
- `RuntimeStructuredLogEvent`
  - `event_id`
    - 约束：非空字符串；相同 id 的重复写入只能是 identical replay
  - `task_id`
    - 约束：非空字符串；不得出现脱离 task 的失败日志
  - `event_type`
    - 约束：只允许 `task_accepted`、`task_running`、`attempt_started`、`attempt_finished`、`retry_scheduled`、`timeout_triggered`、`admission_concurrency_rejected`、`retry_concurrency_rejected`、`task_failed`、`task_succeeded`、`observability_write_failed`
  - `level`
    - 约束：只允许 `info`、`warning`、`error`；不承载错误分类语义
  - `attempt_index`
    - 约束：非负整数；没有多次尝试时使用 `0`；`admission_concurrency_rejected` 必须为 `0`，`retry_concurrency_rejected` 表达上一已完成 attempt 的索引，不表示创建了新的 attempt outcome
  - `failure_signal_id`
    - 约束：失败相关日志必须引用对应 `RuntimeFailureSignal.signal_id`；非失败生命周期日志可为空
  - `resource_trace_refs`
    - 约束：与事件相关的 resource trace 引用集合；无相关资源事件时为空集合
  - `runtime_result_refs`
    - 约束：与事件相关的 `ExecutionAttemptOutcome` / `ExecutionControlEvent` 引用集合；`retry_scheduled` 只允许引用命中 `FR-0016` 固定 retryable predicate 的上一次结果，且该结果必须通过 idempotency safety gate；`retry_concurrency_rejected` 必须引用 `ExecutionControlEvent(event_type=retry_concurrency_rejected, control_code=concurrency_limit_exceeded)`
  - `message`
    - 约束：人类可读摘要；不得作为唯一机器判定来源
  - `occurred_at`
    - 约束：RFC3339 UTC 时间戳
- `RuntimeExecutionMetricSample`
  - `metric_id`
    - 约束：非空字符串；相同 id 重复写入必须 payload 完全一致
  - `task_id`
    - 约束：非空字符串；指标样本必须可回到 task
  - `metric_name`
    - 约束：只允许 `task_started_total`、`task_succeeded_total`、`task_failed_total`、`attempt_started_total`、`retry_scheduled_total`、`timeout_total`、`admission_concurrency_rejected_total`、`retry_concurrency_rejected_total`、`execution_duration_ms`
  - `metric_value`
    - 约束：计数型指标为非负整数；duration 型指标为非负数
  - `unit`
    - 约束：计数型指标使用 `count`；duration 型指标使用 `ms`
  - `adapter_key` / `capability`
    - 约束：必须与执行上下文一致
  - `error_category` / `error_code` / `failure_phase`
    - 约束：失败相关指标必须与 `RuntimeFailureSignal` 一致；成功或生命周期计数可为空
  - `attempt_index`
    - 约束：非负整数；非 attempt 指标可使用 `0`；`admission_concurrency_rejected_total` 必须为 `0`，`retry_concurrency_rejected_total` 表达上一已完成 attempt 的索引，不表示创建了新的 attempt outcome
  - `occurred_at`
    - 约束：RFC3339 UTC 时间戳

## 关联规则

- `task_id` 是所有 observability carrier 的最小关联轴。
- `RuntimeFailureSignal.envelope_ref` 与 `task_record_ref` 必须能证明 failed envelope 与 TaskRecord 属于同一 `task_id`。
- `resource_trace_refs` 只引用 `FR-0011` 已存在的 tracing truth，不生成资源状态或 trace 事件。
- `runtime_result_refs` 只引用 `FR-0016` 的 `ExecutionAttemptOutcome` / `ExecutionControlEvent`，不重新定义调度策略。
- `error_category` 与 `error_code` 只能从 failed envelope 投影，不由日志或指标层重新计算。
- pre-accepted admission rejection 的 `error_code=concurrency_limit_exceeded` 与 `error_category=invalid_input` 必须继续来自 failed envelope，同时 `task_record_ref=none`。
- post-accepted retry reacquire rejection 的 signal / metric 可以把 `failure_phase` 记为 `concurrency_rejected`，但 `error_code / error_category` 必须继续保持最终 failed envelope 中上一已完成 attempt 的原因；`concurrency_limit_exceeded` 只能通过 `ExecutionControlEvent`、日志或 details 暴露。

## 生命周期

- 创建：
  - 任务进入共享运行时主路径后，Core 可以创建生命周期日志与执行指标。
  - 当最终失败 envelope 形成时，Core 必须创建对应 `RuntimeFailureSignal`。
- 更新：
  - carrier 均为 append-only 语义；不得原地覆写旧 signal / event / metric。
  - 相同 id 的 identical replay 可作为 idempotent no-op。
- 失效/归档：
  - 本 FR 不定义 retention、归档策略或指标后端；如需长期存储、索引或 dashboard，必须由后续事项扩张。
