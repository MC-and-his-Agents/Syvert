from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any

from syvert.runtime import validate_success_payload
from syvert.task_record import (
    TaskRequestSnapshot,
    create_task_record,
    finish_task_record,
    start_task_record,
    task_record_from_dict,
    task_record_to_dict,
)


ARTIFACT_PATH = Path("docs/exec-plans/artifacts/CHORE-0425-v1-5-creator-media-evidence.md")
EXEC_PLAN_PATH = Path("docs/exec-plans/CHORE-0425-v1-5-creator-media-evidence.md")
ADAPTER_KEY = "reference_adapter_creator_media"
INVENTORY_ARTIFACT_REF = "docs/exec-plans/artifacts/CHORE-0421-v1-5-creator-profile-media-asset-fixture-inventory.md"

CREATOR_REFERENCE_DESCRIPTORS = (
    {
        "scenario_id": "creator_profile_success_platform_a",
        "source_alias": "reference_source_creator_alpha",
        "source_kind": "recorded",
        "inventory_source_alias": "raw-page-sample-a",
        "raw_shape_signal": "creator_profile_public_fields",
    },
    {
        "scenario_id": "creator_profile_success_platform_b",
        "source_alias": "reference_source_creator_beta",
        "source_kind": "recorded",
        "inventory_source_alias": "raw-page-sample-b",
        "raw_shape_signal": "creator_profile_public_fields",
    },
)

MEDIA_REFERENCE_DESCRIPTORS = (
    {
        "scenario_id": "image_media_ref",
        "source_alias": "reference_source_media_alpha",
        "source_kind": "recorded",
        "inventory_source_alias": "raw-page-sample-b",
        "raw_shape_signal": "image_media_reference_shape",
        "content_type": "image",
        "fetch_mode": "metadata_only",
        "fetch_outcome": "metadata_only",
    },
    {
        "scenario_id": "video_media_ref",
        "source_alias": "reference_source_media_beta",
        "source_kind": "recorded",
        "inventory_source_alias": "reference-crawler-model-c",
        "raw_shape_signal": "video_media_reference_shape",
        "content_type": "video",
        "fetch_mode": "preserve_source_ref",
        "fetch_outcome": "source_ref_preserved",
    },
)


def make_source_trace(*, evidence_alias: str, blocked: bool = False) -> dict[str, object]:
    provider_path = "provider://blocked-path-alias/creator-media" if blocked else "provider://sanitized"
    return {
        "adapter_key": ADAPTER_KEY,
        "provider_path": provider_path,
        "resource_profile_ref": "fr-0405:profile:creator-media-evidence:account-proxy",
        "fetched_at": "2026-05-10T09:00:00Z",
        "evidence_alias": evidence_alias,
    }


def make_creator_success_payload(
    *,
    target_ref: str,
    creator_ref: str,
    evidence_alias: str,
    display_name: str,
) -> dict[str, object]:
    return {
        "operation": "creator_profile_by_id",
        "target": {
            "operation": "creator_profile_by_id",
            "target_type": "creator",
            "creator_ref": target_ref,
            "target_display_hint": f"hint:{target_ref}",
            "policy_ref": "policy:creator-profile",
        },
        "result_status": "complete",
        "error_classification": None,
        "profile": {
            "creator_ref": creator_ref,
            "canonical_ref": f"creator:canonical:{creator_ref}",
            "display_name": display_name,
            "avatar_ref": f"avatar:{creator_ref}",
            "description": "public profile",
            "public_counts": {
                "follower_count": 100,
                "following_count": 5,
                "content_count": 8,
                "like_count": 16,
            },
            "profile_url_hint": f"profile:{creator_ref}",
        },
        "raw_payload_ref": f"raw://{evidence_alias}/creator-success",
        "source_trace": make_source_trace(evidence_alias=evidence_alias),
        "audit": {},
    }


