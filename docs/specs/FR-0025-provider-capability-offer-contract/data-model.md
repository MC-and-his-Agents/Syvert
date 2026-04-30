# FR-0025 数据模型

## ProviderCapabilityOffer

- 作用：表达某个 Adapter-bound Provider 对某个 adapter-facing capability 的 offer 输入、资源 profile 支持、错误映射、版本、证据、生命周期边界、观测预期与 fail-closed 规则。
- 稳定性：`v0.8.0` Provider capability offer 的 canonical carrier；manifest、SDK、validator、docs / evidence 与 compatibility decision 不得维护第二套同义模型。
- 字段：
  - `provider_key`
    - 类型：`string`
    - 约束：非空、稳定；只在 `adapter_binding.adapter_key` 下有意义；不得作为 Core registry key、global provider key、marketplace listing 或 routing key。
  - `adapter_binding`
    - 类型：`ProviderAdapterBinding`
    - 约束：必须声明 Adapter-bound provider port 边界；不得声明 Core-bound 或跨 adapter provider。
  - `capability_offer`
    - 类型：`ProviderCapabilityOfferDescriptor`
    - 约束：当前必须且只能表达 `content_detail_by_url + url + hybrid` 的 `content_detail` offer。
  - `resource_support`
    - 类型：`ProviderResourceSupport`
    - 约束：必须消费 `FR-0027` profile tuple / proof binding；不得表达 priority、fallback、selection、resource supply 或 lifecycle runtime。
  - `error_carrier`
    - 类型：`ProviderOfferErrorCarrier`
    - 约束：只表达 Provider offer 内部错误口径与 Adapter 映射要求；不得新增 Core-facing provider failed envelope category。
  - `version`
    - 类型：`ProviderOfferVersion`
    - 约束：必须固定 contract version 与依赖 contract refs；不得表达产品支持或 SLA。
  - `evidence`
    - 类型：`ProviderOfferEvidence`
    - 约束：必须回指 offer、resource profile 与 adapter binding 证据。
  - `lifecycle`
    - 类型：`ProviderOfferLifecycleExpectation`
    - 约束：只表达 Adapter-bound provider port 与既有 resource lifecycle 的消费边界，不定义 acquire/release/runtime store。
  - `observability`
    - 类型：`ProviderOfferObservabilityExpectation`
    - 约束：只表达 offer 可追踪字段，不暴露 selector、routing、fallback、marketplace 或技术链路字段。
  - `fail_closed`
    - 类型：`boolean`
    - 约束：必须为 `true`。

## ProviderAdapterBinding

- 作用：表达 Provider offer 只能通过哪个 Adapter-owned provider port 进入系统。
- 字段：
  - `adapter_key`
    - 类型：`string`
    - 约束：非空、稳定；必须与后续 decision 输入的 Adapter identity 对齐。
  - `binding_scope`
    - 类型：`enum`
    - 允许值：当前只允许 `adapter_bound`
  - `provider_port_ref`
    - 类型：`string`
    - 约束：非空、稳定；只用于追溯 Adapter-owned provider port，不是 Core import path 或 public SDK entry。
- 禁止语义：
  - `core_bound`
  - `global_provider`
  - cross-adapter provider binding
  - provider marketplace listing
  - Core provider registry / discovery / routing

## ProviderCapabilityOfferDescriptor

- 作用：表达 Provider 声称在 Adapter 边界内提供的 adapter-facing capability 与 approved execution slice。
- 字段：
  - `capability`
    - 类型：`enum`
    - 允许值：当前只允许 `content_detail`
  - `operation`
    - 类型：`enum`
    - 允许值：当前只允许 `content_detail_by_url`
  - `target_type`
    - 类型：`enum`
    - 允许值：当前只允许 `url`
  - `collection_mode`
    - 类型：`enum`
    - 允许值：当前只允许 `hybrid`

## ProviderResourceSupport

