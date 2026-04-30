# FR-0024 contracts

## canonical carrier

- canonical requirement：`AdapterCapabilityRequirement`
- 目的：为 `adapter_key + capability + execution_requirement` 声明 Adapter 执行该 capability 所需的资源 profile、证据、生命周期预期、观测预期与 fail-closed 规则。

### required fields

- `adapter_key`
- `capability`
- `execution_requirement`
- `resource_requirement`
- `evidence`
- `lifecycle`
- `observability`
- `fail_closed`

## execution requirement

### required fields

- `operation`
- `target_type`
- `collection_mode`

### validation rules

- 当前 approved slice 只允许 `operation=content_detail_by_url`
- 当前 approved slice 只允许 `target_type=url`
- 当前 approved slice 只允许 `collection_mode=hybrid`
- `capability` 当前只允许 `content_detail`

## resource requirement binding

- `resource_requirement` 必须消费 `FR-0027` 的 `AdapterResourceRequirementDeclarationV2`
- `resource_requirement.adapter_key` 必须等于 `AdapterCapabilityRequirement.adapter_key`
- `resource_requirement.capability` 必须等于 `AdapterCapabilityRequirement.capability`
- `resource_requirement.resource_requirement_profiles[*].evidence_refs` 必须按 `FR-0027` 规则唯一命中 `ApprovedSharedResourceRequirementProfileEvidenceEntry.profile_ref`
- proof 不可解析、不唯一、不对齐、不覆盖 declaration adapter，或不在当前 approved execution slice 内，一律归类为 `runtime_contract + invalid_resource_requirement`
- 本 contract 不重新定义 profile tuple、matcher `one-of`、single proof binding 或 profile approval decision；这些语义由 `FR-0027` 持有

## evidence contract

### required fields

- `resource_profile_evidence_refs`
- `capability_requirement_evidence_refs`

### validation rules

- `resource_profile_evidence_refs` 必须与 `resource_requirement` 内所有 profile proof refs 对齐
- `capability_requirement_evidence_refs` 必须非空、去重，并回指本 FR formal spec、manifest fixture、reference adapter migration 或 closeout evidence
- evidence 不得引用 adapter 私有注释、运行期临时日志或未经批准的 provider offer 材料作为 resource profile proof

## lifecycle contract

- 只允许表达 Adapter 对既有 Core resource lifecycle 的消费预期
- 允许字段：
  - `requires_core_resource_bundle`
  - `resource_profiles_drive_admission`
  - `uses_existing_disposition_hint`
- 禁止字段或同义语义：
  - resource acquisition / release implementation
  - resource pool / lease store
  - provider-owned lifecycle
  - cross-adapter resource scheduler

## observability contract

- 只允许表达 requirement 级可追踪最小字段
- 允许字段：
  - `requirement_id`
  - `profile_keys`
  - `proof_refs`
  - `admission_outcome_fields`
- `admission_outcome_fields` 当前只允许：
  - `match_status`
  - `error_code`
  - `failure_category`
- 禁止 provider identity、provider selector、priority、fallback outcome、Playwright、CDP、Chromium、browser profile、network tier 或 transport 技术字段

## fail-closed contract

- `fail_closed` 必须存在且必须为 `true`
- 任一固定字段缺失、字段不一致、proof 不合法、resource profile 不合法、execution slice 越界或出现被禁止字段时，必须阻断
- 合法 Adapter requirement 只代表 requirement declared；不得推出 Provider offer 存在、Provider compatible 或可以绑定执行

## explicitly forbidden

- `provider_offer`
- `provider_capability_offer`
- `compatibility_decision`
- `provider_key`
- `provider_selection`
- `provider_routing`
- `priority`
- `fallback`
- `fallback_order`
- `preferred_profile`
- `optional_capabilities`
- 新共享能力词汇
- runtime implementation details
