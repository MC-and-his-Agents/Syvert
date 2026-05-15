from __future__ import annotations

from datetime import datetime, timezone
import unittest
from unittest import mock

from syvert.batch_dataset import (
    BATCH_ITEM_DUPLICATE_SKIPPED,
    BATCH_ITEM_FAILED,
    BATCH_ITEM_SUCCEEDED,
    BATCH_RESULT_ALL_FAILED,
    BATCH_RESULT_COMPLETE,
    BATCH_RESULT_PARTIAL_SUCCESS,
    BATCH_RESULT_RESUMABLE,
    BatchDatasetContractError,
    BatchItemOutcome,
    BatchRequest,
    BatchResultEnvelope,
    BatchResumeToken,
    BatchTargetItem,
    ReferenceDatasetSink,
    batch_result_envelope_to_dict,
    batch_resume_token_to_dict,
    batch_target_set_hash,
    execute_batch_request,
    validate_batch_request,
    validate_batch_item_outcome,
    validate_batch_target_item,
    validate_dataset_record,
)
from syvert.runtime import TaskInput, TaskRequest, execute_task
from tests.runtime.test_task_record import (
    make_collection_result,
    make_comment_collection_result,
    make_creator_profile_result,
    make_media_asset_fetch_result,
)


TEST_ADAPTER_KEY = "xhs"


class CollectionAdapter:
    supported_capabilities = frozenset({"content_search"})
    supported_targets = frozenset({"keyword"})
    supported_collection_modes = frozenset({"paginated"})

    def execute(self, request):
        return make_collection_result(target_ref=request.input.keyword or "")


class CursorRecordingAdapter(CollectionAdapter):
    supported_capabilities = frozenset({"comment_collection"})
    supported_targets = frozenset({"content"})
    supported_collection_modes = frozenset({"paginated"})

    def __init__(self) -> None:
        self.request_cursors = []

    def execute(self, request):
        self.request_cursors.append(request.input.comment_request_cursor)
        return make_comment_collection_result(target_ref=request.input.content_ref or "")


class ReplyCommentCollectionAdapter(CursorRecordingAdapter):
    def execute(self, request):
        self.request_cursors.append(request.input.comment_request_cursor)
        payload = make_comment_collection_result(target_ref=request.input.content_ref or "")
        payload["items"][0]["source_id"] = "reply-1"
        payload["items"][0]["source_ref"] = "comment://reply-1"
        payload["items"][0]["normalized"]["source_id"] = "reply-1"
        payload["items"][0]["normalized"]["canonical_ref"] = "comment:reply-1"
        payload["items"][0]["normalized"]["parent_comment_ref"] = "comment:root-1"
        payload["items"][0]["normalized"]["target_comment_ref"] = "comment:root-1"
        return payload


class PaginatedCursorRecordingAdapter:
    supported_capabilities = frozenset({"content_search", "content_list"})
    supported_targets = frozenset({"keyword", "creator"})
    supported_collection_modes = frozenset({"paginated"})

    def __init__(self) -> None:
        self.request_cursors = []

    def execute(self, request):
        self.request_cursors.append(request.request.request_cursor)
        if request.capability == "content_search":
            return make_collection_result(target_ref=request.target_value)
        if request.capability == "content_list":
            return make_collection_result(
                operation="content_list_by_creator",
                target_type="creator",
                target_ref=request.target_value,
            )
        raise AssertionError(f"unexpected capability {request.capability}")


class MultiReadSideAdapter:
    supported_capabilities = frozenset(
        {
            "content_search",
            "content_list",
            "comment_collection",
            "creator_profile",
            "media_asset_fetch",
        }
    )
    supported_targets = frozenset({"keyword", "creator", "content", "media_ref"})
    supported_collection_modes = frozenset({"paginated", "direct"})

    def execute(self, request):
        if request.capability == "content_search":
            return make_collection_result(target_ref=request.input.keyword or "")
        if request.capability == "content_list":
            return make_collection_result(
                operation="content_list_by_creator",
                target_type="creator",
                target_ref=request.input.creator_id or "",
            )
        if request.capability == "comment_collection":
            return make_comment_collection_result(target_ref=request.input.content_ref or "")
        if request.capability == "creator_profile":
            return make_creator_profile_result(target_ref=request.input.creator_id or "")
        if request.capability == "media_asset_fetch":
            return make_media_asset_fetch_result(target_ref=request.input.media_ref or "")
        raise AssertionError(f"unexpected capability {request.capability}")


class FailingCollectionAdapter(CollectionAdapter):
    def execute(self, request):
        from syvert.runtime import PlatformAdapterError

        raise PlatformAdapterError(
            code="permission_denied",
            message="permission denied",
            details={"evidence_ref": "evidence:permission-denied"},
        )


class KeywordFailingCollectionAdapter(CollectionAdapter):
    def __init__(self, failing_keywords: set[str]) -> None:
        self.failing_keywords = failing_keywords

    def execute(self, request):
        from syvert.runtime import PlatformAdapterError

        if request.input.keyword in self.failing_keywords:
            raise PlatformAdapterError(
                code="permission_denied",
                message="permission denied",
                details={"evidence_ref": "evidence:permission-denied"},
            )
        return make_collection_result(target_ref=request.input.keyword or "")


class UnsafeFailingCollectionAdapter(CollectionAdapter):
    def execute(self, request):
        from syvert.runtime import PlatformAdapterError

        raise PlatformAdapterError(
            code="permission_denied",
            message="permission denied",
            details={"local_path": "/etc/passwd", "evidence_ref": "evidence:permission-denied"},
        )


class TimeoutCollectionAdapter(CollectionAdapter):
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request):
        from syvert.runtime import PlatformAdapterError

        self.calls += 1
        raise PlatformAdapterError(
            code="execution_timeout",
            message="execution timed out",
            details={"control_code": "execution_timeout", "evidence_ref": "evidence:timeout"},
        )


class UnsafeSourceTraceAdapter(CollectionAdapter):
    def execute(self, request):
        payload = make_collection_result(target_ref=request.input.keyword or "")
        payload["source_trace"] = {
            "adapter_key": TEST_ADAPTER_KEY,
            "provider_path": "https://provider.example/raw",
            "fetched_at": "2026-05-13T10:00:00Z",
            "evidence_alias": "evidence:unsafe",
            "storage_handle": "private-storage-handle",
        }
        return payload


class UnsafeProviderPathAdapter(CollectionAdapter):
    def execute(self, request):
        payload = make_collection_result(target_ref=request.input.keyword or "")
        payload["source_trace"] = {
            "adapter_key": TEST_ADAPTER_KEY,
            "provider_path": "https://provider.example/route",
            "fetched_at": "2026-05-13T10:00:00Z",
            "evidence_alias": "evidence:unsafe-provider-path",
        }
        return payload


class UnsafeNormalizedPayloadAdapter(CollectionAdapter):
    def execute(self, request):
        payload = make_collection_result(target_ref=request.input.keyword or "")
        payload["items"][0]["normalized"]["artifact"] = "/etc/passwd"
        return payload


class PublicUrlCollectionAdapter(CollectionAdapter):
    def execute(self, request):
        payload = make_collection_result(target_ref=request.input.keyword or "")
        payload["items"][0]["source_ref"] = "https://example.com/posts/1"
        payload["items"][0]["normalized"]["canonical_ref"] = "https://example.com/posts/1"
        return payload


class UnsafeSuccessAuditAdapter(CollectionAdapter):
    def execute(self, request):
        payload = make_collection_result(target_ref=request.input.keyword or "")
        payload["audit"] = {"local_path": "/etc/passwd"}
        return payload


class FailingDatasetSink(ReferenceDatasetSink):
    def write(self, record):
        raise BatchDatasetContractError(
            "dataset_write_failed",
            "write failed",
            details={"evidence_ref": "evidence:dataset-write-failed"},
        )


class RuntimeFailingDatasetSink(ReferenceDatasetSink):
    def write(self, record):
        raise RuntimeError("disk unavailable at /private/storage")


def now() -> datetime:
    return datetime(2026, 5, 13, 10, 0, 0, tzinfo=timezone.utc)


def target(
    item_id: str,
    target_ref: str,
    *,
    dedup_key: str | None = None,
    operation: str = "content_search_by_keyword",
) -> BatchTargetItem:
    return BatchTargetItem(
        item_id=item_id,
        operation=operation,
        adapter_key=TEST_ADAPTER_KEY,
        target_type="keyword",
        target_ref=target_ref,
        dedup_key=dedup_key or f"dedup:{target_ref}",
    )


def request(
    *items: BatchTargetItem,
    resume_token: BatchResumeToken | None = None,
    dataset_id: str | None = None,
) -> BatchRequest:
    return BatchRequest(
        batch_id="batch-001",
        target_set=items,
        resume_token=resume_token,
        dataset_id=dataset_id,
        dataset_sink_ref="dataset-sink:reference",
        audit_context={"evidence_ref": "evidence:batch"},
    )


def runtime_result_envelope(payload, *, task_id="task-test-1", adapter_key=TEST_ADAPTER_KEY, capability=None):
    return {
        "task_id": task_id,
        "adapter_key": adapter_key,
        "capability": capability or payload["operation"],
        "status": "success",
        **payload,
    }


class BatchDatasetRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapters = {TEST_ADAPTER_KEY: CollectionAdapter()}
        self.task_ids = iter(f"task-{index}" for index in range(1, 20))

    def task_id(self) -> str:
        return next(self.task_ids)

    def execute(self, batch_request: BatchRequest, *, sink=None, **kwargs):
        with mock.patch.dict("syvert.runtime.RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE", {}, clear=True):
            return execute_batch_request(
                batch_request,
                adapters=self.adapters,
                dataset_sink=sink if sink is not None else ReferenceDatasetSink(),
                task_id_factory=self.task_id,
                now_factory=now,
                **kwargs,
            )

    def test_all_success_writes_dataset_records(self) -> None:
        sink = ReferenceDatasetSink()
        result = self.execute(request(target("item-1", "alpha"), target("item-2", "beta")), sink=sink)

        self.assertEqual(result.result_status, BATCH_RESULT_COMPLETE)
        self.assertEqual([outcome.outcome_status for outcome in result.item_outcomes], [BATCH_ITEM_SUCCEEDED] * 2)
        self.assertEqual(result.dataset_id, "dataset:batch-001")
        self.assertEqual(len(sink.read_by_dataset("dataset:batch-001")), 2)
        self.assertEqual(len(sink.read_by_batch("batch-001")), 2)
        self.assertEqual(sink.audit_replay("dataset:batch-001")[0]["evidence_ref"], "alias://collection-page-1")
        self.assertEqual(result.audit_trace["batch_id"], "batch-001")
        self.assertEqual(result.audit_trace["started_at"], "2026-05-13T10:00:00Z")
        self.assertEqual(result.audit_trace["finished"], True)
        self.assertEqual(
            result.audit_trace["item_trace_refs"],
            ("audit:batch:batch-001:item-1", "audit:batch:batch-001:item-2"),
        )
        self.assertIn("evidence:batch", result.audit_trace["evidence_refs"])

    def test_reference_sink_readback_is_defensive_copy(self) -> None:
        sink = ReferenceDatasetSink()
        original_record = {
            "dataset_record_id": "record-1",
            "dataset_id": "dataset-1",
            "source_operation": "content_search_by_keyword",
            "adapter_key": TEST_ADAPTER_KEY,
            "target_ref": "alpha",
            "raw_payload_ref": "raw://alpha",
            "normalized_payload": {"items": [{"title_or_text_hint": "safe"}]},
            "evidence_ref": "evidence:alpha",
            "source_trace": {
                "adapter_key": TEST_ADAPTER_KEY,
                "provider_path": "provider://sanitized",
                "fetched_at": "2026-05-13T10:00:00Z",
                "evidence_alias": "evidence:alpha",
            },
            "dedup_key": "dedup:alpha",
            "batch_id": "batch-001",
            "batch_item_id": "item-1",
            "recorded_at": "2026-05-13T10:00:00Z",
        }

        written = sink.write(original_record)
        original_record["normalized_payload"]["items"][0]["local_path"] = "/etc/passwd"
        written.normalized_payload["items"][0]["storage_handle"] = "private-storage-handle"
        first_read = sink.read_by_dataset("dataset-1")[0]
        first_read.normalized_payload["items"][0]["download_url"] = "https://private.example/raw"
        first_replay = sink.audit_replay("dataset-1")[0]
        first_replay["normalized_payload"]["items"][0]["file_path"] = "/tmp/raw.json"

        second_read = sink.read_by_dataset("dataset-1")[0]
        second_replay = sink.audit_replay("dataset-1")[0]
        self.assertEqual(second_read.normalized_payload, {"items": [{"title_or_text_hint": "safe"}]})
        self.assertEqual(second_replay["normalized_payload"], {"items": [{"title_or_text_hint": "safe"}]})

    def test_execute_task_rejects_direct_batch_execution_as_shared_request(self) -> None:
        class LegacyBatchAdapter:
            supported_capabilities = frozenset({"batch_execution"})
            supported_targets = frozenset({"operation_batch"})
            supported_collection_modes = frozenset({"batch"})

            def execute(self, request):
                return {"raw": {"provider_batch": True}, "normalized": {"provider_batch": True}}

        envelope = execute_task(
            TaskRequest(adapter_key=TEST_ADAPTER_KEY, capability="batch_execution", input=TaskInput()),
            adapters={TEST_ADAPTER_KEY: LegacyBatchAdapter()},
            task_id_factory=lambda: "task-direct-batch",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_capability")
        self.assertEqual(envelope["error"]["details"]["task_record_ref"], "none")

    def test_batch_result_serialization_rejects_unsafe_top_level_carriers(self) -> None:
        result = self.execute(request(target("item-1", "alpha")))
        unsafe_cases = (
            ("batch_id", {"batch_id": "file:///tmp/raw-batch.json"}, "unsafe_ref"),
            ("windows batch_id", {"batch_id": "C:/work/raw-batch.json"}, "unsafe_ref"),
            ("relative batch_id", {"batch_id": "batch:../raw.json"}, "unsafe_ref"),
            ("dataset_sink_ref", {"dataset_sink_ref": "storage://private/sink"}, "unsafe_ref"),
            ("windows dataset_id", {"dataset_id": "D:/exports/dataset.json"}, "unsafe_ref"),
            ("relative dataset_id", {"dataset_id": "dataset:cache/state.json"}, "unsafe_ref"),
            ("dataset_id", {"dataset_id": "/etc/dataset"}, "unsafe_ref"),
            ("result_status", {"result_status": "provider_fallback"}, "invalid_batch_result_status"),
            (
                "audit evidence",
                {"audit_trace": {**result.audit_trace, "evidence_refs": ("file:///tmp/raw.json",)}},
                "unsafe_public_payload",
            ),
            (
                "audit stop reason",
                {"audit_trace": {**result.audit_trace, "stop_reason": "storage://private/stop-reason"}},
                "unsafe_public_payload",
            ),
            (
                "windows audit payload",
                {"audit_trace": {**result.audit_trace, "stop_reason": "C:/work/cache.json"}},
                "unsafe_public_payload",
            ),
        )
        for _label, overrides, code in unsafe_cases:
            forged = BatchResultEnvelope(
                batch_id=overrides.get("batch_id", result.batch_id),
                operation=overrides.get("operation", result.operation),
                result_status=overrides.get("result_status", result.result_status),
                item_outcomes=result.item_outcomes,
                resume_token=overrides.get("resume_token", result.resume_token),
                dataset_sink_ref=overrides.get("dataset_sink_ref", result.dataset_sink_ref),
                dataset_id=overrides.get("dataset_id", result.dataset_id),
                audit_trace=overrides.get("audit_trace", result.audit_trace),
            )
            with self.subTest(_label):
                with self.assertRaises(BatchDatasetContractError) as context:
                    batch_result_envelope_to_dict(forged)

                self.assertEqual(context.exception.code, code)

    def test_batch_result_serialization_rejects_sink_without_dataset_identity(self) -> None:
        result = self.execute(request(target("item-1", "alpha")))
        forged = BatchResultEnvelope(
            batch_id=result.batch_id,
            operation=result.operation,
            result_status=result.result_status,
            item_outcomes=result.item_outcomes,
            resume_token=result.resume_token,
            dataset_sink_ref=result.dataset_sink_ref,
            dataset_id=None,
            audit_trace=result.audit_trace,
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            batch_result_envelope_to_dict(forged)

        self.assertEqual(context.exception.code, "invalid_dataset_boundary")

    def test_batch_result_serialization_rejects_incomplete_audit_trace(self) -> None:
        result = self.execute(request(target("item-1", "alpha")))
        forged = BatchResultEnvelope(
            batch_id=result.batch_id,
            operation=result.operation,
            result_status=result.result_status,
            item_outcomes=result.item_outcomes,
            resume_token=result.resume_token,
            dataset_sink_ref=result.dataset_sink_ref,
            dataset_id=result.dataset_id,
            audit_trace={},
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            batch_result_envelope_to_dict(forged)

        self.assertEqual(context.exception.code, "invalid_batch_audit_trace")

    def test_batch_result_serialization_rejects_forged_item_trace_refs(self) -> None:
        result = self.execute(request(target("item-1", "alpha")))
        forged = BatchResultEnvelope(
            batch_id=result.batch_id,
            operation=result.operation,
            result_status=result.result_status,
            item_outcomes=result.item_outcomes,
            resume_token=result.resume_token,
            dataset_sink_ref=result.dataset_sink_ref,
            dataset_id=result.dataset_id,
            audit_trace={**result.audit_trace, "item_trace_refs": ("audit:batch:batch-001:other-item",)},
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            batch_result_envelope_to_dict(forged)

        self.assertEqual(context.exception.code, "invalid_batch_audit_trace")

    def test_batch_result_serialization_rejects_audit_trace_shape_drift_matrix(self) -> None:
        result = self.execute(request(target("item-1", "alpha")))
        cases = (
            ("wrong-batch", {**result.audit_trace, "batch_id": "other-batch"}),
            ("wrong-count", {**result.audit_trace, "item_count": 2}),
            ("bool-count", {**result.audit_trace, "item_count": True}),
            ("extra-field", {**result.audit_trace, "debug": "extra"}),
            ("string-trace-refs", {**result.audit_trace, "item_trace_refs": "audit:batch:batch-001:item-1"}),
            ("wrong-evidence-type", {**result.audit_trace, "evidence_refs": "evidence:batch"}),
        )

        for label, audit_trace in cases:
            with self.subTest(label=label):
                forged = BatchResultEnvelope(
                    batch_id=result.batch_id,
                    operation=result.operation,
                    result_status=result.result_status,
                    item_outcomes=result.item_outcomes,
                    resume_token=result.resume_token,
                    dataset_sink_ref=result.dataset_sink_ref,
                    dataset_id=result.dataset_id,
                    audit_trace=audit_trace,
                )

                with self.assertRaises(BatchDatasetContractError) as context:
                    batch_result_envelope_to_dict(forged)

                self.assertEqual(context.exception.code, "invalid_batch_audit_trace")

    def test_batch_result_serialization_rejects_aggregate_status_drift(self) -> None:
        success = self.execute(request(target("item-1", "alpha")))
        self.adapters = {TEST_ADAPTER_KEY: FailingCollectionAdapter()}
        failed = self.execute(request(target("item-1", "alpha")))
        self.adapters = {TEST_ADAPTER_KEY: CollectionAdapter(), "failed": FailingCollectionAdapter()}
        mixed = self.execute(
            BatchRequest(
                batch_id="batch-001",
                target_set=(
                    target("item-1", "alpha"),
                    BatchTargetItem(
                        item_id="item-2",
                        operation="content_search_by_keyword",
                        adapter_key="failed",
                        target_type="keyword",
                        target_ref="beta",
                        dedup_key="dedup:beta",
                    ),
                ),
                dataset_sink_ref="dataset-sink:reference",
            ),
        )
        cases = (
            ("success-as-all-failed", success, BATCH_RESULT_ALL_FAILED, BATCH_RESULT_COMPLETE),
            ("failed-as-complete", failed, BATCH_RESULT_COMPLETE, BATCH_RESULT_ALL_FAILED),
            ("mixed-as-complete", mixed, BATCH_RESULT_COMPLETE, BATCH_RESULT_PARTIAL_SUCCESS),
            ("mixed-as-all-failed", mixed, BATCH_RESULT_ALL_FAILED, BATCH_RESULT_PARTIAL_SUCCESS),
        )

        for label, source, forged_status, expected in cases:
            with self.subTest(label=label):
                forged = BatchResultEnvelope(
                    batch_id=source.batch_id,
                    operation=source.operation,
                    result_status=forged_status,
                    item_outcomes=source.item_outcomes,
                    resume_token=source.resume_token,
                    dataset_sink_ref=source.dataset_sink_ref,
                    dataset_id=source.dataset_id,
                    audit_trace=source.audit_trace,
                )

                with self.assertRaises(BatchDatasetContractError) as context:
                    batch_result_envelope_to_dict(forged)

                self.assertEqual(context.exception.code, "invalid_batch_result_status")
                self.assertEqual(context.exception.details["expected"], expected)

    def test_batch_result_serialization_rejects_invalid_resume_boundary(self) -> None:
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            stop_after_items=1,
            stop_reason="timeout",
        )
        forged = BatchResultEnvelope(
            batch_id=first.batch_id,
            operation=first.operation,
            result_status=first.result_status,
            item_outcomes=first.item_outcomes,
            resume_token=BatchResumeToken(**{**first.resume_token.__dict__, "dataset_id": "dataset:other"}),
            dataset_sink_ref=first.dataset_sink_ref,
            dataset_id=first.dataset_id,
            audit_trace=first.audit_trace,
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            batch_result_envelope_to_dict(forged)

        self.assertEqual(context.exception.code, "invalid_resume_token")

        forged_position = BatchResultEnvelope(
            batch_id=first.batch_id,
            operation=first.operation,
            result_status=first.result_status,
            item_outcomes=(),
            resume_token=first.resume_token,
            dataset_sink_ref=first.dataset_sink_ref,
            dataset_id=first.dataset_id,
            audit_trace=first.audit_trace,
        )

        with self.assertRaises(BatchDatasetContractError) as position_context:
            batch_result_envelope_to_dict(forged_position)

        self.assertEqual(position_context.exception.code, "invalid_resume_token")

    def test_resume_token_serialization_rejects_unsafe_runtime_position_carriers(self) -> None:
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            stop_after_items=1,
            stop_reason="timeout",
        )
        unsafe_cases = (
            ("resume_token", "provider:fallback:marketplace", "unsafe_ref"),
            ("resume_token", "resume:cache/state.json", "unsafe_ref"),
            ("batch_id", "file:///tmp/batch", "unsafe_ref"),
            ("target_set_hash", "provider:fallback:marketplace", "unsafe_ref"),
            ("next_item_index", -1, "invalid_resume_position"),
            ("issued_at", "not-a-timestamp", "invalid_timestamp"),
            ("dataset_sink_ref", "storage://private/sink", "unsafe_ref"),
            ("dataset_id", "/etc/dataset", "unsafe_ref"),
        )
        for field, value, code in unsafe_cases:
            forged = BatchResumeToken(**{**first.resume_token.__dict__, field: value})
            with self.subTest(field):
                with self.assertRaises(BatchDatasetContractError) as context:
                    batch_resume_token_to_dict(forged)

                self.assertEqual(context.exception.code, code)

    def test_resume_token_serialization_rejects_sink_without_dataset_identity(self) -> None:
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            stop_after_items=1,
            stop_reason="timeout",
        )
        forged = BatchResumeToken(**{**first.resume_token.__dict__, "dataset_id": None})

        with self.assertRaises(BatchDatasetContractError) as context:
            batch_resume_token_to_dict(forged)

        self.assertEqual(context.exception.code, "invalid_dataset_boundary")

    def test_request_validation_rejects_unsafe_public_ids(self) -> None:
        unsafe_batch = BatchRequest(
            batch_id="http://evil/batch",
            target_set=(target("item-1", "alpha"),),
            dataset_sink_ref="dataset-sink:reference",
            audit_context={"evidence_ref": "evidence:batch"},
        )
        with self.assertRaises(BatchDatasetContractError) as batch_context:
            self.execute(unsafe_batch)

        self.assertEqual(batch_context.exception.code, "unsafe_ref")

        unsafe_item = BatchRequest(
            batch_id="batch-001",
            target_set=(target("http://evil/item", "alpha"),),
            dataset_sink_ref="dataset-sink:reference",
            audit_context={"evidence_ref": "evidence:batch"},
        )
        with self.assertRaises(BatchDatasetContractError) as item_context:
            self.execute(unsafe_item)

        self.assertEqual(item_context.exception.code, "unsafe_ref")

    def test_request_validation_rejects_malformed_media_fetch_cursor(self) -> None:
        media_item = BatchTargetItem(
            item_id="media",
            operation="media_asset_fetch_by_ref",
            adapter_key=TEST_ADAPTER_KEY,
            target_type="media_ref",
            target_ref="media:alpha",
            dedup_key="dedup:media",
            request_cursor={"allow_download": "yes", "storage_handle": "secret"},
        )

        for validator in (
            lambda: validate_batch_target_item(media_item),
            lambda: validate_batch_request(request(media_item)),
        ):
            with self.subTest(validator=validator):
                with self.assertRaises(BatchDatasetContractError) as context:
                    validator()

                self.assertEqual(context.exception.code, "invalid_task_request")

    def test_request_validation_rejects_malformed_comment_cursor(self) -> None:
        comment_item = BatchTargetItem(
            item_id="comments",
            operation="comment_collection",
            adapter_key=TEST_ADAPTER_KEY,
            target_type="content",
            target_ref="content:alpha",
            dedup_key="dedup:comments",
            request_cursor={
                "reply_cursor": {
                    "reply_cursor_token": "reply-cursor-1",
                    "reply_cursor_family": "opaque",
                    "resume_target_ref": "content:other",
                    "resume_comment_ref": "comment:root-1",
                }
            },
        )

        for validator in (
            lambda: validate_batch_target_item(comment_item),
            lambda: validate_batch_request(request(comment_item)),
        ):
            with self.subTest(validator=validator):
                with self.assertRaises(BatchDatasetContractError) as context:
                    validator()

                self.assertEqual(context.exception.code, "cursor_invalid_or_expired")

    def test_request_validation_rejects_duplicate_item_ids(self) -> None:
        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(
                    target("item-1", "alpha", dedup_key="dedup:alpha"),
                    target("item-1", "beta", dedup_key="dedup:beta"),
                )
            )

        self.assertEqual(context.exception.code, "duplicate_item_id")
        self.assertEqual(context.exception.details["item_id"], "item-1")

    def test_search_keyword_allows_common_content_words(self) -> None:
        sink = ReferenceDatasetSink()
        result = self.execute(
            request(target("item-1", "fallback selector marketplace account-pool guide", dedup_key="dedup:keyword-common")),
            sink=sink,
        )

        self.assertEqual(result.result_status, BATCH_RESULT_COMPLETE)
        self.assertEqual(result.item_outcomes[0].outcome_status, BATCH_ITEM_SUCCEEDED)
        self.assertEqual(sink.read_by_batch("batch-001")[0].target_ref, "fallback selector marketplace account-pool guide")

    def test_malformed_audit_context_fails_closed(self) -> None:
        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                BatchRequest(
                    batch_id="batch-001",
                    target_set=(target("item-1", "alpha"),),
                    dataset_sink_ref="dataset-sink:reference",
                    audit_context=[],
                )
            )

        self.assertEqual(context.exception.code, "invalid_field")

    def test_public_payload_allows_free_text_urls_and_rejects_success_error_mix(self) -> None:
        result_envelope = runtime_result_envelope(make_collection_result(target_ref="alpha"), capability="content_search_by_keyword")
        result_envelope["items"][0]["normalized"]["title_or_text_hint"] = (
            "mentions https://example.invalid and /home text as content"
        )
        validate_batch_item_outcome(
            BatchItemOutcome(
                item_id="item-1",
                operation="content_search_by_keyword",
                adapter_key=TEST_ADAPTER_KEY,
                target_ref="alpha",
                outcome_status=BATCH_ITEM_SUCCEEDED,
                result_envelope=result_envelope,
                audit={"reason": "dataset_record_written"},
            )
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            validate_batch_item_outcome(
                BatchItemOutcome(
                    item_id="item-1",
                    operation="content_search_by_keyword",
                    adapter_key=TEST_ADAPTER_KEY,
                    target_ref="alpha",
                    outcome_status=BATCH_ITEM_SUCCEEDED,
                    result_envelope={"status": "success", "items": []},
                    error_envelope={"code": "stale", "message": "stale", "details": {}},
                    audit={"reason": "dataset_record_written"},
                )
            )

        self.assertEqual(context.exception.code, "invalid_item_outcome")

    def test_batch_item_outcome_rejects_wrong_read_side_result_envelope(self) -> None:
        forged = BatchItemOutcome(
            item_id="item-1",
            operation="content_search_by_keyword",
            adapter_key=TEST_ADAPTER_KEY,
            target_ref="alpha",
            outcome_status=BATCH_ITEM_SUCCEEDED,
            result_envelope=runtime_result_envelope(
                make_creator_profile_result(target_ref="creator-1"),
                capability="creator_profile_by_id",
            ),
            audit={"reason": "dataset_record_written"},
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            validate_batch_item_outcome(forged)

        self.assertEqual(context.exception.code, "result_envelope_boundary_mismatch")

    def test_batch_item_outcome_rejects_extra_result_envelope_fields(self) -> None:
        result_envelope = runtime_result_envelope(
            make_creator_profile_result(target_ref="creator-1"),
            capability="creator_profile_by_id",
        )
        result_envelope["debug"] = {"raw": "not in public contract"}
        forged = BatchItemOutcome(
            item_id="creator",
            operation="creator_profile_by_id",
            adapter_key=TEST_ADAPTER_KEY,
            target_ref="creator-1",
            outcome_status=BATCH_ITEM_SUCCEEDED,
            result_envelope=result_envelope,
            audit={"reason": "dataset_record_written"},
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            validate_batch_item_outcome(forged)

        self.assertEqual(context.exception.code, "result_envelope_boundary_mismatch")

    def test_batch_item_outcome_rejects_malformed_runtime_result_wrapper_matrix(self) -> None:
        base = runtime_result_envelope(make_collection_result(target_ref="alpha"), capability="content_search_by_keyword")
        cases = (
            ("missing-status", {key: value for key, value in base.items() if key != "status"}, "result_envelope_boundary_mismatch"),
            ("missing-task-id", {key: value for key, value in base.items() if key != "task_id"}, "result_envelope_boundary_mismatch"),
            ("failed-status", {**base, "status": "failed"}, "result_envelope_boundary_mismatch"),
            ("wrong-capability", {**base, "capability": "comment_collection"}, "result_envelope_boundary_mismatch"),
            ("wrong-adapter", {**base, "adapter_key": "other-adapter"}, "result_envelope_boundary_mismatch"),
            ("unsafe-task-id", {**base, "task_id": "file:///tmp/task"}, "unsafe_ref"),
            ("unsafe-task-record-ref", {**base, "task_record_ref": "file:///tmp/task-record"}, "unsafe_ref"),
            (
                "unsafe-runtime-result-ref",
                {**base, "runtime_result_refs": [{"ref_type": "ExecutionAttemptOutcome", "ref_id": "s3://bucket/raw"}]},
                "unsafe_ref",
            ),
            (
                "unsafe-control-event-ref",
                {**base, "execution_control_events": [{"event_id": "event-1", "task_record_ref": "/Users/mc/private"}]},
                "unsafe_ref",
            ),
            (
                "unsafe-runtime-log-message",
                {**base, "runtime_structured_log_events": [{"event_id": "event-1", "message": "token=secret"}]},
                "unsafe_public_payload",
            ),
        )

        for label, result_envelope, expected_code in cases:
            with self.subTest(label=label):
                forged = BatchItemOutcome(
                    item_id="item-1",
                    operation="content_search_by_keyword",
                    adapter_key=TEST_ADAPTER_KEY,
                    target_ref="alpha",
                    outcome_status=BATCH_ITEM_SUCCEEDED,
                    result_envelope=result_envelope,
                    audit={"reason": "dataset_record_written"},
                )

                with self.assertRaises(BatchDatasetContractError) as context:
                    validate_batch_item_outcome(forged)

                self.assertEqual(context.exception.code, expected_code)

    def test_batch_item_outcome_rejects_cursor_bound_comment_without_cursor_context(self) -> None:
        result_envelope = runtime_result_envelope(
            make_comment_collection_result(target_ref="content:alpha"),
            capability="comment_collection",
        )
        result_envelope["items"][0]["normalized"]["parent_comment_ref"] = "comment:root-1"
        result_envelope["items"][0]["normalized"]["target_comment_ref"] = "comment:root-1"
        forged = BatchItemOutcome(
            item_id="comments",
            operation="comment_collection",
            adapter_key=TEST_ADAPTER_KEY,
            target_ref="content:alpha",
            outcome_status=BATCH_ITEM_SUCCEEDED,
            result_envelope=result_envelope,
            audit={"reason": "dataset_record_written"},
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            validate_batch_item_outcome(forged)

        self.assertEqual(context.exception.code, "result_envelope_boundary_mismatch")

    def test_error_and_audit_strings_reject_raw_paths(self) -> None:
        for index, outcome in enumerate(
            (
                BatchItemOutcome(
                    item_id="item-1",
                    operation="content_search_by_keyword",
                    adapter_key=TEST_ADAPTER_KEY,
                    target_ref="alpha",
                    outcome_status=BATCH_ITEM_FAILED,
                    error_envelope={
                        "code": "permission_denied",
                        "message": "failed at /etc/passwd",
                        "details": {"path": "/etc/passwd"},
                    },
                    audit={"reason": "item_failed"},
                ),
                BatchItemOutcome(
                    item_id="item-1",
                    operation="content_search_by_keyword",
                    adapter_key=TEST_ADAPTER_KEY,
                    target_ref="alpha",
                    outcome_status=BATCH_ITEM_FAILED,
                    error_envelope={"code": "permission_denied", "message": "permission denied", "details": {}},
                    audit={"reason": "file:///tmp/raw"},
                ),
            ),
            start=1,
        ):
            with self.subTest(index=index):
                with self.assertRaises(BatchDatasetContractError) as context:
                    validate_batch_item_outcome(outcome)

                self.assertEqual(context.exception.code, "unsafe_public_payload")

    def test_all_stable_read_side_item_operations_are_projected_through_existing_envelopes(self) -> None:
        self.adapters = {TEST_ADAPTER_KEY: MultiReadSideAdapter()}
        sink = ReferenceDatasetSink()
        batch_request = request(
            target("search", "alpha"),
            BatchTargetItem(
                item_id="list",
                operation="content_list_by_creator",
                adapter_key=TEST_ADAPTER_KEY,
                target_type="creator",
                target_ref="creator:alpha",
                dedup_key="dedup:list",
            ),
            BatchTargetItem(
                item_id="comments",
                operation="comment_collection",
                adapter_key=TEST_ADAPTER_KEY,
                target_type="content",
                target_ref="content:alpha",
                dedup_key="dedup:comments",
            ),
            BatchTargetItem(
                item_id="creator",
                operation="creator_profile_by_id",
                adapter_key=TEST_ADAPTER_KEY,
                target_type="creator",
                target_ref="creator:alpha",
                dedup_key="dedup:creator",
            ),
            BatchTargetItem(
                item_id="media",
                operation="media_asset_fetch_by_ref",
                adapter_key=TEST_ADAPTER_KEY,
                target_type="media_ref",
                target_ref="media:alpha",
                dedup_key="dedup:media",
                request_cursor={
                    "fetch_mode": "metadata_only",
                    "allowed_content_types": ["image", "video"],
                    "allow_download": False,
                    "max_bytes": None,
                },
            ),
        )

        result = self.execute(batch_request, sink=sink)

        self.assertEqual(result.result_status, BATCH_RESULT_COMPLETE)
        self.assertEqual([outcome.outcome_status for outcome in result.item_outcomes], [BATCH_ITEM_SUCCEEDED] * 5)
        self.assertEqual(
            [record.source_operation for record in sink.read_by_batch("batch-001")],
            [
                "content_search_by_keyword",
                "content_list_by_creator",
                "comment_collection",
                "creator_profile_by_id",
                "media_asset_fetch_by_ref",
            ],
        )

    def test_partial_success_preserves_item_failure(self) -> None:
        self.adapters = {TEST_ADAPTER_KEY: CollectionAdapter(), "failed": FailingCollectionAdapter()}
        batch_request = BatchRequest(
            batch_id="batch-001",
            target_set=(
                target("item-1", "alpha"),
                BatchTargetItem(
                    item_id="item-2",
                    operation="content_search_by_keyword",
                    adapter_key="failed",
                    target_type="keyword",
                    target_ref="beta",
                    dedup_key="dedup:beta",
                ),
            ),
            dataset_sink_ref="dataset-sink:reference",
        )

        result = self.execute(batch_request)

        self.assertEqual(result.result_status, BATCH_RESULT_PARTIAL_SUCCESS)
        self.assertEqual(result.item_outcomes[0].outcome_status, BATCH_ITEM_SUCCEEDED)
        self.assertEqual(result.item_outcomes[1].outcome_status, BATCH_ITEM_FAILED)
        self.assertEqual(result.item_outcomes[1].error_envelope["code"], "permission_denied")

    def test_failed_item_unsafe_error_details_are_sanitized_before_return(self) -> None:
        self.adapters = {TEST_ADAPTER_KEY: UnsafeFailingCollectionAdapter()}

        result = self.execute(request(target("item-1", "alpha")))

        self.assertEqual(result.result_status, BATCH_RESULT_ALL_FAILED)
        self.assertEqual(result.item_outcomes[0].outcome_status, BATCH_ITEM_FAILED)
        self.assertEqual(result.item_outcomes[0].error_envelope["code"], "unsafe_item_outcome")
        self.assertNotIn("/etc/passwd", repr(result.item_outcomes[0].error_envelope))

    def test_all_failed_has_no_dataset_records(self) -> None:
        self.adapters = {TEST_ADAPTER_KEY: FailingCollectionAdapter()}
        sink = ReferenceDatasetSink()

        result = self.execute(request(target("item-1", "alpha")), sink=sink)

        self.assertEqual(result.result_status, BATCH_RESULT_ALL_FAILED)
        self.assertEqual(result.item_outcomes[0].outcome_status, BATCH_ITEM_FAILED)
        self.assertEqual(sink.read_by_batch("batch-001"), ())

    def test_unsafe_success_outcome_does_not_write_dataset_record(self) -> None:
        self.adapters = {TEST_ADAPTER_KEY: UnsafeSuccessAuditAdapter()}
        sink = ReferenceDatasetSink()

        result = self.execute(request(target("item-1", "alpha")), sink=sink)

        self.assertEqual(result.result_status, BATCH_RESULT_ALL_FAILED)
        self.assertEqual(result.item_outcomes[0].outcome_status, BATCH_ITEM_FAILED)
        self.assertEqual(result.item_outcomes[0].error_envelope["code"], "unsafe_item_outcome")
        self.assertEqual(sink.read_by_batch("batch-001"), ())
        self.assertEqual(sink.read_by_dataset("dataset:batch-001"), ())

    def test_unsafe_success_source_trace_is_failed_item_not_batch_exception(self) -> None:
        self.adapters = {TEST_ADAPTER_KEY: UnsafeProviderPathAdapter()}
        sink = ReferenceDatasetSink()

        result = self.execute(request(target("item-1", "alpha")), sink=sink)

        self.assertEqual(result.result_status, BATCH_RESULT_ALL_FAILED)
        self.assertEqual(result.item_outcomes[0].outcome_status, BATCH_ITEM_FAILED)
        self.assertEqual(result.item_outcomes[0].error_envelope["code"], "unsafe_item_outcome")
        self.assertEqual(result.item_outcomes[0].error_envelope["details"]["blocked_code"], "unsafe_provider_path")
        self.assertIsNone(result.item_outcomes[0].result_envelope)
        self.assertEqual(sink.read_by_batch("batch-001"), ())

    def test_duplicate_target_is_neutral_and_first_wins(self) -> None:
        sink = ReferenceDatasetSink()

        result = self.execute(
            request(
                target("item-1", "alpha", dedup_key="same"),
                target("item-2", "alpha", dedup_key="same"),
            ),
            sink=sink,
        )

        self.assertEqual(result.result_status, BATCH_RESULT_COMPLETE)
        self.assertEqual(result.item_outcomes[1].outcome_status, BATCH_ITEM_DUPLICATE_SKIPPED)
        self.assertEqual(len(sink.read_by_batch("batch-001")), 1)

    def test_duplicate_skipped_is_neutral_when_other_items_fail(self) -> None:
        self.adapters = {TEST_ADAPTER_KEY: KeywordFailingCollectionAdapter({"beta"})}
        sink = ReferenceDatasetSink()

        result = self.execute(
            request(
                target("item-1", "alpha", dedup_key="same"),
                target("item-2", "alpha", dedup_key="same"),
                target("item-3", "beta"),
            ),
            sink=sink,
        )

        self.assertEqual(result.result_status, BATCH_RESULT_PARTIAL_SUCCESS)
        self.assertEqual(
            [outcome.outcome_status for outcome in result.item_outcomes],
            [BATCH_ITEM_SUCCEEDED, BATCH_ITEM_DUPLICATE_SKIPPED, BATCH_ITEM_FAILED],
        )
        self.assertEqual(len(sink.read_by_batch("batch-001")), 1)

    def test_duplicate_skipped_is_neutral_when_all_non_duplicates_fail(self) -> None:
        self.adapters = {TEST_ADAPTER_KEY: KeywordFailingCollectionAdapter({"beta"})}
        sink = ReferenceDatasetSink()

        result = self.execute(
            request(
                target("item-1", "beta", dedup_key="same"),
                target("item-2", "beta", dedup_key="same"),
            ),
            sink=sink,
        )

        self.assertEqual(result.result_status, BATCH_RESULT_ALL_FAILED)
        self.assertEqual(
            [outcome.outcome_status for outcome in result.item_outcomes],
            [BATCH_ITEM_FAILED, BATCH_ITEM_DUPLICATE_SKIPPED],
        )
        self.assertEqual(sink.read_by_batch("batch-001"), ())

    def test_caller_dataset_id_round_trips_to_result_and_records(self) -> None:
        sink = ReferenceDatasetSink()

        result = self.execute(request(target("item-1", "alpha"), dataset_id="dataset:custom-001"), sink=sink)

        self.assertEqual(result.result_status, BATCH_RESULT_COMPLETE)
        self.assertEqual(result.dataset_id, "dataset:custom-001")
        records = sink.read_by_batch("batch-001")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].dataset_id, "dataset:custom-001")
        self.assertEqual(sink.read_by_dataset("dataset:custom-001")[0].dataset_id, "dataset:custom-001")

    def test_resume_returns_prefix_then_combined_terminal_outcomes(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )

        self.assertEqual(first.result_status, BATCH_RESULT_RESUMABLE)
        self.assertEqual(len(first.item_outcomes), 1)
        self.assertEqual(first.resume_token.next_item_index, 1)
        resumed_request = request(
            target("item-1", "alpha"),
            target("item-2", "beta"),
            resume_token=first.resume_token,
        )
        resumed = self.execute(resumed_request, sink=sink, prior_item_outcomes=first.item_outcomes)

        self.assertEqual(resumed.result_status, BATCH_RESULT_COMPLETE)
        self.assertIsNone(resumed.resume_token)
        self.assertEqual([outcome.item_id for outcome in resumed.item_outcomes], ["item-1", "item-2"])
        self.assertEqual(len(sink.read_by_batch("batch-001")), 2)

    def test_resume_stop_after_items_advances_from_resume_position(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta"), target("item-3", "gamma")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )

        second = self.execute(
            request(
                target("item-1", "alpha"),
                target("item-2", "beta"),
                target("item-3", "gamma"),
                resume_token=first.resume_token,
            ),
            sink=sink,
            prior_item_outcomes=first.item_outcomes,
            stop_after_items=1,
            stop_reason="timeout",
        )

        self.assertEqual(second.result_status, BATCH_RESULT_RESUMABLE)
        self.assertEqual(second.resume_token.next_item_index, 2)
        self.assertEqual([outcome.item_id for outcome in second.item_outcomes], ["item-1", "item-2"])

    def test_resume_rejects_rewound_runtime_position(self) -> None:
        sink = ReferenceDatasetSink()
        target_set = (target("item-1", "alpha"), target("item-2", "beta"), target("item-3", "gamma"))
        second = self.execute(
            request(*target_set),
            sink=sink,
            stop_after_items=2,
            stop_reason="timeout",
        )
        rewound_token = BatchResumeToken(
            **{
                **second.resume_token.__dict__,
                "resume_token": "resume:batch-001:1",
                "next_item_index": 1,
            }
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(*target_set, resume_token=rewound_token),
                sink=sink,
                prior_item_outcomes=second.item_outcomes[:1],
            )

        self.assertEqual(context.exception.code, "invalid_resume_position")

    def test_resume_rejects_forged_prior_outcome_prefix(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        forged = type(first.item_outcomes[0])(
            **{**first.item_outcomes[0].__dict__, "item_id": "other-item"}
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(target("item-1", "alpha"), target("item-2", "beta"), resume_token=first.resume_token),
                sink=sink,
                prior_item_outcomes=(forged,),
            )

        self.assertEqual(context.exception.code, "resume_outcome_prefix_mismatch")

    def test_resume_rejects_forged_prior_success_result_envelope_target(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        forged_envelope = {
            **first.item_outcomes[0].result_envelope,
            "operation": "content_list_by_creator",
            "target": {
                "operation": "content_list_by_creator",
                "target_type": "creator",
                "target_ref": "creator-beta",
            },
        }
        forged = BatchItemOutcome(
            **{
                **first.item_outcomes[0].__dict__,
                "result_envelope": forged_envelope,
            }
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(target("item-1", "alpha"), target("item-2", "beta"), resume_token=first.resume_token),
                sink=sink,
                prior_item_outcomes=(forged,),
            )

        self.assertEqual(context.exception.code, "result_envelope_boundary_mismatch")

    def test_resume_rejects_forged_prior_success_result_envelope_wrapper(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        forged = BatchItemOutcome(
            **{
                **first.item_outcomes[0].__dict__,
                "result_envelope": {
                    **first.item_outcomes[0].result_envelope,
                    "status": "failed",
                    "capability": "comment_collection",
                    "adapter_key": "other-adapter",
                },
            }
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(target("item-1", "alpha"), target("item-2", "beta"), resume_token=first.resume_token),
                sink=sink,
                prior_item_outcomes=(forged,),
            )

        self.assertEqual(context.exception.code, "result_envelope_boundary_mismatch")

    def test_resume_rejects_non_duplicate_prior_outcome_marked_duplicate_skipped(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        forged = BatchItemOutcome(
            **{**first.item_outcomes[0].__dict__, "outcome_status": BATCH_ITEM_DUPLICATE_SKIPPED}
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(target("item-1", "alpha"), target("item-2", "beta"), resume_token=first.resume_token),
                sink=sink,
                prior_item_outcomes=(forged,),
            )

        self.assertEqual(context.exception.code, "invalid_item_outcome")

    def test_resume_rejects_unknown_prior_outcome_status(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        forged = BatchItemOutcome(
            **{**first.item_outcomes[0].__dict__, "outcome_status": "stale_pending"}
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(target("item-1", "alpha"), target("item-2", "beta"), resume_token=first.resume_token),
                sink=sink,
                prior_item_outcomes=(forged,),
            )

        self.assertEqual(context.exception.code, "invalid_item_outcome_status")

    def test_resume_rejects_prior_outcome_with_unsafe_source_trace(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        forged = BatchItemOutcome(
            **{
                **first.item_outcomes[0].__dict__,
                "source_trace": {
                    "adapter_key": TEST_ADAPTER_KEY,
                    "provider_path": "https://provider.example/route",
                    "fetched_at": "2026-05-13T10:00:00Z",
                    "evidence_alias": "evidence:unsafe",
                    "storage_handle": "private-storage-handle",
                },
            }
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(target("item-1", "alpha"), target("item-2", "beta"), resume_token=first.resume_token),
                sink=sink,
                prior_item_outcomes=(forged,),
            )

        self.assertEqual(context.exception.code, "unsafe_source_trace")

    def test_resume_rejects_prior_outcome_with_invalid_source_trace_timestamp(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        forged = BatchItemOutcome(
            **{
                **first.item_outcomes[0].__dict__,
                "source_trace": {
                    **first.item_outcomes[0].source_trace,
                    "fetched_at": "/etc/passwd",
                },
            }
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(target("item-1", "alpha"), target("item-2", "beta"), resume_token=first.resume_token),
                sink=sink,
                prior_item_outcomes=(forged,),
            )

        self.assertEqual(context.exception.code, "invalid_timestamp")

    def test_resume_rejects_prior_outcome_with_unsafe_result_envelope(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        forged = BatchItemOutcome(
            **{
                **first.item_outcomes[0].__dict__,
                "result_envelope": {
                    **first.item_outcomes[0].result_envelope,
                    "storage_handle": "private-storage-handle",
                    "storageHandle": "private-storage-handle",
                },
            }
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(target("item-1", "alpha"), target("item-2", "beta"), resume_token=first.resume_token),
                sink=sink,
                prior_item_outcomes=(forged,),
            )

        self.assertEqual(context.exception.code, "unsafe_public_payload")

    def test_resume_rejects_failed_prior_outcome_without_error_envelope(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        forged = BatchItemOutcome(
            **{
                **first.item_outcomes[0].__dict__,
                "outcome_status": BATCH_ITEM_FAILED,
                "result_envelope": None,
                "error_envelope": None,
                "dataset_record_ref": None,
            }
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(target("item-1", "alpha"), target("item-2", "beta"), resume_token=first.resume_token),
                sink=sink,
                prior_item_outcomes=(forged,),
            )

        self.assertEqual(context.exception.code, "invalid_item_outcome")

    def test_resume_rejects_failed_prior_outcome_with_dataset_record_ref(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        forged = BatchItemOutcome(
            **{
                **first.item_outcomes[0].__dict__,
                "outcome_status": BATCH_ITEM_FAILED,
                "result_envelope": None,
                "error_envelope": {"code": "permission_denied", "message": "permission denied", "details": {}},
                "dataset_record_ref": "dataset:batch-001:item-1",
            }
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(target("item-1", "alpha"), target("item-2", "beta"), resume_token=first.resume_token),
                sink=sink,
                prior_item_outcomes=(forged,),
            )

        self.assertEqual(context.exception.code, "invalid_item_outcome")

    def test_resume_without_dataset_sink_rejects_forged_dataset_record_ref(self) -> None:
        first = self.execute(
            BatchRequest(
                batch_id="batch-001",
                target_set=(target("item-1", "alpha"), target("item-2", "beta")),
                dataset_sink_ref=None,
                audit_context={"evidence_ref": "evidence:batch"},
            ),
            stop_after_items=1,
            stop_reason="timeout",
        )
        forged = BatchItemOutcome(
            **{**first.item_outcomes[0].__dict__, "dataset_record_ref": "dataset:forged:item-1"}
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                BatchRequest(
                    batch_id="batch-001",
                    target_set=(target("item-1", "alpha"), target("item-2", "beta")),
                    resume_token=first.resume_token,
                    dataset_sink_ref=None,
                    audit_context={"evidence_ref": "evidence:batch"},
                ),
                prior_item_outcomes=(forged,),
            )

        self.assertEqual(context.exception.code, "invalid_resume_token")

    def test_resume_rejects_failed_prior_outcome_with_stale_sink_record(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        forged_failed = BatchItemOutcome(
            **{
                **first.item_outcomes[0].__dict__,
                "outcome_status": BATCH_ITEM_FAILED,
                "result_envelope": None,
                "error_envelope": {"code": "permission_denied", "message": "permission denied", "details": {}},
                "dataset_record_ref": None,
            }
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(target("item-1", "alpha"), target("item-2", "beta"), resume_token=first.resume_token),
                sink=sink,
                prior_item_outcomes=(forged_failed,),
            )

        self.assertEqual(context.exception.code, "resume_dataset_state_mismatch")

    def test_resume_rejects_duplicate_prior_outcome_with_stale_sink_record(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(
                target("item-1", "alpha", dedup_key="same"),
                target("item-2", "alpha", dedup_key="same"),
                target("item-3", "beta"),
            ),
            sink=sink,
            stop_after_items=2,
            stop_reason="timeout",
        )
        stale = type(sink.read_by_batch("batch-001")[0])(
            **{
                **sink.read_by_batch("batch-001")[0].__dict__,
                "dataset_record_id": "dataset:batch-001:item-2",
                "batch_item_id": "item-2",
            }
        )
        sink._records.append(stale)

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(
                    target("item-1", "alpha", dedup_key="same"),
                    target("item-2", "alpha", dedup_key="same"),
                    target("item-3", "beta"),
                    resume_token=first.resume_token,
                ),
                sink=sink,
                prior_item_outcomes=first.item_outcomes,
            )

        self.assertEqual(context.exception.code, "resume_dataset_state_mismatch")

    def test_resume_rejects_duplicate_prior_outcome_with_error_payload(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(
                target("item-1", "alpha", dedup_key="same"),
                target("item-2", "alpha", dedup_key="same"),
                target("item-3", "beta"),
            ),
            sink=sink,
            stop_after_items=2,
            stop_reason="timeout",
        )
        forged_duplicate = BatchItemOutcome(
            **{
                **first.item_outcomes[1].__dict__,
                "error_envelope": {"code": "stale", "message": "stale", "details": {}},
            }
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(
                    target("item-1", "alpha", dedup_key="same"),
                    target("item-2", "alpha", dedup_key="same"),
                    target("item-3", "beta"),
                    resume_token=first.resume_token,
                ),
                sink=sink,
                prior_item_outcomes=(first.item_outcomes[0], forged_duplicate),
            )

        self.assertEqual(context.exception.code, "invalid_item_outcome")

    def test_fresh_execution_rejects_prior_outcomes_without_resume_token(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(target("item-1", "alpha"), target("item-2", "beta")),
                sink=sink,
                prior_item_outcomes=first.item_outcomes,
            )

        self.assertEqual(context.exception.code, "resume_outcome_prefix_mismatch")

    def test_resume_rejects_success_prefix_without_dataset_sink_state(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(target("item-1", "alpha"), target("item-2", "beta"), resume_token=first.resume_token),
                sink=ReferenceDatasetSink(),
                prior_item_outcomes=first.item_outcomes,
            )

        self.assertEqual(context.exception.code, "resume_dataset_state_mismatch")

    def test_resume_rejects_tampered_success_dataset_record_identity(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        record = sink.read_by_batch("batch-001")[0]
        cases = (
            {"target_ref": "other-target"},
            {"source_operation": "content_list_by_creator"},
            {"adapter_key": "other-adapter"},
            {"dataset_record_id": "dataset:batch-001:other-item"},
        )

        for overrides in cases:
            with self.subTest(overrides=overrides):
                tampered_sink = ReferenceDatasetSink()
                tampered_sink.write(type(record)(**{**record.__dict__, **overrides}))

                with self.assertRaises(BatchDatasetContractError) as context:
                    self.execute(
                        request(target("item-1", "alpha"), target("item-2", "beta"), resume_token=first.resume_token),
                        sink=tampered_sink,
                        prior_item_outcomes=first.item_outcomes,
                    )

                self.assertEqual(context.exception.code, "resume_dataset_state_mismatch")

    def test_resume_rejects_success_dataset_record_with_wrong_batch_identity(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        record = sink.read_by_batch("batch-001")[0]
        tampered_sink = ReferenceDatasetSink()
        tampered_sink.write(
            type(record)(
                **{
                    **record.__dict__,
                    "dataset_record_id": "dataset:batch-001:item-1-tampered",
                    "batch_item_id": "other-item",
                }
            )
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(target("item-1", "alpha"), target("item-2", "beta"), resume_token=first.resume_token),
                sink=tampered_sink,
                prior_item_outcomes=first.item_outcomes,
            )

        self.assertEqual(context.exception.code, "resume_dataset_state_mismatch")

    def test_resume_rejects_omitted_dataset_sink_ref_boundary(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        resumed_request = BatchRequest(
            batch_id="batch-001",
            target_set=(target("item-1", "alpha"), target("item-2", "beta")),
            resume_token=first.resume_token,
            dataset_sink_ref=None,
            audit_context={"evidence_ref": "evidence:batch"},
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(resumed_request, sink=sink, prior_item_outcomes=first.item_outcomes)

        self.assertEqual(context.exception.code, "invalid_resume_token")

    def test_resume_rejects_changed_dataset_id_boundary(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        resumed_request = BatchRequest(
            batch_id="batch-001",
            target_set=(target("item-1", "alpha"), target("item-2", "beta")),
            resume_token=first.resume_token,
            dataset_sink_ref="dataset-sink:reference",
            dataset_id="dataset:changed",
            audit_context={"evidence_ref": "evidence:batch"},
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(resumed_request, sink=sink, prior_item_outcomes=first.item_outcomes)

        self.assertEqual(context.exception.code, "invalid_resume_token")

    def test_resume_token_mismatch_fails_closed(self) -> None:
        token = BatchResumeToken(
            resume_token="resume:bad",
            batch_id="other",
            target_set_hash=batch_target_set_hash((target("item-1", "alpha"),)),
            next_item_index=1,
            issued_at="2026-05-13T10:00:00Z",
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(request(target("item-1", "alpha"), resume_token=token))

        self.assertEqual(context.exception.code, "invalid_resume_token")

    def test_request_validation_rejects_malformed_nested_resume_token_matrix(self) -> None:
        sink = ReferenceDatasetSink()
        target_set = (target("item-1", "alpha"), target("item-2", "beta"))
        first = self.execute(
            request(*target_set),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        cases = (
            ("bad-token-id", {**first.resume_token.__dict__, "resume_token": "not-a-token"}, "invalid_resume_token"),
            ("wrong-batch", {**first.resume_token.__dict__, "batch_id": "other-batch"}, "invalid_resume_token"),
            ("wrong-target-hash", {**first.resume_token.__dict__, "target_set_hash": "sha256:other"}, "invalid_resume_token"),
            ("wrong-dataset", {**first.resume_token.__dict__, "dataset_id": "dataset:other"}, "invalid_resume_token"),
            ("outside-target-set", {**first.resume_token.__dict__, "next_item_index": 3}, "invalid_resume_position"),
        )

        for label, token_payload, expected_code in cases:
            with self.subTest(label=label):
                forged_request = BatchRequest(
                    batch_id="batch-001",
                    target_set=target_set,
                    resume_token=BatchResumeToken(**token_payload),
                    dataset_sink_ref="dataset-sink:reference",
                    audit_context={"evidence_ref": "evidence:batch"},
                )

                with self.assertRaises(BatchDatasetContractError) as context:
                    validate_batch_request(forged_request)

                self.assertEqual(context.exception.code, expected_code)

    def test_resume_token_carrier_rejects_routing_semantics(self) -> None:
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        forged_token = BatchResumeToken(
            **{
                **first.resume_token.__dict__,
                "resume_token": f"{first.resume_token.resume_token}:provider:fallback:marketplace",
            }
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(target("item-1", "alpha"), target("item-2", "beta"), resume_token=forged_token),
                sink=sink,
                prior_item_outcomes=first.item_outcomes,
            )

        self.assertEqual(context.exception.code, "unsafe_ref")

    def test_timeout_item_failure_stops_batch_as_resumable(self) -> None:
        adapter = TimeoutCollectionAdapter()
        self.adapters = {TEST_ADAPTER_KEY: adapter}
        sink = ReferenceDatasetSink()

        result = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=sink,
        )

        self.assertEqual(result.result_status, BATCH_RESULT_RESUMABLE)
        self.assertEqual(adapter.calls, 1)
        self.assertEqual(len(result.item_outcomes), 1)
        self.assertEqual(result.item_outcomes[0].outcome_status, BATCH_ITEM_FAILED)
        self.assertEqual(result.resume_token.next_item_index, 1)
        self.assertEqual(result.audit_trace["finished"], False)
        self.assertEqual(result.audit_trace["stop_reason"], "execution_timeout")
        self.assertEqual(result.audit_trace["item_trace_refs"], ("audit:batch:batch-001:item-1",))
        self.assertIn("evidence:batch:execution_timeout", result.audit_trace["evidence_refs"])

    def test_invalid_target_operation_is_rejected(self) -> None:
        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(request(target("item-1", "alpha", operation="content_publish")))

        self.assertEqual(context.exception.code, "invalid_target_operation")

    def test_search_and_list_request_cursors_are_passed_to_existing_item_path(self) -> None:
        adapter = PaginatedCursorRecordingAdapter()
        self.adapters = {TEST_ADAPTER_KEY: adapter}

        result = self.execute(
            request(
                BatchTargetItem(
                    item_id="search",
                    operation="content_search_by_keyword",
                    adapter_key=TEST_ADAPTER_KEY,
                    target_type="keyword",
                    target_ref="alpha",
                    dedup_key="dedup:search",
                    request_cursor={"continuation_token": "search-page"},
                ),
                BatchTargetItem(
                    item_id="list",
                    operation="content_list_by_creator",
                    adapter_key=TEST_ADAPTER_KEY,
                    target_type="creator",
                    target_ref="creator:alpha",
                    dedup_key="dedup:list",
                    request_cursor={"continuation_token": "list-page"},
                ),
            )
        )

        self.assertEqual(result.result_status, BATCH_RESULT_COMPLETE)
        self.assertEqual([outcome.outcome_status for outcome in result.item_outcomes], [BATCH_ITEM_SUCCEEDED, BATCH_ITEM_SUCCEEDED])
        self.assertEqual(
            adapter.request_cursors,
            [{"continuation_token": "search-page"}, {"continuation_token": "list-page"}],
        )

    def test_paginated_request_cursor_must_be_object(self) -> None:
        cases = (
            BatchTargetItem(
                item_id="search",
                operation="content_search_by_keyword",
                adapter_key=TEST_ADAPTER_KEY,
                target_type="keyword",
                target_ref="alpha",
                dedup_key="dedup:search",
                request_cursor=[],
            ),
            BatchTargetItem(
                item_id="list",
                operation="content_list_by_creator",
                adapter_key=TEST_ADAPTER_KEY,
                target_type="creator",
                target_ref="creator:alpha",
                dedup_key="dedup:list",
                request_cursor=[],
            ),
        )

        for index, item in enumerate(cases):
            with self.subTest(operation=item.operation):
                with self.assertRaises(BatchDatasetContractError) as context:
                    validate_batch_target_item(item, index=index)

                self.assertEqual(context.exception.code, "invalid_field")
                self.assertEqual(context.exception.details["field"], "request_cursor")

    def test_creator_profile_request_cursor_is_rejected_instead_of_silently_dropped(self) -> None:
        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(
                    BatchTargetItem(
                        item_id="creator",
                        operation="creator_profile_by_id",
                        adapter_key=TEST_ADAPTER_KEY,
                        target_type="creator",
                        target_ref="creator:alpha",
                        dedup_key="dedup:creator",
                        request_cursor={"profile_cursor": "ignored"},
                    )
                )
            )

        self.assertEqual(context.exception.code, "unsupported_request_cursor")

    def test_comment_request_cursor_is_passed_to_existing_item_path(self) -> None:
        adapter = CursorRecordingAdapter()
        self.adapters = {TEST_ADAPTER_KEY: adapter}
        cursor = {
            "page_continuation": {
                "continuation_token": "comment-page-cursor-1",
                "continuation_family": "opaque",
                "resume_target_ref": "content:alpha",
                "issued_at": "2026-05-09T10:00:00Z",
            }
        }

        self.execute(
            request(
                BatchTargetItem(
                    item_id="comments",
                    operation="comment_collection",
                    adapter_key=TEST_ADAPTER_KEY,
                    target_type="content",
                    target_ref="content:alpha",
                    dedup_key="dedup:comments",
                    request_cursor=cursor,
                )
            )
        )

        self.assertEqual(adapter.request_cursors, [cursor])

    def test_cursor_sensitive_comment_outcome_uses_item_cursor_for_public_validation(self) -> None:
        adapter = ReplyCommentCollectionAdapter()
        self.adapters = {TEST_ADAPTER_KEY: adapter}
        cursor = {
            "reply_cursor": {
                "reply_cursor_token": "reply-cursor-1",
                "reply_cursor_family": "opaque",
                "resume_target_ref": "content:alpha",
                "resume_comment_ref": "comment:root-1",
                "issued_at": "2026-05-09T10:00:00Z",
            }
        }

        result = self.execute(
            request(
                BatchTargetItem(
                    item_id="comments",
                    operation="comment_collection",
                    adapter_key=TEST_ADAPTER_KEY,
                    target_type="content",
                    target_ref="content:alpha",
                    dedup_key="dedup:comments",
                    request_cursor=cursor,
                )
            )
        )

        self.assertEqual(result.result_status, BATCH_RESULT_COMPLETE)
        self.assertEqual(result.item_outcomes[0].outcome_status, BATCH_ITEM_SUCCEEDED)
        self.assertEqual(adapter.request_cursors, [cursor])
        payload = batch_result_envelope_to_dict(result)
        self.assertEqual(payload["item_outcomes"][0]["outcome_status"], BATCH_ITEM_SUCCEEDED)
        self.assertNotIn("request_cursor_context", payload["item_outcomes"][0])

    def test_resume_reattaches_cursor_context_for_prior_comment_outcome_serialization(self) -> None:
        adapter = ReplyCommentCollectionAdapter()
        self.adapters = {TEST_ADAPTER_KEY: adapter}
        cursor = {
            "reply_cursor": {
                "reply_cursor_token": "reply-cursor-1",
                "reply_cursor_family": "opaque",
                "resume_target_ref": "content:alpha",
                "resume_comment_ref": "comment:root-1",
                "issued_at": "2026-05-09T10:00:00Z",
            }
        }
        first_item = BatchTargetItem(
            item_id="comments",
            operation="comment_collection",
            adapter_key=TEST_ADAPTER_KEY,
            target_type="content",
            target_ref="content:alpha",
            dedup_key="dedup:comments",
            request_cursor=cursor,
        )
        second_item = BatchTargetItem(
            item_id="comments-duplicate",
            operation="comment_collection",
            adapter_key=TEST_ADAPTER_KEY,
            target_type="content",
            target_ref="content:alpha",
            dedup_key="dedup:comments",
            request_cursor=cursor,
        )
        sink = ReferenceDatasetSink()
        first = self.execute(
            request(first_item, second_item),
            sink=sink,
            stop_after_items=1,
            stop_reason="timeout",
        )
        prior_without_context = tuple(
            BatchItemOutcome(**{key: value for key, value in outcome.__dict__.items() if key != "request_cursor_context"})
            for outcome in first.item_outcomes
        )

        resumed = self.execute(
            request(first_item, second_item, resume_token=first.resume_token),
            sink=sink,
            prior_item_outcomes=prior_without_context,
        )

        self.assertEqual(resumed.result_status, BATCH_RESULT_COMPLETE)
        payload = batch_result_envelope_to_dict(resumed)
        self.assertEqual(payload["item_outcomes"][0]["outcome_status"], BATCH_ITEM_SUCCEEDED)
        self.assertNotIn("request_cursor_context", payload["item_outcomes"][0])

    def test_dataset_write_failure_is_failed_item(self) -> None:
        result = self.execute(request(target("item-1", "alpha")), sink=FailingDatasetSink())

        self.assertEqual(result.result_status, BATCH_RESULT_ALL_FAILED)
        self.assertEqual(result.item_outcomes[0].outcome_status, BATCH_ITEM_FAILED)
        self.assertIsNone(result.item_outcomes[0].dataset_record_ref)
        self.assertEqual(result.item_outcomes[0].error_envelope["code"], "dataset_write_failed")
        self.assertIsNotNone(result.item_outcomes[0].result_envelope)

    def test_dataset_sink_runtime_failure_is_failed_item(self) -> None:
        result = self.execute(request(target("item-1", "alpha")), sink=RuntimeFailingDatasetSink())

        self.assertEqual(result.result_status, BATCH_RESULT_ALL_FAILED)
        self.assertEqual(result.item_outcomes[0].outcome_status, BATCH_ITEM_FAILED)
        self.assertIsNone(result.item_outcomes[0].dataset_record_ref)
        self.assertEqual(result.item_outcomes[0].error_envelope["code"], "dataset_write_failed")
        self.assertEqual(result.item_outcomes[0].error_envelope["details"]["error_type"], "RuntimeError")
        self.assertNotIn("/private/storage", repr(result.item_outcomes[0].error_envelope))
        self.assertIsNotNone(result.item_outcomes[0].result_envelope)

    def test_dataset_sink_ref_without_sink_fails_closed(self) -> None:
        with mock.patch.dict("syvert.runtime.RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE", {}, clear=True):
            result = execute_batch_request(
                request(target("item-1", "alpha")),
                adapters=self.adapters,
                dataset_sink=None,
                task_id_factory=self.task_id,
                now_factory=now,
            )

        self.assertEqual(result.result_status, BATCH_RESULT_ALL_FAILED)
        self.assertEqual(result.item_outcomes[0].outcome_status, BATCH_ITEM_FAILED)
        self.assertEqual(result.item_outcomes[0].error_envelope["code"], "dataset_sink_unavailable")

    def test_batch_has_no_resource_precondition_but_item_uses_resource_governance(self) -> None:
        sink = ReferenceDatasetSink()

        result = execute_batch_request(
            request(target("item-1", "alpha")),
            adapters=self.adapters,
            dataset_sink=sink,
            task_id_factory=self.task_id,
            now_factory=now,
        )

        self.assertEqual(result.result_status, BATCH_RESULT_ALL_FAILED)
        self.assertEqual(result.item_outcomes[0].outcome_status, BATCH_ITEM_FAILED)
        self.assertEqual(result.item_outcomes[0].error_envelope["code"], "invalid_resource_requirement")
        self.assertEqual(sink.read_by_batch("batch-001"), ())

    def test_dataset_validator_rejects_non_json_normalized_payload(self) -> None:
        sink = ReferenceDatasetSink()
        bad = {
            "dataset_record_id": "record-1",
            "dataset_id": "dataset-1",
            "source_operation": "content_search_by_keyword",
            "adapter_key": TEST_ADAPTER_KEY,
            "target_ref": "alpha",
            "raw_payload_ref": "raw://alpha",
            "normalized_payload": {"bad": object()},
            "evidence_ref": "evidence:alpha",
            "source_trace": {
                "adapter_key": TEST_ADAPTER_KEY,
                "provider_path": "provider://sanitized",
                "fetched_at": "2026-05-13T10:00:00Z",
                "evidence_alias": "evidence:alpha",
            },
            "dedup_key": "dedup:alpha",
            "batch_id": "batch-001",
            "batch_item_id": "item-1",
            "recorded_at": "2026-05-13T10:00:00Z",
        }

        with self.assertRaises(BatchDatasetContractError) as context:
            sink.write(bad)

        self.assertEqual(context.exception.code, "non_json_safe_value")

    def test_dataset_validator_rejects_private_normalized_payload_fields(self) -> None:
        payloads = (
            {"items": [{"canonical_ref": "content://item-1", "raw_payload_ref": "raw://alpha"}]},
            {"items": [{"canonical_ref": "content://item-1", "Raw_Payload_Ref": "raw://alpha"}]},
            {"items": [{"canonical_ref": "content://item-1", "rawPayloadRef": "raw://alpha"}]},
            {"items": [{"canonical_ref": "content://item-1", "providerPath": "provider://raw"}]},
            {"items": [{"canonical_ref": "content://item-1", "sourceName": "private-source"}]},
            {"items": [{"canonical_ref": "content://item-1", "RAW_PAYLOAD": {"id": "raw"}}]},
            {"items": [{"canonical_ref": "content://item-1", "artifact": "/etc/passwd"}]},
            {"items": [{"canonical_ref": "content://item-1", "artifact": " /etc/passwd"}]},
            {"items": [{"canonical_ref": "content://item-1", "artifact": "storage://private-bucket/raw"}]},
        )
        for index, normalized_payload in enumerate(payloads, start=1):
            with self.subTest(index=index):
                with self.assertRaises(BatchDatasetContractError) as context:
                    ReferenceDatasetSink().write(
                        {
                            "dataset_record_id": f"record-{index}",
                            "dataset_id": "dataset-1",
                            "source_operation": "content_search_by_keyword",
                            "adapter_key": TEST_ADAPTER_KEY,
                            "target_ref": "alpha",
                            "raw_payload_ref": "raw://alpha",
                            "normalized_payload": normalized_payload,
                            "evidence_ref": "evidence:alpha",
                            "source_trace": {
                                "adapter_key": TEST_ADAPTER_KEY,
                                "provider_path": "provider://sanitized",
                                "fetched_at": "2026-05-13T10:00:00Z",
                                "evidence_alias": "evidence:alpha",
                            },
                            "dedup_key": f"dedup:alpha:{index}",
                            "batch_id": "batch-001",
                            "batch_item_id": "item-1",
                            "recorded_at": "2026-05-13T10:00:00Z",
                        }
                    )
                self.assertEqual(context.exception.code, "unsafe_normalized_payload")

    def test_runtime_dataset_normalized_payload_rejects_unsafe_string_values(self) -> None:
        self.adapters = {TEST_ADAPTER_KEY: UnsafeNormalizedPayloadAdapter()}
        sink = ReferenceDatasetSink()

        result = self.execute(request(target("item-1", "alpha")), sink=sink)

        self.assertEqual(result.result_status, BATCH_RESULT_ALL_FAILED)
        self.assertEqual(result.item_outcomes[0].outcome_status, BATCH_ITEM_FAILED)
        self.assertEqual(result.item_outcomes[0].error_envelope["code"], "invalid_adapter_success_payload")
        self.assertEqual(sink.read_by_batch("batch-001"), ())

    def test_runtime_dataset_allows_public_collection_canonical_ref_urls(self) -> None:
        self.adapters = {TEST_ADAPTER_KEY: PublicUrlCollectionAdapter()}
        sink = ReferenceDatasetSink()

        result = self.execute(request(target("item-1", "alpha")), sink=sink)

        self.assertEqual(result.result_status, BATCH_RESULT_COMPLETE)
        self.assertEqual(result.item_outcomes[0].outcome_status, BATCH_ITEM_SUCCEEDED)
        record = sink.read_by_batch("batch-001")[0]
        self.assertEqual(record.normalized_payload["items"][0]["source_ref"], "https://example.com/posts/1")
        self.assertEqual(record.normalized_payload["items"][0]["normalized"]["canonical_ref"], "https://example.com/posts/1")

    def test_dataset_normalized_payload_rejects_url_in_non_ref_or_private_url_ref(self) -> None:
        record = {
            "dataset_record_id": "record-1",
            "dataset_id": "dataset-1",
            "source_operation": "content_search_by_keyword",
            "adapter_key": TEST_ADAPTER_KEY,
            "target_ref": "alpha",
            "raw_payload_ref": "raw://alpha",
            "normalized_payload": {"items": []},
            "evidence_ref": "evidence:alpha",
            "source_trace": {
                "adapter_key": TEST_ADAPTER_KEY,
                "provider_path": "provider://sanitized",
                "fetched_at": "2026-05-13T10:00:00Z",
                "evidence_alias": "evidence:alpha",
            },
            "dedup_key": "dedup:alpha",
            "batch_id": "batch-001",
            "batch_item_id": "item-1",
            "recorded_at": "2026-05-13T10:00:00Z",
        }
        cases = (
            {"items": [{"artifact": "https://example.com/posts/1"}]},
            {"items": [{"normalized": {"canonical_ref": "https://storage.example/private/raw.json"}}]},
            {"items": [{"normalized": {"canonical_ref": "file:///Users/mc/private/raw.json"}}]},
            {"items": [{"normalized": {"source_ref": "storage://private-bucket/raw"}}]},
            {"items": [{"normalized": {"source_ref": "C:\\Users\\mc\\private\\raw.json"}}]},
        )

        for index, normalized_payload in enumerate(cases, start=1):
            with self.subTest(index=index):
                with self.assertRaises(BatchDatasetContractError) as context:
                    ReferenceDatasetSink().write({**record, "dataset_record_id": f"record-url-{index}", "normalized_payload": normalized_payload})

                self.assertEqual(context.exception.code, "unsafe_normalized_payload")

    def test_runtime_dataset_normalized_payload_strips_raw_fields(self) -> None:
        sink = ReferenceDatasetSink()

        self.execute(request(target("item-1", "alpha")), sink=sink)
        record = sink.read_by_batch("batch-001")[0]
        item_payload = record.normalized_payload["items"][0]

        self.assertNotIn("raw_payload_ref", item_payload)
        self.assertNotIn("source_trace", item_payload)

    def test_raw_storage_url_ref_is_rejected(self) -> None:
        with self.assertRaises(BatchDatasetContractError) as context:
            ReferenceDatasetSink().write(
                {
                    "dataset_record_id": "record-1",
                    "dataset_id": "dataset-1",
                    "source_operation": "content_search_by_keyword",
                    "adapter_key": TEST_ADAPTER_KEY,
                    "target_ref": "alpha",
                    "raw_payload_ref": "https://storage.example/raw.json",
                    "normalized_payload": {"items": []},
                    "evidence_ref": "evidence:alpha",
                    "source_trace": {
                        "adapter_key": TEST_ADAPTER_KEY,
                        "provider_path": "provider://sanitized",
                        "fetched_at": "2026-05-13T10:00:00Z",
                        "evidence_alias": "evidence:alpha",
                    },
                    "dedup_key": "dedup:alpha",
                    "batch_id": "batch-001",
                    "batch_item_id": "item-1",
                    "recorded_at": "2026-05-13T10:00:00Z",
                }
            )

        self.assertEqual(context.exception.code, "unsafe_ref")

        with self.assertRaises(BatchDatasetContractError) as whitespace_context:
            ReferenceDatasetSink().write(
                {
                    "dataset_record_id": "record-1",
                    "dataset_id": "dataset-1",
                    "source_operation": "content_search_by_keyword",
                    "adapter_key": TEST_ADAPTER_KEY,
                    "target_ref": "alpha",
                    "raw_payload_ref": " /etc/passwd",
                    "normalized_payload": {"items": []},
                    "evidence_ref": "evidence:alpha",
                    "source_trace": {
                        "adapter_key": TEST_ADAPTER_KEY,
                        "provider_path": "provider://sanitized",
                        "fetched_at": "2026-05-13T10:00:00Z",
                        "evidence_alias": "evidence:alpha",
                    },
                    "dedup_key": "dedup:alpha",
                    "batch_id": "batch-001",
                    "batch_item_id": "item-1",
                    "recorded_at": "2026-05-13T10:00:00Z",
                }
            )

        self.assertEqual(whitespace_context.exception.code, "unsafe_ref")

    def test_reference_sink_rejects_duplicate_dataset_record_id(self) -> None:
        sink = ReferenceDatasetSink()
        record = {
            "dataset_record_id": "record-1",
            "dataset_id": "dataset-1",
            "source_operation": "content_search_by_keyword",
            "adapter_key": TEST_ADAPTER_KEY,
            "target_ref": "alpha",
            "raw_payload_ref": "raw://alpha",
            "normalized_payload": {"items": []},
            "evidence_ref": "evidence:alpha",
            "source_trace": {
                "adapter_key": TEST_ADAPTER_KEY,
                "provider_path": "provider://sanitized",
                "fetched_at": "2026-05-13T10:00:00Z",
                "evidence_alias": "evidence:alpha",
            },
            "dedup_key": "dedup:alpha",
            "batch_id": "batch-001",
            "batch_item_id": "item-1",
            "recorded_at": "2026-05-13T10:00:00Z",
        }

        sink.write(record)
        with self.assertRaises(BatchDatasetContractError) as context:
            sink.write({**record, "dedup_key": "dedup:beta", "batch_item_id": "item-2"})

        self.assertEqual(context.exception.code, "duplicate_dataset_record")
        self.assertEqual(context.exception.details["dataset_record_id"], "record-1")

    def test_local_absolute_path_ref_is_rejected_but_raw_alias_is_allowed(self) -> None:
        sink = ReferenceDatasetSink()
        record = sink.write(
            {
                "dataset_record_id": "record-1",
                "dataset_id": "dataset-1",
                "source_operation": "content_search_by_keyword",
                "adapter_key": TEST_ADAPTER_KEY,
                "target_ref": "alpha",
                "raw_payload_ref": "raw://alpha",
                "normalized_payload": {"items": []},
                "evidence_ref": "evidence:alpha",
                "source_trace": {
                    "adapter_key": TEST_ADAPTER_KEY,
                    "provider_path": "provider://sanitized",
                    "fetched_at": "2026-05-13T10:00:00Z",
                    "evidence_alias": "evidence:alpha",
                },
                "dedup_key": "dedup:alpha",
                "batch_id": "batch-001",
                "batch_item_id": "item-1",
                "recorded_at": "2026-05-13T10:00:00Z",
            }
        )
        self.assertEqual(record.raw_payload_ref, "raw://alpha")

        for local_path in ("/home/me/raw.json", "/etc/passwd"):
            with self.subTest(local_path=local_path):
                with self.assertRaises(BatchDatasetContractError) as context:
                    ReferenceDatasetSink().write(
                        {
                            "dataset_record_id": f"record-{local_path.rsplit('/', 1)[-1]}",
                            "dataset_id": "dataset-1",
                            "source_operation": "content_search_by_keyword",
                            "adapter_key": TEST_ADAPTER_KEY,
                            "target_ref": "alpha",
                            "raw_payload_ref": local_path,
                            "normalized_payload": {"items": []},
                            "evidence_ref": "evidence:alpha",
                            "source_trace": {
                                "adapter_key": TEST_ADAPTER_KEY,
                                "provider_path": "provider://sanitized",
                                "fetched_at": "2026-05-13T10:00:00Z",
                                "evidence_alias": "evidence:alpha",
                            },
                            "dedup_key": f"dedup:{local_path.rsplit('/', 1)[-1]}",
                            "batch_id": "batch-001",
                            "batch_item_id": "item-1",
                            "recorded_at": "2026-05-13T10:00:00Z",
                        }
                    )
                self.assertEqual(context.exception.code, "unsafe_ref")

    def test_prefixed_local_path_refs_are_rejected_in_public_carriers(self) -> None:
        base_record = {
            "dataset_record_id": "record-1",
            "dataset_id": "dataset-1",
            "source_operation": "content_search_by_keyword",
            "adapter_key": TEST_ADAPTER_KEY,
            "target_ref": "alpha",
            "raw_payload_ref": "raw://alpha",
            "normalized_payload": {"items": []},
            "evidence_ref": "evidence:alpha",
            "source_trace": {
                "adapter_key": TEST_ADAPTER_KEY,
                "provider_path": "provider://sanitized",
                "fetched_at": "2026-05-13T10:00:00Z",
                "evidence_alias": "evidence:alpha",
            },
            "dedup_key": "dedup:alpha",
            "batch_id": "batch-001",
            "batch_item_id": "item-1",
            "recorded_at": "2026-05-13T10:00:00Z",
        }
        dataset_cases = (
            ("raw_payload_ref", "raw:///etc/passwd"),
            ("evidence_ref", "evidence:/etc/passwd"),
            ("dataset_record_id", "record:/home/me/raw.json"),
            ("dataset_id", "dataset:/home/me/raw.json"),
        )
        for field, value in dataset_cases:
            with self.subTest(field=field):
                with self.assertRaises(BatchDatasetContractError) as context:
                    ReferenceDatasetSink().write({**base_record, field: value})

                self.assertEqual(context.exception.code, "unsafe_ref")

        result = self.execute(request(target("item-1", "alpha")))
        with self.assertRaises(BatchDatasetContractError) as outcome_context:
            validate_batch_item_outcome(
                BatchItemOutcome(
                    **{
                        **result.item_outcomes[0].__dict__,
                        "dataset_record_ref": "record:/etc/passwd",
                    }
                )
            )
        self.assertEqual(outcome_context.exception.code, "unsafe_ref")

        with self.assertRaises(BatchDatasetContractError) as envelope_context:
            batch_result_envelope_to_dict(
                BatchResultEnvelope(
                    batch_id=result.batch_id,
                    operation=result.operation,
                    result_status=result.result_status,
                    item_outcomes=result.item_outcomes,
                    resume_token=result.resume_token,
                    dataset_sink_ref=result.dataset_sink_ref,
                    dataset_id="dataset:/home/me/raw.json",
                    audit_trace=result.audit_trace,
                )
            )
        self.assertEqual(envelope_context.exception.code, "unsafe_ref")

    def test_sanitized_provider_path_is_allowed_but_raw_path_rejected(self) -> None:
        result = self.execute(request(target("item-1", "alpha")))
        record = ReferenceDatasetSink().write(
            {
                "dataset_record_id": "record-1",
                "dataset_id": "dataset-1",
                "source_operation": "content_search_by_keyword",
                "adapter_key": TEST_ADAPTER_KEY,
                "target_ref": "alpha",
                "raw_payload_ref": "raw://alpha",
                "normalized_payload": {"items": []},
                "evidence_ref": "evidence:alpha",
                "source_trace": {
                    "adapter_key": TEST_ADAPTER_KEY,
                    "provider_path": "provider://sanitized",
                    "fetched_at": "2026-05-13T10:00:00Z",
                    "evidence_alias": "evidence:alpha",
                },
                "dedup_key": "dedup:alpha",
                "batch_id": "batch-001",
                "batch_item_id": "item-1",
                "recorded_at": "2026-05-13T10:00:00Z",
            }
        )
        self.assertEqual(record.source_trace["provider_path"], "provider://sanitized")
        for invalid_number in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(invalid_number=invalid_number):
                with self.assertRaises(BatchDatasetContractError) as json_context:
                    validate_dataset_record(
                        type(record)(
                            **{
                                **record.__dict__,
                                "dataset_record_id": f"record-non-finite-{repr(invalid_number)}",
                                "normalized_payload": {"score": invalid_number},
                            }
                        )
                    )
                self.assertEqual(json_context.exception.code, "non_json_safe_value")
        with self.assertRaises(BatchDatasetContractError) as timestamp_context:
            validate_dataset_record(
                type(record)(
                    **{
                        **record.__dict__,
                        "dataset_record_id": "record-invalid-fetched-at",
                        "source_trace": {**record.source_trace, "fetched_at": "/etc/passwd"},
                    }
                )
            )
        self.assertEqual(timestamp_context.exception.code, "invalid_timestamp")
        with self.assertRaises(BatchDatasetContractError) as mapping_timestamp_context:
            ReferenceDatasetSink().write(
                {
                    "dataset_record_id": "record-mapping-invalid-recorded-at",
                    "dataset_id": "dataset-1",
                    "source_operation": "content_search_by_keyword",
                    "adapter_key": TEST_ADAPTER_KEY,
                    "target_ref": "alpha",
                    "raw_payload_ref": "raw://alpha",
                    "normalized_payload": {"items": []},
                    "evidence_ref": "evidence:alpha",
                    "source_trace": {
                        "adapter_key": TEST_ADAPTER_KEY,
                        "provider_path": "provider://sanitized",
                        "fetched_at": "2026-05-13T10:00:00Z",
                        "evidence_alias": "evidence:alpha",
                    },
                    "dedup_key": "dedup:alpha-mapping",
                    "batch_id": "batch-001",
                    "batch_item_id": "item-1",
                    "recorded_at": "/etc/passwd",
                }
            )
        self.assertEqual(mapping_timestamp_context.exception.code, "invalid_timestamp")
        with self.assertRaises(BatchDatasetContractError):
            validate_dataset_record(
                type(record)(
                    **{
                        **record.__dict__,
                        "dataset_record_id": "record-2",
                        "source_trace": {**record.source_trace, "provider_path": "https://provider.example/route"},
                    }
                )
            )
        for local_path in ("/home/me/provider-route", "/etc/provider-route", "C:/work/provider-route", "D:\\exports\\provider-route"):
            with self.subTest(local_path=local_path):
                with self.assertRaises(BatchDatasetContractError):
                    validate_dataset_record(
                        type(record)(
                            **{
                                **record.__dict__,
                                "dataset_record_id": f"record-{local_path.rsplit('/', 1)[-1]}",
                                "source_trace": {**record.source_trace, "provider_path": local_path},
                            }
                        )
                    )
        for field, value, code in (
            ("raw_payload_ref", "C:/work/raw.json", "unsafe_ref"),
            ("evidence_ref", "D:/exports/evidence.json", "unsafe_ref"),
            ("normalized_payload", {"artifact": "C:/work/cache.json"}, "unsafe_normalized_payload"),
        ):
            with self.subTest(field=field):
                with self.assertRaises(BatchDatasetContractError) as local_path_context:
                    validate_dataset_record(type(record)(**{**record.__dict__, "dataset_record_id": f"record-windows-{field}", field: value}))

                self.assertEqual(local_path_context.exception.code, code)
        with self.assertRaises(BatchDatasetContractError):
            validate_dataset_record(
                type(record)(
                    **{
                        **record.__dict__,
                        "dataset_record_id": "record-whitespace-path",
                        "source_trace": {**record.source_trace, "provider_path": " /etc/provider-route"},
                    }
                )
            )
        for provider_path in (
            "storage://private-bucket/raw",
            "s3://private-bucket/raw",
            "provider:account-pool:main",
            "provider:proxy-pool:main",
            "provider:route:main",
            "provider:routing:main",
            "provider:fallback:route",
            "provider:marketplace:route",
            "provider:credential:route",
            "provider:signed-download-bucket",
            "provider:sanitized:download-bucket-public",
            "provider:sanitized:private-download-bucket",
            "provider:sanitized:raw-route",
            "provider:token=secret",
        ):
            with self.subTest(provider_path=provider_path):
                with self.assertRaises(BatchDatasetContractError):
                    validate_dataset_record(
                        type(record)(
                            **{
                                **record.__dict__,
                                "dataset_record_id": f"record-{abs(hash(provider_path))}",
                                "source_trace": {**record.source_trace, "provider_path": provider_path},
                            }
                        )
                    )

    def test_source_trace_rejects_private_extra_fields(self) -> None:
        with self.assertRaises(BatchDatasetContractError) as context:
            ReferenceDatasetSink().write(
                {
                    "dataset_record_id": "record-1",
                    "dataset_id": "dataset-1",
                    "source_operation": "content_search_by_keyword",
                    "adapter_key": TEST_ADAPTER_KEY,
                    "target_ref": "alpha",
                    "raw_payload_ref": "raw://alpha",
                    "normalized_payload": {"items": []},
                    "evidence_ref": "evidence:alpha",
                    "source_trace": {
                        "adapter_key": TEST_ADAPTER_KEY,
                        "provider_path": "provider://sanitized",
                        "fetched_at": "2026-05-13T10:00:00Z",
                        "evidence_alias": "evidence:alpha",
                        "storage_handle": "opaque-storage-handle",
                    },
                    "dedup_key": "dedup:alpha",
                    "batch_id": "batch-001",
                    "batch_item_id": "item-1",
                    "recorded_at": "2026-05-13T10:00:00Z",
                }
            )

        self.assertEqual(context.exception.code, "unsafe_source_trace")

    def test_batch_item_outcome_does_not_expose_unsafe_source_trace_without_dataset_sink(self) -> None:
        self.adapters = {TEST_ADAPTER_KEY: UnsafeSourceTraceAdapter()}

        result = self.execute(
            BatchRequest(
                batch_id="batch-001",
                target_set=(target("item-1", "alpha"),),
                dataset_sink_ref=None,
                audit_context={"evidence_ref": "evidence:batch"},
            )
        )

        self.assertEqual(result.result_status, BATCH_RESULT_ALL_FAILED)
        self.assertEqual(result.item_outcomes[0].outcome_status, BATCH_ITEM_FAILED)
        self.assertIsNone(result.item_outcomes[0].source_trace)
        self.assertEqual(result.item_outcomes[0].error_envelope["code"], "invalid_adapter_success_payload")

    def test_batch_item_outcome_rejects_invalid_source_trace_timestamp(self) -> None:
        result = self.execute(request(target("item-1", "alpha")))
        forged = BatchItemOutcome(
            **{
                **result.item_outcomes[0].__dict__,
                "source_trace": {**result.item_outcomes[0].source_trace, "fetched_at": "/etc/passwd"},
            }
        )

        with self.assertRaises(BatchDatasetContractError) as context:
            validate_batch_item_outcome(forged)

        self.assertEqual(context.exception.code, "invalid_timestamp")

    def test_batch_item_outcome_allows_plain_error_and_audit_text(self) -> None:
        outcome = BatchItemOutcome(
            item_id="item-1",
            operation="content_search_by_keyword",
            adapter_key=TEST_ADAPTER_KEY,
            target_ref="alpha",
            outcome_status=BATCH_ITEM_FAILED,
            error_envelope={
                "code": "adapter_unavailable",
                "message": "fallback unavailable",
                "details": {"reason": "selector returned no marketplace match"},
            },
            audit={"reason": "fallback unavailable"},
        )

        validate_batch_item_outcome(outcome)

    def test_audit_context_evidence_ref_must_be_sanitized(self) -> None:
        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                BatchRequest(
                    batch_id="batch-001",
                    target_set=(target("item-1", "alpha"),),
                    dataset_sink_ref="dataset-sink:reference",
                    audit_context={"evidence_ref": "file:///tmp/raw-payload.json"},
                )
            )

        self.assertEqual(context.exception.code, "unsafe_ref")

        with self.assertRaises(BatchDatasetContractError) as non_string_context:
            self.execute(
                BatchRequest(
                    batch_id="batch-001",
                    target_set=(target("item-1", "alpha"),),
                    dataset_sink_ref="dataset-sink:reference",
                    audit_context={"evidence_ref": {"alias": "evidence:batch"}},
                )
            )

        self.assertEqual(non_string_context.exception.code, "invalid_field")

        with self.assertRaises(BatchDatasetContractError) as whitespace_context:
            self.execute(
                BatchRequest(
                    batch_id="batch-001",
                    target_set=(target("item-1", "alpha"),),
                    dataset_sink_ref="dataset-sink:reference",
                    audit_context={"evidence_ref": " file:///tmp/raw-payload.json"},
                )
            )

        self.assertEqual(whitespace_context.exception.code, "unsafe_ref")

    def test_source_trace_alias_fields_must_be_strings(self) -> None:
        with self.assertRaises(BatchDatasetContractError) as context:
            ReferenceDatasetSink().write(
                {
                    "dataset_record_id": "record-1",
                    "dataset_id": "dataset-1",
                    "source_operation": "content_search_by_keyword",
                    "adapter_key": TEST_ADAPTER_KEY,
                    "target_ref": "alpha",
                    "raw_payload_ref": "raw://alpha",
                    "normalized_payload": {"items": []},
                    "evidence_ref": "evidence:alpha",
                    "source_trace": {
                        "adapter_key": TEST_ADAPTER_KEY,
                        "provider_path": "provider://sanitized",
                        "fetched_at": "2026-05-13T10:00:00Z",
                        "evidence_alias": "evidence:alpha",
                        "resource_profile_ref": {"profile": "resource:public"},
                    },
                    "dedup_key": "dedup:alpha",
                    "batch_id": "batch-001",
                    "batch_item_id": "item-1",
                    "recorded_at": "2026-05-13T10:00:00Z",
                }
            )

        self.assertEqual(context.exception.code, "invalid_field")


if __name__ == "__main__":
    unittest.main()
