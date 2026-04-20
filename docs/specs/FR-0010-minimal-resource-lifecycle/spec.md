# FR-0010 Minimal resource lifecycle

## 关联信息

- item_key：`FR-0010-minimal-resource-lifecycle`
- Issue：`#163`
- item_type：`FR`
- release：`v0.4.0`
- sprint：`2026-S17`

## 背景与目标

- 背景：`v0.3.0` 已冻结任务、结果与持久化闭环，但 `v0.4.0` 仍缺少最小资源系统。当前账号、代理与执行资源仍容易退化为 adapter 私有约定，Core 无法稳定表达“拿到什么资源、何时占用、何时释放、何时失效”。
- 目标：为 `v0.4.0` 冻结账号资源、代理资源、最小资源包、`AVAILABLE / IN_USE / INVALID` 状态集合，以及 Core 侧 `acquire / release` 主 contract 与失败语义，使后续实现可以围绕统一生命周期语义推进。

## 范围

- 本次纳入：
  - 冻结 `account` 与 `proxy` 两类最小共享资源类型
  - 冻结最小 `ResourceBundle` / `ResourceLease` 生命周期 carrier
  - 冻结 Core 侧 `acquire` / `release` 输入输出与失败语义
  - 冻结 `AVAILABLE -> IN_USE -> AVAILABLE|INVALID` 的最小迁移规则
- 本次不纳入：
  - 浏览器资源、设备资源或其他高阶资源类型
  - 资源能力匹配、需求声明、选择策略扩展与多资源档位
  - 资源使用日志与 task-bound 审计明细
  - Adapter 注入边界与“禁止自行来源化资源”的执行约束
  - 控制台、查询面、UI/API 与高级健康恢复循环

## 需求说明

- 功能需求：
  - `v0.4.0` 受管资源类型固定为 `account` 与 `proxy`，Core 不得在本 FR 中提前扩张到浏览器、设备或任意自定义资源族。
  - 每个共享资源至少必须具备稳定 `resource_id`、固定 `resource_type`、最小状态 `status` 与供后续消费的 `material`。`material` 允许承载账号/代理各自的 provider-side key 等类型专属、JSON-safe 的不透明 payload，但在 `v0.4.0` 不得把这些类型专属标识升格为新的共享顶层字段。
  - Core 侧最小 `acquire` 请求必须显式携带 `task_id`、`adapter_key`、`capability` 与 `requested_slots`；其中 `requested_slots` 必须为非空、去重数组，且允许值固定为 `account`、`proxy`。
  - `acquire` 成功时必须返回单个 `ResourceBundle`，至少包含 `bundle_id`、`lease_id`、`task_id`、`adapter_key`、`capability`、`requested_slots`、`acquired_at` 与对应 slot 下的资源实体。
  - `acquire` 的成功语义必须是“整包成功”：一旦请求声明某个 slot，Core 只有在该 slot 已被确定绑定到 `AVAILABLE` 资源时才可返回成功；不得返回缺 slot 的部分 bundle 并把其伪装成成功。
  - `acquire` 成功返回的 `ResourceBundle` 与同次建立的 `ResourceLease.resource_ids` 必须精确覆盖 `requested_slots` 对应的资源集合：请求了哪些 slot，就只能返回哪些 slot；不得附带未请求的 `account` / `proxy` 资源。
  - `release` 请求必须显式携带 `lease_id`、`task_id`、`target_status_after_release` 与 `reason`。`target_status_after_release` 在 `v0.4.0` 只允许 `AVAILABLE` 或 `INVALID`，`reason` 必须为非空字符串。
  - `release` 成功时必须只作用于该 `lease_id` 所绑定的同一组资源；Core 不得把 release 扩散到其他 bundle、其他 lease 或其他 task 的持有关系。
  - `release` 成功时必须返回同一 `lease_id` 的 settled `ResourceLease` 视图，至少包含 `lease_id`、`bundle_id`、`task_id`、`adapter_key`、`capability`、`resource_ids`、`acquired_at`、`released_at`、`target_status_after_release` 与 `release_reason`；后续实现不得在 `void`、确认字符串或另一套影子 carrier 之间自由发挥。
  - 相同 `lease_id` 的重复 `release` 只有在目标状态与理由语义完全一致时才允许作为 idempotent no-op；idempotent no-op 仍必须返回与首次成功 release 同一份 settled `ResourceLease` 语义，不得切换成其他 success carrier。任何冲突性重复 release、重复 acquire 绑定或 lease/task 对不上号都必须 fail-closed。
  - `v0.4.0` 的生命周期实现若需要本地默认后端，必须让资源库存 truth 与 lease truth 落在同一份 `ResourceLifecycleSnapshot` 中，并支持内部 `seed_resources(records)` bootstrap surface；该 surface 仅供测试与后续 provider 接入使用，不得被提升为终端用户 CLI / API。
