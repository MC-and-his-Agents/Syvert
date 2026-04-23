# FR-0016 Minimal execution controls

## 关联信息

- item_key：`FR-0016-minimal-execution-controls`
- Issue：`#219`
- item_type：`FR`
- release：`v0.6.0`
- sprint：`2026-S19`

## 背景与目标

- 背景：`v0.3.0` 已冻结 `TaskRecord`、本地持久化与 CLI 查询闭环，`v0.4.0` / `v0.5.0` 已冻结资源生命周期、资源追踪、资源需求声明与能力匹配。但当前 Core 执行仍是单次同步调用，缺少统一的超时、基础重试与并发限制语义。若这些控制继续散落在 adapter 私有实现或调用方脚本中，后续 HTTP 服务面会绕过 Core 运行时真相，任务记录也无法稳定解释“为什么任务失败或被拒绝”。
- 目标：为 `v0.6.0` 冻结最小 `ExecutionControlPolicy` contract，使 Core 统一拥有 attempt 级超时、固定边界内的重试与 fail-fast 并发限制语义，并把这些控制结果投影到同一条 TaskRecord / failed envelope / 后续可观测信号路径。

## 范围

- 本次纳入：
  - 冻结 canonical control carrier `ExecutionControlPolicy`
  - 冻结 attempt 级 `timeout_ms` 语义
  - 冻结基础 `RetryPolicy`：`max_attempts`、固定可重试范围、固定 `backoff_ms`
  - 冻结基础 `ConcurrencyLimitPolicy`：scope、`max_in_flight`、fail-fast 拒绝
  - 冻结控制面与 `TaskRecord`、failed envelope、资源释放与后续 `FR-0017` 可观测信号之间的边界
  - 冻结 CLI 与后续 HTTP API 必须通过 Core 消费同一份执行控制策略的约束
- 本次不纳入：
  - 生产级调度器、分布式队列、后台 worker 池或任务恢复系统
  - 优先级、公平性、排队等待、取消、暂停、恢复或复杂策略 DSL
  - adapter 私有 timeout / retry 实现细节、平台 SDK 超时参数或浏览器桥接细节
  - `FR-0017` 的结构化日志字段、指标聚合与观测输出实现
  - `FR-0018` 的 HTTP endpoint 实现
  - `FR-0019` 的 release gate runtime
  - `FR-0013` / `FR-0014` / `FR-0015` 的资源能力词汇、provider 选择边界或 fallback 禁止边界

## 需求说明

