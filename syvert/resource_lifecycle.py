from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol, Union
from uuid import uuid4

from syvert.runtime import failure_envelope, invalid_input_error, is_valid_rfc3339_utc, runtime_contract_error
from syvert.task_record import TaskRecordContractError, normalize_json_value


RESOURCE_LIFECYCLE_VERSION = "v0.4.0"
RESOURCE_TYPES = frozenset({"account", "proxy"})
RESOURCE_STATUSES = frozenset({"AVAILABLE", "IN_USE", "INVALID"})
RELEASE_TARGET_STATUSES = frozenset({"AVAILABLE", "INVALID"})


class ResourceLifecycleContractError(ValueError):
    pass


@dataclass(frozen=True)
class ResourceRecord:
    resource_id: str
    resource_type: str
    status: str
    material: Any


@dataclass(frozen=True)
class ResourceBundle:
    bundle_id: str
    lease_id: str
    task_id: str
    adapter_key: str
    capability: str
    requested_slots: tuple[str, ...]
    acquired_at: str
    account: ResourceRecord | None = None
    proxy: ResourceRecord | None = None


@dataclass(frozen=True)
class ResourceLease:
    lease_id: str
    bundle_id: str
    task_id: str
    adapter_key: str
    capability: str
    resource_ids: tuple[str, ...]
    acquired_at: str
    released_at: str | None = None
    target_status_after_release: str | None = None
    release_reason: str | None = None


@dataclass(frozen=True)
class AcquireRequest:
    task_id: str
    adapter_key: str
    capability: str
    requested_slots: tuple[str, ...]


@dataclass(frozen=True)
class ReleaseRequest:
    lease_id: str
    task_id: str
    target_status_after_release: str
    reason: str


@dataclass(frozen=True)
class ResourceLifecycleSnapshot:
    schema_version: str
    revision: int
    resources: tuple[ResourceRecord, ...]
    leases: tuple[ResourceLease, ...]


class ResourceLifecycleStore(Protocol):
    """Store boundary for lifecycle truth.

    Implementations should raise ResourceLifecycleContractError on fail-closed errors.
    acquire()/release() still defensively coerce unexpected backend exceptions into
    resource_state_conflict so callers do not observe raw store failures.
    """

    def load_snapshot(self) -> ResourceLifecycleSnapshot:
        ...

    def write_snapshot(self, snapshot: ResourceLifecycleSnapshot) -> ResourceLifecycleSnapshot:
        ...


ResourceAcquireResult = Union[ResourceBundle, dict[str, Any]]
ResourceReleaseResult = Union[ResourceLease, dict[str, Any]]


def now_rfc3339_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def empty_snapshot() -> ResourceLifecycleSnapshot:
    return ResourceLifecycleSnapshot(
        schema_version=RESOURCE_LIFECYCLE_VERSION,
        revision=0,
        resources=(),
        leases=(),
    )


def acquire(
    request: Any,
    store: ResourceLifecycleStore,
    task_context_task_id: str,
) -> ResourceAcquireResult:
    task_context_task_id = require_task_context_task_id(task_context_task_id)
    envelope_task_id = recover_acquire_failure_task_id(request, task_context_task_id)
    adapter_key = recover_acquire_failure_adapter_key(request)
    capability = recover_acquire_failure_capability(request)

    try:
        normalized_request = normalize_acquire_request(request)
        snapshot = load_snapshot_from_store(store)
        validate_snapshot(snapshot)
    except ResourceLifecycleContractError as error:
        return failure_envelope(
            envelope_task_id,
            adapter_key,
            capability,
            classify_acquire_contract_error(error),
        )

    adapter_key = normalized_request.adapter_key
    capability = normalized_request.capability
    try:
        current_snapshot = snapshot
        while True:
            selected = select_available_resources(current_snapshot, normalized_request.requested_slots)
            selected_resource_ids = {slot: record.resource_id for slot, record in selected.items()}
            acquired_at = now_rfc3339_utc()
            bundle = build_resource_bundle(
                task_id=normalized_request.task_id,
                adapter_key=adapter_key,
                capability=capability,
                requested_slots=normalized_request.requested_slots,
                selected_resources=selected,
                acquired_at=acquired_at,
            )
            lease = build_resource_lease(bundle)
            updated_resources = apply_acquire_transition(current_snapshot.resources, selected)
            updated_snapshot = ResourceLifecycleSnapshot(
                schema_version=current_snapshot.schema_version,
                revision=current_snapshot.revision + 1,
                resources=tuple(sorted(updated_resources, key=lambda record: record.resource_id)),
                leases=tuple([*current_snapshot.leases, lease]),
            )
            validate_snapshot(updated_snapshot)
            try:
                write_snapshot_to_store(store, updated_snapshot)
                return bundle
            except ResourceLifecycleContractError as error:
                if not is_retryable_revision_conflict(error):
                    raise
                refreshed_snapshot = load_snapshot_from_store(store)
                validate_snapshot(refreshed_snapshot)
                try:
                    refreshed_selected = select_available_resources(
                        refreshed_snapshot,
                        normalized_request.requested_slots,
                    )
                except ResourceLifecycleContractError as refreshed_error:
                    raise state_conflict_error("revision 冲突后资源选择已过期") from refreshed_error
                refreshed_resource_ids = {
                    slot: record.resource_id for slot, record in refreshed_selected.items()
                }
                if refreshed_resource_ids != selected_resource_ids:
                    raise state_conflict_error("revision 冲突后资源选择已过期")
                current_snapshot = refreshed_snapshot
    except ResourceLifecycleContractError as error:
        return failure_envelope(
            normalized_request.task_id,
            adapter_key,
            capability,
            classify_acquire_contract_error(error),
        )


