# FR-0026 数据模型

## AdapterProviderCompatibilityDecisionInput

- 作用：表达 compatibility decision 的 canonical 输入。
- 字段：
  - `requirement`
    - 类型：`AdapterCapabilityRequirement`
    - 来源：`FR-0024`
    - 约束：必须合法；其 `resource_requirement` 与 proof binding 必须满足 `FR-0027`。
  - `offer`
    - 类型：`ProviderCapabilityOffer`
    - 来源：`FR-0025`
    - 约束：必须合法；其 `resource_support` 与 proof binding 必须满足 `FR-0027`。
  - `decision_context`
    - 类型：`CompatibilityDecisionContext`
    - 约束：只表达 decision 追溯、contract refs 与 fail-closed 配置，不承载 routing、selector、priority、fallback 或 provider product metadata。

## CompatibilityDecisionContext

- 作用：表达 decision 执行时的最小上下文。
- 字段：
  - `decision_id`
    - 类型：`string`
    - 约束：非空、稳定；建议由 `adapter_key + provider_key + requirement_id + offer_id + contract_version` 派生。
  - `contract_version`
    - 类型：`string`
    - 允许值：当前固定 `v0.8.0`
  - `requirement_contract_ref`
    - 类型：`string`
    - 允许值：当前固定 `FR-0024`
  - `offer_contract_ref`
    - 类型：`string`
    - 允许值：当前固定 `FR-0025`
  - `resource_profile_contract_ref`
    - 类型：`string`
    - 允许值：当前固定 `FR-0027`
  - `provider_port_boundary_ref`
    - 类型：`string`
    - 允许值：当前固定 `FR-0021`
  - `fail_closed`
    - 类型：`boolean`
    - 约束：必须为 `true`
- 禁止语义：
  - provider selector / routing / priority / score / fallback
  - marketplace listing / provider product support / SLA
  - Core provider registry / discovery / routing
  - provider-owned resource lifecycle

## AdapterProviderCompatibilityDecision

- 作用：表达一组 requirement / offer 输入的 compatibility decision 结果。
- 字段：
  - `decision_id`
    - 类型：`string`
    - 约束：必须与 `decision_context.decision_id` 对齐。
  - `adapter_key`
    - 类型：`string`
    - 约束：必须同时等于 `requirement.adapter_key` 与 `offer.adapter_binding.adapter_key`；不一致时不得产生非错误 decision。
  - `provider_key`
    - 类型：`string`
    - 约束：来自 `offer.provider_key`；只允许在 Adapter-bound decision evidence 中出现，不得进入 Core-facing surface。
  - `capability`
    - 类型：`string`
    - 允许值：当前只允许 `content_detail`
  - `execution_slice`
    - 类型：`CompatibilityExecutionSlice`
    - 约束：当前必须且只能表达 `content_detail_by_url + url + hybrid`。
  - `decision_status`
    - 类型：`enum`
    - 允许值：`matched`、`unmatched`、`invalid_contract`
  - `matched_profiles`
    - 类型：`MatchedCompatibilityProfile[]`
    - 约束：当 `decision_status=matched` 时非空；当 `unmatched` 或 `invalid_contract` 时必须为空。
  - `error`
    - 类型：`CompatibilityDecisionError | null`
    - 约束：当 `invalid_contract` 时必须存在；当 `matched` 或 `unmatched` 时必须为空。
  - `evidence`
    - 类型：`CompatibilityDecisionEvidence`
    - 约束：必须回指 requirement、offer、resource profile proof 与 decision contract evidence。
  - `observability`
    - 类型：`CompatibilityDecisionObservability`
    - 约束：只表达 Adapter-bound decision 追踪字段；不得进入 Core-facing provider routing 或 persistence surface。
  - `no_leakage`
    - 类型：`CompatibilityNoLeakageAssertion`
    - 约束：必须证明 provider 信息不会进入 Core routing、registry discovery、TaskRecord 或 resource lifecycle。
  - `fail_closed`
    - 类型：`boolean`
    - 约束：必须为 `true`。

## CompatibilityExecutionSlice

- 作用：表达 decision 覆盖的 approved execution slice。
- 字段：
  - `operation`
    - 类型：`enum`
    - 允许值：当前只允许 `content_detail_by_url`
  - `target_type`
    - 类型：`enum`
    - 允许值：当前只允许 `url`
  - `collection_mode`
    - 类型：`enum`
    - 允许值：当前只允许 `hybrid`

## MatchedCompatibilityProfile

