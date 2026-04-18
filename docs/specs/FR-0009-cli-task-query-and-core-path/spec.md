# FR-0009 CLI task query and core path

## 关联信息

- item_key：`FR-0009-cli-task-query-and-core-path`
- Issue：`#128`
- item_type：`FR`
- release：`v0.3.0`
- sprint：`2026-S16`

## 背景与目标

- 背景：`FR-0008` 已冻结 `TaskRecord` 聚合、共享序列化与本地持久化 contract，但当前 CLI 仍只有“提交并立即执行”入口，缺少按 `task_id` 回读 durable history 的最小 public surface，也尚未明确查询是否必须继续围绕同一条 Core / task-record / store 路径工作。
- 目标：为 `v0.3.0` 冻结 CLI 查询任务记录与同路径执行闭环的 formal contract，明确 `run/query` public surface、legacy 平铺执行入口兼容边界、query 成功/失败输出语义，以及查询只能消费共享 `TaskRecord` durable truth 的约束。

## 范围

- 本次纳入：
  - 冻结按 `task_id` 查询单条 durable `TaskRecord` 的最小 CLI public surface
  - 冻结 `run` / `query` 顶层子命令与 legacy 平铺执行入口之间的兼容边界
  - 冻结 query 成功输出完整共享 `TaskRecord` JSON、失败时复用 shared failed envelope 的 contract
  - 冻结 query 对 `task_record_not_found` / `task_record_unavailable` / `invalid_cli_arguments` 的最小错误语义
  - 冻结 CLI 提交、执行、持久化、查询继续围绕同一条 Core / task-record / store 路径工作的约束
- 本次不纳入：
  - 列表查询、筛选、排序、分页、摘要视图
  - HTTP API、远程查询服务、多进程调度或资源系统
  - `FR-0008` 已冻结的状态机、终态 envelope、日志 contract 语义改写
  - 新的 store 选择 CLI flag、第二套查询 schema 或第二套持久化布局

## 需求说明

- 功能需求：
  - CLI 顶层必须提供两个 public subcommand：`run` 与 `query`。
  - `run` 语义必须等价于当前执行入口：继续承接当前 CLI 执行入口暴露的请求载体，并把它投影到 `FR-0004` / `FR-0008` 已冻结的共享请求模型，再沿同一条 Core 执行路径完成 admission、adapter 执行、`TaskRecord` durable 写入与终态输出。
  - legacy 平铺执行入口 `python -m syvert.cli --adapter ... --capability ... --url ...` 必须继续兼容，并映射到 `run` 语义；引入 subcommand 后不得破坏当前 parse failure 的 machine-readable 行为。
  - `query` 的最小 public surface 固定为 `python -m syvert.cli query --task-id <id>`；`v0.3.0` 不额外提供列表查询、筛选或摘要模式。
  - `query` 成功时必须把同一份 durable `TaskRecord` 的完整共享 JSON-safe 表示写到 `stdout`；该输出必须与 `FR-0008` 已冻结的共享序列化 contract 一致，不得裁剪请求快照、执行日志或终态 envelope，也不得增加 CLI 私有字段。
  - `query` 必须允许回读任意合法 durable `TaskRecord`，不限终态；`accepted`、`running`、`succeeded`、`failed` 都必须可查询。
  - `query` 失败时必须输出 machine-readable shared failed envelope 到 `stderr`，并维持返回码非零。
  - `query` 与 `run` 必须继续消费同一份共享 local store truth，并沿当前共享 store 选择 contract 工作；`v0.3.0` 不得引入 query 专用文件、影子状态表、影子结果 payload 或 query 专用 store 选择入口。
- 契约需求：
  - `query` 成功输出的 JSON 形状必须与共享 `TaskRecord` contract 一致，即该 durable record 的完整共享 JSON-safe 序列化载荷。
  - `query` 缺少 `--task-id`、携带未知参数或子命令参数形状不合法时：
    - `error.code` 固定为 `invalid_cli_arguments`
    - `error.category` 固定为 `invalid_input`
    - `task_id` 由 `resolve_task_id(task_id_factory)` 生成或注入，沿用当前 parse-failure 兜底语义
    - `adapter_key=""`
    - `capability=""`
  - `query` 的 `task_id` 不存在 durable record 时：
    - `error.code` 固定为 `task_record_not_found`
    - `error.category` 固定为 `invalid_input`
    - `task_id` 必须回显用户请求的 `task_id`
    - `adapter_key=""`
    - `capability=""`
  - store 根目录不可用、invalid marker、JSON 损坏、contract 非法、记录不可读、权限或 IO 异常时：
    - `error.code` 固定为 `task_record_unavailable`
    - `error.category` 固定为 `runtime_contract`
    - `task_id` 必须回显用户请求的 `task_id`
    - `adapter_key=""`
    - `capability=""`
  - 一旦 durable record 已成功加载，后续若在共享序列化或 CLI 输出阶段仍需构造 failed envelope，`adapter_key` 与 `capability` 必须回填自 `record.request`，不得继续留空。
  - `query` 不得通过重新拼装 success/failed envelope、单独读取结果文件，或维护第二套查询 schema 来伪造任务历史。
