# FR-0017 Runtime failure observability

## 关联信息

- item_key：`FR-0017-runtime-failure-observability`
- Issue：`#220`
- item_type：`FR`
- release：`v0.6.0`
- sprint：`2026-S19`

## 背景与目标

- 背景：`FR-0005` 已冻结统一错误模型，`FR-0008` 已冻结 `TaskRecord` 持久化，`FR-0011` 已冻结 task-bound 资源追踪，`FR-0016` 已冻结最小执行控制 carrier 与 timeout / retry / concurrency 口径。当前缺少一层 formal contract 来回答“失败发生后，Core 至少应留下哪些可关联、可审查、可计数的运行时信号”。如果这层语义散落在 adapter 私有日志、一次性 stderr 或实现注释里，失败排查会重新退回平台私有事实，无法围绕同一 `task_id`、执行 envelope、TaskRecord 与资源追踪建立最小真相链。
- 目标：为 `v0.6.0` 冻结运行时失败可观测性的最小 contract，在不重写 `FR-0005` 错误分类和 `FR-0016` 执行控制本体的前提下，明确失败分类投影、结构化日志、最小执行指标，以及这些信号如何关联 `task_id`、TaskRecord、执行 envelope、资源追踪和 `FR-0016` 的 `ExecutionAttemptOutcome` / `ExecutionControlEvent`。

## 范围

- 本次纳入：
  - 冻结 runtime failure observability 的最小信号集合：`RuntimeFailureSignal`、`RuntimeStructuredLogEvent`、`RuntimeExecutionMetricSample`
  - 冻结失败分类投影如何复用 `FR-0005` 的 `error.category` 与 `error.code`，不得新增第二套错误分类
  - 冻结结构化日志的最小字段、事件类型与 task-bound 关联规则
  - 冻结最小执行指标的字段、计数口径与关联维度
  - 冻结信号如何关联 `task_id`、TaskRecord、执行 envelope、资源追踪事件、以及 `FR-0016` 的 `ExecutionAttemptOutcome` / `ExecutionControlEvent`
  - 冻结 observability 写入失败时的 fail-closed / degraded 边界
- 本次不纳入：
  - 完整 observability 平台、日志采集后端、指标存储系统或 dashboard
  - OpenTelemetry、Prometheus、ELK、云厂商日志服务等具体技术选型
  - adapter 私有平台语义分类、平台私有错误 taxonomy 或诊断 UI
  - `raw` / `normalized` 成功结果重写
  - 资源生命周期、TaskRecord 状态机、timeout / retry / concurrency 本体 contract 的重新定义
  - `syvert/**`、`tests/**`、`scripts/**` 的实现改造

## 需求说明

- 功能需求：
  - Core 必须在每个进入共享运行时主路径的任务上产出可按 `task_id` 关联的最小失败可观测信号；这些信号不得只存在于非结构化 stdout / stderr。
  - `RuntimeFailureSignal` 是失败可观测性的 canonical failure projection；它必须从同一次执行产生的 failed envelope 中投影，而不是由日志层重新分类。
  - `RuntimeStructuredLogEvent` 是 task-bound 结构化日志的最小事件 carrier；它必须能表达任务生命周期、运行时失败、retry 尝试、timeout 触发、以及 accepted 前后不同类型的 concurrency 拒绝或收口等关键运行时节点。
  - `RuntimeExecutionMetricSample` 是最小执行指标 carrier；它只冻结可本地计数与聚合的执行事实，不要求持久化指标后端或实时采集系统。
  - 所有失败相关信号必须至少能回溯到同一 `task_id`，并在存在相关事实时回溯到 TaskRecord、failed envelope、resource trace、runtime attempt 与 `FR-0016` 的 `ExecutionAttemptOutcome` / `ExecutionControlEvent`。
  - Core 必须保证最终失败对外可见时，至少存在一条可关联的 `RuntimeFailureSignal` 与一条结构化失败日志；否则该执行不得被宣称为 observability-complete。
  - 对于成功执行，本 FR 不要求改写 success envelope，也不要求新增 `raw` / `normalized` 字段；成功路径只允许产生最小执行指标与生命周期日志，不得改变成功结果 contract。