def release(
    request: Any,
    store: ResourceLifecycleStore,
    task_context_task_id: str,
) -> ResourceReleaseResult:
    task_context_task_id = require_task_context_task_id(task_context_task_id)
    snapshot: ResourceLifecycleSnapshot | None = None
    lease: ResourceLease | None = None
    raw_lease_id = extract_optional_string(request, "lease_id")
    try:
        snapshot = load_snapshot_from_store(store)
        validate_snapshot(snapshot)
        if raw_lease_id:
            lease = find_lease(snapshot, raw_lease_id)
    except ResourceLifecycleContractError:
        snapshot = None
        lease = None

    envelope_task_id = recover_release_failure_task_id(request, task_context_task_id, lease)
    adapter_key = recover_release_failure_adapter_key(lease)
    capability = recover_release_failure_capability(lease)

    try:
        normalized_request = normalize_release_request(request)
        if snapshot is None:
            snapshot = load_snapshot_from_store(store)
            validate_snapshot(snapshot)
        lease = require_lease(snapshot, normalized_request.lease_id)
    except ResourceLifecycleContractError as error:
        return failure_envelope(
            envelope_task_id,
            adapter_key,
            capability,
            classify_release_contract_error(error),
        )

    envelope_task_id = normalized_request.task_id
    adapter_key = lease.adapter_key
    capability = lease.capability

    try:
        current_snapshot = snapshot
        while True:
            current_lease = require_lease(current_snapshot, normalized_request.lease_id)
            if current_lease.task_id != normalized_request.task_id:
                raise lease_mismatch_error("release task_id 与 lease 绑定 task_id 不一致")
            if current_lease.released_at is not None:
                if (
                    current_lease.target_status_after_release == normalized_request.target_status_after_release
                    and current_lease.release_reason == normalized_request.reason
                ):
                    return current_lease
                raise release_conflict_error("重复 release 的目标状态或原因与既有 settled lease 不一致")

            resources_by_id = {record.resource_id: record for record in current_snapshot.resources}
            for resource_id in current_lease.resource_ids:
                record = resources_by_id.get(resource_id)
                if record is None:
                    raise state_conflict_error(f"lease 绑定的资源 `{resource_id}` 不存在")
                if record.status != "IN_USE":
                    raise state_conflict_error(f"lease 绑定的资源 `{resource_id}` 未处于 IN_USE")

            released_at = now_rfc3339_utc()
            settled_lease = ResourceLease(
                lease_id=current_lease.lease_id,
                bundle_id=current_lease.bundle_id,
                task_id=current_lease.task_id,
                adapter_key=current_lease.adapter_key,
                capability=current_lease.capability,
                resource_ids=current_lease.resource_ids,
                acquired_at=current_lease.acquired_at,
                released_at=released_at,
                target_status_after_release=normalized_request.target_status_after_release,
                release_reason=normalized_request.reason,
            )
            validate_resource_lease(settled_lease)
            updated_resources = apply_release_transition(
                current_snapshot.resources,
                current_lease.resource_ids,
                normalized_request.target_status_after_release,
            )
            updated_leases = tuple(
                settled_lease if existing.lease_id == current_lease.lease_id else existing
                for existing in current_snapshot.leases
            )
            updated_snapshot = ResourceLifecycleSnapshot(
                schema_version=current_snapshot.schema_version,
                revision=current_snapshot.revision + 1,
                resources=tuple(sorted(updated_resources, key=lambda record: record.resource_id)),
                leases=updated_leases,
            )
            validate_snapshot(updated_snapshot)
            try:
                write_snapshot_to_store(store, updated_snapshot)
                return settled_lease
            except ResourceLifecycleContractError as error:
                refreshed_snapshot = load_snapshot_from_store(store)
                validate_snapshot(refreshed_snapshot)
                refreshed_lease = require_lease(refreshed_snapshot, current_lease.lease_id)
                if refreshed_lease.released_at is not None:
                    if (
                        refreshed_lease.target_status_after_release == normalized_request.target_status_after_release
                        and refreshed_lease.release_reason == normalized_request.reason
                    ):
                        return refreshed_lease
                    raise release_conflict_error("重复 release 的目标状态或原因与既有 settled lease 不一致")
                if not is_retryable_revision_conflict(error):
                    raise
                current_snapshot = refreshed_snapshot
    except ResourceLifecycleContractError as error:
        return failure_envelope(
            envelope_task_id,
            adapter_key,
            capability,
            classify_release_contract_error(error),
        )


