from __future__ import annotations

import os
import tempfile
from typing import Any
from unittest import mock

from syvert.registry import baseline_multi_profile_resource_requirement_declaration
from syvert.resource_lifecycle import MANAGED_ACCOUNT_ADAPTER_KEY_FIELD, ResourceBundle, ResourceRecord
from syvert.resource_lifecycle_store import default_resource_lifecycle_store
from syvert.resource_trace_store import default_resource_trace_store


def generic_account_material() -> dict[str, Any]:
    return {
        "cookies": "a=1; b=2",
        "user_agent": "Mozilla/5.0 TestAgent",
        "sign_base_url": "http://127.0.0.1:8000",
        "verify_fp": "verify-1",
        "ms_token": "ms-token-1",
        "webid": "webid-1",
        "timeout_seconds": 5,
    }


def xhs_account_material() -> dict[str, Any]:
    return {
        "cookies": "a=1; b=2",
        "user_agent": "Mozilla/5.0 TestAgent",
        "sign_base_url": "http://127.0.0.1:8000",
        "timeout_seconds": 5,
    }


def douyin_account_material() -> dict[str, Any]:
    return {
        "cookies": "a=1; b=2",
        "user_agent": "Mozilla/5.0 TestAgent",
        "verify_fp": "verify-1",
        "ms_token": "ms-token-1",
        "webid": "webid-1",
        "sign_base_url": "http://127.0.0.1:8000",
        "timeout_seconds": 5,
    }


def proxy_material() -> dict[str, Any]:
    return {"proxy_endpoint": "http://proxy-001"}


def managed_account_material(material: dict[str, Any], *, adapter_key: str) -> dict[str, Any]:
    return {**material, MANAGED_ACCOUNT_ADAPTER_KEY_FIELD: adapter_key}


def baseline_resource_requirement_declarations(
    *,
    adapter_key: str,
    capability: str = "content_detail",
) -> tuple[object, ...]:
    return (
        baseline_multi_profile_resource_requirement_declaration(
            adapter_key=adapter_key,
            capability=capability,
        ),
    )


def build_managed_resource_bundle(
    *,
    adapter_key: str,
    task_id: str,
    capability: str = "content_detail_by_url",
    requested_slots: tuple[str, ...] = ("account", "proxy"),
    account_material: dict[str, Any] | None = None,
    proxy_slot_material: dict[str, Any] | None = None,
    bundle_id: str = "bundle-test-001",
    lease_id: str = "lease-test-001",
) -> ResourceBundle:
    include_account = "account" in requested_slots
    include_proxy = "proxy" in requested_slots
    return ResourceBundle(
        bundle_id=bundle_id,
        lease_id=lease_id,
        task_id=task_id,
        adapter_key=adapter_key,
        capability=capability,
        requested_slots=requested_slots,
        acquired_at="2026-04-21T04:30:00.000000Z",
        account=(
            ResourceRecord(
                resource_id="account-bundle-001",
                resource_type="account",
                status="IN_USE",
                material=managed_account_material(account_material or generic_account_material(), adapter_key=adapter_key),
            )
            if include_account
            else None
        ),
        proxy=(
            ResourceRecord(
                resource_id="proxy-bundle-001",
                resource_type="proxy",
                status="IN_USE",
                material=proxy_slot_material or proxy_material(),
            )
            if include_proxy
            else None
        ),
    )


def seed_default_runtime_resources(
    *,
    adapter_key: str = "stub",
    account_resource_id: str = "account-001",
    proxy_resource_id: str = "proxy-001",
    account_material: dict[str, Any] | None = None,
    proxy_slot_material: dict[str, Any] | None = None,
) -> None:
    store = default_resource_lifecycle_store()
    store.seed_resources(
        [
            ResourceRecord(
                resource_id=account_resource_id,
                resource_type="account",
                status="AVAILABLE",
                material=managed_account_material(account_material or generic_account_material(), adapter_key=adapter_key),
            ),
            ResourceRecord(
                resource_id=proxy_resource_id,
                resource_type="proxy",
                status="AVAILABLE",
                material=proxy_slot_material or proxy_material(),
            ),
        ]
    )


class ResourceStoreEnvMixin:
    resource_store_adapter_key = "xhs"

    def setUp(self) -> None:
        super().setUp()
        self._resource_store_dir = tempfile.TemporaryDirectory()
        self._resource_store_path = os.path.join(self._resource_store_dir.name, "resource-lifecycle.json")
        self._resource_trace_store_path = os.path.join(self._resource_store_dir.name, "resource-trace-events.jsonl")
        self._resource_store_patcher = mock.patch.dict(
            os.environ,
            {
                "SYVERT_RESOURCE_LIFECYCLE_STORE_FILE": self._resource_store_path,
                "SYVERT_RESOURCE_TRACE_STORE_FILE": self._resource_trace_store_path,
            },
            clear=False,
        )
        self._resource_store_patcher.start()
        seed_default_runtime_resources(adapter_key=self.resource_store_adapter_key)

    def tearDown(self) -> None:
        self._resource_store_patcher.stop()
        self._resource_store_dir.cleanup()
        super().tearDown()

    def make_trace_store(self):
        return default_resource_trace_store()
