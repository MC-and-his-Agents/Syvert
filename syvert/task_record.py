from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
import re
from typing import Any

from syvert.read_side_collection import (
    COMMENT_COLLECTION_OPERATION,
    READ_SIDE_COLLECTION_OPERATIONS,
    comment_collection_result_envelope_from_dict,
    collection_result_envelope_from_dict,
)

TASK_RECORD_SCHEMA_VERSION = "v0.3.0"
TASK_RECORD_STATUSES = frozenset({"accepted", "running", "succeeded", "failed"})
TASK_LOG_STAGES = frozenset({"admission", "execution", "completion"})
TASK_LOG_LEVELS = frozenset({"info", "error"})
TASK_LOG_STAGE_ORDER = {"admission": 0, "execution": 1, "completion": 2}
SHARED_CAPABILITIES = frozenset(
    {
        "content_detail_by_url",
        "content_search_by_keyword",
        "content_list_by_creator",
        "comment_collection",
        "media_asset_fetch_by_ref",
    }
)
SHARED_TARGET_TYPES = frozenset({"url", "content", "content_id", "creator", "creator_id", "keyword", "media_ref"})
SHARED_COLLECTION_MODES = frozenset({"public", "authenticated", "hybrid", "paginated", "direct"})
ALLOWED_CONTENT_TYPES = frozenset({"video", "image_post", "mixed_media", "unknown"})
MEDIA_ASSET_CONTENT_TYPES = frozenset({"image", "video"})
MEDIA_ASSET_FETCH_MODES = frozenset({"metadata_only", "preserve_source_ref", "download_if_allowed", "download_required"})
MEDIA_ASSET_FETCH_OUTCOMES = frozenset({"metadata_only", "source_ref_preserved", "downloaded_bytes"})
MEDIA_ASSET_RESULT_STATUSES = frozenset({"complete", "unavailable", "failed"})
MEDIA_ASSET_UNAVAILABLE_CLASSIFICATIONS = frozenset({"media_unavailable", "permission_denied"})
MEDIA_ASSET_FAILED_CLASSIFICATIONS = frozenset(
    {
        "unsupported_content_type",
        "fetch_policy_denied",
        "rate_limited",
        "platform_failed",
        "provider_or_network_blocked",
        "parse_failed",
        "credential_invalid",
        "verification_required",
        "signature_or_request_invalid",
    }
)
MEDIA_ASSET_FORBIDDEN_REF_VALUE_TOKENS = (
    "http://",
    "https://",
    "file://",
    "/tmp/",
    "/var/",
    "\\",
    "token=",
    "session",
    "credential",
    "secret",
    "signed",
    "bucket",
    "download",
    "fallback",
    "selector",
    "route",
    "routing",
)
ALLOWED_ERROR_CATEGORIES = frozenset({"invalid_input", "unsupported", "runtime_contract", "platform"})
RUNTIME_FAILURE_PHASES = frozenset(
    {
        "admission",
        "pre_execution",
        "resource_acquire",
        "adapter_execution",
        "timeout",
        "retry_exhausted",
        "concurrency_rejected",
        "persistence",
        "observability",
    }
)
RUNTIME_STRUCTURED_LOG_EVENT_TYPES = frozenset(
    {
        "task_accepted",
        "task_running",
        "attempt_started",
        "attempt_finished",
        "retry_scheduled",
        "timeout_triggered",
        "admission_concurrency_rejected",
        "retry_concurrency_rejected",
        "task_failed",
        "task_succeeded",
        "observability_write_failed",
    }
)
RUNTIME_STRUCTURED_LOG_LEVELS = frozenset({"info", "warning", "error"})
RUNTIME_EXECUTION_METRIC_NAMES = frozenset(
    {
        "task_started_total",
        "task_succeeded_total",
        "task_failed_total",
        "attempt_started_total",
        "retry_scheduled_total",
        "timeout_total",
        "admission_concurrency_rejected_total",
        "retry_concurrency_rejected_total",
        "execution_duration_ms",
    }
)
RUNTIME_RESULT_REF_TYPES = frozenset({"ExecutionAttemptOutcome", "ExecutionControlEvent"})
EXECUTION_ATTEMPT_OUTCOMES = frozenset({"succeeded", "failed", "timeout"})
EXECUTION_CONTROL_EVENT_TYPES = frozenset(
    {"admission_concurrency_rejected", "retry_concurrency_rejected", "retry_exhausted"}
)
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")


class TaskRecordContractError(ValueError):
    pass


@dataclass(frozen=True)
class TaskRequestSnapshot:
    adapter_key: str
    capability: str
    target_type: str
    target_value: str
    collection_mode: str


@dataclass(frozen=True)
class TaskLogEntry:
    sequence: int
    occurred_at: str
    stage: str
    level: str
    message: str
    code: str | None = None


@dataclass(frozen=True)
class TaskTerminalResult:
    envelope: dict[str, Any]


@dataclass(frozen=True)
class TaskRecord:
    schema_version: str
    task_id: str
    request: TaskRequestSnapshot
    status: str
    created_at: str
    updated_at: str
    terminal_at: str | None
    result: TaskTerminalResult | None
    logs: tuple[TaskLogEntry, ...]
    task_record_ref: str | None = None
    runtime_result_refs: tuple[Any, ...] = field(default_factory=tuple)
    execution_control_events: tuple[Any, ...] = field(default_factory=tuple)
    runtime_failure_signals: tuple[Any, ...] = field(default_factory=tuple)
    runtime_structured_log_events: tuple[Any, ...] = field(default_factory=tuple)
    runtime_execution_metric_samples: tuple[Any, ...] = field(default_factory=tuple)


def now_rfc3339_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def task_record_ref_for(task_id: str) -> str:
    return f"task_record:{task_id}"


def _runtime_structured_log_event(
    *,
    task_id: str,
    adapter_key: str,
    capability: str,
    event_type: str,
    level: str,
    occurred_at: str,
    message: str,
    attempt_index: int = 0,
    failure_signal_id: str = "",
    resource_trace_refs: tuple[Any, ...] | list[Any] | None = None,
    runtime_result_refs: tuple[Any, ...] | list[Any] | None = None,
) -> dict[str, Any]:
    return {
        "event_id": f"runtime_log:{task_id}:{event_type}:{attempt_index}",
        "task_id": task_id,
        "adapter_key": adapter_key,
        "capability": capability,
        "event_type": event_type,
        "level": level,
        "attempt_index": attempt_index,
        "failure_signal_id": failure_signal_id,
        "resource_trace_refs": list(resource_trace_refs or []),
        "runtime_result_refs": list(runtime_result_refs or []),
        "message": message,
        "occurred_at": occurred_at,
    }


def _runtime_execution_metric_sample(
    *,
    task_id: str,
    adapter_key: str,
    capability: str,
    metric_name: str,
    metric_value: int | float,
    unit: str,
    occurred_at: str,
    attempt_index: int = 0,
    error_category: str = "",
    error_code: str = "",
    failure_phase: str = "",
) -> dict[str, Any]:
    return {
        "metric_id": f"runtime_metric:{task_id}:{metric_name}:{attempt_index}",
        "task_id": task_id,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "unit": unit,
        "adapter_key": adapter_key,
        "capability": capability,
        "error_category": error_category,
        "error_code": error_code,
        "failure_phase": failure_phase,
        "attempt_index": attempt_index,
        "occurred_at": occurred_at,
    }


def build_task_request_snapshot(request: Any) -> TaskRequestSnapshot:
    try:
        target = request.target
        policy = request.policy
        snapshot = TaskRequestSnapshot(
            adapter_key=target.adapter_key,
            capability=target.capability,
            target_type=target.target_type,
            target_value=target.target_value,
            collection_mode=policy.collection_mode,
        )
    except AttributeError as error:
        raise TaskRecordContractError("TaskRequestSnapshot 缺少共享请求字段") from error
    validate_request_snapshot(snapshot)
    return snapshot


