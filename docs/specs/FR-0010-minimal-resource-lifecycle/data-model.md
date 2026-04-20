# FR-0010 数据模型

## 实体清单

- 实体：`ResourceRecord`
  - 用途：表达被 Core 统一管理的最小共享资源基类
- 实体：`AccountResource`
  - 用途：表达账号类执行资源
- 实体：`ProxyResource`
  - 用途：表达代理类执行资源
- 实体：`ResourceBundle`
  - 用途：表达一次 `acquire` 成功后返回给调用方的整包资源 carrier
- 实体：`ResourceLease`
  - 用途：表达某组资源被某个 task 占用的唯一共享真相
- 实体：`ResourceLifecycleSnapshot`
  - 用途：表达 host-side durable store 中的 canonical lifecycle snapshot；为 bootstrap、load/write 与 revision compare-and-swap 提供唯一真相

## 关键字段

- `ResourceRecord`
  - `resource_id`
    - 约束：非空字符串；是资源唯一标识
  - `resource_type`
    - 约束：在 `v0.4.0` 只允许 `account` 或 `proxy`
  - `status`
    - 约束：只允许 `AVAILABLE`、`IN_USE`、`INVALID`
  - `material`
    - 约束：JSON-safe 的不透明 payload；允许承载账号/代理专属执行材料与 provider-side key，但在 `v0.4.0` 不得把这些类型专属值升格为新的共享顶层字段
- `AccountResource`
  - 继承约束：
    - 必须同时携带 `ResourceRecord` 的 `resource_id`、`resource_type`、`status`、`material`
    - 账号资源的 provider-side 专属标识若需要暴露，只允许封装在 `material` 中；`v0.4.0` 不另建稳定顶层 `account_key`
- `ProxyResource`
  - 继承约束：
    - 必须同时携带 `ResourceRecord` 的 `resource_id`、`resource_type`、`status`、`material`
    - 代理资源的 provider-side 专属标识若需要暴露，只允许封装在 `material` 中；`v0.4.0` 不另建稳定顶层 `proxy_key`
- `ResourceBundle`
  - `bundle_id`
    - 约束：非空字符串；用于标识本次成功 acquire 的 bundle
  - `lease_id`
    - 约束：非空字符串；必须与同次 acquire 建立的 `ResourceLease` 一一对应
  - `task_id` / `adapter_key` / `capability`
    - 约束：复用共享请求上下文，不再创建第二套 task 关联字段
  - `requested_slots`
    - 约束：非空、去重数组；只允许 `account`、`proxy`；成功时 bundle 中的已声明 slot 必须全部被填充，且未声明 slot 不得出现在成功 bundle 中
  - `acquired_at`
    - 约束：RFC3339 UTC 时间；必须与同次 acquire 成功建立的 `ResourceLease.acquired_at` 语义一致
  - `account` / `proxy`
    - 约束：对应 slot 若被请求，则成功 bundle 中必须存在且其 `status=IN_USE`；若未被请求，则对应 slot 不得出现在成功 bundle 中
- `ResourceLease`
  - `lease_id`
    - 约束：唯一、非空；是占用关系的唯一标识
  - `bundle_id`
    - 约束：必须回指同次 acquire 产生的 `ResourceBundle`
  - `task_id`
    - 约束：非空字符串；lease 只属于单个 task
  - `adapter_key` / `capability`
    - 约束：复用共享请求上下文；必须作为 lease 真相的一部分被持有，以支持 release 失败 envelope 的 canonical 回填
  - `resource_ids`
    - 约束：必须与 bundle 中实际承载的资源集合一致，且只能覆盖 `requested_slots` 对应的资源，不得额外记录未请求资源
  - `acquired_at`
    - 约束：RFC3339 UTC 时间；仅 acquire 成功后出现
  - `released_at`
    - 约束：仅 release 成功后出现
  - `target_status_after_release`
    - 约束：只允许 `AVAILABLE` 或 `INVALID`
  - `release_reason`
    - 约束：仅 release 成功后出现；非空字符串；与 `target_status_after_release` 一起构成重复 release 的幂等判定真相
