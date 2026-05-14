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
    BatchResumeToken,
    BatchTargetItem,
    ReferenceDatasetSink,
    batch_result_envelope_to_dict,
    batch_target_set_hash,
    execute_batch_request,
    validate_dataset_record,
)
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


class FailingDatasetSink(ReferenceDatasetSink):
    def write(self, record):
        raise BatchDatasetContractError(
            "dataset_write_failed",
            "write failed",
            details={"evidence_ref": "evidence:dataset-write-failed"},
        )


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


def request(*items: BatchTargetItem, resume_token: BatchResumeToken | None = None) -> BatchRequest:
    return BatchRequest(
        batch_id="batch-001",
        target_set=items,
        resume_token=resume_token,
        dataset_sink_ref="dataset-sink:reference",
        audit_context={"evidence_ref": "evidence:batch"},
    )


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

    def test_all_failed_has_no_dataset_records(self) -> None:
        self.adapters = {TEST_ADAPTER_KEY: FailingCollectionAdapter()}
        sink = ReferenceDatasetSink()

        result = self.execute(request(target("item-1", "alpha")), sink=sink)

        self.assertEqual(result.result_status, BATCH_RESULT_ALL_FAILED)
        self.assertEqual(result.item_outcomes[0].outcome_status, BATCH_ITEM_FAILED)
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

    def test_search_request_cursor_is_rejected_instead_of_silently_dropped(self) -> None:
        with self.assertRaises(BatchDatasetContractError) as context:
            self.execute(
                request(
                    BatchTargetItem(
                        item_id="item-1",
                        operation="content_search_by_keyword",
                        adapter_key=TEST_ADAPTER_KEY,
                        target_type="keyword",
                        target_ref="alpha",
                        dedup_key="dedup:alpha",
                        request_cursor={"continuation_token": "next-page"},
                    )
                )
            )

        self.assertEqual(context.exception.code, "unsupported_request_cursor")

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

    def test_dataset_write_failure_is_failed_item(self) -> None:
        result = self.execute(request(target("item-1", "alpha")), sink=FailingDatasetSink())

        self.assertEqual(result.result_status, BATCH_RESULT_ALL_FAILED)
        self.assertEqual(result.item_outcomes[0].outcome_status, BATCH_ITEM_FAILED)
        self.assertIsNone(result.item_outcomes[0].dataset_record_ref)
        self.assertEqual(result.item_outcomes[0].error_envelope["code"], "dataset_write_failed")
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
        with self.assertRaises(BatchDatasetContractError) as context:
            ReferenceDatasetSink().write(
                {
                    "dataset_record_id": "record-1",
                    "dataset_id": "dataset-1",
                    "source_operation": "content_search_by_keyword",
                    "adapter_key": TEST_ADAPTER_KEY,
                    "target_ref": "alpha",
                    "raw_payload_ref": "raw://alpha",
                    "normalized_payload": {
                        "items": [
                            {
                                "canonical_ref": "content://item-1",
                                "raw_payload_ref": "https://storage.example/raw.json",
                            }
                        ]
                    },
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


if __name__ == "__main__":
    unittest.main()
