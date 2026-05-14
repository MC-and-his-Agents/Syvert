from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any
from uuid import uuid4

from syvert.runtime import TaskInput, TaskRequest, execute_task


BATCH_EXECUTION_OPERATION = "batch_execution"
BATCH_RESULT_COMPLETE = "complete"
BATCH_RESULT_PARTIAL_SUCCESS = "partial_success"
BATCH_RESULT_ALL_FAILED = "all_failed"
BATCH_RESULT_RESUMABLE = "resumable"
BATCH_ITEM_SUCCEEDED = "succeeded"
BATCH_ITEM_FAILED = "failed"
BATCH_ITEM_DUPLICATE_SKIPPED = "duplicate_skipped"
DATASET_WRITE_FAILED = "dataset_write_failed"
DATASET_SINK_UNAVAILABLE = "dataset_sink_unavailable"
STOP_BOUNDARY_ERROR_CODES = frozenset(
    {
        "execution_timeout",
        "execution_cancelled",
        "task_cancelled",
        "cancelled",
    }
)

ALLOWED_BATCH_ITEM_OPERATIONS = frozenset(
    {
        "content_search_by_keyword",
        "content_list_by_creator",
        "comment_collection",
        "creator_profile_by_id",
        "media_asset_fetch_by_ref",
    }
)

TARGET_TYPE_BY_OPERATION = {
    "content_search_by_keyword": "keyword",
    "content_list_by_creator": "creator",
    "comment_collection": "content",
    "creator_profile_by_id": "creator",
    "media_asset_fetch_by_ref": "media_ref",
}

_FORBIDDEN_REF_TOKENS = (
    "http://",
    "https://",
    "s3://",
    "gs://",
    "storage://",
    "file://",
    "/tmp/",
    "/var/",
    "/users/",
    "\\",
    "token=",
    "secret",
    "credential",
    "signed",
    "bucket",
    "download",
    "selector",
    "fallback",
    "marketplace",
    "account-pool",
    "proxy-pool",
)
_FORBIDDEN_PUBLIC_PAYLOAD_KEY_TOKENS = (
    "storage_handle",
    "storage_url",
    "download_url",
    "local_path",
    "file_path",
    "source_name",
    "provider_path",
    "account_material",
    "account_secret",
    "private_account",
    "private_creator",
    "private_media",
    "cookie",
    "credential",
    "session_token",
)
_FORBIDDEN_NORMALIZED_PAYLOAD_KEYS = frozenset(
    {
        "raw_payload",
        "raw_payload_ref",
        "source_trace",
        "provider_path",
        "storage_handle",
        "storage_url",
        "download_url",
        "local_path",
        "file_path",
        "source_name",
    }
)
_ALLOWED_SOURCE_TRACE_FIELDS = frozenset(
    {"adapter_key", "provider_path", "fetched_at", "evidence_alias", "resource_profile_ref"}
)


class BatchDatasetContractError(ValueError):
    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})


@dataclass(frozen=True)
class BatchTargetItem:
    item_id: str
    operation: str
    adapter_key: str
    target_type: str
    target_ref: str
    dedup_key: str
    request_cursor: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class BatchResumeToken:
    resume_token: str
    batch_id: str
    target_set_hash: str
    next_item_index: int
    issued_at: str


@dataclass(frozen=True)
class BatchRequest:
    batch_id: str
    target_set: Sequence[BatchTargetItem]
    resume_token: BatchResumeToken | None = None
    dataset_sink_ref: str | None = None
    dataset_id: str | None = None
    audit_context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BatchItemOutcome:
    item_id: str
    operation: str
    adapter_key: str
    target_ref: str
    outcome_status: str
    result_envelope: Mapping[str, Any] | None = None
    error_envelope: Mapping[str, Any] | None = None
    dataset_record_ref: str | None = None
    source_trace: Mapping[str, Any] | None = None
    audit: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DatasetRecord:
    dataset_record_id: str
    dataset_id: str
    source_operation: str
    adapter_key: str
    target_ref: str
    raw_payload_ref: str | None
    normalized_payload: Any
    evidence_ref: str
    source_trace: Mapping[str, Any]
    dedup_key: str
    batch_id: str
    batch_item_id: str
    recorded_at: str


@dataclass(frozen=True)
class BatchResultEnvelope:
    batch_id: str
    operation: str
    result_status: str
    item_outcomes: tuple[BatchItemOutcome, ...]
    resume_token: BatchResumeToken | None = None
    dataset_sink_ref: str | None = None
    dataset_id: str | None = None
    audit_trace: Mapping[str, Any] = field(default_factory=dict)


