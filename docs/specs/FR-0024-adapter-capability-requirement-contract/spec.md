# FR-0024 Adapter capability requirement contract

## 关联信息

- item_key：`FR-0024-adapter-capability-requirement-contract`
- Issue：`#296`
- item_type：`FR`
- release：`v0.8.0`
- sprint：`2026-S21`

## 背景与目标

- 背景：`v0.8.0` 要把开放接入路径推进到“第三方 Adapter 与 Adapter + Provider 兼容性可以被稳定判断”。在进入 Provider offer 与 compatibility decision 之前，Adapter 侧必须先有唯一、可验证、可被 manifest / SDK / validator / reference adapter migration 一致消费的 capability requirement carrier。`FR-0027` 已冻结多 profile resource requirement 与 proof binding，本 FR 在其上承接 Adapter capability requirement 的更高层声明。
- 目标：冻结 `AdapterCapabilityRequirement` 作为 Adapter capability requirement 的 canonical carrier，明确 capability、execution requirement、resource profiles、evidence、lifecycle、observability 与 fail-closed 字段边界，使后续 `#314/#315/#316` 可以基于同一 requirement truth 进入 manifest fixture validator、reference adapter migration 与父 FR closeout。

## 范围

- 本次纳入：
  - 冻结 `AdapterCapabilityRequirement` canonical carrier。
  - 冻结 capability identity、execution requirement、resource requirement profiles、proof binding、lifecycle expectation、observability expectation 与 fail-closed 字段边界。
  - 明确 `AdapterCapabilityRequirement.resource_requirement` 必须消费 `FR-0027` 的 `AdapterResourceRequirementDeclarationV2` 与 `ApprovedSharedResourceRequirementProfileEvidenceEntry`。
  - 明确 requirement validator / manifest fixture / SDK 文档 / reference adapter migration 的进入条件。
  - 明确 requirement 声明在 `v0.8.0` 当前 approved slice 中只覆盖 `content_detail_by_url + target_type=url + collection_mode=hybrid`。
- 本次不纳入：
  - Provider capability offer 本体。
  - `AdapterCapabilityRequirement x ProviderCapabilityOffer` 的 compatibility decision 规则。
  - profile 优先级、排序、自动 fallback、打分或 provider selector。
  - 新共享能力词汇。
  - runtime matcher、manifest validator、reference adapter migration 或 contract test 实现。
  - 关闭父 FR `#296`。

## 需求说明

- 功能需求：
  - `AdapterCapabilityRequirement` 必须是 `v0.8.0` 及之后 Adapter capability requirement 的唯一 canonical carrier；不得并行维护第二套 manifest-only、SDK-only 或 adapter-private requirement 模型。
  - `AdapterCapabilityRequirement` 至少必须固定以下字段：
    - `adapter_key`
    - `capability`
    - `execution_requirement`
    - `resource_requirement`
    - `evidence`
    - `lifecycle`
    - `observability`
    - `fail_closed`
  - `adapter_key` 必须是非空稳定字符串，并且必须与 Adapter registry / manifest 中的 adapter identity 一致。
  - `capability` 必须表达 adapter-facing capability family；当前 `v0.8.0` approved slice 只允许 `content_detail`。
  - `execution_requirement` 必须固定 Core public operation 到 Adapter capability 的投影边界，当前必须且只能表达：
    - `operation=content_detail_by_url`
    - `target_type=url`
    - `collection_mode=hybrid`
  - `resource_requirement` 必须直接嵌入或引用 `FR-0027` 的 `AdapterResourceRequirementDeclarationV2`，并保持 `adapter_key`、`capability` 与当前 execution slice 一致。
  - `resource_requirement.resource_requirement_profiles` 的合法性、profile tuple、single proof binding、adapter coverage 与 `invalid_resource_requirement` 口径必须完全消费 `FR-0027`；本 FR 不重新定义第二套 profile 规则。
  - `evidence` 必须把 requirement 声明回指到已批准 formal proof。当前至少必须包含：
    - `resource_profile_evidence_refs`：来自 `FR-0027` declaration profile 的 proof refs，最终唯一命中 `ApprovedSharedResourceRequirementProfileEvidenceEntry.profile_ref`
    - `capability_requirement_evidence_refs`：回指本 FR 或后续 manifest fixture / reference adapter migration 的 requirement 级验证证据
  - `lifecycle` 必须表达 Adapter 在该 capability 上对 Core resource lifecycle 的消费预期，而不是定义新的 lifecycle store。当前只允许声明：
    - 是否需要 Core 注入资源 bundle
    - profile 满足后 Adapter 是否必须按现有 resource disposition / lease 语义回传执行结果或失败 hint
    - 不得声明 acquire/release 实现细节、资源池策略或 provider-owned lifecycle
  - `observability` 必须表达 requirement 可被追踪与审计的最小字段，当前至少覆盖 requirement id、profile key、proof refs、match status / failure code 的可记录性；不得引入 provider product、selector、priority 或技术链路字段。
  - `fail_closed` 必须固定为显式 `true`。任何 requirement 缺字段、字段不一致、proof 不可解析、resource profile 不合法、execution slice 越界或出现被禁止字段时，都不得被宽松视为可执行。
  - requirement carrier 可以被 manifest fixture、SDK 文档、reference adapter baseline 与后续 compatibility decision 消费，但这些消费者不得扩写本 FR 未批准的字段。
