from __future__ import annotations

import fcntl
import json
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
    ResourceLifecycleSnapshot,
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

    def test_concurrent_acquire_fails_closed_after_stale_selection_conflict(self) -> None:
        class ConcurrentAcquireStore:
            def __init__(self, inner_store):
                self._inner_store = inner_store
                self._barrier = threading.Barrier(2)

            def load_snapshot(self):
                return self._inner_store.load_snapshot()

            def seed_resources(self, records):
                return self._inner_store.seed_resources(records)

            def write_snapshot(self, snapshot):
                if snapshot.revision == 2:
                    self._barrier.wait()
                return self._inner_store.write_snapshot(snapshot)

        store = ConcurrentAcquireStore(self.make_store())
        store.seed_resources(
            [
                ResourceRecord(
                    resource_id="account-001",
                    resource_type="account",
                    status="AVAILABLE",
                    material={"provider_account_id": "pa-001"},
                ),
                ResourceRecord(
                    resource_id="account-002",
                    resource_type="account",
                    status="AVAILABLE",
                    material={"provider_account_id": "pa-002"},
                ),
            ]
        )

        results = []

        def worker(task_id: str) -> None:
            results.append(
                acquire(
                    AcquireRequest(
                        task_id=task_id,
                        adapter_key="xhs",
                        capability="content_detail_by_url",
                        requested_slots=("account",),
                    ),
                    store,
                    f"task-context-{task_id}",
                )
            )

        thread_a = threading.Thread(target=worker, args=("task-001a",))
        thread_b = threading.Thread(target=worker, args=("task-001b",))
        thread_a.start()
        thread_b.start()
        thread_a.join()
        thread_b.join()

        self.assertEqual(len(results), 2)
        successes = [result for result in results if isinstance(result, ResourceBundle)]
        failures = [result for result in results if isinstance(result, dict)]
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["error"]["code"], "resource_state_conflict")
        snapshot = self.make_store().load_snapshot()
        statuses = {record.resource_id: record.status for record in snapshot.resources}
        self.assertEqual(statuses["account-001"], "IN_USE")
        self.assertEqual(statuses["account-002"], "AVAILABLE")

    def test_acquire_retries_when_unrelated_write_advances_revision_without_changing_selection(self) -> None:
        class ConcurrentAcquireRetryStore:
            def __init__(self, inner_store):
                self._inner_store = inner_store
                self._injected = False

            def load_snapshot(self):
                return self._inner_store.load_snapshot()

            def seed_resources(self, records):
                return self._inner_store.seed_resources(records)

            def write_snapshot(self, snapshot):
                if snapshot.revision == 2 and not self._injected:
                    self._injected = True
                    self._inner_store.seed_resources(
                        [
                            ResourceRecord(
                                resource_id="proxy-001",
                                resource_type="proxy",
                                status="AVAILABLE",
                                material={"proxy_endpoint": "http://proxy-001"},
                            )
                        ]
                    )
                return self._inner_store.write_snapshot(snapshot)

        store = ConcurrentAcquireRetryStore(self.make_store())
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
                task_id="task-001c",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            store,
            "task-context-001c",
        )

        self.assertIsInstance(result, ResourceBundle)
        assert isinstance(result, ResourceBundle)
        assert result.account is not None
        self.assertEqual(result.account.resource_id, "account-001")
        self.assertEqual(result.account.status, "IN_USE")

        snapshot = self.make_store().load_snapshot()
        self.assertEqual(snapshot.revision, 3)
        statuses = {record.resource_id: record.status for record in snapshot.resources}
        self.assertEqual(statuses["account-001"], "IN_USE")
        self.assertEqual(statuses["proxy-001"], "AVAILABLE")
        self.assertEqual(len(snapshot.leases), 1)

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

    def test_acquire_rejects_unhashable_requested_slots(self) -> None:
        self.seed_default_resources()

        result = acquire(
            {
                "task_id": "task-002b",
                "adapter_key": "xhs",
                "capability": "content_detail_by_url",
                "requested_slots": [{"slot": "account"}],
            },
            self.make_store(),
            "task-context-002b",
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["category"], "invalid_input")
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

    def test_acquire_requires_non_empty_task_context(self) -> None:
        with self.assertRaisesRegex(ValueError, "task_context_task_id"):
            acquire(
                {
                    "task_id": "task-011b",
                    "adapter_key": "xhs",
                    "capability": "content_detail_by_url",
                    "requested_slots": ("account",),
                },
                self.make_store(),
                "",
            )

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

    def test_release_requires_non_empty_task_context(self) -> None:
        with self.assertRaisesRegex(ValueError, "task_context_task_id"):
            release(
                {
                    "lease_id": "lease-012b",
                    "task_id": "task-012b",
                    "target_status_after_release": "AVAILABLE",
                    "reason": "normal",
                },
                self.make_store(),
                "",
            )

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

    def test_release_rejects_concurrent_conflicting_semantics(self) -> None:
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
                task_id="task-015b",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            store,
            "task-context-015b",
        )
        assert isinstance(bundle, ResourceBundle)

        results = []

        def worker(target_status_after_release: str, reason: str) -> None:
            results.append(
                release(
                    ReleaseRequest(
                        lease_id=bundle.lease_id,
                        task_id="task-015b",
                        target_status_after_release=target_status_after_release,
                        reason=reason,
                    ),
                    store,
                    "task-context-015b",
                )
            )

        thread_a = threading.Thread(target=worker, args=("AVAILABLE", "normal"))
        thread_b = threading.Thread(target=worker, args=("INVALID", "burned"))
        thread_a.start()
        thread_b.start()
        thread_a.join()
        thread_b.join()

        self.assertEqual(len(results), 2)
        successful = [result for result in results if isinstance(result, ResourceLease)]
        failed = [result for result in results if isinstance(result, dict)]
        self.assertEqual(len(successful), 1)
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["error"]["code"], "resource_release_conflict")

        snapshot = self.make_store().load_snapshot()
        self.assertEqual(len(snapshot.leases), 1)
        lease = snapshot.leases[0]
        self.assertIsNotNone(lease.released_at)
        self.assertIn(lease.target_status_after_release, {"AVAILABLE", "INVALID"})
        self.assertIn(lease.release_reason, {"normal", "burned"})
        expected_status = "AVAILABLE" if lease.target_status_after_release == "AVAILABLE" else "INVALID"
        self.assertEqual(snapshot.resources[0].status, expected_status)

    def test_release_retries_when_unrelated_write_advances_revision(self) -> None:
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
                task_id="task-015e",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            store,
            "task-context-015e",
        )
        assert isinstance(bundle, ResourceBundle)

        results: list[object] = []

        def release_worker() -> None:
            results.append(
                release(
                    ReleaseRequest(
                        lease_id=bundle.lease_id,
                        task_id="task-015e",
                        target_status_after_release="AVAILABLE",
                        reason="normal",
                    ),
                    store,
                    "task-context-015e",
                )
            )

        def acquire_worker() -> None:
            results.append(
                acquire(
                    AcquireRequest(
                        task_id="task-015f",
                        adapter_key="xhs",
                        capability="content_detail_by_url",
                        requested_slots=("proxy",),
                    ),
                    store,
                    "task-context-015f",
                )
            )

        thread_a = threading.Thread(target=release_worker)
        thread_b = threading.Thread(target=acquire_worker)
        thread_a.start()
        thread_b.start()
        thread_a.join()
        thread_b.join()

        self.assertEqual(len(results), 2)
        self.assertTrue(any(isinstance(result, ResourceLease) for result in results))
        self.assertTrue(any(isinstance(result, ResourceBundle) for result in results))
        snapshot = self.make_store().load_snapshot()
        resources_by_id = {record.resource_id: record for record in snapshot.resources}
        self.assertEqual(resources_by_id["account-001"].status, "AVAILABLE")
        self.assertEqual(resources_by_id["proxy-001"].status, "IN_USE")

    def test_same_second_transitions_preserve_latest_settled_truth(self) -> None:
        self.seed_default_resources()

        with mock.patch("syvert.resource_lifecycle.now_rfc3339_utc", return_value="2026-04-20T00:00:00Z"):
            first_bundle = acquire(
                AcquireRequest(
                    task_id="task-015c",
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    requested_slots=("account",),
                ),
                self.make_store(),
                "task-context-015c",
            )
            assert isinstance(first_bundle, ResourceBundle)
            first_release = release(
                ReleaseRequest(
                    lease_id=first_bundle.lease_id,
                    task_id="task-015c",
                    target_status_after_release="AVAILABLE",
                    reason="normal",
                ),
                self.make_store(),
                "task-context-015c",
            )
            assert isinstance(first_release, ResourceLease)
            second_bundle = acquire(
                AcquireRequest(
                    task_id="task-015d",
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    requested_slots=("account",),
                ),
                self.make_store(),
                "task-context-015d",
            )
            assert isinstance(second_bundle, ResourceBundle)
            second_release = release(
                ReleaseRequest(
                    lease_id=second_bundle.lease_id,
                    task_id="task-015d",
                    target_status_after_release="INVALID",
                    reason="burned",
                ),
                self.make_store(),
                "task-context-015d",
            )

        self.assertIsInstance(second_release, ResourceLease)
        snapshot = self.make_store().load_snapshot()
        self.assertEqual(snapshot.resources[0].status, "INVALID")
        self.assertEqual(snapshot.leases[-1].target_status_after_release, "INVALID")

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

    def test_acquire_fails_closed_for_snapshot_that_resurrects_invalid_resource(self) -> None:
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

        result = acquire(
            AcquireRequest(
                task_id="task-013-invalid",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-context-013-invalid",
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["category"], "runtime_contract")
        self.assertEqual(result["error"]["code"], "resource_state_conflict")

    def test_acquire_fails_closed_for_snapshot_with_invalid_material_payload(self) -> None:
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

        result = acquire(
            AcquireRequest(
                task_id="task-013-material",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-context-013-material",
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["category"], "runtime_contract")
        self.assertEqual(result["error"]["code"], "resource_state_conflict")

    def test_acquire_returns_failed_envelope_when_store_write_setup_raises_oserror(self) -> None:
        self.seed_default_resources()

        with mock.patch("syvert.resource_lifecycle_store.tempfile.mkstemp", side_effect=OSError("disk full")):
            result = acquire(
                AcquireRequest(
                    task_id="task-013b",
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    requested_slots=("account",),
                ),
                self.make_store(),
                "task-context-013b",
            )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["category"], "runtime_contract")
        self.assertEqual(result["error"]["code"], "resource_state_conflict")

    def test_acquire_stays_successful_when_post_commit_directory_sync_fails(self) -> None:
        self.seed_default_resources()
        real_open = os.open

        def flaky_open(path, flags, mode=0o777):
            target_path = Path(path)
            if target_path == Path(self._resource_store_dir.name):
                raise OSError("directory fsync failed")
            return real_open(path, flags, mode)

        with mock.patch("syvert.resource_lifecycle_store.os.open", side_effect=flaky_open):
            result = acquire(
                AcquireRequest(
                    task_id="task-013-post-commit",
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    requested_slots=("account",),
                ),
                self.make_store(),
                "task-context-013-post-commit",
            )

        self.assertIsInstance(result, ResourceBundle)
        snapshot = self.make_store().load_snapshot()
        self.assertEqual(snapshot.revision, 2)
        self.assertEqual(snapshot.resources[0].status, "IN_USE")

    def test_acquire_returns_failed_envelope_for_invalid_utf8_snapshot(self) -> None:
        Path(self._resource_store_path).write_bytes(b"\xff\xfe")

        result = acquire(
            AcquireRequest(
                task_id="task-013-utf8",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-context-013-utf8",
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["code"], "resource_state_conflict")

    def test_acquire_returns_failed_envelope_when_store_load_raises_unexpected_error(self) -> None:
        class BrokenStore:
            def load_snapshot(self):
                raise OSError("backend unavailable")

            def write_snapshot(self, snapshot):
                raise AssertionError("write_snapshot should not be called")

        result = acquire(
            AcquireRequest(
                task_id="task-013-store-boundary",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            BrokenStore(),
            "task-context-013-store-boundary",
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["category"], "runtime_contract")
        self.assertEqual(result["error"]["code"], "resource_state_conflict")

    def test_acquire_returns_failed_envelope_for_invalid_in_memory_snapshot(self) -> None:
        class InvalidSnapshotStore:
            def load_snapshot(self):
                return ResourceLifecycleSnapshot(
                    schema_version="v0.4.0",
                    revision=0,
                    resources=(
                        ResourceRecord(
                            resource_id="",
                            resource_type="account",
                            status="AVAILABLE",
                            material={"provider_account_id": "pa-invalid"},
                        ),
                    ),
                    leases=(),
                )

            def write_snapshot(self, snapshot):
                raise AssertionError("write_snapshot should not be called")

        result = acquire(
            AcquireRequest(
                task_id="task-013-invalid-snapshot",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            InvalidSnapshotStore(),
            "task-context-013-invalid-snapshot",
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["category"], "runtime_contract")
        self.assertEqual(result["error"]["code"], "resource_state_conflict")

    def test_acquire_canonicalizes_material_from_in_memory_snapshot(self) -> None:
        class TupleMaterialStore:
            def load_snapshot(self):
                return ResourceLifecycleSnapshot(
                    schema_version="v0.4.0",
                    revision=0,
                    resources=(
                        ResourceRecord(
                            resource_id="account-tuple",
                            resource_type="account",
                            status="AVAILABLE",
                            material={"vals": ("a", "b")},
                        ),
                    ),
                    leases=(),
                )

            def write_snapshot(self, snapshot):
                return snapshot

        result = acquire(
            AcquireRequest(
                task_id="task-013-canonical-material",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            TupleMaterialStore(),
            "task-context-013-canonical-material",
        )

        self.assertIsInstance(result, ResourceBundle)
        assert isinstance(result, ResourceBundle)
        assert result.account is not None
        self.assertEqual(result.account.material, {"vals": ["a", "b"]})

    def test_release_returns_failed_envelope_when_store_lock_raises_oserror(self) -> None:
        self.seed_default_resources()
        bundle = acquire(
            AcquireRequest(
                task_id="task-013c",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-context-013c",
        )
        assert isinstance(bundle, ResourceBundle)

        with mock.patch("syvert.resource_lifecycle_store.fcntl.flock", side_effect=OSError("lock failed")):
            result = release(
                ReleaseRequest(
                    lease_id=bundle.lease_id,
                    task_id="task-013c",
                    target_status_after_release="AVAILABLE",
                    reason="normal",
                ),
                self.make_store(),
                "task-context-013c",
            )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["category"], "runtime_contract")
        self.assertEqual(result["error"]["code"], "resource_state_conflict")

    def test_acquire_stays_successful_when_unlock_fails_after_commit(self) -> None:
        self.seed_default_resources()
        real_flock = fcntl.flock

        def flaky_flock(fd, operation):
            if operation == fcntl.LOCK_UN:
                raise OSError("unlock failed")
            return real_flock(fd, operation)

        with mock.patch("syvert.resource_lifecycle_store.fcntl.flock", side_effect=flaky_flock):
            result = acquire(
                AcquireRequest(
                    task_id="task-013d",
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    requested_slots=("account",),
                ),
                self.make_store(),
                "task-context-013d",
            )

        self.assertIsInstance(result, ResourceBundle)
        snapshot = self.make_store().load_snapshot()
        self.assertEqual(snapshot.revision, 2)
        self.assertEqual(snapshot.resources[0].status, "IN_USE")
        self.assertEqual(len(snapshot.leases), 1)


if __name__ == "__main__":
    unittest.main()
