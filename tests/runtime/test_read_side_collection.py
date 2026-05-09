from __future__ import annotations

from typing import Any
import unittest

from syvert.read_side_collection import (
    CollectionContractError,
    collection_result_envelope_from_dict,
    collection_result_envelope_to_dict,
    validate_collection_result_envelope,
)


def make_source_trace() -> dict[str, Any]:
    return {
        "adapter_key": "fake-adapter",
        "provider_path": "tests.fake_provider",
        "fetched_at": "2026-05-09T00:00:00Z",
        "evidence_alias": "evidence-read-side-collection-001",
    }


def make_target(
    *,
    operation: str = "content_search_by_keyword",
    target_type: str = "keyword",
    target_ref: str = "keyword-search",
) -> dict[str, Any]:
    return {
        "operation": operation,
        "target_type": target_type,
        "target_ref": target_ref,
    }


def make_continuation(*, target_ref: str = "keyword-search") -> dict[str, Any]:
    return {
        "continuation_token": "cursor-1",
        "continuation_family": "opaque",
        "resume_target_ref": target_ref,
        "issued_at": "2026-05-09T00:00:00Z",
    }


def make_normalized_item(*, index: int, source_platform: str = "xhs") -> dict[str, Any]:
    return {
        "source_platform": source_platform,
        "source_type": "post",
        "source_id": f"sid-{index}",
        "canonical_ref": f"https://example.com/posts/{index}",
        "title_or_text_hint": f"item title {index}",
        "creator_ref": f"creator-{index}",
        "published_at": "2026-05-09T00:00:00Z",
        "media_refs": [f"media-{index}-1", f"media-{index}-2"],
    }


def make_item(*, index: int = 1, dedup_key: str = "dedup-1") -> dict[str, Any]:
    return {
        "item_type": "content",
        "dedup_key": dedup_key,
        "source_id": f"source-{index}",
        "source_ref": f"https://example.com/posts/{index}",
        "normalized": make_normalized_item(index=index),
        "raw_payload_ref": f"raw-payload-{index}",
        "source_trace": make_source_trace(),
    }


def make_payload(
    *,
    operation: str = "content_search_by_keyword",
    target_type: str = "keyword",
    result_status: str = "complete",
    error_classification: str = "platform_failed",
    items: tuple[dict[str, Any], ...] | list[dict[str, Any]] = (make_item(index=1),),
    has_more: bool = False,
    include_continuation: bool = False,
) -> dict[str, Any]:
    target = make_target(operation=operation, target_type=target_type)
    return {
        "operation": operation,
        "target": target,
        "items": list(items),
        "has_more": has_more,
        "next_continuation": make_continuation(target_ref=target["target_ref"]) if include_continuation else None,
        "result_status": result_status,
        "error_classification": error_classification,
        "raw_payload_ref": f"raw-result-{result_status}-{operation}",
        "source_trace": make_source_trace(),
        "audit": {
            "carrier": "fake-read-side-collection",
            "test_mode": True,
        },
    }


class FakeReadSideCarrier:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def execute(self, _request: dict[str, Any]) -> dict[str, Any]:
        return self.payload


class ReadSideCollectionCarrierTests(unittest.TestCase):
    def test_fake_carrier_happy_path(self) -> None:
        payload = make_payload(
            has_more=True,
            include_continuation=True,
        )
        adapter = FakeReadSideCarrier(payload)
        envelope = collection_result_envelope_from_dict(adapter.execute({}))

        self.assertIsNone(validate_collection_result_envelope(envelope))
        self.assertEqual(collection_result_envelope_to_dict(envelope), payload)

    def test_fake_carrier_empty_result(self) -> None:
        payload = make_payload(
            result_status="empty",
            error_classification="empty_result",
            items=(),
            has_more=False,
            include_continuation=False,
        )

        envelope = collection_result_envelope_from_dict(payload)

        self.assertIsNone(validate_collection_result_envelope(envelope))
        self.assertEqual(collection_result_envelope_to_dict(envelope), payload)

    def test_fake_carrier_partial_result(self) -> None:
        payload = make_payload(
            result_status="partial_result",
            error_classification="parse_failed",
            items=(
                make_item(index=1, dedup_key="dedup-1"),
                make_item(index=2, dedup_key="dedup-2"),
            ),
            has_more=False,
            include_continuation=False,
        )

        envelope = collection_result_envelope_from_dict(payload)

        self.assertIsNone(validate_collection_result_envelope(envelope))
        self.assertEqual(collection_result_envelope_to_dict(envelope)["result_status"], "partial_result")

    def test_fake_carrier_duplicate_dedup_keys_are_rejected(self) -> None:
        payload = make_payload(
            items=[
                make_item(index=1, dedup_key="dup-key"),
                make_item(index=2, dedup_key="dup-key"),
            ]
        )
        payload["has_more"] = False

        self.assertEqual(
            validate_collection_result_envelope(payload),
            {
                "code": "invalid_collection_contract",
                "message": "CollectionItemEnvelope.dedup_key 不能重复",
                "details": {"field": "items"},
            },
        )

    def test_fake_carrier_cursor_invalid_or_expired(self) -> None:
        payload = make_payload(
            operation="content_list_by_creator",
            target_type="creator",
            result_status="complete",
            error_classification="cursor_invalid_or_expired",
            items=(make_item(index=1),),
            has_more=False,
        )
        payload["target"]["target_ref"] = "creator-search"
        payload["has_more"] = True
        payload["next_continuation"] = make_continuation(target_ref="creator-different")

        result = validate_collection_result_envelope(payload)

        self.assertEqual(result["code"], "invalid_collection_contract")
        self.assertIn("resume_target_ref", str(result))

    def test_fake_carrier_error_classification_variants(self) -> None:
        for error_classification in (
            "permission_denied",
            "rate_limited",
            "provider_or_network_blocked",
            "credential_invalid",
            "verification_required",
            "signature_or_request_invalid",
            "platform_failed",
            "target_not_found",
            "empty_result",
        ):
            with self.subTest(error_classification=error_classification):
                payload = make_payload(
                    result_status="complete",
                    error_classification=error_classification,
                    has_more=False,
                    items=(make_item(index=1),),
                )
                if error_classification == "empty_result":
                    payload["result_status"] = "empty"
                    payload["items"] = []

                self.assertIsNone(
                    validate_collection_result_envelope(payload),
                    msg=f"{error_classification} should be valid",
                )

    def test_fake_carrier_parse_failed_malformed(self) -> None:
        payload = make_payload(
            result_status="partial_result",
            error_classification="parse_failed",
            items=(make_item(index=1),),
        )
        payload["items"][0]["normalized"]["source_id"] = ""

        result = validate_collection_result_envelope(payload)

        self.assertEqual(result["code"], "parse_failed")
        self.assertIn("source_id", result["message"])


if __name__ == "__main__":
    unittest.main()