def seedable_resource_records(records: Sequence[ResourceRecord]) -> tuple[ResourceRecord, ...]:
    if isinstance(records, (str, bytes)):
        raise ResourceLifecycleContractError("seed_resources 需要 ResourceRecord 数组")
    normalized: list[ResourceRecord] = []
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, ResourceRecord):
            raise ResourceLifecycleContractError("seed_resources 仅允许写入 ResourceRecord")
        normalized_record = canonical_resource_record(record)
        if record.resource_id in seen:
            raise ResourceLifecycleContractError("seed_resources 不允许重复 resource_id")
        seen.add(normalized_record.resource_id)
        normalized.append(normalized_record)
    return tuple(sorted(normalized, key=lambda record: record.resource_id))


def snapshot_to_dict(snapshot: ResourceLifecycleSnapshot) -> dict[str, Any]:
    validate_snapshot(snapshot)
    return {
        "schema_version": snapshot.schema_version,
        "revision": snapshot.revision,
        "resources": [resource_record_to_dict(record) for record in snapshot.resources],
        "leases": [resource_lease_to_dict(lease) for lease in snapshot.leases],
    }


def snapshot_from_dict(payload: Mapping[str, Any]) -> ResourceLifecycleSnapshot:
    if not isinstance(payload, Mapping):
        raise ResourceLifecycleContractError("资源生命周期快照必须是对象")
    raw_resources = payload.get("resources")
    raw_leases = payload.get("leases")
    if not isinstance(raw_resources, list):
        raise ResourceLifecycleContractError("资源生命周期快照.resources 必须是数组")
    if not isinstance(raw_leases, list):
        raise ResourceLifecycleContractError("资源生命周期快照.leases 必须是数组")
    snapshot = ResourceLifecycleSnapshot(
        schema_version=require_contract_non_empty_string(payload.get("schema_version"), field="snapshot.schema_version"),
        revision=require_non_negative_int(payload.get("revision"), field="snapshot.revision"),
        resources=tuple(resource_record_from_dict(item) for item in raw_resources),
        leases=tuple(resource_lease_from_dict(item) for item in raw_leases),
    )
    validate_snapshot(snapshot)
    return snapshot


def resource_record_to_dict(record: ResourceRecord) -> dict[str, Any]:
    validate_resource_record(record)
    return {
        "resource_id": record.resource_id,
        "resource_type": record.resource_type,
        "status": record.status,
        "material": normalize_resource_material(record.material, field=f"resource[{record.resource_id}].material"),
    }


def resource_record_from_dict(payload: Mapping[str, Any]) -> ResourceRecord:
    if not isinstance(payload, Mapping):
        raise ResourceLifecycleContractError("资源记录必须是对象")
    record = ResourceRecord(
        resource_id=require_contract_non_empty_string(payload.get("resource_id"), field="resource.resource_id"),
        resource_type=require_contract_non_empty_string(payload.get("resource_type"), field="resource.resource_type"),
        status=require_contract_non_empty_string(payload.get("status"), field="resource.status"),
        material=normalize_resource_material(payload.get("material"), field="resource.material"),
    )
    validate_resource_record(record)
    return record


def resource_bundle_to_dict(bundle: ResourceBundle) -> dict[str, Any]:
    validate_resource_bundle(bundle)
    payload: dict[str, Any] = {
        "bundle_id": bundle.bundle_id,
        "lease_id": bundle.lease_id,
        "task_id": bundle.task_id,
        "adapter_key": bundle.adapter_key,
        "capability": bundle.capability,
        "requested_slots": list(bundle.requested_slots),
        "acquired_at": bundle.acquired_at,
    }
    if bundle.account is not None:
        payload["account"] = resource_record_to_dict(bundle.account)
    if bundle.proxy is not None:
        payload["proxy"] = resource_record_to_dict(bundle.proxy)
    return payload


def resource_lease_to_dict(lease: ResourceLease) -> dict[str, Any]:
    validate_resource_lease(lease)
    return {
        "lease_id": lease.lease_id,
        "bundle_id": lease.bundle_id,
        "task_id": lease.task_id,
        "adapter_key": lease.adapter_key,
        "capability": lease.capability,
        "resource_ids": list(lease.resource_ids),
        "acquired_at": lease.acquired_at,
        "released_at": lease.released_at,
        "target_status_after_release": lease.target_status_after_release,
        "release_reason": lease.release_reason,
    }