- 非功能需求：
  - query 读取 durable record 时必须 fail-closed；任何无法证明为合法共享 `TaskRecord` 的历史都不得被宽松修复后继续输出。
  - `run` 与 legacy 平铺入口在同一输入语义下必须先投影到同一份共享请求模型，再写入等价的 durable truth；不得分叉为两条不同路径或两套请求 contract。
  - `v0.3.0` 的 query contract 必须保持实现无关，不绑定唯一文件布局、唯一目录命名或唯一嵌入式存储引擎。

## 约束

- 阶段约束：
  - 本事项只服务 `v0.3.0` 的“CLI 查询任务状态/结果 + CLI 仍走同一条 Core 执行路径”目标，不提前展开丰富查询层或服务面。
  - 本事项不重写 `FR-0008` 已冻结的 durable `TaskRecord` schema，只定义 CLI 如何消费它。
- 架构约束：
  - Core 继续负责共享请求、执行、终态 envelope、`TaskRecord` 与 store boundary；CLI 只暴露入口，不得拥有私有 durable truth。
  - formal spec 与实现 PR 必须分离；`#141` 只冻结 formal contract，不混入 `syvert/**` 与 `tests/**` 实现改动。
  - `#142` 只收口 CLI query public surface；`#143` 只收口 run/query 同路径闭环与端到端证据；二者不得各自扩张 requirement。

## GWT 验收场景

### 场景 1

Given 某个 `task_id` 对应的 durable `TaskRecord` 已存在  
When 用户执行 `python -m syvert.cli query --task-id <id>`  
Then CLI 必须把完整共享 `TaskRecord` JSON 输出到 `stdout`，而不是输出 CLI 私有摘要视图

### 场景 2

Given 某个 durable `TaskRecord` 当前状态为 `accepted`、`running`、`succeeded` 或 `failed`  
When 用户执行同一条 `query` 命令  
Then CLI 都必须能够回读并输出该记录，而不是只允许终态记录被查询

### 场景 3

Given 用户仍使用 legacy 平铺执行入口 `--adapter --capability --url`  
When CLI 运行任务  
Then 该入口必须继续兼容，并沿与 `run` 子命令等价的 Core / task-record / store 路径执行

### 场景 4

Given `query` 参数缺失 `--task-id`、出现未知参数或子命令参数形状不合法  
When CLI 构造失败输出  
Then 它必须返回 `invalid_cli_arguments` failed envelope，并继续使用 parse-failure 的 `task_id` 兜底语义

### 场景 5

Given `query` 请求的 `task_id` 不存在 durable record  
When store 能被正常访问  
Then CLI 必须返回 `task_record_not_found` failed envelope，而不是把“不存在”误报为 store 不可用

### 场景 6

Given store 根目录不可用、invalid marker 存在、记录 JSON 损坏、contract 非法或记录不可读  
When `query` 试图回读该 `task_id`  
Then CLI 必须返回 `task_record_unavailable` failed envelope，并拒绝输出看似合法的任务历史

## 异常与边界场景

- 异常场景：
  - 若 `query` 通过读取第二套结果文件、CLI 私有摘要文件或影子状态表返回历史，则违反同路径 contract。
  - 若 `query` 成功加载 durable record 后仍丢弃 `record.request.adapter_key` / `capability`，则会破坏失败输出的可追溯性。
  - 若 subcommand 改造导致 legacy 平铺执行入口不再保留当前 parse-failure 行为，则构成回归。
- 边界场景：
  - 本事项只要求按单个 `task_id` 查询；不要求在 `v0.3.0` 提供列表、筛选或分页。
  - durable record 的存在与否只针对共享 store truth；CLI 不维护额外缓存或索引层。
  - `query` 可读取非终态记录，但不得为非终态记录伪造终态摘要。

## 验收标准

- [ ] formal spec 明确冻结 `run` / `query` public surface 与 legacy 平铺执行入口兼容边界
- [ ] formal spec 明确要求 `query` 成功输出完整共享 `TaskRecord` JSON，而不是 CLI 私有 schema
- [ ] formal spec 明确允许 `query` 回读任意合法 durable `TaskRecord`，不限终态
- [ ] formal spec 明确冻结 `invalid_cli_arguments`、`task_record_not_found`、`task_record_unavailable` 的最小错误 contract
- [ ] formal spec 明确要求 `run/query` 继续消费同一条 Core / task-record / store truth，禁止影子 schema 或旁路路径

## 依赖与外部前提

- 外部依赖：
  - `#126` 作为 `v0.3.0` 阶段事项已建立
  - `#128` 作为本 FR 的 canonical requirement 容器已建立，并绑定 `#141/#142/#143/#144`
  - `FR-0008` 已冻结 `TaskRecord`、共享序列化、本地持久化与 fail-closed 回读 contract
- 上下游影响：
  - `#141` 将据此冻结 formal spec 套件
  - `#142` 将据此实现 CLI `query` surface 与 `run/query` 顶层解析
  - `#143` 将据此完成 run/query 同路径闭环与端到端验证
  - `#144` 将据此把 release / sprint / exec-plan / GitHub 关闭语义收口到同一条证据链
