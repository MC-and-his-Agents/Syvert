from __future__ import annotations

from collections.abc import Mapping
import os
import tempfile
from dataclasses import dataclass, replace
from typing import Iterator, Tuple
import unittest
from unittest import mock

import syvert.runtime as runtime_module
from syvert.adapters.douyin import DouyinAdapter
from syvert.adapters.xhs import XhsAdapter
from syvert.resource_lifecycle_store import default_resource_lifecycle_store
from syvert.runtime import (
    AdapterExecutionContext,
    AdapterTaskRequest,
    CollectionPolicy,
    CoreTaskRequest,
    InputTarget,
    PlatformAdapterError,
    TaskInput,
    TaskRequest,
    execute_task,
)
from tests.runtime.resource_fixtures import ResourceStoreEnvMixin, seed_default_runtime_resources


class TaskRecordStoreEnvMixin(ResourceStoreEnvMixin):
    def setUp(self) -> None:
        super().setUp()
        self._task_record_store_dir = tempfile.TemporaryDirectory()
        self._task_record_store_patcher = mock.patch.dict(
            os.environ,
            {"SYVERT_TASK_RECORD_STORE_DIR": self._task_record_store_dir.name},
            clear=False,
        )
        self._task_record_store_patcher.start()

    def tearDown(self) -> None:
        self._task_record_store_patcher.stop()
        self._task_record_store_dir.cleanup()
        super().tearDown()


@dataclass(frozen=True)
class ExtendedTaskInput(TaskInput):
    platform_hint: str


@dataclass(frozen=True)
class ExtendedTaskRequest(TaskRequest):
    extra: str


class SuccessfulAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: TaskRequest) -> dict[str, object]:
        self.last_request = request
        return {
            "raw": {
                "id": "raw-1",
                "url": request.input.url,
            },
            "normalized": {
                "platform": "stub",
                "content_id": "content-1",
                "content_type": "unknown",
                "canonical_url": request.input.url,
                "title": "",
                "body_text": "",
                "published_at": None,
                "author": {
                    "author_id": None,
                    "display_name": None,
                    "avatar_url": None,
                },
                "stats": {
                    "like_count": None,
                    "comment_count": None,
                    "share_count": None,
                    "collect_count": None,
                },
                "media": {
                    "cover_url": None,
                    "video_url": None,
                    "image_urls": [],
                },
            },
        }


class MissingRawAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: TaskRequest) -> dict[str, object]:
        return {
            "normalized": {
                "platform": "stub",
                "content_id": "content-1",
                "content_type": "unknown",
                "canonical_url": request.input.url,
                "title": "",
                "body_text": "",
                "published_at": None,
                "author": {
                    "author_id": None,
                    "display_name": None,
                    "avatar_url": None,
                },
                "stats": {
                    "like_count": None,
                    "comment_count": None,
                    "share_count": None,
                    "collect_count": None,
                },
                "media": {
                    "cover_url": None,
                    "video_url": None,
                    "image_urls": [],
                },
            },
        }


class NonePayloadAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: TaskRequest):
        return None


class ListPayloadAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: TaskRequest):
        return []


class CrashingAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: TaskRequest):
        raise RuntimeError("boom")


class PlatformErrorWithBadDetailsAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: TaskRequest):
        from syvert.runtime import PlatformAdapterError

        raise PlatformAdapterError(code="platform_broken", message="bad details", details=None)


class PlatformFailureAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: TaskRequest) -> dict[str, object]:
        raise PlatformAdapterError(
            code="content_not_found",
            message="content not found",
            details={"reason": "missing"},
        )


class InvalidatingHintAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: AdapterExecutionContext) -> dict[str, object]:
        assert request.resource_bundle is not None
        return {
            "raw": {"id": "raw-invalid-hint"},
            "normalized": {
                "platform": "stub",
                "content_id": "content-invalid-hint",
                "content_type": "unknown",
                "canonical_url": request.input.url,
                "title": "",
                "body_text": "",
                "published_at": None,
                "author": {
                    "author_id": None,
                    "display_name": None,
                    "avatar_url": None,
                },
                "stats": {
                    "like_count": None,
                    "comment_count": None,
                    "share_count": None,
                    "collect_count": None,
                },
                "media": {
                    "cover_url": None,
                    "video_url": None,
                    "image_urls": [],
                },
            },
            "resource_disposition_hint": {
                "lease_id": request.resource_bundle.lease_id,
                "target_status_after_release": "INVALID",
                "reason": "account_invalidated_by_adapter",
            },
        }


class LeaseIdMismatchHintAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: AdapterExecutionContext) -> dict[str, object]:
        return {
            "raw": {"id": "raw-bad-hint"},
            "normalized": {
                "platform": "stub",
                "content_id": "content-bad-hint",
                "content_type": "unknown",
                "canonical_url": request.input.url,
                "title": "",
                "body_text": "",
                "published_at": None,
                "author": {
                    "author_id": None,
                    "display_name": None,
                    "avatar_url": None,
                },
                "stats": {
                    "like_count": None,
                    "comment_count": None,
                    "share_count": None,
                    "collect_count": None,
                },
                "media": {
                    "cover_url": None,
                    "video_url": None,
                    "image_urls": [],
                },
            },
            "resource_disposition_hint": {
                "lease_id": "lease-mismatch",
                "target_status_after_release": "INVALID",
                "reason": "bad_hint",
            },
        }


class InvalidTargetStatusHintAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: AdapterExecutionContext) -> dict[str, object]:
        assert request.resource_bundle is not None
        return {
            "raw": {"id": "raw-bad-status-hint"},
            "normalized": {
                "platform": "stub",
                "content_id": "content-bad-status-hint",
                "content_type": "unknown",
                "canonical_url": request.input.url,
                "title": "",
                "body_text": "",
                "published_at": None,
                "author": {
                    "author_id": None,
                    "display_name": None,
                    "avatar_url": None,
                },
                "stats": {
                    "like_count": None,
                    "comment_count": None,
                    "share_count": None,
                    "collect_count": None,
                },
                "media": {
                    "cover_url": None,
                    "video_url": None,
                    "image_urls": [],
                },
            },
            "resource_disposition_hint": {
                "lease_id": request.resource_bundle.lease_id,
                "target_status_after_release": "IN_USE",
                "reason": "bad_hint",
            },
        }


class NeverCalledAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: AdapterExecutionContext):
        raise AssertionError("adapter should not be called")


class PrePlatformValidationAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: TaskRequest):
        raise PlatformAdapterError(
            code="adapter_precheck_failed",
            message="adapter pre-platform validation failed",
            details={"reason": "precheck"},
            category="invalid_input",
        )


class NoneCapabilitiesAdapter:
    adapter_key = "stub"
    supported_capabilities = None

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class NonContainerCapabilitiesAdapter:
    adapter_key = "stub"
    supported_capabilities = 123

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class NonStringCapabilitiesAdapter:
    adapter_key = "stub"
    supported_capabilities = ("content_detail", 1)

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class MissingCapabilitiesAdapter:
    adapter_key = "stub"

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class BrokenCapabilitiesIterable:
    def __iter__(self):
        yield "content_detail"
        raise RuntimeError("broken-iterator")


class BrokenIterableCapabilitiesAdapter:
    adapter_key = "stub"
    supported_capabilities = BrokenCapabilitiesIterable()

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class ExplodingAdapterRegistry(Mapping[str, object]):
    def __iter__(self) -> Iterator[str]:
        return iter(())

    def __len__(self) -> int:
        return 0

    def __getitem__(self, key: str) -> object:
        raise KeyError(key)

    def items(self) -> Iterator[Tuple[str, object]]:
        raise RuntimeError("boom")