class ReferenceDatasetSink:
    def __init__(self) -> None:
        self._records: list[DatasetRecord] = []
        self._dedup_keys: set[tuple[str, str]] = set()

    def write(self, record: DatasetRecord | Mapping[str, Any]) -> DatasetRecord:
        normalized = canonical_dataset_record(record)
        dedup_identity = (normalized.dataset_id, normalized.dedup_key)
        if dedup_identity in self._dedup_keys:
            raise BatchDatasetContractError(
                "duplicate_dataset_record",
                "dataset sink first-wins dedup_key already exists",
                details={"dataset_id": normalized.dataset_id, "dedup_key": normalized.dedup_key},
            )
        self._records.append(normalized)
        self._dedup_keys.add(dedup_identity)
        return normalized

    def read_by_dataset(self, dataset_id: str) -> tuple[DatasetRecord, ...]:
        dataset_id = _require_non_empty_string(dataset_id, field="dataset_id")
        return tuple(record for record in self._records if record.dataset_id == dataset_id)

    def read_by_batch(self, batch_id: str) -> tuple[DatasetRecord, ...]:
        batch_id = _require_non_empty_string(batch_id, field="batch_id")
        return tuple(record for record in self._records if record.batch_id == batch_id)

    def audit_replay(self, dataset_id: str) -> tuple[Mapping[str, Any], ...]:
        return tuple(
            {
                "dataset_record_id": record.dataset_record_id,
                "dataset_id": record.dataset_id,
                "batch_id": record.batch_id,
                "batch_item_id": record.batch_item_id,
                "source_operation": record.source_operation,
                "adapter_key": record.adapter_key,
                "target_ref": record.target_ref,
                "evidence_ref": record.evidence_ref,
                "dedup_key": record.dedup_key,
                "normalized_payload": record.normalized_payload,
            }
            for record in self.read_by_dataset(dataset_id)
        )


def execute_batch_request(
    request: BatchRequest,
    *,
    adapters: Mapping[str, Any],
    dataset_sink: ReferenceDatasetSink | None = None,
    task_id_factory: Callable[[], str] | None = None,
    now_factory: Callable[[], datetime] | None = None,
    prior_item_outcomes: Sequence[BatchItemOutcome] = (),
    stop_after_items: int | None = None,
    stop_reason: str = "interrupted",
) -> BatchResultEnvelope:
    validated = validate_batch_request(request)
    target_set_hash = batch_target_set_hash(validated.target_set)
    start_index = 0
    if validated.resume_token is not None:
        _validate_resume_token(validated.resume_token, request=validated, target_set_hash=target_set_hash)
        start_index = validated.resume_token.next_item_index
    outcomes = list(_canonical_item_outcomes(prior_item_outcomes))
    dataset_id = _dataset_id_for_request(validated)
    now = now_factory or (lambda: datetime.now(timezone.utc))
    started_at = now().isoformat().replace("+00:00", "Z")
    if len(outcomes) != start_index:
        raise BatchDatasetContractError(
            "resume_outcome_prefix_mismatch",
            "prior item outcomes must match resume_token.next_item_index",
            details={"prior_outcomes": len(outcomes), "next_item_index": start_index},
        )
    if start_index:
        _validate_resume_outcome_prefix(
            validated,
            outcomes=outcomes,
            dataset_id=dataset_id,
            dataset_sink=dataset_sink,
            next_item_index=start_index,
        )
    seen_dedup_keys = {validated.target_set[index].dedup_key for index in range(min(start_index, len(validated.target_set)))}
    task_id_factory = task_id_factory or (lambda: f"batch-item-{uuid4().hex}")
    stop_at = stop_after_items if stop_after_items is not None else len(validated.target_set)

    for index in range(start_index, len(validated.target_set)):
        if index >= stop_at:
            return _resumable_result(
                validated,
                outcomes=outcomes,
                target_set_hash=target_set_hash,
                next_item_index=index,
                dataset_id=dataset_id,
                started_at=started_at,
                now=now,
                stop_reason=stop_reason,
            )
        item = validated.target_set[index]
        if item.dedup_key in seen_dedup_keys:
            outcomes.append(
                BatchItemOutcome(
                    item_id=item.item_id,
                    operation=item.operation,
                    adapter_key=item.adapter_key,
                    target_ref=item.target_ref,
                    outcome_status=BATCH_ITEM_DUPLICATE_SKIPPED,
                    audit={"reason": "duplicate_dedup_key", "dedup_key": item.dedup_key},
                )
            )
            continue
        seen_dedup_keys.add(item.dedup_key)
        envelope = execute_task(
            _task_request_from_batch_item(item),
            adapters=adapters,
            task_id_factory=task_id_factory,
        )
        outcome = _outcome_from_task_envelope(
            item,
            envelope,
            request=validated,
            dataset_id=dataset_id,
            dataset_sink=dataset_sink,
            now=now,
        )
        outcomes.append(outcome)
        if _is_stop_boundary_outcome(outcome) and index + 1 < len(validated.target_set):
            return _resumable_result(
                validated,
                outcomes=outcomes,
                target_set_hash=target_set_hash,
                next_item_index=index + 1,
                dataset_id=dataset_id,
                started_at=started_at,
                now=now,
                stop_reason=str((outcome.error_envelope or {}).get("code") or "execution_interrupted"),
            )

    return BatchResultEnvelope(
        batch_id=validated.batch_id,
        operation=BATCH_EXECUTION_OPERATION,
        result_status=_aggregate_batch_result(outcomes),
        item_outcomes=tuple(outcomes),
        dataset_sink_ref=validated.dataset_sink_ref,
        dataset_id=dataset_id,
        audit_trace=_batch_audit_trace(
            validated,
            outcomes=outcomes,
            started_at=started_at,
            finished=True,
        ),
    )


