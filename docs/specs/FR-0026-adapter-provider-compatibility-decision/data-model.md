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
    - 约束：非空、稳定；必须使用不暴露 provider identity 的 opaque id 或 hash，不得由 `provider_key`、`offer_id` 等可逆 provider 标识直接拼接派生。
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
    - 类型：`string | null`
    - 约束：`matched` / `unmatched` 时必须同时等于 `requirement.adapter_key` 与 `offer.adapter_binding.adapter_key`；`invalid_contract` 且 adapter key 缺失或不一致时必须为 `null`，冲突值进入 `invalid_contract_evidence.observed_values`。
  - `capability`
    - 类型：`string | null`
    - 约束：`matched` / `unmatched` 时必须同时等于 requirement 与 offer 的 approved capability，当前只允许 `content_detail`；`invalid_contract` 且 capability 缺失、不一致或越界时必须为 `null`，冲突值进入 `invalid_contract_evidence.observed_values`。
  - `execution_slice`
    - 类型：`CompatibilityExecutionSlice | null`
    - 约束：`matched` / `unmatched` 时必须同时等于 requirement 与 offer 的 approved execution slice，当前必须且只能表达 `content_detail_by_url + url + hybrid`；`invalid_contract` 且 operation / target_type / collection_mode 缺失、不一致或越界时必须为 `null`，冲突值进入 `invalid_contract_evidence.observed_values`。
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
    - 约束：只表达无 provider identity 的 decision 追踪字段；不得包含 `provider_key`、`offer_id`、provider routing 或 provider persistence surface。
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
    - 约束：`matched` / `unmatched` 时必须非空、去重并回指 `FR-0024` requirement evidence；`invalid_contract` 且 requirement evidence 缺失、不可解析或不唯一时可以为空，不得伪造占位 ref。
  - `offer_evidence_refs`
    - 类型：`string[]`
    - 约束：`matched` / `unmatched` 时必须非空、去重并回指 `FR-0025` offer evidence；`invalid_contract` 且 offer evidence 缺失、不可解析或不唯一时可以为空，不得伪造占位 ref。
  - `resource_profile_evidence_refs`
    - 类型：`string[]`
    - 约束：只记录已成功解析且满足 `FR-0027` 的 profile proof refs；`matched` / `unmatched` 时必须非空、去重并与参与 decision 的 requirement / offer profile proof refs 对齐；`invalid_contract` 且 proof refs 为空、重复、不可解析或不唯一时可以为空，不得伪造占位 proof ref。
  - `compatibility_decision_evidence_refs`
    - 类型：`string[]`
    - 约束：非空、去重；回指本 FR formal spec、后续 runtime tests、no-leakage guard、docs / evidence 或 closeout evidence。
  - `adapter_bound_provider_evidence`
    - 类型：`AdapterBoundProviderEvidence | null`
    - 约束：只允许在 Adapter-bound decision evidence 中记录 provider identity；不得复制到 decision 顶层字段、observability 或 Core-facing projection。
  - `invalid_contract_evidence`
    - 类型：`InvalidCompatibilityContractEvidence | null`
    - 约束：当 `decision_status=invalid_contract` 时必须存在；当 `matched` 或 `unmatched` 时必须为空。

## AdapterBoundProviderEvidence

- 作用：在 Adapter-bound evidence 中追溯被比较的 Provider offer。
- 字段：
  - `provider_key`
    - 类型：`string`
    - 约束：来自 `offer.provider_key`；只允许 Adapter-bound evidence 使用。
  - `offer_id`
    - 类型：`string`
    - 约束：来自 `offer.observability.offer_id` 或等价 Adapter-bound offer evidence；不得成为 Core-facing field。
- 禁止语义：
  - decision 顶层 provider field
  - Core registry / routing / TaskRecord / resource lifecycle provider field

## InvalidCompatibilityContractEvidence

- 作用：在无法解析合法 proof refs 或输入 carrier 违法时，构造可审查的 `invalid_contract` 结果。
- 字段：
  - `source_contract_ref`
    - 类型：`string`
    - 允许值：`FR-0024`、`FR-0025`、`FR-0027`、`FR-0026`
  - `violated_rule`
    - 类型：`string`
    - 约束：非空，记录被违反的 formal rule id 或简短规则描述。
  - `unresolved_refs`
    - 类型：`string[]`
    - 约束：记录无法解析、不唯一或重复的原始 refs；当输入缺少 refs 时可以为空数组。
  - `resolved_profile_evidence_refs`
    - 类型：`string[]`
    - 约束：只记录已成功解析的 profile proof refs；不得为了满足非空约束而伪造 ref。
  - `observed_values`
    - 类型：`object`
    - 约束：仅记录构造 `invalid_contract` 所需的冲突或缺失摘要，例如 `requirement_adapter_key`、`offer_adapter_key`、`requirement_capability`、`offer_capability`、`requirement_execution_slice`、`offer_execution_slice`；不得包含 provider selector、routing、priority、score 或 fallback。

## CompatibilityDecisionObservability

- 作用：表达 Adapter-bound decision 可追踪最小字段。
- 通用约束：`matched` / `unmatched` 时必须记录已解析的 `adapter_key`、`capability` 与 `operation`；`invalid_contract` 且这些输入缺失、不一致或越界时，对应字段必须为 `null` 或省略，冲突摘要只能进入 `invalid_contract_evidence.observed_values`。
- 字段：
  - `decision_id`
  - `adapter_key`
  - `requirement_id`
  - `capability`
  - `operation`
  - `matched_profile_keys`
  - `decision_status`
  - `error_code`
  - `contract_refs`
  - `proof_refs`
- 禁止语义：
  - 在 `invalid_contract` 冲突场景中复制任一侧 adapter / capability / execution value 作为已解析事实
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
- adapter key 缺失或不一致时，decision 顶层 `adapter_key=null`，冲突值进入 `invalid_contract_evidence.observed_values`
- requirement 与 offer 的 capability / operation / target_type / collection_mode 不一致 -> `decision_status=invalid_contract`
- 任一侧越过 `content_detail_by_url + url + hybrid` -> `decision_status=invalid_contract`
- capability 缺失、不一致或越界时，decision 顶层 `capability=null`，冲突值进入 `invalid_contract_evidence.observed_values`
- execution slice 缺失、不一致或越界时，decision 顶层 `execution_slice=null`，冲突值进入 `invalid_contract_evidence.observed_values`
- 两侧输入合法且任一 requirement profile 与 offer supported profile 的 canonical tuple 完全一致 -> `decision_status=matched`
- 两侧输入合法但无任何 profile 完全满足 -> `decision_status=unmatched`
- decision 或 Core-facing surface 出现 provider selector、routing、priority、score、fallback、marketplace、provider product support、provider lifecycle 或 provider leakage -> `decision_status=invalid_contract`
- `matched` 不代表 selected provider、fallback order、Core routing、真实 provider 产品支持或 provider runtime 可用性
- decision 顶层字段或 observability 出现 `provider_key` / `offer_id` -> `decision_status=invalid_contract` 或 no-leakage guard 阻断
- Core-facing projection 只能携带无 provider identity 的 status / error 摘要，不得嵌入 `adapter_bound_provider_evidence`
