from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path
import tempfile
from dataclasses import dataclass, replace
from typing import Iterator, Tuple
import unittest
from unittest import mock

import syvert.runtime as runtime_module
from syvert.adapters.douyin import DouyinAdapter
from syvert.adapters.xhs import XhsAdapter
from syvert.registry import (
    AdapterResourceRequirementDeclaration,
    AdapterResourceRequirementDeclarationV2,
    AdapterResourceRequirementProfile,
    baseline_multi_profile_resource_requirement_declaration,
    baseline_required_resource_requirement_declaration,
)
from syvert.read_side_collection import CommentReplyCursor, CommentRequestCursor
from syvert.resource_lifecycle import ResourceRecord
from syvert.resource_lifecycle_store import LocalResourceLifecycleStore
from syvert.resource_lifecycle_store import default_resource_lifecycle_store
from syvert.resource_trace_store import LocalResourceTraceStore
from syvert.runtime import (
    AdapterExecutionContext,
    AdapterTaskRequest,
    CollectionPolicy,
    CoreTaskRequest,
    ExecutionConcurrencyPolicy,
    ExecutionControlPolicy,
    ExecutionRetryPolicy,
    ExecutionTimeoutPolicy,
    InputTarget,
    PlatformAdapterError,
    TaskInput,
    TaskRequest,
    execute_task,
    execute_task_with_record,
    validate_success_payload,
)
from tests.runtime.resource_fixtures import (
    ResourceStoreEnvMixin,
    baseline_resource_requirement_declarations,
    generic_account_material,
    managed_account_material,
    proxy_material,
    seed_default_runtime_resources,
)
from tests.runtime.contract_harness.third_party_entry import _build_success_runtime_envelope
from tests.runtime.contract_harness.validation_tool import (
    ContractSampleDefinition,
    HarnessExecutionResult,
    validate_contract_sample,
)

TEST_ADAPTER_KEY = "xhs"


def make_collection_result(
    *,
    operation: str,
    target_type: str,
    target_ref: str,
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
        },
        "items": [],
        "has_more": False,
        "next_continuation": None,
        "result_status": "empty",
        "error_classification": "empty_result",
        "raw_payload_ref": "raw://comment-page-empty",
        "source_trace": {
            "adapter_key": TEST_ADAPTER_KEY,
            "provider_path": "provider://sanitized",
            "resource_profile_ref": "profile://comment-collection-runtime-placeholder",
            "fetched_at": "2026-05-09T10:00:00Z",
            "evidence_alias": "alias://comment-page-empty",
        },
        "audit": {"page_index": 1},
    }


def make_media_asset_fetch_result(
    *,
    target_ref: str = "media:asset-001",
    content_type: str = "image",
    fetch_mode: str = "metadata_only",
    fetch_outcome: str | None = "metadata_only",
    result_status: str = "complete",
    error_classification: str | None = None,
) -> dict[str, object]:
    media = None
    if result_status == "complete":
        metadata: dict[str, object] = {"mime_type": "image/jpeg", "width": 1200, "height": 900}
        if fetch_outcome == "downloaded_bytes":
            metadata.update(
                {
                    "byte_size": 2048,
                    "checksum_digest": "sha256:abc123",
                    "checksum_family": "sha256",
                }
            )
        media = {
            "source_media_ref": f"source:{target_ref}",
            "source_ref_lineage": {
                "input_ref": target_ref,
                "source_media_ref": f"source:{target_ref}",
                "resolved_ref": f"resolved:{target_ref}",
                "canonical_ref": f"canonical:{target_ref}",
                "preservation_status": "preserved",
            },
            "canonical_ref": f"canonical:{target_ref}",
            "content_type": content_type,
            "metadata": metadata,
        }
    return {
        "operation": "media_asset_fetch_by_ref",
        "target": {
            "operation": "media_asset_fetch_by_ref",
            "target_type": "media_ref",
            "media_ref": target_ref,
        },
        "content_type": content_type,
        "fetch_policy": {
            "fetch_mode": fetch_mode,
            "allowed_content_types": ["image", "video"],
            "allow_download": fetch_outcome == "downloaded_bytes",
            "max_bytes": 4096 if fetch_outcome == "downloaded_bytes" else None,
        },
        "fetch_outcome": fetch_outcome,
        "result_status": result_status,
        "error_classification": error_classification,
        "raw_payload_ref": "raw://media-asset-fetch/asset-001",
        "media": media,
        "no_storage": {
            "stored": False,
            "downloaded_byte_length": 2048 if fetch_outcome == "downloaded_bytes" else 0,
            "retention_policy": "metadata_only",
        },
        "source_trace": {
            "adapter_key": TEST_ADAPTER_KEY,
            "provider_path": "provider://sanitized",
            "resource_profile_ref": "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
            "fetched_at": "2026-05-09T10:00:00Z",
            "evidence_alias": "alias://media-asset-fetch-1",
        },
        "audit": (
            {
                "transfer_observed": True,
                "byte_size": 2048,
                "checksum_digest": "sha256:abc123",
                "checksum_family": "sha256",
            }
            if fetch_outcome == "downloaded_bytes"
            else {}
        ),
    }


def make_comment_collection_reply_result(
    *,
    target_ref: str = "content-001",
    root_comment_ref: str = "comment:root-1",
) -> dict[str, object]:
    payload = make_comment_collection_result(target_ref=target_ref)
    payload["items"] = [
        {
            "item_type": "comment",
            "dedup_key": "comment:reply-1",
            "source_id": "reply-1",
            "source_ref": "source:comment:reply-1",
            "visibility_status": "visible",
            "normalized": {
                "source_platform": "reference-platform",
                "source_type": "comment",
                "source_id": "reply-1",
                "canonical_ref": "comment:reply-1",
                "body_text_hint": "reply",
                "root_comment_ref": root_comment_ref,
                "parent_comment_ref": root_comment_ref,
            },
            "raw_payload_ref": "raw:comment:reply-1",
            "source_trace": payload["source_trace"],
        }
    ]
    payload["result_status"] = "partial_result"
    payload["error_classification"] = "parse_failed"
    return payload


def make_comment_page_continuation(*, target_ref: str = "content-001") -> dict[str, object]:
    return {
        "continuation_token": "comment-page-cursor-1",
        "continuation_family": "opaque",
        "resume_target_ref": target_ref,
        "issued_at": "2026-05-09T10:00:00Z",
    }


def make_comment_reply_cursor(*, target_ref: str = "content-001", comment_ref: str = "comment:root-1") -> dict[str, object]:
    return {
        "reply_cursor_token": "reply-cursor-1",
        "reply_cursor_family": "opaque",
        "resume_target_ref": target_ref,
        "resume_comment_ref": comment_ref,
        "issued_at": "2026-05-09T10:00:00Z",
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


@dataclass(frozen=True)
class ExtendedTaskInput(TaskInput):
    platform_hint: str = ""


@dataclass(frozen=True)
class ExtendedTaskRequest(TaskRequest):
    extra: str = ""


class StubContentDetailDeclarationMixin:
    resource_requirement_declarations = baseline_resource_requirement_declarations(adapter_key=TEST_ADAPTER_KEY)


class SuccessfulAdapter(StubContentDetailDeclarationMixin):
    adapter_key = TEST_ADAPTER_KEY
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


class CollectionSearchAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_search"})
    supported_targets = frozenset({"keyword"})
    supported_collection_modes = frozenset({"paginated"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(
        adapter_key=TEST_ADAPTER_KEY,
        capability="content_search",
    )

    def execute(self, request: TaskRequest) -> dict[str, object]:
        self.last_request = request
        return make_collection_result(
            operation="content_search_by_keyword",
            target_type="keyword",
            target_ref=request.input.keyword or "",
        )


class CommentCollectionAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"comment_collection"})
    supported_targets = frozenset({"content"})
    supported_collection_modes = frozenset({"paginated"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(
        adapter_key=TEST_ADAPTER_KEY,
        capability="comment_collection",
    )

    def execute(self, request: TaskRequest) -> dict[str, object]:
        self.last_request = request
        return make_comment_collection_result(target_ref=request.input.content_ref or "")


class MediaAssetFetchAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"media_asset_fetch"})
    supported_targets = frozenset({"media_ref"})
    supported_collection_modes = frozenset({"direct"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(
        adapter_key=TEST_ADAPTER_KEY,
        capability="media_asset_fetch",
    )

    def execute(self, request: TaskRequest) -> dict[str, object]:
        self.last_request = request
        return make_media_asset_fetch_result(target_ref=request.input.media_ref or "")


class MediaAssetFetchLeakyStorageAdapter(MediaAssetFetchAdapter):
    def execute(self, request: TaskRequest) -> dict[str, object]:
        payload = make_media_asset_fetch_result(target_ref=request.input.media_ref or "")
        payload["no_storage"]["local_path"] = "forbidden-storage-ref"
        return payload


class MediaAssetFetchUnexpectedDownloadAdapter(MediaAssetFetchAdapter):
    def execute(self, request: TaskRequest) -> dict[str, object]:
        self.last_request = request
        return make_media_asset_fetch_result(
            target_ref=request.input.media_ref or "",
            fetch_mode="download_if_allowed",
            fetch_outcome="downloaded_bytes",
        )


class V1AccountOnlyMediaAssetFetchAdapter(MediaAssetFetchAdapter):
    resource_requirement_declarations = (
        AdapterResourceRequirementDeclaration(
            adapter_key=TEST_ADAPTER_KEY,
            capability="media_asset_fetch",
            resource_dependency_mode="required",
            required_capabilities=("account",),
            evidence_refs=(
                "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                "fr-0015:xhs:content-detail:url:hybrid:account-material",
            ),
        ),
    )


class MultiProfileMediaAssetFetchAdapter(MediaAssetFetchAdapter):
    resource_requirement_declarations = (
        baseline_multi_profile_resource_requirement_declaration(
            adapter_key=TEST_ADAPTER_KEY,
            capability="media_asset_fetch",
        ),
    )


class V1AccountOnlyCommentCollectionAdapter(CommentCollectionAdapter):
    resource_requirement_declarations = (
        AdapterResourceRequirementDeclaration(
            adapter_key=TEST_ADAPTER_KEY,
            capability="comment_collection",
            resource_dependency_mode="required",
            required_capabilities=("account",),
            evidence_refs=(
                "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                "fr-0015:xhs:content-detail:url:hybrid:account-material",
            ),
        ),
    )


class MutatingCommentCursorAdapter(CommentCollectionAdapter):
    def execute(self, request: TaskRequest) -> dict[str, object]:
        self.last_request = request
        cursor = request.request.request_cursor
        if isinstance(cursor, dict):
            reply_cursor = cursor.get("reply_cursor")
            if isinstance(reply_cursor, dict):
                reply_cursor["resume_comment_ref"] = "comment:other-root"
        return make_comment_collection_reply_result(root_comment_ref="comment:other-root")


def make_execution_control_policy(scope: str) -> ExecutionControlPolicy:
    return ExecutionControlPolicy(
        timeout=ExecutionTimeoutPolicy(timeout_ms=30000),
        retry=ExecutionRetryPolicy(max_attempts=1, backoff_ms=0),
        concurrency=ExecutionConcurrencyPolicy(scope=scope, max_in_flight=1, on_limit="reject"),
    )


class MissingRawAdapter(StubContentDetailDeclarationMixin):
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: TaskRequest) -> dict[str, object]:
        return {
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


class NonePayloadAdapter(StubContentDetailDeclarationMixin):
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: TaskRequest):
        return None


class ListPayloadAdapter(StubContentDetailDeclarationMixin):
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: TaskRequest):
        return []


class CrashingAdapter(StubContentDetailDeclarationMixin):
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: TaskRequest):
        raise RuntimeError("boom")