- 功能需求：
  - Core 执行控制的 canonical carrier 固定为 `ExecutionControlPolicy`；CLI、HTTP API 或其他调用方不得在 Core 外部用私有 wrapper 表达另一套 timeout / retry / concurrency 语义。
  - `ExecutionControlPolicy` 至少包含：`timeout`、`retry`、`concurrency` 三个子策略；实现可以在代码中拆分模块，但对执行路径暴露的语义必须等价于这三个子策略。
  - `timeout.timeout_ms` 表达单个 adapter execution attempt 的最大等待时间，必须为正整数毫秒；`null`、缺字段、零或负数不得表示“无限等待”。
  - `v0.6.0` 只冻结 attempt 级 timeout，不冻结全任务 total deadline；一个任务的最坏执行时长由 `max_attempts`、每次 attempt 的 `timeout_ms` 与固定 backoff 共同界定。
  - Core 必须在每次 attempt 进入 adapter 执行前建立 deadline，并在 deadline 过期时把该 attempt 归类为 timeout outcome；超时 attempt 不得再被报告为成功 attempt。
  - 若底层 adapter 或宿主无法被安全抢占，Core 仍必须隔离 late completion：deadline 后到达的 adapter 结果不得改写已产生的 failed TaskRecord 终态、不得追加第二个终态，也不得泄漏资源释放职责。
  - `retry.max_attempts` 表达包含首次执行在内的最大 attempt 数，必须为正整数；`max_attempts=1` 表示不重试。
  - `v0.6.0` 的可重试范围固定为：Core 产生的 `execution_timeout`，以及 adapter 平台执行返回的 `error.category=platform` 失败；不得把 `invalid_input`、`unsupported` 或一般 `runtime_contract` 失败默认纳入重试。
  - `retry.backoff_ms` 表达 attempt 之间的固定等待时间，必须为非负整数毫秒；`v0.6.0` 不定义指数退避、抖动、重试预算、按错误码 DSL 或调用方自定义 predicate。
  - 同一任务的所有 attempts 必须共享同一个 `task_id` 与同一条 TaskRecord 聚合根；不得为每次 retry 创建新的 durable task truth。
  - 只要任务已进入 durable `accepted` 生命周期，所有 attempt outcome 都必须最终收口到同一条 `succeeded` 或 `failed` 终态；成功 attempt 后不得继续执行后续 attempts。
  - 当全部 attempts 耗尽仍未成功时，任务必须进入 `failed` 终态；终态 failed envelope 必须保留最终失败原因，并在 `error.details` 或后续 `FR-0017` 观测信号中表达 attempts 总数与最后一次 attempt outcome。
  - `concurrency.max_in_flight` 表达同一并发 scope 内允许同时处于 adapter execution attempt 阶段的最大数量，必须为正整数。
  - `concurrency.scope` 在 `v0.6.0` 只允许 `global`、`adapter`、`adapter_capability` 三类；scope 只用于 Core 内部 slot 计数，不表达租户、用户、优先级或资源 provider 选择。
  - `v0.6.0` 的并发限制固定为 fail-fast gate：当目标 scope 没有可用 slot 时，本次提交必须被拒绝，而不是排队等待、降级执行或绕过 gate。
  - 并发 slot 只能覆盖实际 adapter execution attempt 的运行窗口；attempt 结束、timeout、异常或任务终态收口后，Core 必须释放 slot。
  - 当并发 gate 在 durable `accepted` 建档前拒绝请求时，不得伪造已接受 TaskRecord；该失败必须返回 shared failed envelope，并由 `FR-0017` 后续定义的结构化信号记录为 admission/control rejection。
  - 当任务已经持有 slot 并进入 TaskRecord 生命周期后，任何 timeout、retry exhausted、adapter 失败或资源释放异常都必须沿同一条 Core / TaskRecord 终态路径收口。
- 契约需求：
  - `ExecutionControlPolicy` 的非法形状必须在进入 adapter execution attempt 前 fail-closed，并复用 `FR-0005` 的 `runtime_contract` 分类；不得被宽松修复为默认无限等待、无限重试或无限并发。
  - `execution_timeout` 是 Core 控制面失败 code，必须使用 `FR-0005` 已批准的失败 envelope 顶层结构；`error.category` 继续限定在既有闭集内，不得新增 `timeout`、`retry` 或 `concurrency` category。
  - `concurrency_limit_exceeded` 是 Core control admission rejection code；当它发生在 durable `accepted` 前，调用方只能得到 failed envelope，不得查询到对应 TaskRecord。
  - `retry_exhausted` 只能用于表达 retry 控制器已按 policy 用尽 attempts 的 task-level 聚合事实；它不得被建模为单次 attempt outcome。终态 envelope 不得丢失最后一次 attempt 的原始失败 code / category。后续实现可通过 `error.details.last_error`、`ExecutionControlEvent` 或 `FR-0017` 冻结的 signal 暴露该信息。
  - timeout / retry / concurrency 的实现不得改写 success envelope 的 `raw` 与 `normalized` contract；成功结果继续由既有 Core success envelope 持有。
  - 执行控制不得绕过 `FR-0010` / `FR-0011` / `FR-0012` 的资源生命周期、资源追踪与 Core 注入边界；任一 timeout 或 retry path 都必须按既有资源释放 contract 结束当前 attempt。
  - CLI 与后续 HTTP API 必须把执行控制交给同一 Core 入口消费；任何只在 CLI wrapper、HTTP handler 或 adapter 私有层实现的 timeout / retry / concurrency 都不满足本 FR。
