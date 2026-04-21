from __future__ import annotations

import os
import tempfile
from typing import Any
from unittest import mock

from syvert.resource_lifecycle import ResourceBundle, ResourceRecord
from syvert.resource_lifecycle_store import default_resource_lifecycle_store


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
                material=account_material or generic_account_material(),
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
    account_material: dict[str, Any] | None = None,
    proxy_slot_material: dict[str, Any] | None = None,
) -> None:
    store = default_resource_lifecycle_store()
    store.seed_resources(
        [
            ResourceRecord(
                resource_id="account-001",
                resource_type="account",
                status="AVAILABLE",
                material=account_material or generic_account_material(),
            ),
            ResourceRecord(
                resource_id="proxy-001",
                resource_type="proxy",
                status="AVAILABLE",
                material=proxy_slot_material or proxy_material(),
            ),
        ]
    )


class ResourceStoreEnvMixin:
    def setUp(self) -> None:
        super().setUp()
        self._resource_store_dir = tempfile.TemporaryDirectory()
        self._resource_store_path = os.path.join(self._resource_store_dir.name, "resource-lifecycle.json")
        self._resource_store_patcher = mock.patch.dict(
            os.environ,
            {"SYVERT_RESOURCE_LIFECYCLE_STORE_FILE": self._resource_store_path},
            clear=False,
        )
        self._resource_store_patcher.start()
        seed_default_runtime_resources()

    def tearDown(self) -> None:
        self._resource_store_patcher.stop()
        self._resource_store_dir.cleanup()
        super().tearDown()
