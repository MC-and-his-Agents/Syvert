from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from syvert.cli import main
from syvert.http_api import TaskHttpService
from syvert.runtime import (
    PlatformAdapterError,
    TaskExecutionResult,
    failure_envelope,
    invalid_input_error,
)
from syvert.task_record import (
    TaskRequestSnapshot,
    create_task_record,
    finish_task_record,
    start_task_record,
    task_record_to_dict,
)
from syvert.task_record_store import LocalTaskRecordStore
from tests.runtime.resource_fixtures import ResourceStoreEnvMixin, baseline_resource_requirement_declarations


TEST_ADAPTER_KEY = "xhs"
TEST_CAPABILITY = "content_detail_by_url"


class DeterministicSuccessAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(adapter_key=TEST_ADAPTER_KEY)

    def execute(self, request):
        url = request.input.url
        return {
            "raw": {"id": "raw-same-path", "url": url},
            "normalized": {
                "platform": TEST_ADAPTER_KEY,
                "content_id": "content-same-path",
                "content_type": "unknown",
                "canonical_url": url,
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


class DeterministicFailureAdapter(DeterministicSuccessAdapter):
    def execute(self, request):
        del request
        raise PlatformAdapterError(
            code="platform_broken",
            message="boom",
            details={"reason": "same-path", "retryable": False},
        )


def normalize_record_payload(payload: dict[str, object]) -> dict[str, object]:
    normalized = json.loads(json.dumps(payload))
    normalized["task_id"] = "normalized-task-id"
    if isinstance(normalized.get("task_record_ref"), str):
        normalized["task_record_ref"] = "normalized-task-record-ref"
    result = normalized.get("result")
    if isinstance(result, dict):
        envelope = result.get("envelope")
        normalize_envelope_identity(envelope)
    for field in ("created_at", "updated_at", "terminal_at"):
        if isinstance(normalized.get(field), str):
            normalized[field] = f"normalized-{field}"
    logs = normalized.get("logs")
    if isinstance(logs, list):
        for index, entry in enumerate(logs, start=1):
            if isinstance(entry, dict) and isinstance(entry.get("occurred_at"), str):
                entry["occurred_at"] = f"normalized-log-{index}-occurred-at"
    return normalized


def normalize_envelope_identity(envelope: object) -> None:
    if not isinstance(envelope, dict):
        return
    if isinstance(envelope.get("task_id"), str):
        envelope["task_id"] = "normalized-task-id"
    if isinstance(envelope.get("task_record_ref"), str):
        envelope["task_record_ref"] = "normalized-task-record-ref"


def make_request_snapshot(url: str = "https://example.com/posts/same-path") -> TaskRequestSnapshot:
    return TaskRequestSnapshot(
        adapter_key=TEST_ADAPTER_KEY,
        capability=TEST_CAPABILITY,
        target_type="url",
        target_value=url,
        collection_mode="hybrid",
    )


def make_success_envelope(task_id: str, url: str = "https://example.com/posts/same-path") -> dict[str, object]:
    return {
        "task_id": task_id,
        "adapter_key": TEST_ADAPTER_KEY,
        "capability": TEST_CAPABILITY,
        "status": "success",
        "task_record_ref": f"task_record:{task_id}",
        "raw": {"id": "raw-same-path", "url": url},
        "normalized": {
            "platform": TEST_ADAPTER_KEY,
            "content_id": "content-same-path",
            "content_type": "unknown",
            "canonical_url": url,
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


def make_failed_envelope(
    task_id: str,
    *,
    category: str = "platform",
    code: str = "platform_broken",
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "task_id": task_id,
        "adapter_key": TEST_ADAPTER_KEY,
        "capability": TEST_CAPABILITY,
        "status": "failed",
        "task_record_ref": f"task_record:{task_id}",
        "error": {
            "category": category,
            "code": code,
            "message": "boom",
            "details": details or {"reason": "same-path"},
        },
    }


class CliHttpSamePathTests(ResourceStoreEnvMixin, unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self._task_record_store_dir = tempfile.TemporaryDirectory()
        self._task_record_store_patcher = mock.patch.dict(
            os.environ,
            {"SYVERT_TASK_RECORD_STORE_DIR": self._task_record_store_dir.name},
            clear=False,
        )
        self._task_record_store_patcher.start()
        self.store = LocalTaskRecordStore(Path(self._task_record_store_dir.name))

    def tearDown(self) -> None:
        self._task_record_store_patcher.stop()
        self._task_record_store_dir.cleanup()
        super().tearDown()

    def run_cli_task(
        self,
        *,
        task_id: str,
        url: str,
        capability: str = TEST_CAPABILITY,
        adapter: object | None = None,
    ) -> tuple[int, dict[str, object], str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        exit_code = main(
            [
                "run",
                "--adapter",
                TEST_ADAPTER_KEY,
                "--capability",
                capability,
                "--url",
                url,
            ],
            adapters={TEST_ADAPTER_KEY: adapter or DeterministicSuccessAdapter()},
            stdout=stdout,
            stderr=stderr,
            task_id_factory=lambda: task_id,
        )
        stream_payload = stdout.getvalue() or stderr.getvalue()
        return exit_code, json.loads(stream_payload), "stdout" if stdout.getvalue() else "stderr"

    def query_cli_task(self, task_id: str) -> tuple[int, dict[str, object], str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        exit_code = main(
            ["query", "--task-id", task_id],
            stdout=stdout,
            stderr=stderr,
        )
        stream_payload = stdout.getvalue() or stderr.getvalue()
        return exit_code, json.loads(stream_payload), "stdout" if stdout.getvalue() else "stderr"

    def make_http_service(self, *, task_id: str = "task-http-same-path", adapter: object | None = None) -> TaskHttpService:
        return TaskHttpService(
            {TEST_ADAPTER_KEY: adapter or DeterministicSuccessAdapter()},
            task_record_store=self.store,
            task_id_factory=lambda: task_id,
        )

    def submit_http_task(
        self,
        *,
        task_id: str,
        url: str,
        capability: str = TEST_CAPABILITY,
        adapter: object | None = None,
    ):
        return self.make_http_service(task_id=task_id, adapter=adapter).submit(
            {
                "adapter_key": TEST_ADAPTER_KEY,
                "capability": capability,
                "target": {"url": url},
            }
        )

    def write_record_lifecycle(self, record) -> None:
        accepted = create_task_record(record.task_id, record.request, occurred_at=record.created_at)
        self.store.write(accepted)
        if record.status in {"running", "succeeded", "failed"}:
            running = start_task_record(
                accepted,
                occurred_at=record.updated_at if record.status == "running" else "2026-04-24T00:00:01Z",
            )
            self.store.write(running)
        if record.status in {"succeeded", "failed"}:
            assert record.result is not None
            assert record.terminal_at is not None
            self.store.write(finish_task_record(running, record.result.envelope, occurred_at=record.terminal_at))

    def task_record_files(self) -> list[Path]:
        if not self.store.root.exists():
            return []
        return sorted(self.store.root.glob("*.json"))

    def test_same_path_success_shared_truth(self) -> None:
        url = "https://example.com/posts/same-path-success"

        cli_exit_code, cli_envelope, cli_stream = self.run_cli_task(task_id="task-cli-same-success", url=url)
        http_response = self.submit_http_task(task_id="task-http-same-success", url=url)

        self.assertEqual(cli_exit_code, 0)
        self.assertEqual(cli_stream, "stdout")
        self.assertEqual(cli_envelope["status"], "success")
        self.assertEqual(http_response.status_code, 202)
        cli_record = task_record_to_dict(self.store.load("task-cli-same-success"))
        http_record = task_record_to_dict(self.store.load("task-http-same-success"))

        self.assertEqual(normalize_record_payload(cli_record), normalize_record_payload(http_record))
        self.assertEqual(cli_record["status"], "succeeded")
        self.assertEqual(http_record["status"], "succeeded")
        self.assertEqual(cli_record["request"], http_record["request"])

    def test_cli_created_task_can_be_read_by_http_status_and_result(self) -> None:
        url = "https://example.com/posts/cli-created"
        exit_code, _, _ = self.run_cli_task(task_id="task-cli-created-http-read", url=url)
        self.assertEqual(exit_code, 0)

        query_exit_code, query_payload, query_stream = self.query_cli_task("task-cli-created-http-read")
        status_response = self.make_http_service().status("task-cli-created-http-read")
        result_response = self.make_http_service().result("task-cli-created-http-read")

        self.assertEqual(query_exit_code, 0)
        self.assertEqual(query_stream, "stdout")
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.body, query_payload)
        self.assertEqual(result_response.status_code, 200)
        self.assertEqual(result_response.body, query_payload["result"]["envelope"])

    def test_http_created_task_can_be_read_by_cli_query(self) -> None:
        url = "https://example.com/posts/http-created"
        submit_response = self.submit_http_task(task_id="task-http-created-cli-read", url=url)
        self.assertEqual(submit_response.status_code, 202)

        query_exit_code, query_payload, query_stream = self.query_cli_task("task-http-created-cli-read")
        status_response = self.make_http_service().status("task-http-created-cli-read")

        self.assertEqual(query_exit_code, 0)
        self.assertEqual(query_stream, "stdout")
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(query_payload, status_response.body)

    def test_same_path_terminal_failed_envelope_is_not_rewrapped(self) -> None:
        submit_response = self.submit_http_task(
            task_id="task-http-failed-cli-read",
            url="https://example.com/posts/http-failed",
            adapter=DeterministicFailureAdapter(),
        )
        self.assertEqual(submit_response.status_code, 202)

        query_exit_code, query_payload, query_stream = self.query_cli_task("task-http-failed-cli-read")
        result_response = self.make_http_service().result("task-http-failed-cli-read")

        self.assertEqual(query_exit_code, 0)
        self.assertEqual(query_stream, "stdout")
        self.assertEqual(query_payload["status"], "failed")
        self.assertEqual(result_response.status_code, 200)
        self.assertEqual(result_response.body, query_payload["result"]["envelope"])
        self.assertEqual(result_response.body["error"]["category"], "platform")
        self.assertEqual(result_response.body["error"]["code"], "platform_broken")
        self.assertEqual(result_response.body["error"]["details"]["reason"], "same-path")
        self.assertFalse(result_response.body["error"]["details"]["retryable"])
        self.assertTrue(result_response.body["error"]["details"]["resource_trace_refs"])

    def test_same_path_pre_admission_invalid_input_does_not_create_task_record(self) -> None:
        url = "https://example.com/posts/invalid-capability"

        cli_exit_code, cli_payload, cli_stream = self.run_cli_task(
            task_id="task-cli-invalid-capability",
            url=url,
            capability="content_detail",
        )
        http_response = self.submit_http_task(
            task_id="task-http-invalid-capability",
            url=url,
            capability="content_detail",
        )

        self.assertEqual(cli_exit_code, 1)
        self.assertEqual(cli_stream, "stderr")
        self.assertEqual(cli_payload["status"], "failed")
        self.assertEqual(http_response.status_code, 400)
        self.assertEqual(http_response.body["status"], "failed")
        self.assertEqual(cli_payload["error"]["category"], "invalid_input")
        self.assertEqual(http_response.body["error"]["category"], "invalid_input")
        self.assertEqual(cli_payload["error"]["code"], "invalid_capability")
        self.assertEqual(http_response.body["error"]["code"], "invalid_capability")
        self.assertEqual(self.task_record_files(), [])

    def test_same_path_pre_accepted_concurrency_rejection_uses_shared_failed_envelope(self) -> None:
        def reject_before_accepted(request, *, task_id_factory=None, **kwargs):
            del kwargs
            task_id = task_id_factory() if task_id_factory is not None else "task-concurrency-rejected"
            return TaskExecutionResult(
                failure_envelope(
                    task_id,
                    request.adapter_key,
                    request.capability,
                    invalid_input_error(
                        "concurrency_limit_exceeded",
                        "concurrency limit exceeded",
                        details={"scope": "global", "max_in_flight": 1, "on_limit": "reject"},
                    ),
                ),
                None,
            )

        with mock.patch("syvert.cli.execute_task_with_record", side_effect=reject_before_accepted):
            cli_exit_code, cli_payload, cli_stream = self.run_cli_task(
                task_id="task-cli-concurrency-rejected",
                url="https://example.com/posts/concurrency-rejected",
            )
        with mock.patch("syvert.http_api.execute_task_with_record", side_effect=reject_before_accepted):
            http_response = self.submit_http_task(
                task_id="task-http-concurrency-rejected",
                url="https://example.com/posts/concurrency-rejected",
            )

        self.assertEqual(cli_exit_code, 1)
        self.assertEqual(cli_stream, "stderr")
        self.assertEqual(http_response.status_code, 409)
        self.assertEqual(cli_payload["status"], "failed")
        self.assertEqual(http_response.body["status"], "failed")
        self.assertEqual(cli_payload["error"]["category"], "invalid_input")
        self.assertEqual(http_response.body["error"]["category"], "invalid_input")
        self.assertEqual(cli_payload["error"]["code"], "concurrency_limit_exceeded")
        self.assertEqual(http_response.body["error"]["code"], "concurrency_limit_exceeded")
        self.assertEqual(cli_payload["error"]["details"], http_response.body["error"]["details"])
        self.assertEqual(self.task_record_files(), [])

    def test_same_path_durable_record_unavailable_fails_closed(self) -> None:
        exit_code, _, _ = self.run_cli_task(
            task_id="task-unavailable-shared",
            url="https://example.com/posts/unavailable",
        )
        self.assertEqual(exit_code, 0)
        self.store.mark_invalid(
            "task-unavailable-shared",
            stage="completion",
            reason="forced-same-path-invalid-marker",
        )

        query_exit_code, query_payload, query_stream = self.query_cli_task("task-unavailable-shared")
        status_response = self.make_http_service().status("task-unavailable-shared")
        result_response = self.make_http_service().result("task-unavailable-shared")

        self.assertEqual(query_exit_code, 1)
        self.assertEqual(query_stream, "stderr")
        self.assertEqual(status_response.status_code, 500)
        self.assertEqual(result_response.status_code, 500)
        self.assertEqual(query_payload["error"]["category"], "runtime_contract")
        self.assertEqual(status_response.body["error"]["category"], "runtime_contract")
        self.assertEqual(result_response.body["error"]["category"], "runtime_contract")
        self.assertEqual(query_payload["error"]["code"], "task_record_unavailable")
        self.assertEqual(status_response.body["error"]["code"], "task_record_unavailable")
        self.assertEqual(result_response.body["error"]["code"], "task_record_unavailable")

    def test_execution_timeout_terminal_truth_is_shared_by_cli_query_and_http_result(self) -> None:
        task_id = "task-execution-timeout-shared"
        accepted = create_task_record(
            task_id,
            make_request_snapshot("https://example.com/posts/execution-timeout"),
            occurred_at="2026-04-24T00:00:00Z",
        )
        running = start_task_record(accepted, occurred_at="2026-04-24T00:00:01Z")
        terminal = finish_task_record(
            running,
            make_failed_envelope(
                task_id,
                code="execution_timeout",
                details={"control_code": "execution_timeout", "retryable": True},
            ),
            occurred_at="2026-04-24T00:00:02Z",
        )
        self.write_record_lifecycle(terminal)

        query_exit_code, query_payload, query_stream = self.query_cli_task(task_id)
        result_response = self.make_http_service().result(task_id)

        self.assertEqual(query_exit_code, 0)
        self.assertEqual(query_stream, "stdout")
        self.assertEqual(result_response.status_code, 200)
        self.assertEqual(result_response.body, query_payload["result"]["envelope"])
        self.assertEqual(result_response.body["error"]["category"], "platform")
        self.assertEqual(result_response.body["error"]["code"], "execution_timeout")
        self.assertEqual(result_response.body["error"]["details"]["control_code"], "execution_timeout")

    def test_closeout_control_state_failure_terminal_truth_is_shared(self) -> None:
        task_id = "task-closeout-control-state-shared"
        accepted = create_task_record(
            task_id,
            make_request_snapshot("https://example.com/posts/closeout-control-state"),
            occurred_at="2026-04-24T00:00:00Z",
        )
        running = start_task_record(accepted, occurred_at="2026-04-24T00:00:01Z")
        terminal = finish_task_record(
            running,
            make_failed_envelope(
                task_id,
                category="runtime_contract",
                code="closeout_control_state_failed",
                details={"control_code": "retry_slot_release_failed"},
            ),
            occurred_at="2026-04-24T00:00:02Z",
        )
        self.write_record_lifecycle(terminal)

        query_exit_code, query_payload, query_stream = self.query_cli_task(task_id)
        status_response = self.make_http_service().status(task_id)
        result_response = self.make_http_service().result(task_id)

        self.assertEqual(query_exit_code, 0)
        self.assertEqual(query_stream, "stdout")
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.body, query_payload)
        self.assertEqual(result_response.status_code, 200)
        self.assertEqual(result_response.body, query_payload["result"]["envelope"])
        self.assertEqual(result_response.body["error"]["category"], "runtime_contract")
        self.assertEqual(result_response.body["error"]["code"], "closeout_control_state_failed")

    def test_same_path_nonterminal_status_and_result_boundary(self) -> None:
        accepted = create_task_record(
            "task-nonterminal-accepted",
            make_request_snapshot("https://example.com/posts/accepted"),
            occurred_at="2026-04-24T00:00:00Z",
        )
        running = start_task_record(
            create_task_record(
                "task-nonterminal-running",
                make_request_snapshot("https://example.com/posts/running"),
                occurred_at="2026-04-24T00:00:00Z",
            ),
            occurred_at="2026-04-24T00:00:01Z",
        )
        self.store.write(accepted)
        self.write_record_lifecycle(running)

        for task_id, expected_record in (
            ("task-nonterminal-accepted", accepted),
            ("task-nonterminal-running", running),
        ):
            with self.subTest(task_id=task_id):
                query_exit_code, query_payload, query_stream = self.query_cli_task(task_id)
                status_response = self.make_http_service().status(task_id)
                result_response = self.make_http_service().result(task_id)

                self.assertEqual(query_exit_code, 0)
                self.assertEqual(query_stream, "stdout")
                self.assertEqual(query_payload, task_record_to_dict(expected_record))
                self.assertEqual(status_response.status_code, 200)
                self.assertEqual(status_response.body, query_payload)
                self.assertEqual(result_response.status_code, 409)
                self.assertEqual(result_response.body["status"], "failed")
                self.assertEqual(result_response.body["error"]["category"], "invalid_input")
                self.assertEqual(result_response.body["error"]["code"], "result_not_ready")

    def test_runtime_result_refs_are_preserved_across_cli_query_and_http_result(self) -> None:
        task_id = "task-observability-same-path"
        accepted = create_task_record(
            task_id,
            make_request_snapshot("https://example.com/posts/observability"),
            occurred_at="2026-04-24T00:00:00Z",
        )
        running = start_task_record(accepted, occurred_at="2026-04-24T00:00:01Z")
        envelope = make_success_envelope(task_id, "https://example.com/posts/observability")
        envelope["runtime_result_refs"] = [{"ref_type": "ExecutionAttemptOutcome", "ref_id": "attempt-same-path-1"}]
        envelope["execution_control_events"] = [
            {
                "event_type": "retry_concurrency_rejected",
                "control_code": "concurrency_limit_exceeded",
            }
        ]
        terminal = finish_task_record(running, envelope, occurred_at="2026-04-24T00:00:02Z")
        self.write_record_lifecycle(terminal)

        query_exit_code, query_payload, query_stream = self.query_cli_task(task_id)
        result_response = self.make_http_service().result(task_id)

        self.assertEqual(query_exit_code, 0)
        self.assertEqual(query_stream, "stdout")
        self.assertEqual(result_response.status_code, 200)
        self.assertEqual(query_payload["task_record_ref"], f"task_record:{task_id}")
        self.assertEqual(query_payload["runtime_result_refs"], envelope["runtime_result_refs"])
        self.assertEqual(query_payload["execution_control_events"], envelope["execution_control_events"])
        self.assertEqual(result_response.body["task_record_ref"], f"task_record:{task_id}")
        self.assertEqual(result_response.body["runtime_result_refs"], envelope["runtime_result_refs"])
        self.assertEqual(result_response.body["execution_control_events"], envelope["execution_control_events"])
        self.assertEqual(result_response.body, query_payload["result"]["envelope"])

    def test_post_accepted_retry_reacquire_rejection_does_not_rewrite_terminal_failure(self) -> None:
        task_id = "task-retry-reacquire-rejection"
        accepted = create_task_record(
            task_id,
            make_request_snapshot("https://example.com/posts/retry-reacquire"),
            occurred_at="2026-04-24T00:00:00Z",
        )
        running = start_task_record(accepted, occurred_at="2026-04-24T00:00:01Z")
        envelope = make_failed_envelope(
            task_id,
            code="platform_broken",
            details={"reason": "transient-platform", "retryable": True},
        )
        envelope["runtime_result_refs"] = [{"ref_type": "ExecutionAttemptOutcome", "ref_id": "attempt-before-reacquire"}]
        envelope["execution_control_events"] = [
            {
                "event_type": "retry_concurrency_rejected",
                "control_code": "concurrency_limit_exceeded",
                "details": {"scope": "global", "max_in_flight": 1, "on_limit": "reject"},
            }
        ]
        terminal = finish_task_record(running, envelope, occurred_at="2026-04-24T00:00:02Z")
        self.write_record_lifecycle(terminal)

        query_exit_code, query_payload, query_stream = self.query_cli_task(task_id)
        result_response = self.make_http_service().result(task_id)

        self.assertEqual(query_exit_code, 0)
        self.assertEqual(query_stream, "stdout")
        self.assertEqual(result_response.status_code, 200)
        self.assertEqual(result_response.body, query_payload["result"]["envelope"])
        self.assertEqual(result_response.body["error"]["category"], "platform")
        self.assertEqual(result_response.body["error"]["code"], "platform_broken")
        self.assertEqual(result_response.body["runtime_result_refs"], envelope["runtime_result_refs"])
        self.assertEqual(result_response.body["execution_control_events"], envelope["execution_control_events"])


if __name__ == "__main__":
    unittest.main()
