from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest import mock

import syvert.runtime as runtime_module
from syvert.runtime import (
    ExecutionConcurrencyPolicy,
    ExecutionControlPolicy,
    ExecutionRetryPolicy,
    ExecutionTimeoutPolicy,
    PlatformAdapterError,
    TaskInput,
    TaskRequest,
    execute_task_with_record,
)
from syvert.task_record_store import LocalTaskRecordStore
from syvert.resource_lifecycle_store import default_resource_lifecycle_store
from tests.runtime.resource_fixtures import ResourceStoreEnvMixin, baseline_resource_requirement_declarations


TEST_ADAPTER_KEY = "xhs"
TEST_CAPABILITY = "content_detail_by_url"


def parse_rfc3339_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc)


def make_policy(
    *,
    timeout_ms: int = 30000,
    max_attempts: int = 1,
    backoff_ms: int = 0,
    scope: str = "global",
    max_in_flight: int = 1,
) -> ExecutionControlPolicy:
    return ExecutionControlPolicy(
        timeout=ExecutionTimeoutPolicy(timeout_ms=timeout_ms),
        retry=ExecutionRetryPolicy(max_attempts=max_attempts, backoff_ms=backoff_ms),
        concurrency=ExecutionConcurrencyPolicy(scope=scope, max_in_flight=max_in_flight, on_limit="reject"),
    )


def make_request(policy: ExecutionControlPolicy) -> TaskRequest:
    return TaskRequest(
        adapter_key=TEST_ADAPTER_KEY,
        capability=TEST_CAPABILITY,
        input=TaskInput(url="https://example.com/posts/execution-control"),
        execution_control_policy=policy,
    )


class BaseAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(adapter_key=TEST_ADAPTER_KEY)

    def success_payload(self, request):
        return {
            "raw": {"id": "raw-control", "url": request.input.url},
            "normalized": {
                "platform": TEST_ADAPTER_KEY,
                "content_id": "content-control",
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


class SlowAdapter(BaseAdapter):
    def __init__(self) -> None:
        self.finished = False

    def execute(self, request):
        time.sleep(0.05)
        self.finished = True
        return self.success_payload(request)


class SlowInvalidDispositionAdapter(BaseAdapter):
    def execute(self, request):
        time.sleep(0.05)
        payload = self.success_payload(request)
        payload["resource_disposition_hint"] = {
            "lease_id": request.resource_bundle.lease_id,
            "target_status_after_release": "INVALID",
            "reason": "late_timeout_invalid_resource",
        }
        return payload


class SlowMalformedDispositionAdapter(BaseAdapter):
    def execute(self, request):
        time.sleep(0.05)
        payload = self.success_payload(request)
        payload["resource_disposition_hint"] = {
            "lease_id": request.resource_bundle.lease_id,
            "target_status_after_release": "BOGUS",
            "reason": "late_timeout_bad_hint",
        }
        return payload


class SuccessAdapter(BaseAdapter):
    def execute(self, request):
        return self.success_payload(request)


class CorruptingSlotReleaseAdapter(BaseAdapter):
    def execute(self, request):
        runtime_module._EXECUTION_CONCURRENCY_IN_FLIGHT.clear()
        return self.success_payload(request)


class RetryableThenSuccessAdapter(BaseAdapter):
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request):
        self.calls += 1
        if self.calls == 1:
            raise PlatformAdapterError(
                code="transient_platform",
                message="try again",
                details={"retryable": True},
            )
        return self.success_payload(request)


class SlowThenSuccessAdapter(BaseAdapter):
    def __init__(self) -> None:
        self.calls = 0
        self.events: list[str] = []

    def execute(self, request):
        self.calls += 1
        self.events.append(f"start-{self.calls}")
        if self.calls == 1:
            time.sleep(0.03)
            self.events.append("end-1")
            return self.success_payload(request)
        self.events.append("end-2")
        return self.success_payload(request)


class HangingAdapter(BaseAdapter):
    def __init__(self) -> None:
        self.calls = 0
        self.started = threading.Event()
        self.stop = threading.Event()

    def execute(self, request):
        self.calls += 1
        self.started.set()
        self.stop.wait()
        return self.success_payload(request)


class NonRetryablePlatformAdapter(BaseAdapter):
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request):
        self.calls += 1
        raise PlatformAdapterError(
            code="hard_platform",
            message="do not retry",
            details={"retryable": False},
        )


