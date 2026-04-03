from __future__ import annotations

import unittest

from syvert.runtime import PlatformAdapterError, TaskRequest, execute_task


class SuccessfulAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail_by_url"})

    def execute(self, request: TaskRequest) -> dict[str, object]:
        self.last_request = request
        return {
            "raw": {
                "id": "raw-1",
                "url": request.input_url,
            },
            "normalized": {
                "platform": "stub",
                "content_id": "content-1",
                "content_type": "unknown",
                "canonical_url": request.input_url,
                "title": "",
                "body_text": "",
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


class MissingRawAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail_by_url"})

    def execute(self, request: TaskRequest) -> dict[str, object]:
        return {
            "normalized": {
                "platform": "stub",
                "content_id": "content-1",
                "content_type": "unknown",
                "canonical_url": request.input_url,
                "title": "",
                "body_text": "",
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


class NonePayloadAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail_by_url"})

    def execute(self, request: TaskRequest):
        return None


class ListPayloadAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail_by_url"})

    def execute(self, request: TaskRequest):
        return []


class PlatformFailureAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail_by_url"})

    def execute(self, request: TaskRequest) -> dict[str, object]:
        raise PlatformAdapterError(
            code="content_not_found",
            message="content not found",
            details={"reason": "missing"},
        )


class RuntimeExecutionTests(unittest.TestCase):
    def test_execute_task_builds_success_envelope_from_adapter_payload(self) -> None:
        adapter = SuccessfulAdapter()
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input_url="https://example.com/posts/1",
        )

        envelope = execute_task(
            request,
            adapters={"stub": adapter},
            task_id_factory=lambda: "task-001",
        )

        self.assertEqual(envelope["task_id"], "task-001")
        self.assertEqual(envelope["adapter_key"], "stub")
        self.assertEqual(envelope["capability"], "content_detail_by_url")
        self.assertEqual(envelope["status"], "success")
        self.assertIn("raw", envelope)
        self.assertEqual(envelope["normalized"]["canonical_url"], request.input_url)
        self.assertEqual(adapter.last_request.input_url, request.input_url)

    def test_execute_task_rejects_unknown_adapter_as_runtime_contract_failure(self) -> None:
        request = TaskRequest(
            adapter_key="missing",
            capability="content_detail_by_url",
            input_url="https://example.com/posts/1",
        )

        envelope = execute_task(
            request,
            adapters={},
            task_id_factory=lambda: "task-002",
        )

        self.assertEqual(envelope["task_id"], "task-002")
        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "adapter_not_found")

    def test_execute_task_rejects_unsupported_capability(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="search",
            input_url="https://example.com/posts/1",
        )

        envelope = execute_task(
            request,
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: "task-unsupported",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_capability")

    def test_execute_task_rejects_success_without_raw_payload(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input_url="https://example.com/posts/1",
        )

        envelope = execute_task(
            request,
            adapters={"stub": MissingRawAdapter()},
            task_id_factory=lambda: "task-003",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_success_payload")

    def test_execute_task_fails_closed_when_adapter_returns_none(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input_url="https://example.com/posts/1",
        )

        envelope = execute_task(
            request,
            adapters={"stub": NonePayloadAdapter()},
            task_id_factory=lambda: "task-004",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_success_payload")

    def test_execute_task_fails_closed_when_adapter_returns_non_mapping_payload(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input_url="https://example.com/posts/1",
        )

        envelope = execute_task(
            request,
            adapters={"stub": ListPayloadAdapter()},
            task_id_factory=lambda: "task-005",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_success_payload")

    def test_execute_task_wraps_platform_error(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input_url="https://example.com/posts/1",
        )

        envelope = execute_task(
            request,
            adapters={"stub": PlatformFailureAdapter()},
            task_id_factory=lambda: "task-platform-failure",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "platform")
        self.assertEqual(envelope["error"]["code"], "content_not_found")
        self.assertEqual(envelope["error"]["details"]["reason"], "missing")


if __name__ == "__main__":
    unittest.main()
