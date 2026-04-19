from __future__ import annotations

import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from syvert.resource_lifecycle import (
    AcquireRequest,
    ReleaseRequest,
    ResourceBundle,
    ResourceLease,
    ResourceRecord,
    acquire,
    release,
)
from syvert.resource_lifecycle_store import default_resource_lifecycle_store


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


class ResourceLifecycleTests(ResourceStoreEnvMixin, unittest.TestCase):
    def seed_default_resources(self) -> None:
        self.make_store().seed_resources(
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

    def test_acquire_succeeds_for_exact_requested_slots(self) -> None:
        self.seed_default_resources()

        result = acquire(
            AcquireRequest(
                task_id="task-001",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account", "proxy"),
            ),
            self.make_store(),
            "task-context-001",
        )

        self.assertIsInstance(result, ResourceBundle)
        assert isinstance(result, ResourceBundle)
        self.assertEqual(result.requested_slots, ("account", "proxy"))
        self.assertIsNotNone(result.account)
        self.assertIsNotNone(result.proxy)
        assert result.account is not None
        assert result.proxy is not None
        self.assertEqual(result.account.status, "IN_USE")
        self.assertEqual(result.proxy.status, "IN_USE")

    def test_acquire_fails_closed_when_any_slot_is_missing(self) -> None:
        self.make_store().seed_resources(
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
            self.make_store(),
            "task-context-002",
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["category"], "runtime_contract")
        self.assertEqual(result["error"]["code"], "resource_unavailable")
        snapshot = self.make_store().load_snapshot()
        self.assertEqual(snapshot.leases, ())
        self.assertEqual(snapshot.resources[0].status, "AVAILABLE")

    def test_acquire_rejects_duplicate_slots(self) -> None:
        self.seed_default_resources()

        result = acquire(
            AcquireRequest(
                task_id="task-003",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account", "account"),
            ),
            self.make_store(),
            "task-context-003",
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["category"], "invalid_input")
        self.assertEqual(result["error"]["code"], "invalid_resource_request")

    def test_acquire_rejects_unknown_slot(self) -> None:
        self.seed_default_resources()

        result = acquire(
            {
                "task_id": "task-004",
                "adapter_key": "xhs",
                "capability": "content_detail_by_url",
                "requested_slots": ["browser"],
            },
            self.make_store(),
            "task-context-004",
        )

        self.assertEqual(result["error"]["code"], "invalid_resource_request")

    def test_acquire_rejects_invalid_resource_reuse(self) -> None:
        self.make_store().seed_resources(
            [
                ResourceRecord(
                    resource_id="account-001",
                    resource_type="account",
                    status="INVALID",
                    material={"provider_account_id": "pa-001"},
                )
            ]
        )

        result = acquire(
            AcquireRequest(
                task_id="task-005",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-context-005",
        )

        self.assertEqual(result["error"]["code"], "resource_unavailable")

    def test_release_returns_resources_to_available(self) -> None:
        self.seed_default_resources()
        bundle = acquire(
            AcquireRequest(
                task_id="task-006",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account", "proxy"),
            ),
            self.make_store(),
            "task-context-006",
        )
        assert isinstance(bundle, ResourceBundle)

        result = release(
            ReleaseRequest(
                lease_id=bundle.lease_id,
                task_id="task-006",
                target_status_after_release="AVAILABLE",
                reason="normal",
            ),
            self.make_store(),
            "task-context-006",
        )

        self.assertIsInstance(result, ResourceLease)
        assert isinstance(result, ResourceLease)
        self.assertEqual(result.target_status_after_release, "AVAILABLE")
        snapshot = self.make_store().load_snapshot()
        self.assertEqual({record.status for record in snapshot.resources}, {"AVAILABLE"})

    def test_release_can_invalidate_resources(self) -> None:
        self.seed_default_resources()
        bundle = acquire(
            AcquireRequest(
                task_id="task-007",
                adapter_key="douyin",
                capability="content_detail_by_url",
                requested_slots=("proxy",),
            ),
            self.make_store(),
            "task-context-007",
        )
        assert isinstance(bundle, ResourceBundle)

        result = release(
            ReleaseRequest(
                lease_id=bundle.lease_id,
                task_id="task-007",
                target_status_after_release="INVALID",
                reason="network-broken",
            ),
            self.make_store(),
            "task-context-007",
        )

        self.assertIsInstance(result, ResourceLease)
        snapshot = self.make_store().load_snapshot()
        proxy = next(record for record in snapshot.resources if record.resource_type == "proxy")
        self.assertEqual(proxy.status, "INVALID")

    def test_release_is_idempotent_for_same_semantics(self) -> None:
        self.seed_default_resources()
        bundle = acquire(
            AcquireRequest(
                task_id="task-008",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-context-008",
        )
        assert isinstance(bundle, ResourceBundle)
        first = release(
            ReleaseRequest(
                lease_id=bundle.lease_id,
                task_id="task-008",
                target_status_after_release="AVAILABLE",
                reason="normal",
            ),
            self.make_store(),
            "task-context-008",
        )
        second = release(
            ReleaseRequest(
                lease_id=bundle.lease_id,
                task_id="task-008",
                target_status_after_release="AVAILABLE",
                reason="normal",
            ),
            self.make_store(),
            "task-context-008",
        )

        self.assertEqual(first, second)

    def test_release_rejects_conflicting_repeat(self) -> None:
        self.seed_default_resources()
        bundle = acquire(
            AcquireRequest(
                task_id="task-009",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-context-009",
        )
        assert isinstance(bundle, ResourceBundle)
        release(
            ReleaseRequest(
                lease_id=bundle.lease_id,
                task_id="task-009",
                target_status_after_release="AVAILABLE",
                reason="normal",
            ),
            self.make_store(),
            "task-context-009",
        )

        result = release(
            ReleaseRequest(
                lease_id=bundle.lease_id,
                task_id="task-009",
                target_status_after_release="INVALID",
                reason="late-conflict",
            ),
            self.make_store(),
            "task-context-009",
        )

        self.assertEqual(result["error"]["code"], "resource_release_conflict")

    def test_release_rejects_lease_task_mismatch(self) -> None:
        self.seed_default_resources()
        bundle = acquire(
            AcquireRequest(
                task_id="task-010",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-context-010",
        )
        assert isinstance(bundle, ResourceBundle)

        result = release(
            ReleaseRequest(
                lease_id=bundle.lease_id,
                task_id="task-other",
                target_status_after_release="AVAILABLE",
                reason="normal",
            ),
            self.make_store(),
            "task-context-010",
        )

        self.assertEqual(result["error"]["code"], "resource_lease_mismatch")
        self.assertEqual(result["adapter_key"], "xhs")
        self.assertEqual(result["capability"], "content_detail_by_url")

    def test_acquire_rejects_resource_already_in_use(self) -> None:
        self.seed_default_resources()
        first = acquire(
            AcquireRequest(
                task_id="task-010b",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-context-010b",
        )
        assert isinstance(first, ResourceBundle)

        second = acquire(
            AcquireRequest(
                task_id="task-010c",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-context-010c",
        )

        self.assertEqual(second["error"]["code"], "resource_unavailable")

    def test_release_rejects_invalid_target_status(self) -> None:
        self.seed_default_resources()
        bundle = acquire(
            AcquireRequest(
                task_id="task-010d",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-context-010d",
        )
        assert isinstance(bundle, ResourceBundle)

        result = release(
            {
                "lease_id": bundle.lease_id,
                "task_id": "task-010d",
                "target_status_after_release": "IN_USE",
                "reason": "invalid-target",
            },
            self.make_store(),
            "task-context-010d",
        )

        self.assertEqual(result["error"]["code"], "invalid_resource_release")
        self.assertEqual(result["error"]["category"], "invalid_input")

    def test_release_invalid_non_string_fields_map_to_invalid_resource_release(self) -> None:
        self.seed_default_resources()

        result = release(
            {
                "lease_id": 123,
                "task_id": "task-010e",
                "target_status_after_release": "AVAILABLE",
                "reason": "normal",
            },
            self.make_store(),
            "task-context-010e",
        )

        self.assertEqual(result["error"]["category"], "invalid_input")
        self.assertEqual(result["error"]["code"], "invalid_resource_release")

    def test_acquire_failure_backfills_task_id_from_context(self) -> None:
        self.seed_default_resources()

        result = acquire(
            {
                "task_id": "",
                "adapter_key": 123,
                "capability": None,
                "requested_slots": [],
            },
            self.make_store(),
            "task-context-011",
        )

        self.assertEqual(result["task_id"], "task-context-011")
        self.assertEqual(result["adapter_key"], "")
        self.assertEqual(result["capability"], "")
        self.assertEqual(result["error"]["code"], "invalid_resource_request")

    def test_release_failure_backfills_from_lease_context(self) -> None:
        self.seed_default_resources()
        bundle = acquire(
            AcquireRequest(
                task_id="task-012",
                adapter_key="douyin",
                capability="content_detail_by_url",
                requested_slots=("proxy",),
            ),
            self.make_store(),
            "task-context-012",
        )
        assert isinstance(bundle, ResourceBundle)

        result = release(
            {
                "lease_id": bundle.lease_id,
                "task_id": "",
                "target_status_after_release": "",
                "reason": "",
            },
            self.make_store(),
            "task-context-012",
        )

        self.assertEqual(result["task_id"], "task-context-012")
        self.assertEqual(result["adapter_key"], "douyin")
        self.assertEqual(result["capability"], "content_detail_by_url")
        self.assertEqual(result["error"]["code"], "invalid_resource_release")

    def test_release_is_idempotent_under_concurrent_same_semantics(self) -> None:
        class ConcurrentReleaseStore:
            def __init__(self, inner_store):
                self._inner_store = inner_store
                self._barrier = threading.Barrier(2)

            def load_snapshot(self):
                return self._inner_store.load_snapshot()

            def seed_resources(self, records):
                return self._inner_store.seed_resources(records)

            def write_snapshot(self, snapshot):
                if snapshot.revision == 3:
                    self._barrier.wait()
                return self._inner_store.write_snapshot(snapshot)

        store = ConcurrentReleaseStore(self.make_store())
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
                task_id="task-015",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            store,
            "task-context-015",
        )
        assert isinstance(bundle, ResourceBundle)

        results = []

        def worker() -> None:
            results.append(
                release(
                    ReleaseRequest(
                        lease_id=bundle.lease_id,
                        task_id="task-015",
                        target_status_after_release="AVAILABLE",
                        reason="normal",
                    ),
                    store,
                    "task-context-015",
                )
            )

        thread_a = threading.Thread(target=worker)
        thread_b = threading.Thread(target=worker)
        thread_a.start()
        thread_b.start()
        thread_a.join()
        thread_b.join()

        self.assertEqual(len(results), 2)
        self.assertTrue(all(isinstance(result, ResourceLease) for result in results))
        first, second = results
        assert isinstance(first, ResourceLease)
        assert isinstance(second, ResourceLease)
        self.assertEqual(first, second)

    def test_seed_resources_rejects_in_use_without_active_lease(self) -> None:
        with self.assertRaisesRegex(Exception, "IN_USE 资源必须由唯一 active lease 持有"):
            self.make_store().seed_resources(
                [
                    ResourceRecord(
                        resource_id="account-in-use",
                        resource_type="account",
                        status="IN_USE",
                        material={"provider_account_id": "pa-in-use"},
                    )
                ]
            )

    def test_acquire_returns_failed_envelope_for_corrupt_snapshot(self) -> None:
        Path(self._resource_store_path).write_text("{not-json", encoding="utf-8")

        result = acquire(
            AcquireRequest(
                task_id="task-013",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-context-013",
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["code"], "resource_state_conflict")

    def test_release_returns_failed_envelope_for_corrupt_snapshot(self) -> None:
        Path(self._resource_store_path).write_text("{not-json", encoding="utf-8")

        result = release(
            ReleaseRequest(
                lease_id="lease-missing",
                task_id="task-014",
                target_status_after_release="AVAILABLE",
                reason="normal",
            ),
            self.make_store(),
            "task-context-014",
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["code"], "resource_state_conflict")


if __name__ == "__main__":
    unittest.main()
