from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from syvert.resource_trace import ResourceTraceEvent
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
        self.assertEqual(resource_events[0].event_type, "acquired")
        self.assertEqual(resource_events[1].event_type, "released")

    def test_resolve_trace_store_path_prefers_env_then_default(self) -> None:
        self.assertEqual(resolve_resource_trace_store_path(), Path(self._trace_store_path))
        self.assertEqual(
            resolve_resource_trace_store_path(env={}),
            Path.home() / ".syvert" / "resource-trace-events.jsonl",
        )
