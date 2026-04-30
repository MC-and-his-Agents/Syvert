from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from syvert.runtime import AdapterExecutionContext, PlatformAdapterError

THIRD_PARTY_FIXTURE_ADAPTER_KEY = "community_content"
THIRD_PARTY_FIXTURE_SDK_CONTRACT_ID = "syvert-adapter-runtime-v0.8.0"
THIRD_PARTY_SUCCESS_FIXTURE_ID = "third-party-content-detail-success"
THIRD_PARTY_ERROR_MAPPING_FIXTURE_ID = "third-party-content-detail-error-mapping"


def third_party_resource_requirement_declarations() -> tuple[dict[str, Any], ...]:
    return (
        {
            "adapter_key": THIRD_PARTY_FIXTURE_ADAPTER_KEY,
            "capability": "content_detail",
            "resource_requirement_profiles": (
                {
                    "profile_key": "account_proxy",
                    "resource_dependency_mode": "required",
                    "required_capabilities": ("account", "proxy"),
                    "evidence_refs": ("fr-0027:profile:content-detail-by-url-hybrid:account-proxy",),
                },
                {
                    "profile_key": "account",
                    "resource_dependency_mode": "required",
                    "required_capabilities": ("account",),
                    "evidence_refs": ("fr-0027:profile:content-detail-by-url-hybrid:account",),
                },
            ),
        },
    )


def minimal_third_party_adapter_manifest() -> dict[str, Any]:
    return {
        "adapter_key": THIRD_PARTY_FIXTURE_ADAPTER_KEY,
        "sdk_contract_id": THIRD_PARTY_FIXTURE_SDK_CONTRACT_ID,
        "supported_capabilities": ("content_detail",),
        "supported_targets": ("url",),
        "supported_collection_modes": ("hybrid",),
        "resource_requirement_declarations": third_party_resource_requirement_declarations(),
        "result_contract": {
            "success_payload_fields": ("raw", "normalized"),
            "normalized_owner": "adapter",
        },
        "error_mapping": {
            "content_not_found": {
                "category": "platform",
                "code": "content_not_found",
                "message": "content is unavailable or deleted",
            },
        },
        "fixture_refs": (
            THIRD_PARTY_SUCCESS_FIXTURE_ID,
            THIRD_PARTY_ERROR_MAPPING_FIXTURE_ID,
        ),
        "contract_test_profile": "adapter_only_content_detail_v0_8",
    }


def minimal_third_party_adapter_fixtures() -> tuple[dict[str, Any], ...]:
    return (
        {
            "fixture_id": THIRD_PARTY_SUCCESS_FIXTURE_ID,
            "manifest_ref": THIRD_PARTY_FIXTURE_ADAPTER_KEY,
            "case_type": "success",
            "input": {
                "operation": "content_detail_by_url",
                "capability": "content_detail",
                "target_type": "url",
                "target_value": "https://contract-host/third-party/success",
                "collection_mode": "hybrid",
                "resource_profile_key": "account_proxy",
            },
            "expected": {
                "status": "success",
                "required_payload_fields": ("raw", "normalized"),
            },
        },
        {
            "fixture_id": THIRD_PARTY_ERROR_MAPPING_FIXTURE_ID,
            "manifest_ref": THIRD_PARTY_FIXTURE_ADAPTER_KEY,
            "case_type": "error_mapping",
            "input": {
                "operation": "content_detail_by_url",
                "capability": "content_detail",
                "target_type": "url",
                "target_value": "https://contract-host/third-party/content-not-found",
                "collection_mode": "hybrid",
                "resource_profile_key": "account_proxy",
            },
            "expected": {
                "status": "failed",
                "error": {
                    "source_error": "content_not_found",
                    "category": "platform",
                    "code": "content_not_found",
                },
            },
        },
    )


def _success_payload(url: str) -> dict[str, Any]:
    return {
        "raw": {
            "content_id": "third-party-raw-001",
            "canonical_url": url,
        },
        "normalized": {
            "platform": "third_party_fixture",
            "content_id": "third-party-content-001",
            "content_type": "unknown",
            "canonical_url": url,
            "title": "Third-party adapter fixture",
            "body_text": "deterministic contract fixture body",
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
class ThirdPartyContractFixtureAdapter:
    success_payload_shape: str = "valid"
    error_code: str = "content_not_found"
    last_resource_slots: tuple[str, ...] | None = None

    adapter_key = THIRD_PARTY_FIXTURE_ADAPTER_KEY
    sdk_contract_id = THIRD_PARTY_FIXTURE_SDK_CONTRACT_ID
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = third_party_resource_requirement_declarations()
    result_contract = {
        "success_payload_fields": ("raw", "normalized"),
        "normalized_owner": "adapter",
    }
    error_mapping = {
        "content_not_found": {
            "category": "platform",
            "code": "content_not_found",
            "message": "content is unavailable or deleted",
        },
    }
    fixture_refs = (
        THIRD_PARTY_SUCCESS_FIXTURE_ID,
        THIRD_PARTY_ERROR_MAPPING_FIXTURE_ID,
    )
    contract_test_profile = "adapter_only_content_detail_v0_8"

    def execute(self, request: AdapterExecutionContext) -> dict[str, Any]:
        self.last_resource_slots = (
            request.resource_bundle.requested_slots
            if request.resource_bundle is not None
            else None
        )
        if "content-not-found" in request.target_value:
            raise PlatformAdapterError(
                code=self.error_code,
                message="third-party fixture mapped platform error",
                details={"source_error": "content_not_found"},
            )
        if self.success_payload_shape == "missing_normalized":
            return {"raw": {"content_id": "third-party-invalid-raw"}}
        return _success_payload(request.target_value)


__all__ = [
    "THIRD_PARTY_ERROR_MAPPING_FIXTURE_ID",
    "THIRD_PARTY_FIXTURE_ADAPTER_KEY",
    "THIRD_PARTY_FIXTURE_SDK_CONTRACT_ID",
    "THIRD_PARTY_SUCCESS_FIXTURE_ID",
    "ThirdPartyContractFixtureAdapter",
    "minimal_third_party_adapter_fixtures",
    "minimal_third_party_adapter_manifest",
    "third_party_resource_requirement_declarations",
]
