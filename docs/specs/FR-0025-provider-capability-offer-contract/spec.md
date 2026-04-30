# FR-0025 Provider capability offer contract

## 关联信息

- item_key：`FR-0025-provider-capability-offer-contract`
- Issue：`#297`
- item_type：`FR`
- release：`v0.8.0`
- sprint：`2026-S21`

## 背景与目标

- 背景：`v0.8.0` 要把 Adapter + Provider 兼容性判断推进到可被 formal spec、manifest、SDK 与 validator 一致解释的阶段。`FR-0024` 已冻结 Adapter capability requirement，`FR-0027` 已冻结 multi-profile resource requirement 与 proof binding；在进入 `FR-0026` compatibility decision 前，Provider 侧也必须有唯一、可验证、可 fail-closed 的 offer carrier。
- 目标：冻结 `ProviderCapabilityOffer` 作为 Provider capability offer 的 canonical carrier，明确 provider key、adapter binding、capability offer、resource support、error carrier、version、evidence、lifecycle、observability 与 fail-closed 字段边界，使后续 `#320/#321/#322` 可以基于同一 offer truth 进入 manifest validator、SDK docs / evidence 与父 FR closeout。

## 范围

- 本次纳入：
  - 冻结 `ProviderCapabilityOffer` canonical carrier。
  - 冻结 `provider_key`、`adapter_binding`、`capability_offer`、`resource_support`、`error_carrier`、`version`、`evidence`、`lifecycle`、`observability` 与 `fail_closed` 字段边界。
  - 明确 offer 必须消费 `FR-0024` 的 `AdapterCapabilityRequirement` 作为后续 decision 输入语义，不反向改写 requirement carrier。
  - 明确 offer 的 resource support 必须消费 `FR-0027` 的 profile tuple、approved execution slice 与 proof binding 语义，不重新定义 matcher 或 profile approval。
  - 明确 Provider 仍是 Adapter-bound 能力；Provider offer 不进入 Core discovery、routing、registry、TaskRecord 或 resource lifecycle。
  - 明确 offer manifest / validator、SDK docs / evidence 与父 FR closeout 的进入条件。
- 本次不纳入：
  - `AdapterCapabilityRequirement x ProviderCapabilityOffer` compatibility decision 规则。
  - provider selector、priority、fallback、排序、打分、marketplace 或真实 provider 产品支持。
  - Core provider registry、Core provider discovery、Core routing、provider runtime implementation 或 provider manifest validator 实现。
  - 新共享能力词汇、新 resource lifecycle runtime 或 provider resource supply model。
  - 关闭父 FR `#297`。

## 需求说明

