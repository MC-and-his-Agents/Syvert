# CHORE-0358 v0.9.0 external provider sample evidence

## 目的

本文档记录 `FR-0355` 的 implementation evidence。它证明 `v0.9.0` 已有一个 external provider sample 可以经过 `AdapterCapabilityRequirement -> ProviderCapabilityOffer -> AdapterProviderCompatibilityDecision -> Adapter-bound execution evidence` 链路，并可被 `FR-0351` 的 `provider_compatibility_sample` gate item 消费。

## Evidence Summary

- release：`v0.9.0`
- FR：`FR-0355`
- Work Item：`#358 / CHORE-0358-v0-9-external-provider-sample-evidence`
- consumed gate：`FR-0351:provider_compatibility_sample`
- approved slice：`capability=content_detail + operation=content_detail_by_url + target_type=url + collection_mode=hybrid`
- sample origin：`external_provider_sample`
- sample_id：`v0.9.0-external-provider-sample-content-detail`
- manifest_id：`v0.9.0-external-provider-sample-content-detail`
- manifest_ref：`syvert/fixtures/v0_9_external_provider_sample_manifest.json`
- provenance_ref：`controlled-record:v0.9.0:external-provider-sample-content-detail`
- controlled_record_ref：`controlled-record:v0.9.0:external-provider-sample-content-detail`
- author_path：`external-provider-author-fixture`
- adapter_key：`xhs`
- provider_identity_scope：`adapter_bound`
- provider_key_redaction：`stable fixture provider key; not a product support claim`
- not_native_provider_self_evidence：`true`
- provider support claim：`false`
- forbidden_claims：`()`
- requirement_ref：`fr-0024:reference-adapter-migration:xhs-douyin-content-detail`
- offer_ref：`fr-0025:offer-manifest-fixture-validator:v0-9-external-provider-sample`
- decision_ref：`v0-9-external-provider-sample-matched`
- decision_contract_ref：`fr-0026:runtime-tests:adapter-provider-compatibility-decision`
- profile_proof_refs：`fr-0027:profile:content-detail-by-url-hybrid:account-proxy`、`fr-0027:profile:content-detail-by-url-hybrid:account`
- status：`pass`
- decision_matrix_ref：`docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md#decision-matrix`
- adapter_bound_execution_ref：`docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md#adapter-bound-execution-evidence`
- no_leakage_ref：`docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md#no-leakage-evidence`
- dual_reference_ref：`tests.runtime.test_real_adapter_regression`
- third_party_adapter_entry_ref：`tests.runtime.test_third_party_adapter_contract_entry`
- api_cli_same_core_path_ref：`tests.runtime.test_cli_http_same_path`

## Decision Matrix

- `matched`：`v0-9-external-provider-sample-matched`
  - case ref：`fr-0355:decision-matrix:matched`
  - external provider offer 合法绑定 `adapter_key=xhs`。
  - requirement 与 offer 同处 approved slice。
  - resource profile refs 覆盖 `account_proxy` 与 `account`。
- `unmatched`：`v0-9-external-provider-sample-unmatched`
  - case ref：`fr-0355:decision-matrix:unmatched`
  - requirement 合法需要 `account_proxy`。
  - offer 合法只支持 `account`。
  - decision 返回 `unmatched`，不把合法不兼容误报为 contract violation。
- `invalid_contract`：`v0-9-external-provider-sample-invalid-contract`
  - case ref：`fr-0355:decision-matrix:invalid-contract`
  - external offer 带 forbidden `selected_provider`。
  - decision fail-closed 返回 `invalid_contract`。

## Adapter-Bound Execution Evidence

- matched_decision_ref：`fr-0355:decision-matrix:matched`
- matched_decision_id：`v0-9-external-provider-sample-matched`
- matched decision 后进入 Adapter-owned provider seam：`xhs:adapter-owned-provider-port:external-fixture`。
- success evidence 覆盖：
  - raw_payload_ref：`external-fixture://content-detail/success#raw`
  - normalized_result_ref：`external-fixture://content-detail/success#normalized`
  - normalized result：`platform=xhs`、`content_id=external-fixture-content-001`
  - resource profile consumption：`account_proxy`
  - resource lifecycle disposition hint：`release`
  - observability carrier：adapter / capability / operation / decision status / proof refs
- failure evidence 边界：
  - provider failure input：`source_error=external_provider_timeout`
  - adapter_mapped_failed_envelope_ref：`external-fixture://content-detail/provider-timeout#adapter-mapped-failed-envelope`
  - Adapter-mapped failed envelope：`category=platform`、`code=external_sample_unavailable`
  - Core-facing failed envelope 不新增 provider category。

## Core Surface Projection

- core_surface_projection_ref：`docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md#core-surface-projection`
- projection fields：`decision_id`、`adapter_key`、`capability`、`decision_status`、`error_code`、`failure_category`、`fail_closed`
- provider fields：none

## No-Leakage Evidence

`build_core_surface_no_leakage_evidence()` 审计以下 Core-facing surfaces：

- core projection
- registry discovery
- core routing
- TaskRecord
- resource lifecycle
- Core-facing failed envelope

结果：

| surface | status | forbidden_field_paths | forbidden_value_paths |
|---|---|---|---|
| `core_projection` | `passed` | `()` | `()` |
| `registry_discovery` | `passed` | `()` | `()` |
| `core_routing` | `passed` | `()` | `()` |
| `task_record` | `passed` | `()` | `()` |
| `resource_lifecycle` | `passed` | `()` | `()` |
| `core_facing_failed_envelope` | `passed` | `()` | `()` |

- provider_identity_in_core_surface：`false`
- registry_discovery_checked：`true`
- core_routing_checked：`true`
- task_record_checked：`true`
- resource_lifecycle_checked：`true`
- failed_envelope_checked：`true`
- all_forbidden_paths_empty：`true`

这些 surfaces 均不得出现 `provider_key`、`offer_id`、provider selector、fallback、routing、marketplace、provider lifecycle 或 resource supply 字段。

## Validation Evidence

| validation | command | result |
|---|---|---|
| external provider sample evidence | `python3 -m unittest tests.runtime.test_real_provider_sample_evidence` | `pass` |
| compatibility decision / no-leakage / sample | `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard tests.runtime.test_real_provider_sample_evidence` | `pass` |
| dual reference / third-party entry / API CLI same path | `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_cli_http_same_path` | `pass` |

## Boundary

- 本 evidence 不声明任何指定 provider 产品正式支持。
- 本 evidence 不引入 provider selector、fallback、marketplace 或 Core provider registry。
- 本 evidence 不扩大 approved slice 到 search/list/comment/batch/dataset 或发布能力。
- 本 evidence 不替代双参考基线、第三方 Adapter-only entry 或 API / CLI same Core path；这些作为 `v0.9.0` closeout required evidence 继续单独验证。
