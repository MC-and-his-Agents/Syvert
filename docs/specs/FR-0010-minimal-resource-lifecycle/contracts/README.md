# resource-lifecycle contract（v0.4.0）

## 接口名称与版本

- 接口名称：`resource-lifecycle`
- contract 版本：`v0.4.0`
- 作用：定义账号资源、代理资源、资源包、共享 lease 与 Core 侧 `acquire / release` 最小边界

## 输入输出结构

- `acquire`
  - 输入：
    - `task_id`
    - `adapter_key`
    - `capability`
    - `requested_slots[]`，必须非空且去重，允许值固定为 `account`、`proxy`
  - 输出：
    - 成功时返回单个 `ResourceBundle`
    - `ResourceBundle` 至少包含 `bundle_id`、`lease_id`、`task_id`、`adapter_key`、`capability`、`requested_slots`、`acquired_at` 与对应 slot 下的资源实体
  - 成功约束：
    - 所有 `requested_slots` 都已绑定到 `AVAILABLE` 资源
    - bundle 内资源在返回时统一处于 `IN_USE`
    - 对应 slot 下的资源实体至少包含共享 `resource_id`、`resource_type`、`status`、`material`；账号/代理专属标识继续封装在 `material` 中，不额外冻结新的共享顶层字段
    - `ResourceBundle` 与同次 `ResourceLease.resource_ids` 只能且必须覆盖 `requested_slots` 对应的资源；不得额外附带未请求 slot
- `release`
  - 输入：
    - `lease_id`
    - `task_id`
    - `target_status_after_release`
    - `reason`
  - 输出：
    - 成功时返回 settled `ResourceLease`
  - 成功约束：
    - `target_status_after_release` 只允许 `AVAILABLE` 或 `INVALID`
    - release 只允许作用于该 lease 当前持有的资源集合
    - 返回载荷至少包含 `lease_id`、`bundle_id`、`task_id`、`adapter_key`、`capability`、`resource_ids`、`acquired_at`、`released_at`、`target_status_after_release`、`release_reason`
    - 返回的 `ResourceLease` 必须保留 `adapter_key` 与 `capability`，作为后续 release 失败 envelope 的 canonical 回填来源

## host-side durable store / bootstrap surface

- `ResourceLifecycleSnapshot`
  - 作用：作为 host-side local store 的 canonical durable carrier，承载 `schema_version`、`revision`、`resources[]`、`leases[]`
  - 约束：
    - 空 durable truth 的 canonical 初始值固定为 `schema_version=v0.4.0`、`revision=0`、`resources=[]`、`leases=[]`
    - `resources[]` / `leases[]` 必须继续满足 `FR-0010` 已冻结的 `ResourceRecord` / `ResourceLease` contract，不得在 store 层降格成第二套影子 schema
    - snapshot 中的 active / settled lease truth 必须能唯一解释资源当前状态；`IN_USE` 资源不得脱离 active lease 单独存在
- durable truth 读取 / 提交语义
  - 读取边界：
    - 若本地 store 尚不存在，读取结果必须回落到空 snapshot，而不是 `null`、`{}` 或其他影子 carrier
    - 不可读、损坏、shape 非法或 contract 非法的 snapshot 都必须被视为共享 truth 冲突，而不是被静默忽略或自动修复
  - 提交约束：
    - 只允许提交满足完整 snapshot contract 的 payload
    - 任一成功的 `acquire`、`release` 或 `seed_resources(records)` 都必须把本次变更后的 `resources[]` 与 `leases[]` 真相作为同一份 snapshot 原子提交；不得留下部分资源状态已更新、lease truth 未更新，或仅推进 `revision` 的半完成结果
    - `revision` 必须精确等于当前 durable truth 的 `revision + 1`
    - 任一 stale write、乱序 revision 或试图覆写更新 durable truth 的行为，都必须以 `resource_state_conflict` fail-closed
- `seed_resources(records)` internal bootstrap surface
  - 作用：在 `acquire` 前向 snapshot 注入初始 `ResourceRecord` truth；这是 host-side internal bootstrap 入口，不是 Adapter-facing public runtime surface
  - 成功约束：
    - 输入只允许 `ResourceRecord` 序列；bootstrap 不得越权写入 lease truth
    - 同一输入批次若出现重复 `resource_id`，必须在触达 durable truth 前直接 fail-closed；不得静默去重，也不得把同批重复解释为 replay / conflict
    - 对此前不存在的 `resource_id`，允许把记录并入当前 snapshot
    - 对已存在的 `resource_id`，只有与既有 truth 完全一致时才允许 same-value replay / no-op
    - same-value replay / no-op 必须保持当前 `revision` 不变
    - 同一 `resource_id` 只要 truth 不一致，就必须返回 `resource_state_conflict`，而不是覆写既有资源 truth
    - disjoint 新增资源必须并入同一份 canonical snapshot，而不是拆成多份并行 truth
