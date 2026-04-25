from __future__ import annotations

import os
import json
import tempfile
import unittest
from unittest import mock

import syvert.runtime as runtime_module
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
from tests.runtime.resource_fixtures import ResourceStoreEnvMixin, baseline_resource_requirement_declarations

TEST_ADAPTER_KEY = "xhs"


class TaskRecordStoreEnvMixin(ResourceStoreEnvMixin):
    def setUp(self) -> None:
        super().setUp()
        self._task_record_store_dir = tempfile.TemporaryDirectory()
        self._task_record_store_patcher = mock.patch.dict(
            os.environ,
            {"SYVERT_TASK_RECORD_STORE_DIR": self._task_record_store_dir.name},
            clear=False,
        )
        self._task_record_store_patcher.start()

    def tearDown(self) -> None:
        self._task_record_store_patcher.stop()
        self._task_record_store_dir.cleanup()
        super().tearDown()


class SuccessfulAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(adapter_key=TEST_ADAPTER_KEY)

    def execute(self, request):
        return {
            "raw": {"id": "raw-1"},
            "normalized": {
                "platform": TEST_ADAPTER_KEY,
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
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(adapter_key=TEST_ADAPTER_KEY)

    def execute(self, request):
        from syvert.runtime import PlatformAdapterError

        raise PlatformAdapterError(
            code="platform_broken",
            message="boom",
            details={"reason": "bad"},
        )


class UnsupportedCapabilityAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"creator_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request):
        raise AssertionError("execute should not be called")


class UnserializableSuccessAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(adapter_key=TEST_ADAPTER_KEY)

    def execute(self, request):
        return {
            "raw": {"id": "raw-bad", "bad": object()},
            "normalized": {
                "platform": TEST_ADAPTER_KEY,
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


class OffsetTimestampSuccessAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(adapter_key=TEST_ADAPTER_KEY)

    def execute(self, request):
        return {
            "raw": {"id": "raw-offset-1"},
            "normalized": {
                "platform": TEST_ADAPTER_KEY,
                "content_id": "content-offset-1",
                "content_type": "unknown",
                "canonical_url": request.input.url,
                "title": "",
                "body_text": "",
                "published_at": "2026-04-17T10:30:00+00:00",
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


class TaskRecordCodecTests(TaskRecordStoreEnvMixin, unittest.TestCase):
    def test_round_trips_success_record(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/1"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
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
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/2"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-2",
        )
        payload = task_record_to_dict(outcome.task_record)
        payload["logs"] = payload["logs"][:-1]

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_rejects_conflicting_observability_replay_id(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/observability-conflict"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-observability-conflict",
        )
        payload = task_record_to_dict(outcome.task_record)
        duplicate_event = dict(payload["runtime_structured_log_events"][0])
        duplicate_event["message"] = "conflicting replay"
        payload["runtime_structured_log_events"].append(duplicate_event)

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_rejects_invalid_runtime_observability_enum_values(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/observability-enum"),
            ),
            adapters={TEST_ADAPTER_KEY: PlatformFailureAdapter()},
            task_id_factory=lambda: "task-record-observability-enum",
        )
        payload = json.loads(json.dumps(task_record_to_dict(outcome.task_record)))

        invalid_signal = json.loads(json.dumps(task_record_to_dict(outcome.task_record)))
        invalid_signal["runtime_failure_signals"][0]["failure_phase"] = "not_approved"
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(invalid_signal)

        invalid_event = json.loads(json.dumps(task_record_to_dict(outcome.task_record)))
        invalid_event["runtime_structured_log_events"][0]["event_type"] = "not_approved"
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(invalid_event)

        invalid_metric = payload
        invalid_metric["runtime_execution_metric_samples"][0]["metric_name"] = "not_approved"
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(invalid_metric)

    def test_rejects_failed_observability_without_required_signal_or_error_metadata(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/observability-required-fields"),
            ),
            adapters={TEST_ADAPTER_KEY: PlatformFailureAdapter()},
            task_id_factory=lambda: "task-record-observability-required-fields",
        )
        payload = json.loads(json.dumps(task_record_to_dict(outcome.task_record)))

        missing_signal_id = json.loads(json.dumps(payload))
        missing_signal_id["runtime_failure_signals"][0]["signal_id"] = ""
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(missing_signal_id)

        missing_signal_ref = json.loads(json.dumps(payload))
        failed_event = next(
            event
            for event in missing_signal_ref["runtime_structured_log_events"]
            if event["event_type"] == "task_failed"
        )
        failed_event["failure_signal_id"] = ""
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(missing_signal_ref)

        for event_type in ("retry_scheduled", "observability_write_failed"):
            with self.subTest(event_type=event_type):
                missing_event_signal_ref = json.loads(json.dumps(payload))
                failed_event = next(
                    event
                    for event in missing_event_signal_ref["runtime_structured_log_events"]
                    if event["event_type"] == "task_failed"
                )
                extra_event = dict(failed_event)
                extra_event["event_id"] = f"runtime_log_event:required-fields:{event_type}"
                extra_event["event_type"] = event_type
                extra_event["failure_signal_id"] = ""
                missing_event_signal_ref["runtime_structured_log_events"].append(extra_event)
                with self.assertRaises(TaskRecordContractError):
                    task_record_from_dict(missing_event_signal_ref)

        missing_error_metadata = json.loads(json.dumps(payload))
        failed_metric = next(
            metric
            for metric in missing_error_metadata["runtime_execution_metric_samples"]
            if metric["metric_name"] == "task_failed_total"
        )
        failed_metric["error_category"] = ""
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(missing_error_metadata)

        missing_failure_phase = json.loads(json.dumps(payload))
        failed_metric = next(
            metric
            for metric in missing_failure_phase["runtime_execution_metric_samples"]
            if metric["metric_name"] == "task_failed_total"
        )
        failed_metric["failure_phase"] = ""
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(missing_failure_phase)

        missing_error_code = json.loads(json.dumps(payload))
        failed_metric = next(
            metric
            for metric in missing_error_code["runtime_execution_metric_samples"]
            if metric["metric_name"] == "task_failed_total"
        )
        failed_metric["error_code"] = ""
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(missing_error_code)

        for metric_name in (
            "timeout_total",
            "admission_concurrency_rejected_total",
            "retry_concurrency_rejected_total",
        ):
            with self.subTest(metric_name=metric_name):
                missing_metric_metadata = json.loads(json.dumps(payload))
                failed_metric = next(
                    metric
                    for metric in missing_metric_metadata["runtime_execution_metric_samples"]
                    if metric["metric_name"] == "task_failed_total"
                )
                extra_metric = dict(failed_metric)
                extra_metric["metric_id"] = f"runtime_metric_sample:required-fields:{metric_name}"
                extra_metric["metric_name"] = metric_name
                extra_metric["error_category"] = ""
                missing_metric_metadata["runtime_execution_metric_samples"].append(extra_metric)
                with self.assertRaises(TaskRecordContractError):
                    task_record_from_dict(missing_metric_metadata)

        invalid_signal_resource_refs = json.loads(json.dumps(payload))
        invalid_signal_resource_refs["runtime_failure_signals"][0]["resource_trace_refs"] = [{"bogus": "value"}]
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(invalid_signal_resource_refs)

        invalid_signal_runtime_refs = json.loads(json.dumps(payload))
        invalid_signal_runtime_refs["runtime_failure_signals"][0]["runtime_result_refs"] = [{"bogus": "value"}]
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(invalid_signal_runtime_refs)

        invalid_log_resource_refs = json.loads(json.dumps(payload))
        failed_event = next(
            event
            for event in invalid_log_resource_refs["runtime_structured_log_events"]
            if event["event_type"] == "task_failed"
        )
        failed_event["resource_trace_refs"] = [{"bogus": "value"}]
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(invalid_log_resource_refs)

        invalid_log_runtime_refs = json.loads(json.dumps(payload))
        failed_event = next(
            event
            for event in invalid_log_runtime_refs["runtime_structured_log_events"]
            if event["event_type"] == "task_failed"
        )
        failed_event["runtime_result_refs"] = [{"bogus": "value"}]
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(invalid_log_runtime_refs)

    def test_migrates_missing_and_rejects_mismatched_task_record_ref(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/ref"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-ref-1",
        )
        payload = task_record_to_dict(outcome.task_record)

        missing_ref = dict(payload)
        missing_ref.pop("task_record_ref")
        restored = task_record_from_dict(missing_ref)
        self.assertEqual(restored.task_record_ref, "task_record:task-record-ref-1")

        mismatched_ref = dict(payload)
        mismatched_ref["task_record_ref"] = "task_record:other"
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(mismatched_ref)

    def test_rejects_mismatched_terminal_observability_fields(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/observability"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-observability-1",
        )
        payload = task_record_to_dict(outcome.task_record)

        for field, value in (
            ("task_record_ref", "task_record:other"),
            ("runtime_result_refs", [{"kind": "artifact", "id": "other"}]),
            ("execution_control_events", [{"event": "other"}]),
        ):
            with self.subTest(field=field):
                corrupted = dict(payload)
                corrupted["result"] = {
                    "envelope": dict(payload["result"]["envelope"]),
                }
                corrupted["result"]["envelope"][field] = value
                with self.assertRaises(TaskRecordContractError):
                    task_record_from_dict(corrupted)

    def test_accepts_idempotent_terminal_rewrite_and_rejects_conflicting_terminal(self) -> None:
        snapshot = TaskRequestSnapshot(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            target_type="url",
            target_value="https://example.com/post/3",
            collection_mode="hybrid",
        )
        accepted = create_task_record("task-record-3", snapshot, occurred_at="2026-04-17T10:30:00Z")
        running = start_task_record(accepted, occurred_at="2026-04-17T10:30:01Z")
        envelope = {
            "task_id": "task-record-3",
            "adapter_key": TEST_ADAPTER_KEY,
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
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/3b"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-3b",
        )
        payload = task_record_to_dict(outcome.task_record)
        payload["task_id"] = 123

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_rejects_terminal_envelope_mismatch_during_round_trip_load(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/3c"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-3c",
        )
        payload = task_record_to_dict(outcome.task_record)
        payload["result"]["envelope"]["task_id"] = "task-record-other"

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_rejects_success_envelope_nested_type_drift_during_round_trip_load(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/3cc"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-3cc",
        )
        payload = task_record_to_dict(outcome.task_record)
        payload["result"]["envelope"]["normalized"]["author"]["author_id"] = 123
        payload["result"]["envelope"]["normalized"]["stats"]["like_count"] = "1"
        payload["result"]["envelope"]["normalized"]["media"]["image_urls"] = [1]

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_rejects_failed_envelope_without_details_during_round_trip_load(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/3cf"),
            ),
            adapters={TEST_ADAPTER_KEY: PlatformFailureAdapter()},
            task_id_factory=lambda: "task-record-3cf",
        )
        payload = task_record_to_dict(outcome.task_record)
        del payload["result"]["envelope"]["error"]["details"]

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_rejects_failed_envelope_with_invalid_category_during_round_trip_load(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/3cg"),
            ),
            adapters={TEST_ADAPTER_KEY: PlatformFailureAdapter()},
            task_id_factory=lambda: "task-record-3cg",
        )
        payload = task_record_to_dict(outcome.task_record)
        payload["result"]["envelope"]["error"]["category"] = "broken"

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_rejects_untrusted_timeline_during_round_trip_load(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/3d"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-3d",
        )
        payload = task_record_to_dict(outcome.task_record)
        payload["logs"][1]["occurred_at"] = "2026-04-17T10:29:59Z"

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_rejects_snapshot_values_outside_shared_request_model(self) -> None:
        with self.assertRaises(TaskRecordContractError):
            create_task_record(
                "task-record-3e",
                TaskRequestSnapshot(
                    adapter_key=TEST_ADAPTER_KEY,
                    capability="content_detail_by_url",
                    target_type="unsupported",
                    target_value="https://example.com/post/3e",
                    collection_mode="hybrid",
                ),
            )


class RuntimeTaskRecordTests(TaskRecordStoreEnvMixin, unittest.TestCase):
    def test_execute_task_with_record_keeps_preaccepted_failure_outside_durable_history(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/4"),
            ),
            adapters={TEST_ADAPTER_KEY: UnsupportedCapabilityAdapter()},
            task_id_factory=lambda: "task-record-4",
        )

        self.assertEqual(outcome.envelope["status"], "failed")
        self.assertEqual(outcome.envelope["error"]["code"], "capability_not_supported")
        self.assertIsNone(outcome.task_record)

    def test_execute_task_with_record_builds_failed_record_for_business_failure(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/5"),
            ),
            adapters={TEST_ADAPTER_KEY: PlatformFailureAdapter()},
            task_id_factory=lambda: "task-record-5",
        )

        self.assertEqual(outcome.envelope["status"], "failed")
        self.assertIsNotNone(outcome.task_record)
        self.assertEqual(outcome.task_record.status, "failed")
        self.assertEqual(outcome.task_record.result.envelope["error"]["code"], "platform_broken")

    def test_execute_task_with_record_builds_failed_record_for_unmatched_resource_capabilities(self) -> None:
        with mock.patch.dict(
            runtime_module.RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE,
            {(runtime_module.CONTENT_DETAIL_BY_URL, runtime_module.LEGACY_COLLECTION_MODE): ("account",)},
            clear=True,
        ), mock.patch(
            "syvert.runtime.acquire_runtime_resource_bundle",
            side_effect=AssertionError("acquire should not run when matcher is unmatched"),
        ):
            outcome = execute_task_with_record(
                TaskRequest(
                    adapter_key=TEST_ADAPTER_KEY,
                    capability="content_detail_by_url",
                    input=TaskInput(url="https://example.com/post/5b"),
                ),
                adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
                task_id_factory=lambda: "task-record-5b",
            )

        self.assertEqual(outcome.envelope["status"], "failed")
        self.assertEqual(outcome.envelope["error"]["code"], "resource_unavailable")
        self.assertIsNotNone(outcome.task_record)
        self.assertEqual(outcome.task_record.status, "failed")
        self.assertEqual(outcome.task_record.result.envelope["error"]["code"], "resource_unavailable")

    def test_execute_task_envelope_contract_stays_unchanged(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/6"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-6",
        )

        self.assertEqual(envelope["status"], "success")
        self.assertEqual(envelope["task_id"], "task-record-6")
        self.assertIn("raw", envelope)
        self.assertIn("normalized", envelope)

    def test_execute_task_preserves_stateless_replay_for_fixed_task_id(self) -> None:
        first = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/6b"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-6b",
        )
        second = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/6b"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-6b",
        )

        self.assertEqual(first["status"], "success")
        self.assertEqual(second["status"], "success")

    def test_execute_task_with_record_fails_closed_when_terminal_envelope_is_not_json_serializable(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/7"),
            ),
            adapters={TEST_ADAPTER_KEY: UnserializableSuccessAdapter()},
            task_id_factory=lambda: "task-record-7",
        )

        self.assertEqual(outcome.envelope["status"], "failed")
        self.assertEqual(outcome.envelope["error"]["code"], "envelope_not_json_serializable")
        self.assertEqual(outcome.envelope["runtime_failure_signal"]["failure_phase"], "persistence")
        self.assertEqual(outcome.envelope["runtime_failure_signal"]["task_record_ref"], "task_record:task-record-7")
        task_failed_log = next(
            event
            for event in outcome.envelope["runtime_structured_log_events"]
            if event["event_type"] == "task_failed"
        )
        self.assertEqual(task_failed_log["failure_signal_id"], outcome.envelope["runtime_failure_signal"]["signal_id"])
        task_failed_metric = next(
            metric
            for metric in outcome.envelope["runtime_execution_metric_samples"]
            if metric["metric_name"] == "task_failed_total"
        )
        self.assertEqual(task_failed_metric["error_code"], "envelope_not_json_serializable")
        self.assertIsNone(outcome.task_record)

    def test_execute_task_preserves_public_envelope_when_task_record_fails_to_close(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/8"),
            ),
            adapters={TEST_ADAPTER_KEY: UnserializableSuccessAdapter()},
            task_id_factory=lambda: "task-record-8",
        )

        self.assertEqual(envelope["status"], "success")
        self.assertEqual(envelope["task_id"], "task-record-8")
        self.assertIn("raw", envelope)
        self.assertEqual(type(envelope["raw"]["bad"]).__name__, "object")

    def test_execute_task_with_record_accepts_offset_utc_timestamp_in_success_payload(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/9"),
            ),
            adapters={TEST_ADAPTER_KEY: OffsetTimestampSuccessAdapter()},
            task_id_factory=lambda: "task-record-9",
        )

        self.assertEqual(outcome.envelope["status"], "success")
        self.assertIsNotNone(outcome.task_record)
        self.assertEqual(
            outcome.task_record.result.envelope["normalized"]["published_at"],
            "2026-04-17T10:30:00+00:00",
        )


if __name__ == "__main__":
    unittest.main()