class PlatformErrorWithBadDetailsAdapter(StubContentDetailDeclarationMixin):
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: TaskRequest):
        from syvert.runtime import PlatformAdapterError

        raise PlatformAdapterError(code="platform_broken", message="bad details", details=None)


class PlatformFailureAdapter(StubContentDetailDeclarationMixin):
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: TaskRequest) -> dict[str, object]:
        raise PlatformAdapterError(
            code="content_not_found",
            message="content not found",
            details={"reason": "missing"},
        )


class InvalidatingHintAdapter(StubContentDetailDeclarationMixin):
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: AdapterExecutionContext) -> dict[str, object]:
        assert request.resource_bundle is not None
        return {
            "raw": {"id": "raw-invalid-hint"},
            "normalized": {
                "platform": TEST_ADAPTER_KEY,
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


class LeaseIdMismatchHintAdapter(StubContentDetailDeclarationMixin):
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: AdapterExecutionContext) -> dict[str, object]:
        return {
            "raw": {"id": "raw-bad-hint"},
            "normalized": {
                "platform": TEST_ADAPTER_KEY,
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


class InvalidTargetStatusHintAdapter(StubContentDetailDeclarationMixin):
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: AdapterExecutionContext) -> dict[str, object]:
        assert request.resource_bundle is not None
        return {
            "raw": {"id": "raw-bad-status-hint"},
            "normalized": {
                "platform": TEST_ADAPTER_KEY,
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


class NeverCalledAdapter(StubContentDetailDeclarationMixin):
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: AdapterExecutionContext):
        raise AssertionError("adapter should not be called")


class PrePlatformValidationAdapter(StubContentDetailDeclarationMixin):
    adapter_key = TEST_ADAPTER_KEY
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


class MissingResourceRequirementAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class InvalidResourceRequirementDeclarationAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = (
        {
            "adapter_key": TEST_ADAPTER_KEY,
            "capability": "content_detail",
            "resource_dependency_mode": "required",
            "required_capabilities": ("account", "browser_state"),
            "evidence_refs": ("fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",),
        },
    )

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class InvalidSiblingResourceRequirementDeclarationAdapter:
    adapter_key = "douyin"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = (
        {
            "adapter_key": "douyin",
            "capability": "content_detail",
            "resource_dependency_mode": "required",
            "required_capabilities": ("account", "browser_state"),
            "evidence_refs": ("fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",),
        },
    )

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class NoneResourceRequirementCollectionAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = None

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class ExtraFieldResourceRequirementDeclarationAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = (
        {
            "adapter_key": TEST_ADAPTER_KEY,
            "capability": "content_detail",
            "resource_dependency_mode": "required",
            "required_capabilities": ("account", "proxy"),
            "evidence_refs": baseline_required_resource_requirement_declaration(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail",
            ).evidence_refs,
            "unexpected_field": "shadow",
        },
    )

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class NoneModeResourceRequirementDeclarationAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = (
        {
            "adapter_key": TEST_ADAPTER_KEY,
            "capability": "content_detail",
            "resource_dependency_mode": "none",
            "required_capabilities": (),
            "evidence_refs": baseline_required_resource_requirement_declaration(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail",
            ).evidence_refs,
        },
    )

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class MultiProfileResourceRequirementAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = (
        AdapterResourceRequirementDeclarationV2(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail",
            resource_requirement_profiles=(
                AdapterResourceRequirementProfile(
                    profile_key="account_proxy",
                    resource_dependency_mode="required",
                    required_capabilities=("account", "proxy"),
                    evidence_refs=("fr-0027:profile:content-detail-by-url-hybrid:account-proxy",),
                ),
                AdapterResourceRequirementProfile(
                    profile_key="account",
                    resource_dependency_mode="required",
                    required_capabilities=("account",),
                    evidence_refs=("fr-0027:profile:content-detail-by-url-hybrid:account",),
                ),
            ),
        ),
    )

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class NoneCapabilitiesAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = None

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class NonContainerCapabilitiesAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = 123

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class NonStringCapabilitiesAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = ("content_detail", 1)

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class MissingCapabilitiesAdapter:
    adapter_key = TEST_ADAPTER_KEY

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class BrokenCapabilitiesIterable:
    def __iter__(self):
        yield "content_detail"
        raise RuntimeError("broken-iterator")


class BrokenIterableCapabilitiesAdapter:
    adapter_key = TEST_ADAPTER_KEY
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
        return iter((TEST_ADAPTER_KEY, TEST_ADAPTER_KEY))

    def __len__(self) -> int:
        return 2

    def __getitem__(self, key: str) -> object:
        if key != TEST_ADAPTER_KEY:
            raise KeyError(key)
        return self._adapter

    def items(self) -> Iterator[Tuple[str, object]]:
        return iter(((TEST_ADAPTER_KEY, self._adapter), (TEST_ADAPTER_KEY, self._adapter)))


class ExplodingRequestMapping(dict):
    def get(self, key, default=None):
        raise RuntimeError("boom")


class MissingTargetsAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class UnsupportedHybridCollectionModeAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"authenticated"})

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class BroadAxesAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url", "content_id", "creator_id", "keyword"})
    supported_collection_modes = frozenset({"public", "authenticated", "hybrid"})

    def execute(self, request: TaskRequest):
        raise AssertionError("shared admission should fail before adapter execution")


class MissingCollectionModesAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})

    def execute(self, request: TaskRequest):
        raise AssertionError("execute should not be called")


