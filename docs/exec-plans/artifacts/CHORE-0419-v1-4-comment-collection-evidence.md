# CHORE-0419 v1.4 comment collection evidence

## Purpose

This artifact records sanitized, replayable evidence for `FR-0404` after the #417 runtime carrier and #418 consumer migration merged. It proves `comment_collection` can express comment pages, reply hierarchy, visibility states, cursor resume and fail-closed boundaries without committing raw payloads, source names, external project names or local paths.

## Evidence Summary

- release：`v1.4.0`
- fr_ref：`FR-0404`
- work_item_ref：`#419 / CHORE-0419-v1-4-comment-collection-evidence`
- governing_spec_ref：`docs/specs/FR-0404-comment-collection-contract/`
- predecessor_pr_refs：
  - `#427`
  - `#429`
  - `#430`
- status：`pass`
- covered scenarios：
  - top-level first page / next page
  - reply hierarchy and reply cursor resume
  - empty result
  - deleted / invisible / unavailable item visibility
  - duplicate comment item fail-closed
  - permission denied
  - rate limited
  - target not found
  - platform failed
  - provider or network blocked
  - cursor invalid or expired
  - credential invalid
  - verification required
  - signature or request invalid
  - partial result with parse failure
  - total parse failure with zero successful items

## Structured Evidence Snapshot

`tests.runtime.test_comment_collection_evidence` rebuilds this report from the comment collection contract helpers and compares it to the JSON snapshot below.

<!-- syvert:comment-collection-evidence-json:start -->
```json
{
  "baseline": {
    "baseline_regression_refs": [
      "tests.runtime.test_cli_http_same_path",
      "tests.runtime.test_read_side_collection_evidence"
    ],
    "content_detail_by_url_unchanged": true,
    "fr_0403_collection_behavior_unchanged": true
  },
  "fr_ref": "FR-0404",
  "governing_spec_ref": "docs/specs/FR-0404-comment-collection-contract/",
  "predecessor_pr_refs": [
    "#427",
    "#429",
    "#430"
  ],
  "release": "v1.4.0",
  "report_id": "CHORE-0419-v1-4-comment-collection-evidence",
  "sanitization": {
    "external_project_name_present": false,
    "local_path_present": false,
    "raw_payload_embedded": false,
    "source_alias_only": true
  },
  "scenarios": {
    "credential_invalid": {
      "error_classification": "credential_invalid",
      "item_count": 0,
      "result_status": "complete"
    },
    "cursor_invalid_or_expired": {
      "error_classification": "cursor_invalid_or_expired",
      "item_count": 0,
      "result_status": "complete"
    },
    "duplicate_comment_item": {
      "code": "invalid_comment_collection_contract",
      "message": "CommentItemEnvelope.dedup_key 不能重复"
    },
    "empty_result": {
      "error_classification": "empty_result",
      "result_status": "empty"
    },
    "partial_result_parse_failed": {
      "error_classification": "parse_failed",
      "item_count": 1,
      "result_status": "partial_result"
    },
    "permission_denied": {
      "error_classification": "permission_denied",
      "item_count": 0,
      "result_status": "complete"
    },
    "platform_failed": {
      "error_classification": "platform_failed",
      "item_count": 0,
      "result_status": "complete"
    },
    "provider_or_network_blocked": {
      "error_classification": "provider_or_network_blocked",
      "item_count": 0,
      "result_status": "complete"
    },
    "rate_limited": {
      "error_classification": "rate_limited",
      "item_count": 0,
      "result_status": "complete"
    },
    "reply_hierarchy": {
      "error_classification": "success",
      "parent_comment_ref": "comment:alpha-root-1",
      "reply_cursor_resume": "comment:alpha-root-1",
      "result_status": "complete",
      "root_comment_ref": "comment:alpha-root-1",
      "target_comment_ref": "comment:alpha-root-1"
    },
    "signature_or_request_invalid": {
      "error_classification": "signature_or_request_invalid",
      "item_count": 0,
      "result_status": "complete"
    },
    "target_not_found": {
      "error_classification": "target_not_found",
      "item_count": 0,
      "result_status": "complete"
    },
    "top_level_first_page": {
      "error_classification": "success",
      "has_more": true,
      "item_count": 1,
      "next_continuation": true,
      "reply_cursor": true,
      "result_status": "complete",
      "source_alias": "reference_source_comment_alpha"
    },
    "top_level_next_page": {
      "error_classification": "success",
      "item_count": 1,
      "result_status": "complete",
      "source_alias": "reference_source_comment_beta"
    },
    "total_parse_failed": {
      "error_classification": "parse_failed",
      "item_count": 0,
      "result_status": "complete"
    },
    "verification_required": {
      "error_classification": "verification_required",
      "item_count": 0,
      "result_status": "complete"
    },
    "visibility_states": {
      "error_classification": "success",
      "item_count": 3,
      "result_status": "complete",
      "statuses": [
        "deleted",
        "invisible",
        "unavailable"
      ]
    }
  },
  "status": "pass",
  "two_reference_equivalent_proof": {
    "operation": "comment_collection",
    "public_surface_consistent": true,
    "raw_shape_families": [
      "top_level_page",
      "reply_page",
      "cursor_page"
    ],
    "source_aliases": [
      "reference_source_comment_alpha",
      "reference_source_comment_beta"
    ]
  },
  "validation_commands": [
    "python3 -m unittest tests.runtime.test_comment_collection tests.runtime.test_comment_collection_evidence tests.runtime.test_runtime tests.runtime.test_operation_taxonomy_admission_evidence tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_task_record tests.runtime.test_read_side_collection_evidence tests.runtime.test_platform_leakage tests.runtime.test_cli_http_same_path tests.runtime.test_real_adapter_regression",
    "python3 scripts/spec_guard.py --mode ci --base-sha ac421426eb5f5a4bce1ea5d0ed908962a05b6e5f --head-sha HEAD",
    "python3 scripts/docs_guard.py --mode ci",
    "python3 scripts/workflow_guard.py --mode ci",
    "python3 scripts/version_guard.py --mode ci",
    "python3 scripts/governance_gate.py --mode ci --base-sha ac421426eb5f5a4bce1ea5d0ed908962a05b6e5f --head-sha HEAD --head-ref issue-419-404-v1-4-0-comment-collection-evidence"
  ],
  "work_item_ref": "#419"
}
```
<!-- syvert:comment-collection-evidence-json:end -->

## Scenario Notes

- `reference_source_comment_alpha` and `reference_source_comment_beta` are sanitized source aliases only; the repository does not store their private mapping.
- All raw inputs remain represented as `raw_payload_ref` aliases. No raw response body or platform-private object is committed.
- Visibility evidence distinguishes item-level `deleted`, `invisible` and `unavailable` without exposing platform moderation flags.
- Collection-level failures are fail-closed: `items=[]`, `has_more=false` and no continuation.
- Duplicate comment evidence proves public `dedup_key` collisions are rejected by the comment contract.
- `content_detail_by_url` and `FR-0403` collection behavior are covered only as regression references, not rewritten by this artifact.
