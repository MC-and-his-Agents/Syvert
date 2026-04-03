from __future__ import annotations

from syvert.runtime import TaskRequest


class SuccessfulAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail_by_url"})

    def execute(self, request: TaskRequest) -> dict[str, object]:
        return {
            "raw": {"id": "raw-cli-module-1", "url": request.input.url},
            "normalized": {
                "platform": "stub",
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
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail_by_url"})

    def execute(self, request: TaskRequest) -> dict[str, object]:
        return {
            "raw": {"id": "raw-cli-module-2", "bad": object()},
            "normalized": {
                "platform": "stub",
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
    return {"stub": SuccessfulAdapter()}


def build_unserializable_adapters() -> dict[str, object]:
    return {"stub": UnserializableSuccessAdapter()}