def resource_lease_from_dict(payload: Mapping[str, Any]) -> ResourceLease:
    if not isinstance(payload, Mapping):
        raise ResourceLifecycleContractError("资源 lease 必须是对象")
    raw_resource_ids = payload.get("resource_ids")
    if not isinstance(raw_resource_ids, list):
        raise ResourceLifecycleContractError("lease.resource_ids 必须是数组")
    lease = ResourceLease(
        lease_id=require_contract_non_empty_string(payload.get("lease_id"), field="lease.lease_id"),
        bundle_id=require_contract_non_empty_string(payload.get("bundle_id"), field="lease.bundle_id"),
        task_id=require_contract_non_empty_string(payload.get("task_id"), field="lease.task_id"),
        adapter_key=require_contract_non_empty_string(payload.get("adapter_key"), field="lease.adapter_key"),
        capability=require_contract_non_empty_string(payload.get("capability"), field="lease.capability"),
        resource_ids=tuple(
            require_contract_non_empty_string(resource_id, field="lease.resource_ids[]") for resource_id in raw_resource_ids
        ),
        acquired_at=require_contract_non_empty_string(payload.get("acquired_at"), field="lease.acquired_at"),
        released_at=require_optional_contract_non_empty_string(payload.get("released_at"), field="lease.released_at"),
        target_status_after_release=require_optional_contract_non_empty_string(
            payload.get("target_status_after_release"),
            field="lease.target_status_after_release",
        ),
        release_reason=require_optional_contract_non_empty_string(payload.get("release_reason"), field="lease.release_reason"),
    )
    validate_resource_lease(lease)
    return lease


def validate_snapshot(snapshot: ResourceLifecycleSnapshot) -> None:
    if snapshot.schema_version != RESOURCE_LIFECYCLE_VERSION:
        raise ResourceLifecycleContractError("资源生命周期快照 schema_version 不合法")
    if isinstance(snapshot.revision, bool) or not isinstance(snapshot.revision, int) or snapshot.revision < 0:
        raise ResourceLifecycleContractError("资源生命周期快照 revision 不合法")

    resource_ids: set[str] = set()
    resources_by_id: dict[str, ResourceRecord] = {}
    for record in snapshot.resources:
        validate_resource_record(record)
        if record.resource_id in resource_ids:
            raise ResourceLifecycleContractError("资源生命周期快照存在重复 resource_id")
        resource_ids.add(record.resource_id)
        resources_by_id[record.resource_id] = record

    lease_ids: set[str] = set()
    active_resource_ids: set[str] = set()
    latest_settled_by_resource_id: dict[str, tuple[tuple[datetime, int], str]] = {}
    invalid_released_at_by_resource_id: dict[str, tuple[datetime, int]] = {}
    leases_by_resource_id: dict[str, list[tuple[tuple[datetime, int], tuple[datetime, int] | None, ResourceLease]]] = {}
    for lease_index, lease in enumerate(snapshot.leases):
        validate_resource_lease(lease)
        acquired_marker = (parse_rfc3339_utc_datetime(lease.acquired_at, field="lease.acquired_at"), lease_index)
        if lease.lease_id in lease_ids:
            raise ResourceLifecycleContractError("资源生命周期快照存在重复 lease_id")
        lease_ids.add(lease.lease_id)
        for resource_id in lease.resource_ids:
            if resource_id not in resources_by_id:
                raise ResourceLifecycleContractError("lease 绑定了不存在的 resource_id")
        released_marker: tuple[datetime, int] | None = None
        if lease.released_at is None:
            for resource_id in lease.resource_ids:
                if resource_id in active_resource_ids:
                    raise ResourceLifecycleContractError("同一资源被多个 active lease 重复占用")
                active_resource_ids.add(resource_id)
        else:
            assert lease.target_status_after_release is not None
            released_marker = (parse_rfc3339_utc_datetime(lease.released_at, field="lease.released_at"), lease_index)
            for resource_id in lease.resource_ids:
                latest = latest_settled_by_resource_id.get(resource_id)
                if latest is None or released_marker > latest[0]:
                    latest_settled_by_resource_id[resource_id] = (released_marker, lease.target_status_after_release)
                if lease.target_status_after_release == "INVALID":
                    invalid_released_at = invalid_released_at_by_resource_id.get(resource_id)
                    if invalid_released_at is None or released_marker > invalid_released_at:
                        invalid_released_at_by_resource_id[resource_id] = released_marker
        for resource_id in lease.resource_ids:
            leases_by_resource_id.setdefault(resource_id, []).append((acquired_marker, released_marker, lease))

    for resource_id in active_resource_ids:
        if resources_by_id[resource_id].status != "IN_USE":
            raise ResourceLifecycleContractError("active lease 绑定资源必须处于 IN_USE")
    for resource_id, record in resources_by_id.items():
        if record.status == "IN_USE" and resource_id not in active_resource_ids:
            raise ResourceLifecycleContractError("IN_USE 资源必须由唯一 active lease 持有")
        if record.status != "IN_USE" and resource_id not in active_resource_ids:
            latest_settled = latest_settled_by_resource_id.get(resource_id)
            if latest_settled is not None and record.status != latest_settled[1]:
                raise ResourceLifecycleContractError("资源状态必须与最新 settled lease truth 一致")
        invalid_released_at = invalid_released_at_by_resource_id.get(resource_id)
        if invalid_released_at is not None:
            if record.status != "INVALID":
                raise ResourceLifecycleContractError("INVALID 资源不得被重新写回其他状态")
            for acquired_marker, _, _lease in leases_by_resource_id.get(resource_id, []):
                if acquired_marker > invalid_released_at:
                    raise ResourceLifecycleContractError("INVALID 资源不得在 settled 后再次被 lease 占用")
        intervals = sorted(leases_by_resource_id.get(resource_id, []), key=lambda item: item[0])
        previous_end: tuple[datetime, int] | None = None
        active_seen = False
        for acquired_marker, released_marker, _lease in intervals:
            if active_seen:
                raise ResourceLifecycleContractError("active lease 之后不得再出现后续 lease")
            if previous_end is not None and acquired_marker < previous_end:
                raise ResourceLifecycleContractError("同一资源的 lease 时间区间不得重叠")
            previous_end = released_marker
            if released_marker is None:
                active_seen = True