- 默认本地 store 路径
  - host-side 默认本地 store 位置由环境变量 `SYVERT_RESOURCE_LIFECYCLE_STORE_FILE` 控制；未显式覆盖时，默认路径固定为 `~/.syvert/resource-lifecycle.json`
  - `v0.4.0` 的当前默认本地入口可使用单文件 `ResourceLifecycleSnapshot`；上述 env var / fallback path 属于该默认入口的正式 traceability contract，而不是可随意漂移的实现提示
  - 该路径选择 contract 只属于本地 durable store boundary；`FR-0010` 不因此新增 `acquire` / `release` 的 public store-path 参数，也不引入第二套 store selector

## 错误与边界行为

- 失败返回 carrier：
  - `acquire` / `release` 失败都必须复用共享 failed envelope
  - 顶层字段固定为：`task_id`、`adapter_key`、`capability`、`status=failed`、`error`
  - `acquire` 失败时：`task_id`、`adapter_key`、`capability` 必须优先回显可恢复的请求值；`task_id` 若缺失、不可恢复或形状非法，仍必须回填当前 task-bound Core 上下文中的非空 `task_id`；`adapter_key` / `capability` 若缺失、不可恢复或形状非法，则固定回填为空字符串
  - `release` 失败时：`task_id` 必须优先回显请求值；若请求里缺失、不可恢复或形状非法，仍必须回填当前 task-bound Core 上下文中的非空 `task_id`；若 `lease_id` 已解析到既有 lease，则 `adapter_key` / `capability` 回填自该 lease；否则二者固定为空字符串
- `invalid_input`
  - 适用场景：
    - 缺少 `task_id`、`adapter_key`、`capability`
    - `requested_slots` 为空、重复、形状不合法或出现 `account`、`proxy` 之外的未知 slot
    - `release` 缺少 `lease_id`、`task_id`、`target_status_after_release` 或 `reason`
    - `reason` 为空字符串
    - `target_status_after_release` 不是 `AVAILABLE` 或 `INVALID`
  - canonical `error.code`：
    - `invalid_resource_request`
    - `invalid_resource_release`
- `runtime_contract`
  - 适用场景：
    - 请求形状与 slot 集合法，但当前运行时资源集合没有足够的 `AVAILABLE` 资源满足整包 acquire，导致 host-side runtime 的整包 acquire contract 无法成立
    - 资源在 acquire 过程中出现状态冲突或重复分配
    - host-side durable snapshot 不可读、损坏、shape 非法、schema/version/revision 非法，或其 active / settled truth 与资源状态不一致
    - snapshot write 的 `revision` 与当前 durable truth 不一致，导致 stale write 试图覆写更新 truth
    - `lease_id` 与 `task_id` 不匹配，或 release 试图收口非当前持有关系
    - 重复 release 的语义冲突，无法被判定为 idempotent no-op
    - `seed_resources(records)` 试图覆写既有 `resource_id` 的资源 truth，或把 bootstrap 输入扩张成 lease / shadow schema 写入
    - 任一资源试图执行未批准的状态迁移
  - canonical `error.code`：
    - `resource_unavailable`
    - `resource_lease_mismatch`
    - `resource_release_conflict`
    - `resource_state_conflict`
- 边界约束：
  - acquire 失败时不得返回部分 bundle
  - acquire 成功时不得返回未在 `requested_slots` 中声明的额外 slot 或资源
  - release 失败时不得静默把资源重新标记为 `AVAILABLE`
  - 重复 `release` 只有在 `lease_id` 一致、`target_status_after_release` 一致且 `reason` 完全一致时，才允许作为 canonical idempotent no-op
  - canonical idempotent no-op 仍必须返回与首次成功 release 同一份 settled `ResourceLease`
  - 任一重复 `release` 只要目标状态或 `reason` 不一致，就必须返回 `resource_release_conflict`
  - `ResourceBundle` 是 host-side canonical carrier；Adapter 注入边界由 `FR-0012` 继续定义，不在本 contract 中重写

## 向后兼容约束

- `task_id`、`adapter_key`、`capability` 继续复用上游已冻结字段，不另建影子上下文字段
- `v0.4.0` 不引入第三种以上资源类型，也不引入复杂匹配与调度语义
- `INVALID` 在 `v0.4.0` 为终态；若后续需要恢复机制，必须通过新的 formal spec 扩张 contract
