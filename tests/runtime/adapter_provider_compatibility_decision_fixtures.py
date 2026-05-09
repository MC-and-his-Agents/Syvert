from __future__ import annotations

from copy import deepcopy
from typing import Any

from tests.runtime.adapter_capability_requirement_fixtures import valid_adapter_capability_requirement
from tests.runtime.provider_capability_offer_fixtures import valid_provider_capability_offer


def valid_compatibility_decision_input(
    *,
    adapter_key: str = "xhs",
    provider_key: str = "native_xhs_detail",
    capability: str = "content_detail",
    operation: str = "content_detail_by_url",
    target_type: str = "url",
    collection_mode: str = "hybrid",
) -> dict[str, Any]:
    return {
        "requirement": valid_adapter_capability_requirement(
            adapter_key=adapter_key,
            capability=capability,
            operation=operation,
            target_type=target_type,
            collection_mode=collection_mode,
        ),
        "offer": valid_provider_capability_offer(
            adapter_key=adapter_key,
            provider_key=provider_key,
            capability=capability,
            operation=operation,
            target_type=target_type,
            collection_mode=collection_mode,
        ),
        "decision_context": {
            "decision_id": "compatibility-decision-001",
            "contract_version": "v0.8.0",
            "requirement_contract_ref": "FR-0024",
            "offer_contract_ref": "FR-0025",
            "resource_profile_contract_ref": "FR-0027",
            "provider_port_boundary_ref": "FR-0021",
            "fail_closed": True,
        },
    }


def copy_decision_input(input_value: dict[str, Any] | None = None) -> dict[str, Any]:
    return deepcopy(input_value if input_value is not None else valid_compatibility_decision_input())