def validate_batch_request(request: BatchRequest) -> BatchRequest:
    if not isinstance(request, BatchRequest):
        raise BatchDatasetContractError("invalid_batch_request", "BatchRequest expected")
    _require_non_empty_string(request.batch_id, field="batch_id")
    if not request.target_set:
        raise BatchDatasetContractError("empty_target_set", "BatchRequest.target_set must not be empty")
    for index, item in enumerate(request.target_set):
        validate_batch_target_item(item, index=index)
    if request.dataset_sink_ref is not None:
        _validate_sanitized_ref(request.dataset_sink_ref, field="dataset_sink_ref")
    if request.dataset_id is not None:
        _validate_sanitized_ref(request.dataset_id, field="dataset_id")
    _ensure_json_safe(request.audit_context, field="audit_context")
    _audit_context_evidence_refs(request.audit_context)
    return request


def validate_batch_target_item(item: BatchTargetItem, *, index: int = 0) -> BatchTargetItem:
    if not isinstance(item, BatchTargetItem):
        raise BatchDatasetContractError("invalid_target_item", "BatchTargetItem expected", details={"index": index})
    _require_non_empty_string(item.item_id, field="item_id")
    _validate_sanitized_ref(item.adapter_key, field="adapter_key")
    if item.operation not in ALLOWED_BATCH_ITEM_OPERATIONS:
        raise BatchDatasetContractError(
            "invalid_target_operation",
            "batch target operation is not an admitted read-side operation",
            details={"operation": item.operation, "index": index},
        )
    expected_target_type = TARGET_TYPE_BY_OPERATION[item.operation]
    if item.target_type != expected_target_type:
        raise BatchDatasetContractError(
            "invalid_target_type",
            "batch target_type does not match operation",
            details={"operation": item.operation, "target_type": item.target_type, "expected": expected_target_type},
        )
    _validate_sanitized_ref(item.target_ref, field="target_ref")
    _validate_sanitized_ref(item.dedup_key, field="dedup_key")
    if item.request_cursor is not None:
        _ensure_json_safe(item.request_cursor, field="request_cursor")
        if item.operation in {"content_search_by_keyword", "content_list_by_creator", "creator_profile_by_id"}:
            raise BatchDatasetContractError(
                "unsupported_request_cursor",
                "batch request_cursor is not yet supported for this item operation",
                details={"operation": item.operation, "index": index},
            )
    return item


def canonical_dataset_record(record: DatasetRecord | Mapping[str, Any]) -> DatasetRecord:
    if isinstance(record, DatasetRecord):
        normalized = record
    elif isinstance(record, Mapping):
        normalized = DatasetRecord(
            dataset_record_id=_require_non_empty_string(record.get("dataset_record_id"), field="dataset_record_id"),
            dataset_id=_require_non_empty_string(record.get("dataset_id"), field="dataset_id"),
            source_operation=_require_non_empty_string(record.get("source_operation"), field="source_operation"),
            adapter_key=_require_non_empty_string(record.get("adapter_key"), field="adapter_key"),
            target_ref=_require_non_empty_string(record.get("target_ref"), field="target_ref"),
            raw_payload_ref=record.get("raw_payload_ref") if record.get("raw_payload_ref") is not None else None,
            normalized_payload=record.get("normalized_payload"),
            evidence_ref=_require_non_empty_string(record.get("evidence_ref"), field="evidence_ref"),
            source_trace=_require_mapping(record.get("source_trace"), field="source_trace"),
            dedup_key=_require_non_empty_string(record.get("dedup_key"), field="dedup_key"),
            batch_id=_require_non_empty_string(record.get("batch_id"), field="batch_id"),
            batch_item_id=_require_non_empty_string(record.get("batch_item_id"), field="batch_item_id"),
            recorded_at=_require_non_empty_string(record.get("recorded_at"), field="recorded_at"),
        )
    else:
        raise BatchDatasetContractError("invalid_dataset_record", "DatasetRecord expected")
    validate_dataset_record(normalized)
    return normalized


def validate_dataset_record(record: DatasetRecord) -> DatasetRecord:
    _validate_sanitized_ref(record.dataset_record_id, field="dataset_record_id")
    _validate_sanitized_ref(record.dataset_id, field="dataset_id")
    if record.source_operation not in ALLOWED_BATCH_ITEM_OPERATIONS:
        raise BatchDatasetContractError("invalid_source_operation", "dataset source_operation is not admitted")
    _validate_sanitized_ref(record.adapter_key, field="adapter_key")
    _validate_sanitized_ref(record.target_ref, field="target_ref")
    if record.raw_payload_ref is not None:
        _validate_sanitized_ref(record.raw_payload_ref, field="raw_payload_ref")
    _ensure_json_safe(record.normalized_payload, field="normalized_payload")
    _validate_normalized_payload_no_leakage(record.normalized_payload, field="normalized_payload")
    _validate_sanitized_ref(record.evidence_ref, field="evidence_ref")
    _validate_source_trace(record.source_trace)
    _validate_sanitized_ref(record.dedup_key, field="dedup_key")
    _validate_sanitized_ref(record.batch_id, field="batch_id")
    _validate_sanitized_ref(record.batch_item_id, field="batch_item_id")
    _require_non_empty_string(record.recorded_at, field="recorded_at")
    return record