- 契约需求：
  - 共享资源状态集合在 `v0.4.0` 固定为：
    - `AVAILABLE`：资源可被 Core 分配，但尚未被当前 task 占用
    - `IN_USE`：资源已被某个有效 `lease_id` 占用，不能再被第二个 task 重复分配
    - `INVALID`：资源已被判定为不可继续使用；在 `v0.4.0` 内视为终态，不定义自动恢复回 `AVAILABLE`
  - 允许的最小状态迁移固定为：
    - `AVAILABLE -> IN_USE`：仅在 `acquire` 成功时发生
    - `IN_USE -> AVAILABLE`：仅在 `release(target_status_after_release=AVAILABLE)` 成功时发生
    - `IN_USE -> INVALID`：仅在 `release(target_status_after_release=INVALID)` 成功时发生
  - 以下迁移必须被视为 contract violation 并 fail-closed：
    - `INVALID -> AVAILABLE`
    - `INVALID -> IN_USE`
    - 对同一资源跳过 `IN_USE` 直接从 `AVAILABLE` 进入第二个 task 的占用关系
    - 未经当前有效 lease 持有即执行 release
  - `ResourceBundle` 是 host-side canonical lifecycle carrier；其字段与 slot 命名在本 FR 冻结，但 Adapter 如何消费该 bundle 的执行边界由 `FR-0012` 定义，不在本 FR 重复展开。
  - `ResourceLease` 是“资源被某个 task 占用”的唯一共享真相源；在 `v0.4.0` 内不得为同一 `lease_id` 维护第二套影子 lease schema。若 `release reason` 参与幂等判定，它也必须落在该共享 carrier 上，而不是由实现层私自引入影子字段。
  - 若实现提供默认本地 store，`ResourceLifecycleSnapshot` 必须同时持有 `schema_version`、`revision`、`resources[]` 与 `leases[]`，并保证一次 `acquire / release / seed_resources` 的整包更新针对同一份 snapshot 原子落盘。
  - `acquire` 失败时不得留下“看似成功但资源未进入 `IN_USE`”的半完成 bundle truth；`release` 失败时也不得把资源悄悄回收到 `AVAILABLE`。
  - `acquire` / `release` 失败时，失败 carrier 必须复用上游 `FR-0002` / `FR-0005` 已冻结的共享 failed envelope：顶层字段继续为 `task_id`、`adapter_key`、`capability`、`status=failed`、`error`，不得额外发明字符串确认、异常对象或第二套错误 payload。
  - `acquire` 失败时，shared failed envelope 必须优先回显请求中可恢复的 `task_id`、`adapter_key`、`capability`；若 `task_id` 缺失、不可恢复或形状非法，Core 仍必须回填当前 task-bound 执行上下文中已存在的非空 `task_id`，不得降格为空字符串；`adapter_key` / `capability` 若缺失、不可恢复或形状非法，则固定回填为 `""`。
  - `release` 失败时，shared failed envelope 的 `task_id` 必须优先回显请求值；若请求里的 `task_id` 缺失、不可恢复或形状非法，Core 仍必须回填当前 task-bound 执行上下文中已存在的非空 `task_id`；若当前 `lease_id` 已解析到既有 `ResourceLease`，则 `adapter_key` 与 `capability` 必须回填自该 lease 绑定的共享上下文；若 lease 尚不可解析，则 `adapter_key=""`、`capability=""`。
  - `acquire` / `release` 的关键失败路径必须冻结稳定 `error.code`，至少包括：
    - `invalid_resource_request`
    - `invalid_resource_release`
    - `resource_unavailable`
    - `resource_lease_mismatch`
    - `resource_release_conflict`
    - `resource_state_conflict`
  - 对于 `resource_unavailable`：其语义固定为“请求形状合法，但当前 host-side runtime 无法为全部 `requested_slots` 提供满足整包 acquire contract 的 `AVAILABLE` 资源”，因此它不得被误报为静态 `unsupported` 或 adapter 已接管后的 `platform` 失败。
  - Core 必须是资源生命周期语义的唯一拥有者；任何 adapter、平台桥接层或外部调用方都不得直接改写共享资源状态。
