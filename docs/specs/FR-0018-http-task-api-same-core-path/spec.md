# FR-0018 HTTP task API same core path

## 关联信息

- item_key：`FR-0018-http-task-api-same-core-path`
- Issue：`#221`
- item_type：`FR`
- release：`v0.6.0`
- sprint：`2026-S19`

## 背景与目标

- 背景：`FR-0008` 已冻结 `TaskRecord` durable truth，`FR-0009` 已冻结 CLI `run/query` 与同路径执行闭环。进入 `v0.6.0` 后，仓库需要暴露第一个外部服务面，但如果 HTTP API 直接调用 adapter、直接写任务记录，或围绕服务面再造一套 request/result envelope，就会把“先闭环再暴露服务面”的路线图要求破坏掉。与此同时，`FR-0016` 已冻结共享执行控制、瞬态失败与 closeout/control-state 边界，`FR-0017` 已冻结这些控制结果进入结构化日志、指标与 `runtime_result_refs` 的语义；`FR-0018` 只能在这些既有共享语义之上暴露 HTTP 服务面，不得重新解释控制结果。
- 目标：为 `v0.6.0` 冻结最小 HTTP 任务 API contract，只允许通过 `submit`、`status`、`result` 三个端点把外部请求接入既有 Core 主路径，并明确 API 与 CLI 必须共享同一 `TaskRecord` durable truth、状态查询语义、结果回读语义，以及共享执行控制与观测真相。

## 范围

- 本次纳入：
  - 冻结最小 HTTP service surface：`submit`、`status`、`result`
  - 冻结 HTTP 请求如何投影到既有共享任务请求模型，并沿同一条 Core 执行路径工作
  - 冻结 `status/result` 如何回读 `FR-0008` 已批准的 durable `TaskRecord`
  - 冻结 HTTP 成功/失败返回如何复用既有共享 envelope 与 `TaskRecord` 语义，而不是新建 shadow carrier
  - 冻结 API 与 CLI 的 same-core-path 约束、职责边界与禁止项
  - 冻结 `ExecutionControlPolicy` 在 HTTP 侧的可见性、默认值、错误边界，以及控制结果如何继续沿共享错误/观测链路对外可见
- 本次不纳入：
  - 认证、多租户、RBAC、API key 管理或审计体系
  - 分布式队列、后台 worker 编排、取消/暂停/恢复、复杂重试控制策略设计本身
  - 列表查询、复杂筛选、分页、搜索 DSL 或完整控制台
  - 直接改写 `FR-0008` 的 `TaskRecord` contract、`FR-0009` 的 CLI public surface，或任何 adapter 平台语义
  - Web UI、OpenAPI 生成链、SDK、部署拓扑与生产级运维细节

## 需求说明

