from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile
from typing import Protocol
from urllib.parse import quote

from syvert.task_record import (
    TaskRecord,
    TaskRecordContractError,
    finish_task_record,
    start_task_record,
    task_record_from_dict,
    task_record_to_dict,
)


DEFAULT_TASK_RECORD_STORE_ENV = "SYVERT_TASK_RECORD_STORE_DIR"


class TaskRecordStore(Protocol):
    def write(self, record: TaskRecord) -> TaskRecord:
        ...

    def load(self, task_id: str) -> TaskRecord:
        ...

    def mark_invalid(self, task_id: str, *, stage: str, reason: str) -> None:
        ...


class TaskRecordStoreError(RuntimeError):
    pass


@dataclass(frozen=True)
class LocalTaskRecordStore:
    root: Path

    def write(self, record: TaskRecord) -> TaskRecord:
        invalid_marker = self.invalid_marker_path(record.task_id)
        if invalid_marker.exists():
            raise TaskRecordStoreError(f"本地任务记录 `{record.task_id}` 已因持久化失败被标记为无效")
        path = self.record_path(record.task_id)
        existing = self._try_load_existing(record.task_id, path)
        candidate = reconcile_persisted_record(existing, record)
        if existing == candidate:
            return existing
        payload = task_record_to_dict(candidate)
        self._write_json_atomic(path, payload)
        return candidate

    def load(self, task_id: str) -> TaskRecord:
        path = self.record_path(task_id)
        invalid_marker = self.invalid_marker_path(task_id)
        if invalid_marker.exists():
            raise TaskRecordStoreError(f"本地任务记录 `{task_id}` 已因持久化失败被标记为无效")
        if not path.exists():
            raise FileNotFoundError(path)
        return self._load_from_path(path)

    def record_path(self, task_id: str) -> Path:
        if not isinstance(task_id, str) or not task_id:
            raise TaskRecordStoreError("task_id 必须为非空字符串")
        return self.root / f"{quote(task_id, safe='')}.json"

    def invalid_marker_path(self, task_id: str) -> Path:
        return self.root / f"{quote(task_id, safe='')}.invalid.json"

    def mark_invalid(self, task_id: str, *, stage: str, reason: str) -> None:
        record_path = self.record_path(task_id)
        marker = self.invalid_marker_path(task_id)
        payload = {"task_id": task_id, "stage": stage, "reason": reason}
        try:
            self._write_json_atomic(marker, payload)
            return
        except (TaskRecordStoreError, OSError) as error:
            marker_error = error
        if record_path.exists():
            try:
                self._move_record_to_invalid_marker(record_path, marker)
                return
            except OSError as error:
                move_error = error
        else:
            move_error = None

        try:
            self._write_json_atomic(record_path, payload)
            return
        except (TaskRecordStoreError, OSError) as poison_error:
            raise TaskRecordStoreError(
                f"无法将本地任务记录 `{task_id}` 标记为无效: "
                f"marker={marker_error}; move={move_error}; poison={poison_error}"
            ) from poison_error

    def _try_load_existing(self, task_id: str, path: Path) -> TaskRecord | None:
        if not path.exists():
            return None
        record = self._load_from_path(path)
        if record.task_id != task_id:
            raise TaskRecordStoreError("本地持久化记录的 task_id 与文件名不一致")
        return record

    def _load_from_path(self, path: Path) -> TaskRecord:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise TaskRecordStoreError(f"无法读取本地任务记录 `{path}`") from error
        if not isinstance(payload, Mapping):
            raise TaskRecordStoreError(f"本地任务记录 `{path}` 必须是对象")
        try:
            return task_record_from_dict(payload)
        except TaskRecordContractError as error:
            raise TaskRecordStoreError(f"本地任务记录 `{path}` 不满足共享 contract") from error

    def _write_json_atomic(self, path: Path, payload: Mapping[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix=f".{path.stem}.", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        except OSError as error:
            raise TaskRecordStoreError(f"无法写入本地任务记录 `{path}`") from error
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def _move_record_to_invalid_marker(self, path: Path, marker: Path) -> None:
        os.replace(path, marker)


def default_task_record_store() -> LocalTaskRecordStore:
    return LocalTaskRecordStore(resolve_task_record_store_root())


def resolve_task_record_store_root(env: Mapping[str, str] | None = None) -> Path:
    source = env if env is not None else os.environ
    configured = source.get(DEFAULT_TASK_RECORD_STORE_ENV)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".syvert" / "task-records"


def reconcile_persisted_record(existing: TaskRecord | None, incoming: TaskRecord) -> TaskRecord:
    if existing is None:
        if incoming.status != "accepted":
            raise TaskRecordStoreError("本地持久化的第一条任务记录必须是 accepted")
        return incoming
    if existing.task_id != incoming.task_id:
        raise TaskRecordStoreError("本地持久化记录的 task_id 不一致")

    try:
        if existing.status == "accepted" and incoming.status == "accepted":
            candidate = existing
        elif existing.status == "accepted" and incoming.status == "running":
            candidate = start_task_record(existing, occurred_at=incoming.updated_at)
        elif existing.status == "running" and incoming.status in {"succeeded", "failed"}:
            if incoming.result is None or incoming.terminal_at is None:
                raise TaskRecordStoreError("终态任务记录缺少结果或终态时间")
            candidate = finish_task_record(existing, incoming.result.envelope, occurred_at=incoming.terminal_at)
        elif existing.status in {"succeeded", "failed"} and incoming.status in {"succeeded", "failed"}:
            if incoming.result is None or incoming.terminal_at is None:
                raise TaskRecordStoreError("终态任务记录缺少结果或终态时间")
            candidate = finish_task_record(existing, incoming.result.envelope, occurred_at=incoming.terminal_at)
        else:
            raise TaskRecordStoreError("本地持久化记录的生命周期推进不合法")
    except TaskRecordContractError as error:
        raise TaskRecordStoreError("本地持久化记录的生命周期推进不合法") from error

    if candidate != incoming:
        raise TaskRecordStoreError("本地持久化记录与共享模型不一致")
    return candidate


def extract_stage_time(record: TaskRecord, stage: str) -> str:
    for entry in record.logs:
        if entry.stage == stage:
            return entry.occurred_at
    raise TaskRecordStoreError(f"任务记录缺少 `{stage}` 生命周期事件")
