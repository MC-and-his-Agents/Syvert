# CHORE-0358 v0.9.0 external provider sample evidence

## 目的

本文档记录 `FR-0355` 的 implementation evidence。它证明 `v0.9.0` 已有一个 external provider sample 可以经过 `AdapterCapabilityRequirement -> ProviderCapabilityOffer -> AdapterProviderCompatibilityDecision -> Adapter-bound execution evidence` 链路，并可被 `FR-0351` 的 `provider_compatibility_sample` gate item 消费。

## Evidence Summary

- release：`v0.9.0`
- fr_ref：`FR-0355`
- work_item_ref：`#358 / CHORE-0358-v0-9-external-provider-sample-evidence`
- consumed_gate_ref：`FR-0351:provider_compatibility_sample`
- approved_slice：`capability=content_detail + operation=content_detail_by_url + target_type=url + collection_mode=hybrid`
- sample_origin：`external_provider_sample`
- sample_id：`v0.9.0-external-provider-sample-content-detail`
- manifest_id：`v0.9.0-external-provider-sample-content-detail`
- manifest_ref：`syvert/fixtures/v0_9_external_provider_sample_manifest.json`
- provenance_ref：`controlled-record:v0.9.0:external-provider-sample-content-detail`
- provenance_artifact_ref：`syvert/fixtures/v0_9_external_provider_sample_provenance.json`
- controlled_record_ref：`controlled-record:v0.9.0:external-provider-sample-content-detail`
- author_path：`external-provider-author-fixture`
- adapter_key：`xhs`
- provider_identity_scope：`adapter_bound`
- provider_key_redaction：`stable fixture provider key; not a product support claim`
- not_native_provider_self_evidence：`true`
- provider_support_claim：`false`
- forbidden_claims：`()`
- requirement_ref：`fr-0024:reference-adapter-migration:xhs-douyin-content-detail`
- offer_ref：`fr-0025:offer-manifest-fixture-validator:v0-9-external-provider-sample`
- adapter_binding_ref：`fr-0025:offer-manifest-fixture-validator:v0-9-external-provider-adapter-binding`
- decision_ref：`v0-9-external-provider-sample-matched`
- decision_contract_ref：`fr-0026:runtime-tests:adapter-provider-compatibility-decision`
- profile_proof_refs：`fr-0027:profile:content-detail-by-url-hybrid:account-proxy`、`fr-0027:profile:content-detail-by-url-hybrid:account`
- status：`pass`
- decision_matrix_ref：`docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md#decision-matrix`
- adapter_bound_execution_ref：`docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md#adapter-bound-execution-evidence`
- no_leakage_ref：`docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md#no-leakage-evidence`
- validation_evidence_ref：`docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-validation.json`
- dual_reference_ref：`tests.runtime.test_real_adapter_regression`
- third_party_adapter_entry_ref：`tests.runtime.test_third_party_adapter_contract_entry`
- api_cli_same_core_path_ref：`tests.runtime.test_cli_http_same_path`

## Structured Evidence Snapshot

`build_real_provider_sample_evidence_report()` 使用以下机器可读 snapshot 与运行时计算结果做一致性校验。Markdown 叙述可调整，但该 JSON snapshot 的关键字段漂移必须 fail-closed。

