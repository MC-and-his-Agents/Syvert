# FR-0011 数据模型

## 实体清单

- 实体：`ResourceTraceEvent`
  - 用途：表达资源状态迁移与 task-bound 占用关系的 canonical append-only 事件
- 实体：`TaskResourceUsageLog`
  - 用途：表达基于 `ResourceTraceEvent` 构建的 task-bound 最小审计投影
- 实体：`ResourceLeaseTimeline`
  - 用途：表达某个 `lease_id` / `bundle_id` 的聚合时间线视图；它只能汇总 `ResourceTraceEvent`，不得替代按 `resource_id` 回放的 canonical 事件时间线

## 关键字段

- `ResourceTraceEvent`
  - `event_id`
    - 约束：非空字符串；是单条 tracing 事件的唯一标识
  - `task_id`
    - 约束：非空字符串；task-bound 事件必须存在
  - `lease_id`
    - 约束：非空字符串；是同一组资源占用关系的聚合键
  - `bundle_id`
    - 约束：非空字符串；必须能回指同次 acquire 的资源包
  - `resource_id`
    - 约束：非空字符串；标识被追踪的具体资源
  - `resource_type`
    - 约束：只允许 `account` 或 `proxy`
  - `adapter_key` / `capability`
    - 约束：复用共享请求上下文，避免 tracing 侧另建影子字段
  - `event_type`
    - 约束：只允许 `acquired`、`released`、`invalidated`
  - `from_status` / `to_status`
    - 约束：必须复用 `FR-0010` 已冻结状态名与允许迁移
  - `occurred_at`
    - 约束：RFC3339 UTC 时间；是时间线判定的最小时间锚点
  - `reason`
    - 约束：非空字符串；对所有事件都必须存在
    - 事件语义：
      - `acquired`：说明资源为何被当前 task 占用；最小 canonical 值允许为 `acquired_for_task`
      - `released`：说明资源为何回收到 `AVAILABLE`
      - `invalidated`：说明资源为何进入 `INVALID`
- `TaskResourceUsageLog`
  - `task_id`
    - 约束：作为投影主键之一，必须可枚举该 task 关联的全部 `ResourceTraceEvent`
  - `events`
    - 约束：来自同一 canonical tracing truth；不得重写或裁剪关键关联字段
- `ResourceLeaseTimeline`
  - `lease_id`
    - 约束：唯一指向某组资源被某个 task 占用的时间线
  - `bundle_id`
    - 约束：必须与同一时间线下的全部事件一致
  - `resource_timelines`
    - 约束：必须按 `resource_id` 汇总该 lease 涉及的全部资源时间线，且不得丢失 per-resource 收口事实
  - `resource_timelines[].acquired_at`
    - 约束：来自对应 `resource_id` 的 `acquired` 事件
  - `resource_timelines[].released_at` / `resource_timelines[].invalidated_at`
    - 约束：二者最多出现其一，用于表达对应 `resource_id` 的收口时间线

## 生命周期

- 创建：
  - 当资源在 task 路径上成功 acquire 时，为每个 `resource_id` 创建一条 `acquired` tracing 事件
- 更新：
  - 当相同 lease 下的资源被正常释放时，为每个 `resource_id` 追加 `released` 事件
  - 当相同 lease 下的资源被判定不可继续复用时，为每个 `resource_id` 追加 `invalidated` 事件
  - 相同 `event_id` 的重复写入仅允许作为完全一致的 no-op
- 失效/归档：
  - 本 FR 不定义 tracing 的归档/压缩/冷热分层策略
  - 缺字段、冲突 payload、非法迁移或无法回映到 task/resource/lease/bundle 的 tracing 事件必须被视为非法 truth 并 fail-closed
