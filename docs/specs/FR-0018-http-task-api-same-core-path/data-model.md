# FR-0018 数据模型

## 实体清单

- 实体：`HttpTaskSubmitRequest`
  - 用途：表达 HTTP `submit` 的最小 transport ingress 载荷，并投影到既有共享任务请求模型
- 实体：`HttpTaskSubmissionReceipt`
  - 用途：表达任务成功进入 shared durable path 后的最小确认响应
- 实体：`HttpTaskStatusView`
  - 用途：表达 durable `TaskRecord` 当前状态的 HTTP 投影视图
- 实体：`HttpTaskResultView`
  - 用途：表达 durable `TaskRecord` 结果语义的 HTTP 投影视图；终态复用 shared envelope，非终态显式表示结果未就绪

## 关键字段

- `HttpTaskSubmitRequest`
  - `adapter_key`
    - 约束：非空字符串；继续复用共享请求语义
  - `capability`
    - 约束：非空字符串；当前 public 值域固定为调用侧 operation id `content_detail_by_url`
  - `target`
    - 约束：必须能表达当前最小 target 载荷；对当前验证切片，必须可回映为 URL target，并继续投影到共享 `target_type=url`、`target_value=<url>`
- `HttpTaskSubmissionReceipt`
  - `task_id`
    - 约束：非空字符串；必须绑定到同一条 durable `TaskRecord`
  - `status`
    - 约束：表示任务已进入 shared durable path 的当前状态；不得脱离 `TaskRecord.status` 单独创造影子状态轴
- `HttpTaskStatusView`
  - `task_id`
    - 约束：非空字符串；来源于 durable `TaskRecord.task_id`
  - `status`
    - 约束：只允许 `accepted`、`running`、`succeeded`、`failed`；直接复用 `TaskRecord.status`
  - `created_at` / `updated_at`
    - 约束：必须与 durable `TaskRecord` 保持一致
  - `terminal_at`
    - 约束：仅终态允许出现；非终态不得伪造
- `HttpTaskResultView`
  - `task_id`
    - 约束：非空字符串；来源于 durable `TaskRecord.task_id`
  - `record_status`
    - 约束：直接复用 durable `TaskRecord.status`
  - `result_envelope`
    - 约束：仅 `succeeded` / `failed` 允许出现；必须与 durable record 中的终态 envelope 完全一致
    - 约束：success envelope 继续包含 `raw` 与 `normalized`；failed envelope 继续包含 `error`
  - `error`
    - 约束：当结果未就绪、record 不存在或 record 不可用时，继续复用 shared failed envelope 语义；不得引入 API 私有错误 carrier

## 生命周期

- 创建：
  - 当 HTTP `submit` 请求通过共享 ingress/admission 校验，并成功进入 durable `accepted` 生命周期时，形成 `HttpTaskSubmissionReceipt`
- 更新：
  - `HttpTaskStatusView` 与 `HttpTaskResultView` 不拥有独立状态机；它们只投影 durable `TaskRecord` 当前 truth
  - 随 `TaskRecord.status` 从 `accepted -> running -> succeeded|failed` 推进，HTTP status/result 视图同步变化
- 失效/归档：
  - `v0.6.0` 不要求为 HTTP 视图定义独立归档或缓存语义
  - 若 durable `TaskRecord` 不可用、非法或无法安全输出，HTTP 视图必须 fail-closed，而不是被修补成合法响应