def batch_result_envelope_to_dict(envelope: BatchResultEnvelope) -> dict[str, Any]:
    return {
        "batch_id": envelope.batch_id,
        "operation": envelope.operation,
        "result_status": envelope.result_status,
        "item_outcomes": [batch_item_outcome_to_dict(outcome) for outcome in envelope.item_outcomes],
        **({"resume_token": batch_resume_token_to_dict(envelope.resume_token)} if envelope.resume_token else {}),
        **({"dataset_sink_ref": envelope.dataset_sink_ref} if envelope.dataset_sink_ref else {}),
        **({"dataset_id": envelope.dataset_id} if envelope.dataset_id else {}),
        "audit_trace": dict(envelope.audit_trace),
    }


def batch_item_outcome_to_dict(outcome: BatchItemOutcome) -> dict[str, Any]:
    validate_batch_item_outcome(outcome)
    return {
        "item_id": outcome.item_id,
        "operation": outcome.operation,
        "adapter_key": outcome.adapter_key,
        "target_ref": outcome.target_ref,
        "outcome_status": outcome.outcome_status,
        **({"result_envelope": dict(outcome.result_envelope)} if outcome.result_envelope is not None else {}),
        **({"error_envelope": dict(outcome.error_envelope)} if outcome.error_envelope is not None else {}),
        **({"dataset_record_ref": outcome.dataset_record_ref} if outcome.dataset_record_ref is not None else {}),
        **({"source_trace": dict(outcome.source_trace)} if outcome.source_trace is not None else {}),
        "audit": dict(outcome.audit),
    }


def dataset_record_to_dict(record: DatasetRecord) -> dict[str, Any]:
    validate_dataset_record(record)
    return {
        "dataset_record_id": record.dataset_record_id,
        "dataset_id": record.dataset_id,
        "source_operation": record.source_operation,
        "adapter_key": record.adapter_key,
        "target_ref": record.target_ref,
        "raw_payload_ref": record.raw_payload_ref,
        "normalized_payload": record.normalized_payload,
        "evidence_ref": record.evidence_ref,
        "source_trace": dict(record.source_trace),
        "dedup_key": record.dedup_key,
        "batch_id": record.batch_id,
        "batch_item_id": record.batch_item_id,
        "recorded_at": record.recorded_at,
    }


def validate_batch_item_outcome(outcome: BatchItemOutcome) -> BatchItemOutcome:
    if not isinstance(outcome, BatchItemOutcome):
        raise BatchDatasetContractError("invalid_item_outcome", "BatchItemOutcome expected")
    _validate_sanitized_ref(outcome.item_id, field="item_id")
    if outcome.operation not in ALLOWED_BATCH_ITEM_OPERATIONS:
        raise BatchDatasetContractError("invalid_target_operation", "batch item outcome operation is not admitted")
    _validate_sanitized_ref(outcome.adapter_key, field="adapter_key")
    _validate_sanitized_ref(outcome.target_ref, field="target_ref")
    if outcome.outcome_status not in {BATCH_ITEM_SUCCEEDED, BATCH_ITEM_FAILED, BATCH_ITEM_DUPLICATE_SKIPPED}:
        raise BatchDatasetContractError(
            "invalid_item_outcome_status",
            "batch item outcome_status is not part of the batch contract",
            details={"outcome_status": outcome.outcome_status},
        )
    if outcome.result_envelope is not None:
        _require_mapping(outcome.result_envelope, field="result_envelope")
        _validate_public_payload_no_leakage(outcome.result_envelope, field="result_envelope")
    if outcome.error_envelope is not None:
        _require_mapping(outcome.error_envelope, field="error_envelope")
        _validate_public_payload_no_leakage(outcome.error_envelope, field="error_envelope")
    if outcome.dataset_record_ref is not None:
        _validate_sanitized_ref(outcome.dataset_record_ref, field="dataset_record_ref")
    if outcome.source_trace is not None:
        _validate_source_trace(outcome.source_trace)
    _require_mapping(outcome.audit, field="audit")
    _validate_public_payload_no_leakage(outcome.audit, field="audit")
    return outcome


def batch_resume_token_to_dict(token: BatchResumeToken) -> dict[str, Any]:
    return {
        "resume_token": token.resume_token,
        "batch_id": token.batch_id,
        "target_set_hash": token.target_set_hash,
        "next_item_index": token.next_item_index,
        "issued_at": token.issued_at,
    }


