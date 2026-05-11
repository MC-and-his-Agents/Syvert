# CHORE-0425 v1.5 creator media evidence

## Purpose

This artifact records sanitized, replayable evidence for `FR-0405` after creator/media runtime carriers and consumer migration merged. It proves `creator_profile_by_id` and `media_asset_fetch_by_ref` expose a stable public contract across two reference shapes without committing raw payload files, source names, local paths, or storage handles.

## Evidence Summary

- release：`v1.5.0`
- fr_ref：`FR-0405`
- work_item_ref：`#425 / CHORE-0425-v1-5-creator-media-evidence`
- governing_spec_ref：`docs/specs/FR-0405-creator-profile-media-asset-read-contract/`
- predecessor_pr_refs：
  - `#428`
  - `#439`
  - `#440`
  - `#441`
- status：`pass`
- covered scenarios：
  - creator success reference A/B
  - creator not found / unavailable / permission denied
  - creator rate limit / platform failed / provider blocked / parse failed / credential invalid / verification required / signature invalid
  - media image / video / metadata-only / source-ref-preserved / downloaded-bytes metadata + audit
  - media unavailable / unsupported content type / fetch policy denied
  - media permission denied / rate limit / platform failed / provider blocked / parse failed / credential invalid / verification required / signature invalid
  - media no-storage boundary fail-closed

## Structured Evidence Snapshot

`tests.runtime.test_creator_media_evidence` rebuilds this report from runtime + TaskRecord contract helpers and compares it to the JSON snapshot below.

