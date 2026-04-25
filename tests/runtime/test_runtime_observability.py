from __future__ import annotations

import unittest
import tempfile
from pathlib import Path
from unittest import mock

from syvert.runtime import (
    ExecutionConcurrencyPolicy,
    ExecutionControlPolicy,
    ExecutionRetryPolicy,
    ExecutionTimeoutPolicy,
    PlatformAdapterError,
    TaskInput,
    TaskRequest,
    acquire_execution_concurrency_slot,
    execute_task,
    execute_task_with_record,
    failure_envelope,
    release_execution_concurrency_slot,
    runtime_contract_error,
)
from syvert.task_record import TaskRecordContractError, task_record_to_dict
from syvert.task_record_store import LocalTaskRecordStore
from tests.runtime.test_runtime import (
    TEST_ADAPTER_KEY,
    PlatformFailureAdapter,
    SuccessfulAdapter,
)
from tests.runtime.resource_fixtures import ResourceStoreEnvMixin


def make_request() -> TaskRequest:
    return TaskRequest(
        adapter_key=TEST_ADAPTER_KEY,
        capability="content_detail_by_url",
        input=TaskInput(url="https://example.com/posts/observability"),
    )


class RetryablePlatformFailureAdapter(PlatformFailureAdapter):
    def execute(self, request):
        raise PlatformAdapterError(
            code="transient_platform",
            message="try again later",
            details={"retryable": True},
        )


class InvalidInputAttemptFailureAdapter(SuccessfulAdapter):
    def execute(self, request):
        raise PlatformAdapterError(
            code="adapter_precheck_failed",
            message="adapter rejected request during execution",
            category="invalid_input",
            details={"reason": "adapter_precheck"},
        )


class RetryableThenSuccessAdapter(SuccessfulAdapter):
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request):
        self.calls += 1
        if self.calls == 1:
            raise PlatformAdapterError(
                code="transient_platform",
                message="try again later",
                details={"retryable": True},
            )
        return super().execute(request)


class TwiceRetryableThenSuccessAdapter(SuccessfulAdapter):
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request):
        self.calls += 1
        if self.calls <= 2:
            raise PlatformAdapterError(
                code="transient_platform",
                message="try again later",
                details={"retryable": True},
            )
        return super().execute(request)


class AcceptedFailingStore:
    def write(self, record):
        raise OSError("boom")

    def mark_invalid(self, task_id: str, *, stage: str, reason: str) -> None:
        self.invalid_marker = {"task_id": task_id, "stage": stage, "reason": reason}


