# FR-0008 Task record persistence contract

## 关联信息

- item_key：`FR-0008-task-record-persistence`
- Issue：`#127`
- item_type：`FR`
- release：`v0.3.0`
- sprint：`2026-S16`

## 背景与目标

- 背景：`v0.2.0` 已证明同一条 Core 主路径可以统一运行真实参考适配器并输出共享 success / failed envelope，但当前结果仍停留在单次进程输出层；进程结束后，任务状态、最终结果与执行日志没有稳定的持久化真相，后续 CLI 查询也缺少可复用的共享基线。
- 目标：为 `v0.3.0` 冻结最小任务记录与本地持久化 formal contract，明确任务状态模型、终态结果、执行日志、共享序列化与本地持久化边界，使后续实现 Work Item 可以在不改写 requirement 的前提下把“执行一次任务”收口为“产生可查询、可回读、可追溯的持久化任务记录”。

## 范围

- 本次纳入：
  - 冻结 `v0.3.0` 最小任务记录聚合根的共享语义
  - 冻结任务状态、终态结果与执行日志的最小共享模型
  - 冻结共享任务/结果序列化与本地稳定存储之间的边界
  - 冻结“持久化必须经由 Core 内部机制，而不是由 CLI 或外部调用方旁路写入”的约束
  - 冻结 `FR-0008` 与 `FR-0009` 的边界：前者负责持久化与共享模型，后者负责查询入口与同路径执行闭环
- 本次不纳入：
  - CLI 查询命令、输出格式或筛选能力
  - HTTP API、远程服务端点或多进程调度
  - 分布式工作队列、重试编排、取消/暂停/恢复等高级任务控制
  - 丰富查询层、二级索引、统计报表或资源系统
  - `FR-0002`、`FR-0004`、`FR-0005` 已冻结的共享 envelope / 输入模型 / 错误模型语义改写

## 需求说明

- 功能需求：
  - `v0.3.0` 范围内，每个已经通过共享 admission 与共享 pre-execution 校验、并正式进入 adapter 执行主路径的任务都必须生成且只生成一条持久化任务记录；该记录以 `task_id` 作为唯一聚合键。
  - `accepted` 任务记录与请求快照的 durable 创建，是进入 adapter 执行前的前置条件；如果初始建档或请求快照序列化/写入失败，执行必须在 adapter 调用前 fail-closed。
  - 任务记录必须覆盖同一条执行主路径上的三个共享面：任务状态、终态结果、执行日志。后续实现可以拆成多个模块，但不能让这三类信息脱离同一个聚合根。
  - 任务状态模型在 `v0.3.0` 的最小闭环固定为：`accepted -> running -> succeeded | failed`。`accepted` 表示任务已通过共享 admission 与共享 pre-execution 校验、完成初始建档并进入持久化轨道；`running` 表示任务已进入 adapter 执行阶段；`succeeded` / `failed` 是唯一允许的终态。
  - 任务状态迁移必须单向闭合；`succeeded` 与 `failed` 一旦写入，即不得在同一条任务记录上回退为非终态，也不得再追加第二个终态。
  - 终态结果必须复用同一条 Core 执行主路径产生的共享 envelope 语义：成功态继续承载 `task_id`、`adapter_key`、`capability`、`status=success`、`raw`、`normalized`；失败态继续承载 `task_id`、`adapter_key`、`capability`、`status=failed`、`error`。持久化层不得重新定义一套独立结果 schema。
  - 一旦任务已经进入 `accepted` 生命周期，此后同一条 adapter 执行主路径上的失败都必须收口为 durable `failed` 任务记录；这至少包括 adapter 执行失败、adapter 返回 payload 校验失败，以及终态结果/状态/日志的持久化失败。
  - 执行日志必须与同一条任务记录共存，并至少表达该任务实际经历过的生命周期事件。所有任务记录都必须包含 `accepted` 事件；进入 `running` 之后必须包含执行开始事件；进入终态之后必须包含终态收口事件。`v0.3.0` 只要求最小共享日志结构，不要求富文本日志流、实时订阅或平台专属调试输出。
  - 共享序列化必须以同一份任务记录聚合为输入，输出 JSON-safe 的稳定表示；写入与回读都必须围绕这同一份共享表示进行，而不是由不同调用方分别维护私有序列化形状。
  - 本地稳定存储是 `v0.3.0` 的唯一持久化目标态；formal spec 允许文件、目录或嵌入式存储等不同实现，但不允许把唯一合法实现绑定到某个具体文件名、某个目录布局或某个存储引擎。
  - `FR-0009` 后续可以基于该持久化任务记录提供 CLI 查询，但不得引入与本 FR 不一致的第二套状态/结果/日志语义。
