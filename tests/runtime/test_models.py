from __future__ import annotations

from dataclasses import dataclass
import unittest

from syvert.runtime import (
    CollectionPolicy,
    CoreTaskRequest,
    InputTarget,
    normalize_request,
    TaskInput,
    TaskRequest,
    validate_request,
    validate_success_payload,
)


@dataclass(frozen=True)
class ExtendedInputTarget(InputTarget):
    note_id: str


class TaskRequestValidationTests(unittest.TestCase):
    def test_accepts_minimal_content_detail_request(self) -> None:
        request = TaskRequest(
            adapter_key="xhs",
            capability="content_detail_by_url",
            input=TaskInput(url="https://www.xiaohongshu.com/explore/abc123"),
        )

        self.assertIsNone(validate_request(request))

    def test_rejects_missing_adapter_key(self) -> None:
        request = TaskRequest(
            adapter_key="",
            capability="content_detail_by_url",
            input=TaskInput(url="https://www.xiaohongshu.com/explore/abc123"),
        )

        error = validate_request(request)

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_task_request")

    def test_rejects_non_string_adapter_key(self) -> None:
        request = TaskRequest(
            adapter_key=1,  # type: ignore[arg-type]
            capability="content_detail_by_url",
            input=TaskInput(url="https://www.xiaohongshu.com/explore/abc123"),
        )

        error = validate_request(request)

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_task_request")

    def test_rejects_unsupported_capability(self) -> None:
        request = TaskRequest(
            adapter_key="xhs",
            capability="search",
            input=TaskInput(url="https://www.xiaohongshu.com/explore/abc123"),
        )

        error = validate_request(request)

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_capability")

    def test_accepts_batch_execution_request(self) -> None:
        request = TaskRequest(
            adapter_key="xhs",
            capability="batch_execution",
            input=TaskInput(),
        )

        normalized_request, error = normalize_request(request)

        self.assertIsNone(error)
        self.assertIsNotNone(normalized_request)
        self.assertEqual(normalized_request.target.capability, "batch_execution")
        self.assertEqual(normalized_request.target.target_type, "operation_batch")
        self.assertEqual(normalized_request.target.target_value, "batch_execution")
        self.assertEqual(normalized_request.policy.collection_mode, "batch")

    def test_rejects_missing_input_url(self) -> None:
        request = TaskRequest(
            adapter_key="xhs",
            capability="content_detail_by_url",
            input=TaskInput(url=""),
        )

        error = validate_request(request)

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_task_request")

    def test_accepts_core_request_model(self) -> None:
        request = CoreTaskRequest(
            target=InputTarget(
                adapter_key="xhs",
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://www.xiaohongshu.com/explore/abc123",
            ),
            policy=CollectionPolicy(collection_mode="hybrid"),
        )

        self.assertIsNone(validate_request(request))

    def test_accepts_batch_execution_core_request_model(self) -> None:
        request = CoreTaskRequest(
            target=InputTarget(
                adapter_key="xhs",
                capability="batch_execution",
                target_type="operation_batch",
                target_value="batch_execution",
            ),
            policy=CollectionPolicy(collection_mode="batch"),
        )

        self.assertIsNone(validate_request(request))

    def test_rejects_empty_target_value(self) -> None:
        request = CoreTaskRequest(
            target=InputTarget(
                adapter_key="xhs",
                capability="content_detail_by_url",
                target_type="url",
                target_value="",
            ),
            policy=CollectionPolicy(collection_mode="hybrid"),
        )

        error = validate_request(request)

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_task_request")

    def test_rejects_unknown_target_type(self) -> None:
        request = CoreTaskRequest(
            target=InputTarget(
                adapter_key="xhs",
                capability="content_detail_by_url",
                target_type="unknown_type",
                target_value="https://www.xiaohongshu.com/explore/abc123",
            ),
            policy=CollectionPolicy(collection_mode="hybrid"),
        )

        error = validate_request(request)

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_task_request")

    def test_rejects_unknown_collection_mode(self) -> None:
        request = CoreTaskRequest(
            target=InputTarget(
                adapter_key="xhs",
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://www.xiaohongshu.com/explore/abc123",
            ),
            policy=CollectionPolicy(collection_mode="private"),
        )

        error = validate_request(request)

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_task_request")

    def test_rejects_extended_target_shape_with_platform_specific_fields(self) -> None:
        request = CoreTaskRequest(
            target=ExtendedInputTarget(
                adapter_key="xhs",
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://www.xiaohongshu.com/explore/abc123",
                note_id="66fad51c000000001b0224b8",
            ),
            policy=CollectionPolicy(collection_mode="hybrid"),
        )

        error = validate_request(request)

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_task_request")


