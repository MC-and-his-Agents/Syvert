from __future__ import annotations

import unittest

from syvert.core.contracts import PlatformAdapterError
from syvert.core.executor import execute_task
from syvert.core.models import TaskInput, TaskRequest


class SuccessfulAdapter:
    adapter_key = "xhs"
    supported_capabilities = {"content_detail_by_url"}

    def collect(self, request: TaskRequest) -> dict[str, object]:
        return {
            "raw": {"id": "abc123"},
            "normalized": {
                "platform": "xhs",
                "content_id": "abc123",
                "content_type": "image_post",
                "canonical_url": request.input.url,
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
            },
        }


class UnsupportedCapabilityAdapter:
    adapter_key = "xhs"
    supported_capabilities = {"creator_detail_by_url"}

    def collect(self, request: TaskRequest) -> dict[str, object]:
        raise AssertionError("collect should not be called")


class PlatformFailureAdapter:
    adapter_key = "douyin"
    supported_capabilities = {"content_detail_by_url"}

    def collect(self, request: TaskRequest) -> dict[str, object]:
        raise PlatformAdapterError(
            code="content_not_found",
            message="content not found",
            details={"reason": "missing"},
        )


class ExecutorTests(unittest.TestCase):
    def test_returns_runtime_contract_failure_when_adapter_is_missing(self) -> None:
        request = TaskRequest(
            adapter_key="missing",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/post/1"),
        )

        result = execute_task(request, adapters={})

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["category"], "runtime_contract")
        self.assertEqual(result["error"]["code"], "adapter_not_found")

    def test_returns_runtime_contract_failure_when_capability_is_unsupported(self) -> None:
        request = TaskRequest(
            adapter_key="xhs",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/post/1"),
        )

        result = execute_task(request, adapters={"xhs": UnsupportedCapabilityAdapter()})

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["category"], "runtime_contract")
        self.assertEqual(result["error"]["code"], "unsupported_capability")

    def test_returns_success_envelope_for_valid_adapter_result(self) -> None:
        request = TaskRequest(
            adapter_key="xhs",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/post/1"),
        )

        result = execute_task(request, adapters={"xhs": SuccessfulAdapter()})

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["adapter_key"], "xhs")
        self.assertEqual(result["capability"], "content_detail_by_url")
        self.assertIsInstance(result["task_id"], str)
        self.assertTrue(result["task_id"])
        self.assertIn("raw", result)
        self.assertIn("normalized", result)

    def test_wraps_platform_error_in_failed_envelope(self) -> None:
        request = TaskRequest(
            adapter_key="douyin",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/post/1"),
        )

        result = execute_task(request, adapters={"douyin": PlatformFailureAdapter()})

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["category"], "platform")
        self.assertEqual(result["error"]["code"], "content_not_found")
        self.assertEqual(result["error"]["details"]["reason"], "missing")


if __name__ == "__main__":
    unittest.main()