- 功能需求：
  - `ProviderCapabilityOffer` 必须是 `v0.8.0` 及之后 Provider capability offer 的唯一 canonical carrier；不得并行维护第二套 manifest-only、SDK-only 或 provider-private offer 模型。
  - `ProviderCapabilityOffer` 至少必须固定以下字段：
    - `provider_key`
    - `adapter_binding`
    - `capability_offer`
    - `resource_support`
    - `error_carrier`
    - `version`
    - `evidence`
    - `lifecycle`
    - `observability`
    - `fail_closed`
  - `provider_key` 必须是非空稳定字符串，只在声明的 `adapter_binding.adapter_key` 下有意义；不得被解释为 Core registry key、跨 adapter 全局路由 key、marketplace listing 或 provider 产品认证。
  - `adapter_binding` 必须表达 Provider offer 绑定到哪个 Adapter 与哪个 adapter-owned provider port。当前只允许 `binding_scope=adapter_bound`，且必须包含非空 `adapter_key`；不得声明 `core_bound`、`global_provider`、跨 adapter 共享绑定或 Core-facing provider SDK。
  - `capability_offer` 必须表达 Provider 声称可为该 Adapter 提供的 adapter-facing capability。当前 `v0.8.0` approved slice 只允许：
    - `capability=content_detail`
    - `operation=content_detail_by_url`
    - `target_type=url`
    - `collection_mode=hybrid`
  - `resource_support` 必须表达 Provider 对该 capability offer 的资源前提或资源容忍边界，并且只能消费 `FR-0027` 已冻结的 profile tuple 与 proof binding 语义。当前允许引用的 profile 组合空间只来自 `none`、`required + [account]`、`required + [proxy]`、`required + [account, proxy]`，但是否与某个 Adapter requirement 兼容必须留给 `FR-0026`。
  - `resource_support.supported_profiles` 可以声明 Provider offer 声称支持的一组 resource profile tuple；每个 profile 必须带有 `profile_key`、`resource_dependency_mode`、`required_capabilities` 与 `evidence_refs`，并按 `FR-0027` 的 canonicalization、single proof binding、approved execution slice、adapter coverage proof binding 与 fail-closed 口径验证。
  - `resource_support.supported_profiles[*].evidence_refs` 命中的 `FR-0027` approved profile proof 除了必须与 profile tuple 和 approved execution slice 完全一致，还必须满足该 proof 的 `reference_adapters` 显式覆盖当前 `adapter_binding.adapter_key`；不得借用只批准给其它 Adapter 的 shared profile proof。
  - `resource_support` 不得表达 profile priority、preferred profile、fallback order、自动选择、资源 acquisition / release、账号池、代理池、provider-owned resource lifecycle 或 provider resource supply。
  - `error_carrier` 必须表达 Provider offer 侧错误如何被 Adapter 映射到既有 Adapter / runtime failed envelope。当前固定允许 `invalid_provider_offer`、`provider_unavailable` 与 `provider_contract_violation` 作为 offer / provider 层内部错误口径；外显到 Core 时必须经 Adapter 映射，不得新增 Core-facing provider failed envelope category。
  - `version` 必须表达 offer carrier 的语义版本与适用边界，当前固定 `contract_version=v0.8.0`，且必须声明 `requirement_contract_ref=FR-0024`、`resource_profile_contract_ref=FR-0027`；不得用 version 字段承诺真实 provider 产品支持、SLA、市场发布或 runtime rollout。
  - `evidence` 必须把 offer 声明回指到可审查、可迁移、可验证的证据。当前至少必须包含：
    - `provider_offer_evidence_refs`：回指本 FR、后续 offer manifest fixture / validator、SDK docs 或 closeout evidence。
    - `resource_profile_evidence_refs`：与 `resource_support.supported_profiles[*].evidence_refs` 对齐，并最终唯一命中 `FR-0027` 中 tuple / execution slice 完全一致且 `reference_adapters` 覆盖当前 `adapter_binding.adapter_key` 的 approved profile proof。
    - `adapter_binding_evidence_refs`：证明该 Provider offer 只通过 Adapter-owned provider port 进入系统的文档或实现证据。
  - `lifecycle` 必须表达 Provider offer 对既有 Adapter-owned provider port 与 Core resource lifecycle 的消费边界，而不是定义新的 lifecycle store。当前只允许声明：
    - Provider 由 Adapter 调用，不由 Core 调用。
    - Provider 只消费 Adapter 传入的已解析执行上下文与资源 bundle 视图。
    - Provider 错误必须由 Adapter 映射到既有失败语义。
  - `observability` 必须表达 offer 可被追踪与审计的最小字段，当前至少覆盖 offer id、provider key、adapter key、capability、operation、profile keys、proof refs、contract version 与 validation outcome fields；不得进入 Core registry discovery、TaskRecord provider field、selector/routing/fallback outcome 或技术链路字段。
  - `fail_closed` 必须固定为显式 `true`。任何 offer 缺字段、字段不一致、profile proof 不可解析、resource support 不合法、approved slice 越界、adapter binding 越界或出现被禁止字段时，都不得被宽松视为可进入 compatibility decision。
  - 合法 `ProviderCapabilityOffer` 只回答“某 Provider 在某 Adapter 边界内声明自己提供了什么 offer 输入”；不回答“它是否满足某个 Adapter requirement”，也不回答“Core 应该选择哪个 Provider”。
