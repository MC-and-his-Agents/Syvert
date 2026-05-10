# CHORE-0418 v1.4 comment collection consumer migration

## 关联信息

- item_key：`CHORE-0418-v1-4-comment-collection-consumer-migration`
- Issue：`#418`
- item_type：`CHORE`
- release：`v1.4.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#404`
- 关联 spec：`docs/specs/FR-0404-comment-collection-contract/spec.md`
- 关联 decision：
- 关联 PR：`#430`
- 状态：`active`
- active 收口事项：`CHORE-0418-v1-4-comment-collection-consumer-migration`

## 目标

- Work Item: #418
- Parent FR: #404
- Scope: migrate `comment_collection` consumers after #417 runtime carrier merge.
- Out of scope: #419 evidence, #420 release closeout, #405 creator/media, batch/dataset/scheduled execution.

## 改动记录

- Adapter resource requirement validation now admits `comment_collection` against the same content-detail-derived account/proxy profile compatibility path already used by #403 read-side collection consumers.
- Adapter/Provider compatibility decision now covers `comment_collection + content + paginated` as matched, unmatched, and invalid_contract.
- Operation taxonomy admission evidence now reflects post-consumer-migration truth: `comment_collection` can match through runtime compatibility after the #418 migration path is present.
- Runtime execution now maps `comment_collection + paginated` to managed resource slots before adapter execution and derives the concrete slots from the matched comment resource profile instead of hard-coding `account/proxy`.
- TaskRecord codec now round-trips a persisted `comment_collection` terminal envelope and keeps target/content query truth aligned with the request snapshot.
- #403 collection consumers and `content_detail_by_url` behavior remain unchanged.

## 验证记录

- `python3 -m unittest tests.runtime.test_operation_taxonomy_consumers.OperationTaxonomyConsumerMigrationTests.test_requirement_offer_and_decision_accept_comment_collection_runtime_slice tests.runtime.test_adapter_provider_compatibility_decision.AdapterProviderCompatibilityDecisionTests.test_decision_matches_comment_collection_slice tests.runtime.test_adapter_provider_compatibility_decision.AdapterProviderCompatibilityDecisionTests.test_decision_returns_unmatched_for_comment_collection_profile_mismatch tests.runtime.test_adapter_provider_compatibility_decision.AdapterProviderCompatibilityDecisionTests.test_decision_returns_invalid_contract_for_comment_collection_slice_drift tests.runtime.test_task_record.TaskRecordCodecTests.test_round_trips_comment_collection_record`
- `python3 -m unittest tests.runtime.test_operation_taxonomy_admission_evidence tests.runtime.test_operation_taxonomy_consumers.OperationTaxonomyConsumerMigrationTests.test_requirement_offer_and_decision_accept_comment_collection_runtime_slice tests.runtime.test_adapter_provider_compatibility_decision.AdapterProviderCompatibilityDecisionTests.test_decision_matches_comment_collection_slice`（6 tests）
- `python3 -m unittest tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_builds_comment_collection_success_envelope_from_adapter_payload tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_uses_comment_collection_account_only_profile tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_fails_closed_when_comment_collection_resource_pool_is_empty tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_returns_resource_unavailable_when_runtime_capability_projection_is_unmatched tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_maps_v2_unmatched_profiles_to_resource_unavailable`（5 tests）
- `python3 -m unittest tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_builds_comment_collection_success_envelope_from_adapter_payload tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_uses_comment_collection_account_only_profile tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_fails_closed_when_comment_collection_resource_pool_is_empty tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_releases_bundle_when_host_side_validation_fails_after_acquire tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_settles_success_without_hint_as_available tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_settles_failure_without_hint_as_available tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_applies_invalidating_hint_without_leaking_internal_field tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_derives_trace_store_as_lifecycle_sibling_when_only_lifecycle_store_is_injected tests.runtime.test_resource_capability_evidence.ResourceCapabilityEvidenceTests.test_proxy_shared_evidence_is_exercised_through_runtime_bundle_binding`（9 tests）
- `python3 -m unittest tests.runtime.test_operation_taxonomy_consumers tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_task_record tests.runtime.test_task_record_store tests.runtime.test_runtime tests.runtime.test_read_side_collection tests.runtime.test_comment_collection tests.runtime.test_operation_taxonomy tests.runtime.test_operation_taxonomy_admission_evidence tests.runtime.test_registry tests.runtime.test_resource_capability_evidence tests.runtime.test_platform_leakage tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_version_gate tests.runtime.test_third_party_adapter_contract_entry`（618 tests）
- `python3 -m py_compile syvert/runtime.py syvert/registry.py tests/runtime/test_operation_taxonomy_consumers.py tests/runtime/test_adapter_provider_compatibility_decision.py tests/runtime/test_task_record.py tests/runtime/operation_taxonomy_admission_fixtures.py tests/runtime/test_operation_taxonomy_admission_evidence.py tests/runtime/test_runtime.py`
- `python3 scripts/spec_guard.py --mode ci --base-sha 4e6444f699e81a7447531fee1e1cd6b4edf58154 --head-sha HEAD`
- `python3 scripts/governance_gate.py --mode ci --base-sha 4e6444f699e81a7447531fee1e1cd6b4edf58154 --head-sha HEAD --head-ref issue-418-404-v1-4-0-comment-collection-consumer-migration`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/version_guard.py --mode ci`
- `git diff --check`

## Review finding 处理记录

- PR #430 guardian finding：admission evidence fixture/test still declared pre-migration truth (`compatibility_match_allowed=False` and `invalid_contract` decision) after runtime consumer migration.
- 处理结果：updated admission fixture/test to post-migration truth (`compatibility_match_allowed=True`, `comment_collection` resource requirement, `matched` decision with matched profiles) and reran focused admission coverage plus the full #418 regression subset.
- PR #430 guardian finding：runtime execution did not map `comment_collection + paginated` to managed resource admission/acquire, leaving declared resource profile truth ahead of execution behavior.
- 处理结果：added the runtime resource slot mapping, updated the fake comment adapter declaration, and added a fail-closed empty-resource-pool regression proving adapter execution is skipped when resources cannot be acquired.
- PR #430 guardian finding：the first runtime resource slot fix hard-coded `account+proxy`, which rejected a legal `comment_collection` account-only profile when only account resources were available.
- 处理结果：limited dynamic minimal-profile slot selection to `comment_collection`, added an account-only resource-pool success regression, and reran focused regressions proving existing content/detail proxy evidence still uses `account+proxy`.

## 未决风险

- #418 only aligns consumer/runtime compatibility paths. Sanitized reference evidence remains owned by #419.

## 回滚方式

- Use a revert PR for this Work Item only. #417 runtime carrier remains independently merged on main.

## 最近一次 checkpoint 对应的 head SHA

- `686562f14ab925fe36df5b59bef12d0961eba4af`
