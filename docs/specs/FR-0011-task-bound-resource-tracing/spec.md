# FR-0011 Task-bound resource tracing and usage logs

## 关联信息

- item_key：`FR-0011-task-bound-resource-tracing`
- Issue：`#165`
- item_type：`FR`
- release：`v0.4.0`
- sprint：`2026-S17`

## 背景与目标

- 背景：`FR-0010` 冻结了资源生命周期主 contract，但 `v0.4.0` 还需要把“资源状态如何被追踪、任务如何证明自己占用了哪些资源、何时释放/失效”落成统一审计语义，否则资源系统只剩状态机而缺少可复验的证据面。
- 目标：为 `v0.4.0` 冻结资源状态跟踪与资源使用日志的 formal contract，明确 `task_id / resource_id / lease_id / bundle_id` 的关联字段、最小事件时间线与最小审计面，使后续实现与 release gate 可以围绕同一套追踪 truth 推进。

## 范围

- 本次纳入：
  - 冻结 task-bound `ResourceTraceEvent` append-only 事件 truth
  - 冻结 task/resource/lease/bundle 的最小关联字段
  - 冻结 `acquired / released / invalidated` 事件类型与最小时间线语义
  - 冻结“资源使用日志”作为 task-bound 投影的最小审计面
- 本次不纳入：
  - 资源生命周期主接口、状态机与 bundle 分配规则
  - Adapter 注入边界与禁止自行来源化执行资源
  - 查询 UI、审计控制台、跨租户报表与高级分析面
  - 非 task-bound 的库存治理、后台修复任务与复杂告警体系

## 需求说明

- 功能需求：
  - 对每一次成功进入任务执行路径的资源占用，Core 都必须记录 append-only 的 `ResourceTraceEvent`。`ResourceTraceEvent` 是本 FR 的 canonical tracing truth，不允许维护第二套影子事件流。
  - `ResourceTraceEvent` 至少必须携带：
    - `event_id`
    - `task_id`
    - `lease_id`
    - `bundle_id`
    - `resource_id`
    - `resource_type`
    - `adapter_key`
    - `capability`
    - `event_type`
    - `from_status`
    - `to_status`
    - `occurred_at`
    - `reason`
  - `reason` 在 `v0.4.0` 内对所有事件都是必填字段：
    - `acquired`：表达资源为何被当前 task 占用；最小 canonical 语义允许使用 `acquired_for_task`
    - `released`：表达资源为何回收到 `AVAILABLE`
    - `invalidated`：表达资源为何进入 `INVALID`
  - `resource_type` 在 `v0.4.0` 只允许复用 `FR-0010` 已冻结的 `account`、`proxy`，不得在 tracing 层另建第三套资源类型命名。
  - `event_type` 在 `v0.4.0` 固定为：
    - `acquired`
    - `released`
    - `invalidated`
  - `from_status` 与 `to_status` 必须严格复用 `FR-0010` 的状态名与允许迁移集合。tracing 层可以观察这些迁移，但不得重新定义新的状态轴。
  - 若一个 `ResourceBundle` 同时包含多个资源 slot，则必须为 bundle 内每个 `resource_id` 分别记录事件，但这些事件必须共享同一 `task_id`、`lease_id`、`bundle_id`，以表达“同一 task 在同一 lease 下占用了一组资源”。
  - “资源使用日志”在 `v0.4.0` 内固定定义为 `ResourceTraceEvent` 的 task-bound 投影：系统至少必须能够按 `task_id`、`lease_id` 或 `resource_id` 重建该 task 使用过哪些资源、何时 acquire、何时 release 或 invalidate。
  - 上述最小审计面同样必须支持按 `bundle_id` 重建同一 bundle 内资源的收口过程。
  - tracing 成功语义必须覆盖最小时间线：
    - `acquired` 事件：`AVAILABLE -> IN_USE`
    - `released` 事件：`IN_USE -> AVAILABLE`
    - `invalidated` 事件：`IN_USE -> INVALID`
  - 若后续实现需要表达更细粒度阶段或扩展事件类型，必须通过新的 formal spec 扩张，而不是在本 FR 的实现中隐式添加。
- 契约需求：
  - 只要某次生命周期迁移已经对外被视为成功，该迁移对应的 `ResourceTraceEvent` 就必须已经成为可信 truth；不得出现“资源已成功释放/失效，但审计面完全缺席”的分叉状态。
  - `ResourceTraceEvent` 必须 append-only；不允许通过原地覆写旧事件来伪造时间线。
  - 相同 `event_id` 的重复写入只有在 payload 完全一致时才允许作为 idempotent no-op；冲突性重复事件必须 fail-closed。
  - 对于 task-bound 事件，`task_id`、`lease_id`、`bundle_id`、`resource_id` 四个轴缺一不可；缺少其中任一字段的事件不得被视为合法审计事实。
  - task-bound usage log 不要求定义独立存储引擎或查询 API，但必须保证同一事件 truth 能被：
    - 按 `task_id` 看到该 task 占用过哪些资源
    - 按 `resource_id` 看到该资源被哪些 task 占用过
    - 按 `lease_id` 或 `bundle_id` 看到同一组资源的收口过程
  - 若事件写入失败、字段不完整、状态迁移与 `FR-0010` 不一致，Core 必须 fail-closed，而不是把 tracing 降格为 best-effort 日志。