- 契约需求：
  - 任务记录聚合至少必须包含：`task_id`、请求快照、当前任务状态、创建/更新时间、执行日志集合，以及在终态时可回读的结果 envelope。
  - 请求快照必须围绕 `FR-0004` 已批准的共享请求模型表达，即可回映到 `adapter_key`、`capability`、`target_type`、`target_value` 与 `collection_mode`；不得为单一平台新增持久化专用字段。
  - 终态结果与任务状态必须保持一致：`succeeded` 只能对应成功 envelope，`failed` 只能对应失败 envelope；非终态任务记录不得伪装出终态 envelope。
  - 执行日志必须是 append-only 语义；每条日志至少要可追溯到发生时间、生命周期阶段与最小可判定消息。`raw` payload、平台私有细节或完整栈信息不是日志模型的必需字段。
  - 序列化与反序列化必须以同一份共享 contract 为准；缺失必需字段、字段类型不合法、终态/结果不一致、缺少当前状态所要求的生命周期事件，或日志序列不可信，都必须被判定为非法持久化记录并 fail-closed。
  - 持久化写入必须通过 Core 内部任务记录机制完成。CLI、adapter 或外部调用方不得绕过 Core 直接落盘“结果文件”来伪装任务已被持久化。
  - 如果终态结果、状态更新或必需日志无法被可靠序列化或可靠写入，本次执行必须 fail-closed；不得继续把该任务报告为“已成功且可查询”的持久化完成态。
  - 查询消费者只能消费已经持久化完成的共享任务记录；formal spec 不允许为查询层维护与任务记录不一致的影子状态表或影子结果 payload。
- 非功能需求：
  - 任务记录必须可被后续 CLI 查询稳定回读，并能区分任务当前状态、终态结果与执行日志三个维度。
  - 持久化 contract 必须保持实现无关，允许本地单进程执行与后续更丰富入口共用同一共享模型。
  - 任务记录必须保持 JSON-safe，避免在本地持久化层留下不可序列化或无法回读的中间对象。
  - 任何持久化异常都必须优先暴露一致性问题，而不是静默降级为“只在 stdout/stderr 输出、但无 durable truth”。

## 约束

- 阶段约束：
  - 本事项只服务 `v0.3.0`“最小任务与结果持久化闭环”，不提前展开 `v0.4.0` 资源系统、`v0.7.0` 服务面或更高阶调度语义。
  - 本事项只冻结任务记录与持久化 contract，不提前定义 `FR-0009` 的查询命令参数、展示格式或 UX 细节。
- 架构约束：
  - Core 负责共享任务记录、状态迁移、序列化与持久化边界；adapter 继续只负责平台语义与平台 payload，不得把平台私有字段注入共享持久化模型。
  - formal spec 与实现 PR 默认分离；当前 formal spec PR 不混入 `syvert/`、`tests/`、`scripts/` 下的实现改动。
  - 终态结果仍受 `FR-0002`、`FR-0004`、`FR-0005` 已批准 contract 约束；`FR-0008` 只能复用这些共享语义，不得在持久化层重定义另一套 success / failed 结果格式。

## GWT 验收场景

### 场景 1

Given 一个请求已经通过共享 admission、获得合法 `task_id` 并准备进入执行  
When `v0.3.0` 的任务记录机制接管该任务  
Then 必须创建一条同 `task_id` 绑定的任务记录，并以 `accepted` 作为最早可持久化状态，而不是等任务结束后才补造结果文件

### 场景 2

Given 一个任务已经进入 adapter 执行阶段  
When 该任务成功完成  
Then 同一条任务记录必须转入 `succeeded`，并保存与 Core success envelope 语义一致的终态结果，同时保留最小生命周期日志

### 场景 3

Given 一个任务已经通过共享 admission 并在 adapter 执行、共享 payload 校验或终态持久化收口阶段失败
When 该任务结束
Then 同一条任务记录必须转入 `failed`，并保存与 Core failed envelope 语义一致的终态结果，而不是只在日志中留下失败痕迹

### 场景 4