def create_task_record(
    task_id: str,
    request: TaskRequestSnapshot,
    *,
    occurred_at: str | None = None,
    existing: TaskRecord | None = None,
) -> TaskRecord:
    timestamp = occurred_at or now_rfc3339_utc()
    validate_request_snapshot(request)
    validate_timestamp(timestamp, field="occurred_at")
    if existing is not None:
        validate_task_record(existing)
        if existing.task_id != task_id:
            raise TaskRecordContractError("重复建档必须绑定同一 task_id")
        if existing.request != request:
            raise TaskRecordContractError("重复建档时请求快照不一致")
        if existing.status != "accepted":
            raise TaskRecordContractError("重复建档只能对既有 accepted 记录执行幂等 no-op")
        return existing

    record = TaskRecord(
        schema_version=TASK_RECORD_SCHEMA_VERSION,
        task_id=task_id,
        request=request,
        status="accepted",
        created_at=timestamp,
        updated_at=timestamp,
        terminal_at=None,
        result=None,
        logs=(
            TaskLogEntry(
                sequence=1,
                occurred_at=timestamp,
                stage="admission",
                level="info",
                message="task accepted",
            ),
        ),
        task_record_ref=task_record_ref_for(task_id),
        runtime_structured_log_events=(
            _runtime_structured_log_event(
                task_id=task_id,
                adapter_key=request.adapter_key,
                capability=request.capability,
                event_type="task_accepted",
                level="info",
                occurred_at=timestamp,
                message="task accepted",
            ),
        ),
        runtime_execution_metric_samples=(
            _runtime_execution_metric_sample(
                task_id=task_id,
                adapter_key=request.adapter_key,
                capability=request.capability,
                metric_name="task_started_total",
                metric_value=1,
                unit="count",
                occurred_at=timestamp,
            ),
        ),
    )
    validate_task_record(record)
    return record


def start_task_record(record: TaskRecord, *, occurred_at: str | None = None) -> TaskRecord:
    validate_task_record(record)
    if record.status == "running":
        return record
    if record.status != "accepted":
        raise TaskRecordContractError("只有 accepted 记录可以进入 running")
    timestamp = occurred_at or now_rfc3339_utc()
    validate_timestamp(timestamp, field="occurred_at")
    updated = TaskRecord(
        schema_version=record.schema_version,
        task_id=record.task_id,
        request=record.request,
        status="running",
        created_at=record.created_at,
        updated_at=timestamp,
        terminal_at=None,
        result=None,
        logs=record.logs
        + (
            TaskLogEntry(
                sequence=len(record.logs) + 1,
                occurred_at=timestamp,
                stage="execution",
                level="info",
                message="task execution started",
            ),
        ),
        task_record_ref=record.task_record_ref,
        runtime_result_refs=record.runtime_result_refs,
        execution_control_events=record.execution_control_events,
        runtime_failure_signals=record.runtime_failure_signals,
        runtime_structured_log_events=record.runtime_structured_log_events
        + (
            _runtime_structured_log_event(
                task_id=record.task_id,
                adapter_key=record.request.adapter_key,
                capability=record.request.capability,
                event_type="task_running",
                level="info",
                occurred_at=timestamp,
                message="task running",
            ),
        ),
        runtime_execution_metric_samples=record.runtime_execution_metric_samples,
    )
    validate_task_record(updated)
    return updated


def finish_task_record(record: TaskRecord, envelope: Mapping[str, Any], *, occurred_at: str | None = None) -> TaskRecord:
    validate_task_record(record)
    terminal_status = terminal_record_status(envelope)
    normalized_envelope = normalize_json_value(envelope, field="result.envelope")
    if not isinstance(normalized_envelope, dict):
        raise TaskRecordContractError("TaskTerminalResult.envelope 必须是对象")
    private_failure_signals = normalized_envelope.pop("_runtime_failure_signals", None)
    private_structured_log_events = normalized_envelope.pop("_runtime_structured_log_events", None)
    private_metric_samples = normalized_envelope.pop("_runtime_execution_metric_samples", None)
    if terminal_status == "succeeded":
        normalized_envelope.pop("runtime_failure_signal", None)
        normalized_envelope.pop("runtime_failure_signals", None)
        normalized_envelope.pop("runtime_structured_log_events", None)
        normalized_envelope.pop("runtime_execution_metric_samples", None)
    task_record_ref = _observability_task_record_ref(normalized_envelope, record)
    if task_record_ref is not None and "task_record_ref" not in normalized_envelope:
        normalized_envelope["task_record_ref"] = task_record_ref
    if record.status in {"succeeded", "failed"}:
        if record.result is None:
            raise TaskRecordContractError("终态记录缺少终态结果")
        if terminal_status != record.status:
            raise TaskRecordContractError("重复终态写入试图改写既有终态状态")
        if record.result.envelope != normalized_envelope:
            raise TaskRecordContractError("重复终态写入试图改写既有终态 envelope")
        return record
    if record.status != "running":
        raise TaskRecordContractError("只有 running 记录可以进入终态")

    timestamp = occurred_at or now_rfc3339_utc()
    validate_timestamp(timestamp, field="occurred_at")
    log_level = "error" if terminal_status == "failed" else "info"
    log_message = "task failed" if terminal_status == "failed" else "task succeeded"
    log_code = None
    error = envelope.get("error")
    if isinstance(error, Mapping):
        code = error.get("code")
        if isinstance(code, str) and code:
            log_code = code

    runtime_failure_signals = (
        record.runtime_failure_signals
        + _observability_entries({"runtime_failure_signals": private_failure_signals}, "runtime_failure_signals", ())
        + _runtime_failure_signals(normalized_envelope, ())
        if private_failure_signals is not None
        else _runtime_failure_signals(normalized_envelope, record.runtime_failure_signals)
    )
    runtime_structured_log_events = record.runtime_structured_log_events + _observability_entries(
        {"runtime_structured_log_events": private_structured_log_events}
        if private_structured_log_events is not None
        else normalized_envelope,
        "runtime_structured_log_events",
        (),
    )
    runtime_execution_metric_samples = record.runtime_execution_metric_samples + _observability_entries(
        {"runtime_execution_metric_samples": private_metric_samples}
        if private_metric_samples is not None
        else normalized_envelope,
        "runtime_execution_metric_samples",
        (),
    )
    if terminal_status == "succeeded":
        runtime_structured_log_events = runtime_structured_log_events + (
            _runtime_structured_log_event(
                task_id=record.task_id,
                adapter_key=record.request.adapter_key,
                capability=record.request.capability,
                event_type="task_succeeded",
                level="info",
                occurred_at=timestamp,
                message="task succeeded",
            ),
        )
        runtime_execution_metric_samples = runtime_execution_metric_samples + (
            _runtime_execution_metric_sample(
                task_id=record.task_id,
                adapter_key=record.request.adapter_key,
                capability=record.request.capability,
                metric_name="task_succeeded_total",
                metric_value=1,
                unit="count",
                occurred_at=timestamp,
            ),
            _runtime_execution_metric_sample(
                task_id=record.task_id,
                adapter_key=record.request.adapter_key,
                capability=record.request.capability,
                metric_name="execution_duration_ms",
                metric_value=max(
                    0,
                    int((parse_timestamp(timestamp, field="terminal_at") - parse_timestamp(record.created_at, field="created_at")).total_seconds() * 1000),
                ),
                unit="ms",
                occurred_at=timestamp,
            ),
        )

    updated = TaskRecord(
        schema_version=record.schema_version,
        task_id=record.task_id,
        request=record.request,
        status=terminal_status,
        created_at=record.created_at,
        updated_at=timestamp,
        terminal_at=timestamp,
        result=TaskTerminalResult(envelope=normalized_envelope),
        logs=record.logs
        + (
            TaskLogEntry(
                sequence=len(record.logs) + 1,
                occurred_at=timestamp,
                stage="completion",
                level=log_level,
                message=log_message,
                code=log_code,
            ),
        ),
        task_record_ref=task_record_ref,
        runtime_result_refs=_observability_entries(normalized_envelope, "runtime_result_refs", record.runtime_result_refs),
        execution_control_events=_observability_entries(
            normalized_envelope,
            "execution_control_events",
            record.execution_control_events,
        ),
        runtime_failure_signals=runtime_failure_signals,
        runtime_structured_log_events=runtime_structured_log_events,
        runtime_execution_metric_samples=runtime_execution_metric_samples,
    )
    validate_task_record(updated)
    return updated


def task_record_to_dict(record: TaskRecord) -> dict[str, Any]:
    validate_task_record(record)
    payload: dict[str, Any] = {
        "schema_version": record.schema_version,
        "task_id": record.task_id,
        "request": {
            "adapter_key": record.request.adapter_key,
            "capability": record.request.capability,
            "target_type": record.request.target_type,
            "target_value": record.request.target_value,
            "collection_mode": record.request.collection_mode,
        },
        "status": record.status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "terminal_at": record.terminal_at,
        "result": None,
        "task_record_ref": record.task_record_ref,
        "runtime_result_refs": list(record.runtime_result_refs),
        "execution_control_events": list(record.execution_control_events),
        "runtime_failure_signals": list(record.runtime_failure_signals),
        "runtime_structured_log_events": list(record.runtime_structured_log_events),
        "runtime_execution_metric_samples": list(record.runtime_execution_metric_samples),
        "logs": [
            {
                "sequence": entry.sequence,
                "occurred_at": entry.occurred_at,
                "stage": entry.stage,
                "level": entry.level,
                "message": entry.message,
                "code": entry.code,
            }
            for entry in record.logs
        ],
    }
    if record.result is not None:
        payload["result"] = {
            "envelope": normalize_json_value(record.result.envelope, field="result.envelope"),
        }
    return payload