- 作用：表达一个合法 requirement profile 被 offer supported profile 满足的证据。
- 字段：
  - `requirement_profile_key`
    - 类型：`string`
    - 约束：必须来自 `requirement.resource_requirement.resource_requirement_profiles[*].profile_key`。
  - `offer_profile_key`
    - 类型：`string`
    - 约束：必须来自 `offer.resource_support.supported_profiles[*].profile_key`。
  - `resource_dependency_mode`
    - 类型：`enum`
    - 允许值：`none`、`required`
  - `required_capabilities`
    - 类型：`string[]`
    - 约束：必须按 `FR-0027` canonical order 规范化；当前只允许空数组、`account`、`proxy`、`account + proxy`。
  - `requirement_profile_evidence_ref`
    - 类型：`string`
    - 约束：必须唯一命中覆盖当前 adapter 的 `FR-0027` approved profile proof。
  - `offer_profile_evidence_ref`
    - 类型：`string`
    - 约束：必须唯一命中覆盖当前 adapter 的 `FR-0027` approved profile proof。

## CompatibilityDecisionError

- 作用：表达 `invalid_contract` 的最小错误口径。
- 字段：
  - `failure_category`
    - 类型：`enum`
    - 允许值：当前固定 `runtime_contract`
  - `error_code`
    - 类型：`enum`
    - 允许值：
      - `invalid_requirement_contract`
      - `invalid_provider_offer_contract`
      - `invalid_compatibility_contract`
      - `provider_leakage_detected`
  - `source_contract_ref`
    - 类型：`string`
    - 允许值：`FR-0024`、`FR-0025`、`FR-0027`、`FR-0026`
  - `adapter_mapping_required`
    - 类型：`boolean`
    - 约束：必须为 `true`，不得新增 Core-facing provider failed envelope category。
- 禁止语义：
  - provider-specific Core failed envelope category
  - selected provider / fallback provider
  - score / rank / priority

## CompatibilityDecisionEvidence

- 作用：把 decision 绑定到可审查、可验证的 contract 与 proof evidence。
- 字段：
  - `requirement_evidence_refs`
    - 类型：`string[]`
    - 约束：非空、去重；必须回指 `FR-0024` requirement evidence。
  - `offer_evidence_refs`
    - 类型：`string[]`
    - 约束：非空、去重；必须回指 `FR-0025` offer evidence。
  - `resource_profile_evidence_refs`
    - 类型：`string[]`
    - 约束：非空、去重；必须与参与 decision 的 requirement / offer profile proof refs 对齐，并满足 `FR-0027`。
  - `compatibility_decision_evidence_refs`
    - 类型：`string[]`
    - 约束：非空、去重；回指本 FR formal spec、后续 runtime tests、no-leakage guard、docs / evidence 或 closeout evidence。

## CompatibilityDecisionObservability

- 作用：表达 Adapter-bound decision 可追踪最小字段。
- 字段：
  - `decision_id`
  - `adapter_key`
  - `provider_key`
  - `requirement_id`
  - `offer_id`
  - `capability`
  - `operation`
  - `matched_profile_keys`
  - `decision_status`
  - `error_code`
  - `contract_refs`
  - `proof_refs`
- 禁止语义：
  - Core registry provider field
  - TaskRecord provider field
  - provider selector / routing / priority / fallback outcome
  - marketplace metadata / provider product support
  - Playwright / CDP / Chromium / browser profile / network tier / transport 技术字段

## CompatibilityNoLeakageAssertion

- 作用：表达 provider information leakage 的禁止边界。
- 字段：
  - `core_registry_provider_fields_allowed`
    - 类型：`boolean`
    - 约束：必须为 `false`
  - `core_routing_provider_fields_allowed`
    - 类型：`boolean`
    - 约束：必须为 `false`
  - `task_record_provider_fields_allowed`
    - 类型：`boolean`
    - 约束：必须为 `false`
  - `resource_lifecycle_provider_fields_allowed`
    - 类型：`boolean`
    - 约束：必须为 `false`
  - `adapter_bound_evidence_provider_fields_allowed`
    - 类型：`boolean`
    - 约束：必须为 `true`

## 判定规则

- requirement 不满足 `FR-0024` -> `decision_status=invalid_contract`，`error_code=invalid_requirement_contract`
- offer 不满足 `FR-0025` -> `decision_status=invalid_contract`，`error_code=invalid_provider_offer_contract`
- 任一 resource profile / proof 不满足 `FR-0027` -> `decision_status=invalid_contract`
- `requirement.adapter_key != offer.adapter_binding.adapter_key` -> `decision_status=invalid_contract`
- requirement 与 offer 的 capability / operation / target_type / collection_mode 不一致 -> `decision_status=invalid_contract`
- 任一侧越过 `content_detail_by_url + url + hybrid` -> `decision_status=invalid_contract`
- 两侧输入合法且任一 requirement profile 与 offer supported profile 的 canonical tuple 完全一致 -> `decision_status=matched`
- 两侧输入合法但无任何 profile 完全满足 -> `decision_status=unmatched`
- decision 或 Core-facing surface 出现 provider selector、routing、priority、score、fallback、marketplace、provider product support、provider lifecycle 或 provider leakage -> `decision_status=invalid_contract`
- `matched` 不代表 selected provider、fallback order、Core routing、真实 provider 产品支持或 provider runtime 可用性
