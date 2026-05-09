# CHORE-0410 v1.3.0 read-side collection evidence

## Purpose

This artifact records sanitized, replayable evidence for `FR-0403` after the #408 runtime carrier and #409 consumer migration merged. It proves `content_search_by_keyword` and `content_list_by_creator` use one public collection envelope without committing raw payloads, source names, external project names, or local paths.

## Evidence Summary

- release：`v1.3.0`
- fr_ref：`FR-0403`
- work_item_ref：`#410 / CHORE-0410-v1-3-read-side-collection-evidence`
- governing_spec_ref：`docs/specs/FR-0403-read-side-collection-result-cursor-contract/`
- predecessor_pr_refs：
  - `#412`
  - `#413`
- status：`pass`
- covered scenarios：
  - search first page / next page
  - creator first page
  - empty result
  - target not found
  - duplicate item fail-closed
  - cursor invalid or expired
  - permission denied
  - rate limited
  - platform failed
  - provider or network blocked
  - partial result with parse failure
  - credential invalid
  - verification required

## Structured Evidence Snapshot

`tests.runtime.test_read_side_collection_evidence` rebuilds this report from the shared collection contract helpers and compares it to the JSON snapshot below.

<!-- syvert:read-side-collection-evidence-json:start -->
```json
{
  "baseline": {
    "baseline_regression_ref": "tests.runtime.test_cli_http_same_path",
    "content_detail_by_url_unchanged": true
  },
  "fr_ref": "FR-0403",
  "governing_spec_ref": "docs/specs/FR-0403-read-side-collection-result-cursor-contract/",
  "predecessor_pr_refs": [
    "#412",
    "#413"
  ],
  "release": "v1.3.0",
  "report_id": "CHORE-0410-v1-3-read-side-collection-evidence",
  "sanitization": {
    "external_project_name_present": false,
    "local_path_present": false,
    "raw_payload_embedded": false,
    "source_alias_only": true
  },
  "scenarios": {
    "creator_first_page": {
      "has_more": true,
      "item_count": 1,
      "result_status": "complete",
      "source_alias": "reference_source_beta"
    },
    "credential_invalid": {
      "error_classification": "credential_invalid",
      "result_status": "complete"
    },
    "cursor_invalid_or_expired": {
      "error_classification": "cursor_invalid_or_expired",
      "result_status": "complete"
    },
    "duplicate_item": {
      "code": "invalid_collection_contract",
      "message": "CollectionItemEnvelope.dedup_key 不能重复"
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
      "result_status": "complete"
    },
    "platform_failed": {
      "error_classification": "platform_failed",
      "result_status": "complete"
    },
    "provider_or_network_blocked": {
      "error_classification": "provider_or_network_blocked",
      "result_status": "complete"
    },
    "rate_limited": {
      "error_classification": "rate_limited",
      "result_status": "complete"
    },
    "search_first_page": {
      "has_more": true,
      "next_continuation": true,
      "result_status": "complete",
      "source_alias": "reference_source_alpha"
    },
    "search_next_page": {
      "has_more": false,
      "item_count": 1,
      "result_status": "complete",
      "source_alias": "reference_source_beta"
    },
    "target_not_found": {
      "error_classification": "target_not_found",
      "result_status": "complete"
    },
    "verification_required": {
      "error_classification": "verification_required",
      "result_status": "complete"
    }
  },
  "status": "pass",
  "two_reference_equivalent_proof": {
    "operations": [
      "content_search_by_keyword",
      "content_list_by_creator"
    ],
    "public_surface_consistent": true,
    "source_aliases": [
      "reference_source_alpha",
      "reference_source_beta"
    ]
  },
  "validation_commands": [
    "python3 -m unittest tests.runtime.test_read_side_collection tests.runtime.test_read_side_collection_evidence tests.runtime.test_platform_leakage tests.runtime.test_cli_http_same_path tests.runtime.test_real_adapter_regression",
    "python3 scripts/spec_guard.py --mode ci --all",
    "python3 scripts/docs_guard.py --mode ci",
    "python3 scripts/workflow_guard.py --mode ci",
    "python3 scripts/version_guard.py --mode ci"
  ],
  "work_item_ref": "#410"
}
```
<!-- syvert:read-side-collection-evidence-json:end -->

## Scenario Notes

- `reference_source_alpha` and `reference_source_beta` are sanitized source aliases only; they do not map to source names inside repository truth.
- All replayable success scenarios use the same collection carrier and differ only by operation, target, alias, continuation, and result classification.
- Duplicate item evidence is intentionally fail-closed and proves cross-page dedup collisions are rejected at the shared contract layer.
- `target_not_found`, `credential_invalid`, and `verification_required` remain explicit public classifications instead of being flattened into `platform_failed`.
- `content_detail_by_url` remains outside this artifact except for unchanged-baseline regression reference.
