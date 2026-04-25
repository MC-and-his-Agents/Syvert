from __future__ import annotations

import unittest
import tempfile
from pathlib import Path

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
    release_execution_concurrency_slot,
)
from syvert.task_record import task_record_to_dict
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


class RuntimeObservabilityTests(ResourceStoreEnvMixin, unittest.TestCase):
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

        log_event = envelope["runtime_structured_log_events"][0]
        self.assertEqual(log_event["event_type"], "task_failed")
        self.assertEqual(log_event["level"], "error")
        self.assertEqual(log_event["failure_signal_id"], signal["signal_id"])

        metric = envelope["runtime_execution_metric_samples"][0]
        self.assertEqual(metric["metric_name"], "task_failed_total")
        self.assertEqual(metric["metric_value"], 1)
        self.assertEqual(metric["error_category"], signal["error_category"])
        self.assertEqual(metric["error_code"], signal["error_code"])

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
        self.assertEqual(
            envelope["runtime_structured_log_events"][0]["event_type"],
            "admission_concurrency_rejected",
        )
        self.assertEqual(
            envelope["runtime_execution_metric_samples"][0]["metric_name"],
            "admission_concurrency_rejected_total",
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
        self.assertEqual(payload["runtime_structured_log_events"], result.envelope["runtime_structured_log_events"])
        self.assertEqual(payload["runtime_execution_metric_samples"], result.envelope["runtime_execution_metric_samples"])
        self.assertEqual(payload["result"]["envelope"]["runtime_failure_signal"], signal)


if __name__ == "__main__":
    unittest.main()
