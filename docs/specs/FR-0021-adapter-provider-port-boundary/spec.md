# FR-0021 Adapter provider port boundary

## 关联信息

- item_key：`FR-0021-adapter-provider-port-boundary`
- Issue：`#265`
- item_type：`FR`
- release：`v0.7.0`
- sprint：`2026-S20`

## 背景与目标

- 背景：当前小红书、抖音 adapter 内部同时承载 Adapter 对 Core 的运行时契约、站点语义、签名/HTTP/browser fallback 等 provider-like 执行细节。该结构在只有 native 实现时可运行，但后续接入外部 provider 前缺少明确的 adapter-owned extension point，容易把 provider 选择、fallback 或技术字段泄漏进 Core。
- 目标：为 `v0.7.0` 冻结 `Syvert Adapter -> Syvert-owned Provider Port -> Native Provider` 的仓内边界，使当前内嵌执行逻辑可被拆成 native provider 实现细节，同时保持 Core 只调用 Adapter，且当前小红书、抖音 `content_detail_by_url` approved slice 行为兼容。

## 范围

- 本次纳入：
  - 定义 adapter-owned provider port 的所有权、稳定性和调用边界
  - 定义 native provider 在当前仓内只服务小红书、抖音 `content_detail_by_url` approved slice
  - 定义 provider result 只返回 adapter 需要的 raw platform payload 与 platform detail object
  - 定义 normalized result、Adapter public metadata、resource requirement declaration 仍由 Adapter 拥有
  - 定义现有 constructor transport hooks 的兼容要求
  - 定义 Core / registry / task record / resource model 不得出现 provider 概念
- 本次不纳入：
  - WebEnvoy、OpenCLI、bb-browser、agent-browser 或任何外部 provider 接入
  - 新增小红书/抖音搜索、评论、账号、发布、通知、浏览/点赞/收藏/评论等业务能力
  - Core provider registry、provider selector、provider fallback priority 或跨 provider routing
  - 新资源类型、浏览器会话资源、账号池、cookie profile 或 provider resource supply model
  - adapter 独立仓库拆分

## 需求说明

- 功能需求：
  - 每个参考 adapter 可以拥有一个内部 provider port，用于把当前站点执行细节从 Adapter public runtime surface 中拆出。
  - 当前批准的 provider port 只服务 adapter-facing `content_detail` family，且只由 Core public operation `content_detail_by_url` 投影进入。
  - native provider 必须由当前仓内 adapter 使用；它不是外部 provider SDK，也不是 Core-facing extension point。
  - Adapter 必须继续暴露既有 runtime surface：`adapter_key`、`supported_capabilities`、`supported_targets`、`supported_collection_modes`、`resource_requirement_declarations` 与 `execute()`。
  - Adapter 必须继续负责 request validation、resource bundle consumption、provider result 到 Syvert normalized result 的转换，以及最终 `{"raw": ..., "normalized": ...}` 成功 payload。
  - provider result 必须只包含 adapter 生成最终结果所需的信息；当前最小形态是 raw platform payload 与已解析的 platform detail object。
  - 现有 `sign_transport`、`detail_transport`、`page_transport`、`page_state_transport` 等 constructor hooks 必须继续可用于测试和本地注入。
- 契约需求：
  - Core 只能调用 Adapter，不得直接调用 provider port、native provider 或 provider module。
  - Registry discovery 只能看到 Adapter public metadata，不得看到 provider key、provider priority、provider capability 或 provider resource requirement。
  - TaskRecord、runtime envelope、resource trace 与 resource lifecycle 不得新增 provider 字段。
  - provider port 不得承载 provider 选择、fallback priority、排序、打分、外部 provider binding 或 resource acquisition 语义。
  - provider 内部错误必须通过 Adapter 映射到现有 `PlatformAdapterError` / failed envelope 语义；不得新增 provider-specific failed envelope category。
  - import compatibility 必须保持：若后续实现移动默认 transport helper，原模块可导入路径必须继续可用。
- 非功能需求：
  - 拆分必须是 behavior-preserving refactor，不能改变小红书、抖音当前 approved slice 的输入、输出、资源需求或失败分类。
  - provider port 在 `v0.7.0` 只作为仓内内部边界稳定；不得承诺第三方 provider compatibility contract。
  - 后续外部 provider 接入必须另建 FR，不得反向扩大本 FR 范围。

## 约束

- 阶段约束：
  - 本 FR 服务 `v0.7.0` 的 adapter surface 稳定化，不扩张业务能力。
  - `v0.7.0` 中唯一 approved adapter-facing capability baseline 仍是小红书、抖音 `content_detail_by_url` 通过 `content_detail` family 执行。
  - 外部 provider 接入、更多站点能力、adapter 独立仓库评估均留到 `v1.0.0` 稳定之后或后续独立 FR。
