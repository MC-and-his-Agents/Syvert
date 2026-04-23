# FR-0019 v0.6 operability release gate

## 关联信息

- item_key：`FR-0019-v0-6-operability-release-gate`
- Issue：`#222`
- item_type：`FR`
- release：`v0.6.0`
- sprint：`2026-S19`

## 背景与目标

- 背景：`FR-0007` 已冻结版本级 gate 的基础语义，要求每个版本在声明完成前具备可追溯、fail-closed 的 gate 结论。`v0.6.0` 的目标进一步从“能验证版本完成”推进到“可运维地判断 HTTP / CLI / Core 主路径是否仍然一致且可回归”。当前仓库已经有任务持久化、CLI 查询、资源能力与双参考适配器证据基线，但还缺少一份专门面向 `v0.6.0` 的 operability release gate 与回归矩阵 formal spec。
- 目标：冻结 `v0.6.0` 可运维发布门禁与回归矩阵，覆盖 timeout / retry / concurrency、failure / log / metrics、HTTP submit / status / result、CLI / API same-path；在不重写 `FR-0007` 既有版本 gate 的前提下，为后续 `#234` release gate matrix implementation 提供 implementation-ready 的需求、契约、数据与验证边界。

## 范围

- 本次纳入：
  - 定义 `v0.6.0` operability release gate 在 `FR-0007` 基础 gate 之上的新增必选检查对象与失败语义。
  - 定义 timeout / retry / concurrency 回归矩阵的最小覆盖范围、可观测结论与 fail-closed 条件。
  - 定义 failure / log / metrics 回归矩阵的最小事件、字段、聚合与可追溯性要求。
  - 定义 HTTP submit / status / result 入口与既有 Core / task-record / result contract 的一致性要求。
  - 定义 CLI / API same-path 证明要求，确保 CLI 与 HTTP API 不形成两套任务语义、持久化真相或结果 envelope。
  - 定义后续实现可消费的 gate result、matrix case、evidence ref 与 same-path proof 的共享语义。
- 本次不纳入：
  - 不重写 `FR-0007` 已批准的 contract harness、双参考适配器回归与平台泄漏 gate。
  - 不执行 release closeout、打 tag、创建 GitHub Release 或声明 `v0.6.0` 已发布。
  - 不引入外部 SaaS 监控、生产环境验收、线上 SLO/SLA、告警平台或第三方可观测性服务。
  - 不引入分布式压测、跨机器队列、真实生产流量回放或容量规划基准。
  - 不修改 `syvert/**`、`tests/**`、`scripts/**` 的实现或测试代码；本 Work Item 只冻结 formal spec。

## 规范性依赖（Normative Dependencies）

- `FR-0007`（baseline gate）：
  - `FR-0019` 只做 `v0.6.0` operability 叠加层；`baseline_gate_ref` 缺失或不可追溯时，`verdict` 必须为 `fail`。
- `FR-0016`（timeout / retry / concurrency control semantics）：
  - 默认 policy 固定为：
    - `policy.timeout_ms=30000`
    - `policy.retry.max_attempts=1`
    - `policy.retry.backoff_ms=0`
    - `policy.concurrency.scope=global`
    - `policy.concurrency.max_in_flight=1`
    - `policy.concurrency.on_limit=reject`
  - retryable predicate 固定为：仅 `execution_timeout`，或 `error.category=platform` 且 `error.details.retryable=true` 的 transient failure，并且必须先通过 idempotency safety gate。
  - 当前批准 capability 固定为 `content_detail_by_url`；矩阵不得引入未批准 capability。
  - `execution_timeout` 的 failed envelope 归类为 `error.category=platform`，并固定写入 `error.details.control_code=execution_timeout` 表示控制面来源。
  - `closeout/control-state` failure 才归类为 `runtime_contract`；不得把正常 `execution_timeout` 映射到 `runtime_contract`。
  - pre-accepted concurrency rejection 必须投影为 `invalid_input`，且不得创建 `TaskRecord`。
  - post-accepted retry reacquire rejection 只能写入 `ExecutionControlEvent.details`，不得改写上一已完成 attempt 的终态 `error.code` / `error.category`。
- `FR-0017`（failure / structured log / metrics / refs）：
  - `failure_log_metrics` 维度必须使用结构化日志字段、结构化指标计数与 evidence refs 的统一 contract，不允许只给抽象描述或文本同义词。
- `FR-0018`（HTTP + CLI through same Core path）：
  - `http_submit_status_result` 与 `cli_api_same_path` 维度必须证明 HTTP 与 CLI 都走同一 Core / TaskRecord / envelope 语义，不允许入口私有 truth。

## 需求说明

