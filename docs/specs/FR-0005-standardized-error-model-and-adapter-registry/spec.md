# FR-0005 v0.2.0 standardized error model and adapter registry

## 关联信息

- item_key：`FR-0005-standardized-error-model-and-adapter-registry`
- Issue：`#65`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`

## 背景与目标

- 背景：`v0.1.0` 已证明最小 Core 可以运行真实参考适配器，但当前错误返回与 adapter 装配仍停留在“能跑即可”的阶段。进入 `v0.2.0` 后，Core 需要把“错误如何分类”和“适配器如何被发现、注册、查找”冻结为稳定契约，才能支撑后续 harness、fake adapter、版本 gate 与双参考适配器回归。
- 目标：为 `v0.2.0` 冻结标准化错误模型与 adapter registry 的 formal contract，明确它们与 Core / Adapter 的职责边界、发现与失败语义，以及后续 Work Item `#69`、`#70` 的实施入口。

## 范围

- 本次纳入：
  - 冻结错误分类的最小语义集合
  - 冻结 adapter registry 的职责边界与最小运行时契约
  - 明确 capability discovery、adapter 注册、adapter 查找与失败路径的统一语义
  - 明确 `fail-closed`、`invalid`、`unsupported` 的边界
  - 明确 `FR-0005` 与 `FR-0004`、`FR-0006`、`FR-0007` 的边界
  - 明确 `#69` 与 `#70` 如何作为本 FR 的后续 Work Item 进入实现
- 本次不纳入：
  - `InputTarget` 与 `CollectionPolicy` 的字段设计或输入建模语义
  - fake adapter、adapter contract test harness、验证工具与 gate 运行方式
  - 双参考适配器回归、平台泄漏检查与版本门禁规则
  - Core / Adapter 的具体代码结构、类层次、模块路径或 import 机制
  - `src/**`、`scripts/**`、`tests/**` 的实现改造

## 需求说明

- 功能需求：
  - Core 必须通过统一的 adapter registry 语义解析可用 adapter，而不是依赖平台特定分支、隐式默认值或调用方自行拼装运行时对象。
  - Core 必须在不执行真实平台采集的前提下，获取“某个 adapter 是否存在”和“某个 adapter 声明支持哪些 capability”的最小发现结果。
  - 错误模型必须为请求校验、registry 查找、adapter 契约失配和平台执行失败提供一致的失败 envelope 语义。
  - discovery 与 lookup 的结果必须可被后续 harness、fake adapter 和 gate 复用，但本 FR 不定义这些工具本身。
