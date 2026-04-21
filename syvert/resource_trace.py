from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


RESOURCE_TRACE_EVENT_TYPES = frozenset({"acquired", "released", "invalidated"})
RESOURCE_TRACE_RESOURCE_TYPES = frozenset({"account", "proxy"})
RESOURCE_TRACE_STATUSES = frozenset({"AVAILABLE", "IN_USE", "INVALID"})
RESOURCE_TRACE_ALLOWED_TRANSITIONS = {
    "acquired": ("AVAILABLE", "IN_USE"),
    "released": ("IN_USE", "AVAILABLE"),
    "invalidated": ("IN_USE", "INVALID"),
}


class ResourceTraceContractError(ValueError):
    pass


@dataclass(frozen=True)
class ResourceTraceEvent:
    event_id: str
    task_id: str
    lease_id: str
    bundle_id: str
    resource_id: str
    resource_type: str
    adapter_key: str
    capability: str
    event_type: str
    from_status: str
    to_status: str
    occurred_at: str
    reason: str


@dataclass(frozen=True)
class TaskResourceUsageLog:
    task_id: str
    events: tuple[ResourceTraceEvent, ...]


@dataclass(frozen=True)
class ResourceTimeline:
    resource_id: str
    resource_type: str
    acquired_at: str
    released_at: str | None
    invalidated_at: str | None
    events: tuple[ResourceTraceEvent, ...]


@dataclass(frozen=True)
class ResourceLeaseTimeline:
    lease_id: str
    bundle_id: str
    resource_timelines: tuple[ResourceTimeline, ...]


def build_resource_trace_event_id(event_type: str, lease_id: str, resource_id: str) -> str:
    return f"{event_type}:{lease_id}:{resource_id}"


def resource_trace_event_to_dict(event: ResourceTraceEvent) -> dict[str, Any]:
    validate_resource_trace_event(event)
    return {
        "event_id": event.event_id,
        "task_id": event.task_id,
        "lease_id": event.lease_id,
        "bundle_id": event.bundle_id,
        "resource_id": event.resource_id,
        "resource_type": event.resource_type,
        "adapter_key": event.adapter_key,
        "capability": event.capability,
        "event_type": event.event_type,
        "from_status": event.from_status,
        "to_status": event.to_status,
        "occurred_at": event.occurred_at,
        "reason": event.reason,
    }


def resource_trace_event_from_dict(payload: Mapping[str, Any]) -> ResourceTraceEvent:
    if not isinstance(payload, Mapping):
        raise ResourceTraceContractError("ResourceTraceEvent 必须是对象")
    event = ResourceTraceEvent(
        event_id=require_non_empty_string(payload.get("event_id"), field="event.event_id"),
        task_id=require_non_empty_string(payload.get("task_id"), field="event.task_id"),
        lease_id=require_non_empty_string(payload.get("lease_id"), field="event.lease_id"),
        bundle_id=require_non_empty_string(payload.get("bundle_id"), field="event.bundle_id"),
        resource_id=require_non_empty_string(payload.get("resource_id"), field="event.resource_id"),
        resource_type=require_non_empty_string(payload.get("resource_type"), field="event.resource_type"),
        adapter_key=require_non_empty_string(payload.get("adapter_key"), field="event.adapter_key"),
        capability=require_non_empty_string(payload.get("capability"), field="event.capability"),
        event_type=require_non_empty_string(payload.get("event_type"), field="event.event_type"),
        from_status=require_non_empty_string(payload.get("from_status"), field="event.from_status"),
        to_status=require_non_empty_string(payload.get("to_status"), field="event.to_status"),
        occurred_at=require_non_empty_string(payload.get("occurred_at"), field="event.occurred_at"),
        reason=require_non_empty_string(payload.get("reason"), field="event.reason"),
    )
    validate_resource_trace_event(event)
    return event