def task_record_from_dict(payload: Mapping[str, Any]) -> TaskRecord:
    if not isinstance(payload, Mapping):
        raise TaskRecordContractError("TaskRecord 载荷必须是对象")
    request_payload = payload.get("request")
    if not isinstance(request_payload, Mapping):
        raise TaskRecordContractError("TaskRecord.request 必须是对象")
    logs_payload = payload.get("logs")
    if not isinstance(logs_payload, list):
        raise TaskRecordContractError("TaskRecord.logs 必须是数组")
    task_id = require_string(payload.get("task_id"), field="task_id")
    result_payload = payload.get("result")
    result: TaskTerminalResult | None = None
    if result_payload is not None:
        if not isinstance(result_payload, Mapping):
            raise TaskRecordContractError("TaskRecord.result 必须是对象或 null")
        envelope = result_payload.get("envelope")
        if not isinstance(envelope, Mapping):
            raise TaskRecordContractError("TaskTerminalResult.envelope 必须是对象")
        normalized_envelope = dict(normalize_json_value(envelope, field="result.envelope"))
        normalized_envelope.setdefault("task_record_ref", task_record_ref_for(task_id))
        result = TaskTerminalResult(envelope=normalized_envelope)

    record = TaskRecord(
        schema_version=require_string(payload.get("schema_version"), field="schema_version"),
        task_id=task_id,
        request=TaskRequestSnapshot(
            adapter_key=require_string(request_payload.get("adapter_key"), field="request.adapter_key"),
            capability=require_string(request_payload.get("capability"), field="request.capability"),
            target_type=require_string(request_payload.get("target_type"), field="request.target_type"),
            target_value=require_string(request_payload.get("target_value"), field="request.target_value"),
            collection_mode=require_string(request_payload.get("collection_mode"), field="request.collection_mode"),
        ),
        status=require_string(payload.get("status"), field="status"),
        created_at=require_string(payload.get("created_at"), field="created_at"),
        updated_at=require_string(payload.get("updated_at"), field="updated_at"),
        terminal_at=require_optional_string(payload.get("terminal_at"), field="terminal_at"),
        result=result,
        logs=tuple(
            TaskLogEntry(
                sequence=coerce_int(entry.get("sequence"), field="logs.sequence"),
                occurred_at=require_string(entry.get("occurred_at"), field="logs.occurred_at"),
                stage=require_string(entry.get("stage"), field="logs.stage"),
                level=require_string(entry.get("level"), field="logs.level"),
                message=require_string(entry.get("message"), field="logs.message"),
                code=require_optional_string(entry.get("code"), field="logs.code"),
            )
            for entry in logs_payload
            if isinstance(entry, Mapping)
        ),
        task_record_ref=require_optional_string(
            payload.get("task_record_ref", task_record_ref_for(task_id)),
            field="task_record_ref",
        ),
        runtime_result_refs=_observability_entries(payload, "runtime_result_refs", ()),
        execution_control_events=_observability_entries(payload, "execution_control_events", ()),
        runtime_failure_signals=_observability_entries(payload, "runtime_failure_signals", ()),
        runtime_structured_log_events=_observability_entries(payload, "runtime_structured_log_events", ()),
        runtime_execution_metric_samples=_observability_entries(payload, "runtime_execution_metric_samples", ()),
    )
    if len(record.logs) != len(logs_payload):
        raise TaskRecordContractError("TaskRecord.logs 项必须全部为对象")
    validate_task_record(record)
    return record


def validate_task_record(record: TaskRecord) -> None:
    if record.schema_version != TASK_RECORD_SCHEMA_VERSION:
        raise TaskRecordContractError("TaskRecord.schema_version 不合法")
    if not isinstance(record.task_id, str) or not record.task_id:
        raise TaskRecordContractError("TaskRecord.task_id 必须为非空字符串")
    task_record_ref = require_optional_string(record.task_record_ref, field="TaskRecord.task_record_ref")
    if task_record_ref != task_record_ref_for(record.task_id):
        raise TaskRecordContractError("TaskRecord.task_record_ref 必须与 task_id 绑定一致")
    if _observability_entries({"runtime_result_refs": record.runtime_result_refs}, "runtime_result_refs", ()) != record.runtime_result_refs:
        raise TaskRecordContractError("TaskRecord.runtime_result_refs 必须预先满足 JSON-safe 约束")
    if (
        _observability_entries({"execution_control_events": record.execution_control_events}, "execution_control_events", ())
        != record.execution_control_events
    ):
        raise TaskRecordContractError("TaskRecord.execution_control_events 必须预先满足 JSON-safe 约束")
    if (
        _observability_entries({"runtime_failure_signals": record.runtime_failure_signals}, "runtime_failure_signals", ())
        != record.runtime_failure_signals
    ):
        raise TaskRecordContractError("TaskRecord.runtime_failure_signals 必须预先满足 JSON-safe 约束")
    validate_observability_replay_ids(record.runtime_failure_signals, id_field="signal_id", field="runtime_failure_signals")
    validate_runtime_failure_signals(record)
    if (
        _observability_entries(
            {"runtime_structured_log_events": record.runtime_structured_log_events},
            "runtime_structured_log_events",
            (),
        )
        != record.runtime_structured_log_events
    ):
        raise TaskRecordContractError("TaskRecord.runtime_structured_log_events 必须预先满足 JSON-safe 约束")
    validate_observability_replay_ids(
        record.runtime_structured_log_events,
        id_field="event_id",
        field="runtime_structured_log_events",
    )
    validate_runtime_structured_log_events(record)
    if (
        _observability_entries(
            {"runtime_execution_metric_samples": record.runtime_execution_metric_samples},
            "runtime_execution_metric_samples",
            (),
        )
        != record.runtime_execution_metric_samples
    ):
        raise TaskRecordContractError("TaskRecord.runtime_execution_metric_samples 必须预先满足 JSON-safe 约束")
    validate_observability_replay_ids(
        record.runtime_execution_metric_samples,
        id_field="metric_id",
        field="runtime_execution_metric_samples",
    )
    validate_runtime_execution_metric_samples(record)
    validate_request_snapshot(record.request)
    if record.status not in TASK_RECORD_STATUSES:
        raise TaskRecordContractError("TaskRecord.status 不在允许值范围内")
    created_at = parse_timestamp(record.created_at, field="created_at")
    updated_at = parse_timestamp(record.updated_at, field="updated_at")
    if updated_at < created_at:
        raise TaskRecordContractError("TaskRecord.updated_at 不得早于 created_at")
    terminal_at = None
    if record.terminal_at is not None:
        terminal_at = parse_timestamp(record.terminal_at, field="terminal_at")
        if terminal_at < updated_at:
            raise TaskRecordContractError("TaskRecord.terminal_at 不得早于 updated_at")
    if not record.logs:
        raise TaskRecordContractError("TaskRecord.logs 不得为空")

    last_sequence = 0
    stage_counts = {stage: 0 for stage in TASK_LOG_STAGES}
    previous_occurred_at: datetime | None = None
    previous_stage_order = -1
    final_log_at: datetime | None = None
    final_stage: str | None = None
    for entry in record.logs:
        if isinstance(entry.sequence, bool) or not isinstance(entry.sequence, int) or entry.sequence <= 0:
            raise TaskRecordContractError("TaskLogEntry.sequence 必须为正整数")
        if entry.sequence != last_sequence + 1:
            raise TaskRecordContractError("TaskRecord.logs.sequence 必须连续递增")
        last_sequence = entry.sequence
        occurred_at = parse_timestamp(entry.occurred_at, field="logs.occurred_at")
        if previous_occurred_at is not None and occurred_at < previous_occurred_at:
            raise TaskRecordContractError("TaskRecord.logs.occurred_at 必须随 sequence 单调推进")
        previous_occurred_at = occurred_at
        if entry.stage not in TASK_LOG_STAGES:
            raise TaskRecordContractError("TaskLogEntry.stage 不在允许值范围内")
        stage_order = TASK_LOG_STAGE_ORDER[entry.stage]
        if stage_order < previous_stage_order:
            raise TaskRecordContractError("TaskRecord.logs.stage 顺序不可信")
        previous_stage_order = stage_order
        if entry.level not in TASK_LOG_LEVELS:
            raise TaskRecordContractError("TaskLogEntry.level 不在允许值范围内")
        if not isinstance(entry.message, str) or not entry.message:
            raise TaskRecordContractError("TaskLogEntry.message 必须为非空字符串")
        if entry.code is not None and (not isinstance(entry.code, str) or not entry.code):
            raise TaskRecordContractError("TaskLogEntry.code 必须为非空字符串或 null")
        stage_counts[entry.stage] += 1
        final_log_at = occurred_at
        final_stage = entry.stage

    if stage_counts["admission"] != 1:
        raise TaskRecordContractError("TaskRecord 必须且只能包含一条 accepted 生命周期事件")
    if record.logs[0].stage != "admission":
        raise TaskRecordContractError("TaskRecord 第一条日志必须是 accepted 生命周期事件")
    if final_log_at is None or final_stage is None:
        raise TaskRecordContractError("TaskRecord.logs 不得为空")
    if final_log_at != updated_at:
        raise TaskRecordContractError("TaskRecord.updated_at 必须等于最后一条可信日志时间")
    if parse_timestamp(record.logs[0].occurred_at, field="logs.occurred_at") != created_at:
        raise TaskRecordContractError("TaskRecord.created_at 必须等于 accepted 生命周期事件时间")

    if record.status == "accepted":
        if stage_counts["execution"] != 0 or stage_counts["completion"] != 0 or final_stage != "admission":
            raise TaskRecordContractError("accepted TaskRecord 不得包含 execution/completion 生命周期事件")
    elif record.status == "running":
        if stage_counts["execution"] != 1 or stage_counts["completion"] != 0 or final_stage != "execution":
            raise TaskRecordContractError("running TaskRecord 必须只包含 accepted/execution 生命周期事件")
    else:
        if stage_counts["execution"] != 1 or stage_counts["completion"] != 1 or final_stage != "completion":
            raise TaskRecordContractError("终态 TaskRecord 必须包含完整且可信的生命周期事件")

    if record.status in {"accepted", "running"}:
        if record.terminal_at is not None or record.result is not None:
            raise TaskRecordContractError("非终态 TaskRecord 不得包含终态结果")
    else:
        if record.terminal_at is None or record.result is None:
            raise TaskRecordContractError("终态 TaskRecord 必须包含终态结果")
        if terminal_at != updated_at:
            raise TaskRecordContractError("终态 TaskRecord.terminal_at 必须等于最后一次可信更新")
        normalized_envelope = normalize_json_value(record.result.envelope, field="result.envelope")
        if not isinstance(normalized_envelope, dict):
            raise TaskRecordContractError("TaskTerminalResult.envelope 必须是对象")
        if normalized_envelope != record.result.envelope:
            raise TaskRecordContractError("TaskTerminalResult.envelope 必须预先满足 JSON-safe 约束")
        validate_terminal_envelope_contract(record, record.result.envelope)
        status = terminal_record_status(record.result.envelope)
        if status != record.status:
            raise TaskRecordContractError("TaskRecord.status 与终态 envelope.status 不一致")