- 契约需求：
  - 以下情况必须归类为 provider offer contract violation，并映射到 `runtime_contract + invalid_provider_offer` 或等价的 spec/validator 阻断口径：
    - 缺少固定字段，或 `fail_closed` 不是 `true`
    - `provider_key` 为空、不稳定，或被声明为 Core / global provider registry key
    - `adapter_binding.adapter_key` 为空，或 `binding_scope` 不是 `adapter_bound`
    - `capability_offer` 超出 `content_detail_by_url + url + hybrid` approved slice
    - `resource_support` 未消费 `FR-0027` profile tuple / proof binding，或包含 profile priority、fallback、selection、resource supply、acquire/release、pooling 语义
    - `resource_profile_evidence_refs` 与 `resource_support.supported_profiles[*].evidence_refs` 不一致、不可唯一解析、未处于 `FR-0027` approved execution slice，或命中的 proof 未在 `reference_adapters` 中覆盖当前 `adapter_binding.adapter_key`
    - `version` 未声明 `v0.8.0` offer contract boundary，或把 version 字段扩写成 provider 产品支持承诺
    - `lifecycle` 试图定义 Core provider discovery、Core routing、provider-owned lifecycle 或跨 adapter resource scheduling
    - `observability` 暴露 provider selector、priority、fallback outcome、marketplace metadata、Playwright、CDP、browser profile、network tier、transport 等技术字段
    - carrier 出现 `compatibility_decision`、`selected_provider`、`routing_policy`、`priority`、`fallback`、`marketplace_listing`、`provider_product_support` 或同义字段
  - 以下情况不得被本 FR 判定为 compatibility 通过：
    - Provider offer 合法，但尚无 Adapter requirement。
    - Provider offer 合法，且 Adapter requirement 合法，但二者尚未经过 `FR-0026` compatibility decision。
    - Provider offer 声明了某个 resource profile，与 Adapter requirement 中存在同名或同 tuple profile。
  - `ProviderCapabilityOffer` 只回答“Adapter-bound Provider 声明自己提供什么 capability offer”；不回答“哪个 Provider 可满足哪个 Adapter requirement”。
- 非功能需求：
  - contract 必须 fail-closed，任何无法证明字段、profile、证据、binding 或 version 一致的情况都不能进入后续 decision-ready 状态。
  - formal spec 必须保持 Core / Adapter / Provider 边界：Core 继续只调用 Adapter，Provider 只能作为 Adapter-bound 能力参与后续兼容性判断。
  - formal suite 必须让 reviewer、guardian、`#320` validator、`#321` SDK docs / evidence 与 `#322` closeout 直接消费，不依赖会话上下文补足隐藏前提。

## 约束

- 阶段约束：
  - 本 FR 服务 `v0.8.0` Provider capability offer 声明契约，不提前完成 compatibility decision、真实 provider 验证样本或外部 provider 产品支持。
  - 当前 approved slice 只覆盖 Adapter-bound `content_detail_by_url + url + hybrid` offer 输入面。
  - 新执行路径、新 target、新 collection mode、新共享能力词汇或真实 provider 产品支持必须另建 evidence / formal spec follow-up。
- 架构约束：
  - `FR-0021` 继续持有 adapter-owned provider port 边界；本 FR 不把 provider port 升格为 Core-facing provider SDK。
  - `FR-0024` 继续持有 Adapter capability requirement truth；本 FR 只声明 offer 输入，不反向改写 requirement carrier。
  - `FR-0027` 继续持有 resource profile / proof binding truth；本 FR 只消费它，不重写 profile tuple、matcher `one-of` 或 approval proof。
  - `FR-0010` / `FR-0012` 继续持有 resource lifecycle 与 Core injected resource bundle truth；本 FR 不定义新的 provider resource lifecycle。
  - formal spec 与实现 PR 必须分离；`#319` 不修改 runtime、tests、adapter 实现、manifest validator 或 contract test 代码。