<!-- syvert:evidence-report-json:start -->
```json
{
  "adapter_bound_execution": {
    "adapter_mapped_error_code": "external_sample_unavailable",
    "adapter_mapped_failed_envelope_ref": "external-fixture://content-detail/provider-timeout#adapter-mapped-failed-envelope",
    "failure_task_record_ref": "task_record:task-v0-9-sample-failure",
    "matched_decision_id": "v0-9-external-provider-sample-matched",
    "matched_decision_ref": "fr-0355:decision-matrix:matched",
    "normalized_result_present": true,
    "normalized_result_ref": "external-fixture://content-detail/success#normalized",
    "observability_carrier_checked": true,
    "provider_error_mapping_checked": true,
    "provider_side_error_code": "provider_unavailable",
    "raw_payload_present": true,
    "raw_payload_ref": "external-fixture://content-detail/success#raw",
    "resource_lifecycle_disposition_checked": true,
    "resource_lifecycle_disposition_hint": null,
    "resource_lifecycle_failure_release_reason": "adapter_failed_without_disposition_hint",
    "resource_lifecycle_release_reason": "adapter_completed_without_disposition_hint",
    "resource_profile_consumption_checked": true,
    "runtime_execution_ref": "syvert.runtime.execute_task_with_record:v0-9-external-provider-sample",
    "status": "pass",
    "success_task_record_ref": "task_record:task-v0-9-sample-success"
  },
  "approved_slice": {
    "capability": "content_detail",
    "collection_mode": "hybrid",
    "operation": "content_detail_by_url",
    "target_type": "url"
  },
  "consumed_gate_ref": "FR-0351:provider_compatibility_sample",
  "core_surface_no_leakage": {
    "all_forbidden_paths_empty": true,
    "core_routing_checked": true,
    "failed_envelope_checked": true,
    "provider_identity_in_core_surface": false,
    "registry_discovery_checked": true,
    "resource_lifecycle_checked": true,
    "status": "pass",
    "surfaces": {
      "core_facing_failed_envelope": {
        "forbidden_field_paths": [],
        "forbidden_value_paths": [],
        "status": "passed"
      },
      "core_projection": {
        "forbidden_field_paths": [],
        "forbidden_value_paths": [],
        "status": "passed"
      },
      "core_routing": {
        "forbidden_field_paths": [],
        "forbidden_value_paths": [],
        "status": "passed"
      },
      "registry_discovery": {
        "forbidden_field_paths": [],
        "forbidden_value_paths": [],
        "status": "passed"
      },
      "resource_lifecycle": {
        "forbidden_field_paths": [],
        "forbidden_value_paths": [],
        "status": "passed"
      },
      "resource_trace": {
        "forbidden_field_paths": [],
        "forbidden_value_paths": [],
        "status": "passed"
      },
      "task_record": {
        "forbidden_field_paths": [],
        "forbidden_value_paths": [],
        "status": "passed"
      }
    },
    "task_record_checked": true
  },
  "decision_matrix": {
    "invalid_contract_case_ref": "fr-0355:decision-matrix:invalid-contract",
    "invalid_contract_case_status": "invalid_contract",
    "matched_case_ref": "fr-0355:decision-matrix:matched",
    "matched_case_status": "matched",
    "unmatched_case_ref": "fr-0355:decision-matrix:unmatched",
    "unmatched_case_status": "unmatched",
    "validator_commands": [
      "python3 -m unittest tests.runtime.test_real_provider_sample_evidence",
      "python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard tests.runtime.test_real_provider_sample_evidence",
      "python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_cli_http_same_path"
    ]
  },
  "external_provider_sample": {
    "adapter_binding_ref": "fr-0025:offer-manifest-fixture-validator:v0-9-external-provider-adapter-binding",
    "adapter_key": "xhs",
    "author_path": "external-provider-author-fixture",
    "decision_contract_ref": "fr-0026:runtime-tests:adapter-provider-compatibility-decision",
    "decision_ref": "v0-9-external-provider-sample-matched",
    "forbidden_claims": [],
    "manifest_id": "v0.9.0-external-provider-sample-content-detail",
    "manifest_ref": "syvert/fixtures/v0_9_external_provider_sample_manifest.json",
    "not_native_provider_self_evidence": true,
    "offer_ref": "fr-0025:offer-manifest-fixture-validator:v0-9-external-provider-sample",
    "profile_proof_refs": [
      "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
      "fr-0027:profile:content-detail-by-url-hybrid:account"
    ],
    "provenance_artifact_ref": "syvert/fixtures/v0_9_external_provider_sample_provenance.json",
    "provenance_ref": "controlled-record:v0.9.0:external-provider-sample-content-detail",
    "provider_identity_scope": "adapter_bound",
    "provider_key_redaction": "stable fixture provider key; not a product support claim",
    "provider_support_claim": false,
    "requirement_ref": "fr-0024:reference-adapter-migration:xhs-douyin-content-detail",
    "sample_id": "v0.9.0-external-provider-sample-content-detail"
  },
  "fr_ref": "FR-0355",
  "provider_support_claim": false,
  "release": "v0.9.0",
  "report_id": "CHORE-0358-v0-9-external-provider-sample-evidence",
  "sample_origin": "external_provider_sample",
  "validation_evidence_ref": "docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-validation.json"
}
```
<!-- syvert:evidence-report-json:end -->

- snapshot_sha256：`31974bc000995d0f746d6b9132afa818dc85e7971ace8b0e355c918a66f9ba76`

## Decision Matrix

- matched_case_ref：`fr-0355:decision-matrix:matched`
  - decision_id：`v0-9-external-provider-sample-matched`
  - external provider offer 合法绑定 `adapter_key=xhs`。
  - requirement 与 offer 同处 approved slice。
  - resource profile refs 覆盖 `account_proxy` 与 `account`。
- unmatched_case_ref：`fr-0355:decision-matrix:unmatched`
  - decision_id：`v0-9-external-provider-sample-unmatched`
  - requirement 合法需要 `account_proxy`。
  - offer 合法只支持 `account`。
  - decision 返回 `unmatched`，不把合法不兼容误报为 contract violation。
- invalid_contract_case_ref：`fr-0355:decision-matrix:invalid-contract`
  - decision_id：`v0-9-external-provider-sample-invalid-contract`
  - external offer 带 forbidden `selected_provider`。
  - decision fail-closed 返回 `invalid_contract`。
