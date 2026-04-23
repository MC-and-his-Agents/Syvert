from __future__ import annotations

from tests.runtime.resource_fixtures import baseline_resource_requirement_declarations
from syvert.runtime import TaskRequest

TEST_ADAPTER_KEY = "xhs"


class SuccessfulAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(adapter_key=TEST_ADAPTER_KEY)

    def execute(self, request: TaskRequest) -> dict[str, object]:
        return {
            "raw": {"id": "raw-cli-module-1", "url": request.input.url},
            "normalized": {
                "platform": TEST_ADAPTER_KEY,
                "content_id": "content-cli-module-1",
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


class UnserializableSuccessAdapter:
    adapter_key = TEST_ADAPTER_KEY
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = baseline_resource_requirement_declarations(adapter_key=TEST_ADAPTER_KEY)

    def execute(self, request: TaskRequest) -> dict[str, object]:
        return {
            "raw": {"id": "raw-cli-module-2", "bad": object()},
            "normalized": {
                "platform": TEST_ADAPTER_KEY,
                "content_id": "content-cli-module-2",
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


def build_adapters() -> dict[str, object]:
    return {TEST_ADAPTER_KEY: SuccessfulAdapter()}


def build_unserializable_adapters() -> dict[str, object]:
    return {TEST_ADAPTER_KEY: UnserializableSuccessAdapter()}