## GWT 验收场景

### 场景 1：合法 Provider offer 声明

Given `provider_key=native_xhs_detail_provider` 的 `ProviderCapabilityOffer` 声明 `adapter_binding.adapter_key=xhs`、`binding_scope=adapter_bound`、`capability=content_detail`、`operation=content_detail_by_url`、`target_type=url`、`collection_mode=hybrid`，且 `resource_support.supported_profiles` 使用 `FR-0027` 合法 profile tuple 与 proof binding  
When offer manifest validator 或 spec review 消费该 offer  
Then offer 必须被视为合法 Provider offer 输入，可进入后续 `#320/#321/#322` 实现工作

### 场景 2：合法 offer 不等于 compatibility approved

Given 一个合法 `ProviderCapabilityOffer` 声明支持 `required + [account, proxy]` profile  
When 尚未存在 `FR-0026` compatibility decision  
Then 系统只能认为 Provider offer 已声明完成，不得推导出它满足任何 `AdapterCapabilityRequirement`

### 场景 2A：profile proof 必须覆盖当前 Adapter

Given `adapter_binding.adapter_key=external_adapter` 的 Provider offer 声明了 `required + [account]` resource profile，且该 profile 的 `evidence_refs` 命中一个只在 `reference_adapters=[xhs, douyin]` 中批准的 `FR-0027` approved profile proof
When offer manifest validator 或 spec review 校验该 offer
Then 该 offer 必须按 `invalid_provider_offer` fail-closed，因为命中的 proof 未覆盖当前 `adapter_binding.adapter_key`

### 场景 3：Provider key 不能进入 Core discovery

Given Provider offer 包含稳定 `provider_key` 与 `adapter_binding.adapter_key`  
When Registry discovery、TaskRecord、Core routing 或 resource lifecycle 消费 Adapter public surface  
Then 这些 Core-facing surface 不得出现 `provider_key`、provider capability、provider selector 或 provider routing 字段

### 场景 4：resource support 不能表达 fallback

Given Provider offer 合法包含多个 `FR-0027` resource profiles  
When 作者试图给这些 profile 添加 `priority`、`fallback_order`、`preferred_profile` 或 `selected_profile`  
Then 该 offer 必须 fail-closed，因为多 profile 只表示 offer 声明集合，不表示排序、偏好、自动 fallback 或 compatibility decision

### 场景 5：adapter binding 必须保持 Adapter-bound

Given Provider offer 声明 `binding_scope=adapter_bound` 并绑定 `adapter_key=douyin`  
When 作者试图把同一 offer 声明为 `core_bound`、`global_provider`、跨 adapter 共享 provider 或 marketplace entry  
Then spec review 或 validator 必须阻断该声明，因为 Provider offer 不能越过 Adapter-owned provider port 边界

### 场景 6：error carrier 必须经 Adapter 映射

Given Provider 内部执行返回 `provider_unavailable`  
When Adapter 把 Provider 结果映射为 Syvert failed envelope  
Then Core-facing 错误必须继续使用既有 Adapter / runtime failed envelope 语义，不得新增 provider-specific Core failed envelope category

### 场景 7：observability 不泄漏 selector 或技术实现

Given offer 需要记录 offer id、provider key、adapter key、profile keys、proof refs 与 validation outcome  
When 作者试图在 `observability` 中记录 provider fallback outcome、routing policy、marketplace metadata、Playwright、CDP、browser profile、network tier 或 transport 字段  
Then 该声明必须被视为 contract violation，因为这些字段不是 Provider capability offer 的 canonical surface

## 异常与边界场景

