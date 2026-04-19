# adapter-resource-injection contract（v0.4.0）

## 接口名称与版本

- 接口名称：`adapter-resource-injection`
- contract 版本：`v0.4.0`
- 作用：定义 Core 向 Adapter 注入 `ResourceBundle` 的最小执行边界

## 输入输出结构

- 输入结构：
  - `AdapterExecutionContext`
  - 其中 `resource_bundle` 完整复用 `FR-0010` 已冻结的 `ResourceBundle` carrier，不得删减其已冻结字段（至少包括 `acquired_at`）
  - `resource_bundle` 只允许两种状态：
    - 合法完整 bundle：用于资源依赖路径
    - `null`：仅当该执行路径被 Core 明确判定为不依赖受管资源
- 输出结构：
  - Adapter 成功/失败结果继续复用既有 Core envelope
  - 若需反馈资源处置建议，返回 `ResourceDispositionHint(lease_id, target_status_after_release, reason)`

## 错误与边界行为

- `invalid_input`
  - 适用场景：
    - `ResourceDispositionHint` 缺少 `lease_id`、`target_status_after_release` 或 `reason`
    - `reason` 为空字符串
    - `target_status_after_release` 不是 `AVAILABLE` 或 `INVALID`
- `runtime_contract`
  - 适用场景：
    - 资源依赖路径下 `resource_bundle` 缺失、slot 不完整或 `lease_id` 与当前 task 不一致
    - Adapter 试图直接改写共享资源状态、lease 或 tracing truth
    - Adapter 试图从注入 bundle 之外再额外来源化账号/代理作为主执行资源
- 边界约束：
  - 缺 bundle 时由 Core 在调用前 fail-closed，不能把补资源责任下放给 Adapter
  - Adapter 允许消费 bundle material 并生成执行内临时对象，但这些临时对象不是新的共享资源 truth
  - 最终 release / invalidate 始终由 Core 执行

## 向后兼容约束

- `resource_bundle` 顶层 carrier 必须继续复用 `FR-0010`，不得新增影子 bundle schema
- `target_status_after_release` 必须继续复用 `FR-0010` release 语义
- `v0.4.0` 不通过本 contract 引入资源需求 DSL、能力匹配或 provider 选择规则
