from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
import re
from typing import Any


TASK_RECORD_SCHEMA_VERSION = "v0.3.0"
TASK_RECORD_STATUSES = frozenset({"accepted", "running", "succeeded", "failed"})
TASK_LOG_STAGES = frozenset({"admission", "execution", "completion"})
TASK_LOG_LEVELS = frozenset({"info", "error"})
TASK_LOG_STAGE_ORDER = {"admission": 0, "execution": 1, "completion": 2}
SHARED_CAPABILITIES = frozenset({"content_detail_by_url"})
SHARED_TARGET_TYPES = frozenset({"url", "content_id", "creator_id", "keyword"})
SHARED_COLLECTION_MODES = frozenset({"public", "authenticated", "hybrid"})
ALLOWED_CONTENT_TYPES = frozenset({"video", "image_post", "mixed_media", "unknown"})
ALLOWED_ERROR_CATEGORIES = frozenset({"invalid_input", "unsupported", "runtime_contract", "platform"})
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


def now_rfc3339_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def task_record_ref_for(task_id: str) -> str:
    return f"task_record:{task_id}"


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
    )
    validate_task_record(updated)
    return updated


def finish_task_record(record: TaskRecord, envelope: Mapping[str, Any], *, occurred_at: str | None = None) -> TaskRecord:
    validate_task_record(record)
    terminal_status = terminal_record_status(envelope)
    normalized_envelope = normalize_json_value(envelope, field="result.envelope")
    if not isinstance(normalized_envelope, dict):
        raise TaskRecordContractError("TaskTerminalResult.envelope 必须是对象")
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


def validate_success_terminal_envelope(envelope: Mapping[str, Any]) -> None:
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