<!-- syvert:creator-media-evidence-json:start -->
```json
{
  "baseline": {
    "baseline_regression_refs": [
      "tests.runtime.test_cli_http_same_path",
      "tests.runtime.test_read_side_collection_evidence",
      "tests.runtime.test_comment_collection_evidence"
    ],
    "content_detail_by_url_unchanged": true,
    "fr_0403_collection_behavior_unchanged": true,
    "fr_0404_comment_behavior_unchanged": true
  },
  "evidence_provenance": {
    "coverage": {
      "creator_recorded_reference_present": true,
      "derived_failure_matrix_present": true,
      "inventory_matrix_replayed": true,
      "media_recorded_reference_present": true
    },
    "creator_reference_descriptors": [
      {
        "inventory_source_alias": "raw-page-sample-a",
        "raw_shape_signal": "creator_profile_public_fields",
        "scenario_id": "creator_profile_success_platform_a",
        "source_alias": "reference_source_creator_alpha",
        "source_kind": "recorded"
      },
      {
        "inventory_source_alias": "raw-page-sample-b",
        "raw_shape_signal": "creator_profile_public_fields",
        "scenario_id": "creator_profile_success_platform_b",
        "source_alias": "reference_source_creator_beta",
        "source_kind": "recorded"
      }
    ],
    "derived_scenario_basis": "creator/media failure and policy scenarios are derived_from_acquired_descriptor from CHORE-0421 inventory.",
    "inventory_artifact_ref": "docs/exec-plans/artifacts/CHORE-0421-v1-5-creator-profile-media-asset-fixture-inventory.md",
    "inventory_matrix_bindings": [
      {
        "raw_shape_signal": "public creator profile response with id, display name, avatar, description, and public counters",
        "scenario_id": "creator_profile_success_platform_a",
        "source_kind": "recorded",
        "status": "acquired_sanitized_descriptor"
      },
      {
        "raw_shape_signal": "second reference public creator model with different field names and optional counters",
        "scenario_id": "creator_profile_success_platform_b",
        "source_kind": "recorded",
        "status": "acquired_sanitized_descriptor"
      },
      {
        "raw_shape_signal": "content/media object exposes image-like media reference",
        "scenario_id": "image_media_ref",
        "source_kind": "recorded",
        "status": "acquired_sanitized_descriptor"
      },
      {
        "raw_shape_signal": "content/media object exposes video-like media reference",
        "scenario_id": "video_media_ref",
        "source_kind": "recorded",
        "status": "acquired_sanitized_descriptor"
      },
      {
        "raw_shape_signal": "media content type is recognized and supported but excluded by `allowed_content_types`",
        "scenario_id": "media_policy_content_type_denied",
        "source_kind": "synthetic",
        "status": "derived_from_acquired_descriptor"
      },
      {
        "raw_shape_signal": "sanitized source ref lineage cannot be preserved",
        "scenario_id": "media_source_ref_lineage_denied",
        "source_kind": "synthetic",
        "status": "derived_from_acquired_descriptor"
      },
      {
        "raw_shape_signal": "`download_if_allowed` request exceeds policy/cost boundary but source ref lineage is available",
        "scenario_id": "media_large_asset_download_if_allowed_downgrade",
        "source_kind": "synthetic",
        "status": "derived_from_acquired_descriptor"
      }
    ],
    "media_reference_descriptors": [
      {
        "content_type": "image",
        "fetch_mode": "metadata_only",
        "fetch_outcome": "metadata_only",
        "inventory_source_alias": "raw-page-sample-b",
        "raw_shape_signal": "image_media_reference_shape",
        "scenario_id": "image_media_ref",
        "source_alias": "reference_source_media_alpha",
        "source_kind": "recorded"
      },
      {
        "content_type": "video",
        "fetch_mode": "preserve_source_ref",
        "fetch_outcome": "source_ref_preserved",
        "inventory_source_alias": "reference-crawler-model-c",
        "raw_shape_signal": "video_media_reference_shape",
        "scenario_id": "video_media_ref",
        "source_alias": "reference_source_media_beta",
        "source_kind": "recorded"
      }
    ]
  },
  "fr_ref": "FR-0405",
  "governing_spec_ref": "docs/specs/FR-0405-creator-profile-media-asset-read-contract/",
  "predecessor_pr_refs": [
    "#428",
    "#439",
    "#440",
    "#441"
  ],
  "release": "v1.5.0",
  "report_id": "CHORE-0425-v1-5-creator-media-evidence",
  "sanitization": {
    "local_path_present": false,
    "raw_payload_embedded": false,
    "source_alias_only": true,
    "source_name_present": false,
    "storage_handle_present": false
  },
  "scenarios": {
    "creator_credential_invalid": {
      "error_classification": "credential_invalid",
      "result_status": "failed"
    },
    "creator_parse_failed": {
      "error_classification": "parse_failed",
      "result_status": "failed"
    },
    "creator_permission_denied": {
      "error_classification": "permission_denied",
      "result_status": "unavailable"
    },
    "creator_platform_failed": {
      "error_classification": "platform_failed",
      "result_status": "failed"
    },
    "creator_profile_unavailable": {
      "error_classification": "profile_unavailable",
      "result_status": "unavailable"
    },
    "creator_provider_or_network_blocked": {
      "error_classification": "provider_or_network_blocked",
      "result_status": "failed"
    },
    "creator_rate_limited": {
      "error_classification": "rate_limited",
      "result_status": "failed"
    },
    "creator_signature_or_request_invalid": {
      "error_classification": "signature_or_request_invalid",
      "result_status": "failed"
    },
    "creator_success_reference_alpha": {
      "display_name": "reference_source_creator_alpha",
      "result_status": "complete",
      "source_alias": "reference_source_creator_alpha"
    },
    "creator_success_reference_beta": {
      "display_name": "reference_source_creator_beta",
      "result_status": "complete",
      "source_alias": "reference_source_creator_beta"
    },
    "creator_target_not_found": {
      "error_classification": "target_not_found",
      "result_status": "unavailable"
    },
    "creator_verification_required": {
      "error_classification": "verification_required",
      "result_status": "failed"
    },
    "media_credential_invalid": {
      "content_type": "image",
      "error_classification": "credential_invalid",
      "result_status": "failed"
    },
    "media_download_if_allowed_downgrade": {
      "fetch_mode": "download_if_allowed",
      "fetch_outcome": "source_ref_preserved",
      "result_status": "complete"
    },
    "media_downloaded_bytes_metadata_audit": {
      "audit_transfer_observed": true,
      "byte_size": 4096,
      "checksum_family": "sha256",
      "fetch_outcome": "downloaded_bytes"
    },
    "media_fetch_policy_denied": {
      "content_type": "image",
      "error_classification": "fetch_policy_denied",
      "result_status": "failed"
    },
    "media_image_ref": {
      "content_type": "image",
      "fetch_outcome": "metadata_only",
      "source_alias": "reference_source_media_alpha"
    },
    "media_media_unavailable": {
      "content_type": "image",
      "error_classification": "media_unavailable",
      "result_status": "unavailable"
    },
    "media_no_storage_boundary": {
      "error_code": "invalid_adapter_success_payload",
      "error_message": "media asset fetch result 不得包含未规约 no_storage 字段"
    },
    "media_parse_failed": {
      "content_type": "image",
      "error_classification": "parse_failed",
      "result_status": "failed"
    },
    "media_permission_denied": {
      "content_type": "image",
      "error_classification": "permission_denied",
      "result_status": "unavailable"
    },
    "media_platform_failed": {
      "content_type": "image",
      "error_classification": "platform_failed",
      "result_status": "failed"
    },
    "media_policy_content_type_denied": {
      "allowed_content_types": [
        "image"
      ],
      "content_type": "video",
      "error_classification": "fetch_policy_denied",
      "result_status": "failed"
    },
    "media_provider_or_network_blocked": {
      "content_type": "image",
      "error_classification": "provider_or_network_blocked",
      "result_status": "failed"
    },
    "media_rate_limited": {
      "content_type": "image",
      "error_classification": "rate_limited",
      "result_status": "failed"
    },
    "media_signature_or_request_invalid": {
      "content_type": "image",
      "error_classification": "signature_or_request_invalid",
      "result_status": "failed"
    },
    "media_source_ref_lineage_denied": {
      "error_classification": "fetch_policy_denied",
      "fetch_mode": "preserve_source_ref",
      "result_status": "failed"
    },
    "media_unsupported_content_type": {
      "content_type": "unknown",
      "error_classification": "unsupported_content_type",
      "result_status": "failed"
    },
    "media_verification_required": {
      "content_type": "image",
      "error_classification": "verification_required",
      "result_status": "failed"
    },
    "media_video_ref": {
      "content_type": "video",
      "fetch_outcome": "source_ref_preserved",
      "source_alias": "reference_source_media_beta"
    }
  },
  "status": "pass",
  "task_record_replay": {
    "creator_profile_by_id_round_trip": true,
    "media_asset_fetch_by_ref_round_trip": true,
    "media_downloaded_bytes_kept": true
  },
  "two_reference_equivalent_proof": {
    "operations": [
      "creator_profile_by_id",
      "media_asset_fetch_by_ref"
    ],
    "public_surface_consistent": true,
    "source_aliases": [
      "reference_source_creator_alpha",
      "reference_source_creator_beta",
      "reference_source_media_alpha",
      "reference_source_media_beta"
    ]
  },
  "validation_commands": [
    "python3 -m unittest tests.runtime.test_creator_media_evidence",
    "python3 -m unittest tests.runtime.test_creator_media_evidence tests.runtime.test_runtime tests.runtime.test_task_record tests.runtime.test_platform_leakage",
    "python3 -m unittest tests.runtime.test_read_side_collection_evidence tests.runtime.test_comment_collection_evidence tests.runtime.test_cli_http_same_path",
    "python3 -m unittest discover -s tests -p 'test*.py'",
    "python3 scripts/spec_guard.py --mode ci --all",
    "python3 scripts/docs_guard.py --mode ci",
    "python3 scripts/workflow_guard.py --mode ci",
    "python3 scripts/version_guard.py --mode ci",
    "python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD",
    "git diff --check"
  ],
  "work_item_ref": "#425"
}
```
<!-- syvert:creator-media-evidence-json:end -->

## Scenario Notes

- Source mappings remain private and are represented only by sanitized aliases.
- Raw payload files are not committed; all scenario inputs are synthetic or alias-based carrier projections.
- TaskRecord replay evidence validates creator/media envelopes against durable contract validation paths, not only runtime payload validation.
- `no_storage` is treated as a fail-closed non-contract field and is validated as an explicit rejection scenario.
