# FR-0015 Dual-reference resource capability evidence

## 关联信息

- item_key：`FR-0015-dual-reference-resource-capability-evidence`
- Issue：`#191`
- item_type：`FR`
- release：`v0.5.0`
- sprint：`2026-S18`

## 背景与目标

- 背景：`FR-0010`、`FR-0011` 与 `FR-0012` 已冻结最小资源生命周期、tracing 与 Core 注入边界，但 `v0.5.0` 进入资源需求声明与能力匹配前，仍缺少一份正式的“双参考适配器证据载体”。如果没有这份载体，新的资源能力名很容易被单平台事实、技术实现细节或会话内判断直接带进 Core 抽象。
- 目标：为 `v0.5.0` 冻结双参考适配器资源能力证据记录 contract，要求所有可进入 Core 的资源能力标识都必须被小红书 / 抖音双参考适配器在同类执行路径上的证据共同支撑；同时把不满足该条件的候选抽象明确收口为 `adapter_only` 或 `rejected`。

## 范围

- 本次纳入：
  - 冻结 canonical evidence carrier `DualReferenceResourceCapabilityEvidenceRecord`
  - 冻结 `shared_status` 的允许值与含义
  - 冻结 `evidence_refs` 的稳定引用约束
  - 冻结 `v0.5.0` 可被 `FR-0013 / FR-0014` 消费的最小资源能力词汇
  - 冻结 research 补充入口中“共性资源语义 / 单平台特例 / 被拒绝抽象候选”的必备内容
- 本次不纳入：
  - 资源需求声明 runtime 实现
  - Core 资源能力匹配 runtime 实现
  - 第三个平台的扩展验证
  - provider 选择、调度策略、浏览器技术绑定或资源编排 DSL

## 需求说明

- 功能需求：
  - `v0.5.0` 内每一个待进入 Core 抽象的资源能力候选，都必须先落成至少一条 `DualReferenceResourceCapabilityEvidenceRecord`。没有该 carrier 的候选，不得在 `FR-0013` 或 `FR-0014` 中直接被消费。
  - `DualReferenceResourceCapabilityEvidenceRecord` 至少必须固定以下字段：
    - `adapter_key`
    - `capability`
    - `execution_path`
    - `resource_signals`
    - `candidate_abstract_capability`
    - `shared_status`
    - `evidence_refs`
    - `decision`
  - `adapter_key` 在 `v0.5.0` 只允许 `xhs` 或 `douyin`；该字段用于表达“是哪一个双参考适配器给出了这条证据”。
  - `capability` 表达 adapter-facing capability family；在当前双参考适配器基线中只允许 `content_detail`，不得把 `FR-0015` 漂移成平台专属操作清单。
  - `execution_path` 用于表达证据成立的执行路径边界；至少必须能稳定表达 `target_type` 与 `collection_mode`。若同一 capability family 下存在多条不可等价的路径，必须在该字段中显式区分，不得把不相容路径压平为一条证据。
  - `resource_signals` 只允许记录观察到的资源事实，例如“runtime 当前请求了哪些受管资源 slot”“adapter 从注入 bundle 中读取了哪些共享 carrier”“回归种子如何证明该路径依赖受管资源”；它不得偷渡 provider 选择、调度算法或实现偏好。
  - `candidate_abstract_capability` 表达当前正在审查的资源能力标识。它可以是待批准候选，也可以是明确被 `adapter_only` / `rejected` 收口的候选。
  - `shared_status` 只允许以下三类值：
    - `shared`：小红书 / 抖音在同类执行路径上都给出了可复验的共同证据，允许作为 `v0.5.0` 的共享能力词汇
    - `adapter_only`：只有单平台证据成立，或虽然有双平台事实但仍只能解释为 adapter 私有前置，禁止进入 Core 抽象
    - `rejected`：证据不足、抽象方向错误，或技术绑定过重，禁止进入 `v0.5.0`
  - `decision` 在 `v0.5.0` 只允许以下三类值：
    - `approve_for_v0_5_0`
    - `keep_adapter_local`
    - `reject_for_v0_5_0`
  - `shared_status` 与 `decision` 的组合必须满足：
    - `shared -> approve_for_v0_5_0`
    - `adapter_only -> keep_adapter_local`
    - `rejected -> reject_for_v0_5_0`
  - `evidence_refs` 必须是非空、去重、稳定的字符串数组；每个引用都必须能落到本 FR 的 `research.md` 中定义的证据登记项，而不是会话描述、一次性截图或无法追溯的口头结论。
  - 一个候选资源能力只有在 `xhs` 与 `douyin` 都形成可复验记录、且两侧 `shared_status=shared` / `decision=approve_for_v0_5_0` 时，才允许进入 `v0.5.0` 的共享能力词汇表。
  - 单平台特例、字段级材料差异、浏览器回退细节、签名服务地址、token 名称等都必须通过本 FR 明确落成 `adapter_only` 或 `rejected`，而不是由下游事项自行决定是否提升为 Core 抽象。
  - `FR-0015` 负责冻结 `v0.5.0` 的最小共享能力词汇。当前可批准并可被 `FR-0013 / FR-0014` 消费的能力标识只允许：
    - `account`
    - `proxy`
  - 以上能力词汇在 `v0.5.0` 只表达最小共享语义：
    - `account`：Core 能注入被 adapter 消费的受管账号材料 carrier
    - `proxy`：Core 能在同一执行路径上提供最小受管代理能力前提
  - 除 `account`、`proxy` 外，`FR-0013 / FR-0014` 不得自行新增 `sign_service`、`browser_state`、`cookies`、`user_agent`、`verify_fp`、`ms_token`、`webid`、`a_bogus`、`xsec_token` 等能力名。