- 功能需求：
  - `v0.6.0` 发布门禁必须先满足 `FR-0007` 的版本级 gate 语义，再叠加本 FR 定义的 operability gate；本 FR 不得把旧 gate 合并、弱化或替换成新的单一矩阵。
  - operability gate 必须形成可复验的回归矩阵，至少包含四个维度：`timeout_retry_concurrency`、`failure_log_metrics`、`http_submit_status_result`、`cli_api_same_path`。
  - timeout / retry / concurrency 矩阵必须覆盖：单任务超时、可重试失败、不可重试失败、重试上限、并发提交、并发状态查询、并发结果读取，以及同一 `task_id` 终态不可被并发路径重复改写。
  - timeout / retry / concurrency 维度的每个 case 必须显式断言以下 policy 字段和值：`timeout_ms=30000`、`retry.max_attempts=1`、`retry.backoff_ms=0`、`concurrency.scope=global`、`concurrency.max_in_flight=1`、`concurrency.on_limit=reject`。
  - retry 语义必须保持 fail-closed：只有 `execution_timeout`，或 `error.category=platform && error.details.retryable=true` 且通过 idempotency safety gate 的 transient failure 才能进入 retry；参数错误、contract violation、非法持久化记录、平台泄漏、不可归类错误不得被宽松重试掩盖。
  - `execution_timeout` case 的期望字段必须固定为 `error.category=platform` 与 `error.details.control_code=execution_timeout`；不得把该类错误投影成 `runtime_contract`。
  - pre-accepted 并发拒绝 case 的期望字段必须固定为 `error.category=invalid_input`，且期望副作用必须固定为“无 TaskRecord 创建”。
  - post-accepted retry reacquire rejection case 的期望字段必须固定为“新增 `ExecutionControlEvent.details`”，并且固定断言“不改写上一已完成 attempt 的终态 `error.code` / `error.category`”。
  - concurrency 语义必须证明共享任务记录、状态迁移、终态 envelope 与日志追加在并发入口下仍保持单一 durable truth；不得出现双终态、状态回退、重复 task record、影子结果或竞态覆盖。
  - `timeout_retry_concurrency` 的最小 mandatory case set 至少固定为：`trc-timeout-platform-control-code`、`trc-retryable-platform-retry-once`、`trc-non-retryable-fail-closed`、`trc-retry-budget-exhausted`、`trc-pre-accept-concurrency-reject`、`trc-concurrent-status-shared-truth`、`trc-concurrent-result-shared-truth`、`trc-post-accept-reacquire-reject`。
  - failure / log / metrics 矩阵必须覆盖成功、业务失败、contract failure、timeout、retry exhausted、store unavailable、HTTP 参数错误、CLI 参数错误与 same-path violation 的可观测输出。
  - `failure_log_metrics` 的最小 mandatory case set 至少固定为：`flm-success-observable`、`flm-business-failure-observable`、`flm-contract-failure-fail-closed`、`flm-timeout-observable`、`flm-retry-exhausted-observable`、`flm-store-unavailable-fail-closed`、`flm-http-invalid-input-observable`、`flm-cli-invalid-input-observable`、`flm-same-path-violation-observable`。
  - failure 输出必须继续复用已批准的 shared failed envelope 和错误分类语义；不得为 HTTP 或 CLI 单独定义不可映射的失败格式。
  - log 证据必须至少可追溯到 durable `task_id`（当请求已进入 `accepted` 后）；对 pre-admission 且无 `TaskRecord` 的 case，必须改为可追溯到稳定 `request_ref`（或等价 `admission_ref`）、入口类型、生命周期阶段、结果状态与失败分类；不得要求记录 raw payload、账号材料、平台 token 或平台私有调试细节。
  - metrics 证据必须至少能表达可本地复验的计数或聚合结论：提交数、成功数、失败数、超时数、retry attempt 数、并发 case 计数 / case verdict、same-path case 计数 / case verdict；该最小集合必须在 gate result 的 machine-readable `metrics_snapshot`（或等价结构）中落盘。它可以是本地测试输出、结构化文件或进程内聚合，不要求外部监控系统。
  - HTTP submit / status / result 矩阵必须证明 HTTP 入口提交任务后产生的任务记录、状态查询与结果读取均消费同一条 Core / task-record / store truth。
  - HTTP `submit` 不得绕过共享 admission、共享请求投影、Core 执行主路径或持久化建档；HTTP `status` 不得维护独立状态缓存；HTTP `result` 不得读取第二套结果文件或拼装 HTTP 私有 envelope。
  - `http_submit_status_result` 的最小 mandatory case set 至少固定为：`http-submit-status-result-shared-truth`；该 case 必须同时证明 submit durable 建档、status 回读共享 `TaskRecord`、result 回读同一 shared envelope。
  - CLI / API same-path 矩阵必须证明 CLI `run/query` 与 HTTP `submit/status/result` 在等价请求下最终回指同一类 `TaskRecord`、同一类 shared success / failed envelope、同一套状态迁移与同一套 failure classification。
  - same-path 证明必须覆盖成功态与失败态，至少包含一个成功 case、一个 pre-admission 参数失败 case、一个 durable record 不可用 case 与一个终态结果读取 case。
  - `cli_api_same_path` 的最小 mandatory case set 至少固定为：`same-path-success-shared-truth`、`same-path-pre-admission-invalid-input`、`same-path-durable-record-unavailable`、`same-path-terminal-result-read`。
  - 每个 matrix case 必须有稳定 case id、验证对象、入口组合、前置条件、预期结果、失败时的 gate 影响与证据引用；`expected_result` 必须写明字段路径与精确值（例如 `error.category=platform`），不得仅写“与上游一致”或同义词描述。缺失任何必需字段都必须使该 case fail-closed。
  - operability gate 的总体结论必须可追溯到 `release=v0.6.0`、`FR-0019`、执行 head 或等价 revision、回归矩阵版本、必选 case 集合与每个 case 的证据。