def validate_resource_trace_event(event: ResourceTraceEvent) -> None:
    require_non_empty_string(event.event_id, field="event.event_id")
    require_non_empty_string(event.task_id, field="event.task_id")
    require_non_empty_string(event.lease_id, field="event.lease_id")
    require_non_empty_string(event.bundle_id, field="event.bundle_id")
    require_non_empty_string(event.resource_id, field="event.resource_id")
    require_non_empty_string(event.adapter_key, field="event.adapter_key")
    require_non_empty_string(event.capability, field="event.capability")
    require_non_empty_string(event.reason, field="event.reason")
    if event.resource_type not in RESOURCE_TRACE_RESOURCE_TYPES:
        raise ResourceTraceContractError("event.resource_type 不在允许值范围内")
    if event.event_type not in RESOURCE_TRACE_EVENT_TYPES:
        raise ResourceTraceContractError("event.event_type 不在允许值范围内")
    if event.from_status not in RESOURCE_TRACE_STATUSES:
        raise ResourceTraceContractError("event.from_status 不在允许值范围内")
    if event.to_status not in RESOURCE_TRACE_STATUSES:
        raise ResourceTraceContractError("event.to_status 不在允许值范围内")
    expected_from_status, expected_to_status = RESOURCE_TRACE_ALLOWED_TRANSITIONS[event.event_type]
    if (event.from_status, event.to_status) != (expected_from_status, expected_to_status):
        raise ResourceTraceContractError("event.from_status / to_status 与 event_type 不一致")
    parse_rfc3339_utc_datetime(event.occurred_at, field="event.occurred_at")
    expected_event_id = build_resource_trace_event_id(event.event_type, event.lease_id, event.resource_id)
    if event.event_id != expected_event_id:
        raise ResourceTraceContractError("event.event_id 与 canonical 规则不一致")


def canonical_resource_trace_event(event: ResourceTraceEvent | Mapping[str, Any]) -> ResourceTraceEvent:
    if isinstance(event, Mapping):
        return resource_trace_event_from_dict(event)
    if not isinstance(event, ResourceTraceEvent):
        raise ResourceTraceContractError("ResourceTraceEvent 必须是 ResourceTraceEvent 或对象")
    validate_resource_trace_event(event)
    return event


def canonicalize_resource_trace_events(events: Sequence[ResourceTraceEvent]) -> tuple[ResourceTraceEvent, ...]:
    seen_by_id: dict[str, ResourceTraceEvent] = {}
    canonical_events: list[ResourceTraceEvent] = []
    for event in sort_resource_trace_events(events):
        existing = seen_by_id.get(event.event_id)
        if existing is not None:
            if existing != event:
                raise ResourceTraceContractError(
                    f"resource trace stream 非法: event_id `{event.event_id}` payload 冲突"
                )
            continue
        seen_by_id[event.event_id] = event
        canonical_events.append(event)
    return tuple(canonical_events)


def validate_resource_trace_stream(events: Sequence[ResourceTraceEvent]) -> tuple[ResourceTraceEvent, ...]:
    canonical_events = canonicalize_resource_trace_events(events)
    lease_task_ids: dict[str, str] = {}
    bundle_task_ids: dict[str, str] = {}
    lease_bundle_ids: dict[str, str] = {}
    bundle_lease_ids: dict[str, str] = {}
    resource_timeline_closeouts: dict[tuple[str, str], str | None] = {}
    resource_timeline_has_acquired: dict[tuple[str, str], bool] = {}
    for event in canonical_events:
        existing_lease_task_id = lease_task_ids.get(event.lease_id)
        if existing_lease_task_id is not None and existing_lease_task_id != event.task_id:
            raise ResourceTraceContractError(
                f"resource trace stream 非法: lease_id `{event.lease_id}` 不能跨多个 task_id"
            )
        lease_task_ids[event.lease_id] = event.task_id
        existing_bundle_task_id = bundle_task_ids.get(event.bundle_id)
        if existing_bundle_task_id is not None and existing_bundle_task_id != event.task_id:
            raise ResourceTraceContractError(
                f"resource trace stream 非法: bundle_id `{event.bundle_id}` 不能跨多个 task_id"
            )
        bundle_task_ids[event.bundle_id] = event.task_id
        existing_bundle_id = lease_bundle_ids.get(event.lease_id)
        if existing_bundle_id is not None and existing_bundle_id != event.bundle_id:
            raise ResourceTraceContractError(
                f"resource trace stream 非法: lease_id `{event.lease_id}` 不能复用多个 bundle_id"
            )
        lease_bundle_ids[event.lease_id] = event.bundle_id
        existing_lease_id = bundle_lease_ids.get(event.bundle_id)
        if existing_lease_id is not None and existing_lease_id != event.lease_id:
            raise ResourceTraceContractError(
                f"resource trace stream 非法: bundle_id `{event.bundle_id}` 不能复用多个 lease_id"
            )
        bundle_lease_ids[event.bundle_id] = event.lease_id
        timeline_key = (event.lease_id, event.resource_id)
        if event.event_type == "acquired":
            if resource_timeline_has_acquired.get(timeline_key):
                raise ResourceTraceContractError(
                    f"resource trace stream 非法: lease_id `{event.lease_id}` / resource_id `{event.resource_id}` 只能有一条 acquired"
                )
            resource_timeline_has_acquired[timeline_key] = True
            resource_timeline_closeouts.setdefault(timeline_key, None)
            continue
        if not resource_timeline_has_acquired.get(timeline_key):
            raise ResourceTraceContractError(
                f"resource trace stream 非法: lease_id `{event.lease_id}` / resource_id `{event.resource_id}` 缺少 acquired"
            )
        existing_closeout = resource_timeline_closeouts.get(timeline_key)
        if existing_closeout is not None:
            raise ResourceTraceContractError(
                f"resource trace stream 非法: lease_id `{event.lease_id}` / resource_id `{event.resource_id}` 不能重复收口"
            )
        resource_timeline_closeouts[timeline_key] = event.event_type
    return tuple(canonical_events)


