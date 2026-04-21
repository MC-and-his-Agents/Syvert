from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from syvert.resource_trace import (
    ResourceTraceContractError,
    ResourceTraceEvent,
    build_resource_lease_timeline,
    build_task_resource_usage_log,
)
from syvert.resource_trace_store import (
    ResourceTracePersistenceError,
    default_resource_trace_store,
    resolve_resource_trace_store_path,
)


class ResourceTraceStoreEnvMixin:
    def setUp(self) -> None:
        super().setUp()
        self._trace_store_dir = tempfile.TemporaryDirectory()
        self._trace_store_path = os.path.join(self._trace_store_dir.name, "resource-trace-events.jsonl")
        self._trace_store_patcher = mock.patch.dict(
            os.environ,
            {"SYVERT_RESOURCE_TRACE_STORE_FILE": self._trace_store_path},
            clear=False,
        )
        self._trace_store_patcher.start()

    def tearDown(self) -> None:
        self._trace_store_patcher.stop()
        self._trace_store_dir.cleanup()
        super().tearDown()

    def make_store(self):
        return default_resource_trace_store()


class ResourceTraceStoreTests(ResourceTraceStoreEnvMixin, unittest.TestCase):
    def acquired_event(self) -> ResourceTraceEvent:
        return ResourceTraceEvent(
            event_id="acquired:lease-001:account-001",
            task_id="task-001",
            lease_id="lease-001",
            bundle_id="bundle-001",
            resource_id="account-001",
            resource_type="account",
            adapter_key="xhs",
            capability="content_detail_by_url",
            event_type="acquired",
            from_status="AVAILABLE",
            to_status="IN_USE",
            occurred_at="2026-04-21T12:00:00.000000Z",
            reason="acquired_for_task",
        )

    def released_event(self) -> ResourceTraceEvent:
        return ResourceTraceEvent(
            event_id="released:lease-001:account-001",
            task_id="task-001",
            lease_id="lease-001",
            bundle_id="bundle-001",
            resource_id="account-001",
            resource_type="account",
            adapter_key="xhs",
            capability="content_detail_by_url",
            event_type="released",
            from_status="IN_USE",
            to_status="AVAILABLE",
            occurred_at="2026-04-21T12:10:00.000000Z",
            reason="adapter_completed_without_disposition_hint",
        )

    def proxy_acquired_event(self) -> ResourceTraceEvent:
        return ResourceTraceEvent(
            event_id="acquired:lease-001:proxy-001",
            task_id="task-001",
            lease_id="lease-001",
            bundle_id="bundle-001",
            resource_id="proxy-001",
            resource_type="proxy",
            adapter_key="xhs",
            capability="content_detail_by_url",
            event_type="acquired",
            from_status="AVAILABLE",
            to_status="IN_USE",
            occurred_at="2026-04-21T12:00:00.000000Z",
            reason="acquired_for_task",
        )

    def proxy_released_event(self) -> ResourceTraceEvent:
        return ResourceTraceEvent(
            event_id="released:lease-001:proxy-001",
            task_id="task-001",
            lease_id="lease-001",
            bundle_id="bundle-001",
            resource_id="proxy-001",
            resource_type="proxy",
            adapter_key="xhs",
            capability="content_detail_by_url",
            event_type="released",
            from_status="IN_USE",
            to_status="AVAILABLE",
            occurred_at="2026-04-21T12:10:00.000000Z",
            reason="adapter_completed_without_disposition_hint",
        )

    def invalidated_event(self) -> ResourceTraceEvent:
        return ResourceTraceEvent(
            **{
                **self.released_event().__dict__,
                "event_id": "invalidated:lease-001:account-001",
                "event_type": "invalidated",
                "to_status": "INVALID",
                "reason": "account_invalidated_by_adapter",
            }
        )

    def cross_task_proxy_acquired_event(self) -> ResourceTraceEvent:
        return ResourceTraceEvent(
            **{**self.proxy_acquired_event().__dict__, "task_id": "task-002"}
        )

    def alternate_bundle_proxy_acquired_event(self) -> ResourceTraceEvent:
        return ResourceTraceEvent(
            **{**self.proxy_acquired_event().__dict__, "bundle_id": "bundle-002"}
        )

    def alternate_lease_proxy_acquired_event(self) -> ResourceTraceEvent:
        return ResourceTraceEvent(
            **{
                **self.proxy_acquired_event().__dict__,
                "lease_id": "lease-002",
                "event_id": "acquired:lease-002:proxy-001",
            }
        )

    def test_append_events_round_trips_jsonl_store(self) -> None:
        store = self.make_store()
        appended = store.append_events((self.acquired_event(), self.proxy_acquired_event()))

        self.assertEqual(len(appended), 2)
        loaded = store.load_events()
        self.assertEqual(loaded, (self.acquired_event(), self.proxy_acquired_event()))

    def test_append_events_allows_same_payload_replay_as_noop(self) -> None:
        store = self.make_store()
        store.append_events((self.acquired_event(),))
        replayed = store.append_events((self.acquired_event(),))

        self.assertEqual(replayed, (self.acquired_event(),))
        self.assertEqual(store.load_events(), (self.acquired_event(),))

    def test_append_events_rejects_conflicting_payload_for_same_event_id(self) -> None:
        store = self.make_store()
        store.append_events((self.acquired_event(),))
        conflicting = ResourceTraceEvent(
            **{**self.acquired_event().__dict__, "reason": "different_reason"}
        )

        with self.assertRaises(ResourceTracePersistenceError):
            store.append_events((conflicting,))

    def test_append_events_rejects_cross_task_reuse_of_same_lease_and_bundle(self) -> None:
        store = self.make_store()
        store.append_events((self.acquired_event(),))

        with self.assertRaises(ResourceTracePersistenceError):
            store.append_events((self.cross_task_proxy_acquired_event(),))

    def test_append_events_rejects_same_lease_reused_with_different_bundle(self) -> None:
        store = self.make_store()
        store.append_events((self.acquired_event(),))

        with self.assertRaises(ResourceTracePersistenceError):
            store.append_events((self.alternate_bundle_proxy_acquired_event(),))

    def test_append_events_rejects_same_bundle_reused_with_different_lease(self) -> None:
        store = self.make_store()
        store.append_events((self.acquired_event(),))

        with self.assertRaises(ResourceTracePersistenceError):
            store.append_events((self.alternate_lease_proxy_acquired_event(),))

    def test_append_events_rejects_released_without_matching_acquired(self) -> None:
        store = self.make_store()

        with self.assertRaises(ResourceTracePersistenceError):
            store.append_events((self.released_event(),))

    def test_append_events_rejects_multiple_closeouts_for_same_resource_timeline(self) -> None:
        store = self.make_store()
        store.append_events((self.acquired_event(), self.released_event()))

        with self.assertRaises(ResourceTracePersistenceError):
            store.append_events((self.invalidated_event(),))

    def test_store_builds_task_usage_log_and_lease_timeline(self) -> None:
        store = self.make_store()
        store.append_events(
            (
                self.acquired_event(),
                self.proxy_acquired_event(),
                self.released_event(),
                self.proxy_released_event(),
            )
        )

        usage_log = store.task_usage_log("task-001")
        lease_timeline = store.lease_timeline("lease-001")
        resource_events = store.resource_events("account-001")

        self.assertEqual(len(usage_log.events), 4)
        self.assertEqual(lease_timeline.bundle_id, "bundle-001")
        self.assertEqual(len(lease_timeline.resource_timelines), 2)
        self.assertEqual(lease_timeline.resource_timelines[0].acquired_at, "2026-04-21T12:00:00.000000Z")
        self.assertEqual(len(resource_events), 2)
        self.assertEqual(store.bundle_timeline("bundle-001"), lease_timeline)
        self.assertEqual(resource_events[0].event_type, "acquired")
        self.assertEqual(resource_events[1].event_type, "released")

    def test_load_events_deduplicates_identical_replayed_event_ids(self) -> None:
        store = self.make_store()
        payload = (
            '{"adapter_key":"xhs","bundle_id":"bundle-001","capability":"content_detail_by_url","event_id":"acquired:lease-001:account-001","event_type":"acquired","from_status":"AVAILABLE","lease_id":"lease-001","occurred_at":"2026-04-21T12:00:00.000000Z","reason":"acquired_for_task","resource_id":"account-001","resource_type":"account","task_id":"task-001","to_status":"IN_USE"}'
        )
        store.path.write_text(f"{payload}\n{payload}\n", encoding="utf-8")

        self.assertEqual(store.load_events(), (self.acquired_event(),))

    def test_load_events_rejects_cross_task_reuse_of_same_lease_and_bundle(self) -> None:
        store = self.make_store()
        store.path.write_text(
            "\n".join(
                (
                    '{"adapter_key":"xhs","bundle_id":"bundle-001","capability":"content_detail_by_url","event_id":"acquired:lease-001:account-001","event_type":"acquired","from_status":"AVAILABLE","lease_id":"lease-001","occurred_at":"2026-04-21T12:00:00.000000Z","reason":"acquired_for_task","resource_id":"account-001","resource_type":"account","task_id":"task-001","to_status":"IN_USE"}',
                    '{"adapter_key":"xhs","bundle_id":"bundle-001","capability":"content_detail_by_url","event_id":"acquired:lease-001:proxy-001","event_type":"acquired","from_status":"AVAILABLE","lease_id":"lease-001","occurred_at":"2026-04-21T12:00:00.000000Z","reason":"acquired_for_task","resource_id":"proxy-001","resource_type":"proxy","task_id":"task-002","to_status":"IN_USE"}',
                    "",
                )
            ),
            encoding="utf-8",
        )

        with self.assertRaises(ResourceTracePersistenceError):
            store.load_events()

    def test_load_events_rejects_same_lease_reused_with_different_bundle(self) -> None:
        store = self.make_store()
        store.path.write_text(
            "\n".join(
                (
                    '{"adapter_key":"xhs","bundle_id":"bundle-001","capability":"content_detail_by_url","event_id":"acquired:lease-001:account-001","event_type":"acquired","from_status":"AVAILABLE","lease_id":"lease-001","occurred_at":"2026-04-21T12:00:00.000000Z","reason":"acquired_for_task","resource_id":"account-001","resource_type":"account","task_id":"task-001","to_status":"IN_USE"}',
                    '{"adapter_key":"xhs","bundle_id":"bundle-002","capability":"content_detail_by_url","event_id":"acquired:lease-001:proxy-001","event_type":"acquired","from_status":"AVAILABLE","lease_id":"lease-001","occurred_at":"2026-04-21T12:00:00.000000Z","reason":"acquired_for_task","resource_id":"proxy-001","resource_type":"proxy","task_id":"task-001","to_status":"IN_USE"}',
                    "",
                )
            ),
            encoding="utf-8",
        )

        with self.assertRaises(ResourceTracePersistenceError):
            store.load_events()

    def test_load_events_rejects_same_bundle_reused_with_different_lease(self) -> None:
        store = self.make_store()
        store.path.write_text(
            "\n".join(
                (
                    '{"adapter_key":"xhs","bundle_id":"bundle-001","capability":"content_detail_by_url","event_id":"acquired:lease-001:account-001","event_type":"acquired","from_status":"AVAILABLE","lease_id":"lease-001","occurred_at":"2026-04-21T12:00:00.000000Z","reason":"acquired_for_task","resource_id":"account-001","resource_type":"account","task_id":"task-001","to_status":"IN_USE"}',
                    '{"adapter_key":"xhs","bundle_id":"bundle-001","capability":"content_detail_by_url","event_id":"acquired:lease-002:proxy-001","event_type":"acquired","from_status":"AVAILABLE","lease_id":"lease-002","occurred_at":"2026-04-21T12:00:00.000000Z","reason":"acquired_for_task","resource_id":"proxy-001","resource_type":"proxy","task_id":"task-001","to_status":"IN_USE"}',
                    "",
                )
            ),
            encoding="utf-8",
        )

        with self.assertRaises(ResourceTracePersistenceError):
            store.load_events()

    def test_projection_builders_reject_cross_task_reuse_of_same_lease_and_bundle(self) -> None:
        events = (self.acquired_event(), self.cross_task_proxy_acquired_event())

        with self.assertRaises(ResourceTraceContractError):
            build_task_resource_usage_log(events, task_id="task-001")
        with self.assertRaises(ResourceTraceContractError):
            build_resource_lease_timeline(events, lease_id="lease-001")

    def test_projection_builders_reject_same_lease_reused_with_different_bundle(self) -> None:
        events = (self.acquired_event(), self.alternate_bundle_proxy_acquired_event())

        with self.assertRaises(ResourceTraceContractError):
            build_task_resource_usage_log(events, task_id="task-001")
        with self.assertRaises(ResourceTraceContractError):
            build_resource_lease_timeline(events, lease_id="lease-001")

    def test_projection_builders_reject_same_bundle_reused_with_different_lease(self) -> None:
        events = (self.acquired_event(), self.alternate_lease_proxy_acquired_event())

        with self.assertRaises(ResourceTraceContractError):
            build_task_resource_usage_log(events, task_id="task-001")
        with self.assertRaises(ResourceTraceContractError):
            build_resource_lease_timeline(events, bundle_id="bundle-001")

    def test_projection_builders_reject_released_without_matching_acquired(self) -> None:
        with self.assertRaises(ResourceTraceContractError):
            build_task_resource_usage_log((self.released_event(),), task_id="task-001")
        with self.assertRaises(ResourceTraceContractError):
            build_resource_lease_timeline((self.released_event(),), lease_id="lease-001")

    def test_projection_builders_reject_multiple_closeouts_for_same_resource_timeline(self) -> None:
        events = (self.acquired_event(), self.released_event(), self.invalidated_event())

        with self.assertRaises(ResourceTraceContractError):
            build_task_resource_usage_log(events, task_id="task-001")
        with self.assertRaises(ResourceTraceContractError):
            build_resource_lease_timeline(events, lease_id="lease-001")

    def test_resolve_trace_store_path_prefers_env_then_default(self) -> None:
        self.assertEqual(resolve_resource_trace_store_path(), Path(self._trace_store_path))
        self.assertEqual(
            resolve_resource_trace_store_path(env={}),
            Path.home() / ".syvert" / "resource-trace-events.jsonl",
        )