- 契约需求：
  - `RuntimeFailureSignal` 至少必须包含：
    - `signal_id`
    - `task_id`
    - `adapter_key`
    - `capability`
    - `status=failed`
    - `error_category`
    - `error_code`
    - `failure_phase`
    - `envelope_ref`
    - `task_record_ref`
    - `occurred_at`
  - `error_category` 必须复用 `FR-0005` 已冻结分类集合：`invalid_input`、`unsupported`、`runtime_contract`、`platform`。本 FR 不新增 `timeout`、`retry_exhausted`、`concurrency_rejected` 等顶层错误分类；这些事实只能进入 `error_code`、`failure_phase`、运行时结果引用或 `details` 投影。
  - `error_code` 必须来自 failed envelope 的 `error.code`；结构化日志或指标不得自行把同一失败重新命名为另一 code。
  - 当 failed envelope 来自 `FR-0016` 的正常 timeout outcome 时，`error_code` 必须保持 `execution_timeout`，`error_category` 必须保持 `platform`，并保留 `error.details.control_code=execution_timeout`；只有 timeout closeout / control-state failure 已经被上游投影为 `runtime_contract` 时，observability 才能继续投影该 `runtime_contract` 失败。
  - `failure_phase` 在 `v0.6.0` 的最小集合固定为：
    - `admission`
    - `pre_execution`
    - `resource_acquire`
    - `adapter_execution`
    - `timeout`
    - `retry_exhausted`
    - `concurrency_rejected`
    - `persistence`
    - `observability`
  - `failure_phase` 表达失败发生或被收口的运行时阶段，不替代 `error.category`。
  - `envelope_ref` 必须能定位同一次执行产生的 failed envelope；若 failed envelope 已作为 TaskRecord 终态结果持久化，该引用必须能与 `task_record_ref` 共同证明二者属于同一 `task_id`。pre-accepted admission rejection 同样必须引用 shared failed envelope，不得暗示只有 rejection event 而没有 failed envelope。
  - `task_record_ref` 必须能定位 `FR-0008` 的同一 `TaskRecord`；若任务尚未进入 `accepted` 生命周期就在 admission 前失败，则必须显式记录 `task_record_ref=none`，并说明该失败不属于 durable TaskRecord 历史。
  - `RuntimeStructuredLogEvent` 至少必须包含：
    - `event_id`
    - `task_id`
    - `event_type`
    - `level`
    - `occurred_at`
    - `message`
    - `adapter_key`
    - `capability`
    - `attempt_index`
    - `failure_signal_id`
    - `resource_trace_refs`
    - `runtime_result_refs`
  - `event_type` 在 `v0.6.0` 的最小集合固定为：`task_accepted`、`task_running`、`attempt_started`、`attempt_finished`、`retry_scheduled`、`timeout_triggered`、`admission_concurrency_rejected`、`retry_concurrency_rejected`、`task_failed`、`task_succeeded`、`observability_write_failed`。
  - `retry_scheduled` 只允许在前一失败命中 `FR-0016` 固定 retryable predicate 时出现：该失败必须是 closeout 完成后的 `execution_timeout`，或 `error.category=platform` 且 `error.details.retryable=true` 的 transient failure，并通过 idempotency safety gate；当前批准 capability 仅限 `content_detail_by_url`。
  - `level` 只表达日志严重度，最小允许 `info`、`warning`、`error`；不得把 `level` 当作错误分类或失败阶段。
  - `RuntimeExecutionMetricSample` 至少必须包含：
    - `metric_id`
    - `task_id`
    - `metric_name`
    - `metric_value`
    - `unit`
    - `adapter_key`
    - `capability`
    - `error_category`
    - `error_code`
    - `failure_phase`
    - `attempt_index`
    - `occurred_at`
  - `metric_name` 在 `v0.6.0` 的最小集合固定为：`task_started_total`、`task_succeeded_total`、`task_failed_total`、`attempt_started_total`、`retry_scheduled_total`、`timeout_total`、`admission_concurrency_rejected_total`、`retry_concurrency_rejected_total`、`execution_duration_ms`。
  - 计数型指标的 `metric_value` 必须为非负整数；duration 型指标的 `metric_value` 必须为非负数且 `unit=ms`。
  - timeout / retry / concurrency 事实必须通过 `runtime_result_refs` 关联 `FR-0016` carrier：attempt 级结果只允许引用 `ExecutionAttemptOutcome`，task-level control fact 只允许引用 `ExecutionControlEvent`；不得在本 FR 中重新定义其调度、锁、队列或重试策略。
  - pre-accepted concurrency rejection 的 observability 投影必须保留 `concurrency_limit_exceeded` failed envelope 与 `invalid_input` 分类，同时显式记录 `task_record_ref=none`；post-accepted retry reacquire rejection 只能通过 `ExecutionControlEvent(event_type=retry_concurrency_rejected, control_code=concurrency_limit_exceeded)`、结构化日志、指标或 envelope details 记录，不得改写上一已完成 attempt 的终态 `error_code / error_category`。
  - 若存在 `FR-0011` 的资源追踪事件，结构化日志和失败信号必须通过 `resource_trace_refs` 或等价引用关联相关 `lease_id / bundle_id / resource_id`；若失败发生在资源 acquire 前，则必须显式为空集合。
  - observability signal 必须 append-only；相同 `signal_id`、`event_id` 或 `metric_id` 的重复写入只有在 payload 完全一致时才允许作为 idempotent no-op，冲突性重复写入必须 fail-closed。