- `ResourceLifecycleSnapshot`
  - `schema_version`
    - 约束：非空字符串；在 `v0.4.0` 固定为 `v0.4.0`
  - `revision`
    - 约束：非负整数；空快照从 `0` 开始；任一改变 durable truth 的成功写入必须以“当前 durable truth 的 `revision + 1`”提交；同值 bootstrap replay / no-op 不得推进 `revision`
  - `resources`
    - 约束：数组；元素必须全部满足 `ResourceRecord` contract；`resource_id` 必须唯一；与 snapshot 内 active / settled lease 真相保持一致
  - `leases`
    - 约束：数组；元素必须全部满足 `ResourceLease` contract；`lease_id` 必须唯一；用于决定哪些资源当前由 active lease 持有，以及最新 settled lease 对应的释放真相

## bootstrap 与 durable snapshot

- `seed_resources(records)` internal bootstrap surface
  - 输入约束：
    - 只允许 `Sequence[ResourceRecord]`；字符串 / bytes、非 `ResourceRecord` 元素或重复 `resource_id` 都必须视为非法 bootstrap 输入
  - 写入约束：
    - 只允许把此前不存在的 `resource_id` 追加进 `ResourceLifecycleSnapshot.resources`
    - 若某个 `resource_id` 已存在，只有与既有 `ResourceRecord` 完全一致时才允许作为 same-value replay / no-op
    - 既有 `resource_id` 只要 truth 不一致，就必须按冲突 fail-closed；bootstrap 不得覆写既有资源 truth
    - bootstrap 不得创建、删除或改写 `ResourceLifecycleSnapshot.leases`
  - 并发 / merge 约束：
    - 多个 disjoint bootstrap 写入必须收敛到同一份 canonical snapshot truth，而不是分叉成影子 store 结果
    - same-value replay / no-op 必须返回既有 snapshot truth，且不得制造新的 `revision`
- host-side 默认本地后端基线
  - `v0.4.0` 的 canonical default local backend 固定为单文件 `ResourceLifecycleSnapshot`
  - 路径入口固定为：优先读取 `SYVERT_RESOURCE_LIFECYCLE_STORE_FILE`，未提供时落到 `~/.syvert/resource-lifecycle.json`
  - 后续若要调整默认后端或默认路径，必须通过新的 formal spec 扩张 contract，而不是把变化降格成实现细节

## 失败载荷上下文

- `acquire` failed envelope
  - `task_id` / `adapter_key` / `capability`
    - 约束：优先回显可恢复的请求值；`task_id` 若缺失、不可恢复或形状非法，仍必须回填当前 task-bound Core 上下文中的非空 `task_id`；`adapter_key` / `capability` 若缺失、不可恢复或形状非法，则固定回填为 `""`
- `release` failed envelope
  - `task_id`
    - 约束：优先回显请求值；若请求里缺失、不可恢复或形状非法，仍必须回填当前 task-bound Core 上下文中的非空 `task_id`
  - `adapter_key` / `capability`
    - 约束：若 `lease_id` 已解析到既有 `ResourceLease`，则必须回填自该 lease 绑定的共享上下文；若 lease 尚不可解析，则固定回填为 `""`

## 生命周期

- bootstrap / durable 建档：
  - 当 host-side local store 尚不存在 durable truth 时，canonical 初始值固定为 `ResourceLifecycleSnapshot(schema_version=v0.4.0, revision=0, resources=(), leases=())`
  - `seed_resources(records)` 只有在新增此前不存在的资源 truth 时才推进 `revision`；同值 replay / no-op 必须保持 `revision` 不变
  - 任一 snapshot 写入若发现自身 `revision` 不是当前 durable truth 的下一个版本，必须 fail-closed，而不是静默覆写 store 中较新的 truth
- 创建：
  - 当 `acquire` 请求形状合法、全部 `requested_slots` 都绑定到 `AVAILABLE` 资源、且 `ResourceBundle` 与 `ResourceLease` 已可靠建立时，创建新的占用关系
  - 创建成功后，bundle 中全部资源状态必须同步推进为 `IN_USE`
- 更新：
  - `release(target_status_after_release=AVAILABLE)` 成功后，lease 绑定资源从 `IN_USE` 回到 `AVAILABLE`
  - `release(target_status_after_release=INVALID)` 成功后，lease 绑定资源从 `IN_USE` 进入 `INVALID`
  - 相同 `lease_id + target_status_after_release + release_reason` 的重复 `release` 只允许作为 idempotent no-op；冲突性重复 release 必须 fail-closed
- 失效/归档：
  - `INVALID` 在 `v0.4.0` 视为终态；本 FR 不定义从 `INVALID` 回到 `AVAILABLE` 的恢复语义
  - 失败 acquire 不得生成半完成 lease；失败 release 不得留下伪装成已释放的影子 truth
