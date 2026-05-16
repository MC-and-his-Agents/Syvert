# CHORE-0449 v1.6 batch / dataset evidence

## Purpose

This artifact records sanitized fake/reference evidence for `FR-0445` after the runtime carrier and consumer Work Items merged. It proves Batch / Dataset Foundation can replay partial success/failure, all failed, resume, timeout, duplicate target, dataset replay, resource boundary, and public-carrier leakage prevention without committing raw payload files, real account credentials, source names, local paths, storage handles, or private provider data.

## Evidence Summary

- release：`v1.6.0`
- fr_ref：`FR-0445`
- work_item_ref：`#449 / CHORE-0449-v1-6-batch-dataset-evidence`
- governing_spec_ref：`docs/specs/FR-0445-batch-dataset-core-contract/`
- predecessor_pr_refs：
  - `#451`
  - `#452`
  - `#453`
- status：`pass`
- covered scenarios：
  - partial success / partial failure
  - all failed
  - resume after interruption
  - timeout resumable boundary
  - duplicate target first-wins
  - dataset readback and audit replay
  - item-scoped resource boundary
  - public carrier leakage prevention

## Structured Evidence Snapshot

`tests.runtime.test_batch_dataset_evidence` rebuilds this report from sanitized fake/reference runtime carriers and compares it to the JSON snapshot below.

<!-- syvert:batch-dataset-evidence-json:start -->
```json
{
  "fr_ref": "FR-0445",
  "governing_spec_ref": "docs/specs/FR-0445-batch-dataset-core-contract/",
  "predecessor_pr_refs": [
    "#451",
    "#452",
    "#453"
  ],
  "release": "v1.6.0",
  "replay_matrix": {
    "dataset_sink": "ReferenceDatasetSink",
    "fixture_family": "sanitized_fake_reference",
    "provider_private_data_required": false,
    "raw_payload_files_required": false,
    "runtime_entry": "execute_batch_request",
    "snapshot_rebuilt_by": "tests.runtime.test_batch_dataset_evidence"
  },
  "report_id": "CHORE-0449-v1-6-batch-dataset-evidence",
  "sanitization": {
    "opaque_storage_free": true,
    "path_free": true,
    "private_entity_fields_present": false,
    "provider_routing_policy_present": false,
    "raw_payload_embedded": false,
    "raw_payload_files_required": false,
    "real_account_credentials_required": false,
    "source_alias_only": true
  },
  "scenario_matrix": {
    "all_failed": {
      "dataset_record_count": 0,
      "item_errors_preserved": [
        "permission_denied",
        "permission_denied"
      ],
      "item_statuses": [
        "failed",
        "failed"
      ],
      "result_status": "all_failed"
    },
    "dataset_replay": {
      "raw_payload_files_required": false,
      "read_by_batch_count": 2,
      "read_by_dataset_count": 2,
      "replay_count": 2,
      "replay_record_keys": [
        "adapter_key",
        "batch_id",
        "batch_item_id",
        "dataset_id",
        "dataset_record_id",
        "dedup_key",
        "evidence_ref",
        "normalized_payload",
        "source_operation",
        "target_ref"
      ],
      "result_status": "complete",
      "storage_handles_returned": false
    },
    "duplicate_target": {
      "dataset_record_count": 1,
      "duplicate_wrote_dataset_record": false,
      "item_statuses": [
        "succeeded",
        "duplicate_skipped"
      ],
      "result_status": "complete"
    },
    "partial_success_failure": {
      "dataset_record_count": 1,
      "failed_error_code": "permission_denied",
      "item_statuses": [
        "succeeded",
        "failed"
      ],
      "raw_payload_files_required": false,
      "result_status": "partial_success"
    },
    "public_carrier_leakage_prevention": {
      "fail_closed_cases": {
        "dataset_opaque_storage_field": "invalid_dataset_record",
        "dataset_path_ref": "unsafe_ref",
        "dataset_private_entity_field": "unsafe_public_payload",
        "dataset_raw_payload_inline_field": "invalid_dataset_record",
        "result_opaque_storage_audit": "unsafe_public_payload",
        "result_routing_resume": "unsafe_ref"
      },
      "raw_payload_files_required": false,
      "sanitized_aliases_only": true
    },
    "resource_boundary": {
      "batch_admission_requires_real_account": false,
      "dataset_record_count": 0,
      "item_error_code": "invalid_resource_requirement",
      "item_resource_governance_preserved": true
    },
    "resume": {
      "dataset_record_count": 2,
      "dedup_write_state_reused": true,
      "interrupted_outcome_count": 1,
      "interrupted_result_status": "resumable",
      "resume_next_item_index": 1,
      "terminal_outcome_count": 2,
      "terminal_result_status": "complete"
    },
    "timeout_resumable": {
      "audit_finished": false,
      "audit_stop_reason": "execution_timeout",
      "failed_error_code": "execution_timeout",
      "item_statuses": [
        "failed"
      ],
      "result_status": "resumable",
      "resume_next_item_index": 1,
      "undispatched_suffix_outcome_count": 0
    }
  },
  "status": "pass",
  "validation_commands": [
    "python3 -m unittest tests.runtime.test_batch_dataset_evidence tests.runtime.test_batch_dataset tests.runtime.test_task_record tests.runtime.test_cli_http_same_path tests.runtime.test_operation_taxonomy_consumers",
    "python3 -m unittest discover",
    "python3 scripts/spec_guard.py --mode ci --all",
    "python3 scripts/docs_guard.py --mode ci",
    "python3 scripts/workflow_guard.py --mode ci",
    "python3 scripts/version_guard.py --mode ci",
    "python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD",
    "git diff --check"
  ],
  "work_item_ref": "#449"
}
```
<!-- syvert:batch-dataset-evidence-json:end -->

## Scenario Notes

- All evidence is rebuilt from sanitized fake/reference carriers through `execute_batch_request` and `ReferenceDatasetSink`.
- Dataset replay returns public record metadata and normalized payload only; it does not require raw payload files or storage handles.
- Resource boundary evidence keeps batch admission independent from real accounts while proving item execution still consumes existing resource governance.
- Leakage prevention cases are fail-closed by public carrier validators and record only error codes, not private values.