- 非功能需求：
  - 本 contract 必须保持实现无关，不绑定任何日志库、指标库、文件格式或后端服务。
  - 信号必须 JSON-safe，字段语义必须可被后续 contract tests、CLI 查询或人工 review 判定。
  - 可观测性不得成为吞错机制：任何 observability 降级都必须留下结构化事实，不能让业务失败被替换成“日志写入失败”而丢失原始 failed envelope。

## 约束

- 阶段约束：
  - 本事项只服务 `v0.6.0` 的最小运行时失败可观测性，不提前建设完整观测平台。
  - 本事项是 formal spec Work Item `#226`，只冻结文档规约；后续 runtime implementation 必须由 `#227` 独立进入实现 PR，再由 `#228` parent closeout 收口。
- 架构约束：
  - Core 负责共享运行时失败信号、结构化日志与最小指标语义；Adapter 只负责提供平台语义和平台错误细节，不负责写入共享 observability truth。
  - `FR-0005` 继续是错误分类权威来源；本 FR 只能投影其分类，不得新增或重命名 `error.category`。
  - `FR-0008` 继续是 TaskRecord 权威来源；本 FR 不重写任务状态、终态 envelope 或持久化幂等语义。
  - `FR-0011` 继续是资源追踪权威来源；本 FR 只引用 resource trace，不新增资源状态机。
  - `FR-0016` 继续持有 timeout / retry / concurrency 运行时结果；本 FR 只规定 `ExecutionAttemptOutcome` / `ExecutionControlEvent` 如何出现在 failure observability 信号中。

## GWT 验收场景

### 场景 1

Given 某个 task 已进入共享运行时主路径并最终返回 `status=failed` 的 envelope  
When Core 收口该失败的 observability 信号  
Then 必须产出 `RuntimeFailureSignal`，其 `task_id / adapter_key / capability / error_category / error_code` 与 failed envelope 保持一致，并可关联到同一 TaskRecord

### 场景 2

Given failed envelope 的 `error.category=platform` 且 adapter 提供平台细节  
When observability 层记录失败  
Then `RuntimeFailureSignal.error_category` 仍必须是 `platform`，不得改写为 adapter 私有平台分类或新的 observability 分类

### 场景 3

Given 某次执行因 `FR-0016` timeout 结果失败  
When Core 记录失败信号、结构化日志与指标  
Then `failure_phase` 可以是 `timeout`，并产生 `timeout_triggered` 日志与 `timeout_total` 指标；若该 timeout 是 closeout 安全完成后的正常 timeout，则 `error_code` 必须保持 `execution_timeout`、`error_category` 必须保持 `platform`，并保留 `error.details.control_code=execution_timeout`；只有上游已经把 closeout / control-state failure 投影为 `runtime_contract` 时，observability 才能继续投影 `runtime_contract`

### 场景 4

Given 某次执行属于 `content_detail_by_url` capability，且前一失败要么是 closeout 完成后的 `execution_timeout`，要么是 `error.category=platform` 且 `error.details.retryable=true` 的 transient failure，并通过 idempotency safety gate  
When Core 评估是否调度下一次 attempt 或最终收口任务  
Then 每次 retry 才允许产出可关联的 `retry_scheduled` 结构化日志与 `retry_scheduled_total` 指标；若失败不命中该固定 predicate，则不得记录 `retry_scheduled`；若全部预算耗尽仍未成功，则最终失败仍必须用同一 `task_id` 关联 failed envelope、TaskRecord 与 `retry_exhausted` 阶段

### 场景 5

Given 某次任务在进入 durable `accepted` 前因 concurrency 限制被共享运行时拒绝进入执行  
When Core 产出 observability 信号  
Then 必须记录 `admission_concurrency_rejected` 事件与 `admission_concurrency_rejected_total` 指标，failed envelope 的 `error.code` 必须保持 `concurrency_limit_exceeded`、`error_category` 必须保持 `invalid_input`，且 `task_record_ref` 必须显式为 `none`

### 场景 6

Given 某个任务已进入 durable `accepted` 生命周期，且 retry attempt 在重新获取 concurrency slot 时被拒绝  
When Core 产出 observability 信号  
Then 必须记录 `retry_concurrency_rejected` 事件与 `retry_concurrency_rejected_total` 指标，并通过 `runtime_result_refs` 引用同一 task 的 `ExecutionControlEvent(event_type=retry_concurrency_rejected, control_code=concurrency_limit_exceeded)`；该失败 signal 的 `error_code / error_category` 仍必须来自最终 failed envelope，不得改写上一已完成 attempt 的终态原因

### 场景 7

Given 某个 task 已 acquire 资源并产生 `FR-0011` resource trace 事件  
When 后续 adapter execution 失败  
Then 失败日志或失败信号必须能通过引用关联相关 `lease_id / bundle_id / resource_id`，而不是只留下不可关联的文字日志

