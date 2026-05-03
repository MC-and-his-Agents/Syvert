from __future__ import annotations

from copy import deepcopy
from typing import Any

from syvert.adapter_provider_compatibility_decision import baseline_compatibility_decision_context
from tests.runtime.adapter_capability_requirement_fixtures import valid_adapter_capability_requirement
from tests.runtime.provider_capability_offer_fixtures import valid_provider_capability_offer


def valid_compatibility_decision_input(
    *,
    adapter_key: str = "xhs",
    provider_key: str = "native_xhs_detail",
) -> dict[str, Any]:
    return {
        "requirement": valid_adapter_capability_requirement(adapter_key=adapter_key),
        "offer": valid_provider_capability_offer(adapter_key=adapter_key, provider_key=provider_key),
        "decision_context": dict(baseline_compatibility_decision_context().__dict__),
    }


def copy_decision_input(input_value: dict[str, Any] | None = None) -> dict[str, Any]:
    return deepcopy(input_value if input_value is not None else valid_compatibility_decision_input())