- 非功能需求：
  - 执行控制必须 fail-closed：未知策略字段、非法数值、slot 计数不可信、attempt 终态不一致或 late completion 试图改写终态时，不得静默放行。
  - 执行控制必须保持最小、确定、可测试；相同请求、相同策略、相同 adapter outcome 序列必须得到可判定的 attempts 与终态结果。
  - 本 FR 只冻结 Core 最小可运维控制面，不提前承诺生产调度吞吐、公平性、可取消性或跨进程一致性。

## 约束

- 阶段约束：
  - 本事项只服务 `v0.6.0` 的最小可运维运行时能力，不提前进入 `v0.7.0` 之后的服务治理、控制台或生产调度能力。
  - 本事项只冻结 formal spec；`#223` 不混入 `syvert/**`、`tests/**`、HTTP API、gate runtime 或 release closeout 改动。
- 架构约束：
  - Core 负责执行控制语义；Adapter 只负责平台执行，不得拥有决定 retry / concurrency 的共享运行时真相。
  - TaskRecord 仍是 durable 任务真相；执行控制不能创建 attempt 级影子任务记录或第二套结果 envelope。
  - `FR-0017` 负责冻结结构化日志与指标字段；本 FR 只声明哪些控制结果必须可被观测，不在这里定义完整观测 schema。

## GWT 验收场景

### 场景 1

Given `ExecutionControlPolicy.timeout.timeout_ms=1000` 且 adapter attempt 未在 deadline 前返回  
When Core 执行该 attempt  
Then 该 attempt 必须被标记为 `execution_timeout`，不得在 deadline 后把 late success 写成任务成功终态

### 场景 2

Given `retry.max_attempts=3` 且前两次 attempt 返回 `error.category=platform`，第三次 attempt 返回 success envelope  
When Core 执行该任务  
Then 同一 `task_id` 下只能产生一条 TaskRecord，并最终进入 `succeeded`，且不得继续执行第四次 attempt

### 场景 3

Given `retry.max_attempts=2` 且两次 attempt 都因 `execution_timeout` 失败  
When Core 用尽 attempts  
Then 任务必须进入 `failed` 终态，并保留最终失败原因与 attempts 总数，而不是无限重试或只返回最后一次裸 timeout

### 场景 4

Given 第一次 attempt 返回 `error.category=invalid_input` 或 `unsupported`  
When Core 评估 retry policy  
Then Core 不得重试该任务，必须直接按该失败 envelope 收口

### 场景 5

Given `concurrency.scope=adapter_capability`、`max_in_flight=1`，且同一 adapter/capability 已有一个 attempt 持有 slot  
When 第二个同 scope 请求进入 Core  
Then 第二个请求必须 fail-fast 返回 `concurrency_limit_exceeded` failed envelope，而不是排队、绕过 slot 或创建伪造 accepted TaskRecord

### 场景 6

Given 某个 attempt 在持有资源和 concurrency slot 后触发 timeout  
When Core 收口该 attempt  
Then Core 必须释放 slot，并按既有资源生命周期 contract 处理资源释放或失效，不得让后续 retry 继承不可信资源状态

### 场景 7

Given CLI 与后续 HTTP API 提交同等请求并使用同一 `ExecutionControlPolicy`  
When 二者进入 Core 执行  
Then timeout / retry / concurrency 判断必须发生在同一 Core 控制路径，而不是分别由 CLI 或 HTTP handler 私有实现

## 异常与边界场景

- 异常场景：
  - `timeout_ms<=0`、缺失 timeout、`max_attempts<=0`、`backoff_ms<0`、`max_in_flight<=0` 或未知 concurrency scope 都必须视为 policy contract violation。
  - retry controller 若试图重试 `invalid_input`、`unsupported` 或一般 `runtime_contract` 失败，必须视为越过最小重试边界。
  - timeout 后 late adapter result 试图写入 success 终态、追加第二个终态或覆盖 failed envelope，必须 fail-closed。
  - slot release 失败、slot 计数为负、同一 attempt 重复释放不同 slot 等情况必须被视为 control state violation。
