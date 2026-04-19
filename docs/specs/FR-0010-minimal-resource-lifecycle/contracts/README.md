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
    - `requested_slots[]`，允许值固定为 `account`、`proxy`
  - 输出：
    - 成功时返回单个 `ResourceBundle`
    - `ResourceBundle` 至少包含 `bundle_id`、`lease_id`、`task_id`、`adapter_key`、`capability`、`requested_slots`、`acquired_at` 与对应 slot 下的资源实体
  - 成功约束：
    - 所有 `requested_slots` 都已绑定到 `AVAILABLE` 资源
    - bundle 内资源在返回时统一处于 `IN_USE`
- `release`
  - 输入：
    - `lease_id`
    - `task_id`
    - `target_status_after_release`
    - `reason`
  - 输出：
    - 成功时确认同一 `lease_id` 已被一致收口
  - 成功约束：
    - `target_status_after_release` 只允许 `AVAILABLE` 或 `INVALID`
    - release 只允许作用于该 lease 当前持有的资源集合

## 错误与边界行为

- `invalid_input`
  - 适用场景：
    - 缺少 `task_id`、`adapter_key`、`capability`
    - `requested_slots` 为空或形状不合法
    - `requested_slots` 出现 `account`、`proxy` 之外的未知 slot
    - `release` 缺少 `lease_id` 或 `task_id`
- `runtime_contract`
  - 适用场景：
    - 任一 `requested_slot` 没有可用 `AVAILABLE` 资源，导致整包 acquire 无法成立
    - 资源在 acquire 过程中出现状态冲突或重复分配
    - `lease_id` 与 `task_id` 不匹配，或 release 试图收口非当前持有关系
    - 重复 release 的语义冲突，无法被判定为 idempotent no-op
    - 任一资源试图执行未批准的状态迁移
- 边界约束：
  - acquire 失败时不得返回部分 bundle
  - release 失败时不得静默把资源重新标记为 `AVAILABLE`
  - `ResourceBundle` 是 host-side canonical carrier；Adapter 注入边界由 `FR-0012` 继续定义，不在本 contract 中重写

## 向后兼容约束

- `task_id`、`adapter_key`、`capability` 继续复用上游已冻结字段，不另建影子上下文字段
- `v0.4.0` 不引入第三种以上资源类型，也不引入复杂匹配与调度语义
- `INVALID` 在 `v0.4.0` 为终态；若后续需要恢复机制，必须通过新的 formal spec 扩张 contract