def validate_resource_record(record: ResourceRecord) -> None:
    require_contract_non_empty_string(record.resource_id, field="resource.resource_id")
    if record.resource_type not in RESOURCE_TYPES:
        raise ResourceLifecycleContractError("resource.resource_type 不在允许值范围内")
    if record.status not in RESOURCE_STATUSES:
        raise ResourceLifecycleContractError("resource.status 不在允许值范围内")
    normalize_resource_material(record.material, field=f"resource[{record.resource_id}].material")


def validate_resource_bundle(bundle: ResourceBundle) -> None:
    require_contract_non_empty_string(bundle.bundle_id, field="bundle.bundle_id")
    require_contract_non_empty_string(bundle.lease_id, field="bundle.lease_id")
    require_contract_non_empty_string(bundle.task_id, field="bundle.task_id")
    require_contract_non_empty_string(bundle.adapter_key, field="bundle.adapter_key")
    require_contract_non_empty_string(bundle.capability, field="bundle.capability")
    validate_requested_slots(bundle.requested_slots, field="bundle.requested_slots")
    validate_rfc3339_utc(bundle.acquired_at, field="bundle.acquired_at")

    for slot in RESOURCE_TYPES:
        resource = getattr(bundle, slot)
        if slot in bundle.requested_slots:
            if resource is None:
                raise ResourceLifecycleContractError("requested slot 在 bundle 中不得缺失")
            validate_resource_record(resource)
            if resource.resource_type != slot:
                raise ResourceLifecycleContractError("bundle slot 与资源类型不一致")
            if resource.status != "IN_USE":
                raise ResourceLifecycleContractError("成功 acquire 返回的资源必须处于 IN_USE")
        elif resource is not None:
            raise ResourceLifecycleContractError("未请求 slot 不得出现在成功 bundle 中")


def validate_resource_lease(lease: ResourceLease) -> None:
    require_contract_non_empty_string(lease.lease_id, field="lease.lease_id")
    require_contract_non_empty_string(lease.bundle_id, field="lease.bundle_id")
    require_contract_non_empty_string(lease.task_id, field="lease.task_id")
    require_contract_non_empty_string(lease.adapter_key, field="lease.adapter_key")
    require_contract_non_empty_string(lease.capability, field="lease.capability")
    validate_unique_non_empty_strings(lease.resource_ids, field="lease.resource_ids")
    acquired_at = parse_rfc3339_utc_datetime(lease.acquired_at, field="lease.acquired_at")

    if lease.released_at is None:
        if lease.target_status_after_release is not None or lease.release_reason is not None:
            raise ResourceLifecycleContractError("active lease 不得包含 release 收口字段")
        return

    released_at = parse_rfc3339_utc_datetime(lease.released_at, field="lease.released_at")
    if released_at < acquired_at:
        raise ResourceLifecycleContractError("lease.released_at 不得早于 lease.acquired_at")
    if lease.target_status_after_release not in RELEASE_TARGET_STATUSES:
        raise ResourceLifecycleContractError("lease.target_status_after_release 不在允许值范围内")
    require_contract_non_empty_string(lease.release_reason, field="lease.release_reason")


def normalize_acquire_request(request: Any) -> AcquireRequest:
    normalized = AcquireRequest(
        task_id=require_request_non_empty_string(extract_string(request, "task_id"), field="acquire.task_id"),
        adapter_key=require_request_non_empty_string(extract_string(request, "adapter_key"), field="acquire.adapter_key"),
        capability=require_request_non_empty_string(extract_string(request, "capability"), field="acquire.capability"),
        requested_slots=tuple(extract_requested_slots(request)),
    )
    validate_acquire_request(normalized)
    return normalized


