# FR-0026 Adapter provider compatibility decision

## 关联信息

- item_key：`FR-0026-adapter-provider-compatibility-decision`
- Issue：`#298`
- item_type：`FR`
- release：`v0.8.0`
- sprint：`2026-S21`

## 背景与目标

- 背景：`v0.8.0` 已分别冻结 `FR-0024` 的 `AdapterCapabilityRequirement`、`FR-0025` 的 `ProviderCapabilityOffer` 与 `FR-0027` 的 resource profile / proof binding。后续 runtime、no-leakage guard、docs / evidence 与父 FR closeout 需要一个单一、可验证、fail-closed 的 compatibility decision contract，回答“某个 Adapter requirement 与某个 Adapter-bound Provider offer 是否兼容”。
- 目标：冻结 `AdapterProviderCompatibilityDecision` canonical carrier、输入验证、输出状态、`matched` / `unmatched` / `invalid_contract` 边界、fail-closed 与 no-leakage 约束，使后续 `#324/#325/#326/#327` 可以只消费已批准 requirement / offer / resource profile truth，不重新定义输入 carrier 或 provider routing。

## 范围

- 本次纳入：
  - 冻结 `AdapterCapabilityRequirement x ProviderCapabilityOffer -> AdapterProviderCompatibilityDecision` 的 decision contract。
  - 明确 decision 输入必须消费 `FR-0024`、`FR-0025` 与 `FR-0027`，不得定义 requirement / offer / resource profile carrier 本体。
  - 明确 `matched`、`unmatched`、`invalid_contract` 三类 decision status 的边界。
  - 明确 Adapter identity、capability、execution slice、resource profile support 与 proof coverage 的匹配规则。
  - 明确 invalid requirement、invalid offer、cross-adapter offer、profile proof 不合法、approved slice 越界与禁止字段出现时必须 fail-closed。
  - 明确 provider 信息不得泄漏到 Core routing、registry discovery、TaskRecord 或 resource lifecycle。
  - 明确 runtime decision、no-leakage guard、docs / evidence 与 parent closeout 的进入条件。
- 本次不纳入：
  - `AdapterCapabilityRequirement` carrier 本体。
  - `ProviderCapabilityOffer` carrier 本体。
  - `AdapterResourceRequirementDeclarationV2`、profile tuple、matcher `one-of` 或 proof binding 本体。
  - provider selector、priority、自动 fallback、排序、打分、marketplace 或真实 provider 产品支持。
  - Core provider registry、Core provider discovery、Core routing、provider runtime implementation 或 contract test 实现。
  - reference adapter migration、SDK docs evidence 或父 FR `#298` closeout。

## 需求说明

