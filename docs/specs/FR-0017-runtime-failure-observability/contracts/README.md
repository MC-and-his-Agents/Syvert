# runtime-failure-observability contract（v0.6.0）

## 接口名称与版本

- 接口名称：`runtime-failure-observability`
- contract 版本：`v0.6.0`
- 作用：定义 Core 在运行时失败发生后必须留下的最小结构化信号、日志与指标，以及它们与 task、TaskRecord、failed envelope、resource trace、`FR-0016` 的 `ExecutionAttemptOutcome` / `ExecutionControlEvent` 的关联语义

## 输入来源

- failed envelope：来自共享 Core 执行主路径，继续使用 `FR-0005` 错误模型和既有 failed envelope 结构
- TaskRecord：来自 `FR-0008` 的同一 `task_id` 聚合根
- ResourceTraceEvent：来自 `FR-0011` 的 task-bound resource tracing truth
- Runtime control result：来自 `FR-0016` 的 `ExecutionAttemptOutcome` / `ExecutionControlEvent`

## 输出结构

- `RuntimeFailureSignal`
  - 必填字段：`signal_id`、`task_id`、`adapter_key`、`capability`、`status`、`error_category`、`error_code`、`failure_phase`、`envelope_ref`、`task_record_ref`、`resource_trace_refs`、`runtime_result_refs`、`occurred_at`
  - 约束：`status` 固定为 `failed`；`error_category` 与 `error_code` 必须从 failed envelope 投影；pre-accepted admission rejection 也必须引用 failed envelope；`resource_trace_refs` / `runtime_result_refs` 必须存在，无相关上游事实时使用空集合
- `RuntimeStructuredLogEvent`
  - 必填字段：`event_id`、`task_id`、`event_type`、`level`、`occurred_at`、`message`、`adapter_key`、`capability`、`attempt_index`、`failure_signal_id`、`resource_trace_refs`、`runtime_result_refs`
  - 约束：失败相关日志必须引用对应 failure signal；生命周期日志不得把 `level` 当作错误分类；`retry_scheduled` 只允许用于命中 `FR-0016` 固定 retryable predicate 且通过 idempotency safety gate 的结果，当前批准 capability 仅 `content_detail_by_url`
- `RuntimeExecutionMetricSample`
  - 必填字段：`metric_id`、`task_id`、`metric_name`、`metric_value`、`unit`、`adapter_key`、`capability`、`error_category`、`error_code`、`failure_phase`、`attempt_index`、`occurred_at`
  - 约束：失败相关指标必须可关联 `error_category`、`error_code` 与 `failure_phase`；成功或生命周期指标必须保留这些字段并以空字符串表达不适用，不得省略字段

## 分类与阶段

- 错误分类：只允许复用 `FR-0005` 的 `invalid_input`、`unsupported`、`runtime_contract`、`platform`
- 失败阶段：只允许 `admission`、`pre_execution`、`resource_acquire`、`adapter_execution`、`timeout`、`retry_exhausted`、`concurrency_rejected`、`persistence`、`observability`
- 约束：`failure_phase` 不替代 `error_category`；timeout / retry / concurrency 不是新的顶层错误分类；正常 `execution_timeout` 继续投影为 `platform`，并通过 `error.details.control_code=execution_timeout` 暴露控制面来源，只有 closeout / control-state failure 才是 `runtime_contract`

## 最小日志事件

- `task_accepted`
- `task_running`
- `attempt_started`
- `attempt_finished`
- `retry_scheduled`
- `timeout_triggered`
- `admission_concurrency_rejected`
- `retry_concurrency_rejected`
- `task_failed`
- `task_succeeded`
- `observability_write_failed`

## 最小指标

- `task_started_total`：单位 `count`
- `task_succeeded_total`：单位 `count`
- `task_failed_total`：单位 `count`
- `attempt_started_total`：单位 `count`
- `retry_scheduled_total`：单位 `count`
- `timeout_total`：单位 `count`
- `admission_concurrency_rejected_total`：单位 `count`
- `retry_concurrency_rejected_total`：单位 `count`
- `execution_duration_ms`：单位 `ms`

## 关联边界

- TaskRecord：进入 `accepted` 生命周期后的失败必须引用同一 `TaskRecord`；admission 前失败允许 `task_record_ref=none`
- Envelope：最终失败对外可见时，failure signal 必须引用同一 failed envelope
- Resource trace：资源 acquire 成功后的失败必须引用相关 `FR-0011` trace；acquire 前失败使用空集合
- Runtime control result：timeout / retry / concurrency 事实通过 `runtime_result_refs` 关联 `FR-0016` 的 `ExecutionAttemptOutcome` / `ExecutionControlEvent`，不在本 contract 中重新定义策略
- Concurrency rejection：pre-accepted rejection 保持 `concurrency_limit_exceeded + invalid_input + task_record_ref=none`；post-accepted retry reacquire rejection 只通过 `ExecutionControlEvent` / 日志 / details 暴露，不改写上一已完成 attempt 的终态 `error_code / error_category`

## 禁止行为

- 新增 observability 私有 `error.category`
- 把 adapter 私有平台 taxonomy 写入 Core 错误分类
- 用日志 `level` 或 metric name 替代 failed envelope 的错误分类
- 改写 success envelope 的 `raw` / `normalized`
- 绑定具体日志采集后端、指标数据库、dashboard 或云厂商协议
- 原地覆盖已有 signal / event / metric payload