def validate_request_snapshot(snapshot: TaskRequestSnapshot) -> None:
    adapter_key = require_string(snapshot.adapter_key, field="TaskRequestSnapshot.adapter_key")
    capability = require_string(snapshot.capability, field="TaskRequestSnapshot.capability")
    target_type = require_string(snapshot.target_type, field="TaskRequestSnapshot.target_type")
    require_string(snapshot.target_value, field="TaskRequestSnapshot.target_value")
    collection_mode = require_string(snapshot.collection_mode, field="TaskRequestSnapshot.collection_mode")
    if capability not in SHARED_CAPABILITIES:
        raise TaskRecordContractError("TaskRequestSnapshot.capability 不在共享请求模型允许值范围内")
    if target_type not in SHARED_TARGET_TYPES:
        raise TaskRecordContractError("TaskRequestSnapshot.target_type 不在共享请求模型允许值范围内")
    if collection_mode not in SHARED_COLLECTION_MODES:
        raise TaskRecordContractError("TaskRequestSnapshot.collection_mode 不在共享请求模型允许值范围内")
    if not adapter_key:
        raise TaskRecordContractError("TaskRequestSnapshot.adapter_key 必须为非空字符串")


def validate_timestamp(value: str, *, field: str) -> None:
    if not isinstance(value, str) or not RFC3339_UTC_RE.fullmatch(value):
        raise TaskRecordContractError(f"{field} 必须为 RFC3339 UTC 时间")
    if parse_timestamp(value, field=field).utcoffset() != timezone.utc.utcoffset(None):
        raise TaskRecordContractError(f"{field} 必须是 UTC 时间")


def parse_timestamp(value: str, *, field: str) -> datetime:
    if not isinstance(value, str) or not RFC3339_UTC_RE.fullmatch(value):
        raise TaskRecordContractError(f"{field} 必须为 RFC3339 UTC 时间")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise TaskRecordContractError(f"{field} 必须为 RFC3339 UTC 时间") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(None):
        raise TaskRecordContractError(f"{field} 必须是 UTC 时间")
    return parsed


def terminal_record_status(envelope: Mapping[str, Any]) -> str:
    raw_status = envelope.get("status")
    if raw_status == "success":
        return "succeeded"
    if raw_status == "failed":
        return "failed"
    raise TaskRecordContractError("终态 envelope.status 必须为 success 或 failed")


def _observability_task_record_ref(envelope: Mapping[str, Any], record: TaskRecord) -> str | None:
    raw_ref = envelope.get("task_record_ref", record.task_record_ref)
    return require_optional_string(raw_ref, field="task_record_ref")


def _observability_entries(source: Mapping[str, Any], field_name: str, default: tuple[Any, ...]) -> tuple[Any, ...]:
    raw_entries = source.get(field_name, list(default))
    normalized = normalize_json_value(raw_entries, field=field_name)
    if not isinstance(normalized, list):
        raise TaskRecordContractError(f"{field_name} 必须是数组")
    return tuple(normalized)


def validate_observability_replay_ids(entries: tuple[Any, ...], *, id_field: str, field: str) -> None:
    seen: dict[str, Any] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise TaskRecordContractError(f"TaskRecord.{field} 项必须是对象")
        entry_id = require_string(entry.get(id_field), field=f"{field}.{id_field}")
        if entry_id in seen and seen[entry_id] != entry:
            raise TaskRecordContractError(f"TaskRecord.{field} 同一 {id_field} 不得对应不同 payload")
        seen[entry_id] = entry


def validate_runtime_failure_signals(record: TaskRecord) -> None:
    for signal in record.runtime_failure_signals:
        if not isinstance(signal, Mapping):
            raise TaskRecordContractError("RuntimeFailureSignal 必须是对象")
        task_id = require_string(signal.get("task_id"), field="RuntimeFailureSignal.task_id")
        adapter_key = require_string(signal.get("adapter_key"), field="RuntimeFailureSignal.adapter_key")
        capability = require_string(signal.get("capability"), field="RuntimeFailureSignal.capability")
        if task_id != record.task_id or adapter_key != record.request.adapter_key or capability != record.request.capability:
            raise TaskRecordContractError("RuntimeFailureSignal 必须绑定同一 TaskRecord 请求上下文")
        if signal.get("status") != "failed":
            raise TaskRecordContractError("RuntimeFailureSignal.status 必须为 failed")
        category = require_string(signal.get("error_category"), field="RuntimeFailureSignal.error_category")
        if category not in ALLOWED_ERROR_CATEGORIES:
            raise TaskRecordContractError("RuntimeFailureSignal.error_category 不在允许值范围内")
        require_string(signal.get("error_code"), field="RuntimeFailureSignal.error_code")
        phase = require_string(signal.get("failure_phase"), field="RuntimeFailureSignal.failure_phase")
        if phase not in RUNTIME_FAILURE_PHASES:
            raise TaskRecordContractError("RuntimeFailureSignal.failure_phase 不在允许值范围内")
        require_string(signal.get("envelope_ref"), field="RuntimeFailureSignal.envelope_ref")
        task_record_ref = require_string(signal.get("task_record_ref"), field="RuntimeFailureSignal.task_record_ref")
        if task_record_ref != "none" and task_record_ref != record.task_record_ref:
            raise TaskRecordContractError("RuntimeFailureSignal.task_record_ref 与 TaskRecord 不一致")
        validate_resource_trace_refs(signal, field="RuntimeFailureSignal.resource_trace_refs")
        validate_runtime_result_refs(record, signal, field="RuntimeFailureSignal.runtime_result_refs")
        validate_timestamp(require_string(signal.get("occurred_at"), field="RuntimeFailureSignal.occurred_at"), field="RuntimeFailureSignal.occurred_at")