- 契约需求：
  - 本 FR 冻结的是 release gate 与回归矩阵 contract，不绑定唯一脚本、唯一 CI workflow、唯一 HTTP 框架、唯一 metrics 后端或唯一日志实现。
  - gate result 至少必须表达：`release`、`fr_item_key`、`gate_id`、`baseline_gate_ref`、`matrix_version`、`cases`、`summary`、`evidence_refs`、`verdict`。
  - `baseline_gate_ref` 必须指向 `FR-0007` gate 结论或其后续受控实现证据；若无法证明旧 gate 已被消费，本 FR 的 operability gate 不得单独放行。
  - `verdict` 只允许 `pass` 或 `fail`；任何缺失必选 case、case 证据不可追溯、case 结论不可信、或旧 gate 未完成的状态都必须落为 `fail`。
  - HTTP contract 只冻结 `submit/status/result` 三类能力语义，不在本 FR 固定具体 URL path、方法名、端口、鉴权方案或序列化框架；后续实现必须在 contracts 文档中保持这些入口映射到共享语义。
  - CLI / API same-path contract 以共享请求模型、`TaskRecord`、状态迁移和 shared envelope 为判据；输出展示差异可以存在，但不得改变共享语义、错误分类或 durable truth。
- 非功能需求：
  - gate 结果必须本地可复验，并适合被 CI 或 release closeout 消费；但本 FR 不要求生产环境验收或外部监控。
  - 回归矩阵必须优先验证语义一致性与 fail-closed 行为，而不是吞吐量、长时间 soak、分布式压测或业务成功率。
  - 失败信息必须足以定位失败维度、case id、入口组合与共享 contract 边界，避免把 HTTP、CLI、Core、store 与 adapter 责任混淆。

## 约束

- 阶段约束：
  - 本事项只服务 `v0.6.0` 的 formal spec closeout，不提前执行 release closeout、版本标签或 GitHub Release。
  - `#233` 只冻结 formal spec；`#234` 负责在 spec review 通过后实现 release gate matrix；`#235` 负责 parent closeout 收口。
  - 本 FR 只承接并叠加 `FR-0007`，不重写 `FR-0007` 的版本 gate 职责边界。
- 架构约束：
  - Core 继续负责共享执行、任务状态、持久化、结果 envelope 与同路径语义；HTTP 与 CLI 只是入口，不得拥有各自的 durable truth。
  - Adapter 继续负责目标系统语义；operability gate 不得把平台专属 URL、错误码、日志字段或 metrics label 引入 Core 共享契约。
  - formal spec 与实现 PR 必须分离；本 PR 不修改 runtime、tests、scripts、release / sprint 索引或 GitHub 状态镜像。

## GWT 验收场景

### 场景 1

Given `FR-0007` 已定义版本级基础 gate，且 `v0.6.0` 准备进入 operability gate 判断  
When 后续实现运行 `FR-0019` 的 release gate matrix  
Then 它必须先消费并记录 `FR-0007` baseline gate 结论，再叠加 timeout / retry / concurrency、failure / log / metrics、HTTP submit / status / result、CLI / API same-path 四类矩阵结论

### 场景 2

Given 一个任务在共享执行路径中触发 timeout，且该 timeout 被矩阵标记为可观测 case  
When gate 评估该 case  
Then 失败 envelope、生命周期日志与 metrics 计数必须能共同证明该 timeout 的任务、入口、阶段与最终失败分类，并且不得把 timeout 静默转成成功或未知状态

### 场景 3

Given 某个失败被共享错误分类标记为不可重试  
When retry 逻辑或 gate case 试图继续重试并最终成功  
Then formal spec 必须判定该 case 失败，因为 retry 掩盖了不可重试 failure 并破坏 fail-closed 语义

### 场景 4

