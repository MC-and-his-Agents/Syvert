from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import math
import re
from typing import Any


TASK_RECORD_SCHEMA_VERSION = "v0.3.0"
TASK_RECORD_STATUSES = frozenset({"accepted", "running", "succeeded", "failed"})
TASK_LOG_STAGES = frozenset({"admission", "execution", "completion"})
TASK_LOG_LEVELS = frozenset({"info", "error"})
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


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


def now_rfc3339_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


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
    )
    validate_task_record(updated)
    return updated


def finish_task_record(record: TaskRecord, envelope: Mapping[str, Any], *, occurred_at: str | None = None) -> TaskRecord:
    validate_task_record(record)
    terminal_status = terminal_record_status(envelope)
    normalized_envelope = normalize_json_value(envelope, field="result.envelope")
    if not isinstance(normalized_envelope, dict):
        raise TaskRecordContractError("TaskTerminalResult.envelope 必须是对象")
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
    result_payload = payload.get("result")
    result: TaskTerminalResult | None = None
    if result_payload is not None:
        if not isinstance(result_payload, Mapping):
            raise TaskRecordContractError("TaskRecord.result 必须是对象或 null")
        envelope = result_payload.get("envelope")
        if not isinstance(envelope, Mapping):
            raise TaskRecordContractError("TaskTerminalResult.envelope 必须是对象")
        result = TaskTerminalResult(envelope=dict(normalize_json_value(envelope, field="result.envelope")))

    record = TaskRecord(
        schema_version=require_string(payload.get("schema_version"), field="schema_version"),
        task_id=require_string(payload.get("task_id"), field="task_id"),
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
    validate_request_snapshot(record.request)
    if record.status not in TASK_RECORD_STATUSES:
        raise TaskRecordContractError("TaskRecord.status 不在允许值范围内")
    validate_timestamp(record.created_at, field="created_at")
    validate_timestamp(record.updated_at, field="updated_at")
    if record.terminal_at is not None:
        validate_timestamp(record.terminal_at, field="terminal_at")
    if not record.logs:
        raise TaskRecordContractError("TaskRecord.logs 不得为空")

    last_sequence = 0
    seen_stages: list[str] = []
    for entry in record.logs:
        if isinstance(entry.sequence, bool) or not isinstance(entry.sequence, int) or entry.sequence <= 0:
            raise TaskRecordContractError("TaskLogEntry.sequence 必须为正整数")
        if entry.sequence != last_sequence + 1:
            raise TaskRecordContractError("TaskRecord.logs.sequence 必须连续递增")
        last_sequence = entry.sequence
        validate_timestamp(entry.occurred_at, field="logs.occurred_at")
        if entry.stage not in TASK_LOG_STAGES:
            raise TaskRecordContractError("TaskLogEntry.stage 不在允许值范围内")
        if entry.level not in TASK_LOG_LEVELS:
            raise TaskRecordContractError("TaskLogEntry.level 不在允许值范围内")
        if not isinstance(entry.message, str) or not entry.message:
            raise TaskRecordContractError("TaskLogEntry.message 必须为非空字符串")
        if entry.code is not None and (not isinstance(entry.code, str) or not entry.code):
            raise TaskRecordContractError("TaskLogEntry.code 必须为非空字符串或 null")
        seen_stages.append(entry.stage)

    if "admission" not in seen_stages:
        raise TaskRecordContractError("TaskRecord 缺少 accepted 生命周期事件")
    if record.status in {"running", "succeeded", "failed"} and "execution" not in seen_stages:
        raise TaskRecordContractError("TaskRecord 缺少 execution 生命周期事件")
    if record.status in {"succeeded", "failed"} and "completion" not in seen_stages:
        raise TaskRecordContractError("终态 TaskRecord 缺少 completion 生命周期事件")

    if record.status in {"accepted", "running"}:
        if record.terminal_at is not None or record.result is not None:
            raise TaskRecordContractError("非终态 TaskRecord 不得包含终态结果")
    else:
        if record.terminal_at is None or record.result is None:
            raise TaskRecordContractError("终态 TaskRecord 必须包含终态结果")
        normalized_envelope = normalize_json_value(record.result.envelope, field="result.envelope")
        if not isinstance(normalized_envelope, dict):
            raise TaskRecordContractError("TaskTerminalResult.envelope 必须是对象")
        if normalized_envelope != record.result.envelope:
            raise TaskRecordContractError("TaskTerminalResult.envelope 必须预先满足 JSON-safe 约束")
        status = terminal_record_status(record.result.envelope)
        if status != record.status:
            raise TaskRecordContractError("TaskRecord.status 与终态 envelope.status 不一致")


def validate_request_snapshot(snapshot: TaskRequestSnapshot) -> None:
    for field_name in ("adapter_key", "capability", "target_type", "target_value", "collection_mode"):
        value = getattr(snapshot, field_name)
        if not isinstance(value, str) or not value:
            raise TaskRecordContractError(f"TaskRequestSnapshot.{field_name} 必须为非空字符串")


def validate_timestamp(value: str, *, field: str) -> None:
    if not isinstance(value, str) or not RFC3339_UTC_RE.fullmatch(value):
        raise TaskRecordContractError(f"{field} 必须为 RFC3339 UTC 时间")


def terminal_record_status(envelope: Mapping[str, Any]) -> str:
    raw_status = envelope.get("status")
    if raw_status == "success":
        return "succeeded"
    if raw_status == "failed":
        return "failed"
    raise TaskRecordContractError("终态 envelope.status 必须为 success 或 failed")


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
