from __future__ import annotations

import os
import json
import tempfile
import unittest
from unittest import mock

import syvert.runtime as runtime_module
from syvert.runtime import TaskInput, TaskRequest, execute_task, execute_task_with_record
from syvert.task_record import (
    TaskRecordContractError,
    TaskRequestSnapshot,
    create_task_record,
    finish_task_record,
    start_task_record,
    task_record_from_dict,
    task_record_to_dict,
)
from tests.runtime.resource_fixtures import ResourceStoreEnvMixin, baseline_resource_requirement_declarations

TEST_ADAPTER_KEY = "xhs"


def make_collection_result(
    *,
    operation: str = "content_search_by_keyword",
    target_type: str = "keyword",
    target_ref: str = "deep learning",
) -> dict[str, object]:
    return {
        "operation": operation,
        "target": {
            "operation": operation,
            "target_type": target_type,
            "target_ref": target_ref,
            "target_display_hint": target_ref,
        },
        "items": [
            {
                "item_type": "content_summary",
                "dedup_key": f"{operation}:item-1",
                "source_id": "source-1",
                "source_ref": "content://item-1",
                "normalized": {
                    "source_platform": TEST_ADAPTER_KEY,
                    "source_type": "post",
                    "source_id": "source-1",
                    "canonical_ref": "content://item-1",
                    "title_or_text_hint": "hint-1",
                    "creator_ref": "creator-1",
                    "published_at": "2026-05-09T10:00:00Z",
                    "media_refs": ["media://1"],
                },
                "raw_payload_ref": "raw://item-1",
                "source_trace": {
                    "adapter_key": TEST_ADAPTER_KEY,
                    "provider_path": "provider://sanitized",
                    "resource_profile_ref": "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                    "fetched_at": "2026-05-09T10:00:00Z",
                    "evidence_alias": "alias://collection-page-1",
                },
            }
        ],
        "has_more": False,
        "next_continuation": None,
        "result_status": "complete",
        "error_classification": "platform_failed",
        "raw_payload_ref": "raw://page-1",
        "source_trace": {
            "adapter_key": TEST_ADAPTER_KEY,
            "provider_path": "provider://sanitized",
            "resource_profile_ref": "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
            "fetched_at": "2026-05-09T10:00:00Z",
            "evidence_alias": "alias://collection-page-1",
        },
        "audit": {"page_index": 1},
    }


def make_comment_collection_result(*, target_ref: str = "content-001") -> dict[str, object]:
    return {
        "operation": "comment_collection",
        "target": {
            "operation": "comment_collection",
            "target_type": "content",
            "target_ref": target_ref,
            "target_display_hint": target_ref,
        },
        "items": [
            {
                "item_type": "comment",
                "dedup_key": "comment:root-1",
                "source_id": "root-1",
                "source_ref": "comment://root-1",
                "normalized": {
                    "source_platform": TEST_ADAPTER_KEY,
                    "source_type": "comment",
                    "source_id": "root-1",
                    "canonical_ref": "comment:root-1",
                    "body_text_hint": "root comment",
                    "author_ref": "creator-1",
                    "published_at": "2026-05-09T10:00:00Z",
                    "root_comment_ref": "comment:root-1",
                    "parent_comment_ref": None,
                    "target_comment_ref": None,
                },
                "visibility_status": "visible",
                "reply_cursor": None,
                "raw_payload_ref": "raw://comment/root-1",
                "source_trace": {
                    "adapter_key": TEST_ADAPTER_KEY,
                    "provider_path": "provider://sanitized",
                    "resource_profile_ref": "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                    "fetched_at": "2026-05-09T10:00:00Z",
                    "evidence_alias": "alias://comment-page-1",
                },
            }
        ],
        "has_more": False,
        "next_continuation": None,
        "result_status": "partial_result",
        "error_classification": "parse_failed",
        "raw_payload_ref": "raw://comment/page-1",
        "source_trace": {
            "adapter_key": TEST_ADAPTER_KEY,
            "provider_path": "provider://sanitized",
            "resource_profile_ref": "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
            "fetched_at": "2026-05-09T10:00:00Z",
            "evidence_alias": "alias://comment-page-1",
        },
        "audit": {"page_index": 1},
    }


def make_creator_profile_result(*, target_ref: str = "creator-001", creator_id: str = "creator-001") -> dict[str, object]:
    return {
        "operation": "creator_profile_by_id",
        "target": {
            "operation": "creator_profile_by_id",
            "target_type": "creator",
            "creator_ref": target_ref,
            "target_display_hint": "creator-hint-001",
            "policy_ref": "policy:creator-profile",
        },
        "result_status": "complete",
        "error_classification": None,
        "profile": {
            "creator_ref": creator_id,
            "canonical_ref": f"creator:canonical:{creator_id}",
            "display_name": "creator-name",
            "avatar_ref": "avatar:creator-001",
            "description": "desc",
            "public_counts": {
                "follower_count": 100,
                "following_count": 5,
                "content_count": 8,
                "like_count": 16,
            },
            "profile_url_hint": "profile:creator-slug",
        },
        "raw_payload_ref": "raw://creator-profile",
        "source_trace": {
            "adapter_key": TEST_ADAPTER_KEY,
            "provider_path": "provider://sanitized",
            "resource_profile_ref": "fr-0405:profile:creator-profile-by-id:account-proxy",
            "fetched_at": "2026-05-09T10:00:00Z",
            "evidence_alias": "alias://creator-profile-success",
        },
        "audit": {},
    }


