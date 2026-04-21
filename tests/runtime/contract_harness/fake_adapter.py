from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from syvert.runtime import AdapterExecutionContext, PlatformAdapterError

FakeAdapterScenario = Literal["success", "legal_failure", "illegal_payload"]


def _build_success_payload(url: str) -> dict[str, Any]:
    return {
        "raw": {"content_id": "fake-raw-001", "canonical_url": url},
        "normalized": {
            "platform": "fake",
            "content_id": "fake-content-001",
            "content_type": "unknown",
            "canonical_url": url,
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


@dataclass
class FakeContractAdapter:
    scenario: FakeAdapterScenario = "success"
    last_request: AdapterExecutionContext | None = None

    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: AdapterExecutionContext) -> dict[str, Any]:
        self.last_request = request
        if self.scenario == "success":
            return _build_success_payload(request.target_value)
        if self.scenario == "legal_failure":
            raise PlatformAdapterError(
                code="content_not_found",
                message="fake adapter returns controlled legal failure",
                details={"scenario": self.scenario},
            )
        if self.scenario == "illegal_payload":
            # Deliberately violate success payload contract to exercise Core fail-closed path.
            return {"raw": {"content_id": "fake-invalid-only-raw"}}
        raise RuntimeError(f"unsupported fake adapter scenario: {self.scenario}")