- 架构约束：
  - Core 负责运行时语义；Adapter 负责目标系统语义；provider port 只属于 Adapter 内部执行边界。
  - Provider port 不得绕过 `FR-0012` Core 注入资源包边界；native provider 只能消费 Adapter 传入的已解析执行上下文。
  - Provider port 不得改写 `FR-0013`/`FR-0014`/`FR-0015` 已冻结的 resource requirement、capability matching 与 evidence baseline。

## GWT 验收场景

### 场景 1：Core 只调用 Adapter

Given Core 正在执行 `adapter_key=xhs`、`capability=content_detail_by_url` 的任务  
When runtime 查找 adapter 并进入执行  
Then Core 只能调用 `XhsAdapter.execute()`，不得直接发现或调用 `NativeXhsProvider`、provider port 或 provider selector

### 场景 2：Adapter 委托 native provider

Given `XhsAdapter.execute()` 已完成 request validation、URL 解析与 resource bundle consumption  
When Adapter 需要执行平台 detail 获取  
Then Adapter 可以通过内部 provider port 调用 native provider，并从 provider result 取得 raw platform payload 与 note detail object

### 场景 3：normalized result 仍由 Adapter 负责

Given native provider 已返回 raw platform payload 与 platform detail object  
When Adapter 生成成功结果  
Then Adapter 必须继续返回 `{"raw": ..., "normalized": ...}`，且 normalized result 不得由 Core 或 provider registry 生成

### 场景 4：Registry 不暴露 provider

Given `AdapterRegistry.from_mapping()` 消费小红书、抖音 adapter  
When 调用方 discovery adapter capabilities、targets、collection modes 或 resource requirements  
Then 返回结果只能包含 Adapter public metadata，不得包含 provider key、provider priority、provider fallback 或 provider capability 字段

### 场景 5：不新增业务能力

Given 有调用方请求搜索、评论、发布、通知、点赞、收藏或账号信息能力  
When 该请求进入 `FR-0021` 范围判断  
Then 本 FR 不批准这些能力，后续实现不得把它们作为 provider port 拆分的一部分落地

### 场景 6：外部 provider 不在范围

Given 后续存在 WebEnvoy、OpenCLI、bb-browser 或 agent-browser provider 候选  
When `v0.7.0` provider port implementation 执行  
Then 只能保留 native provider 落点，不得接入外部 provider、provider selection 或 fallback priority

## 异常与边界场景

- 异常场景：
  - 若实现让 Core、registry、TaskRecord 或 resource lifecycle 出现 provider 字段，视为 contract violation。
  - 若 provider port 返回 Syvert normalized result 并绕过 Adapter normalizer，视为 contract violation。
  - 若 provider port 引入外部 provider binding、排序、打分或 fallback priority，视为 scope 漂移。
  - 若拆分改变 `content_detail_by_url` 的 adapter-facing 输入、资源需求、raw/normalized result 或错误类别，必须阻断合并。
- 边界场景：
  - Adapter 可以保留测试用 constructor hooks；这些 hooks 是仓内测试 seam，不是外部 provider contract。
  - Native provider 可以继续使用现有 HTTP/sign/browser bridge 实现细节，但这些技术字段不得提升到 Core resource model。
  - Provider module 命名可以使用 `xhs_provider.py` / `douyin_provider.py` 或等价内部模块名；正式 contract 绑定的是所有权和行为边界，不绑定物理文件名。

## 验收标准

- [ ] formal spec 明确 adapter-owned provider port 是 Adapter 内部边界，不是 Core-facing provider SDK
- [ ] formal spec 明确 Core、registry、TaskRecord、resource lifecycle 不得出现 provider 字段
- [ ] formal spec 明确 native provider 只服务当前小红书、抖音 `content_detail_by_url` approved slice
- [ ] formal spec 明确 normalized result 仍由 Adapter 负责
- [ ] formal spec 明确现有 constructor transport hooks 必须保持兼容
- [ ] formal spec 明确禁止外部 provider 接入、新业务能力、Core provider registry / selector / fallback priority
- [ ] formal spec 为 `#269`、`#270`、`#271`、`#272` 提供可执行进入条件

## 依赖与外部前提

- 外部依赖：
  - 无新增外部 provider 或外部服务依赖。
- 上下游影响：
  - `#269` 必须消费本 formal spec 实现 provider port / native provider 拆分。
  - `#270` 必须消费本 formal spec 更新 SDK compatibility 与 capability metadata 文档。
  - `#271` 必须证明拆分后双参考 adapter baseline 兼容。
  - `#272` 必须以本 formal spec、实现、metadata 与 evidence 为 closeout 输入。