class AdapterReportedExecutionTimeoutAdapter(BaseAdapter):
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request):
        self.calls += 1
        raise PlatformAdapterError(
            code="execution_timeout",
            message="adapter-owned timeout",
            details={"control_code": "execution_timeout"},
        )


class RetryableFailureAdapter(BaseAdapter):
    def execute(self, request):
        raise PlatformAdapterError(
            code="transient_platform",
            message="still broken",
            details={"retryable": True, "reason": "slot-test"},
        )


class ExecutionControlRuntimeTests(ResourceStoreEnvMixin, unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        runtime_module._EXECUTION_CONCURRENCY_IN_FLIGHT.clear()
        runtime_module._EXECUTION_CONCURRENCY_ADMISSION_GUARDS.clear()
        self._task_record_store_dir = tempfile.TemporaryDirectory()
        self._task_record_store_patcher = mock.patch.dict(
            os.environ,
            {"SYVERT_TASK_RECORD_STORE_DIR": self._task_record_store_dir.name},
            clear=False,
        )
        self._task_record_store_patcher.start()
        self.store = LocalTaskRecordStore(Path(self._task_record_store_dir.name))

    def tearDown(self) -> None:
        runtime_module._EXECUTION_CONCURRENCY_IN_FLIGHT.clear()
        runtime_module._EXECUTION_CONCURRENCY_ADMISSION_GUARDS.clear()
        self._task_record_store_patcher.stop()
        self._task_record_store_dir.cleanup()
        super().tearDown()

    def task_record_files(self) -> list[str]:
        return sorted(path.name for path in self.store.root.glob("*.json"))

    def test_timeout_attempt_fails_as_platform_execution_timeout(self) -> None:
        adapter = SlowAdapter()
        result = execute_task_with_record(
            make_request(make_policy(timeout_ms=1)),
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-timeout-control",
            task_record_store=self.store,
        )

        self.assertTrue(adapter.finished)
        self.assertIsNotNone(result.task_record)
        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["category"], "platform")
        self.assertEqual(result.envelope["error"]["code"], "execution_timeout")
        self.assertEqual(result.envelope["error"]["details"]["control_code"], "execution_timeout")
        self.assertEqual(result.envelope["runtime_result_refs"][0]["outcome"], "timeout")
        self.assertEqual(result.envelope["runtime_result_refs"][0]["control_code"], "execution_timeout")
        self.assertEqual(result.envelope["runtime_result_refs"][0]["adapter_key"], TEST_ADAPTER_KEY)
        self.assertEqual(result.envelope["runtime_result_refs"][0]["capability"], TEST_CAPABILITY)
        self.assertIn("started_at", result.envelope["runtime_result_refs"][0])
        self.assertIn("ended_at", result.envelope["runtime_result_refs"][0])
        self.assertIn("terminal_envelope", result.envelope["runtime_result_refs"][0])
        self.assertEqual(result.envelope["execution_control_events"][0]["event_type"], "retry_exhausted")
        self.assertEqual(result.envelope["runtime_result_refs"][1], result.envelope["execution_control_events"][0])
        self.assertEqual(
            result.envelope["error"]["details"]["execution_control_event"],
            result.envelope["execution_control_events"][0],
        )
        self.assertEqual(result.envelope["error"]["details"]["retry_exhausted"], True)
        self.assertEqual(result.envelope["error"]["details"]["attempt_count"], 1)
        self.assertEqual(result.envelope["error"]["details"]["max_attempts"], 1)
        self.assertEqual(
            result.envelope["error"]["details"]["last_attempt_outcome_ref"],
            result.envelope["runtime_result_refs"][0],
        )
        snapshot = default_resource_lifecycle_store().load_snapshot()
        released_at = snapshot.leases[-1].released_at
        self.assertIsNotNone(released_at)
        self.assertGreater(
            parse_rfc3339_utc(result.envelope["runtime_result_refs"][0]["ended_at"]),
            parse_rfc3339_utc(released_at),
        )
        self.assertEqual(result.task_record.status, "failed")

    def test_timeout_closeout_consumes_late_resource_disposition_hint(self) -> None:
        result = execute_task_with_record(
            make_request(make_policy(timeout_ms=1)),
            adapters={TEST_ADAPTER_KEY: SlowInvalidDispositionAdapter()},
            task_id_factory=lambda: "task-timeout-late-hint",
            task_record_store=self.store,
        )

        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["code"], "execution_timeout")
        snapshot = default_resource_lifecycle_store().load_snapshot()
        self.assertEqual({lease.target_status_after_release for lease in snapshot.leases}, {"INVALID"})
        self.assertEqual({lease.release_reason for lease in snapshot.leases}, {"late_timeout_invalid_resource"})
        self.assertEqual({resource.status for resource in snapshot.resources}, {"INVALID"})

    def test_timeout_closeout_malformed_late_hint_fails_closed_and_quarantines_resources(self) -> None:
        result = execute_task_with_record(
            make_request(make_policy(timeout_ms=1)),
            adapters={TEST_ADAPTER_KEY: SlowMalformedDispositionAdapter()},
            task_id_factory=lambda: "task-timeout-late-bad-hint",
            task_record_store=self.store,
        )

        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["category"], "runtime_contract")
        self.assertEqual(result.envelope["error"]["code"], "execution_control_state_invalid")
        self.assertEqual(result.envelope["error"]["details"]["resource_quarantine"], "INVALID")
        self.assertNotEqual(result.envelope["runtime_failure_signal"]["failure_phase"], "timeout")
        self.assertNotIn(
            "timeout_triggered",
            {event["event_type"] for event in result.envelope["runtime_structured_log_events"]},
        )
        self.assertNotIn(
            "timeout_total",
            {metric["metric_name"] for metric in result.envelope["runtime_execution_metric_samples"]},
        )
        snapshot = default_resource_lifecycle_store().load_snapshot()
        self.assertEqual({lease.target_status_after_release for lease in snapshot.leases}, {"INVALID"})
        self.assertEqual(
            {lease.release_reason for lease in snapshot.leases},
            {"timeout_closeout_invalid_resource_disposition_hint"},
        )
        self.assertEqual({resource.status for resource in snapshot.resources}, {"INVALID"})

    def test_timeout_closeout_cleanup_failure_is_not_retryable(self) -> None:
        adapter = SlowThenSuccessAdapter()

        def fail_cleanup(*args, **kwargs):
            return runtime_module.failure_envelope(
                "task-timeout-cleanup-failure",
                TEST_ADAPTER_KEY,
                TEST_CAPABILITY,
                runtime_module.runtime_contract_error(
                    "execution_control_state_invalid",
                    "resource closeout failed",
                    details={"retryable": False},
                ),
            )

        with mock.patch("syvert.runtime.settle_managed_resource_bundle", side_effect=fail_cleanup):
            result = execute_task_with_record(
                make_request(make_policy(timeout_ms=1, max_attempts=2)),
                adapters={TEST_ADAPTER_KEY: adapter},
                task_id_factory=lambda: "task-timeout-cleanup-failure",
                task_record_store=self.store,
            )

        self.assertEqual(adapter.calls, 1)
        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["category"], "runtime_contract")
        self.assertEqual(result.envelope["error"]["code"], "execution_control_state_invalid")
        self.assertNotIn("execution_control_events", result.envelope)

    def test_timeout_quarantines_late_result_before_retry_reacquires_slot(self) -> None:
        adapter = SlowThenSuccessAdapter()

        result = execute_task_with_record(
            make_request(make_policy(timeout_ms=1, max_attempts=2)),
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-timeout-retry-quarantine",
            task_record_store=self.store,
        )

        self.assertEqual(result.envelope["status"], "success")
        self.assertEqual(adapter.events, ["start-1", "end-1", "start-2", "end-2"])

    def test_hung_adapter_timeout_fails_closed_without_permanent_slot_occupancy(self) -> None:
        adapter = HangingAdapter()
        started_at = time.monotonic()
        result = execute_task_with_record(
            make_request(make_policy(timeout_ms=1, max_attempts=2)),
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-hung-timeout-closeout",
            task_record_store=self.store,
        )
        elapsed = time.monotonic() - started_at

        try:
            self.assertTrue(adapter.started.is_set())
            self.assertLess(elapsed, 0.5)
            self.assertEqual(adapter.calls, 1)
            self.assertEqual(result.envelope["status"], "failed")
            self.assertEqual(result.envelope["error"]["category"], "runtime_contract")
            self.assertEqual(result.envelope["error"]["code"], "execution_control_state_invalid")
            self.assertEqual(result.envelope["error"]["details"]["control_code"], "execution_timeout")
            self.assertEqual(result.envelope["error"]["details"]["retryable"], False)
            self.assertEqual(result.envelope["error"]["details"]["resource_quarantine"], "INVALID")
            self.assertNotEqual(result.envelope["runtime_failure_signal"]["failure_phase"], "timeout")
            self.assertNotIn(
                "timeout_triggered",
                {event["event_type"] for event in result.envelope["runtime_structured_log_events"]},
            )
            self.assertNotIn(
                "timeout_total",
                {metric["metric_name"] for metric in result.envelope["runtime_execution_metric_samples"]},
            )
            self.assertNotIn("runtime_result_refs", result.envelope)
            self.assertEqual(result.task_record.status, "failed")

            snapshot = default_resource_lifecycle_store().load_snapshot()
            self.assertEqual({lease.target_status_after_release for lease in snapshot.leases}, {"INVALID"})
            self.assertEqual({resource.status for resource in snapshot.resources}, {"INVALID"})
            self.assertEqual(sum(runtime_module._EXECUTION_CONCURRENCY_IN_FLIGHT.values()), 1)

            followup = execute_task_with_record(
                make_request(make_policy(timeout_ms=30000, max_attempts=1)),
                adapters={TEST_ADAPTER_KEY: SuccessAdapter()},
                task_id_factory=lambda: "task-after-hung-timeout-closeout",
                task_record_store=self.store,
            )

            self.assertIsNone(followup.task_record)
            self.assertEqual(followup.envelope["error"]["code"], "concurrency_limit_exceeded")
        finally:
            adapter.stop.set()
            for _ in range(100):
                if not runtime_module._EXECUTION_CONCURRENCY_IN_FLIGHT:
                    break
                time.sleep(0.01)
            self.assertEqual(runtime_module._EXECUTION_CONCURRENCY_IN_FLIGHT, {})

    def test_retryable_platform_failure_retries_same_task_until_success(self) -> None:
        adapter = RetryableThenSuccessAdapter()

        result = execute_task_with_record(
            make_request(make_policy(max_attempts=2)),
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-retry-success",
            task_record_store=self.store,
        )

        self.assertEqual(adapter.calls, 2)
        self.assertEqual(result.envelope["status"], "success")
        self.assertEqual(result.task_record.task_id, "task-retry-success")
        self.assertEqual(result.task_record.status, "succeeded")
        self.assertEqual([ref["attempt_index"] for ref in result.envelope["runtime_result_refs"]], [1, 2])
        self.assertTrue(all("control_code" not in ref for ref in result.envelope["runtime_result_refs"]))

    def test_non_retryable_platform_failure_does_not_retry(self) -> None:
        adapter = NonRetryablePlatformAdapter()

        result = execute_task_with_record(
            make_request(make_policy(max_attempts=3)),
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-no-retry",
            task_record_store=self.store,
        )

        self.assertEqual(adapter.calls, 1)
        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["code"], "hard_platform")
        self.assertNotIn("execution_control_events", result.envelope)
        self.assertNotIn("control_code", result.envelope["runtime_result_refs"][0])

    def test_adapter_reported_execution_timeout_does_not_retry_without_retryable_detail(self) -> None:
        adapter = AdapterReportedExecutionTimeoutAdapter()

        result = execute_task_with_record(
            make_request(make_policy(max_attempts=2)),
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-adapter-timeout-not-core-timeout",
            task_record_store=self.store,
        )

        self.assertEqual(adapter.calls, 1)
        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["code"], "execution_timeout")
        self.assertNotIn("execution_control_events", result.envelope)
        self.assertEqual(result.envelope["runtime_result_refs"][0]["outcome"], "failed")
        self.assertNotIn("control_code", result.envelope["runtime_result_refs"][0])

    def test_concurrency_slot_release_underflow_fails_closed(self) -> None:
        result = execute_task_with_record(
            make_request(make_policy()),
            adapters={TEST_ADAPTER_KEY: CorruptingSlotReleaseAdapter()},
            task_id_factory=lambda: "task-slot-release-underflow",
            task_record_store=self.store,
        )

        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["category"], "runtime_contract")
        self.assertEqual(result.envelope["error"]["code"], "execution_control_state_invalid")
        self.assertEqual(
            result.envelope["error"]["details"]["control_code"],
            "execution_control_state_invalid",
        )
        self.assertEqual(result.envelope["runtime_result_refs"][0]["outcome"], "failed")
        self.assertEqual(result.task_record.status, "failed")
        self.assertEqual(runtime_module._EXECUTION_CONCURRENCY_IN_FLIGHT, {})

    def test_pre_accepted_concurrency_rejection_does_not_create_task_record(self) -> None:
        policy = make_policy(scope="global", max_in_flight=1)
        held_slot = runtime_module.acquire_execution_concurrency_slot(
            policy.concurrency,
            adapter_key=TEST_ADAPTER_KEY,
            capability=TEST_CAPABILITY,
        )
        try:
            result = execute_task_with_record(
                make_request(policy),
                adapters={TEST_ADAPTER_KEY: RetryableThenSuccessAdapter()},
                task_id_factory=lambda: "task-pre-accept-rejected",
                task_record_store=self.store,
            )
        finally:
            runtime_module.release_execution_concurrency_slot(held_slot)

        self.assertIsNone(result.task_record)
        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["category"], "invalid_input")
        self.assertEqual(result.envelope["error"]["code"], "concurrency_limit_exceeded")
        self.assertEqual(result.envelope["error"]["details"]["task_record_ref"], "none")
        self.assertEqual(self.task_record_files(), [])

    def test_resource_preparation_does_not_count_as_execution_in_flight(self) -> None:
        policy = make_policy(scope="global", max_in_flight=1)
        first_adapter = HangingAdapter()
        second_result: dict[str, object] = {}
        first_result: dict[str, object] = {}
        resource_prep_entered = threading.Event()
        allow_resource_prep = threading.Event()
        second_finished = threading.Event()
        first_finished = threading.Event()
        real_acquire_resource_bundle = runtime_module.acquire_runtime_resource_bundle

        def blocking_acquire_resource_bundle(*args, **kwargs):
            resource_prep_entered.set()
            self.assertTrue(allow_resource_prep.wait(timeout=1))
            return real_acquire_resource_bundle(*args, **kwargs)

        def run_first() -> None:
            first_result["value"] = execute_task_with_record(
                make_request(policy),
                adapters={TEST_ADAPTER_KEY: first_adapter},
                task_id_factory=lambda: "task-resource-prep-first",
                task_record_store=self.store,
            )
            first_finished.set()

        def run_second() -> None:
            second_result["value"] = execute_task_with_record(
                make_request(policy),
                adapters={TEST_ADAPTER_KEY: SuccessAdapter()},
                task_id_factory=lambda: "task-resource-prep-second",
                task_record_store=self.store,
            )
            second_finished.set()

        with mock.patch("syvert.runtime.acquire_runtime_resource_bundle", side_effect=blocking_acquire_resource_bundle):
            first_thread = threading.Thread(target=run_first)
            second_thread = threading.Thread(target=run_second)
            first_thread.start()
            try:
                self.assertTrue(resource_prep_entered.wait(timeout=1))
                self.assertEqual(runtime_module._EXECUTION_CONCURRENCY_IN_FLIGHT, {})
                self.assertTrue(
                    runtime_module.is_execution_concurrency_slot_available(
                        policy.concurrency,
                        adapter_key=TEST_ADAPTER_KEY,
                        capability=TEST_CAPABILITY,
                    )
                )

                second_thread.start()
                self.assertFalse(second_finished.wait(timeout=0.05))

                allow_resource_prep.set()
                self.assertTrue(first_adapter.started.wait(timeout=1))
                self.assertTrue(second_finished.wait(timeout=1))
            finally:
                first_adapter.stop.set()
                allow_resource_prep.set()
                first_thread.join(timeout=1)
                second_thread.join(timeout=1)

        self.assertTrue(first_finished.is_set())
        self.assertIsNotNone(first_result.get("value"))
        self.assertIsNotNone(second_result.get("value"))
        rejected = second_result["value"]
        self.assertIsNone(rejected.task_record)
        self.assertEqual(rejected.envelope["error"]["code"], "concurrency_limit_exceeded")
        self.assertEqual(self.task_record_files(), ["task-resource-prep-first.json"])

    def test_accepted_persistence_does_not_count_as_execution_in_flight(self) -> None:
        policy = make_policy(scope="global", max_in_flight=1)
        first_adapter = HangingAdapter()
        second_result: dict[str, object] = {}
        first_result: dict[str, object] = {}
        accepted_persist_entered = threading.Event()
        allow_accepted_persist = threading.Event()
        second_finished = threading.Event()
        first_finished = threading.Event()
        real_persist_task_record = runtime_module.persist_task_record

        def blocking_persist_task_record(*args, **kwargs):
            record = args[3]
            if kwargs.get("stage") == "accepted" and record.task_id == "task-accepted-window-first":
                accepted_persist_entered.set()
                self.assertTrue(allow_accepted_persist.wait(timeout=1))
            return real_persist_task_record(*args, **kwargs)

        def run_first() -> None:
            first_result["value"] = execute_task_with_record(
                make_request(policy),
                adapters={TEST_ADAPTER_KEY: first_adapter},
                task_id_factory=lambda: "task-accepted-window-first",
                task_record_store=self.store,
            )
            first_finished.set()

        def run_second() -> None:
            second_result["value"] = execute_task_with_record(
                make_request(policy),
                adapters={TEST_ADAPTER_KEY: SuccessAdapter()},
                task_id_factory=lambda: "task-accepted-window-second",
                task_record_store=self.store,
            )
            second_finished.set()

        with mock.patch("syvert.runtime.persist_task_record", side_effect=blocking_persist_task_record):
            first_thread = threading.Thread(target=run_first)
            second_thread = threading.Thread(target=run_second)
            second_started = False
            first_thread.start()
            try:
                self.assertTrue(accepted_persist_entered.wait(timeout=1))
                self.assertEqual(runtime_module._EXECUTION_CONCURRENCY_IN_FLIGHT, {})

                second_thread.start()
                second_started = True
                self.assertFalse(second_finished.wait(timeout=0.05))

                allow_accepted_persist.set()
                self.assertTrue(first_adapter.started.wait(timeout=1))
                self.assertTrue(second_finished.wait(timeout=1))
            finally:
                first_adapter.stop.set()
                allow_accepted_persist.set()
                first_thread.join(timeout=1)
                if second_started:
                    second_thread.join(timeout=1)

        self.assertTrue(first_finished.is_set())
        self.assertIsNotNone(first_result.get("value"))
        self.assertIsNotNone(second_result.get("value"))
        rejected = second_result["value"]
        self.assertIsNone(rejected.task_record)
        self.assertEqual(rejected.envelope["error"]["code"], "concurrency_limit_exceeded")
        self.assertEqual(self.task_record_files(), ["task-accepted-window-first.json"])

    def test_post_accepted_retry_reacquire_rejection_preserves_previous_failure(self) -> None:
        real_available = runtime_module.is_execution_concurrency_slot_available
        calls = 0

        def available_once_then_reject(policy, *, adapter_key, capability):
            nonlocal calls
            calls += 1
            if calls == 1:
                return real_available(policy, adapter_key=adapter_key, capability=capability)
            return False

        with mock.patch("syvert.runtime.is_execution_concurrency_slot_available", side_effect=available_once_then_reject):
            result = execute_task_with_record(
                make_request(make_policy(max_attempts=2)),
                adapters={TEST_ADAPTER_KEY: RetryableFailureAdapter()},
                task_id_factory=lambda: "task-retry-slot-rejected",
                task_record_store=self.store,
            )

        self.assertIsNotNone(result.task_record)
        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["category"], "platform")
        self.assertEqual(result.envelope["error"]["code"], "transient_platform")
        self.assertEqual(result.envelope["execution_control_events"][0]["event_type"], "retry_concurrency_rejected")
        self.assertEqual(
            result.envelope["error"]["details"]["execution_control_event"],
            result.envelope["execution_control_events"][0],
        )
        self.assertEqual(result.envelope["error"]["details"]["retry_concurrency_rejected"], True)
        self.assertEqual(result.envelope["error"]["details"]["attempt_count"], 1)
        self.assertEqual(result.envelope["runtime_result_refs"][1], result.envelope["execution_control_events"][0])
        self.assertEqual(result.task_record.status, "failed")
        snapshot = default_resource_lifecycle_store().load_snapshot()
        self.assertTrue(all(lease.released_at is not None for lease in snapshot.leases))
        self.assertEqual({resource.status for resource in snapshot.resources}, {"AVAILABLE"})

    def test_retry_slot_accounting_invariant_failure_fails_closed(self) -> None:
        real_acquire = runtime_module.acquire_execution_concurrency_slot
        calls = 0

        def acquire_once_then_invalid(policy, *, adapter_key, capability):
            nonlocal calls
            calls += 1
            if calls == 1:
                return real_acquire(policy, adapter_key=adapter_key, capability=capability)
            return None

        with mock.patch("syvert.runtime.acquire_execution_concurrency_slot", side_effect=acquire_once_then_invalid):
            result = execute_task_with_record(
                make_request(make_policy(max_attempts=2)),
                adapters={TEST_ADAPTER_KEY: RetryableFailureAdapter()},
                task_id_factory=lambda: "task-retry-slot-invariant-invalid",
                task_record_store=self.store,
            )

        self.assertIsNotNone(result.task_record)
        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["category"], "platform")
        self.assertEqual(result.envelope["error"]["code"], "transient_platform")
        self.assertEqual(result.envelope["execution_control_events"][0]["event_type"], "retry_concurrency_rejected")
        self.assertEqual(
            result.envelope["error"]["details"]["execution_control_event"],
            result.envelope["execution_control_events"][0],
        )
        self.assertEqual(result.envelope["runtime_result_refs"][1], result.envelope["execution_control_events"][0])
        self.assertEqual(result.task_record.status, "failed")

    def test_retry_slot_rejection_preserves_current_cleanup_failure(self) -> None:
        real_acquire = runtime_module.acquire_execution_concurrency_slot
        real_settle = runtime_module.settle_managed_resource_bundle
        acquire_calls = 0
        settle_calls = 0

        def acquire_once_then_invalid(policy, *, adapter_key, capability):
            nonlocal acquire_calls
            acquire_calls += 1
            if acquire_calls == 1:
                return real_acquire(policy, adapter_key=adapter_key, capability=capability)
            return None

        def fail_second_settle(*args, **kwargs):
            nonlocal settle_calls
            settle_calls += 1
            if settle_calls == 2:
                return runtime_module.failure_envelope(
                    "task-retry-slot-cleanup-failed",
                    TEST_ADAPTER_KEY,
                    TEST_CAPABILITY,
                    runtime_module.runtime_contract_error(
                        "resource_cleanup_failed",
                        "resource cleanup failed during retry slot rejection",
                        details={"stage": "resource_cleanup", "retryable": False},
                    ),
                )
            return real_settle(*args, **kwargs)

        with (
            mock.patch("syvert.runtime.acquire_execution_concurrency_slot", side_effect=acquire_once_then_invalid),
            mock.patch("syvert.runtime.settle_managed_resource_bundle", side_effect=fail_second_settle),
        ):
            result = execute_task_with_record(
                make_request(make_policy(max_attempts=2)),
                adapters={TEST_ADAPTER_KEY: RetryableFailureAdapter()},
                task_id_factory=lambda: "task-retry-slot-cleanup-failed",
                task_record_store=self.store,
            )

        self.assertIsNotNone(result.task_record)
        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["category"], "runtime_contract")
        self.assertEqual(result.envelope["error"]["code"], "resource_cleanup_failed")
        self.assertEqual(result.envelope["execution_control_events"][0]["event_type"], "retry_concurrency_rejected")
        self.assertEqual(result.envelope["runtime_result_refs"][1], result.envelope["execution_control_events"][0])
        self.assertEqual(result.task_record.status, "failed")

    def test_concurrency_scope_keys_are_enforced_independently(self) -> None:
        global_policy = make_policy(scope="global")
        global_slot = runtime_module.acquire_execution_concurrency_slot(
            global_policy.concurrency,
            adapter_key="xhs",
            capability=TEST_CAPABILITY,
        )
        try:
            self.assertIsNone(
                runtime_module.acquire_execution_concurrency_slot(
                    global_policy.concurrency,
                    adapter_key="douyin",
                    capability=TEST_CAPABILITY,
                )
            )
        finally:
            runtime_module.release_execution_concurrency_slot(global_slot)

        adapter_policy = make_policy(scope="adapter")
        adapter_slot = runtime_module.acquire_execution_concurrency_slot(
            adapter_policy.concurrency,
            adapter_key="xhs",
            capability=TEST_CAPABILITY,
        )
        try:
            self.assertIsNone(
                runtime_module.acquire_execution_concurrency_slot(
                    adapter_policy.concurrency,
                    adapter_key="xhs",
                    capability="other",
                )
            )
            douyin_slot = runtime_module.acquire_execution_concurrency_slot(
                adapter_policy.concurrency,
                adapter_key="douyin",
                capability=TEST_CAPABILITY,
            )
            self.assertIsNotNone(douyin_slot)
            runtime_module.release_execution_concurrency_slot(douyin_slot)
        finally:
            runtime_module.release_execution_concurrency_slot(adapter_slot)

        adapter_capability_policy = make_policy(scope="adapter_capability")
        capability_slot = runtime_module.acquire_execution_concurrency_slot(
            adapter_capability_policy.concurrency,
            adapter_key="xhs",
            capability=TEST_CAPABILITY,
        )
        try:
            self.assertIsNone(
                runtime_module.acquire_execution_concurrency_slot(
                    adapter_capability_policy.concurrency,
                    adapter_key="xhs",
                    capability=TEST_CAPABILITY,
                )
            )
            other_capability_slot = runtime_module.acquire_execution_concurrency_slot(
                adapter_capability_policy.concurrency,
                adapter_key="xhs",
                capability="other_capability",
            )
            self.assertIsNotNone(other_capability_slot)
            runtime_module.release_execution_concurrency_slot(other_capability_slot)
        finally:
            runtime_module.release_execution_concurrency_slot(capability_slot)


if __name__ == "__main__":
    unittest.main()
