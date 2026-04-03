from __future__ import annotations

from dataclasses import dataclass
import unittest

from syvert.runtime import PlatformAdapterError, TaskInput, TaskRequest, execute_task


@dataclass(frozen=True)
class ExtendedTaskInput(TaskInput):
    platform_hint: str


@dataclass(frozen=True)
class ExtendedTaskRequest(TaskRequest):
    extra: str


class SuccessfulAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail_by_url"})

    def execute(self, request: TaskRequest) -> dict[str, object]:
        self.last_request = request
        return {
            "raw": {
                "id": "raw-1",
                "url": request.input.url,
            },
            "normalized": {
                "platform": "stub",
                "content_id": "content-1",
                "content_type": "unknown",
                "canonical_url": request.input.url,
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
                "canonical_url": request.input.url,
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


class CrashingAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail_by_url"})

    def execute(self, request: TaskRequest):
        raise RuntimeError("boom")


class PlatformErrorWithBadDetailsAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail_by_url"})

    def execute(self, request: TaskRequest):
        from syvert.runtime import PlatformAdapterError

        raise PlatformAdapterError(code="platform_broken", message="bad details", details=None)


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
            input=TaskInput(url="https://example.com/posts/1"),
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
        self.assertEqual(envelope["normalized"]["canonical_url"], request.input.url)
        self.assertEqual(adapter.last_request.input.url, request.input.url)

    def test_execute_task_rejects_unknown_adapter_as_runtime_contract_failure(self) -> None:
        request = TaskRequest(
            adapter_key="missing",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
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
            input=TaskInput(url="https://example.com/posts/1"),
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
            input=TaskInput(url="https://example.com/posts/1"),
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
            input=TaskInput(url="https://example.com/posts/1"),
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
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": ListPayloadAdapter()},
            task_id_factory=lambda: "task-005",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_success_payload")

    def test_execute_task_fails_closed_when_adapter_raises_generic_exception(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": CrashingAdapter()},
            task_id_factory=lambda: "task-006",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "adapter_execution_error")

    def test_execute_task_handles_platform_error_with_non_mapping_details(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": PlatformErrorWithBadDetailsAdapter()},
            task_id_factory=lambda: "task-007",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "platform")
        self.assertEqual(envelope["error"]["code"], "platform_broken")
        self.assertEqual(envelope["error"]["details"], {})

    def test_execute_task_wraps_platform_error(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
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

    def test_execute_task_rejects_empty_task_id_from_factory(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: "",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertIsInstance(envelope["task_id"], str)
        self.assertTrue(envelope["task_id"])
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_task_id")

    def test_execute_task_rejects_non_string_task_id_from_factory(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: 123,  # type: ignore[return-value]
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertIsInstance(envelope["task_id"], str)
        self.assertTrue(envelope["task_id"])
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_task_id")

    def test_execute_task_fails_closed_when_task_id_factory_raises(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertIsInstance(envelope["task_id"], str)
        self.assertTrue(envelope["task_id"])
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_task_id")

    def test_execute_task_rejects_extended_task_input_shape(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=ExtendedTaskInput(
                url="https://example.com/posts/1",
                platform_hint="xhs",
            ),
        )

        envelope = execute_task(
            request,
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: "task-extra-shape",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_rejects_extended_task_request_shape(self) -> None:
        request = ExtendedTaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
            extra="leaks",
        )

        envelope = execute_task(
            request,
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: "task-extra-request-shape",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")


if __name__ == "__main__":
    unittest.main()