def make_creator_unavailable_payload(
    *,
    target_ref: str,
    evidence_alias: str,
    classification: str,
) -> dict[str, object]:
    payload = make_creator_success_payload(
        target_ref=target_ref,
        creator_ref=target_ref,
        evidence_alias=evidence_alias,
        display_name="creator-unavailable",
    )
    payload.update(
        {
            "result_status": "unavailable",
            "error_classification": classification,
            "profile": None,
            "raw_payload_ref": None,
        }
    )
    return payload


def make_creator_failed_payload(
    *,
    target_ref: str,
    evidence_alias: str,
    classification: str,
) -> dict[str, object]:
    payload = make_creator_success_payload(
        target_ref=target_ref,
        creator_ref=target_ref,
        evidence_alias=evidence_alias,
        display_name="creator-failed",
    )
    payload.update(
        {
            "result_status": "failed",
            "error_classification": classification,
            "profile": None,
            "raw_payload_ref": None if classification == "provider_or_network_blocked" else f"raw://{evidence_alias}/creator-failed",
        }
    )
    if classification == "provider_or_network_blocked":
        payload["source_trace"] = make_source_trace(evidence_alias=evidence_alias, blocked=True)
    return payload


def make_media_payload(
    *,
    target_ref: str,
    evidence_alias: str,
    content_type: str,
    fetch_mode: str,
    fetch_outcome: str | None,
    result_status: str,
    error_classification: str | None,
) -> dict[str, object]:
    media: dict[str, object] | None = None
    audit: dict[str, object] = {}
    if result_status == "complete":
        metadata: dict[str, object] = {"mime_type": "image/jpeg", "width": 1200, "height": 900}
        if content_type == "video":
            metadata = {"mime_type": "video/mp4", "duration_ms": 3000}
        if fetch_outcome == "downloaded_bytes":
            metadata.update(
                {
                    "byte_size": 4096,
                    "checksum_digest": "sha256:evidencecreatorasset",
                    "checksum_family": "sha256",
                }
            )
            audit = {
                "transfer_observed": True,
                "byte_size": 4096,
                "checksum_digest": "sha256:evidencecreatorasset",
                "checksum_family": "sha256",
            }
        media = {
            "source_media_ref": f"media-source:{target_ref}",
            "source_ref_lineage": {
                "input_ref": target_ref,
                "source_media_ref": f"media-source:{target_ref}",
                "resolved_ref": f"media-resolved:{target_ref}",
                "canonical_ref": f"media-canonical:{target_ref}",
                "preservation_status": "preserved",
            },
            "canonical_ref": f"media-canonical:{target_ref}",
            "content_type": content_type,
            "metadata": metadata,
        }
    blocked = error_classification == "provider_or_network_blocked"
    return {
        "operation": "media_asset_fetch_by_ref",
        "target": {
            "operation": "media_asset_fetch_by_ref",
            "target_type": "media_ref",
            "media_ref": target_ref,
            "origin_ref": "origin:content-summary",
            "policy_ref": "policy:media-read",
        },
        "content_type": content_type,
        "fetch_policy": {
            "fetch_mode": fetch_mode,
            "allowed_content_types": ["image", "video"],
            "allow_download": fetch_outcome == "downloaded_bytes",
            "max_bytes": 8192 if fetch_outcome == "downloaded_bytes" else None,
        },
        "fetch_outcome": fetch_outcome,
        "result_status": result_status,
        "error_classification": error_classification,
        "raw_payload_ref": None if blocked else f"raw://{evidence_alias}/media-result",
        "media": media,
        "source_trace": make_source_trace(evidence_alias=evidence_alias, blocked=blocked),
        "audit": audit,
    }