class RuntimeObservabilityTests(ResourceStoreEnvMixin, unittest.TestCase):
    def test_generic_failure_envelope_does_not_inject_runtime_observability(self) -> None:
        envelope = failure_envelope("", "", "", runtime_contract_error("generic_failure", "generic"))

        self.assertEqual(envelope["status"], "failed")
        self.assertNotIn("runtime_failure_signal", envelope)
        self.assertNotIn("runtime_structured_log_events", envelope)
        self.assertNotIn("runtime_execution_metric_samples", envelope)

    def test_record_lifecycle_contract_failures_project_failure_observability(self) -> None:
        with mock.patch(
            "syvert.runtime.create_task_record",
            side_effect=TaskRecordContractError("bad-create"),
        ):
            create_failure = execute_task(
                make_request(),
                adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
                task_id_factory=lambda: "task-observability-create-record-failed",
            )

        self.assertEqual(create_failure["status"], "failed")
        self.assertIn("runtime_failure_signal", create_failure)
        self.assertIn("runtime_structured_log_events", create_failure)
        self.assertEqual(create_failure["runtime_failure_signal"]["task_record_ref"], "none")
        self.assertEqual(
            create_failure["runtime_structured_log_events"][0]["failure_signal_id"],
            create_failure["runtime_failure_signal"]["signal_id"],
        )

        with mock.patch(
            "syvert.runtime.start_task_record",
            side_effect=TaskRecordContractError("bad-start"),
        ):
            start_failure = execute_task(
                make_request(),
                adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
                task_id_factory=lambda: "task-observability-start-record-failed",
            )

        self.assertEqual(start_failure["status"], "failed")
        self.assertIn("runtime_failure_signal", start_failure)
        self.assertIn("runtime_structured_log_events", start_failure)
        self.assertEqual(
            start_failure["runtime_failure_signal"]["task_record_ref"],
            "task_record:task-observability-start-record-failed",
        )
        self.assertEqual(
            start_failure["runtime_structured_log_events"][0]["failure_signal_id"],
            start_failure["runtime_failure_signal"]["signal_id"],
        )

    def test_failed_envelope_projects_failure_signal_log_and_metric(self) -> None:
        envelope = execute_task(
            make_request(),
            adapters={TEST_ADAPTER_KEY: PlatformFailureAdapter()},
            task_id_factory=lambda: "task-observability-failed",
        )

        self.assertEqual(envelope["status"], "failed")
        signal = envelope["runtime_failure_signal"]
        self.assertEqual(signal["task_id"], "task-observability-failed")
        self.assertEqual(signal["status"], "failed")
        self.assertEqual(signal["error_category"], envelope["error"]["category"])
        self.assertEqual(signal["error_code"], envelope["error"]["code"])
        self.assertEqual(signal["failure_phase"], "adapter_execution")
        self.assertEqual(signal["task_record_ref"], "task_record:task-observability-failed")
        self.assertEqual(signal["runtime_result_refs"], envelope["runtime_result_refs"])
        self.assertTrue(signal["resource_trace_refs"])
        self.assertEqual(signal["resource_trace_refs"], envelope["error"]["details"]["resource_trace_refs"])

        log_event = next(event for event in envelope["runtime_structured_log_events"] if event["event_type"] == "task_failed")
        self.assertEqual(log_event["event_type"], "task_failed")
        self.assertEqual(log_event["level"], "error")
        self.assertEqual(log_event["failure_signal_id"], signal["signal_id"])

        metric = next(metric for metric in envelope["runtime_execution_metric_samples"] if metric["metric_name"] == "task_failed_total")
        self.assertEqual(metric["metric_name"], "task_failed_total")
        self.assertEqual(metric["metric_value"], 1)
        self.assertEqual(metric["error_category"], signal["error_category"])
        self.assertEqual(metric["error_code"], signal["error_code"])
        attempt_envelope = envelope["runtime_result_refs"][0]["terminal_envelope"]
        self.assertNotIn("runtime_failure_signal", attempt_envelope)
        self.assertNotIn("runtime_structured_log_events", attempt_envelope)
        self.assertNotIn("runtime_execution_metric_samples", attempt_envelope)

    def test_success_envelope_does_not_change_success_payload_shape(self) -> None:
        envelope = execute_task(
            make_request(),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-observability-success",
        )

        self.assertEqual(envelope["status"], "success")
        self.assertIn("raw", envelope)
        self.assertIn("normalized", envelope)
        self.assertNotIn("runtime_failure_signal", envelope)
        self.assertNotIn("runtime_structured_log_events", envelope)
        self.assertNotIn("runtime_execution_metric_samples", envelope)

    def test_retryable_failure_signal_preserves_envelope_classification(self) -> None:
        envelope = execute_task(
            make_request(),
            adapters={TEST_ADAPTER_KEY: RetryablePlatformFailureAdapter()},
            task_id_factory=lambda: "task-observability-retryable",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "platform")
        self.assertEqual(envelope["error"]["code"], "transient_platform")
        self.assertEqual(envelope["runtime_failure_signal"]["error_category"], "platform")
        self.assertEqual(envelope["runtime_failure_signal"]["error_code"], "transient_platform")

    def test_adapter_attempt_invalid_input_projects_adapter_execution_phase(self) -> None:
        envelope = execute_task(
            make_request(),
            adapters={TEST_ADAPTER_KEY: InvalidInputAttemptFailureAdapter()},
            task_id_factory=lambda: "task-observability-attempt-invalid-input",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["runtime_failure_signal"]["failure_phase"], "adapter_execution")
        error_event_types = {event["event_type"] for event in envelope["runtime_structured_log_events"] if event["level"] == "error"}
        self.assertIn("task_failed", error_event_types)
        self.assertNotIn("admission_concurrency_rejected", error_event_types)

    def test_admission_concurrency_rejection_observability_uses_none_task_record_ref(self) -> None:
        policy = ExecutionControlPolicy(
            timeout=ExecutionTimeoutPolicy(timeout_ms=30000),
            retry=ExecutionRetryPolicy(max_attempts=1, backoff_ms=0),
            concurrency=ExecutionConcurrencyPolicy(scope="global", max_in_flight=1, on_limit="reject"),
        )
        held_slot = acquire_execution_concurrency_slot(
            policy.concurrency,
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
        )
        try:
            request = TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/posts/concurrency"),
                execution_control_policy=policy,
            )
            envelope = execute_task(
                request,
                adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
                task_id_factory=lambda: "task-observability-admission-rejected",
            )
        finally:
            release_execution_concurrency_slot(held_slot)

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "concurrency_limit_exceeded")
        self.assertEqual(envelope["runtime_failure_signal"]["task_record_ref"], "none")
        self.assertEqual(envelope["runtime_failure_signal"]["failure_phase"], "concurrency_rejected")
        self.assertEqual(envelope["runtime_failure_signal"]["runtime_result_refs"], envelope["runtime_result_refs"])
        self.assertEqual(envelope["runtime_result_refs"][0]["event_type"], "admission_concurrency_rejected")
        self.assertEqual(
            envelope["runtime_structured_log_events"][0]["event_type"],
            "admission_concurrency_rejected",
        )
        self.assertEqual(
            envelope["runtime_execution_metric_samples"][0]["metric_name"],
            "admission_concurrency_rejected_total",
        )

    def test_pre_accepted_invalid_input_observability_uses_none_task_record_ref(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="unsupported_capability",
                input=TaskInput(url="https://example.com/posts/pre-accepted-invalid"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-observability-pre-accepted-invalid",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["runtime_failure_signal"]["task_record_ref"], "none")
        self.assertEqual(envelope["error"]["details"]["stage"], "pre_admission")

    def test_retry_scheduled_log_and_metric_are_preserved_on_terminal_failure(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/retry-scheduled"),
            execution_control_policy=ExecutionControlPolicy(
                timeout=ExecutionTimeoutPolicy(timeout_ms=30000),
                retry=ExecutionRetryPolicy(max_attempts=2, backoff_ms=0),
                concurrency=ExecutionConcurrencyPolicy(scope="global", max_in_flight=1, on_limit="reject"),
            ),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: RetryablePlatformFailureAdapter()},
            task_id_factory=lambda: "task-observability-retry-scheduled",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertIn(
            "retry_scheduled",
            {event["event_type"] for event in envelope["runtime_structured_log_events"]},
        )
        self.assertIn(
            "retry_scheduled_total",
            {metric["metric_name"] for metric in envelope["runtime_execution_metric_samples"]},
        )
        non_lifecycle_events = [
            event
            for event in envelope["runtime_structured_log_events"]
            if event["event_type"] not in {"attempt_started", "attempt_finished", "retry_scheduled"}
        ]
        non_lifecycle_metrics = [
            metric
            for metric in envelope["runtime_execution_metric_samples"]
            if metric["metric_name"] not in {"attempt_started_total", "execution_duration_ms", "retry_scheduled_total"}
        ]
        self.assertEqual(len(non_lifecycle_events), 1)
        self.assertEqual(len(non_lifecycle_metrics), 1)
        for runtime_ref in envelope["runtime_result_refs"]:
            if runtime_ref.get("ref_type") == "ExecutionAttemptOutcome":
                self.assertNotIn("runtime_failure_signal", runtime_ref["terminal_envelope"])
                self.assertNotIn("runtime_structured_log_events", runtime_ref["terminal_envelope"])
                self.assertNotIn("runtime_execution_metric_samples", runtime_ref["terminal_envelope"])

    def test_execution_control_default_policy_failure_projects_pre_execution_phase(self) -> None:
        with mock.patch("syvert.runtime.default_execution_control_policy", return_value=None):
            envelope = execute_task(
                make_request(),
                adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
                task_id_factory=lambda: "task-observability-default-policy-invalid",
            )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["code"], "execution_control_state_invalid")
        self.assertEqual(envelope["error"]["details"]["stage"], "pre_execution")
        self.assertEqual(envelope["runtime_failure_signal"]["task_record_ref"], "none")
        self.assertEqual(envelope["runtime_failure_signal"]["failure_phase"], "pre_execution")

    def test_guarded_admission_slot_disappearance_projects_concurrency_phase(self) -> None:
        with tempfile.TemporaryDirectory() as store_dir:
            with mock.patch("syvert.runtime.acquire_execution_concurrency_slot", return_value=None):
                result = execute_task_with_record(
                    make_request(),
                    adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
                    task_id_factory=lambda: "task-observability-guarded-slot-missing",
                    task_record_store=LocalTaskRecordStore(Path(store_dir)),
                )

        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["code"], "execution_control_state_invalid")
        self.assertEqual(result.envelope["error"]["details"]["control_context"], "guarded_admission")
        self.assertEqual(result.envelope["runtime_failure_signal"]["failure_phase"], "concurrency_rejected")

    def test_retry_success_keeps_success_envelope_surface(self) -> None:
        adapter = RetryableThenSuccessAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/retry-success"),
            execution_control_policy=ExecutionControlPolicy(
                timeout=ExecutionTimeoutPolicy(timeout_ms=30000),
                retry=ExecutionRetryPolicy(max_attempts=2, backoff_ms=0),
                concurrency=ExecutionConcurrencyPolicy(scope="global", max_in_flight=1, on_limit="reject"),
            ),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-observability-retry-success",
        )

        self.assertEqual(envelope["status"], "success")
        self.assertEqual(adapter.calls, 2)
        self.assertEqual([ref["attempt_index"] for ref in envelope["runtime_result_refs"]], [1, 2])
        self.assertNotIn("runtime_failure_signal", envelope)
        self.assertNotIn("runtime_structured_log_events", envelope)
        self.assertNotIn("runtime_execution_metric_samples", envelope)

    def test_retry_success_persists_retry_scheduled_carriers_outside_success_envelope(self) -> None:
        adapter = RetryableThenSuccessAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/retry-success-record"),
            execution_control_policy=ExecutionControlPolicy(
                timeout=ExecutionTimeoutPolicy(timeout_ms=30000),
                retry=ExecutionRetryPolicy(max_attempts=2, backoff_ms=0),
                concurrency=ExecutionConcurrencyPolicy(scope="global", max_in_flight=1, on_limit="reject"),
            ),
        )

        with tempfile.TemporaryDirectory() as store_dir:
            store = LocalTaskRecordStore(Path(store_dir))
            result = execute_task_with_record(
                request,
                adapters={TEST_ADAPTER_KEY: adapter},
                task_id_factory=lambda: "task-observability-retry-success-record",
                task_record_store=store,
            )
            loaded = store.load("task-observability-retry-success-record")

        self.assertEqual(result.envelope["status"], "success")
        self.assertNotIn("runtime_structured_log_events", result.envelope)
        payload = task_record_to_dict(loaded)
        self.assertNotIn("runtime_structured_log_events", payload["result"]["envelope"])
        self.assertNotIn("_runtime_structured_log_events", result.envelope)
        self.assertNotIn("_runtime_execution_metric_samples", result.envelope)
        self.assertNotIn("_runtime_structured_log_events", payload["result"]["envelope"])
        self.assertNotIn("_runtime_execution_metric_samples", payload["result"]["envelope"])
        self.assertIn(
            "retry_scheduled",
            {event["event_type"] for event in payload["runtime_structured_log_events"]},
        )
        self.assertIn(
            "retry_scheduled_total",
            {metric["metric_name"] for metric in payload["runtime_execution_metric_samples"]},
        )
        self.assertEqual(
            {signal["signal_id"] for signal in payload["runtime_failure_signals"]},
            {event["failure_signal_id"] for event in payload["runtime_structured_log_events"] if event["event_type"] == "retry_scheduled"},
        )
        self.assertIn(
            "task_succeeded",
            {event["event_type"] for event in payload["runtime_structured_log_events"]},
        )
        self.assertIn(
            "attempt_started",
            {event["event_type"] for event in payload["runtime_structured_log_events"]},
        )
        self.assertIn(
            "attempt_finished",
            {event["event_type"] for event in payload["runtime_structured_log_events"]},
        )
        self.assertIn(
            "task_succeeded_total",
            {metric["metric_name"] for metric in payload["runtime_execution_metric_samples"]},
        )

    def test_persistence_failures_project_persistence_phase(self) -> None:
        result = execute_task_with_record(
            make_request(),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-observability-persistence",
            task_record_store=AcceptedFailingStore(),
        )

        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["code"], "task_record_persistence_failed")
        self.assertEqual(result.envelope["runtime_failure_signal"]["failure_phase"], "persistence")

    def test_failed_terminal_persistence_preserves_business_failure(self) -> None:
        class CompletionFailingStore(LocalTaskRecordStore):
            def write(self, record):
                if record.status == "failed":
                    raise OSError("boom-completion")
                return super().write(record)

        with tempfile.TemporaryDirectory() as store_dir:
            result = execute_task_with_record(
                make_request(),
                adapters={TEST_ADAPTER_KEY: PlatformFailureAdapter()},
                task_id_factory=lambda: "task-observability-failed-persist",
                task_record_store=CompletionFailingStore(Path(store_dir)),
            )

        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["category"], "platform")
        self.assertEqual(result.envelope["error"]["code"], "content_not_found")
        self.assertIn(
            "observability_write_failed",
            {event["event_type"] for event in result.envelope["runtime_structured_log_events"]},
        )
        write_failure_events = [
            event
            for event in result.envelope["runtime_structured_log_events"]
            if event["event_type"] == "observability_write_failed"
        ]
        self.assertEqual(write_failure_events[0]["failure_signal_id"], result.envelope["runtime_failure_signal"]["signal_id"])
        self.assertEqual(write_failure_events[0]["resource_trace_refs"], result.envelope["runtime_failure_signal"]["resource_trace_refs"])
        self.assertNotIn(
            "observability_write_failed_total",
            {metric["metric_name"] for metric in result.envelope["runtime_execution_metric_samples"]},
        )

    def test_task_record_persists_observability_carriers(self) -> None:
        with tempfile.TemporaryDirectory() as store_dir:
            store = LocalTaskRecordStore(Path(store_dir))
            result = execute_task_with_record(
                make_request(),
                adapters={TEST_ADAPTER_KEY: PlatformFailureAdapter()},
                task_id_factory=lambda: "task-observability-record",
                task_record_store=store,
            )
            loaded = store.load("task-observability-record")

        payload = task_record_to_dict(loaded)
        signal = result.envelope["runtime_failure_signal"]
        self.assertEqual(payload["runtime_failure_signals"], [signal])
        for event in result.envelope["runtime_structured_log_events"]:
            self.assertIn(event, payload["runtime_structured_log_events"])
        for metric in result.envelope["runtime_execution_metric_samples"]:
            self.assertIn(metric, payload["runtime_execution_metric_samples"])
        self.assertIn("task_accepted", {event["event_type"] for event in payload["runtime_structured_log_events"]})
        self.assertIn("task_running", {event["event_type"] for event in payload["runtime_structured_log_events"]})
        self.assertIn("task_started_total", {metric["metric_name"] for metric in payload["runtime_execution_metric_samples"]})
        self.assertIn("attempt_started_total", {metric["metric_name"] for metric in payload["runtime_execution_metric_samples"]})
        self.assertIn("execution_duration_ms", {metric["metric_name"] for metric in payload["runtime_execution_metric_samples"]})
        self.assertEqual(payload["result"]["envelope"]["runtime_failure_signal"], signal)

    def test_repeated_identical_retry_failures_have_distinct_signals_before_success(self) -> None:
        adapter = TwiceRetryableThenSuccessAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/retry-twice-success-record"),
            execution_control_policy=ExecutionControlPolicy(
                timeout=ExecutionTimeoutPolicy(timeout_ms=30000),
                retry=ExecutionRetryPolicy(max_attempts=3, backoff_ms=0),
                concurrency=ExecutionConcurrencyPolicy(scope="global", max_in_flight=1, on_limit="reject"),
            ),
        )

        with tempfile.TemporaryDirectory() as store_dir:
            store = LocalTaskRecordStore(Path(store_dir))
            result = execute_task_with_record(
                request,
                adapters={TEST_ADAPTER_KEY: adapter},
                task_id_factory=lambda: "task-observability-retry-twice-success-record",
                task_record_store=store,
            )
            payload = task_record_to_dict(store.load("task-observability-retry-twice-success-record"))

        self.assertEqual(result.envelope["status"], "success")
        self.assertEqual(adapter.calls, 3)
        signal_ids = [signal["signal_id"] for signal in payload["runtime_failure_signals"]]
        envelope_refs = [signal["envelope_ref"] for signal in payload["runtime_failure_signals"]]
        self.assertEqual(len(signal_ids), 2)
        self.assertEqual(len(set(signal_ids)), 2)
        self.assertEqual(len(set(envelope_refs)), 2)
        self.assertEqual(
            {event["failure_signal_id"] for event in payload["runtime_structured_log_events"] if event["event_type"] == "retry_scheduled"},
            set(signal_ids),
        )
        retry_scheduled_events = [
            event
            for event in payload["runtime_structured_log_events"]
            if event["event_type"] == "retry_scheduled"
        ]
        self.assertEqual(len(retry_scheduled_events), 2)
        for event, direct_attempt_index in zip(retry_scheduled_events, (1, 2), strict=True):
            self.assertEqual(
                [ref.get("attempt_index") for ref in event["runtime_result_refs"]],
                [direct_attempt_index],
            )
            self.assertEqual(
                [ref.get("ref_type") for ref in event["runtime_result_refs"]],
                ["ExecutionAttemptOutcome"],
            )


if __name__ == "__main__":
    unittest.main()
