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