- 非功能需求：
  - 生命周期 contract 必须 fail-closed；任何无法证明资源、bundle、lease 与当前 task 一致的情况，都不得宽松放行。
  - `v0.4.0` 的 lifecycle contract 仍必须保持 provider / adapter 无关；本 FR 冻结的是 host-side durable snapshot truth、revision compare-and-swap、bootstrap replay/no-op/conflict 与当前默认本地入口的 traceability，不把单文件 JSON store 升格为唯一长期后端。
  - 当前默认本地入口的 canonical baseline 为：host-side 默认本地后端可使用单文件 `ResourceLifecycleSnapshot`，路径入口优先读取 `SYVERT_RESOURCE_LIFECYCLE_STORE_FILE`、未提供时落到 `~/.syvert/resource-lifecycle.json`；这组语义只用于约束 `v0.4.0` 的默认本地入口与实现 traceability，不排斥后续通过新 formal spec 引入其他 backend 或路径策略。
  - 本 FR 只冻结“资源如何进入/退出占用态”的最小真相，不提前承诺调度公平性、优先级、租户隔离或复杂匹配。

## 约束

- 阶段约束：
  - 本事项只服务 `v0.4.0` 的最小资源系统，不提前定义 `v0.5.0` 的资源能力抽象或需求声明。
  - 本事项不提前引入浏览器 provider、租户策略或资源控制台语义。
- 架构约束：
  - Core 负责资源生命周期与状态迁移；Adapter 只允许在后续 FR 已批准的边界内消费由 Core 注入的 bundle。
  - formal spec 与实现 PR 必须分离；`#164` 只冻结 requirement，不混入 `syvert/**` 或 `tests/**` 实现改动。
  - 生命周期主 contract 不得偷渡 `FR-0011` 的审计日志细节，也不得提前吞入 `FR-0012` 的 Adapter 注入约束。
  - `resource-lifecycle` 调用固定处于 task-bound Core 运行时路径内；本 FR 不放宽上游 shared envelope 对“`task_id` 始终存在且为非空字符串”的约束。

## GWT 验收场景

### 场景 1

Given Core 收到带有 `task_id`、`adapter_key`、`capability` 和 `requested_slots=[account, proxy]` 的 `acquire` 请求，且两个 slot 都存在 `AVAILABLE` 资源  
When Core 完成分配  
Then Core 必须返回单个成功 `ResourceBundle`，并把该 bundle 内所有资源状态统一推进为 `IN_USE`，且返回 carrier 只能覆盖 `requested_slots` 中声明的两个 slot

### 场景 2

Given `requested_slots=[account, proxy]`，但当前只有 `account` 存在 `AVAILABLE` 资源  
When Core 执行 `acquire`  
Then Core 必须整体失败，而不是返回缺少 `proxy` 的部分 bundle

### 场景 3

Given 某个 `lease_id` 正持有一组 `IN_USE` 资源  
When Core 以 `target_status_after_release=AVAILABLE` 调用 `release`  
Then 该 lease 绑定的全部资源都必须从 `IN_USE` 回到 `AVAILABLE`

### 场景 4

Given 某个 `lease_id` 正持有一组 `IN_USE` 资源，且本次执行判断这些资源不可继续复用  
When Core 以 `target_status_after_release=INVALID` 调用 `release`  
Then 该 lease 绑定的全部资源都必须从 `IN_USE` 进入 `INVALID`

### 场景 5

Given 同一个 `lease_id` 已经成功执行过一次 `release(target_status_after_release=AVAILABLE, reason=normal)`  
When Core 以完全相同的 release 语义再次重试  
Then Core 只允许把这次重复请求视为 idempotent no-op，而不能重新打开或重绑该 lease

### 场景 6

Given 某个资源已经处于 `INVALID`  
When Core 试图再次通过 `acquire` 把它分配进新的 bundle  
Then Core 必须 fail-closed，而不能把 `INVALID` 资源重新当成可用资源

### 场景 7

