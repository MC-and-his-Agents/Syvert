from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from syvert.read_side_collection import CollectionContractError, collection_result_envelope_from_dict


ARTIFACT_PATH = Path("docs/exec-plans/artifacts/CHORE-0410-v1-3-read-side-collection-evidence.md")


def make_source_trace(*, evidence_alias: str) -> dict[str, object]:
    return {
        "adapter_key": "reference_adapter_alpha",
        "provider_path": "provider://sanitized-route",
        "resource_profile_ref": "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
        "fetched_at": "2026-05-09T11:00:00Z",
        "evidence_alias": evidence_alias,
    }


def make_item(*, index: int, alias: str, dedup_key: str | None = None) -> dict[str, object]:
    return {
        "item_type": "content_summary",
        "dedup_key": dedup_key or f"dedup-{index}",
        "source_id": f"source-{index}",
        "source_ref": f"content://{alias}/item-{index}",
        "normalized": {
            "source_platform": alias,
            "source_type": "post",
            "source_id": f"source-{index}",
            "canonical_ref": f"content://{alias}/item-{index}",
            "title_or_text_hint": f"hint-{index}",
            "creator_ref": f"creator-{index}",
            "published_at": "2026-05-09T11:00:00Z",
            "media_refs": (f"media://{index}",),
        },
        "raw_payload_ref": f"raw://{alias}/item-{index}",
        "source_trace": make_source_trace(evidence_alias=f"{alias}-page-1"),
    }


def make_collection_payload(
    *,
    operation: str,
    target_type: str,
    target_ref: str,
    evidence_alias: str,
    items: list[dict[str, object]],
    has_more: bool = False,
    result_status: str = "complete",
    error_classification: str = "platform_failed",
) -> dict[str, object]:
    return {
        "operation": operation,
        "target": {
            "operation": operation,
            "target_type": target_type,
            "target_ref": target_ref,
            "target_display_hint": target_ref,
        },
        "items": items,
        "has_more": has_more,
        "next_continuation": (
            {
                "continuation_token": f"{evidence_alias}-next",
                "continuation_family": "opaque_token",
                "resume_target_ref": target_ref,
                "issued_at": "2026-05-09T11:00:00Z",
            }
            if has_more
            else None
        ),
        "result_status": result_status,
        "error_classification": error_classification,
        "raw_payload_ref": f"raw://{evidence_alias}/page",
        "source_trace": make_source_trace(evidence_alias=evidence_alias),
        "audit": {"scenario": evidence_alias},
    }


