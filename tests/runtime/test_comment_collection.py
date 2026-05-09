from __future__ import annotations

from typing import Any
import unittest

from syvert.read_side_collection import (
    CommentReplyCursor,
    CommentRequestCursor,
    comment_collection_result_envelope_from_dict,
    comment_collection_result_envelope_to_dict,
    validate_comment_collection_result_envelope,
    validate_comment_request_cursor,
)


def make_source_trace() -> dict[str, Any]:
    return {
        "adapter_key": "fake-adapter",
        "provider_path": "tests.fake_provider",
        "fetched_at": "2026-05-09T00:00:00Z",
        "evidence_alias": "evidence-comment-collection-001",
    }


def make_target(*, target_ref: str = "content-001") -> dict[str, Any]:
    return {
        "operation": "comment_collection",
        "target_type": "content",
        "target_ref": target_ref,
    }


def make_page_continuation(*, target_ref: str = "content-001", comment_ref: str | None = None) -> dict[str, Any]:
    return {
        "continuation_token": "comment-page-cursor-1",
        "continuation_family": "opaque",
        "resume_target_ref": target_ref,
        **({"resume_comment_ref": comment_ref} if comment_ref is not None else {}),
        "issued_at": "2026-05-09T00:00:00Z",
    }


def make_reply_cursor(*, target_ref: str = "content-001", comment_ref: str = "comment:root-1") -> dict[str, Any]:
    return {
        "reply_cursor_token": "reply-cursor-1",
        "reply_cursor_family": "opaque",
        "resume_target_ref": target_ref,
        "resume_comment_ref": comment_ref,
        "issued_at": "2026-05-09T00:00:00Z",
    }


def make_normalized_comment(
    *,
    source_id: str = "comment-1",
    canonical_ref: str = "comment:root-1",
    body_text_hint: str = "top-level comment",
    root_comment_ref: str = "comment:root-1",
    parent_comment_ref: str | None = None,
    target_comment_ref: str | None = None,
) -> dict[str, Any]:
    return {
        "source_platform": "reference-platform",
        "source_type": "comment",
        "source_id": source_id,
        "canonical_ref": canonical_ref,
        "body_text_hint": body_text_hint,
        "root_comment_ref": root_comment_ref,
        **({"parent_comment_ref": parent_comment_ref} if parent_comment_ref is not None else {}),
        **({"target_comment_ref": target_comment_ref} if target_comment_ref is not None else {}),
        "author_ref": "creator-1",
        "published_at": "2026-05-09T00:00:00Z",
    }


def make_comment_item(
    *,
    dedup_key: str = "comment:root-1",
    source_id: str = "comment-1",
    canonical_ref: str = "comment:root-1",
    visibility_status: str = "visible",
    body_text_hint: str = "top-level comment",
    root_comment_ref: str = "comment:root-1",
    parent_comment_ref: str | None = None,
    target_comment_ref: str | None = None,
    include_reply_cursor: bool = False,
) -> dict[str, Any]:
    return {
        "item_type": "comment",
        "dedup_key": dedup_key,
        "source_id": source_id,
        "source_ref": f"source:{canonical_ref}",
        "visibility_status": visibility_status,
        "normalized": make_normalized_comment(
            source_id=source_id,
            canonical_ref=canonical_ref,
            body_text_hint=body_text_hint,
            root_comment_ref=root_comment_ref,
            parent_comment_ref=parent_comment_ref,
            target_comment_ref=target_comment_ref,
        ),
        "raw_payload_ref": f"raw:{canonical_ref}",
        "source_trace": make_source_trace(),
        **({"reply_cursor": make_reply_cursor(comment_ref=canonical_ref)} if include_reply_cursor else {}),
    }


def make_payload(
    *,
    items: tuple[dict[str, Any], ...] | list[dict[str, Any]] = (make_comment_item(include_reply_cursor=True),),
    result_status: str = "partial_result",
    error_classification: str = "parse_failed",
    has_more: bool = False,
    include_continuation: bool = False,
    continuation_comment_ref: str | None = None,
) -> dict[str, Any]:
    return {
        "operation": "comment_collection",
        "target": make_target(),
        "items": list(items),
        "has_more": has_more,
        "next_continuation": (
            make_page_continuation(comment_ref=continuation_comment_ref) if include_continuation else None
        ),
        "result_status": result_status,
        "error_classification": error_classification,
        "raw_payload_ref": f"raw-result-{result_status}",
        "source_trace": make_source_trace(),
        "audit": {
            "carrier": "fake-comment-collection",
            "test_mode": True,
        },
    }


