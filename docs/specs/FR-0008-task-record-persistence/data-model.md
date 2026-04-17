# FR-0008 数据模型

## 实体清单

- 实体：`TaskRecord`
  - 用途：`v0.3.0` 持久化任务记录的聚合根，统一承载状态、终态结果、执行日志与请求快照
- 实体：`TaskRequestSnapshot`
  - 用途：持久化任务在进入执行路径时的共享请求快照，供查询与恢复链路回读
- 实体：`TaskTerminalResult`
  - 用途：承载任务终态时的共享 envelope；其语义继续受既有 Core contract 约束，`envelope.status` 是唯一终态结果状态真相源
- 实体：`TaskLogEntry`
  - 用途：承载 append-only 生命周期日志，表达任务在 admission、执行与收口阶段的最小事件

## 关键字段

- `TaskRecord`
  - `schema_version`
    - 约束：固定为当前任务记录共享 contract 的版本标识；用于反序列化时做 fail-closed 校验
  - `task_id`
    - 约束：非空字符串；是唯一聚合键
  - `request`
    - 约束：必须能回映到 `FR-0004` 的共享请求模型；不得引入平台专属持久化字段
  - `status`
    - 约束：仅允许 `accepted`、`running`、`succeeded`、`failed`
  - `created_at` / `updated_at`
    - 约束：RFC3339 UTC 时间；`updated_at` 必须反映最近一次可信状态变更或日志追加
  - `terminal_at`
    - 约束：仅终态允许出现；非终态不得伪造终态时间
  - `result`
    - 约束：仅 `succeeded` / `failed` 允许出现；且必须与 `status` 保持一致
  - `logs`
    - 约束：append-only 序列；必须覆盖当前状态所要求的生命周期事件。所有任务记录都必须含 `accepted` 事件；进入 `running` 之后必须含开始执行事件；进入终态之后必须含终态收口事件
- `TaskRequestSnapshot`
  - `adapter_key`
    - 约束：非空字符串；复用共享请求语义
  - `capability`
    - 约束：非空字符串；复用共享请求语义
  - `target_type` / `target_value`
    - 约束：必须能回映到共享请求模型，不为持久化查询增加平台私有轴
  - `collection_mode`
    - 约束：复用共享请求模型当前允许值
- `TaskTerminalResult`
  - `envelope`
    - 约束：必须是 JSON-safe；成功态继续复用 success envelope，失败态继续复用 failed envelope
    - 约束：`envelope.status` 只能为 `success` 或 `failed`，并与 `TaskRecord.status` 的终态一致
- `TaskLogEntry`
  - `sequence`
    - 约束：单调递增；用于证明日志顺序可信
  - `occurred_at`
    - 约束：RFC3339 UTC 时间
  - `stage`
    - 约束：只表达共享生命周期阶段，例如 `admission`、`execution`、`persistence`、`completion`
  - `level`
    - 约束：只需满足最小可判定等级；`v0.3.0` 不要求富日志级别体系
  - `code`
    - 约束：可选；用于标识共享失败或关键阶段事件
  - `message`
    - 约束：非空字符串；描述当前日志事件的最小语义

## 生命周期

- 创建：
  - 当任务通过共享 admission、共享 pre-execution 校验、拿到合法 `task_id` 且 `accepted` 记录与请求快照已被可靠序列化/写入时，创建 `TaskRecord`
  - 初始状态固定为 `accepted`
- 更新：
  - 任务进入 adapter 执行阶段时，状态更新为 `running`
  - 一旦任务已经进入 `accepted` 生命周期，后续共享执行主路径上的失败必须把同一条记录收口为 `failed`
  - 任务完成后，状态只能进入 `succeeded` 或 `failed`
  - 每次可信状态迁移都应同步刷新 `updated_at` 并追加对应生命周期日志
- 失效/归档：
  - `v0.3.0` 不要求定义独立归档状态或冷存储流程
  - 非法记录、部分写入记录或反序列化失败记录不得被“就地修补”为合法历史，而应 fail-closed 并由后续实现决定如何恢复或重建
