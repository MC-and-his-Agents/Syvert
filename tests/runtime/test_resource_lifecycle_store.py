from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from syvert.resource_lifecycle import (
    AcquireRequest,
    ReleaseRequest,
    ResourceBundle,
    ResourceLifecycleSnapshot,
    ResourceRecord,
    acquire,
    release,
)
from syvert.resource_lifecycle_store import ResourceLifecyclePersistenceError, default_resource_lifecycle_store


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

    def tearDown(self) -> None:
        self._resource_store_patcher.stop()
        self._resource_store_dir.cleanup()
        super().tearDown()

    def make_store(self):
        return default_resource_lifecycle_store()


class ResourceLifecycleStoreTests(ResourceStoreEnvMixin, unittest.TestCase):
    def test_seed_resources_persists_atomic_snapshot(self) -> None:
        store = self.make_store()

        seeded = store.seed_resources(
            [
                ResourceRecord(
                    resource_id="account-001",
                    resource_type="account",
                    status="AVAILABLE",
                    material={"provider_account_id": "pa-001"},
                )
            ]
        )

        self.assertEqual(len(seeded), 1)
        payload = json.loads(Path(self._resource_store_path).read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "v0.4.0")
        self.assertEqual(payload["revision"], 1)
        self.assertEqual(payload["resources"][0]["resource_id"], "account-001")
        self.assertEqual(payload["leases"], [])

    def test_round_trip_loads_written_snapshot(self) -> None:
        store = self.make_store()
        store.seed_resources(
            [
                ResourceRecord(
                    resource_id="account-001",
                    resource_type="account",
                    status="AVAILABLE",
                    material={"provider_account_id": "pa-001"},
                ),
                ResourceRecord(
                    resource_id="proxy-001",
                    resource_type="proxy",
                    status="AVAILABLE",
                    material={"proxy_endpoint": "http://proxy-001"},
                ),
            ]
        )
        bundle = acquire(
            AcquireRequest(
                task_id="task-001",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account", "proxy"),
            ),
            store,
            "task-context-001",
        )
        assert isinstance(bundle, ResourceBundle)
        release(
            ReleaseRequest(
                lease_id=bundle.lease_id,
                task_id="task-001",
                target_status_after_release="AVAILABLE",
                reason="normal",
            ),
            store,
            "task-context-001",
        )

        reloaded = store.load_snapshot()

        self.assertEqual(len(reloaded.resources), 2)
        self.assertEqual(len(reloaded.leases), 1)
        self.assertEqual(reloaded.leases[0].released_at is not None, True)
        self.assertEqual(reloaded.revision, 3)

    def test_failed_acquire_does_not_leave_half_written_truth(self) -> None:
        store = self.make_store()
        store.seed_resources(
            [
                ResourceRecord(
                    resource_id="account-001",
                    resource_type="account",
                    status="AVAILABLE",
                    material={"provider_account_id": "pa-001"},
                )
            ]
        )

        result = acquire(
            AcquireRequest(
                task_id="task-002",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account", "proxy"),
            ),
            store,
            "task-context-002",
        )

        self.assertEqual(result["error"]["code"], "resource_unavailable")
        reloaded = store.load_snapshot()
        self.assertEqual(len(reloaded.leases), 0)
        self.assertEqual(reloaded.resources[0].status, "AVAILABLE")

    def test_write_snapshot_rejects_stale_revision(self) -> None:
        store = self.make_store()
        store.seed_resources(
            [
                ResourceRecord(
                    resource_id="account-001",
                    resource_type="account",
                    status="AVAILABLE",
                    material={"provider_account_id": "pa-001"},
                )
            ]
        )
        base_snapshot = store.load_snapshot()
        first_update = ResourceLifecycleSnapshot(
            schema_version=base_snapshot.schema_version,
            revision=base_snapshot.revision + 1,
            resources=(
                ResourceRecord(
                    resource_id="account-001",
                    resource_type="account",
                    status="AVAILABLE",
                    material={"provider_account_id": "pa-001", "marker": "first"},
                ),
            ),
            leases=base_snapshot.leases,
        )
        store.write_snapshot(first_update)

        stale_update = ResourceLifecycleSnapshot(
            schema_version=base_snapshot.schema_version,
            revision=base_snapshot.revision + 1,
            resources=(
                ResourceRecord(
                    resource_id="account-001",
                    resource_type="account",
                    status="AVAILABLE",
                    material={"provider_account_id": "pa-001", "marker": "stale"},
                ),
            ),
            leases=base_snapshot.leases,
        )

        with self.assertRaises(ResourceLifecyclePersistenceError):
            store.write_snapshot(stale_update)


if __name__ == "__main__":
    unittest.main()