class DuplicateAdapterRegistry(Mapping[str, object]):
    def __init__(self, adapter: object) -> None:
        self._adapter = adapter

    def __iter__(self) -> Iterator[str]:
        return iter(("stub", "stub"))

    def __len__(self) -> int:
        return 2

    def __getitem__(self, key: str) -> object:
        if key != "stub":
            raise KeyError(key)
        return self._adapter

    def items(self) -> Iterator[Tuple[str, object]]:
        return iter((("stub", self._adapter), ("stub", self._adapter)))


class ExplodingRequestMapping(dict):
    def get(self, key, default=None):
        raise RuntimeError("boom")


class MissingTargetsAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class UnsupportedHybridCollectionModeAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"authenticated"})

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class BroadAxesAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url", "content_id", "creator_id", "keyword"})
    supported_collection_modes = frozenset({"public", "authenticated", "hybrid"})

    def execute(self, request: TaskRequest):
        raise AssertionError("shared admission should fail before adapter execution")


class MissingCollectionModesAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class MissingExecuteAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})


class RuntimeExecutionTests(TaskRecordStoreEnvMixin, unittest.TestCase):
    def latest_snapshot(self):
        return default_resource_lifecycle_store().load_snapshot()

    def lease_for_task(self, task_id: str):
        snapshot = self.latest_snapshot()
        return next(lease for lease in snapshot.leases if lease.task_id == task_id)

    def resource_statuses(self) -> dict[str, str]:
        snapshot = self.latest_snapshot()
        return {record.resource_id: record.status for record in snapshot.resources}

    def test_execute_task_builds_success_envelope_from_adapter_payload(self) -> None:
        adapter = SuccessfulAdapter()
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": adapter},
            task_id_factory=lambda: "task-001",
        )

        self.assertEqual(envelope["task_id"], "task-001")
        self.assertEqual(envelope["adapter_key"], "stub")
        self.assertEqual(envelope["capability"], "content_detail_by_url")
        self.assertEqual(envelope["status"], "success")
        self.assertIn("raw", envelope)
        self.assertEqual(envelope["normalized"]["canonical_url"], request.input.url)
        self.assertIsInstance(adapter.last_request, AdapterExecutionContext)
        self.assertEqual(adapter.last_request.request.capability, "content_detail")
        self.assertEqual(adapter.last_request.request.target_type, "url")
        self.assertEqual(adapter.last_request.request.target_value, request.input.url)
        self.assertEqual(adapter.last_request.request.collection_mode, "hybrid")
        self.assertIsNotNone(adapter.last_request.resource_bundle)
        self.assertEqual(adapter.last_request.resource_bundle.capability, "content_detail_by_url")

    def test_execute_task_executes_core_request_through_adapter_projection(self) -> None:
        adapter = SuccessfulAdapter()
        request = CoreTaskRequest(
            target=InputTarget(
                adapter_key="stub",
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/posts/2",
            ),
            policy=CollectionPolicy(collection_mode="hybrid"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": adapter},
            task_id_factory=lambda: "task-001b",
        )

        self.assertEqual(envelope["task_id"], "task-001b")
        self.assertEqual(envelope["status"], "success")
        self.assertEqual(envelope["adapter_key"], "stub")
        self.assertEqual(envelope["normalized"]["canonical_url"], request.target.target_value)
        self.assertIsInstance(adapter.last_request, AdapterExecutionContext)
        self.assertEqual(adapter.last_request.request.capability, "content_detail")
        self.assertEqual(adapter.last_request.request.target_type, "url")
        self.assertEqual(adapter.last_request.request.target_value, request.target.target_value)
        self.assertEqual(adapter.last_request.request.collection_mode, "hybrid")
        self.assertIsNotNone(adapter.last_request.resource_bundle)
        self.assertEqual(adapter.last_request.resource_bundle.capability, "content_detail_by_url")

    def test_execute_task_maps_legacy_and_native_requests_to_same_adapter_projection(self) -> None:
        legacy_adapter = SuccessfulAdapter()
        native_adapter = SuccessfulAdapter()
        legacy_request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/legacy-native"),
        )
        native_request = CoreTaskRequest(
            target=InputTarget(
                adapter_key="stub",
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/posts/legacy-native",
            ),
            policy=CollectionPolicy(collection_mode="hybrid"),
        )

        legacy_envelope = execute_task(
            legacy_request,
            adapters={"stub": legacy_adapter},
            task_id_factory=lambda: "task-legacy-map",
        )
        native_envelope = execute_task(
            native_request,
            adapters={"stub": native_adapter},
            task_id_factory=lambda: "task-native-map",
        )

        self.assertEqual(legacy_envelope["status"], "success")
        self.assertEqual(native_envelope["status"], "success")
        self.assertEqual(legacy_envelope["raw"], native_envelope["raw"])
        self.assertEqual(legacy_envelope["normalized"], native_envelope["normalized"])
        self.assertEqual(legacy_adapter.last_request.request, native_adapter.last_request.request)
        self.assertEqual(legacy_adapter.last_request.request.target_type, "url")
        self.assertEqual(legacy_adapter.last_request.request.target_value, legacy_request.input.url)
        self.assertEqual(legacy_adapter.last_request.request.collection_mode, "hybrid")
        self.assertIsNotNone(legacy_adapter.last_request.resource_bundle)
        self.assertIsNotNone(native_adapter.last_request.resource_bundle)
        self.assertEqual(legacy_adapter.last_request.resource_bundle.capability, "content_detail_by_url")
        self.assertEqual(native_adapter.last_request.resource_bundle.capability, "content_detail_by_url")

    def test_execute_task_rejects_unknown_target_type(self) -> None:
        request = CoreTaskRequest(
            target=InputTarget(
                adapter_key="stub",
                capability="content_detail_by_url",
                target_type="unknown_type",
                target_value="https://example.com/posts/2",
            ),
            policy=CollectionPolicy(collection_mode="hybrid"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: "task-invalid-target-type",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_rejects_unknown_collection_mode(self) -> None:
        request = CoreTaskRequest(
            target=InputTarget(
                adapter_key="stub",
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/posts/2",
            ),
            policy=CollectionPolicy(collection_mode="private"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: "task-invalid-collection-mode",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_rejects_non_url_target_at_shared_projection_guard(self) -> None:
        request = CoreTaskRequest(
            target=InputTarget(
                adapter_key="stub",
                capability="content_detail_by_url",
                target_type="content_id",
                target_value="abc123",
            ),
            policy=CollectionPolicy(collection_mode="hybrid"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": BroadAxesAdapter()},
            task_id_factory=lambda: "task-non-url-target",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_rejects_public_collection_mode_at_shared_projection_guard(self) -> None:
        request = CoreTaskRequest(
            target=InputTarget(
                adapter_key="stub",
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/posts/2",
            ),
            policy=CollectionPolicy(collection_mode="public"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": BroadAxesAdapter()},
            task_id_factory=lambda: "task-public-mode",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_rejects_authenticated_collection_mode_at_shared_projection_guard(self) -> None:
        request = CoreTaskRequest(
            target=InputTarget(
                adapter_key="stub",
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/posts/2",
            ),
            policy=CollectionPolicy(collection_mode="authenticated"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": BroadAxesAdapter()},
            task_id_factory=lambda: "task-authenticated-mode",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_rejects_unknown_adapter_as_unsupported_failure(self) -> None:
        request = TaskRequest(
            adapter_key="missing",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={},
            task_id_factory=lambda: "task-002",
        )

        self.assertEqual(envelope["task_id"], "task-002")
        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "unsupported")
        self.assertEqual(envelope["error"]["code"], "adapter_not_found")

    def test_execute_task_rejects_legacy_request_when_adapter_lacks_supported_targets(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": MissingTargetsAdapter()},
            task_id_factory=lambda: "task-missing-targets",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_targets")

    def test_execute_task_rejects_legacy_request_when_adapter_does_not_declare_hybrid_mode(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": UnsupportedHybridCollectionModeAdapter()},
            task_id_factory=lambda: "task-unsupported-hybrid",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "collection_mode_not_supported")

    def test_execute_task_fails_closed_for_missing_supported_collection_modes(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": MissingCollectionModesAdapter()},
            task_id_factory=lambda: "task-missing-collection-modes",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_collection_modes")

    def test_execute_task_rejects_legacy_and_native_requests_with_same_hybrid_admission_error(self) -> None:
        legacy_request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/no-hybrid"),
        )
        native_request = CoreTaskRequest(
            target=InputTarget(
                adapter_key="stub",
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/posts/no-hybrid",
            ),
            policy=CollectionPolicy(collection_mode="hybrid"),
        )

        legacy_envelope = execute_task(
            legacy_request,
            adapters={"stub": UnsupportedHybridCollectionModeAdapter()},
            task_id_factory=lambda: "task-legacy-no-hybrid",
        )
        native_envelope = execute_task(
            native_request,
            adapters={"stub": UnsupportedHybridCollectionModeAdapter()},
            task_id_factory=lambda: "task-native-no-hybrid",
        )

        self.assertEqual(legacy_envelope["status"], "failed")
        self.assertEqual(native_envelope["status"], "failed")
        self.assertEqual(legacy_envelope["error"]["category"], "invalid_input")
        self.assertEqual(native_envelope["error"]["category"], "invalid_input")
        self.assertEqual(legacy_envelope["error"]["code"], "collection_mode_not_supported")
        self.assertEqual(native_envelope["error"]["code"], "collection_mode_not_supported")
        self.assertEqual(legacy_envelope["error"]["details"], native_envelope["error"]["details"])

    def test_execute_task_rejects_unsupported_capability(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="search",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: "task-unsupported",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_capability")

    def test_execute_task_rejects_success_without_raw_payload(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": MissingRawAdapter()},
            task_id_factory=lambda: "task-003",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_success_payload")

    def test_execute_task_fails_closed_when_adapter_returns_none(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": NonePayloadAdapter()},
            task_id_factory=lambda: "task-004",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_success_payload")

    def test_execute_task_fails_closed_when_adapter_returns_non_mapping_payload(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": ListPayloadAdapter()},
            task_id_factory=lambda: "task-005",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_success_payload")

    def test_execute_task_fails_closed_when_adapter_raises_generic_exception(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": CrashingAdapter()},
            task_id_factory=lambda: "task-006",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "adapter_execution_error")

    def test_execute_task_handles_platform_error_with_non_mapping_details(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": PlatformErrorWithBadDetailsAdapter()},
            task_id_factory=lambda: "task-007",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "platform")
        self.assertEqual(envelope["error"]["code"], "platform_broken")
        self.assertEqual(envelope["error"]["details"], {})

    def test_execute_task_wraps_platform_error(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": PlatformFailureAdapter()},
            task_id_factory=lambda: "task-platform-failure",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "platform")
        self.assertEqual(envelope["error"]["code"], "content_not_found")
        self.assertEqual(envelope["error"]["details"]["reason"], "missing")

    def test_execute_task_releases_bundle_when_host_side_validation_fails_after_acquire(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/host-validation"),
        )
        original_acquire = runtime_module.acquire_runtime_resource_bundle

        def acquire_bundle_with_mutated_capability(**kwargs):
            bundle = original_acquire(**kwargs)
            return replace(bundle, capability="content_detail")

        with mock.patch(
            "syvert.runtime.acquire_runtime_resource_bundle",
            side_effect=acquire_bundle_with_mutated_capability,
        ):
            envelope = execute_task(
                request,
                adapters={"stub": NeverCalledAdapter()},
                task_id_factory=lambda: "task-host-validation",
            )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_resource_bundle")
        lease = self.lease_for_task("task-host-validation")
        self.assertEqual(lease.capability, "content_detail_by_url")
        self.assertEqual(lease.target_status_after_release, "AVAILABLE")
        self.assertEqual(lease.release_reason, "host_side_bundle_validation_failed")
        self.assertIsNotNone(lease.released_at)
        self.assertEqual(set(self.resource_statuses().values()), {"AVAILABLE"})

    def test_execute_task_rejects_bundle_with_mismatched_lease_id_before_adapter_and_settles_real_lease(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/host-validation-lease-id"),
        )
        original_acquire = runtime_module.acquire_runtime_resource_bundle

        def acquire_bundle_with_mutated_lease_id(**kwargs):
            bundle = original_acquire(**kwargs)
            return replace(bundle, lease_id="lease-bogus")

        with mock.patch(
            "syvert.runtime.acquire_runtime_resource_bundle",
            side_effect=acquire_bundle_with_mutated_lease_id,
        ):
            envelope = execute_task(
                request,
                adapters={"stub": NeverCalledAdapter()},
                task_id_factory=lambda: "task-host-validation-lease-id",
            )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_resource_bundle")
        lease = self.lease_for_task("task-host-validation-lease-id")
        self.assertEqual(lease.target_status_after_release, "AVAILABLE")
        self.assertEqual(lease.release_reason, "host_side_bundle_validation_failed")
        self.assertEqual(set(self.resource_statuses().values()), {"AVAILABLE"})

    def test_execute_task_rejects_bundle_with_tampered_material_and_acquired_at_before_adapter(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/host-validation-material"),
        )
        original_acquire = runtime_module.acquire_runtime_resource_bundle

        def acquire_bundle_with_tampered_truth(**kwargs):
            bundle = original_acquire(**kwargs)
            tampered_account = replace(
                bundle.account,
                material={**bundle.account.material, "cookies": "tampered=1"},
            )
            return replace(
                bundle,
                acquired_at="2026-01-01T00:00:00Z",
                account=tampered_account,
            )

        with mock.patch(
            "syvert.runtime.acquire_runtime_resource_bundle",
            side_effect=acquire_bundle_with_tampered_truth,
        ):
            envelope = execute_task(
                request,
                adapters={"stub": NeverCalledAdapter()},
                task_id_factory=lambda: "task-host-validation-material",
            )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_resource_bundle")
        lease = self.lease_for_task("task-host-validation-material")
        self.assertEqual(lease.target_status_after_release, "AVAILABLE")
        self.assertEqual(lease.release_reason, "host_side_bundle_validation_failed")
        self.assertEqual(set(self.resource_statuses().values()), {"AVAILABLE"})

    def test_execute_task_settles_success_without_hint_as_available(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key="stub",
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/posts/no-hint-success"),
            ),
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: "task-no-hint-success",
        )

        self.assertEqual(envelope["status"], "success")
        lease = self.lease_for_task("task-no-hint-success")
        self.assertEqual(lease.capability, "content_detail_by_url")
        self.assertEqual(lease.target_status_after_release, "AVAILABLE")
        self.assertEqual(lease.release_reason, "adapter_completed_without_disposition_hint")
        self.assertEqual(set(self.resource_statuses().values()), {"AVAILABLE"})

    def test_execute_task_settles_failure_without_hint_as_available(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key="stub",
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/posts/no-hint-failure"),
            ),
            adapters={"stub": PlatformFailureAdapter()},
            task_id_factory=lambda: "task-no-hint-failure",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["code"], "content_not_found")
        lease = self.lease_for_task("task-no-hint-failure")
        self.assertEqual(lease.target_status_after_release, "AVAILABLE")
        self.assertEqual(lease.release_reason, "adapter_failed_without_disposition_hint")
        self.assertEqual(set(self.resource_statuses().values()), {"AVAILABLE"})

    def test_execute_task_applies_invalidating_hint_without_leaking_internal_field(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key="stub",
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/posts/invalidating-hint"),
            ),
            adapters={"stub": InvalidatingHintAdapter()},
            task_id_factory=lambda: "task-invalidating-hint",
        )

        self.assertEqual(envelope["status"], "success")
        self.assertNotIn("resource_disposition_hint", envelope)
        lease = self.lease_for_task("task-invalidating-hint")
        self.assertEqual(lease.target_status_after_release, "INVALID")
        self.assertEqual(lease.release_reason, "account_invalidated_by_adapter")
        self.assertEqual(set(self.resource_statuses().values()), {"INVALID"})

    def test_execute_task_rejects_mismatched_hint_lease_id_and_still_settles_bundle(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key="stub",
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/posts/hint-mismatch"),
            ),
            adapters={"stub": LeaseIdMismatchHintAdapter()},
            task_id_factory=lambda: "task-hint-mismatch",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_resource_disposition_hint")
        lease = self.lease_for_task("task-hint-mismatch")
        self.assertEqual(lease.target_status_after_release, "AVAILABLE")
        self.assertEqual(lease.release_reason, "invalid_resource_disposition_hint")
        self.assertEqual(set(self.resource_statuses().values()), {"AVAILABLE"})

    def test_execute_task_rejects_invalid_hint_target_status_and_still_settles_bundle(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key="stub",
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/posts/hint-bad-status"),
            ),
            adapters={"stub": InvalidTargetStatusHintAdapter()},
            task_id_factory=lambda: "task-hint-bad-status",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_resource_disposition_hint")
        lease = self.lease_for_task("task-hint-bad-status")
        self.assertEqual(lease.target_status_after_release, "AVAILABLE")
        self.assertEqual(lease.release_reason, "invalid_resource_disposition_hint")
        self.assertEqual(set(self.resource_statuses().values()), {"AVAILABLE"})

    def test_execute_task_release_failure_overrides_original_success(self) -> None:
        with mock.patch(
            "syvert.resource_lifecycle.release",
            return_value={
                "task_id": "task-release-overrides-success",
                "adapter_key": "stub",
                "capability": "content_detail_by_url",
                "status": "failed",
                "error": {
                    "category": "runtime_contract",
                    "code": "release_write_failed",
                    "message": "release failed",
                    "details": {},
                },
            },
        ):
            envelope = execute_task(
                TaskRequest(
                    adapter_key="stub",
                    capability="content_detail_by_url",
                    input=TaskInput(url="https://example.com/posts/release-success"),
                ),
                adapters={"stub": SuccessfulAdapter()},
                task_id_factory=lambda: "task-release-overrides-success",
            )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["code"], "release_write_failed")

    def test_execute_task_release_failure_overrides_original_failure(self) -> None:
        with mock.patch(
            "syvert.resource_lifecycle.release",
            return_value={
                "task_id": "task-release-overrides-failure",
                "adapter_key": "stub",
                "capability": "content_detail_by_url",
                "status": "failed",
                "error": {
                    "category": "runtime_contract",
                    "code": "release_write_failed",
                    "message": "release failed",
                    "details": {},
                },
            },
        ):
            envelope = execute_task(
                TaskRequest(
                    adapter_key="stub",
                    capability="content_detail_by_url",
                    input=TaskInput(url="https://example.com/posts/release-failure"),
                ),
                adapters={"stub": PlatformFailureAdapter()},
                task_id_factory=lambda: "task-release-overrides-failure",
            )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["code"], "release_write_failed")

    def test_execute_task_maps_real_xhs_invalid_url_to_invalid_input(self) -> None:
        seed_default_runtime_resources(adapter_key="xhs", account_resource_id="xhs-account-001")
        request = TaskRequest(
            adapter_key="xhs",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/not-xhs"),
        )

        envelope = execute_task(
            request,
            adapters={"xhs": XhsAdapter()},
            task_id_factory=lambda: "task-xhs-invalid-url",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_xhs_url")

    def test_execute_task_maps_real_douyin_invalid_url_to_invalid_input(self) -> None:
        seed_default_runtime_resources(adapter_key="douyin", account_resource_id="douyin-account-001")
        request = TaskRequest(
            adapter_key="douyin",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/not-douyin"),
        )

        envelope = execute_task(
            request,
            adapters={"douyin": DouyinAdapter()},
            task_id_factory=lambda: "task-douyin-invalid-url",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_douyin_url")

    def test_execute_task_maps_explicit_pre_platform_adapter_error_to_invalid_input(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": PrePlatformValidationAdapter()},
            task_id_factory=lambda: "task-preplatform-invalid-input",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "adapter_precheck_failed")

    def test_execute_task_rejects_empty_task_id_from_factory(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: "",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertIsInstance(envelope["task_id"], str)
        self.assertTrue(envelope["task_id"])
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_task_id")

    def test_execute_task_rejects_non_string_task_id_from_factory(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: 123,  # type: ignore[return-value]
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertIsInstance(envelope["task_id"], str)
        self.assertTrue(envelope["task_id"])
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_task_id")

    def test_execute_task_fails_closed_when_task_id_factory_raises(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertIsInstance(envelope["task_id"], str)
        self.assertTrue(envelope["task_id"])
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_task_id")

    def test_execute_task_rejects_extended_task_input_shape(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=ExtendedTaskInput(
                url="https://example.com/posts/1",
                platform_hint="xhs",
            ),
        )

        envelope = execute_task(
            request,
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: "task-extra-shape",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_rejects_extended_task_request_shape(self) -> None:
        request = ExtendedTaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
            extra="leaks",
        )

        envelope = execute_task(
            request,
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: "task-extra-request-shape",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_fails_closed_for_malformed_request_mapping(self) -> None:
        envelope = execute_task(
            {
                "adapter_key": "stub",
                "capability": "content_detail_by_url",
                "input": {"url": "https://example.com/posts/1"},
            },  # type: ignore[arg-type]
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: "task-malformed-request",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["task_id"], "task-malformed-request")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_fails_closed_for_request_mapping_that_raises_on_get(self) -> None:
        envelope = execute_task(
            ExplodingRequestMapping(),
            adapters={"stub": SuccessfulAdapter()},
            task_id_factory=lambda: "task-exploding-request",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["task_id"], "task-exploding-request")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_fails_closed_for_none_supported_capabilities(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": NoneCapabilitiesAdapter()},
            task_id_factory=lambda: "task-none-caps",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_capabilities")

    def test_execute_task_fails_closed_for_missing_supported_capabilities(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": MissingCapabilitiesAdapter()},
            task_id_factory=lambda: "task-missing-caps",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_capabilities")

    def test_execute_task_fails_closed_for_adapter_registry_that_raises_on_items(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters=ExplodingAdapterRegistry(),
            task_id_factory=lambda: "task-exploding-registry",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_registry")

    def test_execute_task_fails_closed_for_duplicate_adapter_registry_keys(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters=DuplicateAdapterRegistry(SuccessfulAdapter()),
            task_id_factory=lambda: "task-duplicate-registry",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["task_id"], "task-duplicate-registry")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_registry")

    def test_execute_task_fails_closed_for_non_container_supported_capabilities(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": NonContainerCapabilitiesAdapter()},
            task_id_factory=lambda: "task-non-container-caps",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_capabilities")

    def test_execute_task_fails_closed_for_non_string_supported_capability(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": NonStringCapabilitiesAdapter()},
            task_id_factory=lambda: "task-non-string-caps",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_capabilities")

    def test_execute_task_fails_closed_for_broken_supported_capabilities_iterable(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": BrokenIterableCapabilitiesAdapter()},
            task_id_factory=lambda: "task-broken-caps",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_capabilities")

    def test_execute_task_fails_closed_for_missing_execute_contract(self) -> None:
        request = TaskRequest(
            adapter_key="stub",
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={"stub": MissingExecuteAdapter()},
            task_id_factory=lambda: "task-missing-execute",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_declaration")


if __name__ == "__main__":
    unittest.main()
