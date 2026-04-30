# FR-0025 contracts

## canonical carrier

- canonical offer：`ProviderCapabilityOffer`
- 目的：为 `adapter_key + provider_key + capability_offer` 声明 Adapter-bound Provider 提供的 capability offer、resource support、错误映射、版本、证据、生命周期边界、观测预期与 fail-closed 规则。

### required fields

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

## provider key

### validation rules

- `provider_key` 必须非空、稳定。
- `provider_key` 只在 `adapter_binding.adapter_key` 下有意义。
- `provider_key` 不得被解释为 Core registry key、global provider key、routing key、marketplace listing 或真实 provider 产品支持。

## adapter binding

### required fields

- `adapter_key`
- `binding_scope`
- `provider_port_ref`

### validation rules

- `adapter_key` 必须非空、稳定。
- `binding_scope` 当前只允许 `adapter_bound`。
- `provider_port_ref` 只用于追溯 Adapter-owned provider port，不是 Core import path 或 public SDK entry。
- Core、registry、TaskRecord 与 resource lifecycle 不得通过该 binding 发现或路由 provider。

## capability offer

### required fields

- `capability`
- `operation`
- `target_type`
- `collection_mode`

### validation rules

- 当前 approved slice 只允许 `capability=content_detail`。
- 当前 approved slice 只允许 `operation=content_detail_by_url`。
- 当前 approved slice 只允许 `target_type=url`。
- 当前 approved slice 只允许 `collection_mode=hybrid`。

## resource support

### required fields

- `supported_profiles`
- `resource_profile_contract_ref`

### validation rules

- `resource_profile_contract_ref` 当前必须为 `FR-0027`。
- `supported_profiles` 必须非空。
- 每个 supported profile 必须包含 `profile_key`、`resource_dependency_mode`、`required_capabilities`、`evidence_refs`。
- `resource_dependency_mode=none` -> `required_capabilities=[]`。
- `resource_dependency_mode=required` -> `required_capabilities` 非空、去重，且只能来自 `account`、`proxy`。
- `required_capabilities` 在 proof lookup 和 equality 判断前必须按 `FR-0027` 规则规范化。
- `evidence_refs` 长度恰为 1，并且这唯一一个引用必须唯一命中与 `capability + operation + target_type + collection_mode + resource_dependency_mode + required_capabilities` 完全一致的 `FR-0027` approved profile proof。
- 同一 offer 内不得出现语义重复 profile。
- 本 contract 不重新定义 `FR-0027` matcher `one-of`、profile approval proof 或 `resource_unavailable` 语义。

## error carrier

### required fields

- `invalid_offer_code`
- `provider_unavailable_code`
- `contract_violation_code`
- `adapter_mapping_required`

### validation rules

- `invalid_offer_code` 当前固定为 `invalid_provider_offer`。
- `provider_unavailable_code` 当前固定为 `provider_unavailable`。
- `contract_violation_code` 当前固定为 `provider_contract_violation`。
- `adapter_mapping_required` 必须为 `true`。
- Provider 错误不得作为 Core-facing provider failed envelope 直出；必须经 Adapter 映射到既有 Adapter / runtime failed envelope。

## version contract

### required fields

- `contract_version`
- `requirement_contract_ref`
- `resource_profile_contract_ref`
- `provider_port_boundary_ref`

### validation rules

- `contract_version` 当前固定为 `v0.8.0`。
- `requirement_contract_ref` 当前固定为 `FR-0024`。
- `resource_profile_contract_ref` 当前固定为 `FR-0027`。
- `provider_port_boundary_ref` 当前固定为 `FR-0021`。
- version 字段不得表达 provider product support、marketplace release、SLA 或 runtime rollout。

## evidence contract

### required fields

- `provider_offer_evidence_refs`
- `resource_profile_evidence_refs`
- `adapter_binding_evidence_refs`

### validation rules

- `provider_offer_evidence_refs` 必须非空、去重，并回指本 FR formal spec、offer manifest fixture、SDK docs 或 closeout evidence。
- `resource_profile_evidence_refs` 必须与 `resource_support.supported_profiles[*].evidence_refs` 对齐。
- `adapter_binding_evidence_refs` 必须非空、去重，并证明 offer 只通过 Adapter-owned provider port 进入系统。
- evidence 不得引用 provider 私有注释、运行期临时日志、marketplace 文案或未经批准的 provider 产品材料作为 canonical proof。

## lifecycle contract

- 只允许表达 Provider offer 对 Adapter-owned provider port 与既有 Core resource lifecycle 的消费边界。
- 允许字段：
  - `invoked_by_adapter_only`
  - `core_discovery_allowed`
  - `consumes_adapter_execution_context`
  - `uses_existing_resource_bundle_view`
  - `adapter_error_mapping_required`
- 固定要求：
  - `invoked_by_adapter_only=true`
  - `core_discovery_allowed=false`
  - `consumes_adapter_execution_context=true`
  - `adapter_error_mapping_required=true`
- 禁止字段或同义语义：
  - Core provider lifecycle
  - resource acquisition / release implementation
  - resource pool / lease store
  - provider-owned lifecycle
  - cross-adapter resource scheduler

## observability contract

- 只允许表达 offer 级可追踪最小字段。
- 允许字段：
  - `offer_id`
  - `provider_key`
  - `adapter_key`
  - `capability`
  - `operation`
  - `profile_keys`
  - `proof_refs`
  - `contract_version`
  - `validation_outcome_fields`
- `validation_outcome_fields` 当前只允许：
  - `validation_status`
  - `error_code`
  - `failure_category`
- 禁止 provider selector、routing policy、priority、fallback outcome、marketplace metadata、provider product support、Core registry provider field、TaskRecord provider field、Playwright、CDP、Chromium、browser profile、network tier 或 transport 技术字段。

## fail-closed contract

- `fail_closed` 必须存在且必须为 `true`。
- 任一固定字段缺失、字段不一致、proof 不合法、resource support 不合法、approved slice 越界、adapter binding 越界或出现被禁止字段时，必须阻断。
- 合法 Provider offer 只代表 offer declared；不得推出 Adapter requirement compatible、Provider selected 或 Core 可以绑定执行。

## explicitly forbidden

- `compatibility_decision`
- `selected_provider`
- `provider_selection`
- `provider_selector`
- `provider_routing`
- `routing_policy`
- `priority`
- `score`
- `fallback`
- `fallback_order`
- `preferred_profile`
- `marketplace_listing`
- `provider_product_support`
- Core provider registry / discovery / routing
- 新共享能力词汇
- provider resource supply / pool / lifecycle
- runtime implementation details
