from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile

from syvert.resource_lifecycle import (
    ResourceLifecycleContractError,
    ResourceLifecycleSnapshot,
    ResourceRecord,
    empty_snapshot,
    seedable_resource_records,
    snapshot_from_dict,
    snapshot_to_dict,
    validate_snapshot,
)


DEFAULT_RESOURCE_LIFECYCLE_STORE_ENV = "SYVERT_RESOURCE_LIFECYCLE_STORE_FILE"


class ResourceLifecycleStoreError(RuntimeError):
    pass


class ResourceLifecyclePersistenceError(ResourceLifecycleStoreError):
    pass


@dataclass(frozen=True)
class LocalResourceLifecycleStore:
    path: Path

    def load_snapshot(self) -> ResourceLifecycleSnapshot:
        if not self.path.exists():
            return empty_snapshot()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ResourceLifecyclePersistenceError(f"无法读取资源生命周期快照 `{self.path}`") from error
        if not isinstance(payload, Mapping):
            raise ResourceLifecyclePersistenceError(f"资源生命周期快照 `{self.path}` 必须是对象")
        try:
            return snapshot_from_dict(payload)
        except ResourceLifecycleContractError as error:
            raise ResourceLifecyclePersistenceError(f"资源生命周期快照 `{self.path}` 不满足共享 contract") from error

    def write_snapshot(self, snapshot: ResourceLifecycleSnapshot) -> ResourceLifecycleSnapshot:
        validate_snapshot(snapshot)
        payload = snapshot_to_dict(snapshot)
        self._write_json_atomic(payload)
        return snapshot

    def seed_resources(self, records: Sequence[ResourceRecord]) -> tuple[ResourceRecord, ...]:
        seeded = seedable_resource_records(records)
        snapshot = self.load_snapshot()
        existing_by_id = {record.resource_id: record for record in snapshot.resources}
        for lease in snapshot.leases:
            if lease.released_at is None:
                for resource_id in lease.resource_ids:
                    if resource_id in {record.resource_id for record in seeded}:
                        raise ResourceLifecyclePersistenceError("存在 active lease 时不得覆写其绑定资源")
        for record in seeded:
            existing_by_id[record.resource_id] = record
        updated_snapshot = ResourceLifecycleSnapshot(
            schema_version=snapshot.schema_version,
            resources=tuple(sorted(existing_by_id.values(), key=lambda item: item.resource_id)),
            leases=snapshot.leases,
        )
        self.write_snapshot(updated_snapshot)
        return updated_snapshot.resources

    def _write_json_atomic(self, payload: Mapping[str, object]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix=f".{self.path.stem}.", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
        except OSError as error:
            raise ResourceLifecyclePersistenceError(f"无法写入资源生命周期快照 `{self.path}`") from error
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


def default_resource_lifecycle_store() -> LocalResourceLifecycleStore:
    return LocalResourceLifecycleStore(resolve_resource_lifecycle_store_path())


def resolve_resource_lifecycle_store_path(env: Mapping[str, str] | None = None) -> Path:
    source = env if env is not None else os.environ
    configured = source.get(DEFAULT_RESOURCE_LIFECYCLE_STORE_ENV)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".syvert" / "resource-lifecycle.json"
