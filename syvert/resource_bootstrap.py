from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from syvert.adapters.douyin import (
    DouyinSessionConfig,
    build_session_config_from_context as build_douyin_session_config_from_context,
    load_session_config as load_douyin_session_config,
)
from syvert.adapters.xhs import (
    XhsSessionConfig,
    build_session_config_from_context as build_xhs_session_config_from_context,
    load_session_config as load_xhs_session_config,
)
from syvert.resource_lifecycle import (
    MANAGED_ACCOUNT_ADAPTER_KEY_FIELD,
    ResourceLifecycleContractError,
    ResourceBundle,
    ResourceRecord,
)
from syvert.resource_lifecycle_store import LocalResourceLifecycleStore
from syvert.runtime import AdapterExecutionContext, AdapterTaskRequest, PlatformAdapterError

SUPPORTED_BOOTSTRAP_ADAPTERS = frozenset({"xhs", "douyin"})


def load_bootstrap_material(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(f"bootstrap material file does not exist: {path}") from exc
    except OSError as exc:
        raise ValueError(f"bootstrap material file is not readable: {path}") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"bootstrap material file is not valid JSON: {path}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError(f"bootstrap material file must contain a JSON object: {path}")
    return dict(payload)


def load_account_material(
    *,
    adapter_key: str,
    account_material_file: Path | None = None,
    account_session_file: Path | None = None,
) -> dict[str, Any]:
    account_source_count = int(account_material_file is not None) + int(account_session_file is not None)
    if account_source_count != 1:
        raise ValueError("exactly one of account_material_file or account_session_file must be provided")
    if account_material_file is not None:
        return canonicalize_account_material(
            adapter_key=adapter_key,
            material=load_bootstrap_material(account_material_file),
        )
    assert account_session_file is not None
    return load_account_material_from_session_file(
        adapter_key=adapter_key,
        session_file=account_session_file,
    )


def load_account_material_from_session_file(
    *,
    adapter_key: str,
    session_file: Path,
) -> dict[str, Any]:
    try:
        if adapter_key == "xhs":
            session = load_xhs_session_config(session_file)
            material = _serialize_xhs_session(session)
            material[MANAGED_ACCOUNT_ADAPTER_KEY_FIELD] = adapter_key
            return material
        if adapter_key == "douyin":
            session = load_douyin_session_config(session_file)
            material = _serialize_douyin_session(session)
            material[MANAGED_ACCOUNT_ADAPTER_KEY_FIELD] = adapter_key
            return material
    except PlatformAdapterError as exc:
        raise ValueError(exc.message) from exc
    raise ValueError(f"unsupported bootstrap adapter_key: {adapter_key}")


def canonicalize_account_material(*, adapter_key: str, material: Mapping[str, Any]) -> dict[str, Any]:
    if adapter_key == "xhs":
        normalized = _serialize_xhs_session(_canonicalize_xhs_material(material))
        normalized[MANAGED_ACCOUNT_ADAPTER_KEY_FIELD] = adapter_key
        return normalized
    if adapter_key == "douyin":
        normalized = _serialize_douyin_session(_canonicalize_douyin_material(material))
        normalized[MANAGED_ACCOUNT_ADAPTER_KEY_FIELD] = adapter_key
        return normalized
    raise ValueError(f"unsupported bootstrap adapter_key: {adapter_key}")


def canonicalize_proxy_material(material: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(material, Mapping):
        raise ValueError(f"proxy material must be a JSON object, got {type(material).__name__}")
    normalized = dict(material)
    if not normalized:
        raise ValueError("proxy material must not be empty")
    return normalized


def build_bootstrap_records(
    *,
    adapter_key: str,
    account_resource_id: str,
    account_material: Mapping[str, Any],
    proxy_resource_id: str,
    proxy_material: Mapping[str, Any],
) -> tuple[ResourceRecord, ...]:
    if adapter_key not in SUPPORTED_BOOTSTRAP_ADAPTERS:
        raise ValueError(f"unsupported bootstrap adapter_key: {adapter_key}")
    if not account_resource_id:
        raise ValueError("account_resource_id must be non-empty")
    if not proxy_resource_id:
        raise ValueError("proxy_resource_id must be non-empty")
    canonical_account_material = canonicalize_account_material(
        adapter_key=adapter_key,
        material=account_material,
    )
    canonical_proxy_material = canonicalize_proxy_material(proxy_material)
    return (
        ResourceRecord(
            resource_id=account_resource_id,
            resource_type="account",
            status="AVAILABLE",
            material=canonical_account_material,
        ),
        ResourceRecord(
            resource_id=proxy_resource_id,
            resource_type="proxy",
            status="AVAILABLE",
            material=canonical_proxy_material,
        ),
    )


def bootstrap_resource_store(
    *,
    store: LocalResourceLifecycleStore,
    records: Sequence[ResourceRecord],
) -> tuple[ResourceRecord, ...]:
    try:
        return store.seed_resources(records)
    except ResourceLifecycleContractError as exc:
        raise ValueError(str(exc)) from exc


def _canonicalize_xhs_material(material: Mapping[str, Any]) -> XhsSessionConfig:
    try:
        return build_xhs_session_config_from_context(_material_validation_context(material))
    except PlatformAdapterError as exc:
        raise ValueError(exc.message) from exc


def _canonicalize_douyin_material(material: Mapping[str, Any]) -> DouyinSessionConfig:
    try:
        return build_douyin_session_config_from_context(_material_validation_context(material))
    except PlatformAdapterError as exc:
        raise ValueError(exc.message) from exc


def _material_validation_context(material: Mapping[str, Any]) -> AdapterExecutionContext:
    if not isinstance(material, Mapping):
        raise ValueError(f"account material must be a JSON object, got {type(material).__name__}")
    return AdapterExecutionContext(
        request=AdapterTaskRequest(
            capability="content_detail",
            target_type="url",
            target_value="https://example.com/bootstrap",
            collection_mode="hybrid",
        ),
        resource_bundle=ResourceBundle(
            bundle_id="bundle-bootstrap-validation",
            lease_id="lease-bootstrap-validation",
            task_id="task-bootstrap-validation",
            adapter_key="bootstrap",
            capability="content_detail_by_url",
            requested_slots=("account",),
            acquired_at="2026-04-21T00:00:00Z",
            account=ResourceRecord(
                resource_id="account-bootstrap-validation",
                resource_type="account",
                status="IN_USE",
                material=dict(material),
            ),
            proxy=None,
        ),
    )


def _serialize_xhs_session(session: XhsSessionConfig) -> dict[str, Any]:
    return asdict(session)


def _serialize_douyin_session(session: DouyinSessionConfig) -> dict[str, Any]:
    return asdict(session)


__all__ = [
    "SUPPORTED_BOOTSTRAP_ADAPTERS",
    "bootstrap_resource_store",
    "build_bootstrap_records",
    "canonicalize_account_material",
    "canonicalize_proxy_material",
    "load_account_material",
    "load_account_material_from_session_file",
    "load_bootstrap_material",
]