- 异常场景：
  - 缺少 `provider_key`、`adapter_binding`、`capability_offer`、`resource_support`、`error_carrier`、`version`、`evidence`、`lifecycle`、`observability` 或 `fail_closed` 时，必须视为 contract violation。
  - `adapter_binding.binding_scope` 不是 `adapter_bound`，或 `adapter_binding.adapter_key` 为空时，必须视为 contract violation。
  - `capability_offer` 把 approved slice 外推到搜索、评论、发布、通知、互动、账号管理、非 URL target 或非 hybrid collection mode 时，必须 fail-closed。
  - `resource_support` 回退到 provider-private resource list、旧单声明模型、resource supply model 或未经 `FR-0027` 批准的 profile tuple 时，必须视为 contract violation。
  - proof 不可解析、不唯一、不匹配 approved execution slice、不匹配 profile tuple，或 proof 的 `reference_adapters` 未覆盖当前 `adapter_binding.adapter_key` 时，必须 fail-closed。
  - `version` 缺失 `FR-0024` / `FR-0027` contract refs，或把版本扩写成产品发布、市场上架、SLA 或真实 provider 支持承诺时，必须视为 contract violation。
- 边界场景：
  - 本 FR 允许 offer 声明多个合法 resource profiles，但这些 profile 没有优先级、fallback、自动选择、compatibility approval 或 provider routing 语义。
  - 本 FR 允许 `provider_key` 作为 Adapter-bound offer identity，但不批准 Core provider registry、global provider identity、marketplace listing 或跨 adapter routing。
  - 本 FR 允许 `error_carrier` 定义 offer 内部错误口径，但所有 Core-facing 失败仍必须经 Adapter 映射到既有 failed envelope。
  - 本 FR 不关闭 `#297`；父 FR closeout 必须等待 formal spec、offer manifest validator、SDK docs / evidence 与 GitHub 状态全部一致。
  - 本 FR 不把 legal offer 外推为 legal compatibility；compatibility decision 由 `FR-0026` 承接。

## 验收标准

- [ ] formal spec 明确冻结 `ProviderCapabilityOffer` canonical carrier
- [ ] formal spec 明确 provider key / adapter binding / capability offer / resource support / error carrier / version / evidence / lifecycle / observability / fail-closed 字段边界
- [ ] formal spec 明确消费 `FR-0024` 的 `AdapterCapabilityRequirement` 作为后续 decision 输入语义，但不反向改写 requirement carrier
- [ ] formal spec 明确消费 `FR-0027` 的 resource profile tuple、approved execution slice 与 proof binding，不重写 matcher / approval proof
- [ ] formal spec 明确 proof 不可解析、不唯一、不对齐、未覆盖当前 adapter 或越过 approved slice 时必须 fail-closed
- [ ] formal spec 明确禁止 compatibility decision、provider selector、priority、fallback、marketplace、真实 provider 产品支持、Core discovery / routing 与 runtime 实现
- [ ] formal spec 明确合法 Provider offer 不等于 Provider compatibility approved
- [ ] formal spec 为 `#320/#321/#322` 提供可执行进入条件

## 依赖与外部前提

- 外部依赖：
  - `FR-0024` 已冻结 `AdapterCapabilityRequirement`，作为后续 compatibility decision 的 Adapter requirement input。
  - `FR-0027` 已冻结 multi-profile resource requirement carrier、matcher 语义与 profile proof binding。
  - `FR-0021` 已冻结 adapter-owned provider port 只属于 Adapter 内部边界。
  - `FR-0010` / `FR-0012` 已冻结 resource lifecycle 与 Core injected resource bundle 边界。
- 上下游影响：
  - `#320` 必须基于本 FR 实现 offer manifest fixture / validator 入口。
  - `#321` 必须基于本 FR 补齐 SDK docs / evidence，证明 Provider offer 如何作为 Adapter-bound 能力被声明。
  - `#322` 必须汇总本 formal spec、validator、docs / evidence 与 GitHub 状态，完成父 FR `#297` closeout。
  - `FR-0026` 必须把本 FR 作为 Provider offer input，而不是反向改写 offer carrier。
