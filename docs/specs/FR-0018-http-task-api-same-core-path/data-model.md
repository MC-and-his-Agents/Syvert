# FR-0018 数据模型

## 实体清单

- 实体：`HttpTaskSubmitRequest`
  - 用途：表达 HTTP `submit` 的最小 transport ingress 载荷，并投影到既有共享任务请求模型
- 实体：`HttpTaskSubmissionReceipt`
  - 用途：表达任务成功进入 shared durable path 后的最小确认响应
- 实体：`HttpTaskStatusView`
  - 用途：表达 durable `TaskRecord` 当前状态的 HTTP 投影视图
- 实体：`HttpTaskResultView`
  - 用途：表达 HTTP `result` endpoint 的共享结果语义别名；它不是新的顶层包裹 schema，响应体本身必须直接等于共享 envelope

## 关键字段

- `HttpTaskSubmitRequest`
  - `adapter_key`
    - 约束：非空字符串；继续复用共享请求语义
  - `capability`
    - 约束：非空字符串；当前 public 值域固定且仅允许 `content_detail_by_url`
  - `target`
    - 约束：必须能表达当前最小 target 载荷；对当前验证切片，必须可回映为 URL target，并继续投影到共享 `target_type=url`、`target_value=<url>`
  - `execution_control_policy`
    - 约束：可选对象；若出现，只允许表达共享 `ExecutionControlPolicy` 已批准字段，不得携带 transport 私有成员
    - 约束：若缺失，则由共享 Core path 选择默认策略；HTTP 不得补写 transport 私有默认值
    - 约束：若形状非法、无法投影到共享 contract，或与共享 idempotency safety gate 前提冲突，则 `submit` 必须在 durable `accepted` 之前 fail-closed
- `HttpTaskSubmissionReceipt`
  - `task_id`
    - 约束：非空字符串；必须绑定到同一条 durable `TaskRecord`
  - `status`
    - 约束：表示任务已进入 shared durable path 的当前状态；不得脱离 `TaskRecord.status` 单独创造影子状态轴
  - `accepted_at`
    - 约束：可选时间戳；若返回，必须可回映到 durable `accepted` 生命周期已成立，而不是仅表示 ingress 已接收
- `HttpTaskStatusView`
  - `task_id`
    - 约束：非空字符串；来源于 durable `TaskRecord.task_id`
  - `status`
    - 约束：只允许 `accepted`、`running`、`succeeded`、`failed`；直接复用 `TaskRecord.status`
  - `created_at` / `updated_at`
    - 约束：必须与 durable `TaskRecord` 保持一致
  - `terminal_at`
    - 约束：仅终态允许出现；非终态不得伪造
  - `runtime_result_refs`
    - 约束：可选数组；若 durable record 或共享结果已记录相关 ref，HTTP status 视图不得裁剪或改名这些引用
  - `execution_control_events`
    - 约束：可选投影视图；若共享路径已把控制结果固化为 `ExecutionControlEvent`，HTTP 只能透传其共享事实，不得改写为 transport 私有状态机
- `HttpTaskResultView`
  - 响应体
    - 约束：必须直接等于共享 envelope，而不是 `{task_id, record_status, result_envelope}` 形式的 transport 包裹对象
    - 约束：当 `TaskRecord.status=succeeded` 时，响应体必须与 durable record 中的 success envelope 完全一致，并继续包含共享字段 `raw` 与 `normalized`
    - 约束：当 `TaskRecord.status=failed` 时，响应体必须与 durable record 中的 failed envelope 完全一致，并继续包含共享 `error`
    - 约束：当 `TaskRecord.status=accepted|running` 时，响应体必须固定为 `result_not_ready` / `invalid_input` 的 shared failed envelope
    - 约束：若 `task_id` 对应 durable record 不存在，响应体必须固定为 `task_record_not_found` / `invalid_input` 的 shared failed envelope
    - 约束：若 `task_id` 形状非法或不满足共享任务键 contract，响应体必须固定为 `invalid_task_id` / `runtime_contract` 的 shared failed envelope
    - 约束：若 store、record contract、closeout/control-state truth 或共享序列化不可信，响应体必须固定为 `task_record_unavailable` / `runtime_contract` 的 shared failed envelope
    - 约束：若失败由控制面 `execution_timeout` 收口，必须保留 `error.category=platform` 与 `error.details.control_code=execution_timeout`
    - 约束：若失败属于 closeout/control-state truth 失效，必须保留 `runtime_contract` 分类
    - 约束：post-accepted retry reacquire rejection 不得借由 HTTP result 改写上一已完成 attempt 的终态 `error.code` / `error.category`
    - 约束：若共享 envelope 已持有 `runtime_result_refs`，HTTP result 响应体必须原样保留这些 ref
    - 约束：retryable predicate 不是整个 `platform` category；只有 `execution_timeout` 控制结果，或 `error.category=platform` 且 `error.details.retryable=true` 的瞬态失败，才允许进入共享 retry 判定

## 生命周期

- 创建：
  - 当 HTTP `submit` 请求通过共享 ingress/admission 校验，并成功进入 durable `accepted` 生命周期时，形成 `HttpTaskSubmissionReceipt`
  - 若请求在 durable `accepted` 之前因并发门禁被拒绝，该失败必须投影为 `invalid_input`，且不得创建 durable `TaskRecord`
- 更新：
  - `HttpTaskStatusView` 与 `HttpTaskResultView` 不拥有独立状态机；它们只投影 durable `TaskRecord` 当前 truth
  - 随 `TaskRecord.status` 从 `accepted -> running -> succeeded|failed` 推进，HTTP status/result 视图同步变化
  - 若共享执行路径追加 `ExecutionControlEvent`、结构化控制结果或 `runtime_result_refs`，HTTP 视图只能继续透传这些共享事实，不得改写为 HTTP 私有观测模型
  - 若 post-accepted retry 阶段发生 reacquire rejection，且上一 attempt 已有已完成终态，则该 rejection 只允许写入 `ExecutionControlEvent` / `details` / `runtime_result_refs` 等控制事实，不得覆盖既有终态 envelope
- 失效/归档：
  - `v0.6.0` 不要求为 HTTP 视图定义独立归档或缓存语义
  - 若 durable `TaskRecord`、closeout/control-state truth、结果引用或共享序列化任一环节不可信，HTTP 视图必须 fail-closed，而不是被修补成合法响应
