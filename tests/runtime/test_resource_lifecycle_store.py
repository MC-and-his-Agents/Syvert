from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from syvert.resource_lifecycle import (
    MANAGED_ACCOUNT_ADAPTER_KEY_FIELD,
    AcquireRequest,
    ReleaseRequest,
    ResourceBundle,
    ResourceLifecycleContractError,
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
        return TaggedAccountStore(default_resource_lifecycle_store())


class TaggedAccountStore:
    def __init__(self, inner_store, *, default_adapter_key: str = "xhs") -> None:
        self._inner_store = inner_store
        self._default_adapter_key = default_adapter_key

    def load_snapshot(self):
        return self._inner_store.load_snapshot()

    def write_snapshot(self, snapshot):
        return self._inner_store.write_snapshot(snapshot)

    def seed_resources(self, records: Sequence[ResourceRecord]):
        if not isinstance(records, Sequence):
            return self._inner_store.seed_resources(records)
        return self._inner_store.seed_resources(_tag_default_accounts(records, adapter_key=self._default_adapter_key))


def _tag_default_accounts(
    records: Sequence[ResourceRecord],
    *,
    adapter_key: str,
) -> list[ResourceRecord]:
    tagged: list[ResourceRecord] = []
    for record in records:
        material = record.material
        if record.resource_type != "account" or not isinstance(material, Mapping):
            tagged.append(record)
            continue
        if MANAGED_ACCOUNT_ADAPTER_KEY_FIELD in material:
            tagged.append(record)
            continue
        tagged.append(
            ResourceRecord(
                resource_id=record.resource_id,
                resource_type=record.resource_type,
                status=record.status,
                material={**dict(material), MANAGED_ACCOUNT_ADAPTER_KEY_FIELD: adapter_key},
            )
        )
    return tagged


class ResourceLifecycleStoreTests(ResourceStoreEnvMixin, unittest.TestCase):
    def test_seed_resources_rejects_non_sequence_input(self) -> None:
        with self.assertRaises(ResourceLifecycleContractError):
            self.make_store().seed_resources(None)  # type: ignore[arg-type]

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

    def test_acquire_persists_active_lease_without_null_release_fields(self) -> None:
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

        bundle = acquire(
            AcquireRequest(
                task_id="task-active-shape",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            store,
            "task-context-active-shape",
        )

        assert isinstance(bundle, ResourceBundle)
        payload = json.loads(Path(self._resource_store_path).read_text(encoding="utf-8"))
        lease_payload = payload["leases"][0]

        self.assertNotIn("released_at", lease_payload)
        self.assertNotIn("target_status_after_release", lease_payload)
        self.assertNotIn("release_reason", lease_payload)

    def test_load_snapshot_rejects_active_lease_with_null_release_fields(self) -> None:
        Path(self._resource_store_path).write_text(
            json.dumps(
                {
                    "schema_version": "v0.4.0",
                    "revision": 1,
                    "resources": [
                        {
                            "resource_id": "account-001",
                            "resource_type": "account",
                            "status": "IN_USE",
                            "material": {"provider_account_id": "pa-001"},
                        }
                    ],
                    "leases": [
                        {
                            "lease_id": "lease-001",
                            "bundle_id": "bundle-001",
                            "task_id": "task-001",
                            "adapter_key": "xhs",
                            "capability": "content_detail_by_url",
                            "resource_ids": ["account-001"],
                            "acquired_at": "2026-04-20T11:00:00.000000Z",
                            "released_at": None,
                            "target_status_after_release": None,
                            "release_reason": None,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        with self.assertRaises(ResourceLifecyclePersistenceError):
            self.make_store().load_snapshot()

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

    def test_write_snapshot_rejects_invalid_resource_element_shape(self) -> None:
        invalid_snapshot = ResourceLifecycleSnapshot(
            schema_version="v0.4.0",
            revision=1,
            resources=("not-a-record",),  # type: ignore[arg-type]
            leases=(),
        )

        with self.assertRaises(ResourceLifecyclePersistenceError):
            self.make_store().write_snapshot(invalid_snapshot)

    def test_write_snapshot_serializes_concurrent_same_base_revision(self) -> None:
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
        candidate_a = ResourceLifecycleSnapshot(
            schema_version=base_snapshot.schema_version,
            revision=base_snapshot.revision + 1,
            resources=(
                ResourceRecord(
                    resource_id="account-001",
                    resource_type="account",
                    status="AVAILABLE",
                    material={"provider_account_id": "pa-001", "marker": "a"},
                ),
            ),
            leases=base_snapshot.leases,
        )
        candidate_b = ResourceLifecycleSnapshot(
            schema_version=base_snapshot.schema_version,
            revision=base_snapshot.revision + 1,
            resources=(
                ResourceRecord(
                    resource_id="account-001",
                    resource_type="account",
                    status="AVAILABLE",
                    material={"provider_account_id": "pa-001", "marker": "b"},
                ),
            ),
            leases=base_snapshot.leases,
        )

        barrier = threading.Barrier(2)
        results: list[str] = []
        errors: list[str] = []

        def writer(snapshot: ResourceLifecycleSnapshot, label: str) -> None:
            barrier.wait()
            try:
                store.write_snapshot(snapshot)
                results.append(label)
            except ResourceLifecyclePersistenceError as error:
                errors.append(str(error))

        thread_a = threading.Thread(target=writer, args=(candidate_a, "a"))
        thread_b = threading.Thread(target=writer, args=(candidate_b, "b"))
        thread_a.start()
        thread_b.start()
        thread_a.join()
        thread_b.join()

        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 1)
        self.assertIn("resource_state_conflict", errors[0])
        reloaded = store.load_snapshot()
        marker = reloaded.resources[0].material["marker"]
        self.assertIn(marker, {"a", "b"})

    def test_seed_resources_cannot_resurrect_invalid_resource(self) -> None:
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
        bundle = acquire(
            AcquireRequest(
                task_id="task-invalid",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            store,
            "task-context-invalid",
        )
        assert isinstance(bundle, ResourceBundle)
        release(
            ReleaseRequest(
                lease_id=bundle.lease_id,
                task_id="task-invalid",
                target_status_after_release="INVALID",
                reason="burned",
            ),
            store,
            "task-context-invalid",
        )

        with self.assertRaises(ResourceLifecyclePersistenceError):
            store.seed_resources(
                [
                    ResourceRecord(
                        resource_id="account-001",
                        resource_type="account",
                        status="AVAILABLE",
                        material={"provider_account_id": "pa-001", "marker": "revived"},
                    )
                ]
            )

    def test_seed_resources_cannot_overwrite_existing_resource_truth(self) -> None:
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

        with self.assertRaises(ResourceLifecyclePersistenceError):
            store.seed_resources(
                [
                    ResourceRecord(
                        resource_id="account-001",
                        resource_type="account",
                        status="INVALID",
                        material={"provider_account_id": "pa-001"},
                    )
                ]
            )

    def test_seed_resources_allows_active_truth_replay(self) -> None:
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
        bundle = acquire(
            AcquireRequest(
                task_id="task-active-replay",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            store,
            "task-context-active-replay",
        )
        assert isinstance(bundle, ResourceBundle)
        active_snapshot = store.load_snapshot()
        active_record = active_snapshot.resources[0]

        replayed = store.seed_resources([active_record])
        replayed_snapshot = store.load_snapshot()

        self.assertEqual(len(replayed), 1)
        self.assertEqual(replayed[0], active_record)
        self.assertEqual(replayed_snapshot.revision, active_snapshot.revision)
        self.assertEqual(replayed_snapshot.resources, active_snapshot.resources)

    def test_seed_resources_replay_is_idempotent_for_json_equivalent_material(self) -> None:
        store = self.make_store()
        original = ResourceRecord(
            resource_id="account-001",
            resource_type="account",
            status="AVAILABLE",
            material={"vals": ("a", "b")},
        )

        seeded = store.seed_resources([original])
        replayed = store.seed_resources([original])
        snapshot = store.load_snapshot()

        self.assertEqual(len(seeded), 1)
        self.assertEqual(len(replayed), 1)
        self.assertEqual(snapshot.revision, 1)
        self.assertEqual(snapshot.resources[0].material, {"managed_adapter_key": "xhs", "vals": ["a", "b"]})

    def test_seed_resources_merges_disjoint_concurrent_inserts(self) -> None:
        store = self.make_store()
        barrier = threading.Barrier(2)
        errors: list[str] = []

        def seeder(record: ResourceRecord) -> None:
            barrier.wait()
            try:
                store.seed_resources([record])
            except ResourceLifecyclePersistenceError as error:
                errors.append(str(error))

        thread_a = threading.Thread(
            target=seeder,
            args=(
                ResourceRecord(
                    resource_id="account-001",
                    resource_type="account",
                    status="AVAILABLE",
                    material={"provider_account_id": "pa-001"},
                ),
            ),
        )
        thread_b = threading.Thread(
            target=seeder,
            args=(
                ResourceRecord(
                    resource_id="proxy-001",
                    resource_type="proxy",
                    status="AVAILABLE",
                    material={"proxy_endpoint": "http://proxy-001"},
                ),
            ),
        )
        thread_a.start()
        thread_b.start()
        thread_a.join()
        thread_b.join()

        self.assertEqual(errors, [])
        snapshot = store.load_snapshot()
        self.assertEqual({record.resource_id for record in snapshot.resources}, {"account-001", "proxy-001"})

    def test_load_snapshot_rejects_invalid_utf8_bytes(self) -> None:
        Path(self._resource_store_path).write_bytes(b"\xff\xfe")

        with self.assertRaises(ResourceLifecyclePersistenceError):
            self.make_store().load_snapshot()

    def test_load_snapshot_rejects_invalid_resource_resurrection(self) -> None:
        Path(self._resource_store_path).write_text(
            json.dumps(
                {
                    "schema_version": "v0.4.0",
                    "revision": 1,
                    "resources": [
                        {
                            "resource_id": "account-001",
                            "resource_type": "account",
                            "status": "AVAILABLE",
                            "material": {"provider_account_id": "pa-001"},
                        }
                    ],
                    "leases": [
                        {
                            "lease_id": "lease-invalid",
                            "bundle_id": "bundle-invalid",
                            "task_id": "task-invalid",
                            "adapter_key": "xhs",
                            "capability": "content_detail_by_url",
                            "resource_ids": ["account-001"],
                            "acquired_at": "2026-04-20T00:00:00Z",
                            "released_at": "2026-04-20T00:01:00Z",
                            "target_status_after_release": "INVALID",
                            "release_reason": "burned",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        with self.assertRaises(ResourceLifecyclePersistenceError):
            self.make_store().load_snapshot()

    def test_load_snapshot_rejects_invalid_material_payload(self) -> None:
        Path(self._resource_store_path).write_text(
            """
            {
              "schema_version": "v0.4.0",
              "revision": 1,
              "resources": [
                {
                  "resource_id": "account-001",
                  "resource_type": "account",
                  "status": "AVAILABLE",
                  "material": {"provider_account_id": NaN}
                }
              ],
              "leases": []
            }
            """,
            encoding="utf-8",
        )

        with self.assertRaises(ResourceLifecyclePersistenceError):
            self.make_store().load_snapshot()

    def test_load_snapshot_rejects_released_at_before_acquired_at(self) -> None:
        Path(self._resource_store_path).write_text(
            json.dumps(
                {
                    "schema_version": "v0.4.0",
                    "revision": 1,
                    "resources": [
                        {
                            "resource_id": "account-001",
                            "resource_type": "account",
                            "status": "AVAILABLE",
                            "material": {"provider_account_id": "pa-001"},
                        }
                    ],
                    "leases": [
                        {
                            "lease_id": "lease-invalid-order",
                            "bundle_id": "bundle-invalid-order",
                            "task_id": "task-invalid-order",
                            "adapter_key": "xhs",
                            "capability": "content_detail_by_url",
                            "resource_ids": ["account-001"],
                            "acquired_at": "2026-04-20T00:01:00Z",
                            "released_at": "2026-04-20T00:00:00Z",
                            "target_status_after_release": "AVAILABLE",
                            "release_reason": "normal",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        with self.assertRaises(ResourceLifecyclePersistenceError):
            self.make_store().load_snapshot()

    def test_load_snapshot_rejects_overlapping_resource_leases(self) -> None:
        Path(self._resource_store_path).write_text(
            json.dumps(
                {
                    "schema_version": "v0.4.0",
                    "revision": 2,
                    "resources": [
                        {
                            "resource_id": "account-001",
                            "resource_type": "account",
                            "status": "AVAILABLE",
                            "material": {"provider_account_id": "pa-001"},
                        }
                    ],
                    "leases": [
                        {
                            "lease_id": "lease-a",
                            "bundle_id": "bundle-a",
                            "task_id": "task-a",
                            "adapter_key": "xhs",
                            "capability": "content_detail_by_url",
                            "resource_ids": ["account-001"],
                            "acquired_at": "2026-04-20T00:00:00Z",
                            "released_at": "2026-04-20T00:02:00Z",
                            "target_status_after_release": "AVAILABLE",
                            "release_reason": "normal",
                        },
                        {
                            "lease_id": "lease-b",
                            "bundle_id": "bundle-b",
                            "task_id": "task-b",
                            "adapter_key": "xhs",
                            "capability": "content_detail_by_url",
                            "resource_ids": ["account-001"],
                            "acquired_at": "2026-04-20T00:01:00Z",
                            "released_at": "2026-04-20T00:03:00Z",
                            "target_status_after_release": "AVAILABLE",
                            "release_reason": "normal",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

        with self.assertRaises(ResourceLifecyclePersistenceError):
            self.make_store().load_snapshot()

    def test_load_snapshot_rejects_mixed_precision_reacquire_after_invalid(self) -> None:
        Path(self._resource_store_path).write_text(
            json.dumps(
                {
                    "schema_version": "v0.4.0",
                    "revision": 2,
                    "resources": [
                        {
                            "resource_id": "account-001",
                            "resource_type": "account",
                            "status": "AVAILABLE",
                            "material": {"provider_account_id": "pa-001"},
                        }
                    ],
                    "leases": [
                        {
                            "lease_id": "lease-invalid",
                            "bundle_id": "bundle-invalid",
                            "task_id": "task-invalid",
                            "adapter_key": "xhs",
                            "capability": "content_detail_by_url",
                            "resource_ids": ["account-001"],
                            "acquired_at": "2026-04-20T00:00:00Z",
                            "released_at": "2026-04-20T00:00:00Z",
                            "target_status_after_release": "INVALID",
                            "release_reason": "burned",
                        },
                        {
                            "lease_id": "lease-reacquire",
                            "bundle_id": "bundle-reacquire",
                            "task_id": "task-reacquire",
                            "adapter_key": "xhs",
                            "capability": "content_detail_by_url",
                            "resource_ids": ["account-001"],
                            "acquired_at": "2026-04-20T00:00:00.000001Z",
                            "released_at": "2026-04-20T00:00:01Z",
                            "target_status_after_release": "AVAILABLE",
                            "release_reason": "normal",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

        with self.assertRaises(ResourceLifecyclePersistenceError):
            self.make_store().load_snapshot()


if __name__ == "__main__":
    unittest.main()