def validate_runtime_structured_log_events(record: TaskRecord) -> None:
    signal_ids = {signal.get("signal_id") for signal in record.runtime_failure_signals if isinstance(signal, Mapping)}
    for event in record.runtime_structured_log_events:
        if not isinstance(event, Mapping):
            raise TaskRecordContractError("RuntimeStructuredLogEvent 必须是对象")
        task_id = require_string(event.get("task_id"), field="RuntimeStructuredLogEvent.task_id")
        adapter_key = require_string(event.get("adapter_key"), field="RuntimeStructuredLogEvent.adapter_key")
        capability = require_string(event.get("capability"), field="RuntimeStructuredLogEvent.capability")
        if task_id != record.task_id or adapter_key != record.request.adapter_key or capability != record.request.capability:
            raise TaskRecordContractError("RuntimeStructuredLogEvent 必须绑定同一 TaskRecord 请求上下文")
        event_type = require_string(event.get("event_type"), field="RuntimeStructuredLogEvent.event_type")
        if event_type not in RUNTIME_STRUCTURED_LOG_EVENT_TYPES:
            raise TaskRecordContractError("RuntimeStructuredLogEvent.event_type 不在允许值范围内")
        level = require_string(event.get("level"), field="RuntimeStructuredLogEvent.level")
        if level not in RUNTIME_STRUCTURED_LOG_LEVELS:
            raise TaskRecordContractError("RuntimeStructuredLogEvent.level 不在允许值范围内")
        attempt_index = coerce_int(event.get("attempt_index"), field="RuntimeStructuredLogEvent.attempt_index")
        if attempt_index < 0:
            raise TaskRecordContractError("RuntimeStructuredLogEvent.attempt_index 必须为非负整数")
        failure_signal_id = event.get("failure_signal_id", "")
        if failure_signal_id is not None and not isinstance(failure_signal_id, str):
            raise TaskRecordContractError("RuntimeStructuredLogEvent.failure_signal_id 必须是字符串")
        if event_type in {
            "admission_concurrency_rejected",
            "retry_concurrency_rejected",
            "task_failed",
            "timeout_triggered",
            "retry_scheduled",
            "observability_write_failed",
        }:
            if not failure_signal_id or failure_signal_id not in signal_ids:
                raise TaskRecordContractError("失败相关 RuntimeStructuredLogEvent 必须引用对应 RuntimeFailureSignal")
        validate_resource_trace_refs(event, field="RuntimeStructuredLogEvent.resource_trace_refs")
        validate_runtime_result_refs(record, event, field="RuntimeStructuredLogEvent.runtime_result_refs")
        require_string(event.get("message"), field="RuntimeStructuredLogEvent.message")
        validate_timestamp(require_string(event.get("occurred_at"), field="RuntimeStructuredLogEvent.occurred_at"), field="RuntimeStructuredLogEvent.occurred_at")


def validate_resource_trace_refs(source: Mapping[str, Any], *, field: str) -> None:
    field_name = field.rsplit(".", 1)[-1]
    for ref in _observability_entries(source, field_name, ()):
        if not isinstance(ref, Mapping):
            raise TaskRecordContractError(f"{field} 项必须是对象")
        ref_type = require_string(ref.get("ref_type"), field=f"{field}.ref_type")
        if ref_type != "ResourceTraceEvent":
            raise TaskRecordContractError(f"{field}.ref_type 必须为 ResourceTraceEvent")
        require_string(ref.get("event_id"), field=f"{field}.event_id")
        require_string(ref.get("lease_id"), field=f"{field}.lease_id")
        require_string(ref.get("bundle_id"), field=f"{field}.bundle_id")
        require_string(ref.get("resource_id"), field=f"{field}.resource_id")
        require_string(ref.get("resource_type"), field=f"{field}.resource_type")


def validate_runtime_result_refs(record: TaskRecord, source: Mapping[str, Any], *, field: str) -> None:
    field_name = field.rsplit(".", 1)[-1]
    for ref in _observability_entries(source, field_name, ()):
        if not isinstance(ref, Mapping):
            raise TaskRecordContractError(f"{field} 项必须是对象")
        ref_type = require_string(ref.get("ref_type"), field=f"{field}.ref_type")
        if ref_type not in RUNTIME_RESULT_REF_TYPES:
            raise TaskRecordContractError(f"{field}.ref_type 不在允许值范围内")
        task_id = require_string(ref.get("task_id"), field=f"{field}.task_id")
        adapter_key = require_string(ref.get("adapter_key"), field=f"{field}.adapter_key")
        capability = require_string(ref.get("capability"), field=f"{field}.capability")
        if task_id != record.task_id or adapter_key != record.request.adapter_key or capability != record.request.capability:
            raise TaskRecordContractError(f"{field} 必须绑定同一 TaskRecord 请求上下文")
        require_string(ref.get("ref_id"), field=f"{field}.ref_id")
        if ref_type == "ExecutionAttemptOutcome":
            attempt_index = coerce_int(ref.get("attempt_index"), field=f"{field}.attempt_index")
            if attempt_index < 0:
                raise TaskRecordContractError(f"{field}.attempt_index 必须为非负整数")
            validate_timestamp(require_string(ref.get("started_at"), field=f"{field}.started_at"), field=f"{field}.started_at")
            validate_timestamp(require_string(ref.get("ended_at"), field=f"{field}.ended_at"), field=f"{field}.ended_at")
            outcome = require_string(ref.get("outcome"), field=f"{field}.outcome")
            if outcome not in EXECUTION_ATTEMPT_OUTCOMES:
                raise TaskRecordContractError(f"{field}.outcome 不在允许值范围内")
            if not isinstance(ref.get("terminal_envelope"), Mapping):
                raise TaskRecordContractError(f"{field}.terminal_envelope 必须是对象")
            control_code = ref.get("control_code", "")
            if not isinstance(control_code, str):
                raise TaskRecordContractError(f"{field}.control_code 必须是字符串")
            continue
        event_type = require_string(ref.get("event_type"), field=f"{field}.event_type")
        if event_type not in EXECUTION_CONTROL_EVENT_TYPES:
            raise TaskRecordContractError(f"{field}.event_type 不在允许值范围内")
        attempt_count = coerce_int(ref.get("attempt_count"), field=f"{field}.attempt_count")
        if attempt_count < 0:
            raise TaskRecordContractError(f"{field}.attempt_count 必须为非负整数")
        require_string(ref.get("control_code"), field=f"{field}.control_code")
        task_record_ref = require_string(ref.get("task_record_ref"), field=f"{field}.task_record_ref")
        if task_record_ref != "none" and task_record_ref != record.task_record_ref:
            raise TaskRecordContractError(f"{field}.task_record_ref 与 TaskRecord 不一致")
        if not isinstance(ref.get("policy"), Mapping):
            raise TaskRecordContractError(f"{field}.policy 必须是对象")
        validate_timestamp(require_string(ref.get("occurred_at"), field=f"{field}.occurred_at"), field=f"{field}.occurred_at")


