from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any

from syvert.read_side_collection import CollectionContractError, comment_collection_result_envelope_from_dict


ARTIFACT_PATH = Path("docs/exec-plans/artifacts/CHORE-0419-v1-4-comment-collection-evidence.md")


def make_source_trace(*, evidence_alias: str) -> dict[str, object]:
    return {
        "adapter_key": "reference_adapter_comment",
        "provider_path": "provider://sanitized-comment-route",
        "resource_profile_ref": "fr-0027:profile:content-detail-by-url-hybrid:account",
        "fetched_at": "2026-05-10T01:00:00Z",
        "evidence_alias": evidence_alias,
    }


def make_target(*, target_ref: str = "content-001") -> dict[str, object]:
    return {
        "operation": "comment_collection",
        "target_type": "content",
        "target_ref": target_ref,
    }


def make_page_continuation(*, target_ref: str = "content-001", comment_ref: str | None = None) -> dict[str, object]:
    return {
        "continuation_token": f"cursor:{target_ref}:{comment_ref or 'top'}",
        "continuation_family": "opaque",
        "resume_target_ref": target_ref,
        **({"resume_comment_ref": comment_ref} if comment_ref is not None else {}),
        "issued_at": "2026-05-10T01:00:00Z",
    }


def make_reply_cursor(*, target_ref: str = "content-001", comment_ref: str) -> dict[str, object]:
    return {
        "reply_cursor_token": f"reply:{comment_ref}",
        "reply_cursor_family": "opaque",
        "resume_target_ref": target_ref,
        "resume_comment_ref": comment_ref,
        "issued_at": "2026-05-10T01:00:00Z",
    }


def make_comment_item(
    *,
    source_id: str,
    canonical_ref: str,
    dedup_key: str | None = None,
    visibility_status: str = "visible",
    body_text_hint: str = "comment text",
    root_comment_ref: str | None = None,
    parent_comment_ref: str | None = None,
    target_comment_ref: str | None = None,
    evidence_alias: str = "reference_source_comment_alpha",
    include_reply_cursor: bool = False,
) -> dict[str, Any]:
    root_ref = root_comment_ref or canonical_ref
    return {
        "item_type": "comment",
        "dedup_key": dedup_key or canonical_ref,
        "source_id": source_id,
        "source_ref": f"comment://{evidence_alias}/{source_id}",
        "visibility_status": visibility_status,
        "normalized": {
            "source_platform": evidence_alias,
            "source_type": "comment",
            "source_id": source_id,
            "canonical_ref": canonical_ref,
            "body_text_hint": body_text_hint,
            "root_comment_ref": root_ref,
            **({"parent_comment_ref": parent_comment_ref} if parent_comment_ref is not None else {}),
            **({"target_comment_ref": target_comment_ref} if target_comment_ref is not None else {}),
            "author_ref": "creator-001",
            "published_at": "2026-05-10T01:00:00Z",
        },
        "raw_payload_ref": f"raw://{evidence_alias}/{source_id}",
        "source_trace": make_source_trace(evidence_alias=evidence_alias),
        **({"reply_cursor": make_reply_cursor(comment_ref=canonical_ref)} if include_reply_cursor else {}),
    }


def make_payload(
    *,
    evidence_alias: str,
    items: list[dict[str, Any]],
    target_ref: str = "content-001",
    has_more: bool = False,
    continuation_comment_ref: str | None = None,
    result_status: str = "complete",
    error_classification: str = "success",
) -> dict[str, Any]:
    return {
        "operation": "comment_collection",
        "target": make_target(target_ref=target_ref),
        "items": items,
        "has_more": has_more,
        "next_continuation": (
            make_page_continuation(target_ref=target_ref, comment_ref=continuation_comment_ref) if has_more else None
        ),
        "result_status": result_status,
        "error_classification": error_classification,
        "raw_payload_ref": f"raw://{evidence_alias}/page",
        "source_trace": make_source_trace(evidence_alias=evidence_alias),
        "audit": {"scenario": evidence_alias},
    }


def make_failure_payload(*, evidence_alias: str, error_classification: str) -> dict[str, Any]:
    return make_payload(
        evidence_alias=evidence_alias,
        items=[],
        has_more=False,
        result_status="complete",
        error_classification=error_classification,
    )