- 功能需求：
  - HTTP service 必须提供三个最小 public endpoint：`submit`、`status`、`result`。
  - `submit` 的职责固定为：接收外部请求、完成 HTTP ingress 级形状校验、把请求投影到既有共享任务请求模型、沿同一条 Core 执行路径提交任务，并返回可用于后续查询的 `task_id` 与最小状态信息。
  - `submit` 不得直接调用 adapter，不得跳过 Core admission / pre-execution / execution-control / task-record 流程，也不得自行写入 durable `TaskRecord`。
  - `submit` 对外暴露的最小请求语义必须与 `FR-0009` 的 `run` 入口保持等价：围绕 `adapter_key`、调用侧 capability、target 载荷提交任务，并在进入共享请求模型时继续复用既有投影规则。
  - 对当前验证切片，HTTP public capability 值域固定为调用侧 operation id `content_detail_by_url`；进入共享请求模型后，仍按既有兼容投影落到 adapter-facing capability family `content_detail`，并与 URL target 语义共同构成共享请求。
  - `submit` 可以显式暴露可选 `ExecutionControlPolicy` 请求字段，但它只能作为共享请求模型的 pass-through 语义使用；HTTP transport 不得发明 transport 私有 retry 开关、私有默认策略或私有控制状态机。
  - 当 HTTP 请求未显式提供 `ExecutionControlPolicy` 时，必须继续使用共享 Core 默认策略；该默认值由共享执行路径决定，而不是由 HTTP service 单独决定。
  - `ExecutionControlPolicy` 的 HTTP 边界固定为：HTTP 只校验 transport 形状并投影到共享字段；一旦无法证明该策略可安全投影到共享 contract，`submit` 必须在 durable `accepted` 之前 fail-closed，而不是带着降级/猜测策略继续执行。
  - `submit` 在共享任务已进入 durable `accepted` 生命周期后，必须返回与该 `task_id` 绑定的可追溯响应；若在 durable `accepted` 之前失败，则失败输出必须继续复用 shared failed envelope，而不是伪造 task history。
  - pre-accepted concurrency rejection 必须被投影为 shared failed envelope，且固定 `error.category=invalid_input`；该分支不得创建 durable `TaskRecord`，也不得让 HTTP receipt 伪装成“任务已提交”。
  - `status` 的职责固定为：按 `task_id` 读取同一份 durable `TaskRecord`，并返回该记录当前共享状态视图；它不得拼装影子状态表，也不得只依赖进程内内存状态。
  - `result` 的职责固定为：按 `task_id` 回读 durable `TaskRecord` 的结果语义。对终态任务，它必须返回与同一条 Core 主路径一致的终态 envelope；对非终态任务，它必须明确表达“结果尚不可用”，而不是伪造终态 payload。
  - `status` 与 `result` 都必须允许读取由 CLI 或 HTTP `submit` 创建的任务，只要这些任务共享同一 durable store truth；调用入口来源不得改变查询结果语义。
  - HTTP `status` / `result` 必须继续承接 `FR-0016` / `FR-0017` 的共享控制真相：不得吞掉 `error.category`、`error.code`、`error.details.control_code`、`error.details.retryable`、`ExecutionControlEvent` 相关细节或 `runtime_result_refs`。
  - 共享 retryable predicate 不得被 HTTP surface 改写成“整个 `platform` category 都可重试”。当前唯一允许继续进入共享 retry 判定的 transient failure 只有两类：
    - 控制面 `execution_timeout` 结果，正常投影为 shared failed envelope 的 `error.category=platform`，并通过 `error.details.control_code=execution_timeout` 表达控制面来源
    - `error.category=platform` 且 `error.details.retryable=true` 的平台瞬态失败
  - 上述两类 transient failure 只有在共享 `ExecutionControlPolicy` 的 idempotency safety gate 明确允许时，才可以被后续 retry loop 继续消费；HTTP service 不得单独放宽该 gate。
  - closeout failure、control-state failure、结果引用写入失败或其他无法证明共享控制/持久化真相的故障，必须投影为 `runtime_contract`；HTTP service 不得把这些故障伪装成普通 `platform` 失败。
  - post-accepted retry reacquire rejection 不得改写上一已完成 attempt 的终态 `error.code` / `error.category`；共享路径只允许追加 `ExecutionControlEvent` / `details` 等控制面事实，HTTP `status` / `result` 也必须继续返回该既有终态 truth，而不是重新包装成新的 API 私有终态。
  - HTTP service 必须允许同步读取 durable `accepted`、`running`、`succeeded`、`failed` 四类状态；不得把 API 收窄成“只能看终态”。
  - 若 `task_id` 不存在 durable record，`status` 与 `result` 都必须返回 machine-readable shared failed envelope，且错误语义必须与“记录不存在”一致，而不是混同为 transport 层 404 页面或 store 损坏。
  - 若 durable store 不可用、record 损坏、contract 非法、closeout/control-state truth 不可信或无法安全输出，`status` 与 `result` 都必须 fail-closed 为 shared failed envelope；不得宽松修复为看似合法的任务历史。