def make_media_asset_fetch_result(*, target_ref: str = "media:asset-001") -> dict[str, object]:
    return {
        "operation": "media_asset_fetch_by_ref",
        "target": {
            "operation": "media_asset_fetch_by_ref",
            "target_type": "media_ref",
            "media_ref": target_ref,
        },
        "content_type": "image",
        "fetch_policy": {
            "fetch_mode": "metadata_only",
            "allowed_content_types": ["image", "video"],
            "allow_download": False,
            "max_bytes": None,
        },
        "fetch_outcome": "metadata_only",
        "result_status": "complete",
        "error_classification": None,
        "raw_payload_ref": "raw://media-asset-fetch/asset-001",
        "media": {
            "source_media_ref": f"source:{target_ref}",
            "source_ref_lineage": {
                "input_ref": target_ref,
                "source_media_ref": f"source:{target_ref}",
                "resolved_ref": f"resolved:{target_ref}",
                "canonical_ref": f"canonical:{target_ref}",
                "preservation_status": "preserved",
            },
            "canonical_ref": f"canonical:{target_ref}",
            "content_type": "image",
            "metadata": {"mime_type": "image/jpeg", "width": 1200, "height": 900},
        },
        "source_trace": {
            "adapter_key": TEST_ADAPTER_KEY,
            "provider_path": "provider://sanitized",
            "resource_profile_ref": "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
            "fetched_at": "2026-05-09T10:00:00Z",
            "evidence_alias": "alias://media-asset-fetch-1",
        },
        "audit": {},
    }


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


class SuccessfulAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(adapter_key=TEST_ADAPTER_KEY)

    def execute(self, request):
        return {
            "raw": {"id": "raw-1"},
            "normalized": {
                "platform": TEST_ADAPTER_KEY,
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


class PlatformFailureAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(adapter_key=TEST_ADAPTER_KEY)

    def execute(self, request):
        from syvert.runtime import PlatformAdapterError

        raise PlatformAdapterError(
            code="platform_broken",
            message="boom",
            details={"reason": "bad"},
        )


class UnsupportedCapabilityAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"creator_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request):
        raise AssertionError("execute should not be called")


class UnserializableSuccessAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(adapter_key=TEST_ADAPTER_KEY)

    def execute(self, request):
        return {
            "raw": {"id": "raw-bad", "bad": object()},
            "normalized": {
                "platform": TEST_ADAPTER_KEY,
                "content_id": "content-bad",
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


class OffsetTimestampSuccessAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(adapter_key=TEST_ADAPTER_KEY)

    def execute(self, request):
        return {
            "raw": {"id": "raw-offset-1"},
            "normalized": {
                "platform": TEST_ADAPTER_KEY,
                "content_id": "content-offset-1",
                "content_type": "unknown",
                "canonical_url": request.input.url,
                "title": "",
                "body_text": "",
                "published_at": "2026-04-17T10:30:00+00:00",
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


class CollectionSearchAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_search"})
    supported_targets = frozenset({"keyword"})
    supported_collection_modes = frozenset({"paginated"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(
        adapter_key=TEST_ADAPTER_KEY,
        capability="content_search",
    )

    def execute(self, request):
        return make_collection_result(target_ref=request.input.keyword or "")


class CommentCollectionAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"comment_collection"})
    supported_targets = frozenset({"content"})
    supported_collection_modes = frozenset({"paginated"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(
        adapter_key=TEST_ADAPTER_KEY,
        capability="comment_collection",
    )

    def execute(self, request):
        return make_comment_collection_result(target_ref=request.input.content_ref or "")


class CreatorProfileAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"creator_profile"})
    supported_targets = frozenset({"creator"})
    supported_collection_modes = frozenset({"direct"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(
        adapter_key=TEST_ADAPTER_KEY,
        capability="creator_profile",
    )

    def execute(self, request):
        return make_creator_profile_result(target_ref=request.input.creator_id or "")


class MediaAssetFetchAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"media_asset_fetch"})
    supported_targets = frozenset({"media_ref"})
    supported_collection_modes = frozenset({"direct"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(
        adapter_key=TEST_ADAPTER_KEY,
        capability="media_asset_fetch",
    )

    def execute(self, request):
        return make_media_asset_fetch_result(target_ref=request.input.media_ref or "")


class TaskRecordCodecTests(TaskRecordStoreEnvMixin, unittest.TestCase):
    def make_batch_record(self):
        request = TaskRequestSnapshot(
            adapter_key="core",
            capability="batch_execution",
            target_type="operation_batch",
            target_value="batch-001",
            collection_mode="batch",
        )
        record = start_task_record(
            create_task_record(
                "task-record-batch-1",
                request=request,
                occurred_at="2026-05-16T10:00:00Z",
            ),
            occurred_at="2026-05-16T10:00:01Z",
        )
        return finish_task_record(
            record,
            {
                "task_id": "task-record-batch-1",
                "adapter_key": "core",
                "capability": "batch_execution",
                "status": "success",
                "task_record_ref": "task_record:task-record-batch-1",
                "batch_id": "batch-001",
                "operation": "batch_execution",
                "result_status": "complete",
                "dataset_sink_ref": "sink:reference",
                "dataset_id": "dataset:batch-001",
                "item_outcomes": [
                    {
                        "item_id": "item-1",
                        "operation": "content_search_by_keyword",
                        "adapter_key": TEST_ADAPTER_KEY,
                        "target_ref": "deep learning",
                        "outcome_status": "succeeded",
                        "result_envelope": {
                            "task_id": "batch-item-1",
                            "adapter_key": TEST_ADAPTER_KEY,
                            "capability": "content_search_by_keyword",
                            "status": "success",
                            **make_collection_result(target_ref="deep learning"),
                        },
                        "dataset_record_ref": "dataset:batch-001:item-1",
                        "source_trace": {
                            "adapter_key": TEST_ADAPTER_KEY,
                            "provider_path": "provider://sanitized",
                            "fetched_at": "2026-05-16T10:00:01Z",
                            "evidence_alias": "alias://batch-item-1",
                        },
                        "audit": {"reason": "dataset_record_written"},
                    }
                ],
                "audit_trace": {
                    "batch_id": "batch-001",
                    "started_at": "2026-05-16T10:00:00Z",
                    "finished_at": "2026-05-16T10:00:01Z",
                    "finished": True,
                    "item_count": 1,
                    "item_trace_refs": ["audit:batch:batch-001:item-1"],
                    "evidence_refs": ["evidence:batch:item"],
                },
            },
            occurred_at="2026-05-16T10:00:02Z",
        )

    def test_round_trips_success_record(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/1"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-1",
        )

        self.assertEqual(outcome.envelope["status"], "success")
        self.assertIsNotNone(outcome.task_record)

        payload = task_record_to_dict(outcome.task_record)
        restored = task_record_from_dict(payload)

        self.assertEqual(restored, outcome.task_record)
        self.assertEqual(restored.status, "succeeded")

    def test_round_trips_batch_execution_record(self) -> None:
        record = self.make_batch_record()

        payload = task_record_to_dict(record)
        restored = task_record_from_dict(payload)

        self.assertEqual(restored, record)
        self.assertEqual(restored.request.capability, "batch_execution")
        self.assertEqual(restored.request.target_type, "operation_batch")
        self.assertEqual(restored.request.collection_mode, "batch")
        self.assertEqual(restored.result.envelope["operation"], "batch_execution")
        self.assertEqual(restored.result.envelope["item_outcomes"][0]["dataset_record_ref"], "dataset:batch-001:item-1")
        self.assertNotIn("request_cursor_context", repr(payload))

    def test_rejects_batch_execution_result_status_drift(self) -> None:
        payload = task_record_to_dict(self.make_batch_record())
        payload["result"]["envelope"]["result_status"] = "all_failed"

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_rejects_batch_execution_top_level_raw_payload(self) -> None:
        payload = task_record_to_dict(self.make_batch_record())
        payload["result"]["envelope"]["raw"] = {"provider_batch": True}

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_round_trips_comment_collection_record(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="comment_collection",
                input=TaskInput(content_ref="content-001"),
            ),
            adapters={TEST_ADAPTER_KEY: CommentCollectionAdapter()},
            task_id_factory=lambda: "task-record-comment-collection-1",
        )

        self.assertEqual(outcome.envelope["status"], "success")
        self.assertEqual(outcome.envelope["operation"], "comment_collection")
        self.assertIsNotNone(outcome.task_record)

        payload = task_record_to_dict(outcome.task_record)
        restored = task_record_from_dict(payload)

        self.assertEqual(restored, outcome.task_record)
        self.assertEqual(restored.request.capability, "comment_collection")
        self.assertEqual(restored.request.target_type, "content")
        self.assertEqual(restored.request.target_value, "content-001")

    def test_round_trips_media_asset_fetch_record(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="media_asset_fetch_by_ref",
                input=TaskInput(media_ref="media:asset-001"),
            ),
            adapters={TEST_ADAPTER_KEY: MediaAssetFetchAdapter()},
            task_id_factory=lambda: "task-record-media-asset-fetch-1",
        )

        self.assertEqual(outcome.envelope["status"], "success")
        self.assertEqual(outcome.envelope["operation"], "media_asset_fetch_by_ref")
        self.assertIsNotNone(outcome.task_record)

        payload = task_record_to_dict(outcome.task_record)
        restored = task_record_from_dict(payload)

        self.assertEqual(restored, outcome.task_record)
        self.assertEqual(restored.request.capability, "media_asset_fetch_by_ref")
        self.assertEqual(restored.request.target_type, "media_ref")
        self.assertEqual(restored.request.target_value, "media:asset-001")

    def test_round_trips_creator_profile_record(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="creator_profile_by_id",
                input=TaskInput(creator_id="creator-001"),
            ),
            adapters={TEST_ADAPTER_KEY: CreatorProfileAdapter()},
            task_id_factory=lambda: "task-record-creator-profile-1",
        )

        self.assertEqual(outcome.envelope["status"], "success")
        self.assertEqual(outcome.envelope["operation"], "creator_profile_by_id")
        self.assertIsNotNone(outcome.task_record)

        payload = task_record_to_dict(outcome.task_record)
        restored = task_record_from_dict(payload)

        self.assertEqual(restored, outcome.task_record)
        self.assertEqual(restored.request.capability, "creator_profile_by_id")
        self.assertEqual(restored.request.target_type, "creator")
        self.assertEqual(restored.request.target_value, "creator-001")

    def test_round_trips_creator_profile_optional_target_refs(self) -> None:
        request = TaskRequestSnapshot(
            adapter_key=TEST_ADAPTER_KEY,
            capability="creator_profile_by_id",
            target_type="creator",
            target_value="creator-001",
            collection_mode="direct",
        )
        record = start_task_record(
            create_task_record(
                "task-record-creator-profile-origin",
                request=request,
                occurred_at="2026-05-09T10:00:00Z",
            ),
            occurred_at="2026-05-09T10:00:00Z",
        )
        envelope = make_creator_profile_result(target_ref="creator-001")
        envelope["task_id"] = "task-record-creator-profile-origin"
        envelope["adapter_key"] = TEST_ADAPTER_KEY
        envelope["capability"] = "creator_profile_by_id"
        envelope["status"] = "success"
        record = finish_task_record(
            record,
            envelope,
            occurred_at="2026-05-09T10:00:01Z",
        )

        restored = task_record_from_dict(task_record_to_dict(record))

        self.assertEqual(restored, record)
        self.assertEqual(restored.result.envelope["target"]["target_display_hint"], "creator-hint-001")
        self.assertEqual(restored.result.envelope["target"]["policy_ref"], "policy:creator-profile")

    def test_rejects_private_creator_profile_request_snapshot(self) -> None:
        with self.assertRaises(TaskRecordContractError):
            create_task_record(
                "task-record-creator-private-ref",
                TaskRequestSnapshot(
                    adapter_key=TEST_ADAPTER_KEY,
                    capability="creator_profile_by_id",
                    target_type="creator",
                    target_value="https://xhs.example.invalid/user/1",
                    collection_mode="direct",
                ),
                occurred_at="2026-05-09T10:00:00Z",
            )

    def test_rejects_creator_profile_non_empty_audit(self) -> None:
        request = TaskRequestSnapshot(
            adapter_key=TEST_ADAPTER_KEY,
            capability="creator_profile_by_id",
            target_type="creator",
            target_value="creator-001",
            collection_mode="direct",
        )
        record = start_task_record(
            create_task_record(
                "task-record-creator-profile-audit",
                request=request,
                occurred_at="2026-05-09T10:00:00Z",
            ),
            occurred_at="2026-05-09T10:00:00Z",
        )
        envelope = make_creator_profile_result(target_ref="creator-001")
        envelope["audit"] = {"transfer_observed": True}
        envelope["task_id"] = "task-record-creator-profile-audit"
        envelope["adapter_key"] = TEST_ADAPTER_KEY
        envelope["capability"] = "creator_profile_by_id"
        envelope["status"] = "success"

        with self.assertRaises(TaskRecordContractError):
            finish_task_record(record, envelope, occurred_at="2026-05-09T10:00:01Z")

    def test_round_trips_media_asset_fetch_parse_failed_record(self) -> None:
        request = TaskRequestSnapshot(
            adapter_key=TEST_ADAPTER_KEY,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-parse",
            collection_mode="direct",
        )
        record = start_task_record(
            create_task_record(
                "task-record-media-asset-fetch-parse",
                request=request,
                occurred_at="2026-05-09T10:00:00Z",
            ),
            occurred_at="2026-05-09T10:00:00Z",
        )
        envelope = make_media_asset_fetch_result(target_ref="media:asset-parse")
        envelope["content_type"] = "unknown"
        envelope["fetch_outcome"] = None
        envelope["result_status"] = "failed"
        envelope["error_classification"] = "parse_failed"
        envelope["media"] = None
        envelope["raw_payload_ref"] = "raw://media-asset-fetch/parse-failed"
        envelope["task_id"] = "task-record-media-asset-fetch-parse"
        envelope["adapter_key"] = TEST_ADAPTER_KEY
        envelope["capability"] = "media_asset_fetch_by_ref"
        envelope["status"] = "success"
        record = finish_task_record(
            record,
            envelope,
            occurred_at="2026-05-09T10:00:01Z",
        )

        restored = task_record_from_dict(task_record_to_dict(record))

        self.assertEqual(restored, record)
        self.assertEqual(restored.result.envelope["error_classification"], "parse_failed")

    def test_round_trips_media_asset_fetch_optional_target_refs(self) -> None:
        request = TaskRequestSnapshot(
            adapter_key=TEST_ADAPTER_KEY,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-origin",
            collection_mode="direct",
        )
        record = start_task_record(
            create_task_record(
                "task-record-media-asset-fetch-origin",
                request=request,
                occurred_at="2026-05-09T10:00:00Z",
            ),
            occurred_at="2026-05-09T10:00:00Z",
        )
        envelope = make_media_asset_fetch_result(target_ref="media:asset-origin")
        envelope["target"]["origin_ref"] = "origin:content-001"
        envelope["target"]["policy_ref"] = "policy:media-metadata"
        envelope["task_id"] = "task-record-media-asset-fetch-origin"
        envelope["adapter_key"] = TEST_ADAPTER_KEY
        envelope["capability"] = "media_asset_fetch_by_ref"
        envelope["status"] = "success"
        record = finish_task_record(
            record,
            envelope,
            occurred_at="2026-05-09T10:00:01Z",
        )

        restored = task_record_from_dict(task_record_to_dict(record))

        self.assertEqual(restored, record)
        self.assertEqual(restored.result.envelope["target"]["origin_ref"], "origin:content-001")
        self.assertEqual(restored.result.envelope["target"]["policy_ref"], "policy:media-metadata")

    def test_rejects_media_asset_fetch_no_storage_field(self) -> None:
        request = TaskRequestSnapshot(
            adapter_key=TEST_ADAPTER_KEY,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-storage",
            collection_mode="direct",
        )
        record = start_task_record(
            create_task_record(
                "task-record-media-asset-fetch-storage",
                request=request,
                occurred_at="2026-05-09T10:00:00Z",
            ),
            occurred_at="2026-05-09T10:00:00Z",
        )
        envelope = make_media_asset_fetch_result(target_ref="media:asset-storage")
        envelope["no_storage"] = {"stored": False}
        envelope["task_id"] = "task-record-media-asset-fetch-storage"
        envelope["adapter_key"] = TEST_ADAPTER_KEY
        envelope["capability"] = "media_asset_fetch_by_ref"
        envelope["status"] = "success"

        with self.assertRaises(TaskRecordContractError):
            finish_task_record(record, envelope, occurred_at="2026-05-09T10:00:01Z")

    def test_rejects_media_asset_fetch_record_policy_violation(self) -> None:
        request = TaskRequestSnapshot(
            adapter_key=TEST_ADAPTER_KEY,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-policy",
            collection_mode="direct",
        )
        record = start_task_record(
            create_task_record(
                "task-record-media-asset-fetch-policy",
                request=request,
                occurred_at="2026-05-09T10:00:00Z",
            ),
            occurred_at="2026-05-09T10:00:00Z",
        )
        envelope = make_media_asset_fetch_result(target_ref="media:asset-policy")
        envelope["content_type"] = "video"
        envelope["media"]["content_type"] = "video"
        envelope["fetch_policy"]["allowed_content_types"] = ["image"]

        with self.assertRaises(TaskRecordContractError):
            finish_task_record(record, envelope, occurred_at="2026-05-09T10:00:01Z")

    def test_rejects_private_media_asset_fetch_request_snapshot(self) -> None:
        with self.assertRaises(TaskRecordContractError):
            create_task_record(
                "task-record-media-private-ref",
                TaskRequestSnapshot(
                    adapter_key=TEST_ADAPTER_KEY,
                    capability="media_asset_fetch_by_ref",
                    target_type="media_ref",
                    target_value="https://signed.example.invalid/media?token=secret",
                    collection_mode="direct",
                ),
                occurred_at="2026-05-09T10:00:00Z",
            )

    def test_rejects_missing_required_lifecycle_event(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/2"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-2",
        )
        payload = task_record_to_dict(outcome.task_record)
        payload["logs"] = payload["logs"][:-1]

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_rejects_conflicting_observability_replay_id(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/observability-conflict"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-observability-conflict",
        )
        payload = task_record_to_dict(outcome.task_record)
        duplicate_event = dict(payload["runtime_structured_log_events"][0])
        duplicate_event["message"] = "conflicting replay"
        payload["runtime_structured_log_events"].append(duplicate_event)

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_rejects_invalid_runtime_observability_enum_values(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/observability-enum"),
            ),
            adapters={TEST_ADAPTER_KEY: PlatformFailureAdapter()},
            task_id_factory=lambda: "task-record-observability-enum",
        )
        payload = json.loads(json.dumps(task_record_to_dict(outcome.task_record)))

        invalid_signal = json.loads(json.dumps(task_record_to_dict(outcome.task_record)))
        invalid_signal["runtime_failure_signals"][0]["failure_phase"] = "not_approved"
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(invalid_signal)

        invalid_event = json.loads(json.dumps(task_record_to_dict(outcome.task_record)))
        invalid_event["runtime_structured_log_events"][0]["event_type"] = "not_approved"
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(invalid_event)

        invalid_metric = payload
        invalid_metric["runtime_execution_metric_samples"][0]["metric_name"] = "not_approved"
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(invalid_metric)

    def test_rejects_failed_observability_without_required_signal_or_error_metadata(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/observability-required-fields"),
            ),
            adapters={TEST_ADAPTER_KEY: PlatformFailureAdapter()},
            task_id_factory=lambda: "task-record-observability-required-fields",
        )
        payload = json.loads(json.dumps(task_record_to_dict(outcome.task_record)))

        missing_signal_id = json.loads(json.dumps(payload))
        missing_signal_id["runtime_failure_signals"][0]["signal_id"] = ""
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(missing_signal_id)

        missing_signal_ref = json.loads(json.dumps(payload))
        failed_event = next(
            event
            for event in missing_signal_ref["runtime_structured_log_events"]
            if event["event_type"] == "task_failed"
        )
        failed_event["failure_signal_id"] = ""
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(missing_signal_ref)

        for event_type in ("retry_scheduled", "observability_write_failed"):
            with self.subTest(event_type=event_type):
                missing_event_signal_ref = json.loads(json.dumps(payload))
                failed_event = next(
                    event
                    for event in missing_event_signal_ref["runtime_structured_log_events"]
                    if event["event_type"] == "task_failed"
                )
                extra_event = dict(failed_event)
                extra_event["event_id"] = f"runtime_log_event:required-fields:{event_type}"
                extra_event["event_type"] = event_type
                extra_event["failure_signal_id"] = ""
                missing_event_signal_ref["runtime_structured_log_events"].append(extra_event)
                with self.assertRaises(TaskRecordContractError):
                    task_record_from_dict(missing_event_signal_ref)

        missing_error_metadata = json.loads(json.dumps(payload))
        failed_metric = next(
            metric
            for metric in missing_error_metadata["runtime_execution_metric_samples"]
            if metric["metric_name"] == "task_failed_total"
        )
        failed_metric["error_category"] = ""
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(missing_error_metadata)

        missing_failure_phase = json.loads(json.dumps(payload))
        failed_metric = next(
            metric
            for metric in missing_failure_phase["runtime_execution_metric_samples"]
            if metric["metric_name"] == "task_failed_total"
        )
        failed_metric["failure_phase"] = ""
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(missing_failure_phase)

        missing_error_code = json.loads(json.dumps(payload))
        failed_metric = next(
            metric
            for metric in missing_error_code["runtime_execution_metric_samples"]
            if metric["metric_name"] == "task_failed_total"
        )
        failed_metric["error_code"] = ""
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(missing_error_code)

        for metric_name in (
            "timeout_total",
            "admission_concurrency_rejected_total",
            "retry_concurrency_rejected_total",
        ):
            with self.subTest(metric_name=metric_name):
                missing_metric_metadata = json.loads(json.dumps(payload))
                failed_metric = next(
                    metric
                    for metric in missing_metric_metadata["runtime_execution_metric_samples"]
                    if metric["metric_name"] == "task_failed_total"
                )
                extra_metric = dict(failed_metric)
                extra_metric["metric_id"] = f"runtime_metric_sample:required-fields:{metric_name}"
                extra_metric["metric_name"] = metric_name
                extra_metric["error_category"] = ""
                missing_metric_metadata["runtime_execution_metric_samples"].append(extra_metric)
                with self.assertRaises(TaskRecordContractError):
                    task_record_from_dict(missing_metric_metadata)

        invalid_signal_resource_refs = json.loads(json.dumps(payload))
        invalid_signal_resource_refs["runtime_failure_signals"][0]["resource_trace_refs"] = [{"bogus": "value"}]
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(invalid_signal_resource_refs)

        invalid_signal_runtime_refs = json.loads(json.dumps(payload))
        invalid_signal_runtime_refs["runtime_failure_signals"][0]["runtime_result_refs"] = [{"bogus": "value"}]
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(invalid_signal_runtime_refs)

        invalid_log_resource_refs = json.loads(json.dumps(payload))
        failed_event = next(
            event
            for event in invalid_log_resource_refs["runtime_structured_log_events"]
            if event["event_type"] == "task_failed"
        )
        failed_event["resource_trace_refs"] = [{"bogus": "value"}]
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(invalid_log_resource_refs)

        invalid_log_runtime_refs = json.loads(json.dumps(payload))
        failed_event = next(
            event
            for event in invalid_log_runtime_refs["runtime_structured_log_events"]
            if event["event_type"] == "task_failed"
        )
        failed_event["runtime_result_refs"] = [{"bogus": "value"}]
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(invalid_log_runtime_refs)

    def test_migrates_missing_and_rejects_mismatched_task_record_ref(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/ref"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-ref-1",
        )
        payload = task_record_to_dict(outcome.task_record)

        missing_ref = dict(payload)
        missing_ref.pop("task_record_ref")
        restored = task_record_from_dict(missing_ref)
        self.assertEqual(restored.task_record_ref, "task_record:task-record-ref-1")

        mismatched_ref = dict(payload)
        mismatched_ref["task_record_ref"] = "task_record:other"
        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(mismatched_ref)

    def test_rejects_mismatched_terminal_observability_fields(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/observability"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-observability-1",
        )
        payload = task_record_to_dict(outcome.task_record)

        for field, value in (
            ("task_record_ref", "task_record:other"),
            ("runtime_result_refs", [{"kind": "artifact", "id": "other"}]),
            ("execution_control_events", [{"event": "other"}]),
        ):
            with self.subTest(field=field):
                corrupted = dict(payload)
                corrupted["result"] = {
                    "envelope": dict(payload["result"]["envelope"]),
                }
                corrupted["result"]["envelope"][field] = value
                with self.assertRaises(TaskRecordContractError):
                    task_record_from_dict(corrupted)

    def test_accepts_idempotent_terminal_rewrite_and_rejects_conflicting_terminal(self) -> None:
        snapshot = TaskRequestSnapshot(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            target_type="url",
            target_value="https://example.com/post/3",
            collection_mode="hybrid",
        )
        accepted = create_task_record("task-record-3", snapshot, occurred_at="2026-04-17T10:30:00Z")
        running = start_task_record(accepted, occurred_at="2026-04-17T10:30:01Z")
        envelope = {
            "task_id": "task-record-3",
            "adapter_key": TEST_ADAPTER_KEY,
            "capability": "content_detail_by_url",
            "status": "failed",
            "error": {
                "category": "platform",
                "code": "platform_broken",
                "message": "boom",
                "details": {"reason": "bad"},
            },
        }
        failed = finish_task_record(running, envelope, occurred_at="2026-04-17T10:30:02Z")

        self.assertEqual(finish_task_record(failed, envelope), failed)

        conflicting = dict(envelope)
        conflicting["error"] = dict(envelope["error"])
        conflicting["error"]["code"] = "changed"
        with self.assertRaises(TaskRecordContractError):
            finish_task_record(failed, conflicting)

    def test_rejects_invalid_scalar_types_during_round_trip_load(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/3b"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-3b",
        )
        payload = task_record_to_dict(outcome.task_record)
        payload["task_id"] = 123

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_rejects_terminal_envelope_mismatch_during_round_trip_load(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/3c"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-3c",
        )
        payload = task_record_to_dict(outcome.task_record)
        payload["result"]["envelope"]["task_id"] = "task-record-other"

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_rejects_success_envelope_nested_type_drift_during_round_trip_load(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/3cc"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-3cc",
        )
        payload = task_record_to_dict(outcome.task_record)
        payload["result"]["envelope"]["normalized"]["author"]["author_id"] = 123
        payload["result"]["envelope"]["normalized"]["stats"]["like_count"] = "1"
        payload["result"]["envelope"]["normalized"]["media"]["image_urls"] = [1]

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_rejects_failed_envelope_without_details_during_round_trip_load(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/3cf"),
            ),
            adapters={TEST_ADAPTER_KEY: PlatformFailureAdapter()},
            task_id_factory=lambda: "task-record-3cf",
        )
        payload = task_record_to_dict(outcome.task_record)
        del payload["result"]["envelope"]["error"]["details"]

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_rejects_failed_envelope_with_invalid_category_during_round_trip_load(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/3cg"),
            ),
            adapters={TEST_ADAPTER_KEY: PlatformFailureAdapter()},
            task_id_factory=lambda: "task-record-3cg",
        )
        payload = task_record_to_dict(outcome.task_record)
        payload["result"]["envelope"]["error"]["category"] = "broken"

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_rejects_untrusted_timeline_during_round_trip_load(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/3d"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-3d",
        )
        payload = task_record_to_dict(outcome.task_record)
        payload["logs"][1]["occurred_at"] = "2026-04-17T10:29:59Z"

        with self.assertRaises(TaskRecordContractError):
            task_record_from_dict(payload)

    def test_rejects_snapshot_values_outside_shared_request_model(self) -> None:
        with self.assertRaises(TaskRecordContractError):
            create_task_record(
                "task-record-3e",
                TaskRequestSnapshot(
                    adapter_key=TEST_ADAPTER_KEY,
                    capability="content_detail_by_url",
                    target_type="unsupported",
                    target_value="https://example.com/post/3e",
                    collection_mode="hybrid",
                ),
            )


class RuntimeTaskRecordTests(TaskRecordStoreEnvMixin, unittest.TestCase):
    def test_execute_task_with_record_round_trips_collection_search_record(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_search_by_keyword",
                input=TaskInput(keyword="deep learning"),
            ),
            adapters={TEST_ADAPTER_KEY: CollectionSearchAdapter()},
            task_id_factory=lambda: "task-record-collection-1",
        )

        payload = task_record_to_dict(outcome.task_record)
        restored = task_record_from_dict(payload)

        self.assertEqual(outcome.envelope["status"], "success")
        self.assertEqual(outcome.envelope["target"]["target_ref"], "deep learning")
        self.assertEqual(restored, outcome.task_record)
        self.assertEqual(restored.request.target_type, "keyword")

    def test_execute_task_with_record_keeps_preaccepted_failure_outside_durable_history(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/4"),
            ),
            adapters={TEST_ADAPTER_KEY: UnsupportedCapabilityAdapter()},
            task_id_factory=lambda: "task-record-4",
        )

        self.assertEqual(outcome.envelope["status"], "failed")
        self.assertEqual(outcome.envelope["error"]["code"], "capability_not_supported")
        self.assertIsNone(outcome.task_record)

    def test_execute_task_with_record_builds_failed_record_for_business_failure(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/5"),
            ),
            adapters={TEST_ADAPTER_KEY: PlatformFailureAdapter()},
            task_id_factory=lambda: "task-record-5",
        )

        self.assertEqual(outcome.envelope["status"], "failed")
        self.assertIsNotNone(outcome.task_record)
        self.assertEqual(outcome.task_record.status, "failed")
        self.assertEqual(outcome.task_record.result.envelope["error"]["code"], "platform_broken")

    def test_execute_task_with_record_builds_failed_record_for_unmatched_resource_capabilities(self) -> None:
        with mock.patch.dict(
            runtime_module.RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE,
            {(runtime_module.CONTENT_DETAIL_BY_URL, runtime_module.LEGACY_COLLECTION_MODE): ("proxy",)},
            clear=True,
        ), mock.patch(
            "syvert.runtime.acquire_runtime_resource_bundle",
            side_effect=AssertionError("acquire should not run when matcher is unmatched"),
        ):
            outcome = execute_task_with_record(
                TaskRequest(
                    adapter_key=TEST_ADAPTER_KEY,
                    capability="content_detail_by_url",
                    input=TaskInput(url="https://example.com/post/5b"),
                ),
                adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
                task_id_factory=lambda: "task-record-5b",
            )

        self.assertEqual(outcome.envelope["status"], "failed")
        self.assertEqual(outcome.envelope["error"]["code"], "resource_unavailable")
        self.assertIsNotNone(outcome.task_record)
        self.assertEqual(outcome.task_record.status, "failed")
        self.assertEqual(outcome.task_record.result.envelope["error"]["code"], "resource_unavailable")

    def test_execute_task_envelope_contract_stays_unchanged(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/6"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-6",
        )

        self.assertEqual(envelope["status"], "success")
        self.assertEqual(envelope["task_id"], "task-record-6")
        self.assertIn("raw", envelope)
        self.assertIn("normalized", envelope)

    def test_execute_task_preserves_stateless_replay_for_fixed_task_id(self) -> None:
        first = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/6b"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-6b",
        )
        second = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/6b"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-record-6b",
        )

        self.assertEqual(first["status"], "success")
        self.assertEqual(second["status"], "success")

    def test_execute_task_with_record_fails_closed_when_terminal_envelope_is_not_json_serializable(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/7"),
            ),
            adapters={TEST_ADAPTER_KEY: UnserializableSuccessAdapter()},
            task_id_factory=lambda: "task-record-7",
        )

        self.assertEqual(outcome.envelope["status"], "failed")
        self.assertEqual(outcome.envelope["error"]["code"], "envelope_not_json_serializable")
        self.assertEqual(outcome.envelope["runtime_failure_signal"]["failure_phase"], "persistence")
        self.assertEqual(outcome.envelope["runtime_failure_signal"]["task_record_ref"], "task_record:task-record-7")
        task_failed_log = next(
            event
            for event in outcome.envelope["runtime_structured_log_events"]
            if event["event_type"] == "task_failed"
        )
        self.assertEqual(task_failed_log["failure_signal_id"], outcome.envelope["runtime_failure_signal"]["signal_id"])
        task_failed_metric = next(
            metric
            for metric in outcome.envelope["runtime_execution_metric_samples"]
            if metric["metric_name"] == "task_failed_total"
        )
        self.assertEqual(task_failed_metric["error_code"], "envelope_not_json_serializable")
        self.assertIsNone(outcome.task_record)

    def test_execute_task_preserves_public_envelope_when_task_record_fails_to_close(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/8"),
            ),
            adapters={TEST_ADAPTER_KEY: UnserializableSuccessAdapter()},
            task_id_factory=lambda: "task-record-8",
        )

        self.assertEqual(envelope["status"], "success")
        self.assertEqual(envelope["task_id"], "task-record-8")
        self.assertIn("raw", envelope)
        self.assertEqual(type(envelope["raw"]["bad"]).__name__, "object")

    def test_execute_task_with_record_accepts_offset_utc_timestamp_in_success_payload(self) -> None:
        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/post/9"),
            ),
            adapters={TEST_ADAPTER_KEY: OffsetTimestampSuccessAdapter()},
            task_id_factory=lambda: "task-record-9",
        )

        self.assertEqual(outcome.envelope["status"], "success")
        self.assertIsNotNone(outcome.task_record)
        self.assertEqual(
            outcome.task_record.result.envelope["normalized"]["published_at"],
            "2026-04-17T10:30:00+00:00",
        )


if __name__ == "__main__":
    unittest.main()