- 契约需求：
  - 以下情况必须归类为 requirement contract violation，并映射到 `runtime_contract + invalid_resource_requirement` 或等价的 spec/validator 阻断口径：
    - 缺少固定字段，或 `fail_closed` 不是 `true`
    - `adapter_key` / `capability` / `execution_requirement` 与 embedded `AdapterResourceRequirementDeclarationV2` 不一致
    - `resource_requirement` 未消费 `FR-0027` carrier，或 profile / proof binding 不满足 `FR-0027`
    - `resource_profile_evidence_refs` 与 `FR-0027` proof refs 不一致、不可唯一解析或未覆盖 declaration adapter
    - `execution_requirement` 把 approved slice 外推到搜索、评论、发布、通知、互动或其它 target / collection mode
    - `lifecycle` 试图定义新的 resource acquisition、release、pooling、provider-owned lifecycle 或跨 adapter 资源调度
    - `observability` 暴露 provider identity、provider selector、fallback outcome、browser/CDP/Playwright/network tier 等技术字段
    - carrier 出现 `provider_offer`、`compatibility_decision`、`priority`、`fallback`、`preferred_profile`、`optional_capabilities` 或同义字段
  - 以下情况不得被本 FR 判定为已通过 compatibility：
    - Adapter requirement 合法，但尚无 Provider offer。
    - Adapter requirement 合法，但某个 Provider 是否满足该 requirement 尚未经过 `FR-0026` decision。
  - `AdapterCapabilityRequirement` 只回答“Adapter 声明自己执行某 capability 需要什么前提”；不回答“哪个 Provider 可满足它”。
- 非功能需求：
  - contract 必须 fail-closed，任何无法证明字段、profile 或证据一致的情况都不能进入后续 implementation-ready 状态。
  - formal spec 必须保持 Core / Adapter / Provider 边界：Core 继续只调用 Adapter，Provider 只能作为 Adapter-bound 能力参与后续兼容性判断。
  - formal suite 必须让 reviewer、guardian、`#314` validator、`#315` migration 与 `#316` closeout 直接消费，不依赖会话上下文补足隐藏前提。

## 约束

- 阶段约束：
  - 本 FR 服务 `v0.8.0` adapter capability requirement 声明契约，不提前完成 Provider offer、compatibility decision 或真实 provider 验证样本。
  - 当前 approved slice 只覆盖小红书、抖音参考 adapter 的 `content_detail_by_url + url + hybrid` requirement baseline。
  - 新执行路径、新 target、新 collection mode 或新共享能力词汇必须另建 evidence / formal spec follow-up。
- 架构约束：
  - `FR-0021` 继续持有 adapter-owned provider port 内部边界；本 FR 不把 provider port 升格为 Core-facing provider SDK。
  - `FR-0027` 继续持有 resource profile / proof binding truth；本 FR 只消费它，不改写它。
  - `FR-0010` / `FR-0012` 继续持有 resource lifecycle 与 Core injected resource bundle truth；本 FR 只声明 Adapter capability 的 lifecycle expectation，不定义新的 lifecycle runtime。
  - formal spec 与实现 PR 必须分离；`#313` 不修改 runtime、tests、adapter 实现或 validator 代码。

## GWT 验收场景

### 场景 1：合法 requirement 声明

Given `adapter_key=xhs` 的 `AdapterCapabilityRequirement` 声明 `capability=content_detail`、`operation=content_detail_by_url`、`target_type=url`、`collection_mode=hybrid`，且 `resource_requirement` 使用 `FR-0027` 合法 declaration 与 proof binding  
When manifest fixture validator 或 spec review 消费该 requirement  
Then requirement 必须被视为合法声明输入，可进入后续 `#314/#315` 实现工作

### 场景 2：资源 profile proof 不一致

Given `AdapterCapabilityRequirement.resource_requirement` 中某个 profile 的 `evidence_refs` 无法唯一命中与 `adapter_key`、`capability`、execution slice 和 profile tuple 完全一致的 `ApprovedSharedResourceRequirementProfileEvidenceEntry`  
When requirement 被 validator 或 runtime admission 消费  
Then 它必须 fail-closed，并归类为 `invalid_resource_requirement`

