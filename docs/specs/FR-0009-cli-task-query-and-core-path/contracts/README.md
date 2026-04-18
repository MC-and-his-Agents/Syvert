# cli-task-query contract（v0.3.0）

## 接口名称与版本

- 接口名称：`cli-task-query`
- contract 版本：`v0.3.0`
- 作用：定义 CLI `run/query` public surface 与 query 回读 durable `TaskRecord` 的最小边界

## 输入输出结构

- 输入结构：
  - `run` 的固定 public CLI 形状：`python -m syvert.cli run --adapter <adapter_key> --capability <capability> --url <url>`
  - `run` 在 `v0.3.0` 不新增其他必填参数，也不再向更深层子命令扩张
  - `run` 继续接收当前 CLI 执行入口承载的请求载体；其共享语义必须可无损回映到 `FR-0004` / `FR-0008` 已冻结的 `adapter_key`、`capability`、`target_type`、`target_value`、`collection_mode`
  - legacy 平铺入口 `--adapter --capability --url` 的兼容投影固定为 `target_type=url`、`target_value=<url>`、`collection_mode=hybrid`
  - `query` 只接收单个 `task_id`
  - legacy 平铺执行入口继续兼容，并映射到 `run` 语义
- 输出结构：
  - `run` 继续输出共享 success / failed envelope
  - `query` 成功时输出完整共享 `TaskRecord` JSON，即该 durable record 的共享 JSON-safe 序列化载荷
  - `query` 失败时输出 shared failed envelope，不新增 query 私有错误 schema

## 错误与边界行为

- `invalid_cli_arguments`
  - 适用场景：缺少 `--task-id`、出现未知参数、query 子命令参数形状不合法
  - 约束：`error.category=invalid_input`；若 malformed argv 中仍能恢复 `--task-id <id>`，则 failed envelope 必须回显该值；只有查询键缺失、值缺失或不可恢复时，`task_id` 才使用既有共享 CLI 参数错误兜底 `task_id` contract；`adapter_key=""`；`capability=""`
- `task_record_not_found`
  - 适用场景：store 可访问，但请求的 `task_id` 不存在 durable record
  - 约束：`error.category=invalid_input`；回显用户传入的 `task_id`；`adapter_key=""`；`capability=""`
- `task_record_unavailable`
  - 适用场景：store 根目录不可用、invalid marker、记录 JSON 损坏、contract 非法、记录不可读、权限或 IO 异常
  - 约束：`error.category=runtime_contract`；回显用户传入的 `task_id`；`adapter_key=""`；`capability=""`
- 一旦 durable record 已成功加载，后续序列化或 CLI 输出失败时，必须从 `record.request` 回填 `adapter_key` 与 `capability`
- query 不允许读取影子 schema、影子结果文件或 query 私有摘要 payload

## 向后兼容约束

- legacy 平铺执行入口必须继续兼容，不得因 subcommand 改造而失效
- `FR-0009` 只消费 `FR-0008` durable `TaskRecord` contract，不重写状态、结果或日志 schema
- `run` 与 `query` 继续共享同一份 local store 选择 contract：允许沿现有 `SYVERT_TASK_RECORD_STORE_DIR` 环境变量覆盖共享 store 根目录，未覆盖时回退到共享默认本地 store 位置
- `v0.3.0` 不引入 query 专用 store-path CLI flag，不绑定唯一文件布局或唯一目录命名
