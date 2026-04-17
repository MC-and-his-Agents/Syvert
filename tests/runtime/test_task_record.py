from __future__ import annotations

import unittest

from syvert.runtime import TaskInput, TaskRequest, execute_task, execute_task_with_record
from syvert.task_record import (
    TaskRecordContractError,
    TaskRequestSnapshot,
    create_task_record,
    finish_task_record,
    start_task_record,
    task_record_from_dict,
    task_record_to_dict,
)


class SuccessfulAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request):
        return {
            "raw": {"id": "raw-1"},
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


class PlatformFailureAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request):
        from syvert.runtime import PlatformAdapterError

        raise PlatformAdapterError(
            code="platform_broken",
            message="boom",
            details={"reason": "bad"},
        )


class UnsupportedCapabilityAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"creator_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request):
        raise AssertionError("execute should not be called")


class UnserializableSuccessAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request):
        return {
            "raw": {"id": "raw-bad", "bad": object()},
            "normalized": {
                "platform": "stub",
                "content_id": "content-bad",
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


class TaskRecordCodecTests(unittest.TestCase):
    def test_round_trips_success_record(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key="stub",
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/1"),
            ),
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-1",
        )

        self.assertEqual(outcome.envelope["status"], "success")
        self.assertIsNotNone(outcome.task_record)

        payload = task_record_to_dict(outcome.task_record)
        restored = task_record_from_dict(payload)

        self.assertEqual(restored, outcome.task_record)
        self.assertEqual(restored.status, "succeeded")

    def test_rejects_missing_required_lifecycle_event(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key="stub",
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/2"),
            ),
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-2",
        )
        payload = task_record_to_dict(outcome.task_record)
        payload["logs"] = payload["logs"][:-1]

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_accepts_idempotent_terminal_rewrite_and_rejects_conflicting_terminal(self) -> None:
        snapshot = TaskRequestSnapshot(
            adapter_key="stub",
            capability="content_detail_by_url",
            target_type="url",
            target_value="https://example.com/post/3",
            collection_mode="hybrid",
        )
        accepted = create_task_record("task-record-3", snapshot, occurred_at="2026-04-17T10:30:00Z")
        running = start_task_record(accepted, occurred_at="2026-04-17T10:30:01Z")
        envelope = {
            "task_id": "task-record-3",
            "adapter_key": "stub",
            "capability": "content_detail_by_url",
            "status": "failed",
            "error": {
                "category": "platform",
                "code": "platform_broken",
                "message": "boom",
                "details": {"reason": "bad"},
            },
        }
        failed = finish_task_record(running, envelope, occurred_at="2026-04-17T10:30:02Z")

        self.assertEqual(finish_task_record(failed, envelope), failed)

        conflicting = dict(envelope)
        conflicting["error"] = dict(envelope["error"])
        conflicting["error"]["code"] = "changed"
        with self.assertRaises(TaskRecordContractError):
            finish_task_record(failed, conflicting)

    def test_rejects_invalid_scalar_types_during_round_trip_load(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key="stub",
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/3b"),
            ),
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-3b",
        )
        payload = task_record_to_dict(outcome.task_record)
        payload["task_id"] = 123

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)


class RuntimeTaskRecordTests(unittest.TestCase):
    def test_execute_task_with_record_keeps_preaccepted_failure_outside_durable_history(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key="stub",
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/4"),
            ),
            adapters={"stub": UnsupportedCapabilityAdapter()},
            task_id_factory=lambda: "task-record-4",
        )

        self.assertEqual(outcome.envelope["status"], "failed")
        self.assertEqual(outcome.envelope["error"]["code"], "capability_not_supported")
        self.assertIsNone(outcome.task_record)

    def test_execute_task_with_record_builds_failed_record_for_business_failure(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key="stub",
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/5"),
            ),
            adapters={"stub": PlatformFailureAdapter()},
            task_id_factory=lambda: "task-record-5",
        )

        self.assertEqual(outcome.envelope["status"], "failed")
        self.assertIsNotNone(outcome.task_record)
        self.assertEqual(outcome.task_record.status, "failed")
        self.assertEqual(outcome.task_record.result.envelope["error"]["code"], "platform_broken")

    def test_execute_task_envelope_contract_stays_unchanged(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key="stub",
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/6"),
            ),
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-6",
        )

        self.assertEqual(envelope["status"], "success")
        self.assertEqual(envelope["task_id"], "task-record-6")
        self.assertIn("raw", envelope)
        self.assertIn("normalized", envelope)

    def test_execute_task_with_record_fails_closed_when_terminal_envelope_is_not_json_serializable(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key="stub",
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/7"),
            ),
            adapters={"stub": UnserializableSuccessAdapter()},
            task_id_factory=lambda: "task-record-7",
        )

        self.assertEqual(outcome.envelope["status"], "failed")
        self.assertEqual(outcome.envelope["error"]["code"], "envelope_not_json_serializable")
        self.assertIsNone(outcome.task_record)


if __name__ == "__main__":
    unittest.main()