- 功能需求：
  - `AdapterProviderCompatibilityDecision` 必须是 `v0.8.0` 及之后 Adapter requirement 与 Adapter-bound Provider offer 兼容性判断的唯一 canonical carrier；不得并行维护 manifest-only、SDK-only、runtime-only 或 provider-private decision 模型。
  - decision 输入必须包含一条合法 `AdapterCapabilityRequirement` 与一条合法 `ProviderCapabilityOffer`。
  - requirement 合法性必须完全消费 `FR-0024`；requirement 中 `resource_requirement` 与 profile proof 合法性必须完全消费 `FR-0027`。
  - offer 合法性必须完全消费 `FR-0025`；offer 中 `resource_support` 与 profile proof 合法性必须完全消费 `FR-0027`。
  - decision 不得扩写 requirement 或 offer 字段，也不得以 decision 结果反向修正 requirement / offer / profile proof。
  - decision 输入必须处于同一 Adapter 边界：`requirement.adapter_key` 必须等于 `offer.adapter_binding.adapter_key`。
  - decision 输入必须处于同一 approved capability slice：requirement 的 `capability + operation + target_type + collection_mode` 必须与 offer 的 `capability_offer` 完全一致。当前 approved slice 只允许 `content_detail + content_detail_by_url + url + hybrid`。
  - decision 必须比较 requirement resource profiles 与 offer supported profiles 的 canonical tuple。只要存在任一合法 requirement profile，其 `resource_dependency_mode + normalized_required_capabilities` 与任一合法 offer supported profile 完全一致，且两侧 proof 都满足 `FR-0027` 对当前 adapter、capability 与 approved execution slice 的要求，decision 必须返回 `matched`。
  - 若 requirement 与 offer 各自合法、Adapter / capability / execution slice 完全一致，但不存在任何 requirement profile 被 offer supported profiles 满足，decision 必须返回 `unmatched`。
  - 若 requirement 或 offer 任一输入不合法、字段不一致、proof 不可解析、不唯一、不覆盖当前 adapter、越过 approved slice、出现禁止字段或违反 no-leakage 约束，decision 必须返回 `invalid_contract`，不得宽松降级为 `unmatched`。
  - `matched` 只表达“该 Adapter-bound Provider offer 可满足该 Adapter requirement 的 formal compatibility decision”；它不表达 provider selector、优先级、排序、自动 fallback、Core routing 或真实 provider 产品支持。
  - `unmatched` 只表达“两个合法输入在资源 profile 支持上没有可满足交集”；它不代表输入 contract 违法，也不允许 runtime 自动尝试其它 provider。
  - `invalid_contract` 必须携带最小错误口径，区分 `invalid_requirement_contract`、`invalid_provider_offer_contract`、`invalid_compatibility_contract` 与 `provider_leakage_detected`，并继续映射到既有 Adapter / runtime failed envelope，不新增 Core-facing provider failed envelope category。
  - decision 顶层字段与 observability 不得携带 `provider_key` 或 `offer_id`；provider identity 只允许出现在 Adapter-bound `CompatibilityDecisionEvidence.adapter_bound_provider_evidence`，且该 evidence 不得被复制到 Core-facing registry、TaskRecord、routing 或 resource lifecycle surface。
  - `invalid_contract` 必须可在 proof refs 为空、重复、不可解析或不唯一时构造；此时 `resource_profile_evidence_refs` 只记录已成功解析的 proof refs，违法原因必须进入 `invalid_contract_evidence`，不得伪造 proof ref 占位。
  - `invalid_contract` 必须可在 adapter key 不一致、capability / execution slice 不一致、approved slice 越界或 requirement / offer evidence 缺失时构造；此时 canonical decision 的共同 `adapter_key`、共同 `capability`、共同 `execution_slice` 或 resolved evidence refs 可以为空，实际冲突值与缺失原因必须进入 `invalid_contract_evidence`。
  - `fail_closed` 必须固定为显式 `true`。任何无法证明输入、profile、proof、adapter binding、capability slice 或 no-leakage 一致的情况，都不得返回 `matched`。
- 契约需求：
  - 以下情况必须归类为 `invalid_contract`：
    - requirement 不满足 `FR-0024` 或其 resource profile 不满足 `FR-0027`
    - offer 不满足 `FR-0025` 或其 resource support 不满足 `FR-0027`
    - requirement 与 offer 的 adapter key 不一致
    - requirement 与 offer 的 capability、operation、target_type 或 collection_mode 不一致
    - 任一输入或 decision surface 出现 selector、priority、score、fallback、routing、marketplace、provider product support、resource supply、provider-owned lifecycle 或 runtime 技术字段
    - 任一 proof 不可解析、不唯一、不匹配 tuple / execution slice，或 `reference_adapters` 未覆盖当前 adapter
    - decision 试图把 provider identity 写入 Core registry discovery、Core routing、TaskRecord 或 resource lifecycle
  - 以下情况必须归类为 `unmatched`：
    - requirement 合法、offer 合法、adapter key 与 approved execution slice 完全一致，但 offer supported profiles 没有满足任何 requirement resource profile
  - 以下情况必须归类为 `matched`：
    - requirement 合法、offer 合法、adapter key 与 approved execution slice 完全一致，且至少一个 requirement profile 与 offer supported profile 的 canonical tuple 完全一致
  - 以下情况不得被本 FR 判定为 `matched`：
    - 合法 requirement 与合法 offer 属于不同 adapter
    - 合法 requirement 与合法 offer 属于不同 execution slice
    - 合法 offer 只声明同名 profile_key，但 canonical tuple 或 proof coverage 不匹配
    - 合法输入需要通过 priority、fallback、score 或自动选择才能成立
- 非功能需求：
  - contract 必须 fail-closed，任何 ambiguity、字段漂移、proof 漂移或 provider leakage 都不能返回 `matched`。
  - formal spec 必须保持 Core / Adapter / Provider 边界：Core 继续只调用 Adapter，Provider 只能作为 Adapter-bound 能力参与 compatibility decision。
  - formal suite 必须让 reviewer、guardian、`#324` runtime、`#325` no-leakage guard、`#326` docs / evidence 与 `#327` parent closeout 直接消费，不依赖会话上下文补足隐藏前提。