Given 多个入口并发提交、查询或读取同一任务相关状态  
When gate 检查并发 case 的 durable truth  
Then 同一 `task_id` 只能存在一条任务记录、一个终态、单向状态迁移与可追溯日志，不允许出现双终态、状态回退或影子结果

### 场景 5

Given HTTP `submit` 接收了与 CLI `run` 等价的请求  
When HTTP `status/result` 与 CLI `query` 分别读取任务状态和结果  
Then 两类入口必须回指同一共享任务语义、同一终态 envelope 与同一失败分类，而不是各自维护 HTTP 私有状态或 CLI 私有结果

### 场景 6

Given metrics 证据只存在于外部 SaaS dashboard，且本地 gate 结果无法复验计数来源  
When release gate 尝试引用该证据  
Then formal spec 必须判定该证据不足，不能把外部 dashboard 作为 `v0.6.0` operability gate 的唯一真相源

### 场景 7

Given 某次 gate result 缺少必选 case、缺少 `baseline_gate_ref`、无法追溯到 `v0.6.0`，或无法说明 evidence ref 来源  
When parent closeout 试图消费该 gate result  
Then formal spec 必须把该 gate result 视为 `fail`，并阻止它作为 `v0.6.0` 发布完成证据

## 异常与边界场景

- 异常场景：
  - 若实现只运行 `FR-0007` 的旧 gate 而没有 `FR-0019` operability matrix，则不能宣称 `v0.6.0` operability release gate 已完成。
  - 若 HTTP `status` 使用内存缓存返回状态，而 durable `TaskRecord` 已损坏或不存在，则该路径违反 same-path 和 durable truth 要求。
  - 若 CLI 与 HTTP 在同一非法输入上返回不同错误分类，且无法映射到同一 shared failed envelope，则 same-path case 必须失败。
  - 若 metrics 只证明业务成功率或吞吐量，而不证明必选 case 的计数、失败分类与 retry / timeout / concurrency 结论，则 metrics 证据不足。
  - 若并发 case 需要分布式压测或多机器部署才能运行，则该 case 超出本 FR 范围，应被拆分为未来事项而不是阻塞 `v0.6.0` 本地 gate。
- 边界场景：
  - 本 FR 允许后续实现选择本地脚本、pytest、CI workflow 或 release closeout 命令承载 gate，但不把任何一种实现形式写成唯一合法路径。
  - 本 FR 允许 HTTP 与 CLI 在展示格式、HTTP status code、stderr/stdout 细节上存在入口差异，只要共享 task record、状态、结果 envelope 与失败分类一致。
  - 本 FR 不要求真实生产账号、生产环境、外部监控或线上流量参与验收。
  - 本 FR 不新增平台能力、资源能力或 adapter 私有契约。

## 验收标准

- [ ] formal spec 明确 `FR-0019` 是 `FR-0007` 的 `v0.6.0` operability gate 叠加层，不重写旧版本 gate。
- [ ] formal spec 明确冻结 timeout / retry / concurrency、failure / log / metrics、HTTP submit / status / result、CLI / API same-path 四类必选矩阵维度。
- [ ] formal spec 明确每个 matrix case 的必需字段、fail-closed 条件与 evidence ref 要求。
- [ ] formal spec 明确 HTTP 与 CLI 都必须消费同一 Core / task-record / store / envelope 语义，禁止影子状态与影子结果。
- [ ] formal spec 明确 metrics / logs 的本地可复验边界，并排除外部 SaaS 监控、生产验收和分布式压测。
- [ ] formal spec 明确后续实现入口为 `#234`，parent closeout 收口为 `#235`，本 Work Item 不做 release closeout / tag / GitHub Release。

## 依赖与外部前提

- 外部依赖：
  - `#222` 是本 FR 的 canonical requirement 容器。
  - `#233` 是当前 formal spec closeout Work Item。
  - `FR-0007` 已冻结版本级基础 gate，`FR-0019` 必须消费并叠加其结论。
  - `FR-0016` 提供 timeout / retry / concurrency 控制面与 retry predicate 的规范真相；`FR-0019` 必须按其字段级语义定义矩阵预期。
  - `FR-0017` 提供 failure / structured log / metrics / refs 的规范真相；`FR-0019` 必须引用其结构化字段而非抽象同义词。
  - `FR-0018` 提供 HTTP 与 CLI 同 Core path 的规范真相；`FR-0019` 必须以其 same-path 语义定义入口一致性矩阵。
  - 既有 `FR-0008` / `FR-0009` 为 durable `TaskRecord`、CLI query 与 same-path 基线提供上游语义。
- 上下游影响：
  - `#234` 在 spec review 通过后实现 release gate matrix，不得改写本 FR requirement。
  - `#235` 在实现和审查完成后执行 parent closeout，负责把 GitHub 状态、文档证据与主干真相收成一致。