- validator_commands：
  - `python3 -m unittest tests.runtime.test_real_provider_sample_evidence`
  - `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard tests.runtime.test_real_provider_sample_evidence`
  - `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_cli_http_same_path`

## Adapter-Bound Execution Evidence

- matched_decision_ref：`fr-0355:decision-matrix:matched`
- matched_decision_id：`v0-9-external-provider-sample-matched`
- matched decision 后进入 Adapter-owned provider seam：`xhs:adapter-owned-provider-port:external-fixture`。
- runtime_execution_ref：`syvert.runtime.execute_task_with_record:v0-9-external-provider-sample`
- success_task_record_ref：`task_record:task-v0-9-sample-success`
- failure_task_record_ref：`task_record:task-v0-9-sample-failure`
- success evidence 覆盖：
  - raw_payload_ref：`external-fixture://content-detail/success#raw`
  - raw payload：由 `XhsAdapter(provider=ExternalFixtureXhsProvider)` 经 `execute_task_with_record()` 产出，不携带 `provider_key`。
  - normalized_result_ref：`external-fixture://content-detail/success#normalized`
  - normalized result：`platform=xhs`、`content_id=66fad51c000000001b0224b8`
  - provider_error_mapping_checked：`true`
  - resource_profile_consumption_checked：`true`
  - resource profile consumption：`account_proxy`
  - resource_lifecycle_disposition_checked：`true`
  - resource lifecycle disposition hint：`null`
  - success release reason：`adapter_completed_without_disposition_hint`
  - failure release reason：`adapter_failed_without_disposition_hint`
  - observability_carrier_checked：`true`
  - observability carrier：adapter / capability / operation / decision status / proof refs
- failure evidence 边界：
  - provider-side failure input：`provider_side_error_code=provider_unavailable`、`source_error=external_sample_timeout`
  - Adapter-owned mapping：`provider_unavailable -> external_sample_unavailable`
  - adapter_mapped_failed_envelope_ref：`external-fixture://content-detail/provider-timeout#adapter-mapped-failed-envelope`
  - Adapter-mapped failed envelope：由 `execute_task_with_record()` 产出，`operation=content_detail_by_url`、`category=platform`、`code=external_sample_unavailable`
  - Core-facing failed envelope 不新增 provider category。

## Core Surface Projection

- core_surface_projection_ref：`docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md#core-surface-projection`
- projection fields：`decision_status`、`error_code`、`failure_category`、`fail_closed`
- provider fields：none

## No-Leakage Evidence

`build_core_surface_no_leakage_evidence()` 审计以下 Core-facing surfaces：

- core projection
- registry discovery：来自 `AdapterRegistry.from_mapping({"xhs": XhsAdapter(provider=...)})`
- core routing：来自 `execute_task_with_record()` 的 adapter selection surface
- TaskRecord：来自 success / failure 两条 `LocalTaskRecordStore` durable records
- resource lifecycle：来自 `LocalResourceLifecycleStore` acquire / release snapshot
- resource trace：来自 `LocalResourceTraceStore`
- Core-facing failed envelope：来自 failure sample 的 terminal envelope

结果：

| surface | status | forbidden_field_paths | forbidden_value_paths |
|---|---|---|---|
| `core_projection` | `passed` | `()` | `()` |
| `registry_discovery` | `passed` | `()` | `()` |
| `core_routing` | `passed` | `()` | `()` |
| `task_record` | `passed` | `()` | `()` |
| `resource_lifecycle` | `passed` | `()` | `()` |
| `resource_trace` | `passed` | `()` | `()` |
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

机器可读验证载体：`docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-validation.json`，并绑定 `report_snapshot_sha256=31974bc000995d0f746d6b9132afa818dc85e7971ace8b0e355c918a66f9ba76`。

| validation | command | result |
|---|---|---|
| external provider sample evidence | `python3 -m unittest tests.runtime.test_real_provider_sample_evidence` | `pass` |
| compatibility decision / no-leakage / sample | `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard tests.runtime.test_real_provider_sample_evidence` | `pass` |
| dual reference / third-party entry / API CLI same path | `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_cli_http_same_path` | `pass` |

这些命令的 gate truth 由上述 JSON 载体承载；`build_required_validation_evidence()` 只消费该结构化载体，不在 report 构建过程中启动测试子进程。任一结构化命令状态不是 `pass` 时，report 必须返回 `status=fail` 与 `required_validation_not_pass`。

## Boundary

- 本 evidence 不声明任何指定 provider 产品正式支持。
- 本 evidence 不引入 provider selector、fallback、marketplace 或 Core provider registry。
- 本 evidence 不扩大 approved slice 到 search/list/comment/batch/dataset 或发布能力。
- 本 evidence 不替代双参考基线、第三方 Adapter-only entry 或 API / CLI same Core path；这些作为 `v0.9.0` closeout required evidence 继续单独验证。
