# FR-0026 contracts

## canonical carrier

- canonical decision：`AdapterProviderCompatibilityDecision`
- 目的：对一条 `AdapterCapabilityRequirement` 与一条 `ProviderCapabilityOffer` 执行 Adapter-bound compatibility decision，输出 `matched`、`unmatched` 或 `invalid_contract`。

## input contract

### required inputs

- `requirement`：来自 `FR-0024` 的合法 `AdapterCapabilityRequirement`
- `offer`：来自 `FR-0025` 的合法 `ProviderCapabilityOffer`
- `decision_context`：只包含 contract refs、decision id、contract version 与 `fail_closed`

### validation rules

- `requirement` 必须先满足 `FR-0024`。
- `requirement.resource_requirement` 与 proof binding 必须先满足 `FR-0027`。
- `offer` 必须先满足 `FR-0025`。
- `offer.resource_support` 与 proof binding 必须先满足 `FR-0027`。
- 本 contract 不定义、复制或改写 requirement / offer / resource profile carrier 本体。
- 任一输入不合法时，decision 必须 fail-closed 为 `invalid_contract`。

## adapter and execution binding

### validation rules

- `requirement.adapter_key` 必须等于 `offer.adapter_binding.adapter_key`。
- `requirement.capability` 必须等于 `offer.capability_offer.capability`。
- `requirement.execution_requirement.operation` 必须等于 `offer.capability_offer.operation`。
- `requirement.execution_requirement.target_type` 必须等于 `offer.capability_offer.target_type`。
- `requirement.execution_requirement.collection_mode` 必须等于 `offer.capability_offer.collection_mode`。
- 当前 approved slice 只允许 `content_detail + content_detail_by_url + url + hybrid`。
- adapter 或 execution slice 不一致时，decision status 必须为 `invalid_contract`，不得继续 profile matching。

## profile matching

### validation rules

- matching 只比较 `FR-0027` canonical tuple：`resource_dependency_mode + normalized_required_capabilities`。
- requirement profile 与 offer supported profile 都必须拥有唯一、可解析、覆盖当前 adapter、且与 capability / execution slice / tuple 完全一致的 `FR-0027` proof。
- 当至少一个 requirement profile 与 offer supported profile 的 canonical tuple 完全一致时，返回 `matched`。
- 当 requirement 与 offer 都合法，但没有任何 requirement profile 被 offer supported profile 满足时，返回 `unmatched`。
- 同名 `profile_key` 不构成 compatibility；只有 canonical tuple 与 proof coverage 完全成立才可匹配。
- 不允许 partial match、score、rank、priority、fallback、preferred profile 或自动选择。

## decision status

### `matched`

- 含义：合法 requirement 与合法 Adapter-bound offer 在同一 Adapter、同一 approved execution slice 下存在至少一个 canonical tuple 完全一致的 resource profile。
- 输出要求：
  - `matched_profiles` 非空。
  - `error` 必须为空。
  - `fail_closed=true`。
- 非含义：
  - 不代表 selected provider。
  - 不代表 Core routing。
  - 不代表 priority、score、fallback 或自动执行策略。
  - 不代表真实 provider 产品正式支持、SLA 或 marketplace listing。

### `unmatched`

- 含义：合法 requirement 与合法 Adapter-bound offer 在同一 Adapter、同一 approved execution slice 下没有可满足的 resource profile 交集。
- 输出要求：
  - `matched_profiles` 必须为空。
  - `error` 必须为空。
  - 不得把合法不兼容误报为 input contract violation。
- 非含义：
  - 不代表 requirement 违法。
  - 不代表 offer 违法。
  - 不触发 provider fallback 或自动尝试其它 provider。

### `invalid_contract`

- 含义：输入、proof、adapter binding、execution slice、decision carrier 或 no-leakage guard 存在 contract violation。
- 输出要求：
  - `matched_profiles` 必须为空。
  - `error` 必须存在。
  - `failure_category=runtime_contract`。
  - `adapter_mapping_required=true`。
- 允许错误码：
  - `invalid_requirement_contract`
  - `invalid_provider_offer_contract`
  - `invalid_compatibility_contract`
  - `provider_leakage_detected`

## no-leakage contract

### allowed

- Adapter-bound decision evidence 可以记录：
  - `provider_key`
  - `offer_id`
  - `matched_profile_keys`
  - `proof_refs`
  - `decision_status`

### forbidden

- `AdapterProviderCompatibilityDecision` 顶层字段中出现 `provider_key` 或 `offer_id`。
- `CompatibilityDecisionObservability` 中出现 `provider_key` 或 `offer_id`。
- Core registry discovery 中出现 provider key、provider capability 或 provider registry entry。
- Core routing 中出现 selected provider、provider selector、routing policy、priority、score 或 fallback。
- TaskRecord 中新增 provider-specific public field。
- resource lifecycle 中新增 provider-owned lifecycle、resource supply、account pool、proxy pool 或 provider lease field。
- failed envelope 中新增 Core-facing provider category。
- Core-facing projection 嵌入完整 Adapter-bound decision evidence。

## invalid evidence contract

- `resource_profile_evidence_refs` 只记录已成功解析且满足 `FR-0027` 的 proof refs。
- `matched` / `unmatched` 时，`resource_profile_evidence_refs` 必须非空、去重，并与参与 decision 的 profile refs 对齐。
- `invalid_contract` 且 proof refs 为空、重复、不可解析或不唯一时，`resource_profile_evidence_refs` 可以为空。
- `invalid_contract` 时必须提供 `invalid_contract_evidence`，记录 `source_contract_ref`、`violated_rule` 与原始 `unresolved_refs`。
- 不得为了满足 evidence shape 伪造 proof ref 占位。

## fail-closed contract

- `fail_closed` 必须存在且必须为 `true`。
- 任一固定字段缺失、输入 contract 不合法、proof 不合法、adapter binding 不一致、execution slice 不一致、禁止字段出现或 provider leakage detected 时，必须返回 `invalid_contract`。
- 任何 ambiguity 都不得返回 `matched`。

## explicitly forbidden

- `selected_provider`
- `provider_selector`
- `provider_selection`
- `provider_routing`
- `routing_policy`
- `priority`
- `score`
- `rank`
- `fallback`
- `fallback_order`
- `preferred_profile`
- `marketplace_listing`
- `provider_product_support`
- Core provider registry / discovery / routing
- TaskRecord provider field
- provider resource supply / pool / lifecycle
- runtime implementation details