def validate_runtime_execution_metric_samples(record: TaskRecord) -> None:
    for metric in record.runtime_execution_metric_samples:
        if not isinstance(metric, Mapping):
            raise TaskRecordContractError("RuntimeExecutionMetricSample 必须是对象")
        task_id = require_string(metric.get("task_id"), field="RuntimeExecutionMetricSample.task_id")
        adapter_key = require_string(metric.get("adapter_key"), field="RuntimeExecutionMetricSample.adapter_key")
        capability = require_string(metric.get("capability"), field="RuntimeExecutionMetricSample.capability")
        if task_id != record.task_id or adapter_key != record.request.adapter_key or capability != record.request.capability:
            raise TaskRecordContractError("RuntimeExecutionMetricSample 必须绑定同一 TaskRecord 请求上下文")
        metric_name = require_string(metric.get("metric_name"), field="RuntimeExecutionMetricSample.metric_name")
        if metric_name not in RUNTIME_EXECUTION_METRIC_NAMES:
            raise TaskRecordContractError("RuntimeExecutionMetricSample.metric_name 不在允许值范围内")
        value = metric.get("metric_value")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or math.isnan(value) or value < 0:
            raise TaskRecordContractError("RuntimeExecutionMetricSample.metric_value 必须为非负数")
        unit = require_string(metric.get("unit"), field="RuntimeExecutionMetricSample.unit")
        if metric_name == "execution_duration_ms":
            if unit != "ms":
                raise TaskRecordContractError("RuntimeExecutionMetricSample execution_duration_ms unit 必须为 ms")
        elif unit != "count" or not isinstance(value, int):
            raise TaskRecordContractError("RuntimeExecutionMetricSample 计数指标必须使用 count 整数")
        category = metric.get("error_category")
        if not isinstance(category, str):
            raise TaskRecordContractError("RuntimeExecutionMetricSample.error_category 必须是字符串")
        if category and category not in ALLOWED_ERROR_CATEGORIES:
            raise TaskRecordContractError("RuntimeExecutionMetricSample.error_category 不在允许值范围内")
        error_code = metric.get("error_code")
        if not isinstance(error_code, str):
            raise TaskRecordContractError("RuntimeExecutionMetricSample.error_code 必须是字符串")
        phase = metric.get("failure_phase")
        if not isinstance(phase, str):
            raise TaskRecordContractError("RuntimeExecutionMetricSample.failure_phase 必须是字符串")
        if phase and phase not in RUNTIME_FAILURE_PHASES:
            raise TaskRecordContractError("RuntimeExecutionMetricSample.failure_phase 不在允许值范围内")
        if metric_name in {
            "task_failed_total",
            "timeout_total",
            "admission_concurrency_rejected_total",
            "retry_concurrency_rejected_total",
        }:
            if not category or not error_code or not phase:
                raise TaskRecordContractError("失败相关 RuntimeExecutionMetricSample 必须携带错误元数据")
        attempt_index = coerce_int(metric.get("attempt_index"), field="RuntimeExecutionMetricSample.attempt_index")
        if attempt_index < 0:
            raise TaskRecordContractError("RuntimeExecutionMetricSample.attempt_index 必须为非负整数")
        validate_timestamp(require_string(metric.get("occurred_at"), field="RuntimeExecutionMetricSample.occurred_at"), field="RuntimeExecutionMetricSample.occurred_at")


def _runtime_failure_signals(envelope: Mapping[str, Any], default: tuple[Any, ...]) -> tuple[Any, ...]:
    if "runtime_failure_signal" in envelope:
        normalized = normalize_json_value(envelope["runtime_failure_signal"], field="runtime_failure_signal")
        if not isinstance(normalized, Mapping):
            raise TaskRecordContractError("runtime_failure_signal 必须是对象")
        return (dict(normalized),)
    return _observability_entries(envelope, "runtime_failure_signals", default)


def coerce_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TaskRecordContractError(f"{field} 必须为整数")
    return value


def require_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise TaskRecordContractError(f"{field} 必须为非空字符串")
    return value