## 约束

- 阶段约束：
  - 本 FR 服务 `v0.8.0` compatibility decision contract，不提前完成 runtime、no-leakage guard、docs / evidence、真实 provider 样本或父 FR closeout。
  - 当前 approved slice 只覆盖 Adapter-bound `content_detail_by_url + url + hybrid` compatibility decision。
  - 新执行路径、新 target、新 collection mode、新共享能力词汇或真实 provider 产品支持必须另建 evidence / formal spec follow-up。
- 架构约束：
  - `FR-0024` 继续持有 Adapter capability requirement truth；本 FR 只消费 requirement input，不反向改写 requirement carrier。
  - `FR-0025` 继续持有 Provider capability offer truth；本 FR 只消费 offer input，不反向改写 offer carrier。
  - `FR-0027` 继续持有 resource profile、matcher `one-of` 与 proof binding truth；本 FR 只消费 canonical tuple 与 proof validity，不重写 matcher 或 proof carrier。
  - `FR-0021` 继续持有 adapter-owned provider port 边界；本 FR 不把 provider port 升格为 Core-facing provider SDK。
  - `FR-0010` / `FR-0012` 继续持有 resource lifecycle 与 Core injected resource bundle truth；本 FR 不定义新的 provider lifecycle 或 resource supply runtime。
  - formal spec 与实现 PR 必须分离；`#323` 不修改 runtime、tests、scripts、adapter 实现、validator 或 guard 代码。

## GWT 验收场景

### 场景 1：合法输入返回 matched

Given `adapter_key=xhs` 的 `AdapterCapabilityRequirement` 合法声明 `content_detail_by_url + url + hybrid`，且 `ProviderCapabilityOffer` 合法绑定 `adapter_binding.adapter_key=xhs` 并支持 `required + [account]` profile
When requirement 中至少一个合法 resource profile 的 canonical tuple 与 offer supported profile 完全一致，且两侧 proof 都覆盖 `xhs`
Then decision 必须返回 `matched`，并记录命中的 requirement / offer profile key 与 proof refs

### 场景 2：合法输入但 profile 无交集返回 unmatched

Given requirement 合法需要 `required + [account, proxy]` profile，offer 合法只支持 `required + [account]` profile
When adapter key、capability 与 approved execution slice 均完全一致
Then decision 必须返回 `unmatched`，不得误报为 `invalid_contract`

### 场景 3：Adapter 边界不一致返回 invalid_contract

Given requirement 合法属于 `adapter_key=xhs`，offer 合法绑定 `adapter_binding.adapter_key=douyin`
When compatibility decision 消费这两个输入
Then decision 必须 fail-closed 返回 `invalid_contract`，因为 Adapter-bound Provider offer 不能跨 Adapter 被借用

### 场景 4：execution slice 不一致返回 invalid_contract

Given requirement 与 offer 各自字段完整
When requirement 的 `operation`、`target_type` 或 `collection_mode` 与 offer 的 `capability_offer` 不一致，或任一侧越过 `content_detail_by_url + url + hybrid`
Then decision 必须返回 `invalid_contract`，不得进行 profile 匹配

### 场景 5：proof 未覆盖当前 Adapter 返回 invalid_contract

Given requirement 或 offer 的 profile proof 命中一个未在 `reference_adapters` 中覆盖当前 adapter 的 `FR-0027` approved profile proof
When decision 校验输入
Then decision 必须返回 `invalid_contract`，不得因为 tuple 名称相同而返回 `matched`

### 场景 6：禁止 selector / fallback / score

Given requirement 与 offer 都合法
When decision carrier 或输入中出现 `priority`、`score`、`fallback_order`、`selected_provider`、`routing_policy` 或同义字段
Then decision 必须返回 `invalid_contract`，因为 FR-0026 不批准 provider selector、排序、打分或自动 fallback

### 场景 7：provider 信息不得泄漏到 Core surface

Given decision 返回 `matched`，并在 Adapter-bound evidence 中记录 `provider_key`
When Core registry discovery、Core routing、TaskRecord 或 resource lifecycle surface 被生成或审计
Then 这些 Core-facing surface 不得出现 provider key、provider selector、provider routing、provider profile 或 provider lifecycle 字段