def batch_target_set_hash(target_set: Sequence[BatchTargetItem]) -> str:
    payload = [
        {
            "item_id": item.item_id,
            "operation": item.operation,
            "adapter_key": item.adapter_key,
            "target_type": item.target_type,
            "target_ref": item.target_ref,
            "dedup_key": item.dedup_key,
            "request_cursor": item.request_cursor,
        }
        for item in target_set
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _outcome_from_task_envelope(
    item: BatchTargetItem,
    envelope: Mapping[str, Any],
    *,
    request: BatchRequest,
    dataset_id: str | None,
    dataset_sink: ReferenceDatasetSink | None,
    now: Callable[[], datetime],
) -> BatchItemOutcome:
    source_trace = _validated_optional_source_trace(envelope)
    if envelope.get("status") != "success":
        return BatchItemOutcome(
            item_id=item.item_id,
            operation=item.operation,
            adapter_key=item.adapter_key,
            target_ref=item.target_ref,
            outcome_status=BATCH_ITEM_FAILED,
            error_envelope=_require_mapping(envelope.get("error"), field="error"),
            source_trace=source_trace,
            audit={"reason": "item_failed"},
        )
    if request.dataset_sink_ref is not None and dataset_sink is None:
        return BatchItemOutcome(
            item_id=item.item_id,
            operation=item.operation,
            adapter_key=item.adapter_key,
            target_ref=item.target_ref,
            outcome_status=BATCH_ITEM_FAILED,
            result_envelope=dict(envelope),
            error_envelope={
                "code": DATASET_SINK_UNAVAILABLE,
                "message": "dataset_sink_ref was provided but no dataset sink is available",
                "details": {"dataset_sink_ref": request.dataset_sink_ref},
            },
            source_trace=source_trace,
            audit={"reason": DATASET_SINK_UNAVAILABLE},
        )
    if request.dataset_sink_ref is None or dataset_id is None:
        return BatchItemOutcome(
            item_id=item.item_id,
            operation=item.operation,
            adapter_key=item.adapter_key,
            target_ref=item.target_ref,
            outcome_status=BATCH_ITEM_SUCCEEDED,
            result_envelope=dict(envelope),
            source_trace=source_trace,
            audit={"reason": "item_succeeded_without_dataset_sink"},
        )
    record = DatasetRecord(
        dataset_record_id=f"{dataset_id}:{item.item_id}",
        dataset_id=dataset_id,
        source_operation=item.operation,
        adapter_key=item.adapter_key,
        target_ref=item.target_ref,
        raw_payload_ref=envelope.get("raw_payload_ref") if isinstance(envelope.get("raw_payload_ref"), str) else None,
        normalized_payload=_normalized_payload_from_envelope(envelope),
        evidence_ref=_evidence_ref_from_envelope(envelope),
        source_trace=_source_trace_from_envelope(item, envelope, now=now),
        dedup_key=item.dedup_key,
        batch_id=request.batch_id,
        batch_item_id=item.item_id,
        recorded_at=now().isoformat().replace("+00:00", "Z"),
    )
    try:
        written = dataset_sink.write(record)
    except BatchDatasetContractError as error:
        return BatchItemOutcome(
            item_id=item.item_id,
            operation=item.operation,
            adapter_key=item.adapter_key,
            target_ref=item.target_ref,
            outcome_status=BATCH_ITEM_FAILED,
            result_envelope=dict(envelope),
            error_envelope={"code": DATASET_WRITE_FAILED, "message": error.message, "details": error.details},
            source_trace=source_trace,
            audit={"reason": DATASET_WRITE_FAILED},
        )
    return BatchItemOutcome(
        item_id=item.item_id,
        operation=item.operation,
        adapter_key=item.adapter_key,
        target_ref=item.target_ref,
        outcome_status=BATCH_ITEM_SUCCEEDED,
        result_envelope=dict(envelope),
        dataset_record_ref=written.dataset_record_id,
        source_trace=source_trace,
        audit={"reason": "dataset_record_written"},
    )


def _task_request_from_batch_item(item: BatchTargetItem) -> TaskRequest:
    if item.operation == "content_search_by_keyword":
        task_input = TaskInput(keyword=item.target_ref, continuation_token=_continuation_token(item.request_cursor))
    elif item.operation == "content_list_by_creator":
        task_input = TaskInput(creator_id=item.target_ref, continuation_token=_continuation_token(item.request_cursor))
    elif item.operation == "comment_collection":
        task_input = TaskInput(content_ref=item.target_ref, comment_request_cursor=item.request_cursor)
    elif item.operation == "creator_profile_by_id":
        task_input = TaskInput(creator_id=item.target_ref)
    elif item.operation == "media_asset_fetch_by_ref":
        task_input = TaskInput(media_ref=item.target_ref, media_fetch_policy=item.request_cursor)
    else:
        raise BatchDatasetContractError("invalid_target_operation", "batch target operation is not admitted")
    return TaskRequest(adapter_key=item.adapter_key, capability=item.operation, input=task_input)


def _continuation_token(request_cursor: Mapping[str, Any] | None) -> str | None:
    if not request_cursor:
        return None
    token = request_cursor.get("continuation_token")
    return token if isinstance(token, str) else None


def _resumable_result(
    request: BatchRequest,
    *,
    outcomes: Sequence[BatchItemOutcome],
    target_set_hash: str,
    next_item_index: int,
    dataset_id: str | None,
    started_at: str,
    now: Callable[[], datetime],
    stop_reason: str,
) -> BatchResultEnvelope:
    _validate_sanitized_ref(stop_reason, field="stop_reason")
    token = BatchResumeToken(
        resume_token=f"resume:{request.batch_id}:{next_item_index}",
        batch_id=request.batch_id,
        target_set_hash=target_set_hash,
        next_item_index=next_item_index,
        issued_at=now().isoformat().replace("+00:00", "Z"),
    )
    return BatchResultEnvelope(
        batch_id=request.batch_id,
        operation=BATCH_EXECUTION_OPERATION,
        result_status=BATCH_RESULT_RESUMABLE,
        item_outcomes=tuple(outcomes),
        resume_token=token,
        dataset_sink_ref=request.dataset_sink_ref,
        dataset_id=dataset_id,
        audit_trace=_batch_audit_trace(
            request,
            outcomes=outcomes,
            started_at=started_at,
            finished=False,
            stop_reason=stop_reason,
        ),
    )


def _validate_resume_token(token: BatchResumeToken, *, request: BatchRequest, target_set_hash: str) -> None:
    if token.batch_id != request.batch_id or token.target_set_hash != target_set_hash:
        raise BatchDatasetContractError("invalid_resume_token", "resume token boundary does not match batch request")
    if token.next_item_index < 0 or token.next_item_index > len(request.target_set):
        raise BatchDatasetContractError("invalid_resume_position", "resume token next_item_index is outside target set")


def _aggregate_batch_result(outcomes: Sequence[BatchItemOutcome]) -> str:
    non_duplicate = [outcome for outcome in outcomes if outcome.outcome_status != BATCH_ITEM_DUPLICATE_SKIPPED]
    if not non_duplicate:
        return BATCH_RESULT_ALL_FAILED
    succeeded = sum(1 for outcome in non_duplicate if outcome.outcome_status == BATCH_ITEM_SUCCEEDED)
    failed = sum(1 for outcome in non_duplicate if outcome.outcome_status == BATCH_ITEM_FAILED)
    if succeeded and not failed:
        return BATCH_RESULT_COMPLETE
    if failed and not succeeded:
        return BATCH_RESULT_ALL_FAILED
    return BATCH_RESULT_PARTIAL_SUCCESS


def _is_stop_boundary_outcome(outcome: BatchItemOutcome) -> bool:
    if outcome.outcome_status != BATCH_ITEM_FAILED or outcome.error_envelope is None:
        return False
    code = outcome.error_envelope.get("code")
    return isinstance(code, str) and code in STOP_BOUNDARY_ERROR_CODES


def _batch_audit_trace(
    request: BatchRequest,
    *,
    outcomes: Sequence[BatchItemOutcome],
    started_at: str,
    finished: bool,
    stop_reason: str | None = None,
) -> Mapping[str, Any]:
    item_trace_refs = tuple(_item_trace_ref(request.batch_id, outcome.item_id) for outcome in outcomes)
    evidence_refs = list(_audit_context_evidence_refs(request.audit_context))
    for outcome in outcomes:
        if outcome.source_trace and isinstance(outcome.source_trace.get("evidence_alias"), str):
            evidence_refs.append(_validate_sanitized_ref(outcome.source_trace["evidence_alias"], field="audit_trace.evidence_refs"))
    if stop_reason is not None:
        _validate_sanitized_ref(stop_reason, field="audit_trace.stop_reason")
        evidence_refs.append(_validate_sanitized_ref(f"evidence:batch:{stop_reason}", field="audit_trace.evidence_refs"))
    return {
        "batch_id": request.batch_id,
        "started_at": started_at,
        "finished": finished,
        "item_count": len(outcomes),
        "item_trace_refs": item_trace_refs,
        "evidence_refs": tuple(dict.fromkeys(evidence_refs)),
        **({"stop_reason": stop_reason} if stop_reason is not None else {}),
    }


def _item_trace_ref(batch_id: str, item_id: str) -> str:
    return _validate_sanitized_ref(f"audit:batch:{batch_id}:{item_id}", field="audit_trace.item_trace_refs")


def _audit_context_evidence_refs(audit_context: Mapping[str, Any]) -> tuple[str, ...]:
    refs: list[str] = []
    for field in ("evidence_ref", "evidence_alias"):
        value = audit_context.get(field)
        if value is not None:
            refs.append(_validate_sanitized_ref(str(value), field=f"audit_context.{field}"))
    values = audit_context.get("evidence_refs")
    if values is not None:
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            raise BatchDatasetContractError("invalid_field", "audit_context.evidence_refs must be a sequence")
        for index, value in enumerate(values):
            refs.append(_validate_sanitized_ref(str(value), field=f"audit_context.evidence_refs[{index}]"))
    return tuple(dict.fromkeys(refs))


def _dataset_id_for_request(request: BatchRequest) -> str | None:
    if request.dataset_sink_ref is None:
        return request.dataset_id
    if request.dataset_id:
        return request.dataset_id
    return f"dataset:{request.batch_id}"


def _normalized_payload_from_envelope(envelope: Mapping[str, Any]) -> Any:
    if "normalized" in envelope:
        return _strip_normalized_payload_private_fields(envelope["normalized"])
    if "items" in envelope:
        return {
            "items": _strip_normalized_payload_private_fields(envelope["items"]),
            "result_status": envelope.get("result_status"),
        }
    if "profile" in envelope:
        return {"profile": envelope["profile"], "result_status": envelope.get("result_status")}
    if "media" in envelope:
        return {"media": envelope["media"], "result_status": envelope.get("result_status")}
    return {"operation": envelope.get("operation"), "status": envelope.get("status")}


def _evidence_ref_from_envelope(envelope: Mapping[str, Any]) -> str:
    source_trace = envelope.get("source_trace")
    if isinstance(source_trace, Mapping) and isinstance(source_trace.get("evidence_alias"), str):
        return source_trace["evidence_alias"]
    return "evidence:batch:item"


def _source_trace_from_envelope(
    item: BatchTargetItem,
    envelope: Mapping[str, Any],
    *,
    now: Callable[[], datetime],
) -> Mapping[str, Any]:
    source_trace = envelope.get("source_trace")
    if isinstance(source_trace, Mapping):
        _validate_source_trace(source_trace)
        return dict(source_trace)
    return {
        "adapter_key": item.adapter_key,
        "provider_path": "provider:sanitized:batch",
        "fetched_at": now().isoformat().replace("+00:00", "Z"),
        "evidence_alias": "evidence:batch:item",
    }


def _canonical_item_outcomes(outcomes: Sequence[BatchItemOutcome]) -> tuple[BatchItemOutcome, ...]:
    for outcome in outcomes:
        validate_batch_item_outcome(outcome)
    return tuple(outcomes)


def _validated_optional_source_trace(envelope: Mapping[str, Any]) -> Mapping[str, Any] | None:
    source_trace = envelope.get("source_trace")
    if source_trace is None:
        return None
    if not isinstance(source_trace, Mapping):
        raise BatchDatasetContractError("invalid_field", "source_trace must be an object")
    _validate_source_trace(source_trace)
    return dict(source_trace)


def _validate_resume_outcome_prefix(
    request: BatchRequest,
    *,
    outcomes: Sequence[BatchItemOutcome],
    dataset_id: str | None,
    dataset_sink: ReferenceDatasetSink | None,
    next_item_index: int,
) -> None:
    dataset_records = {
        record.dataset_record_id: record
        for record in (dataset_sink.read_by_dataset(dataset_id) if dataset_sink is not None and dataset_id is not None else ())
    }
    seen_dedup_keys: set[str] = set()
    for index in range(next_item_index):
        item = request.target_set[index]
        outcome = outcomes[index]
        if outcome.outcome_status not in {BATCH_ITEM_SUCCEEDED, BATCH_ITEM_FAILED, BATCH_ITEM_DUPLICATE_SKIPPED}:
            raise BatchDatasetContractError(
                "resume_outcome_status_invalid",
                "prior item outcome status is not part of the batch contract",
                details={"index": index, "item_id": item.item_id, "outcome_status": outcome.outcome_status},
            )
        if (
            outcome.item_id != item.item_id
            or outcome.operation != item.operation
            or outcome.adapter_key != item.adapter_key
            or outcome.target_ref != item.target_ref
        ):
            raise BatchDatasetContractError(
                "resume_outcome_prefix_mismatch",
                "prior item outcome does not match target_set prefix",
                details={"index": index, "item_id": item.item_id},
            )
        duplicate = item.dedup_key in seen_dedup_keys
        seen_dedup_keys.add(item.dedup_key)
        if duplicate and outcome.outcome_status != BATCH_ITEM_DUPLICATE_SKIPPED:
            raise BatchDatasetContractError(
                "resume_dedup_state_mismatch",
                "prior duplicate item outcome does not preserve duplicate_skipped state",
                details={"index": index, "item_id": item.item_id},
            )
        if not duplicate and outcome.outcome_status == BATCH_ITEM_DUPLICATE_SKIPPED:
            raise BatchDatasetContractError(
                "resume_dedup_state_mismatch",
                "prior non-duplicate item outcome must not be duplicate_skipped",
                details={"index": index, "item_id": item.item_id},
            )
        if outcome.outcome_status == BATCH_ITEM_DUPLICATE_SKIPPED and outcome.dataset_record_ref is not None:
            raise BatchDatasetContractError(
                "resume_dedup_state_mismatch",
                "prior duplicate_skipped outcome must not reference a dataset record",
                details={"index": index, "item_id": item.item_id},
            )
        if (
            request.dataset_sink_ref is not None
            and not duplicate
            and outcome.outcome_status == BATCH_ITEM_SUCCEEDED
        ):
            if dataset_sink is None or dataset_id is None or not outcome.dataset_record_ref:
                raise BatchDatasetContractError(
                    "resume_dataset_state_missing",
                    "prior successful outcome must be bound to the resumed dataset sink state",
                    details={"index": index, "item_id": item.item_id},
                )
            record = dataset_records.get(outcome.dataset_record_ref)
            if (
                record is None
                or record.batch_id != request.batch_id
                or record.batch_item_id != item.item_id
                or record.dedup_key != item.dedup_key
            ):
                raise BatchDatasetContractError(
                    "resume_dataset_state_mismatch",
                    "prior successful outcome dataset record is not present in the resumed sink",
                    details={"index": index, "item_id": item.item_id},
                )


def _validate_source_trace(source_trace: Mapping[str, Any]) -> None:
    extra_fields = set(source_trace) - _ALLOWED_SOURCE_TRACE_FIELDS
    if extra_fields:
        raise BatchDatasetContractError(
            "unsafe_source_trace",
            "source_trace contains fields outside the sanitized Core contract",
            details={"fields": sorted(extra_fields)},
        )
    adapter_key = _require_non_empty_string(source_trace.get("adapter_key"), field="source_trace.adapter_key")
    provider_path = _require_non_empty_string(source_trace.get("provider_path"), field="source_trace.provider_path")
    evidence_alias = _require_non_empty_string(source_trace.get("evidence_alias"), field="source_trace.evidence_alias")
    _validate_sanitized_ref(adapter_key, field="source_trace.adapter_key")
    _validate_provider_path(provider_path)
    _validate_sanitized_ref(evidence_alias, field="source_trace.evidence_alias")
    if source_trace.get("resource_profile_ref") is not None:
        _validate_sanitized_ref(str(source_trace.get("resource_profile_ref")), field="source_trace.resource_profile_ref")
    _require_non_empty_string(source_trace.get("fetched_at"), field="source_trace.fetched_at")


def _validate_provider_path(provider_path: str) -> None:
    forbidden = ("http://", "https://", "file://", "/tmp/", "/var/", "\\", "selector", "fallback", "marketplace")
    if any(token in provider_path.lower() for token in forbidden):
        raise BatchDatasetContractError("unsafe_provider_path", "source_trace.provider_path must be a sanitized alias")


def _validate_sanitized_ref(value: str, *, field: str) -> str:
    normalized = _require_non_empty_string(value, field=field)
    lowered = normalized.lower()
    if any(token in lowered for token in _FORBIDDEN_REF_TOKENS):
        raise BatchDatasetContractError("unsafe_ref", f"{field} contains forbidden private or storage token", details={"field": field})
    _ensure_json_safe(normalized, field=field)
    return normalized


def _strip_normalized_payload_private_fields(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _strip_normalized_payload_private_fields(item)
            for key, item in value.items()
            if str(key) not in _FORBIDDEN_NORMALIZED_PAYLOAD_KEYS
        }
    if isinstance(value, list):
        return [_strip_normalized_payload_private_fields(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_strip_normalized_payload_private_fields(item) for item in value)
    return value


def _validate_normalized_payload_no_leakage(value: Any, *, field: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text in _FORBIDDEN_NORMALIZED_PAYLOAD_KEYS:
                raise BatchDatasetContractError(
                    "unsafe_normalized_payload",
                    "normalized_payload contains a private raw/source/storage field",
                    details={"field": f"{field}.{key_text}"},
                )
            _validate_public_payload_key(key_text, field=f"{field}.{key_text}")
            _validate_normalized_payload_no_leakage(item, field=f"{field}.{key_text}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _validate_normalized_payload_no_leakage(item, field=f"{field}[{index}]")
        return
    if isinstance(value, str):
        _validate_public_payload_string(value, field=field)


def _validate_public_payload_no_leakage(value: Any, *, field: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text == "source_trace" and isinstance(item, Mapping):
                _validate_source_trace(item)
                continue
            _validate_public_payload_key(key_text, field=f"{field}.{key_text}")
            _validate_public_payload_no_leakage(item, field=f"{field}.{key_text}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _validate_public_payload_no_leakage(item, field=f"{field}[{index}]")
        return
    if isinstance(value, str):
        _validate_public_payload_string(value, field=field)


def _validate_public_payload_key(key: str, *, field: str) -> None:
    lowered = key.lower()
    if any(token in lowered for token in _FORBIDDEN_PUBLIC_PAYLOAD_KEY_TOKENS):
        raise BatchDatasetContractError(
            "unsafe_public_payload",
            "public batch/dataset carrier contains a private field",
            details={"field": field},
        )


def _validate_public_payload_string(value: str, *, field: str) -> None:
    lowered = value.lower()
    if any(token in lowered for token in _FORBIDDEN_REF_TOKENS):
        raise BatchDatasetContractError(
            "unsafe_public_payload",
            "public batch/dataset carrier contains a raw path, storage handle, or private token",
            details={"field": field},
        )


def _require_non_empty_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BatchDatasetContractError("invalid_field", f"{field} must be a non-empty string", details={"field": field})
    return value


def _require_mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BatchDatasetContractError("invalid_field", f"{field} must be an object", details={"field": field})
    _ensure_json_safe(value, field=field)
    return value


def _ensure_json_safe(value: Any, *, field: str) -> None:
    try:
        json.dumps(value, sort_keys=True)
    except (TypeError, ValueError) as error:
        raise BatchDatasetContractError(
            "non_json_safe_value",
            f"{field} must be JSON-safe",
            details={"field": field, "error": str(error)},
        ) from error