### 场景 3：不能表达 provider offer

Given 一个合法 `AdapterCapabilityRequirement` 需要 `required + [account, proxy]` profile  
When 作者试图在同一 carrier 中加入 `provider_offer`、`provider_key` 或 `provider_selection` 字段  
Then spec review 或 validator 必须阻断该声明，因为 Provider offer 与 compatibility decision 不属于 `FR-0024`

### 场景 4：不能表达 profile fallback

Given 一个 requirement 合法包含多个 `FR-0027` resource profiles  
When 作者试图给 profile 添加 `priority`、`fallback_order` 或 `preferred_profile`  
Then 该声明必须 fail-closed，因为多 profile 只表示合法集合，不表示排序、偏好或自动 fallback

### 场景 5：lifecycle 只能表达消费预期

Given requirement 声明该 capability 需要 Core 注入资源 bundle  
When 作者试图在 `lifecycle` 中声明 resource acquire/release 实现、账号池策略或 provider-owned lifecycle  
Then 该声明必须被视为越界，因为 lifecycle runtime truth 由 `FR-0010` / `FR-0012` 持有

### 场景 6：observability 不泄漏实现技术

Given requirement 需要记录 requirement id、profile key、proof refs 与 fail-closed 结果  
When 作者试图在 `observability` 中记录 Playwright、CDP、browser profile、network tier 或 provider fallback outcome  
Then 该声明必须被视为 contract violation，因为这些字段不是 Adapter capability requirement 的 canonical surface

### 场景 7：合法 requirement 不等于 compatibility approved

Given 某 Adapter 的 `AdapterCapabilityRequirement` 完全合法  
When 尚未存在 Provider offer 与 `FR-0026` compatibility decision  
Then 系统只能认为 Adapter requirement 已声明完成，不得推导出任何 Provider 已兼容或可绑定

## 异常与边界场景

- 异常场景：
  - 缺少 `execution_requirement`、`resource_requirement`、`evidence`、`lifecycle`、`observability` 或 `fail_closed` 时，必须视为 contract violation。
  - `execution_requirement` 与 `resource_requirement.capability` / `adapter_key` 不一致时，必须视为 contract violation。
  - `resource_requirement` 回退到旧单声明 `required_capabilities[]` 而非 `FR-0027` multi-profile carrier 时，必须视为 contract violation。
  - proof 不可解析、不唯一、不覆盖 declaration adapter 或不匹配 approved execution slice 时，必须 fail-closed。
- 边界场景：
  - 本 FR 允许 requirement 引用多个合法 resource profiles，但这些 profile 没有优先级、fallback、自动选择或 provider routing 语义。
  - 本 FR 允许 `observability` 描述可审计字段，但不批准 provider product、selector、transport、browser 或 network 技术字段进入 public requirement。
  - 本 FR 不关闭 `#296`；父 FR closeout 必须等待 formal spec、manifest fixture validator、reference adapter migration 与 GitHub 状态全部一致。
  - 本 FR 不把 legal requirement 外推为 legal compatibility；Provider offer 与 decision 由后续 FR 承接。

## 验收标准

- [ ] formal spec 明确冻结 `AdapterCapabilityRequirement` canonical carrier
- [ ] formal spec 明确 capability / execution requirement / resource profiles / evidence / lifecycle / observability / fail-closed 字段边界
- [ ] formal spec 明确消费 `FR-0027` 的 `AdapterResourceRequirementDeclarationV2` 与 `ApprovedSharedResourceRequirementProfileEvidenceEntry`
- [ ] formal spec 明确 proof 不可解析、不唯一、不对齐或不覆盖 adapter 时必须 fail-closed
- [ ] formal spec 明确禁止 Provider offer、compatibility decision、profile priority/fallback、新共享能力词汇与 runtime 实现
- [ ] formal spec 明确合法 Adapter requirement 不等于 Provider compatibility approved
- [ ] formal spec 为 `#314/#315/#316` 提供可执行进入条件

## 依赖与外部前提

- 外部依赖：
  - `FR-0027` 已合入主干并冻结 multi-profile resource requirement carrier、matcher 语义与 profile proof binding。
  - `FR-0021` 已冻结 adapter-owned provider port 只属于 Adapter 内部边界。
  - `FR-0010` / `FR-0012` 已冻结 resource lifecycle 与 Core injected resource bundle 边界。
- 上下游影响：
  - `#314` 必须基于本 FR 实现 manifest fixture validator / contract test 入口。
  - `#315` 必须基于本 FR 迁移小红书、抖音 reference adapter requirement baseline。
  - `#316` 必须汇总本 formal spec、validator、migration 与 GitHub 状态，完成父 FR `#296` closeout。
  - 后续 Provider offer 与 compatibility decision FR 必须把本 FR 作为 requirement input，而不是反向改写 requirement carrier。
