from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import hashlib
import json
from typing import Any
from uuid import uuid4

from syvert.read_side_collection import validate_comment_request_cursor
from syvert.runtime import (
    CollectionPolicy,
    CoreTaskRequest,
    InputTarget,
    TaskInput,
    TaskRequest,
    execute_task,
    is_valid_rfc3339_utc,
    validate_media_fetch_policy,
    validate_success_payload,
)


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
_COLLECTION_SUCCESS_PAYLOAD_FIELDS = frozenset(
    {
        "operation",
        "target",
        "items",
        "has_more",
        "next_continuation",
        "result_status",
        "error_classification",
        "raw_payload_ref",
        "source_trace",
        "audit",
    }
)
_SUCCESS_PAYLOAD_FIELDS_BY_OPERATION = {
    "content_search_by_keyword": _COLLECTION_SUCCESS_PAYLOAD_FIELDS,
    "content_list_by_creator": _COLLECTION_SUCCESS_PAYLOAD_FIELDS,
    "comment_collection": _COLLECTION_SUCCESS_PAYLOAD_FIELDS,
    "creator_profile_by_id": frozenset(
        {
            "operation",
            "target",
            "result_status",
            "error_classification",
            "profile",
            "raw_payload_ref",
            "source_trace",
            "audit",
        }
    ),
    "media_asset_fetch_by_ref": frozenset(
        {
            "operation",
            "target",
            "content_type",
            "fetch_policy",
            "fetch_outcome",
            "result_status",
            "error_classification",
            "raw_payload_ref",
            "source_trace",
            "media",
            "audit",
        }
    ),
}
_RESULT_ENVELOPE_WRAPPER_FIELDS = frozenset(
    {
        "task_id",
        "adapter_key",
        "capability",
        "status",
        "task_record_ref",
        "runtime_result_refs",
        "execution_control_events",
        "runtime_failure_signal",
        "runtime_structured_log_events",
        "runtime_execution_metric_samples",
    }
)
_REQUIRED_RESULT_ENVELOPE_WRAPPER_FIELDS = frozenset({"task_id", "adapter_key", "capability", "status"})