- 契约需求：
  - `FR-0015` 是 `v0.5.0` 资源能力命名的唯一批准入口。`FR-0013` 只能声明这里已经批准过的能力标识，`FR-0014` 只能匹配这里已经批准过的能力标识。
  - 若某个候选抽象只被单平台证明，或其语义只能落在平台私有材料 / 技术桥接层，它就必须被写成 `adapter_only` 或 `rejected`；下游 FR 不得通过“先实现再补证据”的方式反向改写本 FR。
  - `research.md` 必须显式保留三类内容：
    - 共性资源语义
    - 单平台特例
    - 被拒绝的抽象候选
  - `research.md` 是本 FR 的证据补充入口，但不能成为第二套真相源；一切可批准能力仍以 `DualReferenceResourceCapabilityEvidenceRecord` 与本 spec 冻结的批准规则为准。
  - 能力词汇必须保持实现无关；本 FR 不允许把 Playwright、CDP、Chromium、浏览器 tab、签名服务部署方式或 provider 选择器写成共享能力本身。
- 非功能需求：
  - 证据 contract 必须 fail-closed；任何缺少稳定 `evidence_refs`、无法比较执行路径、或试图把技术绑定字段升格为共享能力的候选，都不得被宽松放行。
  - 证据记录必须可复验、可追溯，并能被 future review 直接消费；不能依赖当前会话上下文才能理解。
  - `FR-0015` 只冻结“哪些能力名可以进入 `v0.5.0`”，不提前承诺这些能力在实现中如何调度、如何 acquire 或如何 fallback。

## 约束

- 阶段约束：
  - 本事项只服务 `v0.5.0` 的 formal spec closeout，不混入 runtime、测试代码、release / sprint 索引或根级治理修正。
  - 本事项只以小红书 / 抖音双参考适配器作为证据边界，不提前纳入第三个平台或更大生态。
- 架构约束：
  - `FR-0015` 不重写 `FR-0010` 的 resource type / bundle / lease 语义，不重写 `FR-0012` 的 Core 注入边界；它只负责判断哪些资源能力词汇有资格进入 `v0.5.0`。
  - formal spec 与实现 PR 必须分离；`#194` 只冻结证据 carrier、批准规则与 research 基线，不实现证据采集流水线。
  - 下游 `FR-0013 / FR-0014` 必须消费本 FR 已批准的能力词汇，不得通过声明或 matcher 反向定义新的共享能力名。

## GWT 验收场景

### 场景 1