### 场景 8：matched 不等于真实 provider 产品支持

Given decision 返回 `matched`
When docs、SDK 或 closeout evidence 描述该结果
Then 它只能表达 Adapter-bound compatibility approved，不得声明任何真实 provider 产品正式支持、SLA、marketplace listing 或 Core 可直接调用 provider

## 异常与边界场景

- 异常场景：
  - requirement 缺字段、`fail_closed != true`、resource requirement 不合法或违反 `FR-0024` 禁止字段时，decision 必须返回 `invalid_contract`。
  - offer 缺字段、`fail_closed != true`、adapter binding 不合法、resource support 不合法或违反 `FR-0025` 禁止字段时，decision 必须返回 `invalid_contract`。
  - proof refs 为空、重复、不可解析、不唯一、不匹配 tuple / execution slice，或未覆盖当前 adapter 时，decision 必须返回 `invalid_contract`。
  - decision 输入合法但没有 resource profile 交集时，必须返回 `unmatched`，不得把合法不兼容误报为 contract violation。
  - decision 顶层字段、observability 或 Core-facing projection 试图携带 provider key、offer id 或 provider selection 时，必须返回 `invalid_contract` 或被 no-leakage guard 阻断。
- 边界场景：
  - 本 FR 允许 decision 在 Adapter-bound evidence 中记录 provider key、offer id 与 matched profile keys，但这些信息不得成为 decision 顶层字段、observability、Core-facing routing 或 persistence contract。
  - 本 FR 要求 Core-facing projection 只能暴露无 provider 的 status / error 摘要；不得嵌入完整 `AdapterProviderCompatibilityDecision` evidence。
  - 本 FR 允许一个 requirement 或 offer 声明多个合法 profile，但 matching 只判断集合满足性，不引入优先级、排序、fallback 或打分。
  - 本 FR 不把 `unmatched` 映射为 `invalid_provider_offer` 或 `invalid_resource_requirement`；合法但不兼容与输入违法必须保持可区分。
  - 本 FR 不关闭 `#298`；父 FR closeout 必须等待 formal spec、runtime decision、no-leakage guard、docs / evidence 与 GitHub 状态全部一致。

## 验收标准

- [ ] formal spec 明确冻结 `AdapterProviderCompatibilityDecision` canonical carrier
- [ ] formal spec 明确只消费 `FR-0024`、`FR-0025` 与 `FR-0027`，不定义 requirement / offer / resource profile carrier 本体
- [ ] formal spec 明确 `matched` / `unmatched` / `invalid_contract` 的可验证边界
- [ ] formal spec 明确 adapter key、capability、execution slice、resource profile tuple 与 proof coverage 的匹配规则
- [ ] formal spec 明确 fail-closed：非法输入、proof 漂移、禁止字段或 provider leakage 一律不得返回 `matched`
- [ ] formal spec 明确禁止 provider selector、priority、score、fallback、routing、marketplace、真实 provider 产品支持、Core discovery / routing 与 runtime 实现
- [ ] formal spec 明确 provider 信息不得泄漏到 Core routing、registry discovery、TaskRecord 或 resource lifecycle
- [ ] formal spec 为 `#324/#325/#326/#327` 提供可执行进入条件

## 依赖与外部前提

- 外部依赖：
  - `FR-0024` 已冻结 `AdapterCapabilityRequirement`，作为 Adapter-side decision input。
  - `FR-0025` 已冻结 `ProviderCapabilityOffer`，作为 Provider-side decision input。
  - `FR-0027` 已冻结 multi-profile resource requirement carrier、matcher `one-of`、canonical tuple 与 proof binding。
  - `FR-0021` 已冻结 adapter-owned provider port 只属于 Adapter 内部边界。
  - `FR-0010` / `FR-0012` 已冻结 resource lifecycle 与 Core injected resource bundle 边界。
- 上下游影响：
  - `#324` 必须基于本 FR 实现 compatibility decision runtime，并覆盖 `matched`、`unmatched` 与 `invalid_contract`。
  - `#325` 必须基于本 FR 实现 provider no-leakage guards，证明 provider 信息不进入 Core-facing surface。
  - `#326` 必须基于本 FR 补齐 docs / evidence，说明 Adapter-bound compatibility decision 的解释边界。
  - `#327` 必须汇总 formal spec、runtime、guard、docs / evidence 与 GitHub 状态，完成父 FR `#298` closeout。