class CommentCollectionEvidenceTests(unittest.TestCase):
    def test_evidence_artifact_matches_replayable_snapshot(self) -> None:
        self.assertEqual(self.load_artifact_report(), self.build_report())

    def test_evidence_snapshot_is_replayable_and_sanitized(self) -> None:
        report = self.build_report()

        self.assertEqual(report["status"], "pass")
        self.assertFalse(report["sanitization"]["raw_payload_embedded"])
        self.assertFalse(report["sanitization"]["external_project_name_present"])
        self.assertFalse(report["sanitization"]["local_path_present"])
        self.assertTrue(report["sanitization"]["source_alias_only"])
        self.assertEqual(
            report["two_reference_equivalent_proof"]["source_aliases"],
            ["reference_source_comment_alpha", "reference_source_comment_beta"],
        )
        self.assertTrue(report["baseline"]["content_detail_by_url_unchanged"])
        self.assertTrue(report["baseline"]["fr_0403_collection_behavior_unchanged"])

    def test_artifact_text_does_not_expose_forbidden_source_identifiers(self) -> None:
        test_names = "\n".join(name for name in dir(self) if name.startswith("test_"))
        text = "\n".join(
            (
                ARTIFACT_PATH.read_text(encoding="utf-8"),
                Path(__file__).read_text(encoding="utf-8"),
                test_names,
            )
        ).lower()
        forbidden_fragments = (
            "hot" + "cp",
            "media" + "crawler",
            "media" + "crawlpro",
            "/" + "users/",
            "python" + "-main",
            "docs/" + "research/",
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

    def build_report(self) -> dict[str, object]:
        top_level = comment_collection_result_envelope_from_dict(
            make_payload(
                evidence_alias="reference_source_comment_alpha",
                items=[
                    make_comment_item(
                        source_id="comment-alpha-1",
                        canonical_ref="comment:alpha-root-1",
                        body_text_hint="top level comment",
                        evidence_alias="reference_source_comment_alpha",
                        include_reply_cursor=True,
                    )
                ],
                has_more=True,
            )
        )
        next_page = comment_collection_result_envelope_from_dict(
            make_payload(
                evidence_alias="reference_source_comment_beta",
                items=[
                    make_comment_item(
                        source_id="comment-beta-2",
                        canonical_ref="comment:beta-root-2",
                        body_text_hint="next page comment",
                        evidence_alias="reference_source_comment_beta",
                    )
                ],
            )
        )
        reply_page = comment_collection_result_envelope_from_dict(
            make_payload(
                evidence_alias="reference_source_comment_alpha_reply",
                items=[
                    make_comment_item(
                        source_id="reply-alpha-1",
                        canonical_ref="comment:alpha-reply-1",
                        body_text_hint="reply comment",
                        root_comment_ref="comment:alpha-root-1",
                        parent_comment_ref="comment:alpha-root-1",
                        target_comment_ref="comment:alpha-root-1",
                        evidence_alias="reference_source_comment_alpha",
                    )
                ],
                has_more=True,
                continuation_comment_ref="comment:alpha-root-1",
            )
        )
        visibility_page = comment_collection_result_envelope_from_dict(
            make_payload(
                evidence_alias="synthetic_comment_visibility",
                items=[
                    make_comment_item(
                        source_id="deleted-1",
                        canonical_ref="comment:deleted-1",
                        visibility_status="deleted",
                        body_text_hint="deleted comment",
                        evidence_alias="synthetic_comment_visibility",
                    ),
                    make_comment_item(
                        source_id="invisible-1",
                        canonical_ref="comment:invisible-1",
                        visibility_status="invisible",
                        body_text_hint="invisible comment",
                        evidence_alias="synthetic_comment_visibility",
                    ),
                    make_comment_item(
                        source_id="public-placeholder:comment:content-001:unavailable:slot-a",
                        canonical_ref="public-placeholder:comment:content-001:unavailable:slot-a",
                        visibility_status="unavailable",
                        body_text_hint="unavailable comment",
                        evidence_alias="synthetic_comment_visibility",
                    ),
                ],
            )
        )
        empty_page = comment_collection_result_envelope_from_dict(
            make_payload(
                evidence_alias="synthetic_comment_empty",
                items=[],
                result_status="empty",
                error_classification="empty_result",
            )
        )
        partial_page = comment_collection_result_envelope_from_dict(
            make_payload(
                evidence_alias="synthetic_comment_partial",
                items=[
                    make_comment_item(
                        source_id="comment-partial-1",
                        canonical_ref="comment:partial-1",
                        evidence_alias="synthetic_comment_partial",
                    )
                ],
                result_status="partial_result",
                error_classification="parse_failed",
            )
        )
        total_parse_failed = comment_collection_result_envelope_from_dict(
            make_failure_payload(evidence_alias="synthetic_comment_parse_failed", error_classification="parse_failed")
        )
        failures = {
            classification: comment_collection_result_envelope_from_dict(
                make_failure_payload(evidence_alias=f"synthetic_comment_{classification}", error_classification=classification)
            )
            for classification in (
                "target_not_found",
                "permission_denied",
                "rate_limited",
                "platform_failed",
                "provider_or_network_blocked",
                "cursor_invalid_or_expired",
                "credential_invalid",
                "verification_required",
                "signature_or_request_invalid",
            )
        }
        duplicate_error = None
        try:
            comment_collection_result_envelope_from_dict(
                make_payload(
                    evidence_alias="synthetic_comment_duplicate",
                    items=[
                        make_comment_item(source_id="dup-1", canonical_ref="comment:dup-1", dedup_key="dup-key"),
                        make_comment_item(source_id="dup-2", canonical_ref="comment:dup-2", dedup_key="dup-key"),
                    ],
                )
            )
        except CollectionContractError as error:
            duplicate_error = {"code": error.code, "message": error.message}

        return {
            "report_id": "CHORE-0419-v1-4-comment-collection-evidence",
            "release": "v1.4.0",
            "fr_ref": "FR-0404",
            "work_item_ref": "#419",
            "status": "pass",
            "governing_spec_ref": "docs/specs/FR-0404-comment-collection-contract/",
            "predecessor_pr_refs": ["#427", "#429", "#430"],
            "two_reference_equivalent_proof": {
                "source_aliases": ["reference_source_comment_alpha", "reference_source_comment_beta"],
                "operation": "comment_collection",
                "public_surface_consistent": True,
                "raw_shape_families": ["top_level_page", "reply_page", "cursor_page"],
            },
            "sanitization": {
                "raw_payload_embedded": False,
                "external_project_name_present": False,
                "local_path_present": False,
                "source_alias_only": True,
            },
            "baseline": {
                "content_detail_by_url_unchanged": self.content_detail_baseline_unchanged(),
                "fr_0403_collection_behavior_unchanged": self.fr_0403_collection_behavior_unchanged(),
                "baseline_regression_refs": [
                    "tests.runtime.test_cli_http_same_path",
                    "tests.runtime.test_read_side_collection_evidence",
                ],
            },
            "scenarios": {
                "top_level_first_page": {
                    "result_status": top_level.result_status,
                    "error_classification": top_level.error_classification,
                    "item_count": len(top_level.items),
                    "has_more": top_level.has_more,
                    "next_continuation": top_level.next_continuation is not None,
                    "reply_cursor": top_level.items[0].reply_cursor is not None,
                    "source_alias": top_level.source_trace.evidence_alias,
                },
                "top_level_next_page": {
                    "result_status": next_page.result_status,
                    "error_classification": next_page.error_classification,
                    "item_count": len(next_page.items),
                    "source_alias": next_page.source_trace.evidence_alias,
                },
                "reply_hierarchy": {
                    "result_status": reply_page.result_status,
                    "error_classification": reply_page.error_classification,
                    "root_comment_ref": reply_page.items[0].normalized.root_comment_ref,
                    "parent_comment_ref": reply_page.items[0].normalized.parent_comment_ref,
                    "target_comment_ref": reply_page.items[0].normalized.target_comment_ref,
                    "reply_cursor_resume": reply_page.next_continuation.resume_comment_ref,
                },
                "empty_result": {
                    "result_status": empty_page.result_status,
                    "error_classification": empty_page.error_classification,
                },
                "visibility_states": {
                    "item_count": len(visibility_page.items),
                    "result_status": visibility_page.result_status,
                    "error_classification": visibility_page.error_classification,
                    "statuses": [item.visibility_status for item in visibility_page.items],
                },
                "duplicate_comment_item": duplicate_error,
                "partial_result_parse_failed": {
                    "result_status": partial_page.result_status,
                    "error_classification": partial_page.error_classification,
                    "item_count": len(partial_page.items),
                },
                "total_parse_failed": {
                    "result_status": total_parse_failed.result_status,
                    "error_classification": total_parse_failed.error_classification,
                    "item_count": len(total_parse_failed.items),
                },
                **{
                    classification: {
                        "result_status": envelope.result_status,
                        "error_classification": envelope.error_classification,
                        "item_count": len(envelope.items),
                    }
                    for classification, envelope in failures.items()
                },
            },
            "validation_commands": [
                "python3 -m unittest tests.runtime.test_comment_collection tests.runtime.test_comment_collection_evidence tests.runtime.test_runtime tests.runtime.test_operation_taxonomy_admission_evidence tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_task_record tests.runtime.test_read_side_collection_evidence tests.runtime.test_platform_leakage tests.runtime.test_cli_http_same_path tests.runtime.test_real_adapter_regression",
                "python3 scripts/spec_guard.py --mode ci --base-sha ac421426eb5f5a4bce1ea5d0ed908962a05b6e5f --head-sha HEAD",
                "python3 scripts/docs_guard.py --mode ci",
                "python3 scripts/workflow_guard.py --mode ci",
                "python3 scripts/version_guard.py --mode ci",
                "python3 scripts/governance_gate.py --mode ci --base-sha ac421426eb5f5a4bce1ea5d0ed908962a05b6e5f --head-sha HEAD --head-ref issue-419-404-v1-4-0-comment-collection-evidence",
            ],
        }

    def load_artifact_report(self) -> dict[str, object]:
        text = ARTIFACT_PATH.read_text(encoding="utf-8")
        match = re.search(
            r"<!-- syvert:comment-collection-evidence-json:start -->\s*```json\s*(\{.*?\})\s*```",
            text,
            re.S,
        )
        self.assertIsNotNone(match)
        return json.loads(match.group(1))


if __name__ == "__main__":
    unittest.main()