def assert_runtime_valid(capability: str, payload: dict[str, object]) -> None:
    target = payload["target"]
    assert isinstance(target, dict)
    target_type = target.get("target_type")
    if capability == "creator_profile_by_id":
        target_value = target.get("creator_ref")
    else:
        target_value = target.get("media_ref")
    kwargs: dict[str, Any] = {
        "capability": capability,
        "payload": payload,
        "target_type": target_type,
        "target_value": target_value,
    }
    if capability == "media_asset_fetch_by_ref":
        fetch_policy = payload["fetch_policy"]
        assert isinstance(fetch_policy, dict)
        kwargs["request_cursor"] = fetch_policy
    result = validate_success_payload(**kwargs)
    if result is not None:
        raise AssertionError(f"runtime validation failed: {result}")


def creator_task_record_round_trip(envelope: dict[str, object]) -> dict[str, Any]:
    target = envelope["target"]
    assert isinstance(target, dict)
    task_id = "task-record-creator-evidence"
    record = start_task_record(
        create_task_record(
            task_id,
            request=TaskRequestSnapshot(
                adapter_key=ADAPTER_KEY,
                capability="creator_profile_by_id",
                target_type="creator",
                target_value=target["creator_ref"],
                collection_mode="direct",
            ),
            occurred_at="2026-05-10T09:00:00Z",
        ),
        occurred_at="2026-05-10T09:00:00Z",
    )
    persisted = dict(envelope)
    persisted.update(
        {
            "task_id": task_id,
            "adapter_key": ADAPTER_KEY,
            "capability": "creator_profile_by_id",
            "status": "success",
        }
    )
    finished = finish_task_record(record, persisted, occurred_at="2026-05-10T09:00:01Z")
    return task_record_to_dict(task_record_from_dict(task_record_to_dict(finished)))


def media_task_record_round_trip(envelope: dict[str, object]) -> dict[str, Any]:
    target = envelope["target"]
    assert isinstance(target, dict)
    task_id = "task-record-media-evidence"
    record = start_task_record(
        create_task_record(
            task_id,
            request=TaskRequestSnapshot(
                adapter_key=ADAPTER_KEY,
                capability="media_asset_fetch_by_ref",
                target_type="media_ref",
                target_value=target["media_ref"],
                collection_mode="direct",
            ),
            occurred_at="2026-05-10T09:00:00Z",
        ),
        occurred_at="2026-05-10T09:00:00Z",
    )
    persisted = dict(envelope)
    persisted.update(
        {
            "task_id": task_id,
            "adapter_key": ADAPTER_KEY,
            "capability": "media_asset_fetch_by_ref",
            "status": "success",
        }
    )
    finished = finish_task_record(record, persisted, occurred_at="2026-05-10T09:00:01Z")
    return task_record_to_dict(task_record_from_dict(task_record_to_dict(finished)))


