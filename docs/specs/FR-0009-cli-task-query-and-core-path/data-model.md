# FR-0009 数据模型

## 总体说明

- `FR-0009` 不引入新的 durable 数据模型。
- query 读取的唯一 durable truth 仍是 `FR-0008` 已冻结的 `TaskRecord` 聚合。
- `FR-0009` 只补充 CLI public surface 的输入/输出 contract，以及它们与共享 durable truth 的映射关系。

## 共享对象

- `TaskRecord`
  - 来源：`FR-0008`
  - 角色：query 成功时输出的完整 durable 载荷
  - 约束：直接复用 `FR-0008` 已冻结的共享 JSON-safe 序列化形状，不增加 CLI 私有字段，不裁剪请求快照、日志或终态结果
- failed envelope
  - 来源：`FR-0002` / `FR-0005`
  - 角色：query 失败时的 machine-readable 输出
  - 约束：继续复用共享 failed envelope 形状，不创建 query 私有错误 schema

## CLI surface 映射

- `run`
  - public surface：`python -m syvert.cli run --adapter <adapter_key> --capability <capability> --url <url>`
  - public surface 约束：`v0.3.0` 不新增其他必填参数，也不新增更深层执行子命令
  - 输入：当前 CLI 执行入口承载的请求载体；其共享语义必须可回映到 `FR-0004` / `FR-0008` 已冻结的 `adapter_key`、`capability`、`target_type`、`target_value`、`collection_mode`
  - legacy URL 兼容投影：`--adapter --capability --url` 必须固定回映到 `target_type=url`、`target_value=<url>`、`collection_mode=hybrid`
  - 输出：共享 success / failed envelope
  - durable side effect：沿共享 Core / task-record / store 路径创建、推进并持久化 `TaskRecord`
- `query`
  - 输入：单个 `task_id`
  - 成功输出：完整 `TaskRecord` JSON
  - 失败输出：shared failed envelope

## 错误码映射

- `invalid_cli_arguments`
  - 适用：`run` / legacy / `query` 的参数形状错误
  - 输出：`error.code=invalid_cli_arguments`、`error.category=invalid_input` 的 failed envelope
  - `task_id` 语义：
    - `run` / legacy：在参数错误且尚无 durable `task_id` 时，使用新生成的非空 fallback CLI `task_id`
    - `query`：若可恢复用户查询键则回显该值，否则使用新生成的非空 fallback CLI `task_id`
- `task_record_not_found`
  - 适用：store 可访问，但 durable record 不存在
  - 输出：`error.code=task_record_not_found`、`error.category=invalid_input` 的 failed envelope
- `task_record_unavailable`
  - 适用：store 根目录不可用、invalid marker、记录 JSON 损坏、contract 非法、记录不可读、权限或 IO 异常
  - 输出：`error.code=task_record_unavailable`、`error.category=runtime_contract` 的 failed envelope