def require_optional_string(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise TaskRecordContractError(f"{field} 必须为非空字符串或 null")
    return value


def validate_terminal_envelope_contract(record: TaskRecord, envelope: Mapping[str, Any]) -> None:
    task_id = require_string(envelope.get("task_id"), field="result.envelope.task_id")
    adapter_key = require_string(envelope.get("adapter_key"), field="result.envelope.adapter_key")
    capability = require_string(envelope.get("capability"), field="result.envelope.capability")
    if task_id != record.task_id:
        raise TaskRecordContractError("TaskTerminalResult.envelope.task_id 与 TaskRecord.task_id 不一致")
    if adapter_key != record.request.adapter_key:
        raise TaskRecordContractError("TaskTerminalResult.envelope.adapter_key 与请求快照不一致")
    if capability != record.request.capability:
        raise TaskRecordContractError("TaskTerminalResult.envelope.capability 与请求快照不一致")
    validate_terminal_envelope_observability_contract(record, envelope)

    status = terminal_record_status(envelope)
    if status == "succeeded":
        validate_success_terminal_envelope(envelope)
        if capability in READ_SIDE_COLLECTION_OPERATIONS:
            collection = collection_result_envelope_from_dict(_collection_result_payload_from_terminal_envelope(envelope))
            if collection.target.target_type != record.request.target_type:
                raise TaskRecordContractError("collection target_type 与请求快照不一致")
            if collection.target.target_ref != record.request.target_value:
                raise TaskRecordContractError("collection target_ref 与请求快照不一致")
        if capability == COMMENT_COLLECTION_OPERATION:
            collection = comment_collection_result_envelope_from_dict(_collection_result_payload_from_terminal_envelope(envelope))
            if collection.target.target_type != record.request.target_type:
                raise TaskRecordContractError("comment collection target_type 与请求快照不一致")
            if collection.target.target_ref != record.request.target_value:
                raise TaskRecordContractError("comment collection target_ref 与请求快照不一致")
        if capability == "media_asset_fetch_by_ref":
            target = envelope.get("target")
            if not isinstance(target, Mapping):
                raise TaskRecordContractError("media asset fetch target 必须是对象")
            if target.get("target_type") != record.request.target_type:
                raise TaskRecordContractError("media asset fetch target_type 与请求快照不一致")
            if target.get("media_ref") != record.request.target_value:
                raise TaskRecordContractError("media asset fetch media_ref 与请求快照不一致")
        if "error" in envelope:
            raise TaskRecordContractError("success TaskTerminalResult.envelope 不得包含 error")
        return

    validate_failed_terminal_envelope(envelope)
    if "raw" in envelope or "normalized" in envelope:
        raise TaskRecordContractError("failed TaskTerminalResult.envelope 不得包含 success payload 字段")


def validate_terminal_envelope_observability_contract(record: TaskRecord, envelope: Mapping[str, Any]) -> None:
    if "task_record_ref" in envelope:
        envelope_task_record_ref = require_optional_string(envelope.get("task_record_ref"), field="result.envelope.task_record_ref")
        if envelope_task_record_ref != record.task_record_ref:
            raise TaskRecordContractError("TaskTerminalResult.envelope.task_record_ref 与 TaskRecord.task_record_ref 不一致")
    if "runtime_result_refs" in envelope:
        envelope_runtime_result_refs = _observability_entries(envelope, "runtime_result_refs", ())
        if envelope_runtime_result_refs != record.runtime_result_refs:
            raise TaskRecordContractError("TaskTerminalResult.envelope.runtime_result_refs 与 TaskRecord.runtime_result_refs 不一致")
    if "execution_control_events" in envelope:
        envelope_execution_control_events = _observability_entries(envelope, "execution_control_events", ())
        if envelope_execution_control_events != record.execution_control_events:
            raise TaskRecordContractError(
                "TaskTerminalResult.envelope.execution_control_events 与 TaskRecord.execution_control_events 不一致"
            )
    if "runtime_failure_signal" in envelope or "runtime_failure_signals" in envelope:
        envelope_failure_signals = _runtime_failure_signals(envelope, ())
        if not _observability_entries_are_subset(envelope_failure_signals, record.runtime_failure_signals):
            raise TaskRecordContractError("TaskTerminalResult.envelope.runtime_failure_signal 与 TaskRecord.runtime_failure_signals 不一致")
    if "runtime_structured_log_events" in envelope:
        envelope_log_events = _observability_entries(envelope, "runtime_structured_log_events", ())
        if not _observability_entries_are_subset(envelope_log_events, record.runtime_structured_log_events):
            raise TaskRecordContractError(
                "TaskTerminalResult.envelope.runtime_structured_log_events 与 TaskRecord.runtime_structured_log_events 不一致"
            )
    if "runtime_execution_metric_samples" in envelope:
        envelope_metric_samples = _observability_entries(envelope, "runtime_execution_metric_samples", ())
        if not _observability_entries_are_subset(envelope_metric_samples, record.runtime_execution_metric_samples):
            raise TaskRecordContractError(
                "TaskTerminalResult.envelope.runtime_execution_metric_samples 与 TaskRecord.runtime_execution_metric_samples 不一致"
            )


def _observability_entries_are_subset(entries: tuple[Any, ...], superset: tuple[Any, ...]) -> bool:
    remaining = list(superset)
    for entry in entries:
        if entry not in remaining:
            return False
        remaining.remove(entry)
    return True


def validate_success_terminal_envelope(envelope: Mapping[str, Any]) -> None:
    capability = require_string(envelope.get("capability"), field="result.envelope.capability")
    if capability in READ_SIDE_COLLECTION_OPERATIONS:
        _validate_collection_success_terminal_envelope(envelope)
        return
    if capability == COMMENT_COLLECTION_OPERATION:
        _validate_comment_collection_success_terminal_envelope(envelope)
        return
    if capability == "media_asset_fetch_by_ref":
        _validate_media_asset_fetch_success_terminal_envelope(envelope)
        return
    if "raw" not in envelope:
        raise TaskRecordContractError("success TaskTerminalResult.envelope 必须包含 raw")
    normalized = envelope.get("normalized")
    if not isinstance(normalized, Mapping):
        raise TaskRecordContractError("success TaskTerminalResult.envelope.normalized 必须是对象")

    required_non_empty = ("platform", "content_id", "content_type", "canonical_url")
    for field in required_non_empty:
        require_string(normalized.get(field), field=f"result.envelope.normalized.{field}")

    if normalized["content_type"] not in ALLOWED_CONTENT_TYPES:
        raise TaskRecordContractError("success TaskTerminalResult.envelope.normalized.content_type 不在允许值范围内")

    for field in ("title", "body_text"):
        value = normalized.get(field)
        if not isinstance(value, str):
            raise TaskRecordContractError(f"result.envelope.normalized.{field} 必须存在且为字符串")

    published_at = normalized.get("published_at")
    if published_at is not None:
        validate_timestamp(published_at, field="result.envelope.normalized.published_at")

    for field in ("author", "stats", "media"):
        if not isinstance(normalized.get(field), Mapping):
            raise TaskRecordContractError(f"result.envelope.normalized.{field} 必须存在且为对象")

    author = normalized["author"]
    stats = normalized["stats"]
    media = normalized["media"]
    for field in ("author_id", "display_name", "avatar_url"):
        if field not in author:
            raise TaskRecordContractError(f"result.envelope.normalized.author.{field} 不得缺失")
    for field in ("like_count", "comment_count", "share_count", "collect_count"):
        if field not in stats:
            raise TaskRecordContractError(f"result.envelope.normalized.stats.{field} 不得缺失")
    for field in ("cover_url", "video_url", "image_urls"):
        if field not in media:
            raise TaskRecordContractError(f"result.envelope.normalized.media.{field} 不得缺失")

    author_id = author.get("author_id")
    display_name = author.get("display_name")
    avatar_url = author.get("avatar_url")
    if author_id is not None and (not isinstance(author_id, str) or not author_id):
        raise TaskRecordContractError("result.envelope.normalized.author.author_id 必须为非空字符串或 null")
    if display_name is not None and (not isinstance(display_name, str) or not display_name):
        raise TaskRecordContractError("result.envelope.normalized.author.display_name 必须为非空字符串或 null")
    if avatar_url is not None and not isinstance(avatar_url, str):
        raise TaskRecordContractError("result.envelope.normalized.author.avatar_url 必须为字符串或 null")

    for field in ("like_count", "comment_count", "share_count", "collect_count"):
        value = stats.get(field)
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
            raise TaskRecordContractError(f"result.envelope.normalized.stats.{field} 必须为整数或 null")

    for field in ("cover_url", "video_url"):
        value = media.get(field)
        if value is not None and not isinstance(value, str):
            raise TaskRecordContractError(f"result.envelope.normalized.media.{field} 必须为字符串或 null")

    image_urls = media.get("image_urls")
    if not isinstance(image_urls, list) or not all(isinstance(item, str) for item in image_urls):
        raise TaskRecordContractError("result.envelope.normalized.media.image_urls 必须是字符串数组")


def _validate_collection_success_terminal_envelope(envelope: Mapping[str, Any]) -> None:
    try:
        collection_result_envelope_from_dict(_collection_result_payload_from_terminal_envelope(envelope))
    except Exception as error:
        raise TaskRecordContractError(f"collection TaskTerminalResult.envelope 不合法: {error}") from error


def _validate_comment_collection_success_terminal_envelope(envelope: Mapping[str, Any]) -> None:
    try:
        comment_collection_result_envelope_from_dict(_collection_result_payload_from_terminal_envelope(envelope))
    except Exception as error:
        raise TaskRecordContractError(f"comment collection TaskTerminalResult.envelope 不合法: {error}") from error


def _media_ref_value_is_sanitized(value: str) -> bool:
    normalized = value.lower()
    return not any(token in normalized for token in MEDIA_ASSET_FORBIDDEN_REF_VALUE_TOKENS)


def _require_sanitized_media_ref(value: Any, *, field: str) -> str:
    ref = require_string(value, field=field)
    if not _media_ref_value_is_sanitized(ref):
        raise TaskRecordContractError(f"{field} 不得包含 URL、路径、凭证、路由或下载定位信息")
    return ref


def _validate_media_asset_fetch_success_terminal_envelope(envelope: Mapping[str, Any]) -> None:
    operation = require_string(envelope.get("operation"), field="result.envelope.operation")
    if operation != "media_asset_fetch_by_ref":
        raise TaskRecordContractError("media asset fetch result.operation 必须为 media_asset_fetch_by_ref")

    target = envelope.get("target")
    if not isinstance(target, Mapping):
        raise TaskRecordContractError("media asset fetch result.target 必须是对象")
    if target.get("target_type") != "media_ref":
        raise TaskRecordContractError("media asset fetch result.target.target_type 必须为 media_ref")
    _require_sanitized_media_ref(target.get("media_ref"), field="media asset fetch result.target.media_ref")

    for required_field in (
        "content_type",
        "fetch_policy",
        "fetch_outcome",
        "result_status",
        "error_classification",
        "raw_payload_ref",
        "source_trace",
        "no_storage",
        "media",
    ):
        if required_field not in envelope:
            raise TaskRecordContractError("media asset fetch result 字段必须显式存在")

    content_type = require_string(envelope.get("content_type"), field="result.envelope.content_type")
    fetch_policy = envelope.get("fetch_policy")
    if not isinstance(fetch_policy, Mapping):
        raise TaskRecordContractError("media asset fetch fetch_policy 必须是对象")
    allowed_policy_fields = {"fetch_mode", "allowed_content_types", "allow_download", "max_bytes"}
    if any(field not in allowed_policy_fields for field in fetch_policy):
        raise TaskRecordContractError("media asset fetch fetch_policy 只能包含公共白名单字段")
    fetch_mode = fetch_policy.get("fetch_mode")
    if fetch_mode not in MEDIA_ASSET_FETCH_MODES:
        raise TaskRecordContractError("media asset fetch fetch_policy.fetch_mode 不在允许范围")
    allowed_content_types = fetch_policy.get("allowed_content_types")
    if (
        not isinstance(allowed_content_types, list)
        or not allowed_content_types
        or not all(isinstance(item, str) and item in MEDIA_ASSET_CONTENT_TYPES for item in allowed_content_types)
        or len(set(allowed_content_types)) != len(allowed_content_types)
    ):
        raise TaskRecordContractError("media asset fetch fetch_policy.allowed_content_types 无效")
    if not isinstance(fetch_policy.get("allow_download"), bool):
        raise TaskRecordContractError("media asset fetch fetch_policy.allow_download 必须为 bool")
    max_bytes = fetch_policy.get("max_bytes")
    if max_bytes is not None and (isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 0):
        raise TaskRecordContractError("media asset fetch fetch_policy.max_bytes 必须为非负整数或 null")

    result_status = require_string(envelope.get("result_status"), field="result.envelope.result_status")
    if result_status not in MEDIA_ASSET_RESULT_STATUSES:
        raise TaskRecordContractError("media asset fetch result_status 不在允许范围")
    fetch_outcome = envelope.get("fetch_outcome")

    error_classification = envelope.get("error_classification")
    if result_status == "complete":
        if content_type not in MEDIA_ASSET_CONTENT_TYPES:
            raise TaskRecordContractError("media asset fetch complete result content_type 不在 stable 允许范围")
        if not isinstance(fetch_outcome, str) or fetch_outcome not in MEDIA_ASSET_FETCH_OUTCOMES:
            raise TaskRecordContractError("media asset fetch complete result fetch_outcome 不在允许范围")
        if error_classification is not None:
            raise TaskRecordContractError("media asset fetch complete result 必须使用 null error_classification")
    elif result_status == "unavailable":
        if fetch_outcome is not None:
            raise TaskRecordContractError("media asset fetch unavailable result 必须使用 null fetch_outcome")
        if not (
            isinstance(error_classification, str)
            and error_classification in MEDIA_ASSET_UNAVAILABLE_CLASSIFICATIONS
        ):
            raise TaskRecordContractError("media asset fetch unavailable result 错误分类不允许")
    else:
        if fetch_outcome is not None:
            raise TaskRecordContractError("media asset fetch failed result 必须使用 null fetch_outcome")
        if not (
            isinstance(error_classification, str)
            and error_classification in MEDIA_ASSET_FAILED_CLASSIFICATIONS
        ):
            raise TaskRecordContractError("media asset fetch failed result 错误分类不允许")

    raw_payload_ref = envelope.get("raw_payload_ref")
    if not (isinstance(raw_payload_ref, str) or raw_payload_ref is None):
        raise TaskRecordContractError("media asset fetch raw_payload_ref 必须为字符串或 null")
    if result_status == "complete" and not (isinstance(raw_payload_ref, str) and raw_payload_ref):
        raise TaskRecordContractError("media asset fetch complete result 必须包含 raw_payload_ref")
    if error_classification == "provider_or_network_blocked" and raw_payload_ref is not None:
        raise TaskRecordContractError("media asset fetch provider_or_network_blocked 必须使用 null raw_payload_ref")

    source_trace = envelope.get("source_trace")
    if not isinstance(source_trace, Mapping):
        raise TaskRecordContractError("media asset fetch source_trace 必须是对象")
    for required_field in ("adapter_key", "provider_path", "fetched_at", "evidence_alias"):
        value = source_trace.get(required_field)
        if not isinstance(value, str) or not value:
            raise TaskRecordContractError(f"media asset fetch source_trace 字段缺失或无效: {required_field}")
    validate_timestamp(source_trace.get("fetched_at"), field="result.envelope.source_trace.fetched_at")
    provider_path = source_trace.get("provider_path")
    if isinstance(provider_path, str) and not _media_ref_value_is_sanitized(provider_path):
        raise TaskRecordContractError("media asset fetch source_trace.provider_path 不得包含路由或定位信息")
    if error_classification == "provider_or_network_blocked" and not (
        isinstance(provider_path, str) and provider_path.startswith("provider://blocked-path-alias")
    ):
        raise TaskRecordContractError("media asset fetch provider_or_network_blocked 必须使用脱敏 blocked-path alias")

    media = envelope.get("media")
    if result_status == "complete":
        if not isinstance(media, Mapping):
            raise TaskRecordContractError("media asset fetch complete result 必须包含 media 对象")
        source_media_ref = _require_sanitized_media_ref(
            media.get("source_media_ref"),
            field="result.envelope.media.source_media_ref",
        )
        canonical_ref = _require_sanitized_media_ref(
            media.get("canonical_ref"),
            field="result.envelope.media.canonical_ref",
        )
        if media.get("content_type") != content_type:
            raise TaskRecordContractError("media asset fetch media.content_type 必须与顶层 content_type 一致")
        lineage = media.get("source_ref_lineage")
        if not isinstance(lineage, Mapping):
            raise TaskRecordContractError("media asset fetch media.source_ref_lineage 必须是对象")
        expected_lineage = {
            "input_ref": target.get("media_ref"),
            "source_media_ref": source_media_ref,
            "canonical_ref": canonical_ref,
            "preservation_status": "preserved",
        }
        for field, expected in expected_lineage.items():
            if lineage.get(field) != expected:
                raise TaskRecordContractError("media asset fetch source_ref_lineage 必须绑定请求和公共媒体引用")
            _require_sanitized_media_ref(lineage.get(field), field=f"result.envelope.media.source_ref_lineage.{field}")
        resolved_ref = lineage.get("resolved_ref")
        if resolved_ref is not None:
            _require_sanitized_media_ref(resolved_ref, field="result.envelope.media.source_ref_lineage.resolved_ref")
        for forbidden_field in (
            "download_handle",
            "storage_handle",
            "download_path",
            "provider_local_file_ref",
            "bytes_retrieval_handle",
            "local_path",
            "file_path",
        ):
            if forbidden_field in lineage:
                raise TaskRecordContractError("media asset fetch source_ref_lineage 不得包含存储或下载定位字段")
        metadata = media.get("metadata") or {}
        if not isinstance(metadata, Mapping):
            raise TaskRecordContractError("media asset fetch media.metadata 必须是对象或 null")
        allowed_metadata_fields = {
            "mime_type",
            "width",
            "height",
            "duration_ms",
            "byte_size",
            "checksum_digest",
            "checksum_family",
        }
        for field in metadata:
            if field not in allowed_metadata_fields:
                raise TaskRecordContractError("media asset fetch media.metadata 只能包含公共白名单字段")
        for forbidden_field in (
            "local_path",
            "file_path",
            "storage_handle",
            "download_handle",
            "retrieval_token",
            "provider_local_file_ref",
            "bytes_retrieval_handle",
        ):
            if forbidden_field in metadata:
                raise TaskRecordContractError("media asset fetch media.metadata 不得包含存储或下载定位字段")
        for field in ("width", "height", "duration_ms"):
            value = metadata.get(field)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise TaskRecordContractError(f"media asset fetch media.metadata.{field} 必须为非负整数或 null")
        mime_type = metadata.get("mime_type")
        if mime_type is not None and not isinstance(mime_type, str):
            raise TaskRecordContractError("media asset fetch media.metadata.mime_type 必须为字符串或 null")
        if fetch_outcome == "downloaded_bytes":
            byte_size = metadata.get("byte_size")
            if isinstance(byte_size, bool) or not isinstance(byte_size, int) or byte_size < 0:
                raise TaskRecordContractError("media asset fetch downloaded_bytes 必须包含非负 metadata.byte_size")
            for field in ("checksum_digest", "checksum_family"):
                value = metadata.get(field)
                if not isinstance(value, str) or not value:
                    raise TaskRecordContractError(f"media asset fetch downloaded_bytes 必须包含非空 metadata.{field}")
        else:
            for field in ("byte_size", "checksum_digest", "checksum_family"):
                if field in metadata:
                    raise TaskRecordContractError("media asset fetch 非 downloaded_bytes outcome 不得包含下载字节元数据")
    elif media is not None:
        raise TaskRecordContractError("media asset fetch unavailable/failed result 时 media 必须为 null")

    no_storage = envelope.get("no_storage")
    if not isinstance(no_storage, Mapping):
        raise TaskRecordContractError("media asset fetch no_storage 必须是对象")
    allowed_no_storage_fields = {"stored", "downloaded_byte_length", "retention_policy"}
    if any(field not in allowed_no_storage_fields for field in no_storage):
        raise TaskRecordContractError("media asset fetch no_storage 只能包含公共白名单字段")
    if no_storage.get("stored") is not False:
        raise TaskRecordContractError("media asset fetch no_storage.stored 必须为 false")
    retention_policy = no_storage.get("retention_policy")
    if retention_policy is not None:
        _require_sanitized_media_ref(retention_policy, field="result.envelope.no_storage.retention_policy")
    if fetch_outcome == "downloaded_bytes":
        byte_length = no_storage.get("downloaded_byte_length")
        if isinstance(byte_length, bool) or not isinstance(byte_length, int) or byte_length < 0:
            raise TaskRecordContractError("media asset fetch downloaded_bytes 必须记录非负 downloaded_byte_length")
        if isinstance(media, Mapping) and isinstance(media.get("metadata"), Mapping):
            byte_size = media["metadata"].get("byte_size")
            if isinstance(byte_size, int) and not isinstance(byte_size, bool) and byte_length != byte_size:
                raise TaskRecordContractError("media asset fetch downloaded_byte_length 必须与 metadata.byte_size 一致")
    else:
        byte_length = no_storage.get("downloaded_byte_length")
        if byte_length not in (None, 0):
            raise TaskRecordContractError("media asset fetch 非 downloaded_bytes outcome 不得记录 downloaded_byte_length")


def _collection_result_payload_from_terminal_envelope(envelope: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
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
    )
    return {key: envelope.get(key) for key in keys}


def validate_failed_terminal_envelope(envelope: Mapping[str, Any]) -> None:
    error = envelope.get("error")
    if not isinstance(error, Mapping):
        raise TaskRecordContractError("failed TaskTerminalResult.envelope.error 必须是对象")
    category = require_string(error.get("category"), field="result.envelope.error.category")
    require_string(error.get("code"), field="result.envelope.error.code")
    require_string(error.get("message"), field="result.envelope.error.message")
    details = error.get("details")
    if not isinstance(details, Mapping):
        raise TaskRecordContractError("result.envelope.error.details 必须存在且为对象")
    if category not in ALLOWED_ERROR_CATEGORIES:
        raise TaskRecordContractError("result.envelope.error.category 不在允许值范围内")


def normalize_json_value(value: Any, *, field: str) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TaskRecordContractError(f"{field} 包含非有限浮点数")
        return value
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise TaskRecordContractError(f"{field} 仅允许非空字符串键")
            normalized[key] = normalize_json_value(item, field=f"{field}.{key}")
        return normalized
    if isinstance(value, (list, tuple)):
        return [normalize_json_value(item, field=f"{field}[]") for item in value]
    raise TaskRecordContractError(f"{field} 包含不可序列化值 `{type(value).__name__}`")
