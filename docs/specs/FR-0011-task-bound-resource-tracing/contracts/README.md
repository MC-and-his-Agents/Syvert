# resource-trace-event contract（v0.4.0）

## 接口名称与版本

- 接口名称：`resource-trace-event`
- contract 版本：`v0.4.0`
- 作用：定义资源状态跟踪与 task-bound 使用日志的最小事件 truth

## 输入输出结构

- 输入结构：
  - 单条 `ResourceTraceEvent`
  - 最小字段：`event_id`、`task_id`、`lease_id`、`bundle_id`、`resource_id`、`resource_type`、`adapter_key`、`capability`、`event_type`、`from_status`、`to_status`、`occurred_at`、`reason`
  - `occurred_at` 必须是 RFC3339 UTC 时间戳，用于保证跨实现的时间线可对齐
- 输出结构：
  - canonical tracing truth：append-only 事件流
  - task-bound usage log：基于同一事件 truth 的最小投影，至少支持按 `task_id`、`resource_id`、`lease_id`、`bundle_id` 重建时间线

## 错误与边界行为

- `invalid_input`
  - 适用场景：
    - 必填字段缺失
    - `event_type` 不是 `acquired`、`released`、`invalidated`
    - `resource_type` 不是 `account`、`proxy`
- `runtime_contract`
  - 适用场景：
    - `from_status / to_status` 不符合 `FR-0010` 已冻结的迁移规则
    - 事件无法回映到明确的 `task_id / lease_id / bundle_id / resource_id`
    - 相同 `event_id` 出现冲突 payload
    - 某次生命周期迁移成功，但 tracing truth 无法同步成立
- 边界约束：
  - tracing truth 必须 append-only，不允许原地改写历史
  - “资源使用日志”是 tracing truth 的投影，不得另建第二套独立 schema
  - 非 task-bound 的库存治理事件不属于本 contract 的最小范围

## 向后兼容约束

- `resource_type`、`from_status`、`to_status` 必须继续复用 `FR-0010` 已批准词汇
- `task_id`、`adapter_key`、`capability` 继续复用上游共享请求语义
- `v0.4.0` 不强制唯一审计后端或唯一查询实现，但 canonical tracing truth 不得漂移