- 契约需求：
  - HTTP ingress 只允许把 transport 细节映射到共享请求 / 共享任务查询 contract；一旦进入 Core，`task_id`、`adapter_key`、`capability`、任务状态、终态结果、执行控制结果与错误分类语义都必须复用既有 shared contract。
  - `submit` 成功响应必须至少包含：`task_id`、`status`，以及一个可判定该任务已进入 shared durable path 的最小确认载荷；该响应不得额外创造与 `TaskRecord` 冲突的 shadow status 字段。
  - `submit` 的成功状态只允许表达“任务已进入共享 durable path”，不得把尚未产生 durable truth 的 ingress 接收动作伪装成已提交任务。
  - `submit` 若显式接收 `execution_control_policy`，则该字段必须完全映射到共享 `ExecutionControlPolicy`；若缺失则使用共享默认值；若字段缺失必需成员、成员类型不合法、违反共享 idempotency safety gate 前提，或无法被安全投影到共享控制 contract，则必须在 durable `accepted` 之前 fail-closed 为 shared failed envelope。
  - `status` 成功响应必须是 `TaskRecord` 当前状态视图的 HTTP 投影；至少要能回映到 `task_id`、当前 `status`、`created_at`、`updated_at`，以及在终态时的 `terminal_at`。
  - `result` 成功响应必须遵守以下闭环：
    - 若 `TaskRecord.status=succeeded`，则返回与 durable record 中 success envelope 一致的结果语义，继续包含共享字段 `raw` 与 `normalized`
    - 若 `TaskRecord.status=failed`，则返回与 durable record 中 failed envelope 一致的失败语义
    - 若 `TaskRecord.status=accepted|running`，则不得返回伪造终态 envelope；必须直接返回 `error.code=result_not_ready` 的 shared failed envelope
  - HTTP API 不得生成第二套 success/failed envelope。成功终态与失败终态都必须直接复用 `FR-0002` / `FR-0005` / `FR-0008` / `FR-0016` 已冻结的共享 carrier；非终态结果不可用分支也必须直接返回 shared failed envelope，而不是发明第三套 result schema 或 `HttpTaskResultView` 包裹层。
  - 对 `execution_timeout` 的共享对外语义，HTTP 必须保留 `error.category=platform` 与 `error.details.control_code=execution_timeout`；不得把它重分类为 `runtime_contract`，也不得隐藏其控制面来源。
  - 对 closeout/control-state failure 的共享对外语义，HTTP 必须保留 `runtime_contract` 分类；不得仅因该故障发生在 retry/closeout 阶段，就把它误投影为普通平台失败。
  - HTTP API 不得维护影子状态缓存、影子结果文件、影子事件流或 transport 私有任务表来替代 durable `TaskRecord` truth。
  - `status` / `result` 对同一 `task_id` 的输出语义必须与 CLI `query` 基于同一 durable record 能观察到的共享 truth 一致；不同入口只允许在 transport 表达上有差异，不允许在任务语义上分叉。
  - `status` / `result` 若共享结果中存在 `runtime_result_refs`，HTTP 必须把这些引用继续作为共享 truth 对外可见；不得在 transport 层吞掉它们，再额外发明 API 私有观测字段。
  - `submit` 若在 HTTP ingress 级别就发现缺少必填字段、字段类型不合法、capability/target 形状不满足当前 contract，或 pre-accepted concurrency gate 已拒绝该请求，则必须在进入 durable `accepted` 之前 fail-closed，并继续复用 shared failed envelope 的 `invalid_input` 语义。
  - `status` / `result` 若请求缺少 `task_id`，必须返回 shared failed envelope 的 `invalid_input` 语义；若 `task_id` 形状非法或不满足共享任务键 contract，则必须固定返回 `invalid_task_id` / `runtime_contract`；若 `task_id` 对应的 durable record 不存在，则必须固定返回 `task_record_not_found` / `invalid_input`；若 store、record contract 或共享序列化 truth 不可信，则必须固定返回 `task_record_unavailable` / `runtime_contract`。transport 层不得吞掉这些 shared error truth。
- 非功能需求：
  - API contract 必须保持实现无关，不绑定具体 web framework、router、线程模型、部署形态或存储引擎。
  - API contract 必须服务 `v0.6.0` 的“先闭环再暴露服务面”目标，只暴露最小 service surface，不提前承诺完整平台控制台。
  - API contract 必须保留 fail-closed 语义：任何无法证明与共享 Core path / durable truth / execution-control truth 一致的状态或结果，都不得对外暴露为合法 API 成功响应。
  - API contract 必须保留观测真相连续性：只要共享路径已经写入结构化控制结果、`ExecutionControlEvent` 或 `runtime_result_refs`，HTTP egress 就不得把这些信息裁剪掉。

## 约束

- 阶段约束：
  - 本事项只服务 `v0.6.0` 的最小可运维 service surface，不提前进入 `v0.7.0+` 的稳定 SDK、认证体系、复杂调度或 richer query 面。
  - `submit/status/result` 是当前唯一必需端点；若后续需要列表、取消、重试控制台、webhook 或流式观测，必须进入新的 formal spec。
