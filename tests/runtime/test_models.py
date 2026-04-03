from __future__ import annotations

import unittest

from syvert.core.models import (
    RuntimeContractError,
    TaskInput,
    TaskRequest,
    validate_normalized_payload,
    validate_task_request,
)


class TaskRequestValidationTests(unittest.TestCase):
    def test_accepts_minimal_content_detail_request(self) -> None:
        request = TaskRequest(
            adapter_key="xhs",
            capability="content_detail_by_url",
            input=TaskInput(url="https://www.xiaohongshu.com/explore/abc123"),
        )

        validate_task_request(request)

    def test_rejects_missing_adapter_key(self) -> None:
        request = TaskRequest(
            adapter_key="",
            capability="content_detail_by_url",
            input=TaskInput(url="https://www.xiaohongshu.com/explore/abc123"),
        )

        with self.assertRaises(RuntimeContractError) as context:
            validate_task_request(request)

        self.assertEqual(context.exception.code, "missing_adapter_key")

    def test_rejects_unsupported_capability(self) -> None:
        request = TaskRequest(
            adapter_key="xhs",
            capability="search",
            input=TaskInput(url="https://www.xiaohongshu.com/explore/abc123"),
        )

        with self.assertRaises(RuntimeContractError) as context:
            validate_task_request(request)

        self.assertEqual(context.exception.code, "unsupported_capability")


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

        validate_normalized_payload(normalized, input_url="https://www.xiaohongshu.com/explore/abc123")

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

        with self.assertRaises(RuntimeContractError) as context:
            validate_normalized_payload(normalized, input_url="https://www.xiaohongshu.com/explore/abc123")

        self.assertEqual(context.exception.code, "missing_normalized_field")


if __name__ == "__main__":
    unittest.main()
