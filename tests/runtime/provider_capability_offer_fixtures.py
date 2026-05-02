from __future__ import annotations

from copy import deepcopy
from typing import Any


PROVIDER_OFFER_EVIDENCE_REF = "fr-0025:offer-manifest-fixture-validator:content-detail-by-url-hybrid"
ADAPTER_BINDING_EVIDENCE_REF = "fr-0021:adapter-provider-port-boundary:adapter-owned-provider-port"


def valid_provider_capability_offer(
    *,
    adapter_key: str = "xhs",
    provider_key: str = "native_xhs_detail",
) -> dict[str, Any]:
    resource_profile_evidence_refs = [
        "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
        "fr-0027:profile:content-detail-by-url-hybrid:account",
    ]
    return {
        "provider_key": provider_key,
        "adapter_binding": {
            "adapter_key": adapter_key,
            "binding_scope": "adapter_bound",
            "provider_port_ref": f"{adapter_key}:adapter-owned-provider-port",
        },
        "capability_offer": {
            "capability": "content_detail",
            "operation": "content_detail_by_url",
            "target_type": "url",
            "collection_mode": "hybrid",
        },
        "resource_support": {
            "supported_profiles": [
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
            "resource_profile_contract_ref": "FR-0027",
        },
        "error_carrier": {
            "invalid_offer_code": "invalid_provider_offer",
            "provider_unavailable_code": "provider_unavailable",
            "contract_violation_code": "provider_contract_violation",
            "adapter_mapping_required": True,
        },
        "version": {
            "contract_version": "v0.8.0",
            "requirement_contract_ref": "FR-0024",
            "resource_profile_contract_ref": "FR-0027",
            "provider_port_boundary_ref": "FR-0021",
        },
        "evidence": {
            "provider_offer_evidence_refs": [PROVIDER_OFFER_EVIDENCE_REF],
            "resource_profile_evidence_refs": resource_profile_evidence_refs,
            "adapter_binding_evidence_refs": [ADAPTER_BINDING_EVIDENCE_REF],
        },
        "lifecycle": {
            "invoked_by_adapter_only": True,
            "core_discovery_allowed": False,
            "consumes_adapter_execution_context": True,
            "uses_existing_resource_bundle_view": True,
            "adapter_error_mapping_required": True,
        },
        "observability": {
            "offer_id": (
                f"{adapter_key}:{provider_key}:content_detail:"
                "content_detail_by_url:url:hybrid:v0.8.0"
            ),
            "provider_key": provider_key,
            "adapter_key": adapter_key,
            "capability": "content_detail",
            "operation": "content_detail_by_url",
            "profile_keys": ["account_proxy", "account"],
            "proof_refs": resource_profile_evidence_refs,
            "contract_version": "v0.8.0",
            "validation_outcome_fields": [
                "validation_status",
                "error_code",
                "failure_category",
            ],
        },
        "fail_closed": True,
    }


def copy_offer(offer: dict[str, Any] | None = None) -> dict[str, Any]:
    return deepcopy(offer if offer is not None else valid_provider_capability_offer())