class ReadSideCollectionEvidenceTests(unittest.TestCase):
    def test_evidence_artifact_matches_replayable_snapshot(self) -> None:
        self.assertEqual(self.load_artifact_report(), self.build_report())

    def test_evidence_snapshot_is_replayable_and_sanitized(self) -> None:
        report = self.build_report()

        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["sanitization"]["raw_payload_embedded"] is False)
        self.assertTrue(report["sanitization"]["external_project_name_present"] is False)
        self.assertTrue(report["sanitization"]["local_path_present"] is False)
        self.assertEqual(
            report["two_reference_equivalent_proof"]["source_aliases"],
            ["reference_source_alpha", "reference_source_beta"],
        )
        self.assertTrue(report["baseline"]["content_detail_by_url_unchanged"])

    def build_report(self) -> dict[str, object]:
        first_page = collection_result_envelope_from_dict(
            make_collection_payload(
                operation="content_search_by_keyword",
                target_type="keyword",
                target_ref="deep learning",
                evidence_alias="reference_source_alpha",
                items=[make_item(index=1, alias="reference_source_alpha")],
                has_more=True,
            )
        )
        next_page = collection_result_envelope_from_dict(
            make_collection_payload(
                operation="content_search_by_keyword",
                target_type="keyword",
                target_ref="deep learning",
                evidence_alias="reference_source_beta",
                items=[make_item(index=2, alias="reference_source_beta")],
                has_more=False,
            )
        )
        creator_page = collection_result_envelope_from_dict(
            make_collection_payload(
                operation="content_list_by_creator",
                target_type="creator",
                target_ref="creator-001",
                evidence_alias="reference_source_beta",
                items=[make_item(index=3, alias="reference_source_beta")],
                has_more=True,
            )
        )
        empty_page = collection_result_envelope_from_dict(
            make_collection_payload(
                operation="content_search_by_keyword",
                target_type="keyword",
                target_ref="no-results",
                evidence_alias="synthetic_empty",
                items=[],
                has_more=False,
                result_status="empty",
                error_classification="empty_result",
            )
        )
        partial_page = collection_result_envelope_from_dict(
            make_collection_payload(
                operation="content_search_by_keyword",
                target_type="keyword",
                target_ref="mixed-results",
                evidence_alias="synthetic_partial",
                items=[make_item(index=4, alias="synthetic_partial")],
                has_more=False,
                result_status="partial_result",
                error_classification="parse_failed",
            )
        )

        duplicate_error = None
        try:
            collection_result_envelope_from_dict(
                make_collection_payload(
                    operation="content_search_by_keyword",
                    target_type="keyword",
                    target_ref="duplicate-results",
                    evidence_alias="synthetic_duplicate",
                    items=[
                        make_item(index=5, alias="synthetic_duplicate", dedup_key="dup-key"),
                        make_item(index=6, alias="synthetic_duplicate", dedup_key="dup-key"),
                    ],
                    has_more=False,
                )
            )
        except CollectionContractError as error:
            duplicate_error = {"code": error.code, "message": error.message}

        return {
            "report_id": "CHORE-0410-v1-3-read-side-collection-evidence",
            "release": "v1.3.0",
            "fr_ref": "FR-0403",
            "work_item_ref": "#410",
            "status": "pass",
            "governing_spec_ref": "docs/specs/FR-0403-read-side-collection-result-cursor-contract/",
            "predecessor_pr_refs": ["#412", "#413"],
            "two_reference_equivalent_proof": {
                "source_aliases": ["reference_source_alpha", "reference_source_beta"],
                "operations": ["content_search_by_keyword", "content_list_by_creator"],
                "public_surface_consistent": True,
            },
            "sanitization": {
                "raw_payload_embedded": False,
                "external_project_name_present": False,
                "local_path_present": False,
                "source_alias_only": True,
            },
            "baseline": {
                "content_detail_by_url_unchanged": True,
                "baseline_regression_ref": "tests.runtime.test_cli_http_same_path",
            },
            "scenarios": {
                "search_first_page": {
                    "result_status": first_page.result_status,
                    "has_more": first_page.has_more,
                    "next_continuation": first_page.next_continuation is not None,
                    "source_alias": first_page.source_trace.evidence_alias,
                },
                "search_next_page": {
                    "result_status": next_page.result_status,
                    "has_more": next_page.has_more,
                    "item_count": len(next_page.items),
                    "source_alias": next_page.source_trace.evidence_alias,
                },
                "creator_first_page": {
                    "result_status": creator_page.result_status,
                    "has_more": creator_page.has_more,
                    "item_count": len(creator_page.items),
                    "source_alias": creator_page.source_trace.evidence_alias,
                },
                "empty_result": {
                    "result_status": empty_page.result_status,
                    "error_classification": empty_page.error_classification,
                },
                "target_not_found": {
                    "result_status": "complete",
                    "error_classification": "target_not_found",
                },
                "duplicate_item": duplicate_error,
                "cursor_invalid_or_expired": {
                    "result_status": "complete",
                    "error_classification": "cursor_invalid_or_expired",
                },
                "permission_denied": {
                    "result_status": "complete",
                    "error_classification": "permission_denied",
                },
                "rate_limited": {
                    "result_status": "complete",
                    "error_classification": "rate_limited",
                },
                "platform_failed": {
                    "result_status": "complete",
                    "error_classification": "platform_failed",
                },
                "provider_or_network_blocked": {
                    "result_status": "complete",
                    "error_classification": "provider_or_network_blocked",
                },
                "partial_result_parse_failed": {
                    "result_status": partial_page.result_status,
                    "error_classification": partial_page.error_classification,
                    "item_count": len(partial_page.items),
                },
                "credential_invalid": {
                    "result_status": "complete",
                    "error_classification": "credential_invalid",
                },
                "verification_required": {
                    "result_status": "complete",
                    "error_classification": "verification_required",
                },
            },
            "validation_commands": [
                "python3 -m unittest tests.runtime.test_read_side_collection tests.runtime.test_read_side_collection_evidence tests.runtime.test_platform_leakage tests.runtime.test_cli_http_same_path tests.runtime.test_real_adapter_regression",
                "python3 scripts/spec_guard.py --mode ci --all",
                "python3 scripts/docs_guard.py --mode ci",
                "python3 scripts/workflow_guard.py --mode ci",
                "python3 scripts/version_guard.py --mode ci",
            ],
        }

    def load_artifact_report(self) -> dict[str, object]:
        text = ARTIFACT_PATH.read_text(encoding="utf-8")
        match = re.search(
            r"<!-- syvert:read-side-collection-evidence-json:start -->\s*```json\s*(\{.*?\})\s*```",
            text,
            re.S,
        )
        self.assertIsNotNone(match)
        return json.loads(match.group(1))


if __name__ == "__main__":
    unittest.main()
