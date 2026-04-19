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

## 关键字段

- `ResourceRecord`
  - `resource_id`
    - 约束：非空字符串；是资源唯一标识
  - `resource_type`
    - 约束：在 `v0.4.0` 只允许 `account` 或 `proxy`
  - `status`
    - 约束：只允许 `AVAILABLE`、`IN_USE`、`INVALID`
  - `material`
    - 约束：JSON-safe 的不透明 payload；允许承载类型专属执行材料，但不得改写共享顶层字段命名
- `AccountResource`
  - `account_key`
    - 约束：非空字符串；用于表达账号资源的稳定引用
- `ProxyResource`
  - `proxy_key`
    - 约束：非空字符串；用于表达代理资源的稳定引用
- `ResourceBundle`
  - `bundle_id`
    - 约束：非空字符串；用于标识本次成功 acquire 的 bundle
  - `lease_id`
    - 约束：非空字符串；必须与同次 acquire 建立的 `ResourceLease` 一一对应
  - `task_id` / `adapter_key` / `capability`
    - 约束：复用共享请求上下文，不再创建第二套 task 关联字段
  - `requested_slots`
    - 约束：只允许 `account`、`proxy`；成功时 bundle 中的已声明 slot 必须全部被填充
  - `account` / `proxy`
    - 约束：对应 slot 若被请求，则成功 bundle 中必须存在且其 `status=IN_USE`
- `ResourceLease`
  - `lease_id`
    - 约束：唯一、非空；是占用关系的唯一标识
  - `bundle_id`
    - 约束：必须回指同次 acquire 产生的 `ResourceBundle`
  - `task_id`
    - 约束：非空字符串；lease 只属于单个 task
  - `resource_ids`
    - 约束：必须与 bundle 中实际承载的资源集合一致
  - `acquired_at`
    - 约束：RFC3339 UTC 时间；仅 acquire 成功后出现
  - `released_at`
    - 约束：仅 release 成功后出现
  - `target_status_after_release`
    - 约束：只允许 `AVAILABLE` 或 `INVALID`

## 生命周期

- 创建：
  - 当 `acquire` 请求形状合法、全部 `requested_slots` 都绑定到 `AVAILABLE` 资源、且 `ResourceBundle` 与 `ResourceLease` 已可靠建立时，创建新的占用关系
  - 创建成功后，bundle 中全部资源状态必须同步推进为 `IN_USE`
- 更新：
  - `release(target_status_after_release=AVAILABLE)` 成功后，lease 绑定资源从 `IN_USE` 回到 `AVAILABLE`
  - `release(target_status_after_release=INVALID)` 成功后，lease 绑定资源从 `IN_USE` 进入 `INVALID`
  - 相同语义的重复 `release` 只允许作为 idempotent no-op；冲突性重复 release 必须 fail-closed
- 失效/归档：
  - `INVALID` 在 `v0.4.0` 视为终态；本 FR 不定义从 `INVALID` 回到 `AVAILABLE` 的恢复语义
  - 失败 acquire 不得生成半完成 lease；失败 release 不得留下伪装成已释放的影子 truth
