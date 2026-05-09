from __future__ import annotations

from copy import deepcopy
from typing import Any


CAPABILITY_REQUIREMENT_EVIDENCE_REF = "fr-0024:manifest-fixture-validator:content-detail-by-url-hybrid"


def valid_adapter_capability_requirement(
    *,
    adapter_key: str = "xhs",
    capability: str = "content_detail",
    operation: str = "content_detail_by_url",
    target_type: str = "url",
    collection_mode: str = "hybrid",
) -> dict[str, Any]:
    return {
        "adapter_key": adapter_key,
        "capability": capability,
        "execution_requirement": {
            "operation": operation,
            "target_type": target_type,
            "collection_mode": collection_mode,
        },
        "resource_requirement": valid_resource_requirement(adapter_key=adapter_key, capability=capability),
        "evidence": {
            "resource_profile_evidence_refs": [
                "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                "fr-0027:profile:content-detail-by-url-hybrid:account",
            ],
            "capability_requirement_evidence_refs": [CAPABILITY_REQUIREMENT_EVIDENCE_REF],
        },
        "lifecycle": {
            "requires_core_resource_bundle": True,
            "resource_profiles_drive_admission": True,
            "uses_existing_disposition_hint": True,
        },
        "observability": {
            "requirement_id": f"{adapter_key}:{capability}:{operation}:{target_type}:{collection_mode}",
            "profile_keys": ["account_proxy", "account"],
            "proof_refs": [
                "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                "fr-0027:profile:content-detail-by-url-hybrid:account",
            ],
            "admission_outcome_fields": [
                "match_status",
                "error_code",
                "failure_category",
            ],
        },
        "fail_closed": True,
    }


def valid_resource_requirement(
    *,
    adapter_key: str = "xhs",
    capability: str = "content_detail",
) -> dict[str, Any]:
    return {
        "adapter_key": adapter_key,
        "capability": capability,
        "resource_requirement_profiles": [
            {
                "profile_key": "account_proxy",
                "resource_dependency_mode": "required",
                "required_capabilities": ["account", "proxy"],
                "evidence_refs": ["fr-0027:profile:content-detail-by-url-hybrid:account-proxy"],
            },
            {
                "profile_key": "account",
                "resource_dependency_mode": "required",
                "required_capabilities": ["account"],
                "evidence_refs": ["fr-0027:profile:content-detail-by-url-hybrid:account"],
            },
        ],
    }


def copy_requirement(requirement: dict[str, Any] | None = None) -> dict[str, Any]:
    return deepcopy(requirement if requirement is not None else valid_adapter_capability_requirement())
