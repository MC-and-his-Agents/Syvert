from __future__ import annotations

import io
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any

from syvert.http_api import HttpResponse, TaskHttpService, build_wsgi_app
from syvert.runtime import PlatformAdapterError
from syvert.task_record import (
    TaskRecord,
    TaskRecordContractError,
    TaskRequestSnapshot,
    TaskTerminalResult,
    create_task_record,
    finish_task_record,
    start_task_record,
    task_record_to_dict,
)
from syvert.task_record_store import LocalTaskRecordStore
from tests.runtime.resource_fixtures import ResourceStoreEnvMixin, baseline_resource_requirement_declarations


TEST_ADAPTER_KEY = "xhs"


class SuccessfulAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(adapter_key=TEST_ADAPTER_KEY)

    def execute(self, request):
        url = request.input.url
        return {
            "raw": {"id": "raw-http-1", "url": url},
            "normalized": {
                "platform": TEST_ADAPTER_KEY,
                "content_id": "content-http-1",
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


class PlatformFailureAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(adapter_key=TEST_ADAPTER_KEY)

    def execute(self, request):
        raise PlatformAdapterError(
            code="platform_broken",
            message="boom",
            details={"reason": "bad"},
        )


class PolicyRecordingAdapter(SuccessfulAdapter):
    def __init__(self) -> None:
        self.execution_control_policy = None

    def execute(self, request):
        self.execution_control_policy = request.execution_control_policy
        return super().execute(request)


def make_request_snapshot() -> TaskRequestSnapshot:
    return TaskRequestSnapshot(
        adapter_key=TEST_ADAPTER_KEY,
        capability="content_detail_by_url",
        target_type="url",
        target_value="https://example.com/posts/1",
        collection_mode="hybrid",
    )


def make_success_envelope(task_id: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "adapter_key": TEST_ADAPTER_KEY,
        "capability": "content_detail_by_url",
        "status": "success",
        "task_record_ref": f"task_record:{task_id}",
        "raw": {"id": "raw-http-record-1"},
        "normalized": {
            "platform": TEST_ADAPTER_KEY,
            "content_id": "content-http-record-1",
            "content_type": "unknown",
            "canonical_url": "https://example.com/posts/1",
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


def make_failed_envelope(task_id: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "adapter_key": TEST_ADAPTER_KEY,
        "capability": "content_detail_by_url",
        "status": "failed",
        "task_record_ref": f"task_record:{task_id}",
        "error": {
            "category": "platform",
            "code": "platform_broken",
            "message": "boom",
            "details": {"retryable": False},
        },
    }


def make_creator_profile_envelope(task_id: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "adapter_key": TEST_ADAPTER_KEY,
        "capability": "creator_profile_by_id",
        "status": "success",
        "task_record_ref": f"task_record:{task_id}",
        "operation": "creator_profile_by_id",
        "target": {
            "operation": "creator_profile_by_id",
            "target_type": "creator",
            "creator_ref": "creator-001",
            "target_display_hint": "creator-hint-001",
            "policy_ref": "policy:creator-profile",
        },
        "result_status": "complete",
        "error_classification": None,
        "profile": {
            "creator_ref": "creator-001",
            "canonical_ref": "creator:canonical:creator-001",
            "display_name": "creator-name",
            "avatar_ref": "avatar:creator-001",
            "description": "desc",
            "public_counts": {
                "follower_count": 100,
                "following_count": 5,
                "content_count": 8,
                "like_count": 16,
            },
            "profile_url_hint": "profile:creator-slug",
        },
        "raw_payload_ref": "raw://creator-profile",
        "source_trace": {
            "adapter_key": TEST_ADAPTER_KEY,
            "provider_path": "provider://sanitized",
            "resource_profile_ref": "fr-0405:profile:creator-profile-by-id:account-proxy",
            "fetched_at": "2026-05-09T10:00:00Z",
            "evidence_alias": "alias://creator-profile-success",
        },
        "audit": {},
    }


def make_media_asset_fetch_envelope(task_id: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "adapter_key": TEST_ADAPTER_KEY,
        "capability": "media_asset_fetch_by_ref",
        "status": "success",
        "task_record_ref": f"task_record:{task_id}",
        "operation": "media_asset_fetch_by_ref",
        "target": {
            "operation": "media_asset_fetch_by_ref",
            "target_type": "media_ref",
            "media_ref": "media:asset-001",
            "origin_ref": "origin:content-001",
            "policy_ref": "policy:media-metadata",
        },
        "content_type": "image",
        "fetch_policy": {
            "fetch_mode": "metadata_only",
            "allowed_content_types": ["image", "video"],
            "allow_download": False,
            "max_bytes": None,
        },
        "fetch_outcome": "metadata_only",
        "result_status": "complete",
        "error_classification": None,
        "raw_payload_ref": "raw://media-asset-fetch/asset-001",
        "media": {
            "source_media_ref": "source:media:asset-001",
            "source_ref_lineage": {
                "input_ref": "media:asset-001",
                "source_media_ref": "source:media:asset-001",
                "resolved_ref": "resolved:media:asset-001",
                "canonical_ref": "canonical:media:asset-001",
                "preservation_status": "preserved",
            },
            "canonical_ref": "canonical:media:asset-001",
            "content_type": "image",
            "metadata": {"mime_type": "image/jpeg", "width": 1200, "height": 900},
        },
        "source_trace": {
            "adapter_key": TEST_ADAPTER_KEY,
            "provider_path": "provider://sanitized",
            "resource_profile_ref": "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
            "fetched_at": "2026-05-09T10:00:00Z",
            "evidence_alias": "alias://media-asset-fetch-1",
        },
        "audit": {},
    }


def invoke_wsgi_app(
    app: Any,
    *,
    method: str,
    path: str,
    body: bytes = b"",
    query_string: str = "",
) -> tuple[str, list[tuple[str, str]], bytes]:
    captured: dict[str, Any] = {}
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_TYPE": "application/json",
        "CONTENT_LENGTH": str(len(body)),
        "QUERY_STRING": query_string,
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8000",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": "http",
        "wsgi.input": io.BytesIO(body),
        "wsgi.errors": io.StringIO(),
        "wsgi.multithread": False,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
    }

    def start_response(status: str, headers: list[tuple[str, str]], exc_info: Any = None) -> None:
        del exc_info
        captured["status"] = status
        captured["headers"] = headers

    chunks = app(environ, start_response)
    payload = b"".join(chunks)
    close = getattr(chunks, "close", None)
    if callable(close):
        close()
    return captured["status"], captured["headers"], payload


class RecordingService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def submit(self, payload: dict[str, Any]) -> HttpResponse:
        self.calls.append(("submit", payload))
        return HttpResponse(202, {"task_id": "task-wsgi", "status": "accepted"})

    def status(self, task_id: str) -> HttpResponse:
        self.calls.append(("status", task_id))
        return HttpResponse(200, {"task_id": task_id, "status": "running"})

    def result(self, task_id: str) -> HttpResponse:
        self.calls.append(("result", task_id))
        return HttpResponse(200, {"task_id": task_id, "status": "failed"})


class BrokenInputStream:
    def read(self, size: int) -> bytes:
        del size
        raise OSError("boom")


class StaticRecordStore:
    def __init__(self, record: TaskRecord) -> None:
        self.record = record

    def write(self, record: TaskRecord) -> TaskRecord:
        self.record = record
        return record

    def load(self, task_id: str) -> TaskRecord:
        del task_id
        return self.record

    def mark_invalid(self, task_id: str, *, stage: str, reason: str) -> None:
        del task_id, stage, reason


class NonRecordStore:
    def write(self, record: TaskRecord) -> TaskRecord:
        return record

    def load(self, task_id: str) -> dict[str, Any]:
        return {"task_id": task_id, "status": "accepted"}

    def mark_invalid(self, task_id: str, *, stage: str, reason: str) -> None:
        del task_id, stage, reason


class MismatchedTaskIdWriteStore:
    def __init__(self, record: TaskRecord) -> None:
        self.record = record

    def write(self, record: TaskRecord) -> TaskRecord:
        if record.status in {"succeeded", "failed"}:
            return self.record
        return record

    def load(self, task_id: str) -> TaskRecord:
        del task_id
        raise FileNotFoundError

    def mark_invalid(self, task_id: str, *, stage: str, reason: str) -> None:
        del task_id, stage, reason


class ContractErrorLoadStore(StaticRecordStore):
    def load(self, task_id: str) -> TaskRecord:
        del task_id
        raise TaskRecordContractError("contract-broken")


class RuntimeErrorLoadStore(StaticRecordStore):
    def load(self, task_id: str) -> TaskRecord:
        del task_id
        raise RuntimeError("boom-load")


class TaskHttpServiceTests(ResourceStoreEnvMixin, unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self._task_record_store_dir = tempfile.TemporaryDirectory()
        self.store = LocalTaskRecordStore(Path(self._task_record_store_dir.name))

    def tearDown(self) -> None:
        self._task_record_store_dir.cleanup()
        super().tearDown()

    def make_service(
        self,
        *,
        adapter: object | None = None,
        task_id: str = "task-http-001",
    ) -> TaskHttpService:
        return TaskHttpService(
            {TEST_ADAPTER_KEY: adapter or SuccessfulAdapter()},
            task_record_store=self.store,
            task_id_factory=lambda: task_id,
        )

    def write_record(self, record) -> None:
        accepted = create_task_record(record.task_id, record.request, occurred_at=record.created_at)
        self.store.write(accepted)
        if record.status in {"running", "succeeded", "failed"}:
            running = start_task_record(accepted, occurred_at=record.updated_at if record.status == "running" else "2026-04-24T00:00:01Z")
            self.store.write(running)
        if record.status in {"succeeded", "failed"}:
            assert record.result is not None
            assert record.terminal_at is not None
            self.store.write(finish_task_record(running, record.result.envelope, occurred_at=record.terminal_at))

    def write_raw_record_payload(self, task_id: str, payload: dict[str, Any]) -> None:
        self.store.root.mkdir(parents=True, exist_ok=True)
        self.store.record_path(task_id).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def make_accepted_record(self, task_id: str):
        return create_task_record(task_id, make_request_snapshot(), occurred_at="2026-04-24T00:00:00Z")

    def make_running_record(self, task_id: str):
        return start_task_record(self.make_accepted_record(task_id), occurred_at="2026-04-24T00:00:01Z")

    def make_succeeded_record(self, task_id: str):
        return finish_task_record(
            self.make_running_record(task_id),
            make_success_envelope(task_id),
            occurred_at="2026-04-24T00:00:02Z",
        )

    def make_failed_record(self, task_id: str):
        return finish_task_record(
            self.make_running_record(task_id),
            make_failed_envelope(task_id),
            occurred_at="2026-04-24T00:00:02Z",
        )

    def make_creator_profile_record(self, task_id: str):
        request = TaskRequestSnapshot(
            adapter_key=TEST_ADAPTER_KEY,
            capability="creator_profile_by_id",
            target_type="creator",
            target_value="creator-001",
            collection_mode="direct",
        )
        accepted = create_task_record(task_id, request, occurred_at="2026-04-24T00:00:00Z")
        running = start_task_record(accepted, occurred_at="2026-04-24T00:00:01Z")
        return finish_task_record(
            running,
            make_creator_profile_envelope(task_id),
            occurred_at="2026-04-24T00:00:02Z",
        )

    def make_media_asset_fetch_record(self, task_id: str):
        request = TaskRequestSnapshot(
            adapter_key=TEST_ADAPTER_KEY,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
            collection_mode="direct",
        )
        accepted = create_task_record(task_id, request, occurred_at="2026-04-24T00:00:00Z")
        running = start_task_record(accepted, occurred_at="2026-04-24T00:00:01Z")
        return finish_task_record(
            running,
            make_media_asset_fetch_envelope(task_id),
            occurred_at="2026-04-24T00:00:02Z",
        )

    def test_submit_happy_path_returns_receipt_and_persists_task_record(self) -> None:
        service = self.make_service(task_id="task-http-submit-1")

        response = service.submit(
            {
                "adapter_key": TEST_ADAPTER_KEY,
                "capability": "content_detail_by_url",
                "target": {"url": "https://example.com/posts/submit-1"},
            }
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.body["task_id"], "task-http-submit-1")
        self.assertEqual(response.body["status"], "succeeded")
        persisted = self.store.load("task-http-submit-1")
        self.assertEqual(persisted.status, "succeeded")
        self.assertEqual(persisted.result.envelope["raw"]["url"], "https://example.com/posts/submit-1")

    def test_status_returns_task_record_projection_from_shared_store(self) -> None:
        record = self.make_running_record("task-http-status-1")
        service = TaskHttpService(
            {TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_record_store=StaticRecordStore(record),
        )

        response = service.status("task-http-status-1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, task_record_to_dict(record))

    def test_status_returns_unavailable_when_store_returns_wrong_task_record(self) -> None:
        wrong_record = self.make_running_record("task-http-other-status-1")
        service = TaskHttpService(
            {TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_record_store=StaticRecordStore(wrong_record),
        )

        response = service.status("task-http-status-1")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.body["task_id"], "task-http-status-1")
        self.assertEqual(response.body["error"]["category"], "runtime_contract")
        self.assertEqual(response.body["error"]["code"], "task_record_unavailable")

    def test_result_returns_unavailable_when_store_returns_wrong_task_record(self) -> None:
        wrong_record = self.make_succeeded_record("task-http-other-result-1")
        service = TaskHttpService(
            {TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_record_store=StaticRecordStore(wrong_record),
        )

        response = service.result("task-http-result-1")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.body["task_id"], "task-http-result-1")
        self.assertEqual(response.body["error"]["category"], "runtime_contract")
        self.assertEqual(response.body["error"]["code"], "task_record_unavailable")

    def test_result_returns_terminal_success_envelope_without_rewrapping(self) -> None:
        record = self.make_succeeded_record("task-http-result-success-1")
        service = TaskHttpService(
            {TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_record_store=StaticRecordStore(record),
        )

        response = service.result("task-http-result-success-1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, make_success_envelope("task-http-result-success-1"))
        self.assertIn("raw", response.body)
        self.assertIn("normalized", response.body)

    def test_status_and_result_preserve_shared_observability_refs(self) -> None:
        task_id = "task-http-observability-1"
        envelope = make_success_envelope(task_id)
        envelope["task_record_ref"] = f"task_record:{task_id}"
        envelope["runtime_result_refs"] = [
            {
                "ref_type": "ExecutionAttemptOutcome",
                "ref_id": "attempt-1",
            }
        ]
        envelope["execution_control_events"] = [
            {
                "event_type": "retry_concurrency_rejected",
                "control_code": "concurrency_limit_exceeded",
            }
        ]
        record = finish_task_record(
            self.make_running_record(task_id),
            envelope,
            occurred_at="2026-04-24T00:00:02Z",
        )
        self.write_record(record)
        service = self.make_service()

        status_response = service.status(task_id)
        result_response = service.result(task_id)

        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.body["task_record_ref"], f"task_record:{task_id}")
        self.assertEqual(status_response.body["runtime_result_refs"], envelope["runtime_result_refs"])
        self.assertEqual(status_response.body["execution_control_events"], envelope["execution_control_events"])
        self.assertEqual(result_response.status_code, 200)
        self.assertEqual(result_response.body["task_record_ref"], f"task_record:{task_id}")
        self.assertEqual(result_response.body["runtime_result_refs"], envelope["runtime_result_refs"])
        self.assertEqual(result_response.body["execution_control_events"], envelope["execution_control_events"])

    def test_result_preserves_record_level_observability_refs_when_envelope_lacks_them(self) -> None:
        task_id = "task-http-record-observability-1"
        record = replace(
            self.make_succeeded_record(task_id),
            runtime_result_refs=(
                {
                    "ref_type": "ExecutionControlEvent",
                    "ref_id": "control-1",
                },
            ),
            execution_control_events=(
                {
                    "event_type": "retry_exhausted",
                    "control_code": "retry_exhausted",
                },
            ),
        )
        service = TaskHttpService(
            {TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_record_store=StaticRecordStore(record),
        )

        response = service.result(task_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["task_record_ref"], f"task_record:{task_id}")
        self.assertEqual(response.body["runtime_result_refs"], list(record.runtime_result_refs))
        self.assertEqual(response.body["execution_control_events"], list(record.execution_control_events))

    def test_result_returns_terminal_failed_envelope_without_rewrapping(self) -> None:
        record = self.make_failed_record("task-http-result-failed-1")
        self.write_record(record)
        service = self.make_service()

        response = service.result("task-http-result-failed-1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, make_failed_envelope("task-http-result-failed-1"))
        self.assertEqual(response.body["error"]["category"], "platform")
        self.assertEqual(response.body["error"]["code"], "platform_broken")

    def test_result_returns_creator_profile_public_envelope_without_rewrapping(self) -> None:
        record = self.make_creator_profile_record("task-http-result-creator-profile-1")
        self.write_record(record)
        service = self.make_service()

        response = service.result("task-http-result-creator-profile-1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, make_creator_profile_envelope("task-http-result-creator-profile-1"))
        self.assertNotIn("fetch_policy", response.body)
        self.assertNotIn("media", response.body)

    def test_result_returns_media_asset_fetch_public_envelope_without_rewrapping(self) -> None:
        record = self.make_media_asset_fetch_record("task-http-result-media-fetch-1")
        self.write_record(record)
        service = self.make_service()

        response = service.result("task-http-result-media-fetch-1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, make_media_asset_fetch_envelope("task-http-result-media-fetch-1"))
        self.assertNotIn("no_storage", response.body)

    def test_result_returns_conflict_when_result_is_not_ready(self) -> None:
        record = self.make_accepted_record("task-http-accepted-1")
        self.write_record(record)
        service = self.make_service()

        response = service.result("task-http-accepted-1")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.body["task_id"], "task-http-accepted-1")
        self.assertEqual(response.body["status"], "failed")
        self.assertEqual(response.body["error"]["category"], "invalid_input")
        self.assertEqual(response.body["error"]["code"], "result_not_ready")

    def test_submit_rejects_non_object_payload(self) -> None:
        response = self.make_service(task_id="task-http-invalid-1").submit(["not-object"])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.body["task_id"], "task-http-invalid-1")
        self.assertEqual(response.body["status"], "failed")
        self.assertEqual(response.body["error"]["category"], "invalid_input")
        self.assertEqual(response.body["error"]["code"], "invalid_http_task_request")

    def test_submit_rejects_missing_required_field(self) -> None:
        response = self.make_service(task_id="task-http-missing-1").submit(
            {
                "adapter_key": TEST_ADAPTER_KEY,
                "capability": "content_detail_by_url",
                "target": {},
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.body["error"]["category"], "invalid_input")
        self.assertEqual(response.body["error"]["code"], "invalid_http_task_request")

    def test_submit_rejects_invalid_capability(self) -> None:
        response = self.make_service(task_id="task-http-invalid-capability-1").submit(
            {
                "adapter_key": TEST_ADAPTER_KEY,
                "capability": "content_detail",
                "target": {"url": "https://example.com/posts/1"},
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.body["error"]["category"], "invalid_input")
        self.assertEqual(response.body["error"]["code"], "invalid_capability")

    def test_submit_passes_valid_execution_control_policy_to_core_path(self) -> None:
        adapter = PolicyRecordingAdapter()
        response = self.make_service(adapter=adapter, task_id="task-http-policy-1").submit(
            {
                "adapter_key": TEST_ADAPTER_KEY,
                "capability": "content_detail_by_url",
                "target": {"url": "https://example.com/posts/1"},
                "execution_control_policy": {
                    "timeout": {"timeout_ms": 30000},
                    "retry": {"max_attempts": 1, "backoff_ms": 0},
                    "concurrency": {"scope": "global", "max_in_flight": 1, "on_limit": "reject"},
                },
            }
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.body["task_id"], "task-http-policy-1")
        self.assertIsNotNone(adapter.execution_control_policy)
        self.assertEqual(adapter.execution_control_policy.timeout.timeout_ms, 30000)
        self.assertEqual(adapter.execution_control_policy.retry.max_attempts, 1)
        self.assertEqual(adapter.execution_control_policy.retry.backoff_ms, 0)
        self.assertEqual(adapter.execution_control_policy.concurrency.scope, "global")
        self.assertEqual(adapter.execution_control_policy.concurrency.max_in_flight, 1)
        self.assertEqual(adapter.execution_control_policy.concurrency.on_limit, "reject")

    def test_submit_materializes_default_execution_control_policy_to_core_path(self) -> None:
        adapter = PolicyRecordingAdapter()
        response = self.make_service(adapter=adapter, task_id="task-http-default-policy-1").submit(
            {
                "adapter_key": TEST_ADAPTER_KEY,
                "capability": "content_detail_by_url",
                "target": {"url": "https://example.com/posts/default-policy"},
            }
        )

        self.assertEqual(response.status_code, 202)
        self.assertIsNotNone(adapter.execution_control_policy)
        self.assertEqual(adapter.execution_control_policy.timeout.timeout_ms, 30000)
        self.assertEqual(adapter.execution_control_policy.retry.max_attempts, 1)
        self.assertEqual(adapter.execution_control_policy.retry.backoff_ms, 0)
        self.assertEqual(adapter.execution_control_policy.concurrency.scope, "global")
        self.assertEqual(adapter.execution_control_policy.concurrency.max_in_flight, 1)
        self.assertEqual(adapter.execution_control_policy.concurrency.on_limit, "reject")

    def test_submit_accepts_all_shared_execution_control_concurrency_scopes(self) -> None:
        for scope in ("global", "adapter", "adapter_capability"):
            with self.subTest(scope=scope):
                adapter = PolicyRecordingAdapter()
                response = self.make_service(adapter=adapter, task_id=f"task-http-policy-{scope}").submit(
                    {
                        "adapter_key": TEST_ADAPTER_KEY,
                        "capability": "content_detail_by_url",
                        "target": {"url": f"https://example.com/posts/{scope}"},
                        "execution_control_policy": {
                            "timeout": {"timeout_ms": 30000},
                            "retry": {"max_attempts": 1, "backoff_ms": 0},
                            "concurrency": {"scope": scope, "max_in_flight": 1, "on_limit": "reject"},
                        },
                    }
                )

                self.assertEqual(response.status_code, 202)
                self.assertIsNotNone(adapter.execution_control_policy)
                self.assertEqual(adapter.execution_control_policy.concurrency.scope, scope)

    def test_submit_rejects_invalid_execution_control_policy(self) -> None:
        response = self.make_service(task_id="task-http-policy-invalid-1").submit(
            {
                "adapter_key": TEST_ADAPTER_KEY,
                "capability": "content_detail_by_url",
                "target": {"url": "https://example.com/posts/1"},
                "execution_control_policy": {
                    "timeout": {"timeout_ms": 30000},
                    "retry": {"max_attempts": 1, "backoff_ms": 0},
                    "concurrency": {"scope": "private", "max_in_flight": 1, "on_limit": "reject"},
                },
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.body["error"]["category"], "invalid_input")
        self.assertEqual(response.body["error"]["code"], "invalid_execution_control_policy")

    def test_submit_rejects_generated_task_id_that_cannot_round_trip_as_path_segment(self) -> None:
        service = TaskHttpService(
            {TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_record_store=self.store,
            task_id_factory=lambda: "task/bad",
        )

        response = service.submit(
            {
                "adapter_key": TEST_ADAPTER_KEY,
                "capability": "content_detail_by_url",
                "target": {"url": "https://example.com/posts/bad-task-id"},
            }
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.body["task_id"], "")
        self.assertEqual(response.body["error"]["category"], "runtime_contract")
        self.assertEqual(response.body["error"]["code"], "invalid_task_id")
        self.assertEqual(list(self.store.root.iterdir()), [])

    def test_submit_preserves_preallocated_task_id_when_store_returns_mismatched_record(self) -> None:
        service = TaskHttpService(
            {TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_record_store=MismatchedTaskIdWriteStore(self.make_succeeded_record("task-http-core-other")),
            task_id_factory=lambda: "task-http-admission-1",
        )

        response = service.submit(
            {
                "adapter_key": TEST_ADAPTER_KEY,
                "capability": "content_detail_by_url",
                "target": {"url": "https://example.com/posts/mismatch"},
            }
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.body["task_id"], "task-http-admission-1")
        self.assertEqual(response.body["error"]["category"], "runtime_contract")
        self.assertEqual(response.body["error"]["code"], "invalid_task_id")

    def test_status_returns_not_found_for_missing_task_record(self) -> None:
        response = self.make_service().status("task-http-missing-1")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.body["task_id"], "task-http-missing-1")
        self.assertEqual(response.body["error"]["category"], "invalid_input")
        self.assertEqual(response.body["error"]["code"], "task_record_not_found")

    def test_status_returns_unavailable_when_store_root_is_missing(self) -> None:
        missing_store = LocalTaskRecordStore(Path(self._task_record_store_dir.name) / "missing-root")
        service = TaskHttpService(
            {TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_record_store=missing_store,
            task_id_factory=lambda: "task-http-fallback-1",
        )

        response = service.status("task-http-missing-root-1")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.body["task_id"], "task-http-missing-root-1")
        self.assertEqual(response.body["error"]["category"], "runtime_contract")
        self.assertEqual(response.body["error"]["code"], "task_record_unavailable")

    def test_status_returns_unavailable_for_invalid_marker(self) -> None:
        record = self.make_accepted_record("task-http-invalid-marker-1")
        self.write_record(record)
        self.store.mark_invalid("task-http-invalid-marker-1", stage="completion", reason="forced-invalid-marker")

        response = self.make_service().status("task-http-invalid-marker-1")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.body["error"]["category"], "runtime_contract")
        self.assertEqual(response.body["error"]["code"], "task_record_unavailable")

    def test_status_and_result_return_unavailable_for_mismatched_task_record_ref(self) -> None:
        record = self.make_succeeded_record("task-http-bad-ref-1")
        payload = task_record_to_dict(record)
        payload["task_record_ref"] = "task_record:other"
        self.write_raw_record_payload("task-http-bad-ref-1", payload)

        status_response = self.make_service().status("task-http-bad-ref-1")
        result_response = self.make_service().result("task-http-bad-ref-1")

        self.assertEqual(status_response.status_code, 500)
        self.assertEqual(status_response.body["error"]["category"], "runtime_contract")
        self.assertEqual(status_response.body["error"]["code"], "task_record_unavailable")
        self.assertEqual(result_response.status_code, 500)
        self.assertEqual(result_response.body["error"]["category"], "runtime_contract")
        self.assertEqual(result_response.body["error"]["code"], "task_record_unavailable")

    def test_status_migrates_legacy_record_missing_task_record_ref(self) -> None:
        record = self.make_succeeded_record("task-http-legacy-ref-1")
        payload = task_record_to_dict(record)
        payload.pop("task_record_ref")
        self.write_raw_record_payload("task-http-legacy-ref-1", payload)

        response = self.make_service().status("task-http-legacy-ref-1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["task_record_ref"], "task_record:task-http-legacy-ref-1")

    def test_status_and_result_return_unavailable_for_mismatched_nested_observability(self) -> None:
        record = self.make_succeeded_record("task-http-bad-nested-observability-1")
        payload = task_record_to_dict(record)
        payload["result"]["envelope"]["runtime_result_refs"] = [{"kind": "artifact", "id": "other"}]
        self.write_raw_record_payload("task-http-bad-nested-observability-1", payload)

        status_response = self.make_service().status("task-http-bad-nested-observability-1")
        result_response = self.make_service().result("task-http-bad-nested-observability-1")

        self.assertEqual(status_response.status_code, 500)
        self.assertEqual(status_response.body["error"]["category"], "runtime_contract")
        self.assertEqual(status_response.body["error"]["code"], "task_record_unavailable")
        self.assertEqual(result_response.status_code, 500)
        self.assertEqual(result_response.body["error"]["category"], "runtime_contract")
        self.assertEqual(result_response.body["error"]["code"], "task_record_unavailable")

    def test_status_returns_invalid_input_when_task_id_is_missing(self) -> None:
        response = self.make_service().status("")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.body["task_id"], "")
        self.assertEqual(response.body["error"]["category"], "invalid_input")
        self.assertEqual(response.body["error"]["code"], "missing_task_id")

    def test_status_rejects_non_string_task_id_with_contract_failed_envelope(self) -> None:
        response = self.make_service().status(123)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.body["task_id"], "")
        self.assertEqual(response.body["error"]["category"], "runtime_contract")
        self.assertEqual(response.body["error"]["code"], "invalid_task_id")

    def test_status_returns_unavailable_when_store_returns_non_record_object(self) -> None:
        service = TaskHttpService({TEST_ADAPTER_KEY: SuccessfulAdapter()}, task_record_store=NonRecordStore())

        response = service.status("task-http-non-record-status-1")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.body["task_id"], "task-http-non-record-status-1")
        self.assertEqual(response.body["error"]["category"], "runtime_contract")
        self.assertEqual(response.body["error"]["code"], "task_record_unavailable")

    def test_status_returns_unavailable_when_store_load_raises_contract_error(self) -> None:
        service = TaskHttpService(
            {TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_record_store=ContractErrorLoadStore(self.make_accepted_record("task-http-contract-load-1")),
        )

        response = service.status("task-http-contract-load-1")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.body["task_id"], "task-http-contract-load-1")
        self.assertEqual(response.body["error"]["category"], "runtime_contract")
        self.assertEqual(response.body["error"]["code"], "task_record_unavailable")

    def test_status_returns_unavailable_when_store_load_raises_unexpected_error(self) -> None:
        service = TaskHttpService(
            {TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_record_store=RuntimeErrorLoadStore(self.make_accepted_record("task-http-runtime-load-1")),
        )

        response = service.status("task-http-runtime-load-1")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.body["task_id"], "task-http-runtime-load-1")
        self.assertEqual(response.body["error"]["category"], "runtime_contract")
        self.assertEqual(response.body["error"]["code"], "task_record_unavailable")

    def test_status_and_result_return_unavailable_for_record_with_malformed_request(self) -> None:
        invalid_record = replace(self.make_succeeded_record("task-http-malformed-request-1"), request=object())
        service = TaskHttpService(
            {TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_record_store=StaticRecordStore(invalid_record),
        )

        status_response = service.status("task-http-malformed-request-1")
        result_response = service.result("task-http-malformed-request-1")

        self.assertEqual(status_response.status_code, 500)
        self.assertEqual(status_response.body["task_id"], "task-http-malformed-request-1")
        self.assertEqual(status_response.body["error"]["category"], "runtime_contract")
        self.assertEqual(status_response.body["error"]["code"], "task_record_unavailable")
        self.assertEqual(result_response.status_code, 500)
        self.assertEqual(result_response.body["task_id"], "task-http-malformed-request-1")
        self.assertEqual(result_response.body["error"]["category"], "runtime_contract")
        self.assertEqual(result_response.body["error"]["code"], "task_record_unavailable")

    def test_result_returns_unavailable_when_store_returns_non_record_object(self) -> None:
        service = TaskHttpService({TEST_ADAPTER_KEY: SuccessfulAdapter()}, task_record_store=NonRecordStore())

        response = service.result("task-http-non-record-result-1")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.body["task_id"], "task-http-non-record-result-1")
        self.assertEqual(response.body["error"]["category"], "runtime_contract")
        self.assertEqual(response.body["error"]["code"], "task_record_unavailable")

    def test_result_returns_unavailable_when_store_load_raises_unexpected_error(self) -> None:
        service = TaskHttpService(
            {TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_record_store=RuntimeErrorLoadStore(self.make_accepted_record("task-http-runtime-result-load-1")),
        )

        response = service.result("task-http-runtime-result-load-1")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.body["task_id"], "task-http-runtime-result-load-1")
        self.assertEqual(response.body["error"]["category"], "runtime_contract")
        self.assertEqual(response.body["error"]["code"], "task_record_unavailable")

    def test_result_returns_unavailable_for_invalid_json_record(self) -> None:
        self.store.root.mkdir(parents=True, exist_ok=True)
        self.store.record_path("task-http-bad-json-1").write_text("{bad json", encoding="utf-8")

        response = self.make_service().result("task-http-bad-json-1")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.body["error"]["category"], "runtime_contract")
        self.assertEqual(response.body["error"]["code"], "task_record_unavailable")

    def test_result_returns_unavailable_for_contract_invalid_record(self) -> None:
        self.store.root.mkdir(parents=True, exist_ok=True)
        invalid_payload = {
            "schema_version": "v0.3.0",
            "task_id": "task-http-bad-contract-1",
            "request": {
                "adapter_key": TEST_ADAPTER_KEY,
                "capability": "content_detail_by_url",
                "target_type": "url",
                "target_value": "https://example.com/posts/query-bad-contract-1",
                "collection_mode": "hybrid",
            },
            "status": "accepted",
            "created_at": "2026-04-24T00:00:00Z",
            "updated_at": "2026-04-24T00:00:00Z",
            "terminal_at": None,
            "result": None,
            "logs": [],
        }
        self.store.record_path("task-http-bad-contract-1").write_text(
            json.dumps(invalid_payload, ensure_ascii=False),
            encoding="utf-8",
        )

        response = self.make_service().result("task-http-bad-contract-1")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.body["error"]["category"], "runtime_contract")
        self.assertEqual(response.body["error"]["code"], "task_record_unavailable")

    def test_result_returns_unavailable_for_invalid_terminal_status_from_store(self) -> None:
        invalid_record = replace(self.make_succeeded_record("task-http-invalid-status-1"), status="paused")
        service = TaskHttpService(
            {TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_record_store=StaticRecordStore(invalid_record),
        )

        response = service.result("task-http-invalid-status-1")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.body["error"]["category"], "runtime_contract")
        self.assertEqual(response.body["error"]["code"], "task_record_unavailable")

    def test_result_returns_unavailable_for_non_json_terminal_envelope(self) -> None:
        invalid_envelope = dict(make_success_envelope("task-http-non-json-1"))
        invalid_envelope["raw"] = {"bad": {"not-json-safe"}}
        invalid_record = replace(
            self.make_succeeded_record("task-http-non-json-1"),
            result=TaskTerminalResult(envelope=invalid_envelope),
        )
        service = TaskHttpService(
            {TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_record_store=StaticRecordStore(invalid_record),
        )

        response = service.result("task-http-non-json-1")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.body["error"]["category"], "runtime_contract")
        self.assertEqual(response.body["error"]["code"], "task_record_unavailable")

    def test_result_returns_unavailable_for_mismatched_terminal_envelope(self) -> None:
        invalid_envelope = dict(make_success_envelope("task-http-mismatched-envelope-other"))
        invalid_record = replace(
            self.make_succeeded_record("task-http-mismatched-envelope-1"),
            result=TaskTerminalResult(envelope=invalid_envelope),
        )
        service = TaskHttpService(
            {TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_record_store=StaticRecordStore(invalid_record),
        )

        response = service.result("task-http-mismatched-envelope-1")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.body["error"]["category"], "runtime_contract")
        self.assertEqual(response.body["error"]["code"], "task_record_unavailable")


class WsgiAppTests(unittest.TestCase):
    def test_wsgi_routes_canonical_submit_status_and_result_paths(self) -> None:
        service = RecordingService()
        app = build_wsgi_app(service)

        submit_status, _, submit_body = invoke_wsgi_app(
            app,
            method="POST",
            path="/v0/tasks",
            body=json.dumps(
                {
                    "adapter_key": TEST_ADAPTER_KEY,
                    "capability": "content_detail_by_url",
                    "target": {"url": "https://example.com/posts/1"},
                }
            ).encode("utf-8"),
        )
        status_status, _, _ = invoke_wsgi_app(app, method="GET", path="/v0/tasks/task-1")
        result_status, _, _ = invoke_wsgi_app(app, method="GET", path="/v0/tasks/task-1/result")

        self.assertEqual(submit_status, "202 Accepted")
        self.assertEqual(json.loads(submit_body.decode("utf-8"))["status"], "accepted")
        self.assertEqual(status_status, "200 OK")
        self.assertEqual(result_status, "200 OK")
        self.assertEqual(
            service.calls,
            [
                (
                    "submit",
                    {
                        "adapter_key": TEST_ADAPTER_KEY,
                        "capability": "content_detail_by_url",
                        "target": {"url": "https://example.com/posts/1"},
                    },
                ),
                ("status", "task-1"),
                ("result", "task-1"),
            ],
        )

    def test_wsgi_rejects_query_alias_with_json_failed_envelope(self) -> None:
        app = build_wsgi_app(RecordingService())

        status, headers, body = invoke_wsgi_app(
            app,
            method="GET",
            path="/v0/tasks/task-1",
            query_string="task_id=task-2",
        )

        header_map = {key.lower(): value for key, value in headers}
        payload_text = body.decode("utf-8")
        payload = json.loads(payload_text)
        self.assertEqual(status, "400 Bad Request")
        self.assertTrue(header_map["content-type"].startswith("application/json"))
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["error"]["code"], "invalid_http_request")
        self.assertEqual(payload["task_id"], "task-1")
        self.assertNotIn("<html", payload_text.lower())

    def test_wsgi_invalid_status_subroute_uses_path_task_id_in_failed_envelope(self) -> None:
        app = build_wsgi_app(RecordingService())

        status, _, body = invoke_wsgi_app(app, method="GET", path="/v0/tasks/task-1/private")

        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(status, "400 Bad Request")
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["task_id"], "task-1")
        self.assertEqual(payload["error"]["code"], "invalid_http_request")

    def test_wsgi_rejects_negative_content_length_without_calling_submit(self) -> None:
        service = RecordingService()
        app = build_wsgi_app(service)

        environ_body = b'{"adapter_key":"xhs"}'
        captured: dict[str, Any] = {}
        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/v0/tasks",
            "CONTENT_TYPE": "application/json",
            "CONTENT_LENGTH": "-1",
            "QUERY_STRING": "",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8000",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "http",
            "wsgi.input": io.BytesIO(environ_body),
            "wsgi.errors": io.StringIO(),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
        }

        def start_response(raw_status: str, headers: list[tuple[str, str]], exc_info: Any = None) -> None:
            del exc_info
            captured["status"] = raw_status
            captured["headers"] = headers

        payload = b"".join(app(environ, start_response))

        self.assertEqual(captured["status"], "400 Bad Request")
        self.assertEqual(json.loads(payload.decode("utf-8"))["error"]["code"], "invalid_http_request")
        self.assertEqual(service.calls, [])

    def test_wsgi_read_failure_returns_json_failed_envelope(self) -> None:
        service = RecordingService()
        app = build_wsgi_app(service)
        captured: dict[str, Any] = {}
        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/v0/tasks",
            "CONTENT_TYPE": "application/json",
            "CONTENT_LENGTH": "2",
            "QUERY_STRING": "",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8000",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "http",
            "wsgi.input": BrokenInputStream(),
            "wsgi.errors": io.StringIO(),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
        }

        def start_response(raw_status: str, headers: list[tuple[str, str]], exc_info: Any = None) -> None:
            del exc_info
            captured["status"] = raw_status
            captured["headers"] = headers

        payload = b"".join(app(environ, start_response))

        self.assertEqual(captured["status"], "400 Bad Request")
        self.assertEqual(json.loads(payload.decode("utf-8"))["error"]["code"], "invalid_http_request")
        self.assertEqual(service.calls, [])

    def test_wsgi_missing_task_id_returns_invalid_input_failed_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskHttpService(
                {TEST_ADAPTER_KEY: SuccessfulAdapter()},
                task_record_store=LocalTaskRecordStore(Path(temp_dir)),
            )
            app = build_wsgi_app(service)

            status, _, body = invoke_wsgi_app(app, method="GET", path="/v0/tasks/")

        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(status, "400 Bad Request")
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["error"]["category"], "invalid_input")
        self.assertEqual(payload["error"]["code"], "missing_task_id")

    def test_wsgi_rejects_percent_encoded_slash_task_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskHttpService(
                {TEST_ADAPTER_KEY: SuccessfulAdapter()},
                task_record_store=LocalTaskRecordStore(Path(temp_dir)),
            )
            app = build_wsgi_app(service)

            status, _, body = invoke_wsgi_app(app, method="GET", path="/v0/tasks/a%2Fb")

        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(status, "400 Bad Request")
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["error"]["category"], "runtime_contract")
        self.assertEqual(payload["error"]["code"], "invalid_task_id")

    def test_wsgi_unknown_route_returns_json_without_html_fallback(self) -> None:
        app = build_wsgi_app(RecordingService())

        status, headers, body = invoke_wsgi_app(app, method="GET", path="/unknown")

        header_map = {key.lower(): value for key, value in headers}
        payload_text = body.decode("utf-8")
        payload = json.loads(payload_text)
        self.assertEqual(status, "404 Not Found")
        self.assertTrue(header_map["content-type"].startswith("application/json"))
        self.assertEqual(payload["status"], "failed")
        self.assertNotIn("<html", payload_text.lower())


if __name__ == "__main__":
    unittest.main()