def normalize_release_request(request: Any) -> ReleaseRequest:
    normalized = ReleaseRequest(
        lease_id=require_release_non_empty_string(extract_release_string(request, "lease_id"), field="release.lease_id"),
        task_id=require_release_non_empty_string(extract_release_string(request, "task_id"), field="release.task_id"),
        target_status_after_release=require_release_non_empty_string(
            extract_release_string(request, "target_status_after_release"),
            field="release.target_status_after_release",
        ),
        reason=require_release_non_empty_string(extract_release_string(request, "reason"), field="release.reason"),
    )
    validate_release_request(normalized)
    return normalized


def validate_acquire_request(request: AcquireRequest) -> None:
    require_request_non_empty_string(request.task_id, field="acquire.task_id")
    require_request_non_empty_string(request.adapter_key, field="acquire.adapter_key")
    require_request_non_empty_string(request.capability, field="acquire.capability")
    validate_requested_slots(request.requested_slots, field="acquire.requested_slots")


def validate_release_request(request: ReleaseRequest) -> None:
    require_release_non_empty_string(request.lease_id, field="release.lease_id")
    require_release_non_empty_string(request.task_id, field="release.task_id")
    if request.target_status_after_release not in RELEASE_TARGET_STATUSES:
        raise invalid_release_error("release.target_status_after_release 不在允许值范围内")
    require_release_non_empty_string(request.reason, field="release.reason")


def build_resource_bundle(
    *,
    task_id: str,
    adapter_key: str,
    capability: str,
    requested_slots: tuple[str, ...],
    selected_resources: Mapping[str, ResourceRecord],
    acquired_at: str,
) -> ResourceBundle:
    bundle = ResourceBundle(
        bundle_id=f"bundle-{uuid4().hex}",
        lease_id=f"lease-{uuid4().hex}",
        task_id=task_id,
        adapter_key=adapter_key,
        capability=capability,
        requested_slots=requested_slots,
        acquired_at=acquired_at,
        account=_selected_resource_for_slot(selected_resources, "account"),
        proxy=_selected_resource_for_slot(selected_resources, "proxy"),
    )
    validate_resource_bundle(bundle)
    return bundle


def build_resource_lease(bundle: ResourceBundle) -> ResourceLease:
    resource_ids = tuple(
        getattr(bundle, slot).resource_id for slot in bundle.requested_slots if getattr(bundle, slot) is not None
    )
    lease = ResourceLease(
        lease_id=bundle.lease_id,
        bundle_id=bundle.bundle_id,
        task_id=bundle.task_id,
        adapter_key=bundle.adapter_key,
        capability=bundle.capability,
        resource_ids=resource_ids,
        acquired_at=bundle.acquired_at,
    )
    validate_resource_lease(lease)
    return lease


def select_available_resources(
    snapshot: ResourceLifecycleSnapshot,
    requested_slots: tuple[str, ...],
) -> dict[str, ResourceRecord]:
    resources_by_type: dict[str, list[ResourceRecord]] = {slot: [] for slot in RESOURCE_TYPES}
    active_resource_ids = {
        resource_id
        for lease in snapshot.leases
        if lease.released_at is None
        for resource_id in lease.resource_ids
    }
    for record in snapshot.resources:
        if record.status == "AVAILABLE":
            resources_by_type[record.resource_type].append(record)
        elif record.status == "INVALID":
            continue

    selected: dict[str, ResourceRecord] = {}
    for slot in requested_slots:
        candidates = sorted(resources_by_type[slot], key=lambda record: record.resource_id)
        if not candidates:
            raise unavailable_error(f"slot `{slot}` 缺少 AVAILABLE 资源")
        candidate = candidates[0]
        if candidate.resource_id in active_resource_ids:
            raise state_conflict_error("AVAILABLE 资源与 active lease 真相冲突")
        selected[slot] = ResourceRecord(
            resource_id=candidate.resource_id,
            resource_type=candidate.resource_type,
            status="IN_USE",
            material=candidate.material,
        )
    return selected


def apply_acquire_transition(
    records: Sequence[ResourceRecord],
    selected_resources: Mapping[str, ResourceRecord],
) -> tuple[ResourceRecord, ...]:
    selected_ids = {record.resource_id for record in selected_resources.values()}
    updated: list[ResourceRecord] = []
    for record in records:
        if record.resource_id in selected_ids:
            if record.status != "AVAILABLE":
                raise state_conflict_error("acquire 只能把 AVAILABLE 资源推进到 IN_USE")
            updated.append(
                ResourceRecord(
                    resource_id=record.resource_id,
                    resource_type=record.resource_type,
                    status="IN_USE",
                    material=record.material,
                )
            )
            continue
        updated.append(record)
    if selected_ids != {record.resource_id for record in updated if record.status == "IN_USE"} & selected_ids:
        raise state_conflict_error("acquire 未能完整推进所有选中资源")
    return tuple(updated)