- 作用：表达 Provider offer 声称支持哪些 `FR-0027` resource profile tuple，作为后续 `FR-0026` compatibility decision 的 Provider-side resource input。
- 字段：
  - `supported_profiles`
    - 类型：`ProviderSupportedResourceProfile[]`
    - 约束：非空；每个元素必须满足 `FR-0027` profile tuple、canonicalization、single proof binding、approved execution slice 与 adapter coverage proof binding 规则。
  - `resource_profile_contract_ref`
    - 类型：`string`
    - 允许值：当前必须为 `FR-0027`
- 禁止语义：
  - profile priority / score / ranking
  - fallback / fallback order / preferred profile
  - provider selection / selected provider
  - resource acquisition / release / pooling
  - account pool / proxy pool / provider resource supply
  - provider-owned lifecycle

## ProviderSupportedResourceProfile

- 作用：表达 Provider offer 中一条可被后续 decision 消费的资源 profile 声明。
- 字段：
  - `profile_key`
    - 类型：`string`
    - 约束：在当前 offer 内唯一；只承担追溯职责，不承载优先级或执行顺序。
  - `resource_dependency_mode`
    - 类型：`enum`
    - 允许值：当前只允许 `none` 或 `required`
  - `required_capabilities`
    - 类型：`string[]`
    - 允许值：当前只允许空数组、`account`、`proxy`、`account + proxy`，并按 `FR-0027` 规则规范化。
  - `evidence_refs`
    - 类型：`string[]`
    - 约束：当前长度必须恰为 1；必须唯一命中与 profile tuple、capability 与 execution slice 完全一致，且 `reference_adapters` 覆盖当前 `adapter_binding.adapter_key` 的 `FR-0027` approved profile proof。

## ProviderOfferErrorCarrier

- 作用：表达 offer / provider 内部错误口径，以及错误必须经 Adapter 映射后才能外显到 Core。
- 字段：
  - `invalid_offer_code`
    - 类型：`enum`
    - 允许值：当前固定 `invalid_provider_offer`
  - `provider_unavailable_code`
    - 类型：`enum`
    - 允许值：当前固定 `provider_unavailable`
  - `contract_violation_code`
    - 类型：`enum`
    - 允许值：当前固定 `provider_contract_violation`
  - `adapter_mapping_required`
    - 类型：`boolean`
    - 约束：必须为 `true`
- 禁止语义：
  - 新增 Core-facing provider failed envelope category
  - 绕过 Adapter 的 Provider error 直出
  - provider-specific TaskRecord failure field

## ProviderOfferVersion

- 作用：表达 offer carrier 的语义版本与依赖 contract 边界。
- 字段：
  - `contract_version`
    - 类型：`string`
    - 允许值：当前固定 `v0.8.0`
  - `requirement_contract_ref`
    - 类型：`string`
    - 允许值：当前固定 `FR-0024`
  - `resource_profile_contract_ref`
    - 类型：`string`
    - 允许值：当前固定 `FR-0027`
  - `provider_port_boundary_ref`
    - 类型：`string`
    - 允许值：当前固定 `FR-0021`
- 禁止语义：
  - provider product support
  - marketplace release
  - SLA / availability guarantee
  - runtime rollout flag

## ProviderOfferEvidence

- 作用：把 Provider capability offer 绑定到可审查、可迁移、可验证的证据。
- 字段：
  - `provider_offer_evidence_refs`
    - 类型：`string[]`
    - 约束：非空、去重；回指本 FR formal spec、offer manifest fixture、SDK docs 或 closeout evidence。
  - `resource_profile_evidence_refs`
    - 类型：`string[]`
    - 约束：必须与 `resource_support.supported_profiles[*].evidence_refs` 对齐；每个 ref 最终必须唯一命中 tuple / execution slice 完全一致且 `reference_adapters` 覆盖当前 `adapter_binding.adapter_key` 的 `FR-0027` approved profile proof。
  - `adapter_binding_evidence_refs`
    - 类型：`string[]`
    - 约束：非空、去重；证明该 offer 只通过 Adapter-owned provider port 进入系统。