def build_task_resource_usage_log(events: Sequence[ResourceTraceEvent], *, task_id: str) -> TaskResourceUsageLog:
    require_non_empty_string(task_id, field="task_id")
    filtered = tuple(event for event in validate_resource_trace_stream(events) if event.task_id == task_id)
    return TaskResourceUsageLog(task_id=task_id, events=filtered)


def build_resource_lease_timeline(
    events: Sequence[ResourceTraceEvent],
    *,
    lease_id: str | None = None,
    bundle_id: str | None = None,
) -> ResourceLeaseTimeline:
    if not lease_id and not bundle_id:
        raise ResourceTraceContractError("lease_id 或 bundle_id 必须至少提供一个")
    canonical_events = validate_resource_trace_stream(events)
    filtered = tuple(
        event
        for event in canonical_events
        if (lease_id is None or event.lease_id == lease_id) and (bundle_id is None or event.bundle_id == bundle_id)
    )
    if not filtered:
        raise ResourceTraceContractError("未找到匹配的 ResourceTraceEvent")
    resolved_lease_id = filtered[0].lease_id
    resolved_bundle_id = filtered[0].bundle_id
    for event in filtered:
        if event.lease_id != resolved_lease_id or event.bundle_id != resolved_bundle_id:
            raise ResourceTraceContractError("lease timeline 中的事件必须共享同一 lease_id / bundle_id")
    grouped: dict[str, list[ResourceTraceEvent]] = defaultdict(list)
    for event in filtered:
        grouped[event.resource_id].append(event)
    resource_timelines: list[ResourceTimeline] = []
    for resource_id, resource_events in sorted(grouped.items()):
        sorted_events = tuple(sort_resource_trace_events(resource_events))
        acquired_events = [event for event in sorted_events if event.event_type == "acquired"]
        if len(acquired_events) != 1:
            raise ResourceTraceContractError("每个 resource timeline 必须且只能有一条 acquired 事件")
        released_events = [event for event in sorted_events if event.event_type == "released"]
        invalidated_events = [event for event in sorted_events if event.event_type == "invalidated"]
        if released_events and invalidated_events:
            raise ResourceTraceContractError("同一 resource timeline 不得同时存在 released 与 invalidated")
        resource_timelines.append(
            ResourceTimeline(
                resource_id=resource_id,
                resource_type=sorted_events[0].resource_type,
                acquired_at=acquired_events[0].occurred_at,
                released_at=released_events[0].occurred_at if released_events else None,
                invalidated_at=invalidated_events[0].occurred_at if invalidated_events else None,
                events=sorted_events,
            )
        )
    return ResourceLeaseTimeline(
        lease_id=resolved_lease_id,
        bundle_id=resolved_bundle_id,
        resource_timelines=tuple(resource_timelines),
    )


def resource_trace_events_for_resource(events: Sequence[ResourceTraceEvent], *, resource_id: str) -> tuple[ResourceTraceEvent, ...]:
    require_non_empty_string(resource_id, field="resource_id")
    return tuple(event for event in validate_resource_trace_stream(events) if event.resource_id == resource_id)


def sort_resource_trace_events(events: Sequence[ResourceTraceEvent]) -> tuple[ResourceTraceEvent, ...]:
    canonical = [canonical_resource_trace_event(event) for event in events]
    return tuple(sorted(canonical, key=lambda event: (parse_rfc3339_utc_datetime(event.occurred_at, field="event.occurred_at"), event.event_id)))


def require_non_empty_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ResourceTraceContractError(f"{field} 必须为非空字符串")
    return value


def parse_rfc3339_utc_datetime(value: str, *, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ResourceTraceContractError(f"{field} 必须为 RFC3339 UTC 时间")
    normalized = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ResourceTraceContractError(f"{field} 必须为 RFC3339 UTC 时间") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ResourceTraceContractError(f"{field} 必须是 UTC 时间")
    return parsed.astimezone(timezone.utc)