def apply_release_transition(
    records: Sequence[ResourceRecord],
    resource_ids: tuple[str, ...],
    target_status_after_release: str,
) -> tuple[ResourceRecord, ...]:
    resource_id_set = set(resource_ids)
    updated: list[ResourceRecord] = []
    released_ids: set[str] = set()
    for record in records:
        if record.resource_id not in resource_id_set:
            updated.append(record)
            continue
        if record.status != "IN_USE":
            raise state_conflict_error("release 只能作用于当前 IN_USE 资源")
        released_ids.add(record.resource_id)
        updated.append(
            ResourceRecord(
                resource_id=record.resource_id,
                resource_type=record.resource_type,
                status=target_status_after_release,
                material=record.material,
            )
        )
    if released_ids != resource_id_set:
        raise state_conflict_error("release 绑定的资源集合不完整")
    return tuple(updated)


def find_lease(snapshot: ResourceLifecycleSnapshot, lease_id: str) -> ResourceLease | None:
    for lease in snapshot.leases:
        if lease.lease_id == lease_id:
            return lease
    return None


def require_lease(snapshot: ResourceLifecycleSnapshot, lease_id: str) -> ResourceLease:
    lease = find_lease(snapshot, lease_id)
    if lease is None:
        raise lease_mismatch_error(f"lease `{lease_id}` 不存在")
    return lease


def classify_acquire_contract_error(error: ResourceLifecycleContractError) -> dict[str, Any]:
    message = str(error)
    if message.startswith("invalid_resource_request:"):
        return invalid_input_error("invalid_resource_request", message.partition(":")[2].strip())
    if message.startswith("resource_unavailable:"):
        return runtime_contract_error("resource_unavailable", message.partition(":")[2].strip())
    if message.startswith("resource_state_conflict:"):
        return runtime_contract_error("resource_state_conflict", message.partition(":")[2].strip())
    return runtime_contract_error("resource_state_conflict", message)


def classify_release_contract_error(error: ResourceLifecycleContractError) -> dict[str, Any]:
    message = str(error)
    if message.startswith("invalid_resource_release:"):
        return invalid_input_error("invalid_resource_release", message.partition(":")[2].strip())
    if message.startswith("resource_lease_mismatch:"):
        return runtime_contract_error("resource_lease_mismatch", message.partition(":")[2].strip())
    if message.startswith("resource_release_conflict:"):
        return runtime_contract_error("resource_release_conflict", message.partition(":")[2].strip())
    if message.startswith("resource_state_conflict:"):
        return runtime_contract_error("resource_state_conflict", message.partition(":")[2].strip())
    return runtime_contract_error("resource_state_conflict", message)


def recover_acquire_failure_task_id(request: Any, task_context_task_id: str) -> str:
    if is_non_empty_string(extract_optional_string(request, "task_id")):
        return extract_optional_string(request, "task_id") or ""
    return task_context_task_id if is_non_empty_string(task_context_task_id) else ""


def recover_acquire_failure_adapter_key(request: Any) -> str:
    return extract_optional_string(request, "adapter_key") or ""


def recover_acquire_failure_capability(request: Any) -> str:
    return extract_optional_string(request, "capability") or ""


def recover_release_failure_task_id(
    request: Any,
    task_context_task_id: str,
    lease: ResourceLease | None,
) -> str:
    request_task_id = extract_optional_string(request, "task_id")
    if request_task_id:
        return request_task_id
    if is_non_empty_string(task_context_task_id):
        return task_context_task_id
    return ""


def recover_release_failure_adapter_key(lease: ResourceLease | None) -> str:
    if lease is None:
        return ""
    return lease.adapter_key


def recover_release_failure_capability(lease: ResourceLease | None) -> str:
    if lease is None:
        return ""
    return lease.capability


def validate_requested_slots(value: Sequence[str], *, field: str) -> None:
    if isinstance(value, (str, bytes)):
        raise invalid_request_error(f"{field} 必须为非空去重数组")
    slots = tuple(value)
    if not slots:
        raise invalid_request_error(f"{field} 必须为非空去重数组")
    seen: set[str] = set()
    for slot in slots:
        if not isinstance(slot, str) or not slot:
            raise invalid_request_error(f"{field} 存在非法 slot")
        if slot in seen:
            raise invalid_request_error(f"{field} 不允许重复 slot")
        seen.add(slot)
        if slot not in RESOURCE_TYPES:
            raise invalid_request_error(f"{field} 存在未知 slot `{slot}`")


def extract_requested_slots(request: Any) -> tuple[str, ...]:
    raw = extract_value(request, "requested_slots")
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence):
        raise invalid_request_error("requested_slots 必须为非空去重数组")
    return tuple(raw)