class CommentCollectionCarrierTests(unittest.TestCase):
    def test_fake_carrier_happy_path_with_reply_cursor_and_page_continuation(self) -> None:
        payload = make_payload(has_more=True, include_continuation=True)

        envelope = comment_collection_result_envelope_from_dict(payload)

        self.assertIsNone(validate_comment_collection_result_envelope(envelope))
        self.assertEqual(comment_collection_result_envelope_to_dict(envelope), payload)

    def test_reply_hierarchy_and_reply_window_continuation_are_valid(self) -> None:
        reply = make_comment_item(
            dedup_key="comment:reply-1",
            source_id="reply-1",
            canonical_ref="comment:reply-1",
            body_text_hint="reply comment",
            root_comment_ref="comment:root-1",
            parent_comment_ref="comment:root-1",
            target_comment_ref="comment:root-1",
        )
        payload = make_payload(
            items=(reply,),
            has_more=True,
            include_continuation=True,
            continuation_comment_ref="comment:root-1",
        )

        self.assertIsNone(validate_comment_collection_result_envelope(payload))

    def test_reply_window_next_page_can_bind_root_comment_not_present_in_items(self) -> None:
        reply = make_comment_item(
            dedup_key="comment:reply-2",
            source_id="reply-2",
            canonical_ref="comment:reply-2",
            body_text_hint="second reply page item",
            root_comment_ref="comment:root-1",
            parent_comment_ref="comment:root-1",
        )
        payload = make_payload(
            items=(reply,),
            has_more=True,
            include_continuation=True,
            continuation_comment_ref="comment:root-1",
        )

        self.assertIsNone(validate_comment_collection_result_envelope(payload))

    def test_reply_window_next_continuation_rejects_opaque_thread_drift(self) -> None:
        reply = make_comment_item(
            dedup_key="comment:reply-2",
            source_id="reply-2",
            canonical_ref="comment:reply-2",
            body_text_hint="second reply page item",
            root_comment_ref="comment:root-1",
            parent_comment_ref="comment:root-1",
        )
        payload = make_payload(
            items=(reply,),
            has_more=True,
            include_continuation=True,
            continuation_comment_ref="comment:other-root",
        )

        result = validate_comment_collection_result_envelope(payload)

        self.assertEqual(result["code"], "invalid_comment_collection_contract")
        self.assertIn("reply thread", result["message"])

    def test_pure_reply_page_next_continuation_requires_resume_comment_ref(self) -> None:
        reply = make_comment_item(
            dedup_key="comment:reply-missing-thread",
            source_id="reply-missing-thread",
            canonical_ref="comment:reply-missing-thread",
            root_comment_ref="comment:root-1",
            parent_comment_ref="comment:root-1",
        )
        payload = make_payload(
            items=(reply,),
            has_more=True,
            include_continuation=True,
            continuation_comment_ref=None,
        )

        result = validate_comment_collection_result_envelope(payload)

        self.assertEqual(result["code"], "invalid_comment_collection_contract")
        self.assertIn("resume_comment_ref", result["message"])

    def test_reply_hierarchy_rejects_independent_target_linkage_for_direct_reply(self) -> None:
        reply = make_comment_item(
            dedup_key="comment:reply-conflict",
            source_id="reply-conflict",
            canonical_ref="comment:reply-conflict",
            body_text_hint="conflicting reply",
            root_comment_ref="comment:root-1",
            parent_comment_ref="comment:root-1",
            target_comment_ref="comment:other-thread",
        )
        payload = make_payload(items=(reply,))

        result = validate_comment_collection_result_envelope(payload)

        self.assertEqual(result["code"], "invalid_comment_collection_contract")
        self.assertIn("target_comment_ref", result["message"])

    def test_reply_hierarchy_rejects_opaque_parent_linkage_without_root_target(self) -> None:
        reply = make_comment_item(
            dedup_key="comment:reply-parent-drift",
            source_id="reply-parent-drift",
            canonical_ref="comment:reply-parent-drift",
            body_text_hint="parent drift reply",
            root_comment_ref="comment:root-1",
            parent_comment_ref="comment:other-root:parent-1",
        )
        payload = make_payload(items=(reply,))

        result = validate_comment_collection_result_envelope(payload)

        self.assertEqual(result["code"], "invalid_comment_collection_contract")
        self.assertIn("target_comment_ref", result["message"])

    def test_reply_hierarchy_rejects_parent_drift_with_root_target(self) -> None:
        reply = make_comment_item(
            dedup_key="comment:reply-parent-root-target",
            source_id="reply-parent-root-target",
            canonical_ref="comment:reply-parent-root-target",
            body_text_hint="parent drift reply with root target",
            root_comment_ref="comment:root-1",
            parent_comment_ref="comment:other-thread-parent",
            target_comment_ref="comment:root-1",
        )
        payload = make_payload(items=(reply,))

        result = validate_comment_collection_result_envelope(payload)

        self.assertEqual(result["code"], "invalid_comment_collection_contract")
        self.assertIn("target_comment_ref", result["message"])

    def test_nested_reply_window_binds_continuation_to_parent_comment(self) -> None:
        reply = make_comment_item(
            dedup_key="comment:reply-nested",
            source_id="reply-nested",
            canonical_ref="comment:reply-nested",
            body_text_hint="nested reply",
            root_comment_ref="comment:root-1",
            parent_comment_ref="comment:root-1:parent-1",
            target_comment_ref="comment:mentioned-1",
        )
        payload = make_payload(
            items=(reply,),
            has_more=True,
            include_continuation=True,
            continuation_comment_ref="comment:root-1:parent-1",
        )

        self.assertIsNone(validate_comment_collection_result_envelope(payload))

    def test_reply_window_allows_descendant_reply_within_resumed_thread(self) -> None:
        reply = make_comment_item(
            dedup_key="comment:reply-descendant",
            source_id="reply-descendant",
            canonical_ref="comment:reply-descendant",
            body_text_hint="descendant reply",
            root_comment_ref="comment:root-1",
            parent_comment_ref="comment:root-1:child-1",
            target_comment_ref="comment:mentioned-1",
        )
        payload = make_payload(
            items=(reply,),
            has_more=True,
            include_continuation=True,
            continuation_comment_ref="comment:root-1",
        )

        self.assertIsNone(validate_comment_collection_result_envelope(payload))

    def test_reply_window_allows_descendant_reply_within_non_root_resumed_thread(self) -> None:
        reply = make_comment_item(
            dedup_key="comment:reply-non-root-descendant",
            source_id="reply-non-root-descendant",
            canonical_ref="comment:reply-non-root-descendant",
            body_text_hint="non-root descendant reply",
            root_comment_ref="comment:root-1",
            parent_comment_ref="comment:child-1",
            target_comment_ref="comment:parent-1",
        )
        payload = make_payload(
            items=(reply,),
            has_more=True,
            include_continuation=True,
            continuation_comment_ref="comment:parent-1",
        )

        self.assertIsNone(validate_comment_collection_result_envelope(payload))

    def test_request_cursor_rejects_page_continuation_and_reply_cursor_together(self) -> None:
        result = validate_comment_request_cursor(
            {
                "page_continuation": make_page_continuation(),
                "reply_cursor": make_reply_cursor(),
            },
            target_ref="content-001",
        )

        self.assertEqual(result["code"], "signature_or_request_invalid")

    def test_request_cursor_rejects_cross_target_reply_cursor(self) -> None:
        result = validate_comment_request_cursor(
            {"reply_cursor": make_reply_cursor(target_ref="other-content")},
            target_ref="content-001",
        )

        self.assertEqual(result["code"], "cursor_invalid_or_expired")

    def test_request_cursor_rejects_malformed_dataclass_reply_cursor(self) -> None:
        result = validate_comment_request_cursor(
            CommentRequestCursor(
                reply_cursor=CommentReplyCursor(
                    reply_cursor_token="",
                    reply_cursor_family="opaque",
                    resume_target_ref="content-001",
                    resume_comment_ref="comment:root-1",
                    issued_at="2026-05-09T10:00:00Z",
                ),
            ),
            target_ref="content-001",
        )

        self.assertEqual(result["code"], "parse_failed")
        self.assertIn("reply_cursor_token", result["message"])

    def test_request_cursor_rejects_dataclass_with_mapping_reply_cursor(self) -> None:
        result = validate_comment_request_cursor(
            CommentRequestCursor(reply_cursor={"reply_cursor_token": "cursor-1"}),  # type: ignore[arg-type]
            target_ref="content-001",
        )

        self.assertEqual(result["code"], "parse_failed")

    def test_empty_result_is_valid_without_continuation(self) -> None:
        payload = make_payload(
            items=(),
            result_status="empty",
            error_classification="empty_result",
        )

        self.assertIsNone(validate_comment_collection_result_envelope(payload))

    def test_complete_success_page_with_comment_items_is_valid(self) -> None:
        payload = make_payload(
            result_status="complete",
            error_classification="partial_result",
        )
        envelope = comment_collection_result_envelope_from_dict(payload)

        self.assertIsNone(validate_comment_collection_result_envelope(envelope))

    def test_collection_level_failures_are_fail_closed(self) -> None:
        for error_classification in (
            "target_not_found",
            "permission_denied",
            "rate_limited",
            "platform_failed",
            "provider_or_network_blocked",
            "cursor_invalid_or_expired",
            "credential_invalid",
            "verification_required",
            "signature_or_request_invalid",
        ):
            with self.subTest(error_classification=error_classification):
                payload = make_payload(
                    items=(),
                    result_status="complete",
                    error_classification=error_classification,
                )

                self.assertIsNone(validate_comment_collection_result_envelope(payload))

    def test_collection_level_failure_with_items_is_rejected(self) -> None:
        for error_classification in ("permission_denied", "platform_failed"):
            with self.subTest(error_classification=error_classification):
                payload = make_payload(
                    items=(make_comment_item(),),
                    result_status="complete",
                    error_classification=error_classification,
                )

                result = validate_comment_collection_result_envelope(payload)

                self.assertEqual(result["code"], "invalid_comment_collection_contract")
                self.assertIn("fail-closed", result["message"])

    def test_deleted_invisible_and_unavailable_are_item_level_visibility(self) -> None:
        placeholder_source_id = "public-placeholder:comment:content-001:unavailable:slot-a"
        payload = make_payload(
            items=(
                make_comment_item(
                    dedup_key="deleted",
                    source_id="deleted-1",
                    canonical_ref="comment:deleted-1",
                    visibility_status="deleted",
                    root_comment_ref="comment:deleted-1",
                ),
                make_comment_item(
                    dedup_key="invisible",
                    source_id="invisible-1",
                    canonical_ref="comment:invisible-1",
                    visibility_status="invisible",
                    root_comment_ref="comment:invisible-1",
                ),
                make_comment_item(
                    dedup_key="unavailable",
                    source_id=placeholder_source_id,
                    canonical_ref="public-placeholder:comment:content-001:unavailable:slot-a",
                    visibility_status="unavailable",
                    body_text_hint="unavailable comment",
                    root_comment_ref="public-placeholder:comment:content-001:unavailable:slot-a",
                ),
            ),
        )

        self.assertIsNone(validate_comment_collection_result_envelope(payload))

    def test_placeholder_canonical_ref_requires_placeholder_source_id(self) -> None:
        payload = make_payload(
            items=(
                make_comment_item(
                    dedup_key="placeholder-drift",
                    source_id="comment-1",
                    canonical_ref="public-placeholder:comment:content-001:unavailable:slot-a",
                    visibility_status="unavailable",
                    body_text_hint="unavailable comment",
                    root_comment_ref="public-placeholder:comment:content-001:unavailable:slot-a",
                ),
            ),
        )

        result = validate_comment_collection_result_envelope(payload)

        self.assertEqual(result["code"], "invalid_comment_collection_contract")
        self.assertIn("source_id", result["message"])

    def test_partial_result_requires_at_least_one_comment_item(self) -> None:
        payload = make_payload(
            items=(),
            result_status="partial_result",
            error_classification="parse_failed",
        )

        result = validate_comment_collection_result_envelope(payload)

        self.assertEqual(result["code"], "invalid_comment_collection_contract")
        self.assertIn("至少一个 comment item", result["message"])

    def test_total_parse_failed_uses_fail_closed_envelope(self) -> None:
        payload = make_payload(
            items=(),
            result_status="complete",
            error_classification="parse_failed",
        )

        self.assertIsNone(validate_comment_collection_result_envelope(payload))

    def test_duplicate_comment_dedup_keys_are_rejected(self) -> None:
        payload = make_payload(
            items=(
                make_comment_item(dedup_key="dup"),
                make_comment_item(dedup_key="dup", source_id="comment-2", canonical_ref="comment:root-2", root_comment_ref="comment:root-2"),
            )
        )

        result = validate_comment_collection_result_envelope(payload)

        self.assertEqual(result["code"], "invalid_comment_collection_contract")
        self.assertIn("dedup_key", result["message"])


if __name__ == "__main__":
    unittest.main()