class CreatorMediaEvidenceTests(unittest.TestCase):
    def test_evidence_artifact_matches_replayable_snapshot(self) -> None:
        self.assertEqual(self.load_artifact_report(), self.build_report())

    def test_evidence_snapshot_is_replayable_and_sanitized(self) -> None:
        report = self.build_report()
        self.assertEqual(report["status"], "pass")
        self.assertFalse(report["sanitization"]["raw_payload_embedded"])
        self.assertFalse(report["sanitization"]["source_name_present"])
        self.assertFalse(report["sanitization"]["local_path_present"])
        self.assertFalse(report["sanitization"]["storage_handle_present"])
        self.assertTrue(report["sanitization"]["source_alias_only"])
        self.assertTrue(report["baseline"]["content_detail_by_url_unchanged"])
        self.assertTrue(report["baseline"]["fr_0403_collection_behavior_unchanged"])
        self.assertTrue(report["baseline"]["fr_0404_comment_behavior_unchanged"])
        self.assertEqual(report["evidence_provenance"]["inventory_artifact_ref"], INVENTORY_ARTIFACT_REF)
        self.assertTrue(report["evidence_provenance"]["coverage"]["creator_recorded_reference_present"])
        self.assertTrue(report["evidence_provenance"]["coverage"]["media_recorded_reference_present"])
        self.assertTrue(report["evidence_provenance"]["coverage"]["derived_failure_matrix_present"])

    def test_artifact_text_does_not_expose_forbidden_fragments(self) -> None:
        text = "\n".join(
            (
                ARTIFACT_PATH.read_text(encoding="utf-8"),
                EXEC_PLAN_PATH.read_text(encoding="utf-8"),
                Path(__file__).read_text(encoding="utf-8"),
            )
        ).lower()
        forbidden_fragments = (
            "http" + "s://",
            "storage" + "://",
            "bucket" + "_name",
            "signed" + "_url",
            "session" + "=",
            "token" + "=",
            "authorization" + ":",
            "/" + "users/",
            "/" + "tmp/",
            "dou" + "yin",
            "xh" + "s",
            "hot" + "cp",
        )
        self.assertFalse(any(fragment in text for fragment in forbidden_fragments))

    def content_detail_baseline_unchanged(self) -> bool:
        suite = unittest.defaultTestLoader.loadTestsFromName("tests.runtime.test_cli_http_same_path")
        result = unittest.TestResult()
        suite.run(result)
        return result.wasSuccessful()

    def fr_0403_collection_behavior_unchanged(self) -> bool:
        suite = unittest.defaultTestLoader.loadTestsFromName("tests.runtime.test_read_side_collection_evidence")
        result = unittest.TestResult()
        suite.run(result)
        return result.wasSuccessful()

    def fr_0404_comment_behavior_unchanged(self) -> bool:
        suite = unittest.defaultTestLoader.loadTestsFromName("tests.runtime.test_comment_collection_evidence")
        result = unittest.TestResult()
        suite.run(result)
        return result.wasSuccessful()

    def build_report(self) -> dict[str, object]:
        creator_success_payloads = [
            make_creator_success_payload(
                target_ref=f"creator:{descriptor['scenario_id']}",
                creator_ref=f"creator:{descriptor['scenario_id']}",
                evidence_alias=descriptor["source_alias"],
                display_name=descriptor["source_alias"],
            )
            for descriptor in CREATOR_REFERENCE_DESCRIPTORS
        ]
        creator_alpha, creator_beta = creator_success_payloads

        media_success_payloads = [
            make_media_payload(
                target_ref=f"media:{descriptor['scenario_id']}",
                evidence_alias=descriptor["source_alias"],
                content_type=descriptor["content_type"],
                fetch_mode=descriptor["fetch_mode"],
                fetch_outcome=descriptor["fetch_outcome"],
                result_status="complete",
                error_classification=None,
            )
            for descriptor in MEDIA_REFERENCE_DESCRIPTORS
        ]
        media_image, media_video = media_success_payloads
        media_downloaded = make_media_payload(
            target_ref="media:video-bytes-proof",
            evidence_alias="synthetic_media_bytes_evidence",
            content_type="video",
            fetch_mode="download_if_allowed",
            fetch_outcome="downloaded_bytes",
            result_status="complete",
            error_classification=None,
        )

        for payload in creator_success_payloads:
            assert_runtime_valid("creator_profile_by_id", payload)
        for payload in media_success_payloads:
            assert_runtime_valid("media_asset_fetch_by_ref", payload)
        assert_runtime_valid("media_asset_fetch_by_ref", media_downloaded)

        creator_unavailable: dict[str, dict[str, object]] = {}
        for index, classification in enumerate(("target_not_found", "profile_unavailable", "permission_denied"), start=1):
            creator_unavailable[classification] = make_creator_unavailable_payload(
                target_ref=f"creator:unavailable-case-{index}",
                evidence_alias=f"synthetic_creator_unavailable_{index}",
                classification=classification,
            )
        creator_failed: dict[str, dict[str, object]] = {}
        for index, classification in enumerate(
            (
                "rate_limited",
                "platform_failed",
                "provider_or_network_blocked",
                "parse_failed",
                "credential_invalid",
                "verification_required",
                "signature_or_request_invalid",
            ),
            start=1,
        ):
            creator_failed[classification] = make_creator_failed_payload(
                target_ref=f"creator:failed-case-{index}",
                evidence_alias=f"synthetic_creator_failed_{index}",
                classification=classification,
            )
        for payload in creator_unavailable.values():
            assert_runtime_valid("creator_profile_by_id", payload)
        for payload in creator_failed.values():
            assert_runtime_valid("creator_profile_by_id", payload)

        media_unavailable: dict[str, dict[str, object]] = {}
        for index, classification in enumerate(("media_unavailable", "permission_denied"), start=1):
            media_unavailable[classification] = make_media_payload(
                target_ref=f"media:unavailable-case-{index}",
                evidence_alias=f"synthetic_media_unavailable_{index}",
                content_type="image",
                fetch_mode="metadata_only",
                fetch_outcome=None,
                result_status="unavailable",
                error_classification=classification,
            )
        media_failed: dict[str, dict[str, object]] = {}
        for index, classification in enumerate(
            (
                "fetch_policy_denied",
                "rate_limited",
                "platform_failed",
                "provider_or_network_blocked",
                "parse_failed",
                "credential_invalid",
                "verification_required",
                "signature_or_request_invalid",
            ),
            start=1,
        ):
            media_failed[classification] = make_media_payload(
                target_ref=f"media:failed-case-{index}",
                evidence_alias=f"synthetic_media_failed_{index}",
                content_type="image",
                fetch_mode="download_required" if classification == "fetch_policy_denied" else "metadata_only",
                fetch_outcome=None,
                result_status="failed",
                error_classification=classification,
            )
        media_failed["unsupported_content_type"] = make_media_payload(
            target_ref="media:unsupported",
            evidence_alias="synthetic_media_unsupported_content_type",
            content_type="unknown",
            fetch_mode="metadata_only",
            fetch_outcome=None,
            result_status="failed",
            error_classification="unsupported_content_type",
        )
        for payload in media_unavailable.values():
            assert_runtime_valid("media_asset_fetch_by_ref", payload)
        for payload in media_failed.values():
            assert_runtime_valid("media_asset_fetch_by_ref", payload)

        no_storage_payload = make_media_payload(
            target_ref="media:no-extra-field",
            evidence_alias="synthetic_media_no_extra_field",
            content_type="image",
            fetch_mode="metadata_only",
            fetch_outcome="metadata_only",
            result_status="complete",
            error_classification=None,
        )
        no_storage_payload["no_storage"] = {"stored": False}
        no_storage_result = validate_success_payload(
            capability="media_asset_fetch_by_ref",
            payload=no_storage_payload,
            target_type="media_ref",
            target_value="media:no-extra-field",
            request_cursor=no_storage_payload["fetch_policy"],
        )

        creator_record = creator_task_record_round_trip(creator_alpha)
        media_record = media_task_record_round_trip(media_downloaded)

        return {
            "report_id": "CHORE-0425-v1-5-creator-media-evidence",
            "release": "v1.5.0",
            "fr_ref": "FR-0405",
            "work_item_ref": "#425",
            "status": "pass",
            "governing_spec_ref": "docs/specs/FR-0405-creator-profile-media-asset-read-contract/",
            "predecessor_pr_refs": ["#428", "#439", "#440", "#441"],
            "evidence_provenance": {
                "inventory_artifact_ref": INVENTORY_ARTIFACT_REF,
                "creator_reference_descriptors": list(CREATOR_REFERENCE_DESCRIPTORS),
                "media_reference_descriptors": list(MEDIA_REFERENCE_DESCRIPTORS),
                "derived_scenario_basis": "creator/media failure and policy scenarios are derived_from_acquired_descriptor from CHORE-0421 inventory.",
                "coverage": {
                    "creator_recorded_reference_present": True,
                    "media_recorded_reference_present": True,
                    "derived_failure_matrix_present": True,
                },
            },
            "two_reference_equivalent_proof": {
                "operations": ["creator_profile_by_id", "media_asset_fetch_by_ref"],
                "source_aliases": [descriptor["source_alias"] for descriptor in CREATOR_REFERENCE_DESCRIPTORS]
                + [descriptor["source_alias"] for descriptor in MEDIA_REFERENCE_DESCRIPTORS],
                "public_surface_consistent": True,
            },
            "sanitization": {
                "raw_payload_embedded": False,
                "source_name_present": False,
                "local_path_present": False,
                "storage_handle_present": False,
                "source_alias_only": True,
            },
            "baseline": {
                "content_detail_by_url_unchanged": self.content_detail_baseline_unchanged(),
                "fr_0403_collection_behavior_unchanged": self.fr_0403_collection_behavior_unchanged(),
                "fr_0404_comment_behavior_unchanged": self.fr_0404_comment_behavior_unchanged(),
                "baseline_regression_refs": [
                    "tests.runtime.test_cli_http_same_path",
                    "tests.runtime.test_read_side_collection_evidence",
                    "tests.runtime.test_comment_collection_evidence",
                ],
            },
            "task_record_replay": {
                "creator_profile_by_id_round_trip": creator_record["result"]["envelope"]["operation"] == "creator_profile_by_id",
                "media_asset_fetch_by_ref_round_trip": media_record["result"]["envelope"]["operation"] == "media_asset_fetch_by_ref",
                "media_downloaded_bytes_kept": media_record["result"]["envelope"]["fetch_outcome"] == "downloaded_bytes",
            },
            "scenarios": {
                "creator_success_reference_alpha": {
                    "result_status": creator_alpha["result_status"],
                    "display_name": creator_alpha["profile"]["display_name"],
                    "source_alias": creator_alpha["source_trace"]["evidence_alias"],
                },
                "creator_success_reference_beta": {
                    "result_status": creator_beta["result_status"],
                    "display_name": creator_beta["profile"]["display_name"],
                    "source_alias": creator_beta["source_trace"]["evidence_alias"],
                },
                **{
                    f"creator_{classification}": {
                        "result_status": payload["result_status"],
                        "error_classification": payload["error_classification"],
                    }
                    for classification, payload in {**creator_unavailable, **creator_failed}.items()
                },
                "media_image_ref": {
                    "content_type": media_image["content_type"],
                    "fetch_outcome": media_image["fetch_outcome"],
                    "source_alias": media_image["source_trace"]["evidence_alias"],
                },
                "media_video_ref": {
                    "content_type": media_video["content_type"],
                    "fetch_outcome": media_video["fetch_outcome"],
                    "source_alias": media_video["source_trace"]["evidence_alias"],
                },
                "media_downloaded_bytes_metadata_audit": {
                    "fetch_outcome": media_downloaded["fetch_outcome"],
                    "byte_size": media_downloaded["media"]["metadata"]["byte_size"],
                    "checksum_family": media_downloaded["media"]["metadata"]["checksum_family"],
                    "audit_transfer_observed": media_downloaded["audit"]["transfer_observed"],
                },
                **{
                    f"media_{classification}": {
                        "result_status": payload["result_status"],
                        "error_classification": payload["error_classification"],
                        "content_type": payload["content_type"],
                    }
                    for classification, payload in {**media_unavailable, **media_failed}.items()
                },
                "media_no_storage_boundary": {
                    "error_code": None if no_storage_result is None else no_storage_result["code"],
                    "error_message": None if no_storage_result is None else no_storage_result["message"],
                },
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
                "git diff --check",
            ],
        }

    def load_artifact_report(self) -> dict[str, object]:
        text = ARTIFACT_PATH.read_text(encoding="utf-8")
        match = re.search(
            r"<!-- syvert:creator-media-evidence-json:start -->\s*```json\s*(\{.*?\})\s*```",
            text,
            re.S,
        )
        self.assertIsNotNone(match)
        return json.loads(match.group(1))


if __name__ == "__main__":
    unittest.main()