Given 终态结果、状态迁移或必需日志无法被可靠序列化或可靠写入稳定存储  
When 任务试图以“持久化完成”状态结束  
Then 该次执行必须 fail-closed，不能对外宣称任务已经以 durable success 方式收口

### 场景 5

Given 后续 CLI 查询或其他消费者需要读取历史任务  
When 它们消费 `FR-0008` 的持久化结果  
Then 它们必须读取同一份共享任务记录表示，而不是各自维护一套影子状态、影子结果或 CLI 私有 schema

### 场景 6

Given 一个持久化任务记录缺失必需字段、终态与结果不一致，或日志序列无法证明其可信性  
When 查询消费者或恢复流程尝试回读该记录  
Then 该记录必须被判定为非法并 fail-closed，而不是被宽松修复成看似合法的任务历史

## 异常与边界场景

- 异常场景：
  - 若任务记录只持久化最终结果，不持久化共享任务状态或生命周期日志，则不满足 `v0.3.0` 的闭环目标。
  - 若持久化层允许 `succeeded` 任务缺少 success envelope，或允许 `failed` 任务缺少 failure envelope，则任务状态与结果语义已经断裂。
  - 若系统允许任务在 `accepted` 初始建档失败后继续执行，并打算事后补写历史，则违反 durable truth 自 `accepted` 开始的 contract。
  - 若外部调用方可以绕过 Core 直接写入查询结果文件，formal spec 必须把该路径视为旁路持久化，不能算作 `FR-0008` 的实现。
  - 若持久化写入失败后系统仍然把任务作为“已成功且可查询”对外暴露，则违反 fail-closed 要求。
- 边界场景：
  - 共享 admission 拒绝、CLI 参数解析失败，或其他发生在 durable `accepted` 建档之前的失败，不属于 `FR-0008` 要求持久化的 `TaskRecord` 生命周期；它们继续只产生共享 failed envelope，而不强制落入 durable task history。
  - 这类 pre-`accepted` 失败至少包括 `FR-0004` 已冻结的共享 admission 失败，以及 `FR-0005` 已冻结的 shared pre-execution 失败，例如 unsupported capability、unsupported `target_type` / `collection_mode`、registry / declaration 失败等。
  - `FR-0008` 不要求在 `v0.3.0` 支持任务取消、重试、恢复、并发锁或分布式队列；这些不在最小状态机内。
  - `FR-0008` 不要求定义唯一的本地文件布局或数据库 schema，只要求共享序列化与稳定存储之间的契约边界保持一致。
  - `FR-0008` 可以为 `FR-0009` 提供可查询基线，但不负责定义 CLI 查询入口的参数、排序、筛选和展示细节。
  - 平台原始 payload 继续允许作为 success envelope 的 `raw` 一部分被持久化，但不要求把平台私有调试细节复制进共享执行日志。

## 验收标准

- [ ] formal spec 明确冻结 `accepted -> running -> succeeded | failed` 的最小任务状态模型
- [ ] formal spec 明确要求终态结果复用同一条 Core success / failed envelope 语义，而不是新建影子 schema
- [ ] formal spec 明确要求任务状态、终态结果与执行日志围绕同一条持久化任务记录聚合
- [ ] formal spec 明确要求共享序列化与反序列化消费同一份任务记录 contract，并对非法记录 fail-closed
- [ ] formal spec 明确要求持久化必须经由 Core 内部机制，禁止 CLI / adapter / 外部调用方旁路落盘
- [ ] formal spec 明确把 `FR-0009` 的 CLI 查询 surface 留在相邻 FR，而不是混入本 FR

## 依赖与外部前提

- 外部依赖：
  - `#126` 作为 `v0.3.0` 阶段事项已在 GitHub 建立
  - `#127` 作为本 FR 的 canonical requirement 容器已建立，并绑定 `#137/#138/#139/#140`
  - `FR-0002`、`FR-0004`、`FR-0005` 已分别冻结共享结果 envelope、请求模型与错误/registry 语义，`FR-0008` 只在其上复用而不改写
- 上下游影响：
  - `#138` 将据此落地共享任务状态/结果/日志模型
  - `#139` 将据此落地本地持久化与共享序列化管线
  - `#141/#142/#143` 所属的 `FR-0009` 将消费本 FR 冻结的持久化任务记录 contract 来提供 CLI 查询与同路径执行闭环