### 场景 8

Given observability 写入结构化日志或指标时发生自身错误  
When 原始业务失败已经产生 failed envelope  
Then Core 不得丢弃原始 failed envelope；必须以 `observability_write_failed` 事件或等价失败信号暴露 observability 链路故障，并保持原始失败可追溯

## 异常与边界场景

- 异常场景：
  - 若 `RuntimeFailureSignal.error_category` 与 failed envelope 的 `error.category` 不一致，则该 signal 非法。
  - 若某条失败日志缺少 `task_id`，或无法证明与 failed envelope / TaskRecord 的关系，则不得被视为合法 task-bound observability truth。
  - 若同一 `signal_id`、`event_id` 或 `metric_id` 被写入不同 payload，必须 fail-closed，不得通过覆盖旧值修复历史。
  - 若 observability 写入失败导致原始业务失败 envelope 丢失，属于阻断级 contract violation。
- 边界场景：
  - admission 前失败可以没有 TaskRecord，但必须显式表达 `task_record_ref=none`，且若该失败已对外可见则仍必须引用 failed envelope；进入 `accepted` 之后的失败必须关联同一 TaskRecord。
  - 资源 acquire 前失败可以没有 resource trace refs；资源 acquire 成功后发生的失败必须能关联已有 resource trace truth。
  - retry 的中间失败可以产生 attempt 日志和指标，但只有命中 `FR-0016` 固定 retryable predicate 且通过 idempotency safety gate 时才允许出现 `retry_scheduled`；对外终态失败仍只能有一个最终 failed envelope。
  - accepted 前后的 concurrency rejection 不得混用同一日志/指标事件名；前者是 `admission_concurrency_rejected`，后者是 `retry_concurrency_rejected`。
  - success path 不因本 FR 改写 `raw` / `normalized`，也不要求产生 failure signal。
  - 本 FR 不规定日志/指标存储路径、采集协议、dashboard 查询语法或 retention policy。

## 验收标准

- [ ] formal spec 明确冻结 `RuntimeFailureSignal`、`RuntimeStructuredLogEvent`、`RuntimeExecutionMetricSample` 三类最小 observability carrier
- [ ] formal spec 明确要求失败分类复用 `FR-0005` 的 `error.category`，不得新增 observability 私有错误分类
- [ ] formal spec 明确结构化日志和指标如何关联 `task_id`、TaskRecord 与 failed envelope
- [ ] formal spec 明确 timeout / retry / concurrency 事实只作为 `failure_phase`、日志事件、指标或 `ExecutionAttemptOutcome` / `ExecutionControlEvent` 引用出现，不重写 `FR-0016`
- [ ] formal spec 明确正常 `execution_timeout` 继续投影为 `platform`，并通过 `error.details.control_code=execution_timeout` 暴露控制面来源；只有 closeout / control-state failure 才是 `runtime_contract`
- [ ] formal spec 明确日志与指标区分 `admission_concurrency_rejected` 与 `retry_concurrency_rejected`，且 post-accepted retry reacquire rejection 不改写上一已完成 attempt 的终态 `error_code / error_category`
- [ ] formal spec 明确与 `FR-0011` resource trace 的关联边界
- [ ] formal spec 明确 observability 信号 append-only、idempotent replay 与冲突写入 fail-closed 语义
- [ ] formal spec 明确不纳入完整 observability 平台、采集后端、指标存储、dashboard、adapter 私有平台分类或 success payload 重写
- [ ] 当前 formal spec PR 未混入 `syvert/**`、`tests/**`、`scripts/**` 实现改造

## 依赖与外部前提

- 外部依赖：
  - `#220` 作为 `FR-0017` canonical requirement 容器已建立
  - `#226` 是本 formal spec Work Item，也是当前执行入口
  - `FR-0005` 已冻结统一错误分类与 failed envelope 语义
  - `FR-0008` 已冻结 TaskRecord、终态结果与执行日志持久化边界
  - `FR-0011` 已冻结 task-bound resource tracing truth
  - `FR-0016` 提供 timeout / retry / concurrency 运行时结果的上游语义，本 FR 只消费 `ExecutionAttemptOutcome` / `ExecutionControlEvent` 引用
- 上下游影响：
  - `#227` 必须在本 spec 通过 `spec review` 后，作为独立 runtime implementation Work Item 落地 failure signal、structured log 与 minimal metrics
  - `#228` 必须在 `#227` 完成并通过实现门禁后，执行 parent closeout，确保 GitHub 状态、repo semantic truth 与 PR 状态一致
  - 后续 observability 平台、采集后端或 dashboard 如需建设，必须以新的 FR / Work Item 扩张，不得反向改写本最小 contract