def extract_string(request: Any, field: str) -> str:
    value = extract_value(request, field)
    if not isinstance(value, str):
        raise invalid_request_error(f"{field} 必须为非空字符串")
    return value


def extract_release_string(request: Any, field: str) -> str:
    value = extract_value(request, field)
    if not isinstance(value, str):
        raise invalid_release_error(f"{field} 必须为非空字符串")
    return value


def extract_optional_string(request: Any, field: str) -> str | None:
    value = extract_value(request, field, missing=None)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        return None
    return value


def extract_value(request: Any, field: str, *, missing: Any = None) -> Any:
    if isinstance(request, Mapping):
        return request.get(field, missing)
    return getattr(request, field, missing)


def require_request_non_empty_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise invalid_request_error(f"{field} 必须为非空字符串")
    return value


def require_release_non_empty_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise invalid_release_error(f"{field} 必须为非空字符串")
    return value


def require_contract_non_empty_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ResourceLifecycleContractError(f"{field} 必须为非空字符串")
    return value


def require_optional_contract_non_empty_string(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ResourceLifecycleContractError(f"{field} 必须为非空字符串或 null")
    return value


def require_non_negative_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ResourceLifecycleContractError(f"{field} 必须为非负整数")
    return value


def require_task_context_task_id(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("task_context_task_id 必须为非空字符串")
    return value


def validate_unique_non_empty_strings(values: Sequence[str], *, field: str) -> None:
    if isinstance(values, (str, bytes)) or not values:
        raise ResourceLifecycleContractError(f"{field} 必须为非空去重数组")
    seen: set[str] = set()
    for value in values:
        require_contract_non_empty_string(value, field=field)
        if value in seen:
            raise ResourceLifecycleContractError(f"{field} 不允许重复值")
        seen.add(value)


def validate_rfc3339_utc(value: str, *, field: str) -> None:
    if not isinstance(value, str) or not is_valid_rfc3339_utc(value):
        raise ResourceLifecycleContractError(f"{field} 必须为 RFC3339 UTC 时间")


def parse_rfc3339_utc_datetime(value: str, *, field: str) -> datetime:
    validate_rfc3339_utc(value, field=field)
    normalized = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ResourceLifecycleContractError(f"{field} 必须为 RFC3339 UTC 时间") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ResourceLifecycleContractError(f"{field} 必须是 UTC 时间")
    return parsed.astimezone(timezone.utc)


def normalize_resource_material(value: Any, *, field: str) -> Any:
    try:
        return normalize_json_value(value, field=field)
    except TaskRecordContractError as error:
        raise ResourceLifecycleContractError(str(error)) from error


def canonical_resource_record(record: ResourceRecord) -> ResourceRecord:
    normalized = ResourceRecord(
        resource_id=record.resource_id,
        resource_type=record.resource_type,
        status=record.status,
        material=normalize_resource_material(record.material, field=f"resource[{record.resource_id}].material"),
    )
    validate_resource_record(normalized)
    return normalized


def _selected_resource_for_slot(
    selected_resources: Mapping[str, ResourceRecord],
    slot: str,
) -> ResourceRecord | None:
    return selected_resources.get(slot)


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def invalid_request_error(message: str) -> ResourceLifecycleContractError:
    return ResourceLifecycleContractError(f"invalid_resource_request: {message}")


def is_retryable_revision_conflict(error: ResourceLifecycleContractError) -> bool:
    return str(error).startswith("resource_state_conflict: 资源生命周期快照 revision 与当前 durable truth 不一致")


def invalid_release_error(message: str) -> ResourceLifecycleContractError:
    return ResourceLifecycleContractError(f"invalid_resource_release: {message}")


def unavailable_error(message: str) -> ResourceLifecycleContractError:
    return ResourceLifecycleContractError(f"resource_unavailable: {message}")


def lease_mismatch_error(message: str) -> ResourceLifecycleContractError:
    return ResourceLifecycleContractError(f"resource_lease_mismatch: {message}")


def release_conflict_error(message: str) -> ResourceLifecycleContractError:
    return ResourceLifecycleContractError(f"resource_release_conflict: {message}")


def state_conflict_error(message: str) -> ResourceLifecycleContractError:
    return ResourceLifecycleContractError(f"resource_state_conflict: {message}")


def load_snapshot_from_store(store: ResourceLifecycleStore) -> ResourceLifecycleSnapshot:
    try:
        return store.load_snapshot()
    except ResourceLifecycleContractError:
        raise
    except Exception as error:
        raise state_conflict_error("资源生命周期 store.load_snapshot 失败") from error


def write_snapshot_to_store(store: ResourceLifecycleStore, snapshot: ResourceLifecycleSnapshot) -> ResourceLifecycleSnapshot:
    try:
        return store.write_snapshot(snapshot)
    except ResourceLifecycleContractError:
        raise
    except Exception as error:
        raise state_conflict_error("资源生命周期 store.write_snapshot 失败") from error