class NormalizedPayloadValidationTests(unittest.TestCase):
    def test_accepts_minimal_normalized_payload(self) -> None:
        normalized = {
            "platform": "xhs",
            "content_id": "abc123",
            "content_type": "image_post",
            "canonical_url": "https://www.xiaohongshu.com/explore/abc123",
            "title": "",
            "body_text": "hello",
            "published_at": None,
            "author": {
                "author_id": None,
                "display_name": None,
                "avatar_url": None,
            },
            "stats": {
                "like_count": None,
                "comment_count": None,
                "share_count": None,
                "collect_count": None,
            },
            "media": {
                "cover_url": None,
                "video_url": None,
                "image_urls": [],
            },
        }

        self.assertIsNone(validate_success_payload({"raw": {"id": "abc123"}, "normalized": normalized}))

    def test_accepts_rfc3339_utc_with_explicit_offset(self) -> None:
        normalized = {
            "platform": "xhs",
            "content_id": "abc123",
            "content_type": "image_post",
            "canonical_url": "https://www.xiaohongshu.com/explore/abc123",
            "title": "",
            "body_text": "hello",
            "published_at": "2026-04-03T10:00:00+00:00",
            "author": {
                "author_id": None,
                "display_name": None,
                "avatar_url": None,
            },
            "stats": {
                "like_count": None,
                "comment_count": None,
                "share_count": None,
                "collect_count": None,
            },
            "media": {
                "cover_url": None,
                "video_url": None,
                "image_urls": [],
            },
        }

        self.assertIsNone(validate_success_payload({"raw": {"id": "abc123"}, "normalized": normalized}))

    def test_rejects_missing_author_object(self) -> None:
        normalized = {
            "platform": "xhs",
            "content_id": "abc123",
            "content_type": "image_post",
            "canonical_url": "https://www.xiaohongshu.com/explore/abc123",
            "title": "",
            "body_text": "hello",
            "published_at": None,
            "stats": {
                "like_count": None,
                "comment_count": None,
                "share_count": None,
                "collect_count": None,
            },
            "media": {
                "cover_url": None,
                "video_url": None,
                "image_urls": [],
            },
        }

        error = validate_success_payload({"raw": {"id": "abc123"}, "normalized": normalized})

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_adapter_success_payload")

    def test_rejects_non_rfc3339_published_at(self) -> None:
        normalized = {
            "platform": "xhs",
            "content_id": "abc123",
            "content_type": "image_post",
            "canonical_url": "https://www.xiaohongshu.com/explore/abc123",
            "title": "",
            "body_text": "hello",
            "published_at": 123,
            "author": {
                "author_id": None,
                "display_name": None,
                "avatar_url": None,
            },
            "stats": {
                "like_count": None,
                "comment_count": None,
                "share_count": None,
                "collect_count": None,
            },
            "media": {
                "cover_url": None,
                "video_url": None,
                "image_urls": [],
            },
        }

        error = validate_success_payload({"raw": {"id": "abc123"}, "normalized": normalized})

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_adapter_success_payload")

    def test_rejects_non_integer_stats_value(self) -> None:
        normalized = {
            "platform": "xhs",
            "content_id": "abc123",
            "content_type": "image_post",
            "canonical_url": "https://www.xiaohongshu.com/explore/abc123",
            "title": "",
            "body_text": "hello",
            "published_at": None,
            "author": {
                "author_id": None,
                "display_name": None,
                "avatar_url": None,
            },
            "stats": {
                "like_count": "3",
                "comment_count": None,
                "share_count": None,
                "collect_count": None,
            },
            "media": {
                "cover_url": None,
                "video_url": None,
                "image_urls": [],
            },
        }

        error = validate_success_payload({"raw": {"id": "abc123"}, "normalized": normalized})

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_adapter_success_payload")

    def test_rejects_invalid_media_cover_url_type(self) -> None:
        normalized = {
            "platform": "xhs",
            "content_id": "abc123",
            "content_type": "image_post",
            "canonical_url": "https://www.xiaohongshu.com/explore/abc123",
            "title": "",
            "body_text": "hello",
            "published_at": None,
            "author": {
                "author_id": None,
                "display_name": None,
                "avatar_url": None,
            },
            "stats": {
                "like_count": None,
                "comment_count": None,
                "share_count": None,
                "collect_count": None,
            },
            "media": {
                "cover_url": 1,
                "video_url": None,
                "image_urls": [],
            },
        }

        error = validate_success_payload({"raw": {"id": "abc123"}, "normalized": normalized})

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_adapter_success_payload")

    def test_rejects_invalid_author_avatar_url_type(self) -> None:
        normalized = {
            "platform": "xhs",
            "content_id": "abc123",
            "content_type": "image_post",
            "canonical_url": "https://www.xiaohongshu.com/explore/abc123",
            "title": "",
            "body_text": "hello",
            "published_at": None,
            "author": {
                "author_id": None,
                "display_name": None,
                "avatar_url": 1,
            },
            "stats": {
                "like_count": None,
                "comment_count": None,
                "share_count": None,
                "collect_count": None,
            },
            "media": {
                "cover_url": None,
                "video_url": None,
                "image_urls": [],
            },
        }

        error = validate_success_payload({"raw": {"id": "abc123"}, "normalized": normalized})

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_adapter_success_payload")

    def test_rejects_missing_required_nested_keys(self) -> None:
        normalized = {
            "platform": "xhs",
            "content_id": "abc123",
            "content_type": "image_post",
            "canonical_url": "https://www.xiaohongshu.com/explore/abc123",
            "title": "",
            "body_text": "hello",
            "published_at": None,
            "author": {
                "display_name": None,
                "avatar_url": None,
            },
            "stats": {
                "comment_count": None,
                "share_count": None,
                "collect_count": None,
            },
            "media": {
                "video_url": None,
                "image_urls": [],
            },
        }

        error = validate_success_payload({"raw": {"id": "abc123"}, "normalized": normalized})

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_adapter_success_payload")

    def test_rejects_invalid_author_identity_fields(self) -> None:
        normalized = {
            "platform": "xhs",
            "content_id": "abc123",
            "content_type": "image_post",
            "canonical_url": "https://www.xiaohongshu.com/explore/abc123",
            "title": "",
            "body_text": "hello",
            "published_at": None,
            "author": {
                "author_id": "",
                "display_name": 1,
                "avatar_url": None,
            },
            "stats": {
                "like_count": None,
                "comment_count": None,
                "share_count": None,
                "collect_count": None,
            },
            "media": {
                "cover_url": None,
                "video_url": None,
                "image_urls": [],
            },
        }

        error = validate_success_payload({"raw": {"id": "abc123"}, "normalized": normalized})

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_adapter_success_payload")

    def test_rejects_bool_as_stats_value(self) -> None:
        normalized = {
            "platform": "xhs",
            "content_id": "abc123",
            "content_type": "image_post",
            "canonical_url": "https://www.xiaohongshu.com/explore/abc123",
            "title": "",
            "body_text": "hello",
            "published_at": None,
            "author": {
                "author_id": None,
                "display_name": None,
                "avatar_url": None,
            },
            "stats": {
                "like_count": False,
                "comment_count": None,
                "share_count": None,
                "collect_count": None,
            },
            "media": {
                "cover_url": None,
                "video_url": None,
                "image_urls": [],
            },
        }

        error = validate_success_payload({"raw": {"id": "abc123"}, "normalized": normalized})

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_adapter_success_payload")

    def test_rejects_impossible_rfc3339_timestamp(self) -> None:
        normalized = {
            "platform": "xhs",
            "content_id": "abc123",
            "content_type": "image_post",
            "canonical_url": "https://www.xiaohongshu.com/explore/abc123",
            "title": "",
            "body_text": "hello",
            "published_at": "2026-99-99T25:61:61Z",
            "author": {
                "author_id": None,
                "display_name": None,
                "avatar_url": None,
            },
            "stats": {
                "like_count": None,
                "comment_count": None,
                "share_count": None,
                "collect_count": None,
            },
            "media": {
                "cover_url": None,
                "video_url": None,
                "image_urls": [],
            },
        }

        error = validate_success_payload({"raw": {"id": "abc123"}, "normalized": normalized})

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_adapter_success_payload")


if __name__ == "__main__":
    unittest.main()