- 契约需求：
  - 失败 envelope 的顶层字段继续由 Core 统一承载，最小结构保持 `task_id`、`adapter_key`、`capability`、`status=failed`、`error`。
  - `error` 的最小字段固定为 `category`、`code`、`message`、`details`。
  - `category` 在 `v0.2.0` 的最小集合固定为：
    - `invalid_input`：请求形状、必填字段、类型或当前契约禁止的调用方式不合法，且失败发生在进入 registry 有效查找或 adapter 平台执行之前。
    - `unsupported`：请求本身合法，但目标 adapter 或 capability 不存在，或目标存在但未声明支持该 capability。
    - `runtime_contract`：registry、adapter 声明、capability 元数据、成功 payload 或 host-side 运行时契约失配；此类问题必须 fail-closed。
    - `platform`：adapter 已接管平台语义，并因平台事实、登录态、签名、资源、风控或平台响应失败而无法完成执行。
  - `invalid_input` 与 `unsupported` 必须区分：
    - 前者表示“请求不合法，不能进入有效分发”。
    - 后者表示“请求合法，但当前 registry / adapter 集合无法满足”。
  - `runtime_contract` 与 `platform` 必须区分：
    - 前者表示 Core / registry / adapter contract 破损或未满足约定。
    - 后者表示 contract 有效，但平台执行失败。
  - adapter 已被成功选中后，若在任何真实平台调用前发现输入无法被该 adapter 解析、归一或接受，则该失败固定归入 `invalid_input`，而不是 `platform` 或 `runtime_contract`。
  - adapter registry 的最小职责固定为：
    - 接收明确的 adapter 绑定集合并形成可查询视图
    - 以稳定 `adapter_key` 提供唯一查找结果
    - 暴露每个 adapter 的 capability 声明结果，供 Core 做分发前判断
    - 对重复 key、歧义注册、无效 adapter 声明和无效 capability 元数据返回统一 fail-closed 语义
  - adapter registry 的最小非职责固定为：
    - 不定义模块扫描、插件市场、远程发现或 import 约定
    - 不负责生成 `InputTarget`、`CollectionPolicy` 或平台输入
    - 不负责 fake adapter、测试 harness 或 gate 调度
    - 不负责平台资源准备、登录态管理或浏览器注入
  - capability discovery 必须满足以下约束：
    - 发现结果来源于 adapter 对外声明的稳定 capability 元数据，而不是一次真实采集结果
    - discovery 不得要求真实平台网络访问、登录态或浏览器副作用
    - 若 capability 声明缺失、形状非法或不可判定，Core 必须返回 `runtime_contract`，不得静默回退
  - fail-closed 语义固定为：
    - registry 无法形成唯一、可验证的 adapter 视图时，Core 必须返回 `runtime_contract`
    - Core 不得在 registry 失效时推断默认 adapter、猜测 capability、跳过校验或回退到平台特定分支
    - adapter 声明与实际返回结果不一致时，Core 必须按 `runtime_contract` 失败，而不是把缺失字段视作成功
  - `details` 的语义固定为：
    - `details` 用于承载机器可判定的补充上下文
    - `invalid_input` 可承载非法字段名、非法值类型或缺失字段列表
    - `unsupported` 可承载已知 `adapter_key` 或 capability 列表
    - `runtime_contract` 可承载失配来源、无效字段、声明形状错误或错误类型
    - `platform` 可承载平台 code、平台消息、资源上下文或平台提示，但不改变统一 envelope 结构
- 非功能需求：
  - formal spec 必须让 reviewer 在不阅读实现代码的前提下判定错误分类与 registry 边界。
  - spec 必须保留实现自由度，不把 registry 具体方法名、类结构、模块布局或缓存策略写死。
  - error model 与 registry 的语义必须可支撑后续双参考适配器与 fake adapter 复用，而不把这些事项提前吞入本 FR。

## 约束

- 阶段约束：
  - 本事项服务于 `v0.2.0` 的“把能跑变成可验证”，只冻结共享契约，不进入实现。
  - 本事项不能提前替代 `FR-0006` 的 harness / fake adapter / 验证工具语义，也不能替代 `FR-0007` 的 gate / regression 语义。
- 架构约束：
  - Core 负责统一错误 envelope、registry 消费与 fail-closed 规则；Adapter 负责平台语义与平台错误细节。
  - 平台特定错误码、签名、登录态、反爬、浏览器桥接与资源细节不得渗入 Core 的分类规则。
  - registry 可以由不同实现机制承载，但对 Core 暴露的查找与 discovery 语义必须稳定。

## GWT 验收场景

### 场景 1

Given Core 持有一个已 materialize 的 adapter registry，且其中存在 `adapter_key=xhs` 并声明支持 `content_detail_by_url`  
When 调用方向 Core 请求查找 `xhs` 并验证该 capability  
Then Core 必须在进入平台执行前得到确定的“adapter 存在且 capability 受支持”的结论

### 场景 2

Given 请求的 `adapter_key` 不存在于当前 registry  
When Core 进行 adapter 查找  
Then Core 必须返回 `category=unsupported` 的失败 envelope，而不是推断默认 adapter 或回退到其他注册项

### 场景 3

Given 当前 registry 存在重复 key、歧义注册、无效 adapter 声明或无效 capability 元数据  
When Core 尝试 materialize、discover 或 lookup  
Then Core 必须返回 `category=runtime_contract` 的失败 envelope，并按 fail-closed 终止该次执行

