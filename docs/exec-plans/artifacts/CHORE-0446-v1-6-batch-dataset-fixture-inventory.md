# CHORE-0446 v1.6.0 batch / dataset fixture inventory

## Purpose

This artifact records the sanitized fixture and error inventory consumed by `FR-0445` Batch 0. It prepares reviewable evidence for batch execution and dataset sink contracts without introducing runtime behavior, raw fixture payload files, source names, repository names, storage handles, or local filesystem paths.

## Inventory Summary

- release：`v1.6.0`
- fr_ref：`FR-0445`
- work_item_ref：`#446 / CHORE-0446-v1-6-batch-dataset-spec`
- phase_ref：`#444`
- roadmap_anchor：`#382` deferred only
- status：`prepared`
- input contract refs：`FR-0403`、`FR-0404`、`FR-0405`
- guarded constraints：no raw payload files; no source names/local paths; no storage handles/private fields; no scheduler/write-side/content-library/BI/UI; no provider selector/fallback/marketplace.

## Fixture Matrix

| scenario_id | source contract | expected assertion | status |
| --- | --- | --- | --- |
| `batch_all_success_two_items` | `FR-0403` + `FR-0405` | batch result `complete`; two succeeded outcomes; two dataset records | `derived_from_published_contract` |
| `batch_partial_success_permission_denied` | `FR-0404` | one succeeded outcome, one failed outcome, batch `partial_success` | `derived_from_published_contract` |
| `batch_all_failed` | `FR-0403` | all item failures preserved, batch `all_failed`, no dataset records | `derived_from_published_contract` |
| `batch_duplicate_target_first_wins` | `FR-0403` | first `dedup_key` writes dataset record; duplicate is `duplicate_skipped`; batch result remains `complete` when no non-duplicate item fails or resumes | `derived_from_published_contract` |
| `batch_resume_after_interruption` | runtime carrier | interrupted envelope contains processed outcome prefix only; resumed terminal envelope returns canonical combined outcomes | `planned_for_runtime_fixture` |
| `batch_cancel_timeout_resumable` | runtime carrier | cancel/timeout returns `resumable` with processed outcome prefix, sanitized audit, and no outcome for undispatched suffix | `planned_for_runtime_fixture` |
| `dataset_write_readback` | dataset sink | written records can be read by `read_by_dataset(dataset_id)` and `read_by_batch(batch_id)` | `planned_for_runtime_fixture` |
| `dataset_id_lifecycle` | batch request + dataset sink | dataset id is request-supplied or derived from batch id, then surfaced in batch result and dataset records | `planned_for_runtime_fixture` |
| `dataset_audit_replay` | dataset sink | replay uses sanitized evidence refs and normalized payload only | `planned_for_runtime_fixture` |
| `item_resource_boundary` | resource governance | item operation consumes existing resource governance; batch has no login precondition | `derived_from_published_contract` |
| `adapter_identity_sanitized` | `InputTarget` + read-side `SourceTrace` | batch item and dataset record retain Syvert adapter alias without source/provider/private leakage | `planned_for_runtime_fixture` |
| `invalid_target_operation_rejected` | operation taxonomy | target item operation outside stable read-side set is rejected before execution | `planned_for_runtime_fixture` |
| `resume_token_mismatch_rejected` | runtime carrier | resume token with mismatched batch id, target set hash, or next item position is rejected | `planned_for_runtime_fixture` |
| `dataset_sink_write_failure_preserved` | dataset sink | dataset write failure produces failed item outcome, empty dataset record ref, preserved read-side result audit, and failed batch aggregation | `planned_for_runtime_fixture` |
| `normalized_payload_non_json_rejected` | dataset validator | non-JSON-safe normalized payload is rejected fail-closed | `planned_for_runtime_fixture` |
| `carrier_validation_error_reported` | batch/dataset validators | invalid batch or dataset carrier returns contract validation error without raw/private leakage | `planned_for_runtime_fixture` |
| `raw_payload_inline_rejected` | dataset validator | inline raw payload is rejected | `planned_for_runtime_fixture` |
| `storage_handle_rejected` | dataset validator | local path, bucket URL, storage handle, signed URL are rejected | `planned_for_runtime_fixture` |
| `provider_selector_rejected` | batch validator | selector/fallback/marketplace fields are rejected | `planned_for_runtime_fixture` |

## Acceptance For Batch 0

- The matrix covers all success, partial success, partial failure, all failed, duplicate target, resume, cancel/timeout, invalid operation, resume mismatch, dataset write failure, JSON-safety failure, carrier validation failure, dataset replay, and resource boundary.
- The matrix only references published contracts and sanitized aliases.
- No raw payload files or source/path/storage/private fields are introduced.
