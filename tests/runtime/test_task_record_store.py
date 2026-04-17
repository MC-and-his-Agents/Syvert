from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from syvert.runtime import TaskInput, TaskRequest, execute_task, execute_task_with_record
from syvert.task_record import (
    TaskRecordContractError,
    TaskRequestSnapshot,
    create_task_record,
    finish_task_record,
    start_task_record,
)
from syvert.task_record_store import LocalTaskRecordStore, TaskRecordStoreError


class SuccessfulAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request):
        self.calls += 1
        return {
            "raw": {"id": "raw-store-1"},
            "normalized": {
                "platform": "stub",
                "content_id": "content-store-1",
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


class SelectiveFailingStore:
    def __init__(self, fail_stage: str) -> None:
        self.fail_stage = fail_stage
        self.records: dict[str, object] = {}

    def write(self, record):
        if record.status == self.fail_stage or (
            self.fail_stage == "completion" and record.status in {"succeeded", "failed"}
        ):
            raise TaskRecordStoreError("boom")
        self.records[record.task_id] = record
        return record

    def load(self, task_id: str):
        return self.records[task_id]

    def mark_invalid(self, task_id: str, *, stage: str, reason: str) -> None:
        self.records[f"invalid:{task_id}"] = {"stage": stage, "reason": reason}


class TerminalFailingLocalStore(LocalTaskRecordStore):
    def __init__(self, root: Path) -> None:
        super().__init__(root)
        self.write_count = 0

    def _write_json_atomic(self, path, payload) -> None:
        if path.suffix == ".json" and path.name.endswith(".json") and not path.name.endswith(".invalid.json"):
            self.write_count += 1
            if self.write_count == 3:
                raise TaskRecordStoreError("boom")
        return super()._write_json_atomic(path, payload)


class BrokenInvalidationLocalStore(TerminalFailingLocalStore):
    def _write_json_atomic(self, path, payload) -> None:
        if path.name.endswith(".invalid.json"):
            raise TaskRecordStoreError("invalid-marker-broken")
        return super()._write_json_atomic(path, payload)


class TaskRecordStoreTests(unittest.TestCase):
    def test_runtime_can_persist_and_reload_success_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = LocalTaskRecordStore(Path(temp_dir))
            outcome = execute_task_with_record(
                TaskRequest(
                    adapter_key="stub",
                    capability="content_detail_by_url",
                    input=TaskInput(url="https://example.com/post/store-1"),
                ),
                adapters={"stub": SuccessfulAdapter()},
                task_id_factory=lambda: "task-store-1",
                task_record_store=store,
            )

            self.assertEqual(outcome.envelope["status"], "success")
            self.assertIsNotNone(outcome.task_record)
            self.assertEqual(store.load("task-store-1"), outcome.task_record)

    def test_runtime_can_persist_and_reload_failed_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = LocalTaskRecordStore(Path(temp_dir))
            outcome = execute_task_with_record(
                TaskRequest(
                    adapter_key="stub",
                    capability="content_detail_by_url",
                    input=TaskInput(url="https://example.com/post/store-2"),
                ),
                adapters={"stub": PlatformFailureAdapter()},
                task_id_factory=lambda: "task-store-2",
                task_record_store=store,
            )

            self.assertEqual(outcome.envelope["status"], "failed")
            self.assertEqual(outcome.envelope["error"]["code"], "platform_broken")
            self.assertIsNotNone(outcome.task_record)
            self.assertEqual(store.load("task-store-2"), outcome.task_record)

    def test_core_default_path_persists_without_explicit_store_argument(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.dict(os.environ, {"SYVERT_TASK_RECORD_STORE_DIR": temp_dir}, clear=False):
                envelope = execute_task(
                    TaskRequest(
                        adapter_key="stub",
                        capability="content_detail_by_url",
                        input=TaskInput(url="https://example.com/post/store-default"),
                    ),
                    adapters={"stub": SuccessfulAdapter()},
                    task_id_factory=lambda: "task-store-default",
                )

            self.assertEqual(envelope["status"], "success")
            persisted = LocalTaskRecordStore(Path(temp_dir)).load("task-store-default")
            self.assertEqual(persisted.status, "succeeded")

    def test_runtime_fails_closed_before_adapter_execute_when_accepted_persistence_fails(self) -> None:
        adapter = SuccessfulAdapter()
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key="stub",
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/store-3"),
            ),
            adapters={"stub": adapter},
            task_id_factory=lambda: "task-store-3",
            task_record_store=SelectiveFailingStore("accepted"),
        )

        self.assertEqual(outcome.envelope["status"], "failed")
        self.assertEqual(outcome.envelope["error"]["category"], "runtime_contract")
        self.assertEqual(outcome.envelope["error"]["code"], "task_record_persistence_failed")
        self.assertEqual(outcome.envelope["error"]["details"]["stage"], "accepted")
        self.assertEqual(adapter.calls, 0)
        self.assertIsNone(outcome.task_record)

    def test_runtime_fails_closed_when_terminal_persistence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = SuccessfulAdapter()
            store = TerminalFailingLocalStore(Path(temp_dir))
            outcome = execute_task_with_record(
                TaskRequest(
                    adapter_key="stub",
                    capability="content_detail_by_url",
                    input=TaskInput(url="https://example.com/post/store-4"),
                ),
                adapters={"stub": adapter},
                task_id_factory=lambda: "task-store-4",
                task_record_store=store,
            )

            self.assertEqual(outcome.envelope["status"], "failed")
            self.assertEqual(outcome.envelope["error"]["code"], "task_record_persistence_failed")
            self.assertEqual(outcome.envelope["error"]["details"]["stage"], "completion")
            self.assertEqual(adapter.calls, 1)
            self.assertIsNone(outcome.task_record)
            with self.assertRaises(TaskRecordStoreError):
                store.load("task-store-4")

    def test_runtime_rejects_half_history_even_when_invalidation_marker_cannot_be_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = SuccessfulAdapter()
            store = BrokenInvalidationLocalStore(Path(temp_dir))
            outcome = execute_task_with_record(
                TaskRequest(
                    adapter_key="stub",
                    capability="content_detail_by_url",
                    input=TaskInput(url="https://example.com/post/store-4b"),
                ),
                adapters={"stub": adapter},
                task_id_factory=lambda: "task-store-4b",
                task_record_store=store,
            )

            self.assertEqual(outcome.envelope["status"], "failed")
            self.assertEqual(outcome.envelope["error"]["code"], "task_record_persistence_failed")
            self.assertIn("invalidation_reason", outcome.envelope["error"]["details"])
            self.assertEqual(adapter.calls, 1)
            with self.assertRaises((TaskRecordStoreError, FileNotFoundError)):
                store.load("task-store-4b")

    def test_store_rejects_non_accepted_first_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = LocalTaskRecordStore(Path(temp_dir))
            snapshot = TaskRequestSnapshot(
                adapter_key="stub",
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/post/store-5",
                collection_mode="hybrid",
            )
            running = start_task_record(create_task_record("task-store-5", snapshot))

            with self.assertRaises(TaskRecordStoreError):
                store.write(running)

    def test_store_allows_idempotent_terminal_rewrite_and_rejects_conflicting_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = LocalTaskRecordStore(Path(temp_dir))
            snapshot = TaskRequestSnapshot(
                adapter_key="stub",
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/post/store-6",
                collection_mode="hybrid",
            )
            accepted = create_task_record("task-store-6", snapshot, occurred_at="2026-04-17T12:00:00Z")
            running = start_task_record(accepted, occurred_at="2026-04-17T12:00:01Z")
            envelope = {
                "task_id": "task-store-6",
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
            failed = finish_task_record(running, envelope, occurred_at="2026-04-17T12:00:02Z")

            store.write(accepted)
            store.write(running)
            stored_failed = store.write(failed)
            self.assertEqual(store.write(failed), stored_failed)

            conflicting = dict(envelope)
            conflicting["error"] = dict(envelope["error"])
            conflicting["error"]["code"] = "changed"
            with self.assertRaises((TaskRecordStoreError, TaskRecordContractError)):
                store.write(finish_task_record(running, conflicting, occurred_at="2026-04-17T12:00:02Z"))


if __name__ == "__main__":
    unittest.main()
