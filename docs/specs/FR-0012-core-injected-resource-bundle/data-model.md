# FR-0012 数据模型

## 实体清单

- 实体：`InjectedResourceBundle`
  - 用途：表达 Core 在调用 Adapter 前注入的 bundle carrier
- 实体：`AdapterExecutionContext`
  - 用途：表达 Adapter 执行时可见的最小上下文，其中包含 `resource_bundle`
- 实体：`ResourceDispositionHint`
  - 用途：表达 Adapter 返回给 Core 的最小资源处置建议

## 关键字段

- `InjectedResourceBundle`
  - `bundle_id`
    - 约束：非空字符串；必须复用 `FR-0010` 已冻结 carrier
  - `lease_id`
    - 约束：非空字符串；必须与当前 task 的占用关系一致
  - `task_id` / `adapter_key` / `capability`
    - 约束：复用共享执行上下文
  - `requested_slots`
    - 约束：与本次资源依赖路径的最小 slot 集一致
  - `account` / `proxy`
    - 约束：若 slot 被请求，则必须存在且与 `FR-0010` 的 bundle truth 一致
- `AdapterExecutionContext`
  - `request`
    - 约束：复用上游已冻结的共享请求语义
  - `resource_bundle`
    - 约束：由 Core 决定是否注入合法 bundle、空 bundle 或 `null`；Adapter 不得自行替换
- `ResourceDispositionHint`
  - `lease_id`
    - 约束：必须指向当前执行使用的注入 bundle
  - `target_status_after_release`
    - 约束：只允许 `AVAILABLE` 或 `INVALID`
  - `reason`
    - 约束：非空字符串；表达最小处置原因

## 生命周期

- 创建：
  - Core 在调用 Adapter 前完成 bundle 注入；只有当 bundle 形状与当前 task 一致时，该执行边界才成立
- 更新：
  - Adapter 在执行内消费 bundle，并可返回 `ResourceDispositionHint`
  - `ResourceDispositionHint` 只表达建议，不直接改写共享资源状态
- 失效/归档：
  - 最终 release / invalidate 仍由 Core 基于 `lease_id` 执行
  - 本 FR 不定义 bundle 的持久化存储、长期缓存或 provider 恢复策略
