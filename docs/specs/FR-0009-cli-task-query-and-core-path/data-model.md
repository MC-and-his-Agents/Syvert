# FR-0009 数据模型

## 总体说明

- `FR-0009` 不引入新的 durable 数据模型。
- query 读取的唯一 durable truth 仍是 `FR-0008` 已冻结的 `TaskRecord` 聚合。
- `FR-0009` 只补充 CLI public surface 的输入/输出 contract，以及它们与共享 durable truth 的映射关系。

## 共享对象

- `TaskRecord`
  - 来源：`FR-0008`
  - 角色：query 成功时输出的完整 durable 载荷
  - 约束：直接复用共享 `task_record_to_dict(record)` 形状，不增加 CLI 私有字段，不裁剪请求快照、日志或终态结果
- failed envelope
  - 来源：`FR-0002` / `FR-0005`
  - 角色：query 失败时的 machine-readable 输出
  - 约束：继续复用共享 failed envelope 形状，不创建 query 私有错误 schema

## CLI surface 映射

- `run`
  - 输入：`adapter_key`、`capability`、`url`
  - 输出：共享 success / failed envelope
  - durable side effect：沿共享 Core / task-record / store 路径创建、推进并持久化 `TaskRecord`
- `query`
  - 输入：单个 `task_id`
  - 成功输出：完整 `TaskRecord` JSON
  - 失败输出：shared failed envelope

## 错误码映射

- `invalid_cli_arguments`
  - 适用：缺少 `--task-id`、未知参数、query 子命令参数形状不合法
  - 输出：failed envelope
- `task_record_not_found`
  - 适用：store 可访问，但 durable record 不存在
  - 输出：failed envelope
- `task_record_unavailable`
  - 适用：store 根目录不可用、invalid marker、记录 JSON 损坏、contract 非法、记录不可读、权限或 IO 异常
  - 输出：failed envelope
