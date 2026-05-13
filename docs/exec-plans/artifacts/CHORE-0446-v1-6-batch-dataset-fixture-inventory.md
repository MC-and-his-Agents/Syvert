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
| `batch_duplicate_target_first_wins` | `FR-0403` | first `dedup_key` writes dataset record; duplicate is `duplicate_skipped` | `derived_from_published_contract` |
| `batch_resume_after_interruption` | runtime carrier | resume token binds batch id, target set hash, next item index | `planned_for_runtime_fixture` |
| `dataset_write_readback` | dataset sink | written records can be read by dataset id and batch id | `planned_for_runtime_fixture` |
| `dataset_audit_replay` | dataset sink | replay uses sanitized evidence refs and normalized payload only | `planned_for_runtime_fixture` |
| `item_resource_boundary` | resource governance | item operation consumes existing resource governance; batch has no login precondition | `derived_from_published_contract` |
| `raw_payload_inline_rejected` | dataset validator | inline raw payload is rejected | `planned_for_runtime_fixture` |
| `storage_handle_rejected` | dataset validator | local path, bucket URL, storage handle, signed URL are rejected | `planned_for_runtime_fixture` |
| `provider_selector_rejected` | batch validator | selector/fallback/marketplace fields are rejected | `planned_for_runtime_fixture` |

## Acceptance For Batch 0

- The matrix covers all success, partial success, partial failure, all failed, duplicate target, resume, dataset replay, and resource boundary.
- The matrix only references published contracts and sanitized aliases.
- No raw payload files or source/path/storage/private fields are introduced.