class MissingExecuteAdapter:
    adapter_key = TEST_ADAPTER_KEY
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

    def test_execute_task_builds_collection_success_envelope_from_adapter_payload(self) -> None:
        adapter = CollectionSearchAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_search_by_keyword",
            input=TaskInput(keyword="deep learning"),
        )

        result = execute_task_with_record(
            request,
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-runtime-collection-1",
        )

        self.assertEqual(result.envelope["status"], "success")
        self.assertEqual(result.envelope["operation"], "content_search_by_keyword")
        self.assertEqual(result.envelope["target"]["target_ref"], "deep learning")
        self.assertEqual(result.task_record.request.target_type, "keyword")
        self.assertEqual(adapter.last_request.collection_mode, "paginated")

    def test_execute_task_builds_media_asset_fetch_success_envelope_from_adapter_payload(self) -> None:
        adapter = MediaAssetFetchAdapter()
        fetch_policy = {
            "fetch_mode": "metadata_only",
            "allowed_content_types": ["image", "video"],
            "allow_download": False,
            "max_bytes": None,
        }
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="media_asset_fetch_by_ref",
            input=TaskInput(media_ref="media:asset-001", media_fetch_policy=fetch_policy),
        )

        result = execute_task_with_record(
            request,
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-runtime-media-asset-fetch-1",
        )

        self.assertEqual(result.envelope["status"], "success")
        self.assertEqual(result.envelope["operation"], "media_asset_fetch_by_ref")
        self.assertEqual(result.envelope["target"]["target_type"], "media_ref")
        self.assertEqual(result.envelope["target"]["media_ref"], "media:asset-001")
        self.assertEqual(result.envelope["result_status"], "complete")
        self.assertEqual(result.envelope["fetch_outcome"], "metadata_only")
        self.assertEqual(result.envelope["fetch_policy"], fetch_policy)
        self.assertFalse(result.envelope["no_storage"]["stored"])
        self.assertNotIn("local_path", result.envelope["no_storage"])
        self.assertEqual(result.task_record.request.target_type, "media_ref")
        self.assertEqual(result.task_record.request.collection_mode, "direct")
        self.assertEqual(adapter.last_request.request.capability, "media_asset_fetch")
        self.assertEqual(adapter.last_request.request.target_type, "media_ref")
        self.assertEqual(adapter.last_request.request.target_value, "media:asset-001")
        self.assertEqual(adapter.last_request.input.media_fetch_policy, fetch_policy)
        self.assertEqual(adapter.last_request.collection_mode, "direct")
        self.assertIsNotNone(adapter.last_request.resource_bundle)
        self.assertEqual(adapter.last_request.resource_bundle.capability, "media_asset_fetch_by_ref")

    def test_validate_success_payload_accepts_media_asset_fetch_unavailable_carrier(self) -> None:
        payload = make_media_asset_fetch_result(
            target_ref="media:asset-missing",
            fetch_outcome=None,
            result_status="unavailable",
            error_classification="media_unavailable",
        )

        self.assertIsNone(
            validate_success_payload(
                payload,
                capability="media_asset_fetch_by_ref",
                target_type="media_ref",
                target_value="media:asset-missing",
            )
        )

    def test_validate_success_payload_rejects_media_asset_fetch_target_drift(self) -> None:
        payload = make_media_asset_fetch_result(target_ref="media:asset-other")

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")
        self.assertEqual(result["details"]["expected_target_ref"], "media:asset-001")

    def test_execute_task_fails_closed_for_media_asset_fetch_storage_leak(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="media_asset_fetch_by_ref",
            input=TaskInput(media_ref="media:asset-leaky"),
        )

        result = execute_task_with_record(
            request,
            adapters={TEST_ADAPTER_KEY: MediaAssetFetchLeakyStorageAdapter()},
            task_id_factory=lambda: "task-runtime-media-asset-fetch-leak",
        )

        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["category"], "runtime_contract")
        self.assertEqual(result.envelope["error"]["code"], "invalid_adapter_success_payload")
        self.assertEqual(result.envelope["error"]["details"]["field"], "local_path")

    def test_execute_task_fails_closed_for_media_asset_fetch_default_policy_download(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="media_asset_fetch_by_ref",
            input=TaskInput(media_ref="media:asset-default-policy"),
        )

        result = execute_task_with_record(
            request,
            adapters={TEST_ADAPTER_KEY: MediaAssetFetchUnexpectedDownloadAdapter()},
            task_id_factory=lambda: "task-runtime-media-asset-fetch-policy",
        )

        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["category"], "runtime_contract")
        self.assertEqual(result.envelope["error"]["code"], "invalid_adapter_success_payload")

    def test_execute_task_rejects_private_media_ref_request(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="media_asset_fetch_by_ref",
            input=TaskInput(media_ref="https://signed.example.invalid/media?token=secret"),
        )

        result = execute_task_with_record(
            request,
            adapters={TEST_ADAPTER_KEY: MediaAssetFetchAdapter()},
            task_id_factory=lambda: "task-runtime-media-private-ref",
        )

        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["code"], "invalid_task_request")

    def test_validate_success_payload_rejects_media_asset_fetch_missing_lineage(self) -> None:
        payload = make_media_asset_fetch_result()
        assert isinstance(payload["media"], dict)
        payload["media"].pop("source_ref_lineage")

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_download_metadata_gap(self) -> None:
        payload = make_media_asset_fetch_result(fetch_outcome="downloaded_bytes", fetch_mode="download_if_allowed")
        assert isinstance(payload["media"], dict)
        assert isinstance(payload["media"]["metadata"], dict)
        payload["media"]["metadata"].pop("checksum_digest")

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_request_policy_drift(self) -> None:
        payload = make_media_asset_fetch_result(fetch_outcome="downloaded_bytes", fetch_mode="download_if_allowed")

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
            request_cursor={
                "fetch_mode": "metadata_only",
                "allowed_content_types": ["image", "video"],
                "allow_download": False,
                "max_bytes": None,
            },
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_max_bytes_violation(self) -> None:
        payload = make_media_asset_fetch_result(fetch_outcome="downloaded_bytes", fetch_mode="download_if_allowed")
        payload["fetch_policy"]["max_bytes"] = 1

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
            request_cursor=payload["fetch_policy"],
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_download_required_degrade(self) -> None:
        payload = make_media_asset_fetch_result(fetch_outcome="source_ref_preserved", fetch_mode="download_required")
        payload["fetch_policy"]["allow_download"] = True

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
            request_cursor=payload["fetch_policy"],
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_download_required_metadata_only(self) -> None:
        payload = make_media_asset_fetch_result(fetch_mode="download_required", fetch_outcome="metadata_only")
        payload["fetch_policy"]["allow_download"] = True

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
            request_cursor=payload["fetch_policy"],
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_missing_failed_media_null(self) -> None:
        payload = make_media_asset_fetch_result(
            fetch_outcome=None,
            result_status="failed",
            error_classification="platform_failed",
        )
        payload.pop("media")

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_missing_nullable_failure_field(self) -> None:
        payload = make_media_asset_fetch_result(
            fetch_outcome=None,
            result_status="failed",
            error_classification="platform_failed",
        )
        payload.pop("fetch_outcome")

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")
        self.assertEqual(result["details"]["field"], "fetch_outcome")

    def test_validate_success_payload_accepts_unsupported_content_type_failure(self) -> None:
        payload = make_media_asset_fetch_result(
            content_type="mixed_media",
            fetch_outcome=None,
            result_status="failed",
            error_classification="unsupported_content_type",
        )

        self.assertIsNone(
            validate_success_payload(
                payload,
                capability="media_asset_fetch_by_ref",
                target_type="media_ref",
                target_value="media:asset-001",
            )
        )

    def test_validate_success_payload_rejects_media_asset_fetch_complete_without_raw_payload_ref(self) -> None:
        payload = make_media_asset_fetch_result()
        payload["raw_payload_ref"] = None

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_task_request_rejects_media_fetch_policy_allowed_content_type_shape(self) -> None:
        result = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="media_asset_fetch_by_ref",
                input=TaskInput(
                    media_ref="media:asset-001",
                    media_fetch_policy={
                        "fetch_mode": "metadata_only",
                        "allowed_content_types": 1,
                        "allow_download": False,
                        "max_bytes": None,
                    },
                ),
            ),
            adapters={TEST_ADAPTER_KEY: MediaAssetFetchAdapter()},
            task_id_factory=lambda: "task-runtime-media-policy-shape",
        )

        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["code"], "invalid_task_request")

    def test_validate_success_payload_rejects_media_asset_fetch_unstable_content_type(self) -> None:
        payload = make_media_asset_fetch_result(content_type="mixed_media")

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_unsupported_content_type_wrong_classification(self) -> None:
        payload = make_media_asset_fetch_result(
            content_type="mixed_media",
            fetch_outcome=None,
            result_status="failed",
            error_classification="parse_failed",
        )

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_accepts_unknown_content_type_parse_failed(self) -> None:
        payload = make_media_asset_fetch_result(
            content_type="unknown",
            fetch_outcome=None,
            result_status="failed",
            error_classification="parse_failed",
        )

        self.assertIsNone(
            validate_success_payload(
                payload,
                capability="media_asset_fetch_by_ref",
                target_type="media_ref",
                target_value="media:asset-001",
            )
        )

    def test_validate_success_payload_rejects_media_asset_fetch_private_metadata(self) -> None:
        payload = make_media_asset_fetch_result()
        assert isinstance(payload["media"], dict)
        assert isinstance(payload["media"]["metadata"], dict)
        payload["media"]["metadata"]["signed_url"] = "https://media.example.invalid/private"

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_private_fetch_policy(self) -> None:
        payload = make_media_asset_fetch_result()
        payload["fetch_policy"]["provider_route"] = "https://signed.example.invalid/route?token=secret"

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_wrong_policy_denied_classification(self) -> None:
        payload = make_media_asset_fetch_result(
            content_type="video",
            fetch_outcome=None,
            result_status="failed",
            error_classification="unsupported_content_type",
        )
        payload["fetch_policy"]["allowed_content_types"] = ["image"]

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
            request_cursor=payload["fetch_policy"],
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_unavailable_policy_bypass(self) -> None:
        payload = make_media_asset_fetch_result(
            content_type="video",
            fetch_outcome=None,
            result_status="unavailable",
            error_classification="permission_denied",
        )
        payload["fetch_policy"]["allowed_content_types"] = ["image"]

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
            request_cursor=payload["fetch_policy"],
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_download_required_policy_failure_class(self) -> None:
        payload = make_media_asset_fetch_result(
            fetch_mode="download_required",
            fetch_outcome=None,
            result_status="failed",
            error_classification="platform_failed",
        )
        payload["fetch_policy"]["allow_download"] = False

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
            request_cursor=payload["fetch_policy"],
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_accepts_media_asset_fetch_formal_media_ref_target(self) -> None:
        payload = make_media_asset_fetch_result()

        self.assertIsNone(
            validate_success_payload(
                payload,
                capability="media_asset_fetch_by_ref",
                target_type="media_ref",
                target_value="media:asset-001",
            )
        )

    def test_validate_success_payload_rejects_media_asset_fetch_legacy_target_ref_only(self) -> None:
        payload = make_media_asset_fetch_result()
        payload["target"]["target_ref"] = payload["target"].pop("media_ref")

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_target_extra_field(self) -> None:
        payload = make_media_asset_fetch_result()
        payload["target"]["signed_url"] = "https://signed.example.invalid/media?token=secret"

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_non_download_byte_count(self) -> None:
        payload = make_media_asset_fetch_result()
        payload["no_storage"]["downloaded_byte_length"] = 1

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_accepts_media_asset_fetch_permission_and_auth_failures(self) -> None:
        for status, classification in (
            ("unavailable", "permission_denied"),
            ("failed", "credential_invalid"),
            ("failed", "verification_required"),
        ):
            with self.subTest(status=status, classification=classification):
                target_ref = f"media:{classification}".replace("credential_invalid", "auth-invalid")
                payload = make_media_asset_fetch_result(
                    target_ref=target_ref,
                    fetch_outcome=None,
                    result_status=status,
                    error_classification=classification,
                )

                self.assertIsNone(
                    validate_success_payload(
                        payload,
                        capability="media_asset_fetch_by_ref",
                        target_type="media_ref",
                        target_value=target_ref,
                    )
                )

    def test_validate_success_payload_rejects_media_asset_fetch_blocked_raw_payload(self) -> None:
        payload = make_media_asset_fetch_result(
            fetch_outcome=None,
            result_status="failed",
            error_classification="provider_or_network_blocked",
        )
        payload["raw_payload_ref"] = "raw://blocked-should-be-null"
        payload["source_trace"]["provider_path"] = "provider://blocked-path-alias/media"

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_blocked_routing_path(self) -> None:
        payload = make_media_asset_fetch_result(
            fetch_outcome=None,
            result_status="failed",
            error_classification="provider_or_network_blocked",
        )
        payload["source_trace"]["provider_path"] = "provider://primary/fallback/selector"

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_private_source_trace_field(self) -> None:
        payload = make_media_asset_fetch_result()
        payload["source_trace"]["signed_url"] = "https://signed.example.invalid/media?token=secret"

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_download_audit_gap(self) -> None:
        payload = make_media_asset_fetch_result(fetch_outcome="downloaded_bytes", fetch_mode="download_if_allowed")
        payload["audit"] = {}

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
            request_cursor=payload["fetch_policy"],
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_download_audit_mismatch(self) -> None:
        payload = make_media_asset_fetch_result(fetch_outcome="downloaded_bytes", fetch_mode="download_if_allowed")
        payload["audit"]["byte_size"] = 9999

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
            request_cursor=payload["fetch_policy"],
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_non_download_audit(self) -> None:
        payload = make_media_asset_fetch_result()
        payload["audit"] = {"transfer_observed": True}

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_accepts_media_asset_fetch_blocked_alias(self) -> None:
        payload = make_media_asset_fetch_result(
            fetch_outcome=None,
            result_status="failed",
            error_classification="provider_or_network_blocked",
        )
        payload["raw_payload_ref"] = None
        payload["source_trace"]["provider_path"] = "provider://blocked-path-alias/media"

        self.assertIsNone(
            validate_success_payload(
                payload,
                capability="media_asset_fetch_by_ref",
                target_type="media_ref",
                target_value="media:asset-001",
            )
        )

    def test_validate_success_payload_rejects_media_asset_fetch_signed_source_ref(self) -> None:
        payload = make_media_asset_fetch_result()
        assert isinstance(payload["media"], dict)
        payload["media"]["source_media_ref"] = "https://signed.example.invalid/media?token=secret"
        assert isinstance(payload["media"]["source_ref_lineage"], dict)
        payload["media"]["source_ref_lineage"]["source_media_ref"] = payload["media"]["source_media_ref"]

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_media_extra_field(self) -> None:
        payload = make_media_asset_fetch_result()
        assert isinstance(payload["media"], dict)
        payload["media"]["storage_handle"] = "storage://private"

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_local_lineage_ref(self) -> None:
        payload = make_media_asset_fetch_result()
        assert isinstance(payload["media"], dict)
        assert isinstance(payload["media"]["source_ref_lineage"], dict)
        payload["media"]["source_ref_lineage"]["resolved_ref"] = "/tmp/downloaded-file.mp4"

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_lineage_extra_field(self) -> None:
        payload = make_media_asset_fetch_result()
        assert isinstance(payload["media"], dict)
        assert isinstance(payload["media"]["source_ref_lineage"], dict)
        payload["media"]["source_ref_lineage"]["platform_media_schema"] = {"private": True}

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_private_target_ref(self) -> None:
        private_ref = "https://signed.example.invalid/media?token=secret"
        payload = make_media_asset_fetch_result(target_ref=private_ref)

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value=private_ref,
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_rejects_media_asset_fetch_no_storage_private_field(self) -> None:
        payload = make_media_asset_fetch_result()
        payload["no_storage"]["signed_url"] = "https://signed.example.invalid/media?token=secret"

        result = validate_success_payload(
            payload,
            capability="media_asset_fetch_by_ref",
            target_type="media_ref",
            target_value="media:asset-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")

    def test_validate_success_payload_accepts_comment_collection_runtime_carrier(self) -> None:
        payload = make_comment_collection_result(target_ref="content-001")

        self.assertIsNone(
            validate_success_payload(
                payload,
                capability="comment_collection",
                target_type="content",
                target_value="content-001",
            )
        )

    def test_validate_success_payload_rejects_emitted_partial_result_classification(self) -> None:
        payload = make_comment_collection_reply_result(root_comment_ref="comment:root-1")
        payload["result_status"] = "complete"
        payload["error_classification"] = "partial_result"

        result = validate_success_payload(
            payload,
            capability="comment_collection",
            target_type="content",
            target_value="content-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")
        self.assertEqual(result["details"]["reason"], "invalid_comment_collection_contract")

    def test_validate_success_payload_rejects_opaque_reply_refs_not_bound_to_request_cursor(self) -> None:
        payload = make_comment_collection_reply_result(root_comment_ref="comment:other-root")

        result = validate_success_payload(
            payload,
            capability="comment_collection",
            target_type="content",
            target_value="content-001",
            request_cursor={"reply_cursor": make_comment_reply_cursor(comment_ref="comment:root-1")},
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["code"], "invalid_adapter_success_payload")
        self.assertEqual(result["details"]["reason"], "cursor_invalid_or_expired")

    def test_validate_success_payload_rejects_opaque_reply_refs_not_bound_to_dataclass_cursor(self) -> None:
        payload = make_comment_collection_reply_result(root_comment_ref="comment:other-root")

        result = validate_success_payload(
            payload,
            capability="comment_collection",
            target_type="content",
            target_value="content-001",
            request_cursor=CommentRequestCursor(
                reply_cursor=CommentReplyCursor(
                    reply_cursor_token="reply-cursor-1",
                    reply_cursor_family="opaque",
                    resume_target_ref="content-001",
                    resume_comment_ref="comment:root-1",
                    issued_at="2026-05-09T10:00:00Z",
                ),
            ),
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["code"], "invalid_adapter_success_payload")
        self.assertEqual(result["details"]["reason"], "cursor_invalid_or_expired")

    def test_validate_success_payload_accepts_explicit_target_binding_against_request_cursor(self) -> None:
        payload = make_comment_collection_reply_result(root_comment_ref="comment:root-1")
        payload["items"][0]["normalized"]["target_comment_ref"] = "comment:root-1"

        self.assertIsNone(
            validate_success_payload(
                payload,
                capability="comment_collection",
                target_type="content",
                target_value="content-001",
                request_cursor={"reply_cursor": make_comment_reply_cursor(comment_ref="comment:root-1")},
            )
        )

    def test_validate_success_payload_rejects_target_ref_as_thread_proof(self) -> None:
        payload = make_comment_collection_reply_result(root_comment_ref="comment:root-1")
        payload["items"][0]["normalized"]["target_comment_ref"] = "comment:other-thread"

        result = validate_success_payload(
            payload,
            capability="comment_collection",
            target_type="content",
            target_value="content-001",
            request_cursor={"reply_cursor": make_comment_reply_cursor(comment_ref="comment:other-thread")},
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")
        self.assertEqual(result["details"]["reason"], "invalid_comment_collection_contract")

    def test_validate_success_payload_rejects_top_level_cursor_reply_window_drift(self) -> None:
        payload = make_comment_collection_reply_result(root_comment_ref="comment:root-1")
        payload["next_continuation"] = {
            "continuation_token": "reply-page-cursor-2",
            "continuation_family": "opaque",
            "resume_target_ref": "content-001",
            "resume_comment_ref": "comment:root-1",
            "issued_at": "2026-05-09T10:00:00Z",
        }
        payload["has_more"] = True

        result = validate_success_payload(
            payload,
            capability="comment_collection",
            target_type="content",
            target_value="content-001",
            request_cursor={"page_continuation": make_comment_page_continuation()},
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")
        self.assertEqual(result["details"]["reason"], "cursor_invalid_or_expired")

    def test_validate_success_payload_rejects_first_page_reply_continuation_drift(self) -> None:
        payload = make_comment_collection_reply_result(root_comment_ref="comment:root-1")
        payload["has_more"] = True
        payload["next_continuation"] = {
            "continuation_token": "reply-page-cursor-2",
            "continuation_family": "opaque",
            "resume_target_ref": "content-001",
            "resume_comment_ref": "comment:root-1",
            "issued_at": "2026-05-09T10:00:00Z",
        }

        result = validate_success_payload(
            payload,
            capability="comment_collection",
            target_type="content",
            target_value="content-001",
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")
        self.assertEqual(result["details"]["reason"], "cursor_invalid_or_expired")

    def test_validate_success_payload_rejects_empty_mapping_cursor_reply_window_drift(self) -> None:
        payload = make_comment_collection_reply_result(root_comment_ref="comment:root-1")
        payload["has_more"] = True
        payload["next_continuation"] = make_comment_page_continuation()
        payload["next_continuation"]["resume_comment_ref"] = "comment:root-1"

        result = validate_success_payload(
            payload,
            capability="comment_collection",
            target_type="content",
            target_value="content-001",
            request_cursor={},
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")
        self.assertEqual(result["details"]["reason"], "cursor_invalid_or_expired")

    def test_validate_success_payload_rejects_empty_dataclass_cursor_reply_window_drift(self) -> None:
        payload = make_comment_collection_reply_result(root_comment_ref="comment:root-1")
        payload["has_more"] = True
        payload["next_continuation"] = make_comment_page_continuation()
        payload["next_continuation"]["resume_comment_ref"] = "comment:root-1"

        result = validate_success_payload(
            payload,
            capability="comment_collection",
            target_type="content",
            target_value="content-001",
            request_cursor=CommentRequestCursor(),
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")
        self.assertEqual(result["details"]["reason"], "cursor_invalid_or_expired")

    def test_validate_success_payload_accepts_top_level_page_with_reply_items(self) -> None:
        payload = make_comment_collection_reply_result(root_comment_ref="comment:root-1")

        self.assertIsNone(
            validate_success_payload(
                payload,
                capability="comment_collection",
                target_type="content",
                target_value="content-001",
            )
        )

    def test_validate_success_payload_accepts_nested_reply_window_bound_to_parent(self) -> None:
        payload = make_comment_collection_reply_result(root_comment_ref="comment:root-1")
        item = payload["items"][0]
        item["normalized"]["parent_comment_ref"] = "comment:root-1:parent-1"
        item["normalized"]["target_comment_ref"] = "comment:mentioned-1"

        self.assertIsNone(
            validate_success_payload(
                payload,
                capability="comment_collection",
                target_type="content",
                target_value="content-001",
                request_cursor={"reply_cursor": make_comment_reply_cursor(comment_ref="comment:root-1:parent-1")},
            )
        )

    def test_validate_success_payload_accepts_descendant_reply_window(self) -> None:
        payload = make_comment_collection_reply_result(root_comment_ref="comment:root-1")
        item = payload["items"][0]
        item["normalized"]["parent_comment_ref"] = "comment:root-1:child-1"
        item["normalized"]["target_comment_ref"] = "comment:mentioned-1"

        self.assertIsNone(
            validate_success_payload(
                payload,
                capability="comment_collection",
                target_type="content",
                target_value="content-001",
                request_cursor={"reply_cursor": make_comment_reply_cursor(comment_ref="comment:root-1")},
            )
        )

    def test_validate_success_payload_accepts_non_root_descendant_when_target_matches_resume(self) -> None:
        payload = make_comment_collection_reply_result(root_comment_ref="comment:root-1")
        item = payload["items"][0]
        item["normalized"]["parent_comment_ref"] = "comment:child-1"
        item["normalized"]["target_comment_ref"] = "comment:parent-1"

        self.assertIsNone(
            validate_success_payload(
                payload,
                capability="comment_collection",
                target_type="content",
                target_value="content-001",
                request_cursor={"reply_cursor": make_comment_reply_cursor(comment_ref="comment:parent-1")},
            )
        )

    def test_validate_success_payload_rejects_reply_target_self_reference(self) -> None:
        payload = make_comment_collection_reply_result(root_comment_ref="comment:root-1")
        item = payload["items"][0]
        item["normalized"]["target_comment_ref"] = item["normalized"]["canonical_ref"]

        result = validate_success_payload(
            payload,
            capability="comment_collection",
            target_type="content",
            target_value="content-001",
            request_cursor={"reply_cursor": make_comment_reply_cursor(comment_ref="comment:root-1")},
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")
        self.assertEqual(result["details"]["reason"], "invalid_comment_collection_contract")

    def test_validate_success_payload_rejects_reply_window_continuation_without_thread_ref(self) -> None:
        payload = make_comment_collection_reply_result(root_comment_ref="comment:root-1")
        payload["has_more"] = True
        payload["next_continuation"] = make_comment_page_continuation()

        result = validate_success_payload(
            payload,
            capability="comment_collection",
            target_type="content",
            target_value="content-001",
            request_cursor={"reply_cursor": make_comment_reply_cursor(comment_ref="comment:root-1")},
        )

        self.assertEqual(result["code"], "invalid_adapter_success_payload")
        self.assertEqual(result["details"]["reason"], "invalid_comment_collection_contract")

    def test_execute_task_builds_comment_collection_success_envelope_from_adapter_payload(self) -> None:
        adapter = CommentCollectionAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="comment_collection",
            input=TaskInput(content_ref="content-001"),
        )

        result = execute_task_with_record(
            request,
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-runtime-comment-collection-1",
        )

        self.assertEqual(result.envelope["status"], "success")
        self.assertEqual(result.envelope["operation"], "comment_collection")
        self.assertEqual(result.envelope["target"]["target_type"], "content")
        self.assertEqual(result.envelope["target"]["target_ref"], "content-001")
        self.assertEqual(result.task_record.request.target_type, "content")
        self.assertEqual(adapter.last_request.collection_mode, "paginated")
        self.assertIsNotNone(adapter.last_request.resource_bundle)
        self.assertEqual(adapter.last_request.resource_bundle.capability, "comment_collection")
        self.assertEqual(adapter.last_request.resource_bundle.requested_slots, ("account",))

    def test_execute_task_uses_comment_collection_account_only_profile(self) -> None:
        adapter = CommentCollectionAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="comment_collection",
            input=TaskInput(content_ref="content-account-only-resource-pool"),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            account_only_store = LocalResourceLifecycleStore(Path(temp_dir) / "resource-lifecycle.json")
            account_only_store.seed_resources(
                (
                    ResourceRecord(
                        resource_id="account-comment-only-001",
                        resource_type="account",
                        status="AVAILABLE",
                        material=managed_account_material(generic_account_material(), adapter_key=TEST_ADAPTER_KEY),
                    ),
                )
            )
            result = execute_task_with_record(
                request,
                adapters={TEST_ADAPTER_KEY: adapter},
                task_id_factory=lambda: "task-runtime-comment-collection-account-only",
                resource_lifecycle_store=account_only_store,
            )

        self.assertEqual(result.envelope["status"], "success")
        self.assertIsNotNone(adapter.last_request.resource_bundle)
        self.assertEqual(adapter.last_request.resource_bundle.requested_slots, ("account",))
        self.assertIsNotNone(adapter.last_request.resource_bundle.account)
        self.assertIsNone(adapter.last_request.resource_bundle.proxy)

    def test_execute_task_uses_v1_comment_collection_account_only_declaration(self) -> None:
        adapter = V1AccountOnlyCommentCollectionAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="comment_collection",
            input=TaskInput(content_ref="content-v1-account-only-resource-pool"),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            account_only_store = LocalResourceLifecycleStore(Path(temp_dir) / "resource-lifecycle.json")
            account_only_store.seed_resources(
                (
                    ResourceRecord(
                        resource_id="account-comment-v1-only-001",
                        resource_type="account",
                        status="AVAILABLE",
                        material=managed_account_material(generic_account_material(), adapter_key=TEST_ADAPTER_KEY),
                    ),
                )
            )
            result = execute_task_with_record(
                request,
                adapters={TEST_ADAPTER_KEY: adapter},
                task_id_factory=lambda: "task-runtime-comment-collection-v1-account-only",
                resource_lifecycle_store=account_only_store,
            )

        self.assertEqual(result.envelope["status"], "success")
        self.assertIsNotNone(adapter.last_request.resource_bundle)
        self.assertEqual(adapter.last_request.resource_bundle.requested_slots, ("account",))
        self.assertIsNotNone(adapter.last_request.resource_bundle.account)
        self.assertIsNone(adapter.last_request.resource_bundle.proxy)

    def test_execute_task_uses_media_asset_fetch_account_only_profile(self) -> None:
        adapter = MultiProfileMediaAssetFetchAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="media_asset_fetch_by_ref",
            input=TaskInput(media_ref="media:account-only-resource-pool"),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            account_only_store = LocalResourceLifecycleStore(Path(temp_dir) / "resource-lifecycle.json")
            account_only_store.seed_resources(
                (
                    ResourceRecord(
                        resource_id="account-media-only-001",
                        resource_type="account",
                        status="AVAILABLE",
                        material=managed_account_material(generic_account_material(), adapter_key=TEST_ADAPTER_KEY),
                    ),
                )
            )
            result = execute_task_with_record(
                request,
                adapters={TEST_ADAPTER_KEY: adapter},
                task_id_factory=lambda: "task-runtime-media-asset-fetch-account-only",
                resource_lifecycle_store=account_only_store,
            )

        self.assertEqual(result.envelope["status"], "success")
        self.assertIsNotNone(adapter.last_request.resource_bundle)
        self.assertEqual(adapter.last_request.resource_bundle.requested_slots, ("account",))
        self.assertIsNotNone(adapter.last_request.resource_bundle.account)
        self.assertIsNone(adapter.last_request.resource_bundle.proxy)

    def test_execute_task_uses_v1_media_asset_fetch_account_only_declaration(self) -> None:
        adapter = V1AccountOnlyMediaAssetFetchAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="media_asset_fetch_by_ref",
            input=TaskInput(media_ref="media:v1-account-only-resource-pool"),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            account_only_store = LocalResourceLifecycleStore(Path(temp_dir) / "resource-lifecycle.json")
            account_only_store.seed_resources(
                (
                    ResourceRecord(
                        resource_id="account-media-v1-only-001",
                        resource_type="account",
                        status="AVAILABLE",
                        material=managed_account_material(generic_account_material(), adapter_key=TEST_ADAPTER_KEY),
                    ),
                )
            )
            result = execute_task_with_record(
                request,
                adapters={TEST_ADAPTER_KEY: adapter},
                task_id_factory=lambda: "task-runtime-media-asset-fetch-v1-account-only",
                resource_lifecycle_store=account_only_store,
            )

        self.assertEqual(result.envelope["status"], "success")
        self.assertIsNotNone(adapter.last_request.resource_bundle)
        self.assertEqual(adapter.last_request.resource_bundle.requested_slots, ("account",))
        self.assertIsNotNone(adapter.last_request.resource_bundle.account)
        self.assertIsNone(adapter.last_request.resource_bundle.proxy)

    def test_execute_task_fails_closed_when_comment_collection_resource_pool_is_empty(self) -> None:
        adapter = CommentCollectionAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="comment_collection",
            input=TaskInput(content_ref="content-empty-resource-pool"),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            empty_store = LocalResourceLifecycleStore(Path(temp_dir) / "resource-lifecycle.json")
            result = execute_task_with_record(
                request,
                adapters={TEST_ADAPTER_KEY: adapter},
                task_id_factory=lambda: "task-runtime-comment-collection-empty-resource-pool",
                resource_lifecycle_store=empty_store,
            )

        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["category"], "runtime_contract")
        self.assertEqual(result.envelope["error"]["code"], "resource_unavailable")
        self.assertIsNotNone(result.task_record)
        self.assertEqual(result.task_record.status, "failed")
        self.assertEqual(result.task_record.result.envelope["error"]["code"], "resource_unavailable")
        self.assertFalse(hasattr(adapter, "last_request"))

    def test_execute_task_passes_comment_request_cursor_to_adapter_context(self) -> None:
        adapter = CommentCollectionAdapter()
        cursor = {"page_continuation": make_comment_page_continuation()}
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="comment_collection",
            input=TaskInput(content_ref="content-001", comment_request_cursor=cursor),
        )

        result = execute_task_with_record(
            request,
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-runtime-comment-collection-cursor-1",
        )

        self.assertEqual(result.envelope["status"], "success")
        self.assertEqual(adapter.last_request.input.comment_request_cursor, cursor)

    def test_execute_task_normalizes_dataclass_cursor_before_adapter_context(self) -> None:
        adapter = CommentCollectionAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="comment_collection",
            input=TaskInput(
                content_ref="content-001",
                comment_request_cursor=CommentRequestCursor(
                    reply_cursor=CommentReplyCursor(
                        reply_cursor_token="reply-cursor-1",
                        reply_cursor_family="opaque",
                        resume_target_ref="content-001",
                        resume_comment_ref="comment:root-1",
                        issued_at="2026-05-09T10:00:00Z",
                    ),
                ),
            ),
        )

        result = execute_task_with_record(
            request,
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-runtime-comment-collection-dataclass-cursor-normalized",
        )

        self.assertEqual(result.envelope["status"], "success")
        self.assertEqual(
            adapter.last_request.input.comment_request_cursor,
            {"page_continuation": None, "reply_cursor": make_comment_reply_cursor(comment_ref="comment:root-1")},
        )

    def test_execute_task_rejects_reply_drift_after_adapter_mutates_visible_cursor(self) -> None:
        adapter = MutatingCommentCursorAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="comment_collection",
            input=TaskInput(
                content_ref="content-001",
                comment_request_cursor={"reply_cursor": make_comment_reply_cursor(comment_ref="comment:root-1")},
            ),
        )

        result = execute_task_with_record(
            request,
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-runtime-comment-collection-mutating-cursor",
        )

        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["code"], "invalid_adapter_success_payload")
        self.assertEqual(result.envelope["error"]["details"]["reason"], "cursor_invalid_or_expired")

    def test_execute_task_returns_comment_fail_closed_carrier_for_mixed_request_cursors(self) -> None:
        adapter = CommentCollectionAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="comment_collection",
            input=TaskInput(
                content_ref="content-001",
                comment_request_cursor={
                    "page_continuation": make_comment_page_continuation(),
                    "reply_cursor": make_comment_reply_cursor(),
                },
            ),
        )

        result = execute_task_with_record(
            request,
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-runtime-comment-collection-cursor-2",
        )

        self.assertEqual(result.envelope["status"], "success")
        self.assertEqual(result.envelope["operation"], "comment_collection")
        self.assertEqual(result.envelope["items"], [])
        self.assertFalse(result.envelope["has_more"])
        self.assertIsNone(result.envelope["next_continuation"])
        self.assertEqual(result.envelope["result_status"], "complete")
        self.assertEqual(result.envelope["error_classification"], "signature_or_request_invalid")
        self.assertIsNotNone(result.task_record)
        self.assertEqual(result.task_record.status, "succeeded")
        self.assertEqual(result.task_record.result.envelope["error_classification"], "signature_or_request_invalid")
        self.assertFalse(hasattr(adapter, "last_request"))

    def test_execute_task_preserves_missing_adapter_failure_before_comment_cursor_fail_closed(self) -> None:
        request = TaskRequest(
            adapter_key="missing-adapter",
            capability="comment_collection",
            input=TaskInput(
                content_ref="content-001",
                comment_request_cursor={
                    "page_continuation": make_comment_page_continuation(),
                    "reply_cursor": make_comment_reply_cursor(),
                },
            ),
        )

        result = execute_task_with_record(
            request,
            adapters={},
            task_id_factory=lambda: "task-runtime-comment-collection-cursor-missing-adapter",
        )

        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["code"], "adapter_not_found")
        self.assertIsNone(result.task_record)

    def test_execute_task_returns_comment_fail_closed_carrier_for_cross_target_reply_cursor(self) -> None:
        adapter = CommentCollectionAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="comment_collection",
            input=TaskInput(
                content_ref="content-001",
                comment_request_cursor={
                    "reply_cursor": make_comment_reply_cursor(target_ref="other-content"),
                },
            ),
        )

        result = execute_task_with_record(
            request,
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-runtime-comment-collection-cursor-3",
        )

        self.assertEqual(result.envelope["status"], "success")
        self.assertEqual(result.envelope["result_status"], "complete")
        self.assertEqual(result.envelope["error_classification"], "cursor_invalid_or_expired")
        self.assertEqual(result.envelope["target"]["target_ref"], "content-001")
        self.assertIsNotNone(result.task_record)
        self.assertEqual(result.task_record.status, "succeeded")
        self.assertFalse(hasattr(adapter, "last_request"))

    def test_execute_task_returns_comment_fail_closed_carrier_for_malformed_request_cursor(self) -> None:
        adapter = CommentCollectionAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="comment_collection",
            input=TaskInput(
                content_ref="content-001",
                comment_request_cursor={
                    "reply_cursor": {
                        "reply_cursor_family": "opaque",
                        "resume_target_ref": "content-001",
                        "resume_comment_ref": "comment:root-1",
                    },
                },
            ),
        )

        result = execute_task_with_record(
            request,
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-runtime-comment-collection-cursor-5",
        )

        self.assertEqual(result.envelope["status"], "success")
        self.assertEqual(result.envelope["result_status"], "complete")
        self.assertEqual(result.envelope["error_classification"], "signature_or_request_invalid")
        self.assertEqual(result.envelope["items"], [])
        self.assertIsNotNone(result.task_record)
        self.assertEqual(result.task_record.status, "succeeded")
        self.assertFalse(hasattr(adapter, "last_request"))

    def test_execute_task_returns_comment_fail_closed_carrier_for_malformed_dataclass_cursor(self) -> None:
        adapter = CommentCollectionAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="comment_collection",
            input=TaskInput(
                content_ref="content-001",
                comment_request_cursor=CommentRequestCursor(
                    reply_cursor=CommentReplyCursor(
                        reply_cursor_token="",
                        reply_cursor_family="opaque",
                        resume_target_ref="content-001",
                        resume_comment_ref="comment:root-1",
                        issued_at="not-a-time",
                    ),
                ),
            ),
        )

        result = execute_task_with_record(
            request,
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-runtime-comment-collection-cursor-6",
        )

        self.assertEqual(result.envelope["status"], "success")
        self.assertEqual(result.envelope["result_status"], "complete")
        self.assertEqual(result.envelope["error_classification"], "signature_or_request_invalid")
        self.assertEqual(result.envelope["items"], [])
        self.assertFalse(hasattr(adapter, "last_request"))

    def test_execute_task_returns_comment_fail_closed_carrier_for_dataclass_cursor_with_mapping_child(self) -> None:
        adapter = CommentCollectionAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="comment_collection",
            input=TaskInput(
                content_ref="content-001",
                comment_request_cursor=CommentRequestCursor(  # type: ignore[arg-type]
                    reply_cursor={"reply_cursor_token": "cursor-1"},
                ),
            ),
        )

        result = execute_task_with_record(
            request,
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-runtime-comment-collection-cursor-7",
        )

        self.assertEqual(result.envelope["status"], "success")
        self.assertEqual(result.envelope["error_classification"], "signature_or_request_invalid")
        self.assertFalse(hasattr(adapter, "last_request"))

    def test_execute_core_task_request_returns_comment_fail_closed_carrier_for_mixed_request_cursors(self) -> None:
        adapter = CommentCollectionAdapter()
        request = CoreTaskRequest(
            target=InputTarget(
                adapter_key=TEST_ADAPTER_KEY,
                capability="comment_collection",
                target_type="content",
                target_value="content-001",
            ),
            policy=CollectionPolicy(collection_mode="paginated"),
            request_cursor={
                "page_continuation": make_comment_page_continuation(),
                "reply_cursor": make_comment_reply_cursor(),
            },
        )

        result = execute_task_with_record(
            request,
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-runtime-comment-collection-cursor-4",
        )

        self.assertEqual(result.envelope["status"], "success")
        self.assertEqual(result.envelope["result_status"], "complete")
        self.assertEqual(result.envelope["error_classification"], "signature_or_request_invalid")
        self.assertEqual(result.envelope["target"]["target_ref"], "content-001")
        self.assertIsNotNone(result.task_record)
        self.assertEqual(result.task_record.status, "succeeded")
        self.assertFalse(hasattr(adapter, "last_request"))

    def test_execute_core_task_request_with_invalid_axes_does_not_rewrite_comment_fail_closed_target(self) -> None:
        adapter = CommentCollectionAdapter()
        request = CoreTaskRequest(
            target=InputTarget(
                adapter_key=TEST_ADAPTER_KEY,
                capability="comment_collection",
                target_type="creator",
                target_value="creator-001",
            ),
            policy=CollectionPolicy(collection_mode="public"),
            request_cursor={
                "page_continuation": make_comment_page_continuation(),
                "reply_cursor": make_comment_reply_cursor(),
            },
        )

        result = execute_task_with_record(
            request,
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-runtime-comment-collection-cursor-6",
        )

        self.assertEqual(result.envelope["status"], "failed")
        self.assertEqual(result.envelope["error"]["code"], "invalid_task_request")
        self.assertNotIn("target", result.envelope)
        self.assertFalse(hasattr(adapter, "last_request"))

    def test_contract_harness_builds_comment_collection_success_envelope(self) -> None:
        payload = make_comment_collection_result(target_ref="content-001")

        envelope = _build_success_runtime_envelope(
            task_id="task-harness-comment-collection-1",
            adapter_key=TEST_ADAPTER_KEY,
            capability="comment_collection",
            payload=payload,
        )
        result = validate_contract_sample(
            ContractSampleDefinition(sample_id="comment-collection-success", expected_outcome="success"),
            HarnessExecutionResult(runtime_envelope=envelope),
        )

        self.assertEqual(envelope["status"], "success")
        self.assertEqual(envelope["operation"], "comment_collection")
        self.assertEqual(envelope["target"]["target_ref"], "content-001")
        self.assertEqual(result["verdict"], "pass")

    def test_contract_harness_rejects_comment_collection_target_drift(self) -> None:
        payload = make_comment_collection_result(target_ref="drifted-content")

        envelope = _build_success_runtime_envelope(
            task_id="task-harness-comment-collection-2",
            adapter_key=TEST_ADAPTER_KEY,
            capability="comment_collection",
            payload=payload,
            target_type="content",
            target_value="content-001",
        )
        result = validate_contract_sample(
            ContractSampleDefinition(
                sample_id="comment-collection-target-drift",
                expected_outcome="success",
                target_type="content",
                target_value="content-001",
            ),
            HarnessExecutionResult(runtime_envelope=envelope),
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_success_payload")
        self.assertEqual(result["verdict"], "contract_violation")

    def test_contract_harness_uses_comment_request_cursor_context(self) -> None:
        payload = make_comment_collection_reply_result(root_comment_ref="comment:other-root")
        envelope = _build_success_runtime_envelope(
            task_id="task-harness-comment-collection-3",
            adapter_key=TEST_ADAPTER_KEY,
            capability="comment_collection",
            payload=payload,
            target_type="content",
            target_value="content-001",
            request_cursor={"reply_cursor": make_comment_reply_cursor(comment_ref="comment:root-1")},
        )
        result = validate_contract_sample(
            ContractSampleDefinition(
                sample_id="comment-collection-cursor-drift",
                expected_outcome="success",
                target_type="content",
                target_value="content-001",
                request_cursor={"reply_cursor": make_comment_reply_cursor(comment_ref="comment:root-1")},
            ),
            HarnessExecutionResult(runtime_envelope=envelope),
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_success_payload")
        self.assertEqual(result["verdict"], "contract_violation")

    def test_execute_task_builds_success_envelope_from_adapter_payload(self) -> None:
        adapter = SuccessfulAdapter()
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-001",
        )

        self.assertEqual(envelope["task_id"], "task-001")
        self.assertEqual(envelope["adapter_key"], TEST_ADAPTER_KEY)
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
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/posts/2",
            ),
            policy=CollectionPolicy(collection_mode="hybrid"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: adapter},
            task_id_factory=lambda: "task-001b",
        )

        self.assertEqual(envelope["task_id"], "task-001b")
        self.assertEqual(envelope["status"], "success")
        self.assertEqual(envelope["adapter_key"], TEST_ADAPTER_KEY)
        self.assertEqual(envelope["normalized"]["canonical_url"], request.target.target_value)
        self.assertIsInstance(adapter.last_request, AdapterExecutionContext)
        self.assertEqual(adapter.last_request.request.capability, "content_detail")
        self.assertEqual(adapter.last_request.request.target_type, "url")
        self.assertEqual(adapter.last_request.request.target_value, request.target.target_value)
        self.assertEqual(adapter.last_request.request.collection_mode, "hybrid")
        self.assertIsNotNone(adapter.last_request.resource_bundle)
        self.assertEqual(adapter.last_request.resource_bundle.capability, "content_detail_by_url")

    def test_execute_task_accepts_all_shared_execution_control_concurrency_scopes(self) -> None:
        for scope in ("global", "adapter", "adapter_capability"):
            with self.subTest(scope=scope):
                adapter = SuccessfulAdapter()
                request = TaskRequest(
                    adapter_key=TEST_ADAPTER_KEY,
                    capability="content_detail_by_url",
                    input=TaskInput(url=f"https://example.com/posts/{scope}"),
                    execution_control_policy=make_execution_control_policy(scope),
                )

                envelope = execute_task(
                    request,
                    adapters={TEST_ADAPTER_KEY: adapter},
                    task_id_factory=lambda scope=scope: f"task-policy-{scope}",
                )

                self.assertEqual(envelope["status"], "success")
                self.assertEqual(adapter.last_request.execution_control_policy.concurrency.scope, scope)

    def test_execute_task_maps_legacy_and_native_requests_to_same_adapter_projection(self) -> None:
        legacy_adapter = SuccessfulAdapter()
        native_adapter = SuccessfulAdapter()
        legacy_request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/legacy-native"),
        )
        native_request = CoreTaskRequest(
            target=InputTarget(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/posts/legacy-native",
            ),
            policy=CollectionPolicy(collection_mode="hybrid"),
        )

        legacy_envelope = execute_task(
            legacy_request,
            adapters={TEST_ADAPTER_KEY: legacy_adapter},
            task_id_factory=lambda: "task-legacy-map",
        )
        native_envelope = execute_task(
            native_request,
            adapters={TEST_ADAPTER_KEY: native_adapter},
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
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                target_type="unknown_type",
                target_value="https://example.com/posts/2",
            ),
            policy=CollectionPolicy(collection_mode="hybrid"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-invalid-target-type",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_rejects_unknown_collection_mode(self) -> None:
        request = CoreTaskRequest(
            target=InputTarget(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/posts/2",
            ),
            policy=CollectionPolicy(collection_mode="private"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-invalid-collection-mode",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_rejects_non_url_target_at_shared_projection_guard(self) -> None:
        request = CoreTaskRequest(
            target=InputTarget(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                target_type="content_id",
                target_value="abc123",
            ),
            policy=CollectionPolicy(collection_mode="hybrid"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: BroadAxesAdapter()},
            task_id_factory=lambda: "task-non-url-target",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_rejects_public_collection_mode_at_shared_projection_guard(self) -> None:
        request = CoreTaskRequest(
            target=InputTarget(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/posts/2",
            ),
            policy=CollectionPolicy(collection_mode="public"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: BroadAxesAdapter()},
            task_id_factory=lambda: "task-public-mode",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_rejects_authenticated_collection_mode_at_shared_projection_guard(self) -> None:
        request = CoreTaskRequest(
            target=InputTarget(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/posts/2",
            ),
            policy=CollectionPolicy(collection_mode="authenticated"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: BroadAxesAdapter()},
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
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: MissingTargetsAdapter()},
            task_id_factory=lambda: "task-missing-targets",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_targets")

    def test_execute_task_rejects_legacy_request_when_adapter_does_not_declare_hybrid_mode(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: UnsupportedHybridCollectionModeAdapter()},
            task_id_factory=lambda: "task-unsupported-hybrid",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "collection_mode_not_supported")

    def test_execute_task_fails_closed_for_missing_supported_collection_modes(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: MissingCollectionModesAdapter()},
            task_id_factory=lambda: "task-missing-collection-modes",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_collection_modes")

    def test_execute_task_rejects_legacy_and_native_requests_with_same_hybrid_admission_error(self) -> None:
        legacy_request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/no-hybrid"),
        )
        native_request = CoreTaskRequest(
            target=InputTarget(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/posts/no-hybrid",
            ),
            policy=CollectionPolicy(collection_mode="hybrid"),
        )

        legacy_envelope = execute_task(
            legacy_request,
            adapters={TEST_ADAPTER_KEY: UnsupportedHybridCollectionModeAdapter()},
            task_id_factory=lambda: "task-legacy-no-hybrid",
        )
        native_envelope = execute_task(
            native_request,
            adapters={TEST_ADAPTER_KEY: UnsupportedHybridCollectionModeAdapter()},
            task_id_factory=lambda: "task-native-no-hybrid",
        )

        self.assertEqual(legacy_envelope["status"], "failed")
        self.assertEqual(native_envelope["status"], "failed")
        self.assertEqual(legacy_envelope["error"]["category"], "invalid_input")
        self.assertEqual(native_envelope["error"]["category"], "invalid_input")
        self.assertEqual(legacy_envelope["error"]["code"], "collection_mode_not_supported")
        self.assertEqual(native_envelope["error"]["code"], "collection_mode_not_supported")
        self.assertEqual(legacy_envelope["error"]["details"], native_envelope["error"]["details"])

    def test_execute_task_fails_closed_when_adapter_lacks_resource_requirement_declaration(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/posts/missing-resource-requirement"),
            ),
            adapters={TEST_ADAPTER_KEY: MissingResourceRequirementAdapter()},
            task_id_factory=lambda: "task-missing-resource-requirement",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_resource_requirement")

    def test_execute_task_maps_registry_resource_requirement_validation_failure_to_invalid_resource_requirement(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/posts/bad-resource-requirement"),
            ),
            adapters={TEST_ADAPTER_KEY: InvalidResourceRequirementDeclarationAdapter()},
            task_id_factory=lambda: "task-bad-resource-requirement",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_resource_requirement")
        self.assertEqual(
            envelope["error"]["details"]["registry_error_code"],
            "invalid_adapter_resource_requirements",
        )

    def test_execute_task_does_not_misclassify_sibling_declaration_failure_as_requested_invalid_resource_requirement(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/posts/valid-request-invalid-sibling"),
            ),
            adapters={
                TEST_ADAPTER_KEY: SuccessfulAdapter(),
                "douyin": InvalidSiblingResourceRequirementDeclarationAdapter(),
            },
            task_id_factory=lambda: "task-valid-request-invalid-sibling",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_resource_requirements")
        self.assertNotIn("registry_error_code", envelope["error"]["details"])

    def test_execute_task_maps_none_resource_requirement_collection_to_invalid_resource_requirement(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/posts/none-resource-requirement-collection"),
            ),
            adapters={TEST_ADAPTER_KEY: NoneResourceRequirementCollectionAdapter()},
            task_id_factory=lambda: "task-none-resource-requirement-collection",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_resource_requirement")
        self.assertEqual(
            envelope["error"]["details"]["registry_error_code"],
            "invalid_adapter_resource_requirements",
        )

    def test_execute_task_maps_extra_field_resource_requirement_declaration_to_invalid_resource_requirement(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/posts/extra-field-resource-requirement"),
            ),
            adapters={TEST_ADAPTER_KEY: ExtraFieldResourceRequirementDeclarationAdapter()},
            task_id_factory=lambda: "task-extra-field-resource-requirement",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_resource_requirement")
        self.assertEqual(
            envelope["error"]["details"]["registry_error_code"],
            "invalid_adapter_resource_requirements",
        )

    def test_execute_task_keeps_none_mode_declarations_unreachable_until_registry_baseline_exists(self) -> None:
        with mock.patch(
            "syvert.runtime.acquire_runtime_resource_bundle",
            side_effect=AssertionError("acquire should not run for none-mode runtime declarations"),
        ):
            envelope = execute_task(
                TaskRequest(
                    adapter_key=TEST_ADAPTER_KEY,
                    capability="content_detail_by_url",
                    input=TaskInput(url="https://example.com/posts/none-mode-runtime-path"),
                ),
                adapters={TEST_ADAPTER_KEY: NoneModeResourceRequirementDeclarationAdapter()},
                task_id_factory=lambda: "task-none-mode-runtime-path",
            )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_resource_requirement")
        self.assertEqual(
            envelope["error"]["details"]["registry_error_code"],
            "invalid_adapter_resource_requirements",
        )

    def test_execute_task_rejects_invalid_runtime_capability_projection_before_task_record(self) -> None:
        with mock.patch.dict(
            runtime_module.RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE,
            {
                (
                    runtime_module.CONTENT_DETAIL_BY_URL,
                    runtime_module.LEGACY_COLLECTION_MODE,
                ): ("account", "browser_state")
            },
            clear=True,
        ), mock.patch(
            "syvert.runtime.acquire_runtime_resource_bundle",
            side_effect=AssertionError("acquire should not run for invalid runtime capability projections"),
        ):
            outcome = execute_task_with_record(
                TaskRequest(
                    adapter_key=TEST_ADAPTER_KEY,
                    capability="content_detail_by_url",
                    input=TaskInput(url="https://example.com/posts/invalid-runtime-capability-projection"),
                ),
                adapters={TEST_ADAPTER_KEY: NeverCalledAdapter()},
                task_id_factory=lambda: "task-invalid-runtime-capability-projection",
            )

        self.assertEqual(outcome.envelope["status"], "failed")
        self.assertEqual(outcome.envelope["error"]["category"], "runtime_contract")
        self.assertEqual(outcome.envelope["error"]["code"], "invalid_resource_requirement")
        self.assertEqual(
            outcome.envelope["error"]["details"]["unknown_capabilities"],
            ("browser_state",),
        )
        self.assertIsNone(outcome.task_record)

    def test_execute_task_returns_resource_unavailable_when_runtime_capability_projection_is_unmatched(self) -> None:
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
                    input=TaskInput(url="https://example.com/posts/unmatched-runtime-capabilities"),
                ),
                adapters={TEST_ADAPTER_KEY: NeverCalledAdapter()},
                task_id_factory=lambda: "task-unmatched-runtime-capabilities",
            )

        self.assertEqual(outcome.envelope["status"], "failed")
        self.assertEqual(outcome.envelope["error"]["category"], "runtime_contract")
        self.assertEqual(outcome.envelope["error"]["code"], "resource_unavailable")
        self.assertIsNotNone(outcome.task_record)
        self.assertEqual(outcome.task_record.status, "failed")
        self.assertEqual(outcome.task_record.result.envelope["error"]["code"], "resource_unavailable")
        self.assertEqual(
            outcome.envelope["runtime_failure_signal"]["task_record_ref"],
            "task_record:task-unmatched-runtime-capabilities",
        )
        self.assertEqual(
            outcome.task_record.result.envelope["runtime_failure_signal"]["task_record_ref"],
            "task_record:task-unmatched-runtime-capabilities",
        )

    def test_execute_task_maps_v2_unmatched_profiles_to_resource_unavailable(self) -> None:
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
                    input=TaskInput(url="https://example.com/posts/unmatched-v2-runtime-capabilities"),
                ),
                adapters={TEST_ADAPTER_KEY: MultiProfileResourceRequirementAdapter()},
                task_id_factory=lambda: "task-unmatched-v2-runtime-capabilities",
            )

        self.assertEqual(outcome.envelope["status"], "failed")
        self.assertEqual(outcome.envelope["error"]["category"], "runtime_contract")
        self.assertEqual(outcome.envelope["error"]["code"], "resource_unavailable")
        self.assertIn("resource_requirement_profiles", outcome.envelope["error"]["details"])
        self.assertNotIn("required_capabilities", outcome.envelope["error"]["details"])
        self.assertIsNotNone(outcome.task_record)
        self.assertEqual(outcome.task_record.result.envelope["error"]["code"], "resource_unavailable")

    def test_execute_task_rejects_unsupported_capability(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="search",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-unsupported",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_capability")

    def test_execute_task_rejects_success_without_raw_payload(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: MissingRawAdapter()},
            task_id_factory=lambda: "task-003",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_success_payload")

    def test_execute_task_fails_closed_when_adapter_returns_none(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: NonePayloadAdapter()},
            task_id_factory=lambda: "task-004",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_success_payload")

    def test_execute_task_fails_closed_when_adapter_returns_non_mapping_payload(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: ListPayloadAdapter()},
            task_id_factory=lambda: "task-005",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_success_payload")

    def test_execute_task_fails_closed_when_adapter_raises_generic_exception(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: CrashingAdapter()},
            task_id_factory=lambda: "task-006",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "adapter_execution_error")

    def test_execute_task_handles_platform_error_with_non_mapping_details(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: PlatformErrorWithBadDetailsAdapter()},
            task_id_factory=lambda: "task-007",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "platform")
        self.assertEqual(envelope["error"]["code"], "platform_broken")
        self.assertEqual(set(envelope["error"]["details"]), {"resource_trace_refs", "task_record_ref"})
        self.assertTrue(envelope["error"]["details"]["resource_trace_refs"])

    def test_execute_task_wraps_platform_error(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: PlatformFailureAdapter()},
            task_id_factory=lambda: "task-platform-failure",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "platform")
        self.assertEqual(envelope["error"]["code"], "content_not_found")
        self.assertEqual(envelope["error"]["details"]["reason"], "missing")

    def test_execute_task_releases_bundle_when_host_side_validation_fails_after_acquire(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
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
                adapters={TEST_ADAPTER_KEY: NeverCalledAdapter()},
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
        trace_events = self.make_trace_store().task_usage_log("task-host-validation").events
        self.assertEqual([event.event_type for event in trace_events], ["acquired", "acquired", "released", "released"])

    def test_execute_task_rejects_bundle_with_mismatched_lease_id_before_adapter_and_settles_real_lease(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
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
                adapters={TEST_ADAPTER_KEY: NeverCalledAdapter()},
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
            adapter_key=TEST_ADAPTER_KEY,
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
                adapters={TEST_ADAPTER_KEY: NeverCalledAdapter()},
                task_id_factory=lambda: "task-host-validation-material",
            )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_resource_bundle")
        lease = self.lease_for_task("task-host-validation-material")
        self.assertEqual(lease.target_status_after_release, "AVAILABLE")
        self.assertEqual(lease.release_reason, "host_side_bundle_validation_failed")
        self.assertEqual(set(self.resource_statuses().values()), {"AVAILABLE"})

    def test_execute_task_derives_trace_store_as_lifecycle_sibling_when_only_lifecycle_store_is_injected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lifecycle_path = Path(temp_dir) / "custom-resource-lifecycle.json"
            derived_trace_path = lifecycle_path.with_name("resource-trace-events.jsonl")
            fallback_home = Path(temp_dir) / "isolated-home"
            fallback_trace_path = fallback_home / ".syvert" / "resource-trace-events.jsonl"
            lifecycle_store = LocalResourceLifecycleStore(lifecycle_path)
            lifecycle_store.seed_resources(
                (
                    ResourceRecord(
                        resource_id="account-derived-001",
                        resource_type="account",
                        status="AVAILABLE",
                        material=managed_account_material(generic_account_material(), adapter_key=TEST_ADAPTER_KEY),
                    ),
                    ResourceRecord(
                        resource_id="proxy-derived-001",
                        resource_type="proxy",
                        status="AVAILABLE",
                        material=proxy_material(),
                    ),
                )
            )

            original_trace_store_env = os.environ.pop("SYVERT_RESOURCE_TRACE_STORE_FILE", None)
            try:
                with mock.patch.dict(os.environ, {"HOME": str(fallback_home)}, clear=False):
                    with mock.patch(
                        "syvert.resource_trace_store.default_resource_trace_store",
                        side_effect=AssertionError("runtime should derive trace store from injected lifecycle store"),
                    ):
                        envelope = execute_task(
                            TaskRequest(
                                adapter_key=TEST_ADAPTER_KEY,
                                capability="content_detail_by_url",
                                input=TaskInput(url="https://example.com/posts/derived-trace-store"),
                            ),
                            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
                            task_id_factory=lambda: "task-derived-trace-store",
                            resource_lifecycle_store=lifecycle_store,
                        )
                self.assertEqual(envelope["status"], "success")
                self.assertTrue(derived_trace_path.exists())
                self.assertEqual(derived_trace_path.parent, lifecycle_path.parent)
                self.assertFalse(fallback_trace_path.exists())
                trace_events = LocalResourceTraceStore(derived_trace_path).task_usage_log(
                    "task-derived-trace-store"
                ).events
                self.assertEqual(
                    [event.event_type for event in trace_events],
                    ["acquired", "acquired", "released", "released"],
                )
            finally:
                if original_trace_store_env is not None:
                    os.environ["SYVERT_RESOURCE_TRACE_STORE_FILE"] = original_trace_store_env

    def test_execute_task_settles_success_without_hint_as_available(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/posts/no-hint-success"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-no-hint-success",
        )

        self.assertEqual(envelope["status"], "success")
        lease = self.lease_for_task("task-no-hint-success")
        self.assertEqual(lease.capability, "content_detail_by_url")
        self.assertEqual(lease.target_status_after_release, "AVAILABLE")
        self.assertEqual(lease.release_reason, "adapter_completed_without_disposition_hint")
        self.assertEqual(set(self.resource_statuses().values()), {"AVAILABLE"})
        trace_events = self.make_trace_store().task_usage_log("task-no-hint-success").events
        self.assertEqual([event.event_type for event in trace_events], ["acquired", "acquired", "released", "released"])
        self.assertEqual({event.bundle_id for event in trace_events}, {lease.bundle_id})

    def test_execute_task_settles_failure_without_hint_as_available(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/posts/no-hint-failure"),
            ),
            adapters={TEST_ADAPTER_KEY: PlatformFailureAdapter()},
            task_id_factory=lambda: "task-no-hint-failure",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["code"], "content_not_found")
        lease = self.lease_for_task("task-no-hint-failure")
        self.assertEqual(lease.target_status_after_release, "AVAILABLE")
        self.assertEqual(lease.release_reason, "adapter_failed_without_disposition_hint")
        self.assertEqual(set(self.resource_statuses().values()), {"AVAILABLE"})
        trace_events = self.make_trace_store().task_usage_log("task-no-hint-failure").events
        self.assertEqual([event.event_type for event in trace_events], ["acquired", "acquired", "released", "released"])

    def test_execute_task_applies_invalidating_hint_without_leaking_internal_field(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/posts/invalidating-hint"),
            ),
            adapters={TEST_ADAPTER_KEY: InvalidatingHintAdapter()},
            task_id_factory=lambda: "task-invalidating-hint",
        )

        self.assertEqual(envelope["status"], "success")
        self.assertNotIn("resource_disposition_hint", envelope)
        lease = self.lease_for_task("task-invalidating-hint")
        self.assertEqual(lease.target_status_after_release, "INVALID")
        self.assertEqual(lease.release_reason, "account_invalidated_by_adapter")
        self.assertEqual(set(self.resource_statuses().values()), {"INVALID"})
        trace_events = self.make_trace_store().task_usage_log("task-invalidating-hint").events
        self.assertEqual([event.event_type for event in trace_events], ["acquired", "acquired", "invalidated", "invalidated"])

    def test_execute_task_rejects_mismatched_hint_lease_id_and_still_settles_bundle(self) -> None:
        envelope = execute_task(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/posts/hint-mismatch"),
            ),
            adapters={TEST_ADAPTER_KEY: LeaseIdMismatchHintAdapter()},
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
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/posts/hint-bad-status"),
            ),
            adapters={TEST_ADAPTER_KEY: InvalidTargetStatusHintAdapter()},
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
                "adapter_key": TEST_ADAPTER_KEY,
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
                    adapter_key=TEST_ADAPTER_KEY,
                    capability="content_detail_by_url",
                    input=TaskInput(url="https://example.com/posts/release-success"),
                ),
                adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
                task_id_factory=lambda: "task-release-overrides-success",
            )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["code"], "release_write_failed")

    def test_execute_task_release_failure_overrides_original_failure(self) -> None:
        with mock.patch(
            "syvert.resource_lifecycle.release",
            return_value={
                "task_id": "task-release-overrides-failure",
                "adapter_key": TEST_ADAPTER_KEY,
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
                    adapter_key=TEST_ADAPTER_KEY,
                    capability="content_detail_by_url",
                    input=TaskInput(url="https://example.com/posts/release-failure"),
                ),
                adapters={TEST_ADAPTER_KEY: PlatformFailureAdapter()},
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
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: PrePlatformValidationAdapter()},
            task_id_factory=lambda: "task-preplatform-invalid-input",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "adapter_precheck_failed")

    def test_execute_task_rejects_empty_task_id_from_factory(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertIsInstance(envelope["task_id"], str)
        self.assertTrue(envelope["task_id"])
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_task_id")

    def test_execute_task_rejects_non_string_task_id_from_factory(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: 123,  # type: ignore[return-value]
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertIsInstance(envelope["task_id"], str)
        self.assertTrue(envelope["task_id"])
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_task_id")

    def test_execute_task_fails_closed_when_task_id_factory_raises(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertIsInstance(envelope["task_id"], str)
        self.assertTrue(envelope["task_id"])
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_task_id")

    def test_execute_task_rejects_extended_task_input_shape(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=ExtendedTaskInput(
                url="https://example.com/posts/1",
                platform_hint="xhs",
            ),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-extra-shape",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_rejects_extended_task_request_shape(self) -> None:
        request = ExtendedTaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
            extra="leaks",
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-extra-request-shape",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_fails_closed_for_malformed_request_mapping(self) -> None:
        envelope = execute_task(
            {
                "adapter_key": TEST_ADAPTER_KEY,
                "capability": "content_detail_by_url",
                "input": {"url": "https://example.com/posts/1"},
            },  # type: ignore[arg-type]
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-malformed-request",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["task_id"], "task-malformed-request")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_fails_closed_for_request_mapping_that_raises_on_get(self) -> None:
        envelope = execute_task(
            ExplodingRequestMapping(),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-exploding-request",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["task_id"], "task-exploding-request")
        self.assertEqual(envelope["error"]["category"], "invalid_input")
        self.assertEqual(envelope["error"]["code"], "invalid_task_request")

    def test_execute_task_fails_closed_for_none_supported_capabilities(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: NoneCapabilitiesAdapter()},
            task_id_factory=lambda: "task-none-caps",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_capabilities")

    def test_execute_task_fails_closed_for_missing_supported_capabilities(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: MissingCapabilitiesAdapter()},
            task_id_factory=lambda: "task-missing-caps",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_capabilities")

    def test_execute_task_fails_closed_for_adapter_registry_that_raises_on_items(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
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
            adapter_key=TEST_ADAPTER_KEY,
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
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: NonContainerCapabilitiesAdapter()},
            task_id_factory=lambda: "task-non-container-caps",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_capabilities")

    def test_execute_task_fails_closed_for_non_string_supported_capability(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: NonStringCapabilitiesAdapter()},
            task_id_factory=lambda: "task-non-string-caps",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_capabilities")

    def test_execute_task_fails_closed_for_broken_supported_capabilities_iterable(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: BrokenIterableCapabilitiesAdapter()},
            task_id_factory=lambda: "task-broken-caps",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_capabilities")

    def test_execute_task_fails_closed_for_missing_execute_contract(self) -> None:
        request = TaskRequest(
            adapter_key=TEST_ADAPTER_KEY,
            capability="content_detail_by_url",
            input=TaskInput(url="https://example.com/posts/1"),
        )

        envelope = execute_task(
            request,
            adapters={TEST_ADAPTER_KEY: MissingExecuteAdapter()},
            task_id_factory=lambda: "task-missing-execute",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_declaration")


if __name__ == "__main__":
    unittest.main()