### 场景 4

Given 请求缺少当前 contract 要求的最小字段，或字段类型不合法  
When Core 在进入有效 registry 分发前校验请求  
Then Core 必须返回 `category=invalid_input` 的失败 envelope

### 场景 5

Given adapter 已被成功查找到，且 capability 声明有效  
When adapter 在真实平台执行过程中遇到登录失效、签名错误、内容不存在或平台风控  
Then Core 必须返回 `category=platform` 的统一失败 envelope，并保留 adapter 提供的结构化平台细节

### 场景 6

Given registry 与请求都合法，但目标 adapter 未声明支持当前 capability  
When Core 在执行前校验 capability  
Then Core 必须返回 `category=unsupported` 的失败 envelope，而不是让 adapter 进入不受支持的执行路径

## 异常与边界场景

- 异常场景：
  - registry 为空本身不自动构成 `runtime_contract`；只有当请求需要的 adapter / capability 无法满足时，才返回 `unsupported`。
  - registry 形状非法、查找结果抛异常、capability 元数据不可判定、adapter 成功 payload 失配，都必须归入 `runtime_contract`。
  - adapter 已被查找到、但在真实平台调用前判定“输入 URL 不属于该平台”“输入无法解析为当前 adapter 所需最小语义”或“adapter 前置输入约束不满足”时，必须返回 `invalid_input`。
  - adapter 抛出未映射到平台语义的宿主异常时，Core 不得直接把该异常冒泡到调用方，必须按统一错误模型处理。
- 边界场景：
  - 本 FR 只冻结“registry 对 Core 的契约”，不规定 registry 如何从模块、配置或插件系统中构建。
  - 本 FR 只冻结“discovery 的语义结果”，不规定后续 harness 如何调用这些结果。
  - 本 FR 不定义 fake adapter、harness、validator、版本 gate 的目录、脚本或测试形态。
  - `FR-0004` 负责冻结输入建模；`FR-0005` 只消费“已经合法进入分发”的请求与错误分类。
  - `FR-0006` 负责冻结 fake adapter / harness / validator 的验证基座；`FR-0005` 只提供其依赖的 error model 与 registry contract。
  - `FR-0007` 负责冻结 gate / regression / 平台泄漏检查流程；`FR-0005` 不直接定义这些门禁。

## 验收标准

- [ ] `invalid_input`、`unsupported`、`runtime_contract`、`platform` 四类错误的语义边界已冻结
- [ ] fail-closed、invalid、unsupported 的判定条件已清楚区分
- [ ] adapter registry 的职责、非职责与 discovery 约束已冻结
- [ ] registry 与 adapter 生命周期 / discovery 之间的契约边界已冻结，且不要求真实平台副作用
- [ ] spec 明确规定 registry / adapter / success payload 失配时必须走 `runtime_contract`
- [ ] spec 明确规定平台执行失败必须走 `platform`
- [ ] `FR-0004`、`FR-0006`、`FR-0007` 的边界，以及 `#69` / `#70` 的后续实现拆分已写清
- [ ] 当前 formal spec PR 未混入实现代码、脚本、测试或 gate 运行时改造

## 依赖与外部前提

- 外部依赖：
  - GitHub Phase `#63` 已建立 `v0.2.0` 上位阶段容器
  - GitHub FR `#65` 已作为 canonical requirement 容器存在
- 上下游影响：
  - `#69` 在本 spec 基础上实现标准化错误模型，负责把错误分类映射到 Core / Adapter 运行时与失败 envelope
  - `#70` 在本 spec 基础上实现 adapter registry，负责把注册、lookup、capability discovery 与 fail-closed 行为落到运行时
  - `FR-0006` 后续可在本 spec 基础上为 fake adapter / harness / validator 建立可验证契约
  - `FR-0007` 后续可在本 spec 基础上把双参考适配器回归与平台泄漏检查接入固定 gate