- 架构约束：
  - Core 继续负责 admission、shared request 投影、执行控制、执行、`TaskRecord` durable truth、状态迁移、终态 envelope、`ExecutionControlEvent`、`runtime_result_refs` 与 fail-closed 语义；HTTP service 只负责 transport ingress/egress。
  - Adapter 继续只负责目标系统语义；HTTP API 不得拥有 adapter 直连旁路。
  - formal spec 与实现 PR 必须分离；当前 formal spec 回合不混入 `syvert/**`、`tests/**`、`scripts/**` 实现改动。

## GWT 验收场景

### 场景 1

Given 用户通过 HTTP `submit` 提交 `adapter_key`、`capability=content_detail_by_url` 与目标 URL  
When service 接收该请求  
Then 它必须把请求投影到既有共享任务请求模型，并沿与 CLI `run` 等价的 Core / `TaskRecord` durable path 工作，而不是直接调用 adapter

### 场景 2

Given 某个任务已经经由 CLI 或 HTTP `submit` 进入 durable `TaskRecord` 生命周期  
When 用户调用 HTTP `status` 并提供该 `task_id`  
Then service 必须回读同一条 durable `TaskRecord` 的当前状态 truth，而不是查询影子状态缓存

### 场景 3

Given 某个 durable `TaskRecord` 已经进入 `succeeded` 终态  
When 用户调用 HTTP `result`  
Then service 必须返回与 durable record 中 success envelope 一致的结果语义，并继续包含共享字段 `raw` 与 `normalized`

### 场景 4

Given 某个 durable `TaskRecord` 已经进入 `failed` 终态  
When 用户调用 HTTP `result`  
Then service 必须返回与 durable record 中 failed envelope 一致的失败语义，而不是重新包装另一套 API 私有错误对象

### 场景 5

Given 某个 durable `TaskRecord` 当前状态为 `accepted` 或 `running`  
When 用户调用 HTTP `result`  
Then service 不得伪造终态结果，而必须直接返回 `result_not_ready` / `invalid_input` 的 shared failed envelope

### 场景 6

Given 用户提交的 HTTP `submit` 或 `status/result` 请求缺少必填字段、字段类型不合法、`task_id` 形状非法，或 `ExecutionControlPolicy` 无法安全映射到共享 contract  
When service 在进入 durable path 前进行共享 contract 校验  
Then 它必须 fail-closed 为 shared failed envelope；其中缺少 `task_id` 继续投影为 `invalid_input`，非法 `task_id` 固定投影为 `invalid_task_id` / `runtime_contract`，而不是返回只属于 transport 层的非结构化错误页

### 场景 7

Given durable store 不可用、task record JSON 损坏、contract 非法、closeout/control-state truth 不可信或序列化阶段失败  
When HTTP `status` 或 `result` 试图回读该任务  
Then service 必须返回 shared failed envelope 并拒绝输出看似合法的状态或结果

### 场景 8

Given 共享执行路径在 durable `accepted` 之前因为并发门禁拒绝该请求  
When HTTP `submit` 返回失败  
Then 它必须投影为 shared failed envelope 的 `invalid_input` 语义，且不得创建 durable `TaskRecord`

### 场景 9

Given 某次执行以控制面 `execution_timeout` 收口  
When HTTP `result` 回读该失败结果  
Then 它必须继续保留 `error.category=platform` 与 `error.details.control_code=execution_timeout`，而不是把该故障重分类为 `runtime_contract`

### 场景 10

Given 某个已接受任务在 post-accepted retry 阶段发生 reacquire rejection，且上一 attempt 已有完成终态  
When HTTP `status` 或 `result` 回读该任务  
Then 它只能继续返回上一已完成 attempt 的终态 `error.code` / `error.category`，并把新的控制面事实限制在 `ExecutionControlEvent` / `details` / `runtime_result_refs` 等共享观测载荷内

## 异常与边界场景

- 异常场景：
  - 若 HTTP API 直接调用 adapter，再事后补写 `TaskRecord`，则违反 same-core-path contract。
  - 若 HTTP API 自行维护任务表、缓存状态、结果文件或控制事件流，并把它们当作查询真相，则违反 durable truth contract。
  - 若 `result` 在 `accepted` / `running` 状态返回伪造终态 payload，或把“结果尚不可用”伪装成空成功对象，则违反结果语义闭环。
  - 若 API 在成功终态或失败终态上重新定义另一套 envelope，或删掉 success envelope 中的共享字段 `raw` / `normalized`，则违反共享 carrier 约束。
  - 若 API 把整个 `platform` category 粗暴视为 retryable，或隐藏 `error.details.retryable` / `error.details.control_code` / `runtime_result_refs`，则违反共享执行控制与观测 truth。
  - 若 post-accepted retry reacquire rejection 被 API 重新包装为新的终态失败，进而覆盖上一已完成 attempt 的 `error.code` / `error.category`，则违反共享 closeout 语义。