- 边界场景：
  - `max_attempts=1` 是合法最小策略，表示执行一次且不重试。
  - `backoff_ms=0` 是合法最小策略，表示相邻 retry attempt 之间不额外等待。
  - 并发 gate 拒绝发生在 durable `accepted` 前时，不要求创建 TaskRecord；若未来引入队列或 accepted-before-run 语义，必须通过新的 formal spec 扩张状态机。
  - 本 FR 不要求跨进程或分布式 slot 一致性；`v0.6.0` 的并发限制只保证当前 Core runtime 边界内的最小控制语义。
  - Adapter 内部仍可使用平台 SDK 自带 timeout 参数，但这不能替代 Core control path，也不能成为 shared TaskRecord 真相源。

## 验收标准

- [ ] formal spec 明确冻结 `ExecutionControlPolicy`、attempt timeout、基础 retry 与 fail-fast concurrency gate
- [ ] formal spec 明确 `timeout_ms`、`max_attempts`、`backoff_ms`、`max_in_flight` 与 `scope` 的最小字段和值域
- [ ] formal spec 明确 retry 只覆盖 `execution_timeout` 与 `platform` 失败，不默认重试 `invalid_input`、`unsupported` 或一般 `runtime_contract`
- [ ] formal spec 明确所有 attempts 共享同一 `task_id` 与同一条 TaskRecord，不创建 attempt 级影子任务记录
- [ ] formal spec 明确 timeout / retry / concurrency 失败继续复用 `FR-0005` failed envelope，不新增 error category
- [ ] formal spec 明确并发限制在 `v0.6.0` 是 fail-fast，不提供队列、优先级、公平性或分布式 slot
- [ ] formal spec 明确 late completion、资源释放、slot release 与终态幂等的 fail-closed 边界
- [ ] formal spec 明确 CLI 与 HTTP API 必须消费同一 Core execution control path

## 数据模型与迁移说明

- 本 formal spec PR 只新增 requirement、data-model 与 contract 文档，不执行 runtime、store 或历史数据迁移。
- `ExecutionControlPolicy`、`ExecutionAttemptOutcome` 与 `ExecutionControlEvent` 是 `#224` implementation 的输入 contract；它们不要求当前 PR 修改 `TaskRecord` 主状态集合、store 文件布局或既有 success / failed envelope 顶层结构。
- `#224` 若把 attempt / control event 写入 TaskRecord 日志或 failed envelope `error.details`，必须保持 JSON-safe、append-only 与既有 TaskRecord 终态幂等语义；不得要求迁移历史 TaskRecord 才能读取旧任务。
- `FR-0017` 可以消费本 FR 的 attempt outcome 与 control event 作为 observability 输入，但不得反向要求本 FR 引入日志后端、指标存储或新的错误 category。
- 若后续实现发现必须新增持久化字段、store schema 或历史记录迁移，必须在对应 implementation Work Item 中显式补充迁移风险、回滚方式与测试证据；不能把该迁移隐含在当前 formal spec PR 中。

## 依赖与外部前提

- 外部依赖：
  - `#218` 已建立 `v0.6.0` 最小可运维与 HTTP 服务面 Phase
  - `#219` 已作为本 FR 的 canonical requirement 容器建立
  - `FR-0005` 已冻结统一 failed envelope 与错误分类闭集
  - `FR-0008` / `FR-0009` 已冻结 TaskRecord、CLI 查询与 Core 同路径闭环
  - `FR-0010` / `FR-0011` / `FR-0012` 已冻结资源生命周期、资源追踪与 Core 注入边界
  - `FR-0013` / `FR-0014` / `FR-0015` 已冻结资源需求声明、能力匹配与双参考资源能力证据基线
- 上下游影响：
  - `#224` 必须据此实现 Core timeout / retry / concurrency runtime
  - `FR-0017` 必须消费本 FR 的 control outcome，冻结结构化日志与指标的可观测字段
  - `FR-0018` 的 HTTP API 不得绕过本 FR 的 Core execution control path
  - `FR-0019` 的 v0.6 gate matrix 必须覆盖本 FR 的 timeout、retry 与 concurrency 场景