_FORBIDDEN_REF_TOKENS = (
    "http://",
    "https://",
    "s3://",
    "gs://",
    "storage://",
    "file://",
    "/tmp/",
    "/var/",
    "/etc/",
    "/home/",
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
    "raw_payload",
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
_PUBLIC_REF_VALUE_KEYS = frozenset(
    {
        "raw_payload_ref",
        "evidence_ref",
        "evidence_alias",
        "dataset_record_ref",
        "resource_profile_ref",
        "task_record_ref",
        "envelope_ref",
        "ref_id",
    }
)
_NORMALIZED_PUBLIC_URL_REF_KEYS = frozenset({"canonical_ref", "source_ref"})
_NORMALIZED_PUBLIC_URL_REF_COMPACT_KEYS = frozenset({"canonicalref", "sourceref"})
_FORBIDDEN_PUBLIC_URL_TOKENS = (
    "storage",
    "bucket",
    "download",
    "raw",
    "private",
    "credential",
    "secret",
    "signed",
    "token=",
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
    dataset_sink_ref: str | None = None
    dataset_id: str | None = None


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
    request_cursor_context: Mapping[str, Any] | None = field(default=None, repr=False, compare=False)


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
        self._record_ids: set[str] = set()

    def write(self, record: DatasetRecord | Mapping[str, Any]) -> DatasetRecord:
        normalized = canonical_dataset_record(record)
        if normalized.dataset_record_id in self._record_ids:
            raise BatchDatasetContractError(
                "duplicate_dataset_record",
                "dataset sink dataset_record_id already exists",
                details={"dataset_record_id": normalized.dataset_record_id},
            )
        dedup_identity = (normalized.dataset_id, normalized.dedup_key)
        if dedup_identity in self._dedup_keys:
            raise BatchDatasetContractError(
                "duplicate_dataset_record",
                "dataset sink first-wins dedup_key already exists",
                details={"dataset_id": normalized.dataset_id, "dedup_key": normalized.dedup_key},
            )
        stored = _clone_dataset_record(normalized)
        self._records.append(stored)
        self._dedup_keys.add(dedup_identity)
        self._record_ids.add(normalized.dataset_record_id)
        return _clone_dataset_record(stored)

    def read_by_dataset(self, dataset_id: str) -> tuple[DatasetRecord, ...]:
        dataset_id = _require_non_empty_string(dataset_id, field="dataset_id")
        return tuple(_clone_dataset_record(record) for record in self._records if record.dataset_id == dataset_id)

    def read_by_batch(self, batch_id: str) -> tuple[DatasetRecord, ...]:
        batch_id = _require_non_empty_string(batch_id, field="batch_id")
        return tuple(_clone_dataset_record(record) for record in self._records if record.batch_id == batch_id)

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


def _clone_dataset_record(record: DatasetRecord) -> DatasetRecord:
    return canonical_dataset_record(
        json.loads(json.dumps(dataset_record_to_dict(record), sort_keys=True, allow_nan=False))
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
    outcomes = list(_canonical_item_outcomes(prior_item_outcomes, target_set=validated.target_set))
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
        _validate_resume_runtime_position(
            validated,
            dataset_id=dataset_id,
            dataset_sink=dataset_sink,
            next_item_index=start_index,
        )
        _validate_resume_outcome_prefix(
            validated,
            outcomes=outcomes,
            dataset_id=dataset_id,
            dataset_sink=dataset_sink,
            next_item_index=start_index,
        )
    seen_dedup_keys = {validated.target_set[index].dedup_key for index in range(min(start_index, len(validated.target_set)))}
    task_id_factory = task_id_factory or (lambda: f"batch-item-{uuid4().hex}")
    stop_at = len(validated.target_set)
    if stop_after_items is not None:
        stop_at = min(len(validated.target_set), start_index + stop_after_items)

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
                _validated_public_outcome(
                    item,
                    BatchItemOutcome(
                        item_id=item.item_id,
                        operation=item.operation,
                        adapter_key=item.adapter_key,
                        target_ref=item.target_ref,
                        outcome_status=BATCH_ITEM_DUPLICATE_SKIPPED,
                        audit={"reason": "duplicate_dedup_key", "dedup_key": item.dedup_key},
                    ),
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
        outcomes.append(_validated_public_outcome(item, outcome))
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
    _validate_sanitized_ref(_require_non_empty_string(request.batch_id, field="batch_id"), field="batch_id")
    if not request.target_set:
        raise BatchDatasetContractError("empty_target_set", "BatchRequest.target_set must not be empty")
    seen_item_ids: set[str] = set()
    for index, item in enumerate(request.target_set):
        validate_batch_target_item(item, index=index)
        if item.item_id in seen_item_ids:
            raise BatchDatasetContractError(
                "duplicate_item_id",
                "BatchRequest.target_set item_id values must be unique",
                details={"item_id": item.item_id, "index": index},
            )
        seen_item_ids.add(item.item_id)
    if request.dataset_sink_ref is not None:
        _validate_sanitized_ref(request.dataset_sink_ref, field="dataset_sink_ref")
    if request.dataset_id is not None:
        _validate_sanitized_ref(request.dataset_id, field="dataset_id")
    if request.resume_token is not None:
        _validate_resume_token(
            request.resume_token,
            request=request,
            target_set_hash=batch_target_set_hash(request.target_set),
        )
    audit_context = _require_mapping(request.audit_context, field="audit_context")
    _audit_context_evidence_refs(audit_context)
    return request


def validate_batch_target_item(item: BatchTargetItem, *, index: int = 0) -> BatchTargetItem:
    if not isinstance(item, BatchTargetItem):
        raise BatchDatasetContractError("invalid_target_item", "BatchTargetItem expected", details={"index": index})
    _validate_sanitized_ref(_require_non_empty_string(item.item_id, field="item_id"), field="item_id")
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
    _validate_target_ref(item.operation, item.target_ref, field="target_ref")
    _validate_sanitized_ref(item.dedup_key, field="dedup_key")
    if item.request_cursor is not None:
        _ensure_json_safe(item.request_cursor, field="request_cursor")
        if not isinstance(item.request_cursor, Mapping):
            raise BatchDatasetContractError(
                "invalid_field",
                "request_cursor must be an object",
                details={"field": "request_cursor", "index": index},
            )
        if item.operation in {"content_search_by_keyword", "content_list_by_creator"}:
            _validate_continuation_request_cursor(item.request_cursor, index=index)
        elif item.operation == "comment_collection":
            _validate_comment_collection_request_cursor(item.request_cursor, target_ref=item.target_ref, index=index)
        elif item.operation == "creator_profile_by_id":
            raise BatchDatasetContractError(
                "unsupported_request_cursor",
                "batch request_cursor is not yet supported for this item operation",
                details={"operation": item.operation, "index": index},
            )
        elif item.operation == "media_asset_fetch_by_ref":
            _validate_media_fetch_request_cursor(item.request_cursor, index=index)
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
    _validate_target_ref(record.source_operation, record.target_ref, field="target_ref")
    if record.raw_payload_ref is not None:
        _validate_sanitized_ref(record.raw_payload_ref, field="raw_payload_ref")
    _ensure_json_safe(record.normalized_payload, field="normalized_payload")
    _validate_normalized_payload_no_leakage(record.normalized_payload, field="normalized_payload")
    _validate_sanitized_ref(record.evidence_ref, field="evidence_ref")
    _validate_source_trace(record.source_trace)
    _validate_sanitized_ref(record.dedup_key, field="dedup_key")
    _validate_sanitized_ref(record.batch_id, field="batch_id")
    _validate_sanitized_ref(record.batch_item_id, field="batch_item_id")
    _validate_public_timestamp(record.recorded_at, field="recorded_at")
    return record


def batch_result_envelope_to_dict(envelope: BatchResultEnvelope) -> dict[str, Any]:
    validate_batch_result_envelope(envelope)
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


def validate_batch_result_envelope(envelope: BatchResultEnvelope) -> BatchResultEnvelope:
    if not isinstance(envelope, BatchResultEnvelope):
        raise BatchDatasetContractError("invalid_batch_result_envelope", "BatchResultEnvelope expected")
    _validate_sanitized_ref(envelope.batch_id, field="batch_id")
    if envelope.operation != BATCH_EXECUTION_OPERATION:
        raise BatchDatasetContractError(
            "invalid_batch_operation",
            "batch result envelope operation must be batch_execution",
            details={"operation": envelope.operation},
        )
    if envelope.result_status not in {
        BATCH_RESULT_COMPLETE,
        BATCH_RESULT_PARTIAL_SUCCESS,
        BATCH_RESULT_ALL_FAILED,
        BATCH_RESULT_RESUMABLE,
    }:
        raise BatchDatasetContractError(
            "invalid_batch_result_status",
            "batch result_status is not part of the batch contract",
            details={"result_status": envelope.result_status},
        )
    for outcome in envelope.item_outcomes:
        validate_batch_item_outcome(outcome, request_cursor=outcome.request_cursor_context)
    expected_result_status = (
        BATCH_RESULT_RESUMABLE
        if envelope.result_status == BATCH_RESULT_RESUMABLE
        else _aggregate_batch_result(envelope.item_outcomes)
    )
    if envelope.result_status != expected_result_status:
        raise BatchDatasetContractError(
            "invalid_batch_result_status",
            "batch result_status does not match item outcome aggregation",
            details={"result_status": envelope.result_status, "expected": expected_result_status},
        )
    if envelope.resume_token is not None:
        validate_batch_resume_token(envelope.resume_token)
        if envelope.resume_token.batch_id != envelope.batch_id:
            raise BatchDatasetContractError(
                "invalid_resume_token",
                "resume token batch boundary does not match result envelope",
            )
        if (
            envelope.resume_token.dataset_sink_ref != envelope.dataset_sink_ref
            or envelope.resume_token.dataset_id != envelope.dataset_id
        ):
            raise BatchDatasetContractError(
                "invalid_resume_token",
                "resume token dataset boundary does not match result envelope",
            )
    if envelope.result_status == BATCH_RESULT_RESUMABLE and envelope.resume_token is None:
        raise BatchDatasetContractError(
            "invalid_batch_result_envelope",
            "resumable batch result must carry a resume token",
        )
    if (
        envelope.result_status == BATCH_RESULT_RESUMABLE
        and envelope.resume_token is not None
        and envelope.resume_token.next_item_index != len(envelope.item_outcomes)
    ):
        raise BatchDatasetContractError(
            "invalid_resume_token",
            "resumable batch result token must point to the processed item prefix",
        )
    if envelope.result_status != BATCH_RESULT_RESUMABLE and envelope.resume_token is not None:
        raise BatchDatasetContractError(
            "invalid_batch_result_envelope",
            "non-resumable batch result must not carry a resume token",
        )
    if envelope.dataset_sink_ref is not None:
        _validate_sanitized_ref(envelope.dataset_sink_ref, field="dataset_sink_ref")
        if envelope.dataset_id is None:
            raise BatchDatasetContractError(
                "invalid_dataset_boundary",
                "batch result envelope with dataset_sink_ref must carry dataset_id",
            )
    if envelope.dataset_id is not None:
        _validate_sanitized_ref(envelope.dataset_id, field="dataset_id")
    _require_mapping(envelope.audit_trace, field="audit_trace")
    _validate_public_payload_no_leakage(envelope.audit_trace, field="audit_trace", validate_strings=True)
    _validate_batch_audit_trace(envelope)
    return envelope


def batch_item_outcome_to_dict(outcome: BatchItemOutcome) -> dict[str, Any]:
    validate_batch_item_outcome(outcome, request_cursor=outcome.request_cursor_context)
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


def validate_batch_item_outcome(
    outcome: BatchItemOutcome,
    *,
    request_cursor: Mapping[str, Any] | None = None,
) -> BatchItemOutcome:
    if not isinstance(outcome, BatchItemOutcome):
        raise BatchDatasetContractError("invalid_item_outcome", "BatchItemOutcome expected")
    _validate_sanitized_ref(outcome.item_id, field="item_id")
    if outcome.operation not in ALLOWED_BATCH_ITEM_OPERATIONS:
        raise BatchDatasetContractError("invalid_target_operation", "batch item outcome operation is not admitted")
    _validate_sanitized_ref(outcome.adapter_key, field="adapter_key")
    _validate_target_ref(outcome.operation, outcome.target_ref, field="target_ref")
    if outcome.outcome_status not in {BATCH_ITEM_SUCCEEDED, BATCH_ITEM_FAILED, BATCH_ITEM_DUPLICATE_SKIPPED}:
        raise BatchDatasetContractError(
            "invalid_item_outcome_status",
            "batch item outcome_status is not part of the batch contract",
            details={"outcome_status": outcome.outcome_status},
        )
    if outcome.outcome_status == BATCH_ITEM_SUCCEEDED and outcome.result_envelope is None:
        raise BatchDatasetContractError(
            "invalid_item_outcome",
            "succeeded batch item outcome must carry a read-side result envelope",
            details={"item_id": outcome.item_id, "outcome_status": outcome.outcome_status},
        )
    if outcome.outcome_status == BATCH_ITEM_SUCCEEDED and outcome.error_envelope is not None:
        raise BatchDatasetContractError(
            "invalid_item_outcome",
            "succeeded batch item outcome must not carry an error envelope",
            details={"item_id": outcome.item_id, "outcome_status": outcome.outcome_status},
        )
    if outcome.outcome_status == BATCH_ITEM_FAILED and outcome.error_envelope is None:
        raise BatchDatasetContractError(
            "invalid_item_outcome",
            "failed batch item outcome must carry an item-level error envelope",
            details={"item_id": outcome.item_id, "outcome_status": outcome.outcome_status},
        )
    if outcome.outcome_status == BATCH_ITEM_FAILED and outcome.dataset_record_ref is not None:
        raise BatchDatasetContractError(
            "invalid_item_outcome",
            "failed batch item outcome must not reference a dataset record",
            details={"item_id": outcome.item_id, "outcome_status": outcome.outcome_status},
        )
    if outcome.outcome_status == BATCH_ITEM_DUPLICATE_SKIPPED and (
        outcome.result_envelope is not None or outcome.error_envelope is not None or outcome.dataset_record_ref is not None
    ):
        raise BatchDatasetContractError(
            "invalid_item_outcome",
            "duplicate_skipped batch item outcome must not carry result, error, or dataset record refs",
            details={"item_id": outcome.item_id, "outcome_status": outcome.outcome_status},
        )
    if outcome.result_envelope is not None:
        _require_mapping(outcome.result_envelope, field="result_envelope")
        _validate_public_payload_no_leakage(outcome.result_envelope, field="result_envelope", validate_strings=False)
        _validate_result_envelope_boundary(
            operation=outcome.operation,
            adapter_key=outcome.adapter_key,
            target_ref=outcome.target_ref,
            request_cursor=request_cursor,
            result_envelope=outcome.result_envelope,
            item_id=outcome.item_id,
            code="result_envelope_boundary_mismatch",
        )
    if outcome.error_envelope is not None:
        _require_mapping(outcome.error_envelope, field="error_envelope")
        _validate_public_payload_no_leakage(outcome.error_envelope, field="error_envelope", validate_strings=True)
    if outcome.dataset_record_ref is not None:
        _validate_sanitized_ref(outcome.dataset_record_ref, field="dataset_record_ref")
    if outcome.source_trace is not None:
        _validate_source_trace(outcome.source_trace)
    _require_mapping(outcome.audit, field="audit")
    _validate_public_payload_no_leakage(outcome.audit, field="audit", validate_strings=True)
    return outcome


def batch_resume_token_to_dict(token: BatchResumeToken) -> dict[str, Any]:
    validate_batch_resume_token(token)
    return {
        "resume_token": token.resume_token,
        "batch_id": token.batch_id,
        "target_set_hash": token.target_set_hash,
        "next_item_index": token.next_item_index,
        "issued_at": token.issued_at,
        **({"dataset_sink_ref": token.dataset_sink_ref} if token.dataset_sink_ref is not None else {}),
        **({"dataset_id": token.dataset_id} if token.dataset_id is not None else {}),
    }


def validate_batch_resume_token(token: BatchResumeToken) -> BatchResumeToken:
    if not isinstance(token, BatchResumeToken):
        raise BatchDatasetContractError("invalid_resume_token", "BatchResumeToken expected")
    _validate_sanitized_ref(token.resume_token, field="resume_token")
    _validate_sanitized_ref(token.batch_id, field="resume_token.batch_id")
    _validate_sanitized_ref(token.target_set_hash, field="resume_token.target_set_hash")
    if (
        not isinstance(token.next_item_index, int)
        or isinstance(token.next_item_index, bool)
        or token.next_item_index < 0
    ):
        raise BatchDatasetContractError(
            "invalid_resume_position",
            "resume token next_item_index must be a non-negative integer",
        )
    _validate_public_timestamp(token.issued_at, field="resume_token.issued_at")
    if token.dataset_sink_ref is not None:
        _validate_sanitized_ref(token.dataset_sink_ref, field="resume_token.dataset_sink_ref")
        if token.dataset_id is None:
            raise BatchDatasetContractError(
                "invalid_dataset_boundary",
                "resume token with dataset_sink_ref must carry dataset_id",
            )
    if token.dataset_id is not None:
        _validate_sanitized_ref(token.dataset_id, field="resume_token.dataset_id")
    return token


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
    try:
        source_trace = _validated_optional_source_trace(envelope)
    except BatchDatasetContractError as error:
        return _unsafe_item_outcome(item, error)
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
    pre_write_outcome = _validated_public_outcome(
        item,
        BatchItemOutcome(
            item_id=item.item_id,
            operation=item.operation,
            adapter_key=item.adapter_key,
            target_ref=item.target_ref,
            outcome_status=BATCH_ITEM_SUCCEEDED,
            result_envelope=dict(envelope),
            source_trace=source_trace,
            audit={"reason": "item_succeeded_pending_dataset_write"},
        ),
    )
    if pre_write_outcome.outcome_status != BATCH_ITEM_SUCCEEDED:
        return pre_write_outcome
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
    except Exception as error:
        return BatchItemOutcome(
            item_id=item.item_id,
            operation=item.operation,
            adapter_key=item.adapter_key,
            target_ref=item.target_ref,
            outcome_status=BATCH_ITEM_FAILED,
            result_envelope=dict(envelope),
            error_envelope={
                "code": DATASET_WRITE_FAILED,
                "message": "dataset sink write failed",
                "details": {"error_type": type(error).__name__},
            },
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


def _task_request_from_batch_item(item: BatchTargetItem) -> TaskRequest | CoreTaskRequest:
    if item.operation == "content_search_by_keyword":
        if item.request_cursor is not None:
            return _core_paginated_task_request_from_batch_item(item)
        task_input = TaskInput(keyword=item.target_ref, continuation_token=_continuation_token(item.request_cursor))
    elif item.operation == "content_list_by_creator":
        if item.request_cursor is not None:
            return _core_paginated_task_request_from_batch_item(item)
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


def _core_paginated_task_request_from_batch_item(item: BatchTargetItem) -> CoreTaskRequest:
    return CoreTaskRequest(
        target=InputTarget(
            adapter_key=item.adapter_key,
            capability=item.operation,
            target_type=item.target_type,
            target_value=item.target_ref,
        ),
        policy=CollectionPolicy(collection_mode="paginated"),
        request_cursor={"continuation_token": _continuation_token(item.request_cursor)},
    )


def _continuation_token(request_cursor: Mapping[str, Any] | None) -> str | None:
    if not request_cursor:
        return None
    token = request_cursor.get("continuation_token")
    return token if isinstance(token, str) else None


def _validate_continuation_request_cursor(request_cursor: Mapping[str, Any], *, index: int) -> None:
    allowed_fields = {"continuation_token"}
    extra_fields = sorted(str(field) for field in request_cursor if field not in allowed_fields)
    if extra_fields:
        raise BatchDatasetContractError(
            "unsupported_request_cursor",
            "batch request_cursor contains fields outside the paginated continuation contract",
            details={"fields": extra_fields, "index": index},
        )
    token = request_cursor.get("continuation_token")
    _require_non_empty_string(token, field="request_cursor.continuation_token")


def _validate_media_fetch_request_cursor(request_cursor: Mapping[str, Any], *, index: int) -> None:
    error = validate_media_fetch_policy(request_cursor)
    if error is not None:
        raise BatchDatasetContractError(
            error.get("code", "invalid_task_request"),
            error.get("message", "media fetch request_cursor does not match the shared fetch policy contract"),
            details={**dict(error.get("details", {})), "field": "request_cursor", "index": index},
        )


def _validate_comment_collection_request_cursor(
    request_cursor: Mapping[str, Any],
    *,
    target_ref: str,
    index: int,
) -> None:
    error = validate_comment_request_cursor(request_cursor, target_ref=target_ref)
    if error is not None:
        raise BatchDatasetContractError(
            error.get("code", "signature_or_request_invalid"),
            error.get("message", "comment_collection request_cursor does not match the shared cursor contract"),
            details={**dict(error.get("details", {})), "field": "request_cursor", "index": index},
        )


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
        dataset_sink_ref=request.dataset_sink_ref,
        dataset_id=dataset_id,
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
    validate_batch_resume_token(token)
    if token.batch_id != request.batch_id or token.target_set_hash != target_set_hash:
        raise BatchDatasetContractError("invalid_resume_token", "resume token boundary does not match batch request")
    if token.dataset_sink_ref != request.dataset_sink_ref or token.dataset_id != _dataset_id_for_request(request):
        raise BatchDatasetContractError("invalid_resume_token", "resume token dataset boundary does not match batch request")
    if token.next_item_index > len(request.target_set):
        raise BatchDatasetContractError("invalid_resume_position", "resume token next_item_index is outside target set")
    expected_resume_token = f"resume:{request.batch_id}:{token.next_item_index}"
    if token.resume_token != expected_resume_token:
        raise BatchDatasetContractError(
            "invalid_resume_token",
            "resume token id must bind to batch_id and next_item_index",
        )


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


def _validated_public_outcome(item: BatchTargetItem, outcome: BatchItemOutcome) -> BatchItemOutcome:
    outcome = _with_request_cursor_context(item, outcome)
    try:
        validate_batch_item_outcome(outcome, request_cursor=item.request_cursor)
    except BatchDatasetContractError as error:
        return _unsafe_item_outcome(item, error)
    return outcome


def _with_request_cursor_context(item: BatchTargetItem, outcome: BatchItemOutcome) -> BatchItemOutcome:
    if outcome.result_envelope is None or item.request_cursor is None or outcome.request_cursor_context is not None:
        return outcome
    return replace(outcome, request_cursor_context=dict(item.request_cursor))


def _unsafe_item_outcome(item: BatchTargetItem, error: BatchDatasetContractError) -> BatchItemOutcome:
    return BatchItemOutcome(
        item_id=item.item_id,
        operation=item.operation,
        adapter_key=item.adapter_key,
        target_ref=item.target_ref,
        outcome_status=BATCH_ITEM_FAILED,
        error_envelope={
            "code": "unsafe_item_outcome",
            "message": "batch item outcome contained unsafe public carrier data",
            "details": {"blocked_code": error.code},
        },
        audit={"reason": "unsafe_item_outcome", "blocked_code": error.code},
    )


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
            refs.append(
                _validate_sanitized_ref(
                    _require_non_empty_string(value, field=f"audit_context.{field}"),
                    field=f"audit_context.{field}",
                )
            )
    values = audit_context.get("evidence_refs")
    if values is not None:
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            raise BatchDatasetContractError("invalid_field", "audit_context.evidence_refs must be a sequence")
        for index, value in enumerate(values):
            refs.append(
                _validate_sanitized_ref(
                    _require_non_empty_string(value, field=f"audit_context.evidence_refs[{index}]"),
                    field=f"audit_context.evidence_refs[{index}]",
                )
            )
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


def _canonical_item_outcomes(
    outcomes: Sequence[BatchItemOutcome],
    *,
    target_set: Sequence[BatchTargetItem] | None = None,
) -> tuple[BatchItemOutcome, ...]:
    canonical: list[BatchItemOutcome] = []
    for index, outcome in enumerate(outcomes):
        item = target_set[index] if target_set is not None and index < len(target_set) else None
        request_cursor = item.request_cursor if item is not None else None
        enriched = _with_request_cursor_context(item, outcome) if item is not None else outcome
        validate_batch_item_outcome(enriched, request_cursor=request_cursor)
        canonical.append(enriched)
    return tuple(canonical)


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
        if outcome.outcome_status == BATCH_ITEM_SUCCEEDED:
            _validate_prior_success_result_envelope(item, outcome.result_envelope, index=index)
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
        if request.dataset_sink_ref is None and outcome.dataset_record_ref is not None:
            raise BatchDatasetContractError(
                "resume_dataset_state_mismatch",
                "prior outcome must not reference a dataset record when resume has no dataset sink boundary",
                details={"index": index, "item_id": item.item_id},
            )
        if request.dataset_sink_ref is not None and outcome.outcome_status in {
            BATCH_ITEM_FAILED,
            BATCH_ITEM_DUPLICATE_SKIPPED,
        }:
            stale_records = [
                record
                for record in dataset_records.values()
                if record.batch_id == request.batch_id and record.batch_item_id == item.item_id
            ]
            if stale_records:
                raise BatchDatasetContractError(
                    "resume_dataset_state_mismatch",
                    "prior failed or duplicate_skipped outcome must not have a dataset record in the resumed sink",
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
                or record.dataset_record_id != outcome.dataset_record_ref
                or record.batch_id != request.batch_id
                or record.batch_item_id != item.item_id
                or record.dedup_key != item.dedup_key
                or record.source_operation != item.operation
                or record.adapter_key != item.adapter_key
                or record.target_ref != item.target_ref
            ):
                raise BatchDatasetContractError(
                    "resume_dataset_state_mismatch",
                    "prior successful outcome dataset record is not present in the resumed sink",
                    details={"index": index, "item_id": item.item_id},
                )


def _validate_resume_runtime_position(
    request: BatchRequest,
    *,
    dataset_id: str | None,
    dataset_sink: ReferenceDatasetSink | None,
    next_item_index: int,
) -> None:
    if request.dataset_sink_ref is None:
        return
    if dataset_id is None or dataset_sink is None:
        raise BatchDatasetContractError(
            "resume_dataset_state_missing",
            "resume requires dataset sink readback state to prove runtime position",
        )
    item_index_by_id = {item.item_id: index for index, item in enumerate(request.target_set)}
    for record in dataset_sink.read_by_dataset(dataset_id):
        if record.batch_id != request.batch_id:
            continue
        record_index = item_index_by_id.get(record.batch_item_id)
        if record_index is not None and record_index >= next_item_index:
            raise BatchDatasetContractError(
                "invalid_resume_position",
                "resume token next_item_index rewinds existing dataset sink state",
                details={
                    "batch_item_id": record.batch_item_id,
                    "record_index": record_index,
                    "next_item_index": next_item_index,
                },
            )


def _validate_prior_success_result_envelope(
    item: BatchTargetItem,
    result_envelope: Mapping[str, Any] | None,
    *,
    index: int,
) -> None:
    if result_envelope is None:
        raise BatchDatasetContractError(
            "resume_result_envelope_mismatch",
            "prior successful outcome must carry a read-side result envelope",
            details={"index": index, "item_id": item.item_id},
        )
    _validate_result_envelope_boundary(
        operation=item.operation,
        adapter_key=item.adapter_key,
        target_ref=item.target_ref,
        request_cursor=item.request_cursor,
        result_envelope=result_envelope,
        item_id=item.item_id,
        index=index,
        code="resume_result_envelope_mismatch",
    )


def _validate_result_envelope_boundary(
    *,
    operation: str,
    adapter_key: str,
    target_ref: str,
    request_cursor: Mapping[str, Any] | None,
    result_envelope: Mapping[str, Any],
    item_id: str,
    code: str,
    index: int | None = None,
) -> None:
    target_type = TARGET_TYPE_BY_OPERATION[operation]
    payload_fields = _SUCCESS_PAYLOAD_FIELDS_BY_OPERATION[operation]
    extra_fields = sorted(set(result_envelope) - (payload_fields | _RESULT_ENVELOPE_WRAPPER_FIELDS))
    if extra_fields:
        raise BatchDatasetContractError(
            code,
            "batch item result_envelope contains fields outside the read-side contract",
            details={"item_id": item_id, "fields": extra_fields, **({"index": index} if index is not None else {})},
        )
    _validate_result_envelope_wrapper(
        operation=operation,
        adapter_key=adapter_key,
        result_envelope=result_envelope,
        item_id=item_id,
        code=code,
        index=index,
    )
    payload = {field: result_envelope[field] for field in payload_fields if field in result_envelope}
    if operation == "comment_collection" and request_cursor is None and _comment_result_requires_cursor_context(payload):
        raise BatchDatasetContractError(
            code,
            "comment_collection result_envelope requires request_cursor context",
            details={"item_id": item_id, **({"index": index} if index is not None else {})},
        )
    error = validate_success_payload(
        payload,
        capability=operation,
        target_type=target_type,
        target_value=target_ref,
        request_cursor=request_cursor,
    )
    if error is not None:
        details = {"item_id": item_id, "reason": error.get("code"), **dict(error.get("details", {}))}
        if index is not None:
            details["index"] = index
        raise BatchDatasetContractError(
            code,
            "batch item result_envelope does not match operation/target boundary",
            details=details,
        )


def _validate_result_envelope_wrapper(
    *,
    operation: str,
    adapter_key: str,
    result_envelope: Mapping[str, Any],
    item_id: str,
    code: str,
    index: int | None,
) -> None:
    details = {"item_id": item_id, **({"index": index} if index is not None else {})}
    missing = sorted(field for field in _REQUIRED_RESULT_ENVELOPE_WRAPPER_FIELDS if field not in result_envelope)
    if missing:
        raise BatchDatasetContractError(
            code,
            "batch item result_envelope is missing runtime wrapper fields",
            details={**details, "missing": missing},
        )
    if result_envelope["status"] != "success":
        raise BatchDatasetContractError(
            code,
            "batch item result_envelope status must be success",
            details={**details, "status": result_envelope["status"]},
        )
    if result_envelope["capability"] != operation:
        raise BatchDatasetContractError(
            code,
            "batch item result_envelope capability must match operation",
            details={**details, "capability": result_envelope["capability"], "expected": operation},
        )
    if result_envelope["adapter_key"] != adapter_key:
        raise BatchDatasetContractError(
            code,
            "batch item result_envelope adapter_key must match outcome",
            details={**details, "adapter_key": result_envelope["adapter_key"], "expected": adapter_key},
        )
    _validate_sanitized_ref(_require_non_empty_string(result_envelope["task_id"], field="result_envelope.task_id"), field="result_envelope.task_id")
    wrapper_payload = {
        field: result_envelope[field]
        for field in _RESULT_ENVELOPE_WRAPPER_FIELDS
        if field in result_envelope
    }
    _validate_public_payload_no_leakage(
        wrapper_payload,
        field="result_envelope.wrapper",
        validate_strings=True,
    )


def _comment_result_requires_cursor_context(payload: Mapping[str, Any]) -> bool:
    next_continuation = payload.get("next_continuation")
    if isinstance(next_continuation, Mapping) and next_continuation.get("resume_comment_ref") is not None:
        return True
    items = payload.get("items")
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        return False
    for item in items:
        if not isinstance(item, Mapping):
            continue
        normalized = item.get("normalized")
        if not isinstance(normalized, Mapping):
            continue
        if normalized.get("parent_comment_ref") is not None or normalized.get("target_comment_ref") is not None:
            return True
    return False


def _validate_batch_audit_trace(envelope: BatchResultEnvelope) -> None:
    audit_trace = envelope.audit_trace
    allowed_fields = {
        "batch_id",
        "started_at",
        "finished",
        "item_count",
        "item_trace_refs",
        "evidence_refs",
        "stop_reason",
    }
    required_fields = allowed_fields - {"stop_reason"}
    missing = sorted(field for field in required_fields if field not in audit_trace)
    extra = sorted(set(audit_trace) - allowed_fields)
    if missing or extra:
        raise BatchDatasetContractError(
            "invalid_batch_audit_trace",
            "batch audit_trace does not match the public carrier schema",
            details={"missing": missing, "extra": extra},
        )
    if audit_trace["batch_id"] != envelope.batch_id:
        raise BatchDatasetContractError(
            "invalid_batch_audit_trace",
            "batch audit_trace.batch_id must match batch_id",
            details={"batch_id": audit_trace["batch_id"], "expected": envelope.batch_id},
        )
    _validate_public_timestamp(audit_trace["started_at"], field="audit_trace.started_at")
    if not isinstance(audit_trace["finished"], bool):
        raise BatchDatasetContractError("invalid_batch_audit_trace", "batch audit_trace.finished must be boolean")
    if not isinstance(audit_trace["item_count"], int) or isinstance(audit_trace["item_count"], bool):
        raise BatchDatasetContractError("invalid_batch_audit_trace", "batch audit_trace.item_count must be an integer")
    if audit_trace["item_count"] != len(envelope.item_outcomes):
        raise BatchDatasetContractError(
            "invalid_batch_audit_trace",
            "batch audit_trace.item_count must match item outcomes",
            details={"item_count": audit_trace["item_count"], "expected": len(envelope.item_outcomes)},
        )
    item_trace_refs = _validate_sanitized_ref_sequence(audit_trace["item_trace_refs"], field="audit_trace.item_trace_refs")
    expected_trace_refs = tuple(_item_trace_ref(envelope.batch_id, outcome.item_id) for outcome in envelope.item_outcomes)
    if item_trace_refs != expected_trace_refs:
        raise BatchDatasetContractError(
            "invalid_batch_audit_trace",
            "batch audit_trace.item_trace_refs must bind to item outcomes",
            details={"item_trace_refs": item_trace_refs, "expected": expected_trace_refs},
        )
    _validate_sanitized_ref_sequence(audit_trace["evidence_refs"], field="audit_trace.evidence_refs")
    if "stop_reason" in audit_trace:
        _validate_sanitized_ref(
            _require_non_empty_string(audit_trace["stop_reason"], field="audit_trace.stop_reason"),
            field="audit_trace.stop_reason",
        )


def _validate_sanitized_ref_sequence(value: Any, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise BatchDatasetContractError("invalid_batch_audit_trace", f"{field} must be a sequence")
    refs: list[str] = []
    for index, item in enumerate(value):
        refs.append(_validate_sanitized_ref(_require_non_empty_string(item, field=f"{field}[{index}]"), field=f"{field}[{index}]"))
    return tuple(refs)


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
        _validate_sanitized_ref(
            _require_non_empty_string(source_trace.get("resource_profile_ref"), field="source_trace.resource_profile_ref"),
            field="source_trace.resource_profile_ref",
        )
    _validate_public_timestamp(source_trace.get("fetched_at"), field="source_trace.fetched_at")


def _validate_provider_path(provider_path: str) -> None:
    forbidden = (
        "http://",
        "https://",
        "s3://",
        "gs://",
        "storage://",
        "file://",
        "/tmp/",
        "/var/",
        "/users/",
        "/home/",
        "/etc/",
        "\\",
        "token=",
        "private",
        "download",
        "bucket",
        "raw",
        "credential",
        "secret",
        "signed",
        "storage-handle",
        "route",
        "routing",
        "fallback",
        "marketplace",
        "account-pool",
        "proxy-pool",
    )
    normalized = _require_non_empty_string(provider_path, field="source_trace.provider_path")
    stripped = normalized.strip()
    if stripped != normalized:
        raise BatchDatasetContractError("unsafe_provider_path", "source_trace.provider_path must not contain surrounding whitespace")
    if stripped.startswith("/") or _is_windows_absolute_path(stripped):
        raise BatchDatasetContractError("unsafe_provider_path", "source_trace.provider_path must not be a local absolute path")
    lowered = stripped.lower()
    if any(token in lowered for token in forbidden):
        raise BatchDatasetContractError("unsafe_provider_path", "source_trace.provider_path must be a sanitized alias")


def _validate_target_ref(operation: str, value: str, *, field: str) -> str:
    normalized = _require_non_empty_string(value, field=field)
    if operation == "content_search_by_keyword":
        _ensure_json_safe(normalized, field=field)
        _validate_search_keyword(normalized, field=field)
        return normalized
    return _validate_sanitized_ref(normalized, field=field)


def _validate_search_keyword(value: str, *, field: str) -> None:
    stripped = value.strip()
    lowered = stripped.lower()
    if stripped.startswith("/") or stripped.startswith("\\") or any(
        token in lowered
        for token in (
            "http://",
            "https://",
            "s3://",
            "gs://",
            "storage://",
            "file://",
            "/tmp/",
            "/var/",
            "/users/",
            "/home/",
            "/etc/",
            "\\",
            "token=",
        )
    ):
        raise BatchDatasetContractError(
            "unsafe_public_payload",
            "search keyword contains a raw path, storage handle, or private token",
            details={"field": field},
        )


def _validate_public_timestamp(value: Any, *, field: str) -> str:
    normalized = _require_non_empty_string(value, field=field)
    if not is_valid_rfc3339_utc(normalized):
        raise BatchDatasetContractError(
            "invalid_timestamp",
            f"{field} must be an RFC3339 UTC timestamp",
            details={"field": field},
        )
    _validate_public_payload_string(normalized, field=field)
    return normalized


def _validate_sanitized_ref(value: str, *, field: str) -> str:
    normalized = _require_non_empty_string(value, field=field)
    stripped = normalized.strip()
    if stripped != normalized:
        raise BatchDatasetContractError("unsafe_ref", f"{field} contains surrounding whitespace", details={"field": field})
    lowered = stripped.lower()
    if stripped.startswith("/") or _is_windows_absolute_path(stripped):
        raise BatchDatasetContractError("unsafe_ref", f"{field} contains a local absolute path", details={"field": field})
    if _contains_relative_path_ref(stripped):
        raise BatchDatasetContractError("unsafe_ref", f"{field} contains a relative path", details={"field": field})
    if any(token in lowered for token in _FORBIDDEN_REF_TOKENS):
        raise BatchDatasetContractError("unsafe_ref", f"{field} contains forbidden private or storage token", details={"field": field})
    _ensure_json_safe(stripped, field=field)
    return stripped


def _contains_relative_path_ref(value: str) -> bool:
    lowered = value.lower()
    if lowered.startswith(("../", "./")) or any(token in lowered for token in ("/../", "/./")):
        return True
    if lowered.endswith(("/..", "/.")):
        return True
    if "/" in value:
        return "://" not in value
    return False


def _strip_normalized_payload_private_fields(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _strip_normalized_payload_private_fields(item)
            for key, item in value.items()
            if not _is_private_normalized_payload_key(str(key))
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
            if _is_private_normalized_payload_key(key_text):
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
        _validate_normalized_payload_string(value, field=field)


def _validate_public_payload_no_leakage(value: Any, *, field: str, validate_strings: bool) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text == "source_trace" and isinstance(item, Mapping):
                _validate_source_trace(item)
                continue
            _validate_public_payload_key(key_text, field=f"{field}.{key_text}")
            if _is_public_ref_value_key(key_text) and item is not None:
                _validate_sanitized_ref(
                    _require_non_empty_string(item, field=f"{field}.{key_text}"),
                    field=f"{field}.{key_text}",
                )
            _validate_public_payload_no_leakage(
                item,
                field=f"{field}.{key_text}",
                validate_strings=validate_strings,
            )
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _validate_public_payload_no_leakage(
                item,
                field=f"{field}[{index}]",
                validate_strings=validate_strings,
            )
        return
    if validate_strings and isinstance(value, str):
        _validate_public_payload_string(value, field=field)


def _validate_public_payload_key(key: str, *, field: str) -> None:
    lowered = key.lower()
    if lowered == "raw_payload_ref":
        return
    compact = _compact_private_key(lowered)
    if any(token in lowered for token in _FORBIDDEN_PUBLIC_PAYLOAD_KEY_TOKENS) or any(
        _compact_private_key(token) in compact for token in _FORBIDDEN_PUBLIC_PAYLOAD_KEY_TOKENS
    ):
        raise BatchDatasetContractError(
            "unsafe_public_payload",
            "public batch/dataset carrier contains a private field",
            details={"field": field},
        )


def _validate_public_payload_string(value: str, *, field: str) -> None:
    stripped = value.strip()
    lowered = stripped.lower()
    if stripped.startswith("/") or _is_windows_absolute_path(stripped) or any(
        token in lowered
        for token in (
            "http://",
            "https://",
            "s3://",
            "gs://",
            "storage://",
            "file://",
            "/tmp/",
            "/var/",
            "/users/",
            "/home/",
            "/etc/",
            "\\",
            "token=",
        )
    ):
        raise BatchDatasetContractError(
            "unsafe_public_payload",
            "public batch/dataset carrier contains a raw path, storage handle, or private token",
            details={"field": field},
        )


def _validate_normalized_payload_string(value: str, *, field: str) -> None:
    stripped = value.strip()
    lowered = stripped.lower()
    if stripped.startswith("/") or stripped.startswith("\\") or _is_windows_absolute_path(stripped):
        raise BatchDatasetContractError(
            "unsafe_normalized_payload",
            "normalized_payload contains a raw path, storage handle, or private token",
            details={"field": field},
        )
    if lowered.startswith(("s3://", "gs://", "storage://", "file://")):
        raise BatchDatasetContractError(
            "unsafe_normalized_payload",
            "normalized_payload contains a raw path, storage handle, or private token",
            details={"field": field},
        )
    if lowered.startswith(("http://", "https://")):
        if not _is_normalized_public_url_ref_field(field) or any(token in lowered for token in _FORBIDDEN_PUBLIC_URL_TOKENS):
            raise BatchDatasetContractError(
                "unsafe_normalized_payload",
                "normalized_payload contains a raw path, storage handle, or private token",
                details={"field": field},
            )
        return
    if any(token in lowered for token in ("token=", "account-pool", "proxy-pool", "storage-handle")):
        raise BatchDatasetContractError(
            "unsafe_normalized_payload",
            "normalized_payload contains a raw path, storage handle, or private token",
            details={"field": field},
        )


def _is_windows_absolute_path(value: str) -> bool:
    return len(value) >= 3 and value[1] == ":" and value[0].isalpha() and value[2] in {"/", "\\"}


def _is_normalized_public_url_ref_field(field: str) -> bool:
    key = field.rsplit(".", 1)[-1]
    return _compact_private_key(key) in _NORMALIZED_PUBLIC_URL_REF_COMPACT_KEYS


def _is_private_normalized_payload_key(key: str) -> bool:
    lowered = key.lower()
    compact = _compact_private_key(lowered)
    return lowered in _FORBIDDEN_NORMALIZED_PAYLOAD_KEYS or any(
        _compact_private_key(token) == compact for token in _FORBIDDEN_NORMALIZED_PAYLOAD_KEYS
    )


def _is_public_ref_value_key(key: str) -> bool:
    lowered = key.lower()
    compact = _compact_private_key(lowered)
    return lowered in _PUBLIC_REF_VALUE_KEYS or any(
        _compact_private_key(token) == compact for token in _PUBLIC_REF_VALUE_KEYS
    )


def _compact_private_key(value: str) -> str:
    return "".join(char for char in value.lower() if char not in {"_", "-", " "})


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
        json.dumps(value, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise BatchDatasetContractError(
            "non_json_safe_value",
            f"{field} must be JSON-safe",
            details={"field": field, "error": str(error)},
        ) from error
