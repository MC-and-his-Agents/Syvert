from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import json
import os
from pathlib import Path
import tempfile

from syvert.resource_trace import (
    ResourceLeaseTimeline,
    ResourceTraceContractError,
    ResourceTraceEvent,
    TaskResourceUsageLog,
    build_resource_lease_timeline,
    build_task_resource_usage_log,
    canonical_resource_trace_event,
    resource_trace_event_from_dict,
    resource_trace_event_to_dict,
    resource_trace_events_for_resource,
)


DEFAULT_RESOURCE_TRACE_STORE_ENV = "SYVERT_RESOURCE_TRACE_STORE_FILE"


class ResourceTraceStoreError(ResourceTraceContractError):
    pass


class ResourceTracePersistenceError(ResourceTraceStoreError):
    pass


@dataclass(frozen=True)
class LocalResourceTraceStore:
    path: Path

    def load_events(self) -> tuple[ResourceTraceEvent, ...]:
        if not self.path.exists():
            return ()
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                return tuple(self._read_events(handle))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ResourceTracePersistenceError(
                f"resource_state_conflict: 无法读取资源 tracing 事件流 `{self.path}`"
            ) from error

    def append_events(self, events: Sequence[ResourceTraceEvent]) -> tuple[ResourceTraceEvent, ...]:
        normalized_events = tuple(canonical_resource_trace_event(event) for event in events)
        if not normalized_events:
            return ()
        with self._exclusive_lock():
            current_events = self.load_events()
            merged_events, events_to_append = merge_resource_trace_events(current_events, normalized_events)
            if not events_to_append:
                return normalized_events
            self.write_events(merged_events)
            return tuple(events_to_append)

    def task_usage_log(self, task_id: str) -> TaskResourceUsageLog:
        return build_task_resource_usage_log(self.load_events(), task_id=task_id)

    def lease_timeline(self, lease_id: str) -> ResourceLeaseTimeline:
        return build_resource_lease_timeline(self.load_events(), lease_id=lease_id)

    def bundle_timeline(self, bundle_id: str) -> ResourceLeaseTimeline:
        return build_resource_lease_timeline(self.load_events(), bundle_id=bundle_id)

    def resource_events(self, resource_id: str) -> tuple[ResourceTraceEvent, ...]:
        return resource_trace_events_for_resource(self.load_events(), resource_id=resource_id)

    def _read_events(self, handle) -> list[ResourceTraceEvent]:
        events: list[ResourceTraceEvent] = []
        seen_by_id: dict[str, ResourceTraceEvent] = {}
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            payload = json.loads(line)
            event = resource_trace_event_from_dict(payload)
            existing = seen_by_id.get(event.event_id)
            if existing is not None and existing != event:
                raise ResourceTracePersistenceError(
                    f"resource_state_conflict: tracing event_id `{event.event_id}` payload 冲突"
                )
            seen_by_id[event.event_id] = event
            events.append(event)
        return events

    def write_events(self, events: Sequence[ResourceTraceEvent]) -> tuple[ResourceTraceEvent, ...]:
        canonical_events = tuple(canonical_resource_trace_event(event) for event in events)
        self._write_events_atomic(canonical_events)
        return canonical_events

    def _write_events_atomic(self, events: Sequence[ResourceTraceEvent]) -> None:
        temp_path: str | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, temp_path = tempfile.mkstemp(prefix=f".{self.path.stem}.", suffix=".tmp", dir=self.path.parent)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                for event in events:
                    json.dump(resource_trace_event_to_dict(event), handle, ensure_ascii=False, sort_keys=True)
                    handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
        except OSError as error:
            raise ResourceTracePersistenceError(
                f"resource_state_conflict: 无法写入资源 tracing 事件流 `{self.path}`"
            ) from error
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
        try:
            dir_fd = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass

    @contextmanager
    def _exclusive_lock(self):
        lock_path = self.path.with_name(f"{self.path.name}.lock")
        try:
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            with lock_path.open("a+", encoding="utf-8") as handle:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                except OSError as error:
                    raise ResourceTracePersistenceError(
                        f"resource_state_conflict: 无法锁定资源 tracing 事件流 `{self.path}`"
                    ) from error
                try:
                    yield
                finally:
                    try:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                    except OSError:
                        pass
        except OSError as error:
            raise ResourceTracePersistenceError(
                f"resource_state_conflict: 无法准备资源 tracing 事件流锁 `{self.path}`"
            ) from error


def default_resource_trace_store() -> LocalResourceTraceStore:
    return LocalResourceTraceStore(resolve_resource_trace_store_path())


def resolve_resource_trace_store_path(env: Mapping[str, str] | None = None) -> Path:
    source = env if env is not None else os.environ
    configured = source.get(DEFAULT_RESOURCE_TRACE_STORE_ENV)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".syvert" / "resource-trace-events.jsonl"


def merge_resource_trace_events(
    existing_events: Sequence[ResourceTraceEvent],
    new_events: Sequence[ResourceTraceEvent],
) -> tuple[tuple[ResourceTraceEvent, ...], tuple[ResourceTraceEvent, ...]]:
    canonical_existing = tuple(canonical_resource_trace_event(event) for event in existing_events)
    canonical_new = tuple(canonical_resource_trace_event(event) for event in new_events)
    existing_by_id = {event.event_id: event for event in canonical_existing}
    events_to_append: list[ResourceTraceEvent] = []
    for event in canonical_new:
        current = existing_by_id.get(event.event_id)
        if current is not None:
            if current != event:
                raise ResourceTracePersistenceError(
                    f"resource_state_conflict: tracing event_id `{event.event_id}` payload 冲突"
                )
            continue
        existing_by_id[event.event_id] = event
        events_to_append.append(event)
    return tuple([*canonical_existing, *events_to_append]), tuple(events_to_append)
