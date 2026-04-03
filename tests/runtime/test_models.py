from __future__ import annotations

import unittest

from syvert.runtime import TaskRequest, validate_request, validate_success_payload


class TaskRequestValidationTests(unittest.TestCase):
    def test_accepts_minimal_content_detail_request(self) -> None:
        request = TaskRequest(
            adapter_key="xhs",
            capability="content_detail_by_url",
            input_url="https://www.xiaohongshu.com/explore/abc123",
        )

        self.assertIsNone(validate_request(request))

    def test_rejects_missing_adapter_key(self) -> None:
        request = TaskRequest(
            adapter_key="",
            capability="content_detail_by_url",
            input_url="https://www.xiaohongshu.com/explore/abc123",
        )

        error = validate_request(request)

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_task_request")

    def test_rejects_unsupported_capability(self) -> None:
        request = TaskRequest(
            adapter_key="xhs",
            capability="search",
            input_url="https://www.xiaohongshu.com/explore/abc123",
        )

        error = validate_request(request)

        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "invalid_capability")


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


if __name__ == "__main__":
    unittest.main()
