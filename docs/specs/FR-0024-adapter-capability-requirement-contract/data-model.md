# FR-0024 数据模型

## AdapterCapabilityRequirement

- 作用：表达某个 Adapter 对某个 adapter-facing capability 的执行前提、资源 profile、证据、生命周期预期、观测预期与 fail-closed 规则。
- 稳定性：`v0.8.0` Adapter capability requirement 的 canonical carrier；manifest、SDK、validator 与 reference adapter migration 不得维护第二套同义模型。
- 字段：
  - `adapter_key`
    - 类型：`string`
    - 约束：非空、稳定；必须与 Adapter registry / manifest identity 一致；必须与 `resource_requirement.adapter_key` 一致。
  - `capability`
    - 类型：`string`
    - 约束：当前 approved slice 只允许 `content_detail`；必须与 `resource_requirement.capability` 一致。
  - `execution_requirement`
    - 类型：`AdapterCapabilityExecutionRequirement`
    - 约束：当前必须且只能表达 `content_detail_by_url + url + hybrid`。
  - `resource_requirement`
    - 类型：`AdapterResourceRequirementDeclarationV2`
    - 来源：`FR-0027`
    - 约束：必须合法；必须通过 `FR-0027` profile / proof binding 校验；不得回退到旧单声明 carrier。
  - `evidence`
    - 类型：`AdapterCapabilityRequirementEvidence`
    - 约束：必须回指 resource profile proof 与 requirement 级验证证据。
  - `lifecycle`
    - 类型：`AdapterCapabilityLifecycleExpectation`
    - 约束：只表达 Adapter 对既有 Core resource lifecycle 的消费预期，不定义 acquire/release/runtime store。
  - `observability`
    - 类型：`AdapterCapabilityObservabilityExpectation`
    - 约束：只表达 requirement 可追踪字段，不暴露 provider、selector、fallback 或技术链路字段。
  - `fail_closed`
    - 类型：`boolean`
    - 约束：必须为 `true`。

## AdapterCapabilityExecutionRequirement

- 作用：表达 Core public operation 到 Adapter capability 的 approved execution slice。
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

## AdapterCapabilityRequirementEvidence

- 作用：把 Adapter capability requirement 绑定到可审查、可迁移、可验证的证据。
- 字段：
  - `resource_profile_evidence_refs`
    - 类型：`string[]`
    - 约束：必须与 `resource_requirement.resource_requirement_profiles[*].evidence_refs` 对齐；每个 ref 最终必须唯一命中 `FR-0027` 的 `ApprovedSharedResourceRequirementProfileEvidenceEntry.profile_ref`。
  - `capability_requirement_evidence_refs`
    - 类型：`string[]`
    - 约束：非空、去重；回指本 FR formal spec、manifest fixture、reference adapter migration 或后续 closeout evidence。

## AdapterCapabilityLifecycleExpectation

- 作用：表达 Adapter 对既有资源生命周期 contract 的消费预期。
- 字段：
  - `requires_core_resource_bundle`
    - 类型：`boolean`
    - 约束：表达 Adapter 是否需要 Core 注入资源 bundle；不定义 bundle shape。
  - `resource_profiles_drive_admission`
    - 类型：`boolean`
    - 约束：必须为 `true`，表示 admission 必须先消费 `FR-0027` resource profile match 结果。
  - `uses_existing_disposition_hint`
    - 类型：`boolean`
    - 约束：若 Adapter 需要表达资源失败或处置建议，只能复用既有 resource disposition / failed envelope 语义。
- 禁止语义：
  - resource acquisition / release 实现
  - resource pool / lease store
  - provider-owned lifecycle
  - cross-adapter resource scheduling

## AdapterCapabilityObservabilityExpectation

- 作用：表达 requirement 级可观测最小字段，便于 manifest validator、runtime trace 与 closeout evidence 对齐。
- 字段：
  - `requirement_id`
    - 类型：`string`
    - 约束：稳定、非空；建议由 `adapter_key + capability + operation + target_type + collection_mode` 派生。
  - `profile_keys`
    - 类型：`string[]`
    - 约束：与 `resource_requirement.resource_requirement_profiles[*].profile_key` 对齐。
  - `proof_refs`
    - 类型：`string[]`
    - 约束：与 `evidence.resource_profile_evidence_refs` 对齐。
  - `admission_outcome_fields`
    - 类型：`string[]`
    - 允许值：当前只允许 `match_status`、`error_code`、`failure_category`。
- 禁止语义：
  - provider identity / provider key
  - provider selection / routing / priority / fallback outcome
  - Playwright / CDP / Chromium / browser profile / network tier / transport 技术字段

## 判定规则

- carrier 缺少固定字段 -> `runtime_contract + invalid_resource_requirement`
- `fail_closed != true` -> `runtime_contract + invalid_resource_requirement`
- `adapter_key` / `capability` / `execution_requirement` 与 `resource_requirement` 不一致 -> `runtime_contract + invalid_resource_requirement`
- `resource_requirement` 不满足 `FR-0027` -> `runtime_contract + invalid_resource_requirement`
- proof refs 不可解析、不唯一、不对齐、不覆盖 declaration adapter -> `runtime_contract + invalid_resource_requirement`
- 出现 provider offer、compatibility decision、priority、fallback、新能力词汇或 runtime 技术字段 -> contract violation
- `AdapterCapabilityRequirement` 合法 -> 仅代表 Adapter requirement declared，不代表任何 Provider compatible