Given host-side 默认本地 store 已持有某个 `ResourceRecord` 的 durable truth，且 `seed_resources(records)` 再次写入完全相同的记录  
When Core 执行 bootstrap replay  
Then 该操作只允许被视为 same-value replay / no-op，不得改写 snapshot truth，也不得推进 `revision`

### 场景 8

Given host-side 默认本地 store 已持有较新的 snapshot truth，或 `seed_resources(records)` 试图为既有 `resource_id` 写入与 durable truth 不一致的记录  
When Core 执行 snapshot 写入或 bootstrap  
Then Core 必须以 `resource_state_conflict` fail-closed，而不是覆写较新的 `revision` 或篡改既有资源 truth

## 异常与边界场景

- 异常场景：
  - `acquire` 请求缺少 `task_id`、`adapter_key`、`capability` 或携带未知 slot 时，必须按无效请求失败，而不是猜测默认值；failed envelope 只能回显可恢复的请求值，其中 `task_id` 仍必须保持非空，`adapter_key` / `capability` 缺失时固定回填为空字符串。
  - 若某个资源在 `acquire` 过程中已经不再处于 `AVAILABLE`，Core 必须整体拒绝本次 bundle，而不是把冲突资源静默替换成其他未知资源。
  - 若 `release` 的 `lease_id` 与 `task_id` 不匹配、或该 lease 已被另一条冲突 release 收口，Core 必须 fail-closed。
- 边界场景：
  - 本事项只定义 `account`、`proxy` 两类 slot；不要求任何 slot 都必须在所有 task 中同时出现。
  - 未出现在 `requested_slots` 中的 slot 不得出现在成功 `ResourceBundle` 或同次 `ResourceLease.resource_ids` 中。
  - `ResourceBundle` 的顶层 carrier 在本 FR 冻结，但 Adapter 如何接入该 bundle、能否读取其中哪部分字段，由 `FR-0012` 再冻结。
  - `seed_resources(records)` 只属于 host-side internal bootstrap surface，不得漂移成终端用户 CLI / API。
  - host-side 默认本地 store 的 canonical baseline 固定为单文件 `ResourceLifecycleSnapshot` 与 `SYVERT_RESOURCE_LIFECYCLE_STORE_FILE` / `~/.syvert/resource-lifecycle.json` 路径入口；该 baseline 的后续调整必须走新的 formal spec。
  - 本 FR 只冻结最小状态机；不要求在 `v0.4.0` 提供 `INVALID` 的恢复、再验证或自动修复循环。

## 验收标准

- [ ] formal spec 明确冻结 `account`、`proxy`、`ResourceBundle` 与 `ResourceLease` 的最小共享语义
- [ ] formal spec 明确冻结 `acquire` / `release` 的输入输出与失败语义
- [ ] formal spec 明确冻结 `AVAILABLE / IN_USE / INVALID` 状态集合与允许迁移
- [ ] formal spec 明确禁止部分 bundle 成功、冲突 lease 与越权状态改写
- [ ] formal spec 明确冻结 `ResourceLifecycleSnapshot`、`seed_resources(records)`、revision compare-and-swap 与 same-value replay / no-op / conflict 语义
- [ ] formal spec 明确冻结 host-side 默认本地 store 的路径入口语义：优先 `SYVERT_RESOURCE_LIFECYCLE_STORE_FILE`，否则 `~/.syvert/resource-lifecycle.json`
- [ ] formal spec 明确把审计日志与 Adapter 注入边界留在相邻 FR，而不是混入同一事项

## 依赖与外部前提

- 外部依赖：
  - `#162` 作为 `v0.4.0` Phase 已建立，并把最小资源系统定义为当前阶段目标
  - `#163` 作为本 FR 的 canonical requirement 容器已建立，并绑定 `#164`
  - `FR-0004` 已冻结 `adapter_key` 与 `capability` 的共享输入语义
  - `FR-0002` 与 `FR-0005` 已冻结 shared envelope 顶层字段与失败分类边界，是 `task_id / adapter_key / capability / status=failed / error` 的上游约束
- 上下游影响：
  - `FR-0011` 必须复用本 FR 冻结的资源类型、状态名与 lease/bundle 主 carrier
  - `FR-0012` 必须消费本 FR 冻结的 `ResourceBundle` truth，而不是另建第二套 bundle schema