- 非功能需求：
  - tracing contract 必须保持实现无关，不绑定唯一数据库、唯一消息总线或唯一审计后端。
  - 审计面只要求最小可判定 truth，不要求 `v0.4.0` 提供富查询、统计、报表或跨租户分析。
  - tracing 只承载资源运行时与 task 的关联真相，不提前承担平台级业务日志或用户态诊断日志职责。

## 约束

- 阶段约束：
  - 本事项只服务 `v0.4.0` 的最小资源追踪闭环，不提前展开审计平台或可视化查询系统。
  - 本事项不重写 `FR-0010` 的 acquire/release 主接口，只消费它们的状态迁移结果。
- 架构约束：
  - Core 负责记录和维护 tracing truth；Adapter 不负责直接写入共享资源状态追踪真相。
  - formal spec 与实现 PR 必须分离；`#166` 只冻结 tracing / usage log requirement，不混入运行时代码。
  - 本事项不得偷渡 `FR-0012` 的注入 boundary，也不得把 tracing payload 变成第二套资源生命周期主 contract。

## GWT 验收场景

### 场景 1

Given 某个 task 通过 `lease_id=l-1` 成功 acquire 到 `account` 与 `proxy` 两个资源  
When Core 记录 tracing truth  
Then Core 必须为两个 `resource_id` 分别写入 `acquired` 事件，且它们共享相同的 `task_id`、`lease_id`、`bundle_id`

### 场景 2

Given 某个 task 的资源执行完成并正常释放  
When Core 收口该 `lease_id`  
Then 每个被该 lease 持有的 `resource_id` 都必须记录 `released` 事件，并把时间线闭合到 `IN_USE -> AVAILABLE`

### 场景 3

Given 某个 task 在执行期间发现当前资源不可继续复用  
When Core 以失效语义收口该 `lease_id`  
Then 每个被该 lease 持有的 `resource_id` 都必须记录 `invalidated` 事件，并把时间线闭合到 `IN_USE -> INVALID`

### 场景 4

Given 调用方按 `task_id` 查询某个 task 的资源使用日志  
When 系统基于 tracing truth 构建最小审计视图  
Then 该视图至少必须能说明该 task 用过哪些 `resource_id`、对应的 `lease_id / bundle_id` 以及 acquire/release 或 invalidate 的发生时间

### 场景 5

Given 某次资源状态迁移已经被当作成功对外可见  
When 对应 tracing 事件缺少 `task_id`、`lease_id`、`bundle_id` 或 `resource_id`  
Then Core 必须把该迁移视为不成立并 fail-closed，而不是把 tracing 降格为可缺失的附属日志

## 异常与边界场景

- 异常场景：
  - 若同一 `event_id` 被写入了不同 payload，系统必须拒绝把它当作合法历史。
  - 若事件中的 `from_status / to_status` 违反 `FR-0010` 已冻结的迁移集合，tracing 层必须 fail-closed。
  - 若同一 bundle 中多个资源的事件失去共同 `lease_id / bundle_id`，则无法证明它们属于同一 task 的同一次占用，必须视为非法审计 truth。
- 边界场景：
  - 本事项只要求 task-bound tracing；不要求在 `v0.4.0` 冻结跨租户审计维度、报表口径或告警规则。
  - “使用日志”是 tracing truth 的最小投影，不要求额外再维护一套不同 schema 的日志存储。
  - 非 task-bound 的库存维护、后台修复或人工剔除流程不在本 FR 的最小审计面内。

## 验收标准

- [ ] formal spec 明确冻结 `ResourceTraceEvent` 的最小字段集合与 append-only 语义
- [ ] formal spec 明确冻结 `acquired / released / invalidated` 事件类型与最小时间线
- [ ] formal spec 明确冻结 task/resource/lease/bundle 的关联字段
- [ ] formal spec 明确要求资源使用日志可由 tracing truth 按 `task_id`、`resource_id`、`lease_id` 与 `bundle_id` 重建
- [ ] formal spec 明确要求 tracing 与生命周期迁移保持单一真相，失败时 fail-closed

## 依赖与外部前提

- 外部依赖：
  - `#162` 已把“资源状态与使用日志可按任务追踪”设为 `v0.4.0` 阶段目标
  - `#165` 作为本 FR 的 canonical requirement 容器已建立，并绑定 `#166`
  - `FR-0010` 负责冻结资源类型、bundle/lease 主 carrier 与状态机，是本 FR 的直接上游前提
- 上下游影响：
  - 后续 release gate 与资源回归验证必须消费本 FR 冻结的 tracing truth
  - `FR-0012` 如需把资源事件反馈回 Core，只能复用本 FR 已冻结的 task/resource/lease 关联语义
