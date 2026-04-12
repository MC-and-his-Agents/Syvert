# FR-0004 v0.2.0 InputTarget and CollectionPolicy

## 关联信息

- item_key：`FR-0004-input-target-and-collection-policy`
- Issue：`#64`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`

## 背景与目标

- 背景：`FR-0002` 已冻结 `content_detail_by_url` 的最小运行时契约，但当前 Core 仍缺少可复用的“输入目标”与“采集策略”抽象，导致后续能力扩展容易把 URL 派生字段、认证资源前置或平台特定策略直接塞回 Core。
- 目标：为 `v0.2.0` 正式定义 `InputTarget` 与 `CollectionPolicy` 两个共享模型，冻结它们在 Core / Adapter 契约中的职责边界、输入输出语义与扩展边界，使后续实现、假适配器、registry、harness 与回归 gate 都围绕同一组 formal spec 语义推进。

## 范围

- 本次纳入：
  - 定义 `InputTarget` 的最小字段与语义
  - 定义 `CollectionPolicy` 的最小字段与语义
  - 定义二者与 Core / Adapter 契约的职责边界
  - 定义二者如何约束输入、采集范围、执行前校验与后续扩展
  - 定义二者与 `FR-0002` 既有 Core 契约的兼容关系
- 本次不纳入：
  - 标准化错误模型
  - adapter registry / capability discovery 机制
  - fake adapter、adapter harness 与版本回归 gate
  - 平台泄漏检查 gate 的具体实现
  - 平台特定 ID、签名、headers、cookie、token、指纹或 fallback 路径设计
  - 任何实现代码、脚本、测试或运行时改造

## 需求说明

- 功能需求：
  - Core 面向“发起一次采集”时，必须能够显式接收一个 `InputTarget` 与一个 `CollectionPolicy`。
  - `InputTarget` 只描述“采什么”，不得混入资源分配、平台签名或执行调度细节。
  - `CollectionPolicy` 只描述“在什么约束下采”，不得退化为平台请求构造脚本或 adapter 内部状态机。
  - adapter 必须显式声明自己支持的 `target_type` 集合与 `collection_mode` 集合；不支持的轴值必须在进入平台执行前被拒绝。
  - Core 必须以 `InputTarget` 与 `CollectionPolicy` 作为共享输入层受理请求，并在进入 adapter 前把它们投影到 adapter-facing contract；不得把平台派生字段提前展开到 Core 层。
- 契约需求：
  - `InputTarget` 的最小字段固定为：`adapter_key`、`capability`、`target_type`、`target_value`。
  - `adapter_key` 表示本次采集绑定的 adapter 路由标识，类型固定为非空字符串；它属于 Core 侧路由输入，不要求作为 adapter-facing request 的必需字段进入 `AdapterRequest`。
  - `capability` 表示本次采集请求的调用侧 operation 标识，类型固定为非空字符串；能力目录本身不在本 FR 中冻结。
  - `target_type` 表示 `target_value` 的解释方式，当前最小允许值固定为：`url`、`content_id`、`creator_id`、`keyword`。
  - `target_value` 类型固定为非空字符串；Core 只负责空值、基本类型与显式组合合法性校验，不负责解释平台语义。
  - `CollectionPolicy` 的最小字段固定为：`collection_mode`。
  - `collection_mode` 当前最小允许值固定为：`public`、`authenticated`、`hybrid`。
  - `collection_mode=public` 表示本次采集只能依赖公开访问路径；Core 不得把“需要认证资源”作为隐式前提塞入该请求。
  - `collection_mode=authenticated` 表示本次采集的合法执行路径必须是认证路径；本 FR 只冻结这一策略语义，不冻结资源对象形态、资源可用性判定算法或 Core 何时完成该判定。
  - `collection_mode=hybrid` 表示本次采集允许 adapter 在“公开路径”与“认证路径”之间选择合法方案，但 Core 不得据此推断任何平台特定请求参数。
  - `InputTarget` 与 `CollectionPolicy` 的最小模型都必须保持单目标语义；批量输入、分页、游标、时间窗、多目标聚合不在本 FR 中定义。
  - 当 `target_type` 不在目标 adapter 的 `supported_targets` 中，或 `collection_mode` 不在其 `supported_collection_modes` 中时，失败必须归因为 Core / Adapter 共享契约不匹配，而不是平台运行时错误。
  - 本 FR 只冻结结构合法性、独立轴合法性与既有 operation -> capability family 的投影规则；不冻结所有 `capability -> target_type -> collection_mode` 组合矩阵。
  - 本 FR 不冻结 `target_type x collection_mode` 的非笛卡尔积支持矩阵；若后续需要表达“某个 target_type 只支持某个 collection_mode 子集”，必须在后续 formal spec 中显式扩展 adapter 声明模型与迁移边界。
  - `InputTarget.capability` 与 SDK 中的 adapter-facing capability family 可以不是同一命名层级；若调用侧 operation 比 adapter-facing family 更具体，Core 必须在进入 adapter 前完成投影。
  - URL 派生值、平台主 ID、签名参数、页面全局变量、HTML fallback 线索等平台语义必须保留在 adapter 内部解析，不得提升为 `InputTarget` 必填字段。
  - `InputTarget` 必须允许表达 `FR-0002` 的既有 URL 输入语义：`adapter_key + capability + input.url` 必须可以无损投影为 `adapter_key + capability + target_type=url + target_value=input.url`。
  - 对 `FR-0002` 既有 `content_detail_by_url` 请求，若原始输入中未显式携带 `CollectionPolicy`，兼容投影必须固定为 `collection_mode=hybrid`；理由是 `FR-0002` 只冻结了单目标 URL 输入与统一结果 envelope，并未冻结“必须公开”或“必须认证”的策略轴，`hybrid` 是唯一不会把旧请求收窄为更严格策略的共享默认值。
  - 对 `FR-0002` 兼容投影得到的 `collection_mode=hybrid`，Core admission 必须采用闭合的兼容归一化规则：若 adapter 仅声明 `public`，则在进入 adapter-facing request 前把该 legacy `hybrid` 归一化为 `public`；若 adapter 仅声明 `authenticated`，则归一化为 `authenticated`；只有 native `FR-0004` 调用方显式提交 `collection_mode=hybrid` 时，Core 才按 adapter 是否显式声明 `hybrid` 来执行常规 admission 规则。
  - 对 `FR-0002` 的 `capability=content_detail_by_url`，兼容投影必须解释为“调用侧 operation id=`content_detail_by_url` 映射到 adapter-facing capability family=`content_detail`，同时 `target_type=url`”；本 FR 不要求修改 `adapter-sdk.md` 中既有 capability family 的命名。
  - 本 FR 只冻结模型语义与边界，不声明现有 `main` 运行时已经完成对这两个模型的实现接入。
- 非功能需求：
  - Core 与 Adapter 的责任边界必须可由 formal spec 直接判定，不依赖 reviewer 脑补。
  - 模型必须足够稳定，能被后续 registry、fake adapter、harness 与版本 gate 复用，但本 FR 不直接定义这些设施。
  - 模型必须避免把当前小红书 / 抖音 detail 路径过拟合成唯一输入形式。
  - formal spec 必须明确列出扩展边界，避免后续 FR 在未回到 spec review 的情况下偷偷扩张字段语义。

## 约束

- 阶段约束：
  - 本事项服务于 `v0.2.0` 的“契约可验证 Core”目标，只冻结共享输入模型与采集策略模型。
  - 本事项不得吞并 `v0.2.0` 中错误模型、adapter registry、fake adapter、adapter harness、version gate 或平台泄漏检查 gate 的 formal spec。
- 架构约束：
  - Core 负责任务输入受理、共享契约校验、资源可用性前置校验与 adapter 调度语义；Adapter 负责平台输入解析、平台请求构造、平台响应处理与平台错误映射。
  - `adapter_key` 属于 Core 侧路由字段；adapter-facing request 至少需要保留由 Core 投影后的 capability family、target 语义与 collection policy 语义，但不要求重复携带 `adapter_key`。
  - Core 不得根据 `target_type=url` 推断平台主 ID、签名参数、认证 cookie、headers、指纹或 fallback 路径。
  - Adapter 不得自行篡改 `InputTarget` 的上游业务语义；若需要平台派生字段，必须从 `target_value` 与 `collection_mode` 出发在 adapter 内部解析。
  - 若后续 FR 需要新增共享字段、批量输入、游标、结果范围、错误语义或 registry 行为，必须重新进入 formal spec 审查链路。

## GWT 验收场景

### 场景 1

Given 调用方提交 `adapter_key=xhs`、`capability=content_detail_by_url`、`target_type=url`、`target_value=<xhs-detail-url>`，且 `collection_mode=authenticated`  
When Core 受理该请求并把共享模型传给目标 adapter  
Then Core 只校验结构与共享组合合法性，不在 Core 层解析 `note_id`、`xsec_token` 或其他平台派生字段

### 场景 2

Given 某 adapter 仅声明支持 `target_type=url` 与 `collection_mode=public`  
When 调用方向该 adapter 提交 `target_type=content_id` 或 `collection_mode=authenticated`  
Then 请求必须在进入平台执行前被拒绝，并归因为共享契约轴值不匹配

### 场景 3

Given 调用方向支持 `hybrid` 的 adapter 提交同一个 `InputTarget`  
When Core 调度该 adapter 执行  
Then Core 只能把 `collection_mode=hybrid` 作为合法策略约束传递，不能替 adapter 决定签名、fallback 或平台请求路径

### 场景 4

Given `FR-0002` 已存在 `adapter_key + capability + input.url` 的正式输入语义  
When 后续实现接入 `InputTarget` 模型  
Then 该既有 URL 输入必须能无损映射为 `target_type=url`、`target_value=input.url` 与 `collection_mode=hybrid`，而不改变单目标 detail 语义

## 异常与边界场景

- 异常场景：
  - 若调用方提交空的 `target_value`、未知的 `target_type` 或未知的 `collection_mode`，请求必须在共享契约层被拒绝。
  - 若 `collection_mode=authenticated`，但后续实现阶段的资源 / auth contract 无法满足该策略要求，请求必须失败；本 FR 不冻结该失败发生在 Core 资源绑定阶段还是 adapter admission 阶段，也不定义统一错误模型字段。
  - 若 adapter 需要从 URL 推导平台主 ID 但推导失败，该失败属于 adapter 平台输入解析失败，不得倒逼 Core 新增平台字段。
- 边界场景：
  - `InputTarget` 当前只承载单一目标，不支持 URL 列表、关键词列表、分页游标、时间区间或结果条数策略。
  - `CollectionPolicy` 当前只冻结 `collection_mode` 这一共享策略轴；重试预算、速率限制、优先级、版本 gate、结果范围与诊断输出不在本 FR 中解决。
  - `target_type=content_id`、`creator_id`、`keyword` 只表示共享输入分类，具体平台是否支持、如何解释、如何校验，仍由 adapter 声明并负责。
  - `hybrid` 允许公开与认证两类合法路径并存，但不代表 Core 可以窥探或操控平台内部 fallback 决策。

## 验收标准

- [ ] `InputTarget` 的最小字段、取值域与职责边界已被冻结为 formal spec
- [ ] `CollectionPolicy` 的最小字段、取值域与执行前语义已被冻结为 formal spec
- [ ] 已明确 Core / Adapter 对结构校验、资源前置校验、平台解析与平台请求构造的职责边界
- [ ] 已明确 `FR-0002` 既有 URL 输入与 `InputTarget` 模型之间的兼容关系
- [ ] 已明确不在本 FR 中解决的事项，且未吞并错误模型、registry、harness、version gate 或平台泄漏检查 gate
- [ ] 已明确 URL 派生值、平台主 ID、签名参数等平台语义不得提升为 Core 共享字段
- [ ] formal spec 足以作为后续 implementation work item、fake adapter、registry 与 harness 的共享输入基线

## 依赖与外部前提

- 外部依赖：
  - GitHub FR `#64` 已作为 canonical requirement 容器建立
  - GitHub Work Item `#68` 已作为本次 spec PR 的执行入口建立
  - `adapter-sdk.md`、`framework-positioning.md` 与 `FR-0002` formal spec 提供现有 Core / Adapter 契约背景
- 上下游影响：
  - 后续实现回合必须围绕本 FR 把调用输入、adapter 声明、资源前置校验与运行时请求对象收口一致
  - 后续错误模型、adapter registry、fake adapter、adapter harness、version gate 与平台泄漏检查 gate 的 formal spec 都必须复用本 FR 的共享模型边界，而不是重写它