- 边界场景：
  - 当前 formal spec 只定义最小 HTTP service surface，不定义具体路径命名、HTTP method、状态码映射、OpenAPI 文档格式或 framework 目录结构。
  - 当前 formal spec 允许 HTTP service 与 CLI 并存，但两者必须共享同一 durable store truth；不允许出现“CLI 看见一种状态，API 看见另一种状态”的分叉。
  - 当前 formal spec 不要求 `submit` 必须暴露同步等待终态、长轮询、流式返回或 webhook；这些能力若需要引入，必须进入新的 formal spec。
  - 当前 formal spec 不把 HTTP transport 身份、租户、权限或审计字段提升为共享任务 request / record contract 的一部分。
  - 当前 formal spec 允许 HTTP 侧显式暴露 `ExecutionControlPolicy`，但不允许把它扩张成 transport 私有调度 DSL；任何新增控制字段都必须先进入新的 shared formal spec。

## 验收标准

- [ ] formal spec 明确冻结最小 HTTP service surface 仅包含 `submit`、`status`、`result`
- [ ] formal spec 明确要求 HTTP `submit` 与 CLI `run` 共享同一条 Core / `TaskRecord` durable path，禁止 adapter 直连与旁路写入
- [ ] formal spec 明确要求 HTTP `status/result` 与 CLI `query` 共享同一 durable `TaskRecord` truth，而不是影子状态或影子结果 schema
- [ ] formal spec 明确要求成功终态与失败终态继续复用 shared envelope，禁止 API 新建第二套 envelope
- [ ] formal spec 明确要求 `accepted` / `running` 状态下 `result` 只能直接返回 `result_not_ready` / `invalid_input` 的 shared failed envelope，不能伪造终态或包裹为第三套 result schema
- [ ] formal spec 明确冻结 `ExecutionControlPolicy` 的 HTTP 可见性、共享默认值、idempotency safety gate 与 pre-accepted failure 边界
- [ ] formal spec 明确冻结 `execution_timeout`、platform transient failure、closeout/control-state failure 与 post-accepted reacquire rejection 的共享对外语义
- [ ] formal spec 明确要求 HTTP 不得吞掉 `ExecutionControlEvent` 细节或 `runtime_result_refs`
- [ ] formal spec 明确写清认证、多租户、RBAC、分布式队列、复杂查询 DSL、完整控制台不在当前范围内

## 依赖与外部前提

- 外部依赖：
  - `FR-0008` 已冻结 `TaskRecord` durable truth、终态 envelope 与 fail-closed 回读 contract
  - `FR-0009` 已冻结 CLI `run/query` same-path contract 与最小查询语义
  - `FR-0016` 已冻结共享执行控制、retryable predicate、`ExecutionControlPolicy` idempotency safety gate，以及 `execution_timeout` / closeout-control-state failure 的分类边界
  - `FR-0017` 已冻结执行控制结果进入结构化日志、指标与 `runtime_result_refs` 的共享可观测性语义
  - `docs/roadmap-v0-to-v1.md` 已把 `v0.6.0` 定义为“闭环后暴露第一个外部服务面”
- 上下游影响：
  - `#230` 将据此实现 HTTP endpoint surface，并把 transport 层接到既有 Core path，同时保留共享执行控制与 `runtime_result_refs` 真相
  - `#231` 将据此补齐 CLI/API same-path regression evidence，证明两个入口共享 durable truth、控制结果分类与结果回读语义
  - `#232` 将据此完成 FR-0018 parent closeout，把 GitHub 状态、PR、review、依赖 FR 与 release/sprint 真相收口
- closeout 语义：
  - `FR-0018` formal spec 完成不等于 HTTP service closeout 完成；只有在 `#230/#231/#232` 均完成，且 `FR-0016` / `FR-0017` 的共享控制与观测 truth 未被 HTTP surface 改写时，`FR-0018` 才算完成端到端 closeout。