## ProviderOfferLifecycleExpectation

- 作用：表达 Provider offer 对 Adapter-owned provider port 与既有资源生命周期 contract 的消费边界。
- 字段：
  - `invoked_by_adapter_only`
    - 类型：`boolean`
    - 约束：必须为 `true`
  - `core_discovery_allowed`
    - 类型：`boolean`
    - 约束：必须为 `false`
  - `consumes_adapter_execution_context`
    - 类型：`boolean`
    - 约束：必须为 `true`
  - `uses_existing_resource_bundle_view`
    - 类型：`boolean`
    - 约束：若 offer 需要资源，只能消费 Adapter 传入的既有 resource bundle 视图。
  - `adapter_error_mapping_required`
    - 类型：`boolean`
    - 约束：必须为 `true`
- 禁止语义：
  - Core provider lifecycle
  - resource acquisition / release implementation
  - resource pool / lease store
  - provider-owned lifecycle
  - cross-adapter resource scheduling

## ProviderOfferObservabilityExpectation

- 作用：表达 offer 级可观测最小字段，便于 manifest validator、SDK evidence 与 closeout 对齐。
- 字段：
  - `offer_id`
    - 类型：`string`
    - 约束：稳定、非空；建议由 `adapter_key + provider_key + capability + operation + target_type + collection_mode + contract_version` 派生。
  - `provider_key`
    - 类型：`string`
    - 约束：只在 Adapter-bound offer trace 中出现，不进入 Core discovery。
  - `adapter_key`
    - 类型：`string`
    - 约束：必须与 `adapter_binding.adapter_key` 对齐。
  - `capability`
    - 类型：`string`
    - 约束：必须与 `capability_offer.capability` 对齐。
  - `operation`
    - 类型：`string`
    - 约束：必须与 `capability_offer.operation` 对齐。
  - `profile_keys`
    - 类型：`string[]`
    - 约束：与 `resource_support.supported_profiles[*].profile_key` 对齐。
  - `proof_refs`
    - 类型：`string[]`
    - 约束：与 `evidence.resource_profile_evidence_refs` 对齐。
  - `contract_version`
    - 类型：`string`
    - 约束：必须与 `version.contract_version` 对齐。
  - `validation_outcome_fields`
    - 类型：`string[]`
    - 允许值：当前只允许 `validation_status`、`error_code`、`failure_category`。
- 禁止语义：
  - provider selection / routing / priority / fallback outcome
  - marketplace metadata / provider product support
  - Core registry / TaskRecord provider field
  - Playwright / CDP / Chromium / browser profile / network tier / transport 技术字段

## 判定规则

- carrier 缺少固定字段 -> `runtime_contract + invalid_provider_offer`
- `fail_closed != true` -> `runtime_contract + invalid_provider_offer`
- `provider_key` 为空或被声明为 Core / global / marketplace identity -> `runtime_contract + invalid_provider_offer`
- `adapter_binding.binding_scope != adapter_bound` -> `runtime_contract + invalid_provider_offer`
- `capability_offer` 超出 `content_detail_by_url + url + hybrid` -> `runtime_contract + invalid_provider_offer`
- `resource_support` 不满足 `FR-0027` profile tuple / proof binding -> `runtime_contract + invalid_provider_offer`
- proof refs 不可解析、不唯一、不对齐、越过 approved execution slice，或未在 `reference_adapters` 中覆盖当前 `adapter_binding.adapter_key` -> `runtime_contract + invalid_provider_offer`
- 出现 compatibility decision、selector、priority、fallback、marketplace、产品支持或 runtime 技术字段 -> contract violation
- `ProviderCapabilityOffer` 合法 -> 仅代表 Provider offer declared，不代表任何 Adapter requirement compatible