Given `xhs` 与 `douyin` 在 `content_detail + target_type=url + collection_mode=hybrid` 路径上都能提供稳定证据，证明该路径依赖受管账号材料 carrier  
When `candidate_abstract_capability=account` 进入 `FR-0015` 审查  
Then 两侧记录都必须被收口为 `shared + approve_for_v0_5_0`，且 `account` 可以进入 `v0.5.0` 批准词汇表

### 场景 2

Given `xhs` 与 `douyin` 当前共享 Core 路径都要求同一条受管代理前提，但 research 没有证明更丰富的浏览器或网络 profile 抽象  
When `candidate_abstract_capability=proxy` 进入 `FR-0015` 审查  
Then `proxy` 只能以“最小受管代理能力前提”被批准，而不能顺势扩张成更高阶的浏览器 / network profile 抽象

### 场景 3

Given `verify_fp`、`ms_token` 或 `webid` 只在抖音账号材料中出现  
When 它们作为候选资源能力进入 `FR-0015` 审查  
Then 它们必须被收口为 `adapter_only + keep_adapter_local`，不得进入共享能力词汇表

### 场景 4

Given `sign_base_url`、`browser_state` 或类似浏览器桥接语义带有明显技术绑定  
When 它们作为候选资源能力进入 `FR-0015` 审查  
Then 它们必须被收口为 `rejected + reject_for_v0_5_0`，不得被 `FR-0013 / FR-0014` 消费

### 场景 5

Given 某个候选能力缺少稳定 `evidence_refs`，或只剩单平台一次性跑通结果  
When 审查者尝试把它加入 `v0.5.0` 能力词汇  
Then `FR-0015` 必须 fail-closed，不得把该候选视为 `shared`

## 异常与边界场景

- 异常场景：
  - 若 `evidence_refs` 为空、重复，或无法回指 `research.md` 中的稳定证据登记项，则该记录不满足 formal contract。
  - 若两条记录表面上属于同一 candidate capability，但 `execution_path` 无法证明是同类路径，则不得据此推出 `shared`。
  - 若某个候选能力试图直接复用技术实现字段名、浏览器框架名或 provider 选择术语，它必须被视为错误抽象方向并进入 `rejected`。
- 边界场景：
  - `FR-0015` 不要求把 `account.material` 的所有内部字段都提升为独立能力；字段级材料可以被 account capability 吸收而不另建共享能力名。
  - `FR-0015` 只冻结 `v0.5.0` 能力命名基线；未来若需新增能力，必须通过新的双参考证据与新的 formal spec follow-up 收口。
  - 本 FR 批准 `proxy` 时，只批准最小共享代理能力前提，不代表已经批准更高阶的代理 provider 分类、网络地理属性或浏览器 profile。

## 验收标准

- [ ] formal spec 明确冻结 `DualReferenceResourceCapabilityEvidenceRecord` 的字段集合与语义
- [ ] formal spec 明确冻结 `shared_status` 与 `decision` 的允许值和映射关系
- [ ] formal spec 明确冻结 `v0.5.0` 批准资源能力词汇仅为 `account`、`proxy`
- [ ] formal spec 明确要求 `research.md` 显式列出共性资源语义、单平台特例与被拒绝抽象候选
- [ ] formal spec 明确禁止下游 `FR-0013 / FR-0014` 自行新增能力标识

## 依赖与外部前提

- 外部依赖：
  - `#188` 已把 `v0.5.0` 定义为资源需求声明、能力匹配与双参考证据收口阶段
  - `#191` 作为本 FR 的 canonical requirement 容器已建立，并绑定 `#194`
  - `FR-0010` 已冻结 `account / proxy` 资源类型与 bundle/lease contract
  - `FR-0012` 已冻结 Core 注入 resource bundle 的边界，证明受管资源必须通过 Core 进入 adapter 执行路径
  - 当前仓内 runtime / adapters / regression 基线已给出小红书 / 抖音共享执行路径与最小资源事实
- 上下游影响：
  - `FR-0013` 只能声明本 FR 已批准的能力标识
  - `FR-0014` 只能匹配本 FR 已批准的能力标识
  - 后续双参考适配器证据收口实现 Work Item 必须复用本 FR 冻结的 evidence carrier，而不是创建另一套影子记录格式
