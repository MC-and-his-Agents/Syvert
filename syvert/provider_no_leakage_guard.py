from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
import re
from typing import Any

from syvert.adapter_provider_compatibility_decision import AdapterProviderCompatibilityDecision


PROVIDER_NO_LEAKAGE_STATUS_PASSED = "passed"
PROVIDER_NO_LEAKAGE_STATUS_FAILED = "failed"
PROVIDER_NO_LEAKAGE_ERROR_PROVIDER_LEAKAGE_DETECTED = "provider_leakage_detected"

FORBIDDEN_CORE_PROVIDER_FIELD_TOKENS = frozenset(
    {
        "provider_capability",
        "provider_key",
        "provider_registry",
        "provider_registry_entry",
        "offer_id",
        "selected_provider",
        "provider_selector",
        "provider_selection",
        "provider_routing",
        "provider_offer",
        "provider_profile",
        "compatibility_decision",
        "selector",
        "routing",
        "routing_policy",
        "priority",
        "rank",
        "score",
        "fallback",
        "fallback_order",
        "preferred_profile",
        "marketplace",
        "marketplace_listing",
        "provider_product_support",
        "provider_lifecycle",
        "provider_lease",
        "resource_supply",
        "resource_pool",
        "account_pool",
        "proxy_pool",
        "core_provider_registry",
        "core_provider_discovery",
    }
)

FORBIDDEN_CORE_PROVIDER_VALUE_TOKENS = frozenset(
    {
        "provider_unavailable",
        "provider_contract_violation",
        "invalid_provider_offer",
    }
)


@dataclass(frozen=True)
class ProviderNoLeakageEvidence:
    surface_name: str
    forbidden_field_paths: tuple[str, ...]
    forbidden_value_paths: tuple[str, ...]
    provider_identity_values_checked: tuple[str, ...]


@dataclass(frozen=True)
class ProviderNoLeakageGuardResult:
    status: str
    error_code: str | None
    evidence: ProviderNoLeakageEvidence


def guard_core_provider_no_leakage(
    *,
    surface_name: str,
    surface: Any,
    decision: AdapterProviderCompatibilityDecision | None = None,
    provider_identity_values: Sequence[str] = (),
) -> ProviderNoLeakageGuardResult:
    identities = _provider_identity_values(decision=decision, provider_identity_values=provider_identity_values)
    forbidden_field_paths: list[str] = []
    forbidden_value_paths: list[str] = []
    _scan_surface(
        surface,
        path=surface_name,
        provider_identity_values=identities,
        forbidden_field_paths=forbidden_field_paths,
        forbidden_value_paths=forbidden_value_paths,
    )
    status = (
        PROVIDER_NO_LEAKAGE_STATUS_FAILED
        if forbidden_field_paths or forbidden_value_paths
        else PROVIDER_NO_LEAKAGE_STATUS_PASSED
    )
    return ProviderNoLeakageGuardResult(
        status=status,
        error_code=PROVIDER_NO_LEAKAGE_ERROR_PROVIDER_LEAKAGE_DETECTED
        if status == PROVIDER_NO_LEAKAGE_STATUS_FAILED
        else None,
        evidence=ProviderNoLeakageEvidence(
            surface_name=surface_name,
            forbidden_field_paths=tuple(forbidden_field_paths),
            forbidden_value_paths=tuple(forbidden_value_paths),
            provider_identity_values_checked=identities,
        ),
    )


def assert_core_provider_no_leakage(
    *,
    surface_name: str,
    surface: Any,
    decision: AdapterProviderCompatibilityDecision | None = None,
    provider_identity_values: Sequence[str] = (),
) -> None:
    result = guard_core_provider_no_leakage(
        surface_name=surface_name,
        surface=surface,
        decision=decision,
        provider_identity_values=provider_identity_values,
    )
    if result.status != PROVIDER_NO_LEAKAGE_STATUS_PASSED:
        raise AssertionError(
            f"provider leakage detected on {surface_name}: "
            f"fields={result.evidence.forbidden_field_paths}, "
            f"values={result.evidence.forbidden_value_paths}"
        )


def _provider_identity_values(
    *,
    decision: AdapterProviderCompatibilityDecision | None,
    provider_identity_values: Sequence[str],
) -> tuple[str, ...]:
    values: list[str] = [value for value in provider_identity_values if isinstance(value, str) and value]
    if decision is not None and decision.evidence.adapter_bound_provider_evidence is not None:
        values.extend(
            (
                decision.evidence.adapter_bound_provider_evidence.provider_key,
                decision.evidence.adapter_bound_provider_evidence.offer_id,
            )
        )
    return _dedupe(values)


def _scan_surface(
    value: Any,
    *,
    path: str,
    provider_identity_values: tuple[str, ...],
    forbidden_field_paths: list[str],
    forbidden_value_paths: list[str],
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _scan_surface(
            asdict(value),
            path=path,
            provider_identity_values=provider_identity_values,
            forbidden_field_paths=forbidden_field_paths,
            forbidden_value_paths=forbidden_value_paths,
        )
        return
    if isinstance(value, Mapping):
        for key, child_value in value.items():
            child_path = f"{path}.{key!s}"
            if isinstance(key, str) and _contains_forbidden_provider_field_token(key):
                forbidden_field_paths.append(child_path)
            if isinstance(key, str) and _contains_provider_identity_value(key, provider_identity_values):
                forbidden_value_paths.append(child_path)
            _scan_surface(
                child_value,
                path=child_path,
                provider_identity_values=provider_identity_values,
                forbidden_field_paths=forbidden_field_paths,
                forbidden_value_paths=forbidden_value_paths,
            )
        return
    if isinstance(value, (str, bytes)):
        if isinstance(value, str) and _contains_provider_identity_value(value, provider_identity_values):
            forbidden_value_paths.append(path)
        return
    if isinstance(value, Iterable):
        for index, child_value in enumerate(value):
            _scan_surface(
                child_value,
                path=f"{path}[{index}]",
                provider_identity_values=provider_identity_values,
                forbidden_field_paths=forbidden_field_paths,
                forbidden_value_paths=forbidden_value_paths,
            )


def _contains_forbidden_provider_field_token(field_name: str) -> bool:
    normalized = _normalize_field_name(field_name)
    return any(token in normalized for token in FORBIDDEN_CORE_PROVIDER_FIELD_TOKENS)


def _contains_provider_identity_value(value: str, provider_identity_values: tuple[str, ...]) -> bool:
    normalized_value = _identity_slug(value)
    for identity_value in provider_identity_values:
        if value == identity_value:
            return True
        normalized_identity = _identity_slug(identity_value)
        if normalized_identity and (
            normalized_value == normalized_identity
            or normalized_value.startswith(f"{normalized_identity}-")
            or normalized_value.endswith(f"-{normalized_identity}")
            or f"-{normalized_identity}-" in normalized_value
        ):
            return True
    if any(_identity_slug(token) == normalized_value for token in FORBIDDEN_CORE_PROVIDER_VALUE_TOKENS):
        return True
    return False


def _identity_slug(value: str) -> str:
    chars: list[str] = []
    previous_was_separator = False
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
            previous_was_separator = False
        elif not previous_was_separator:
            chars.append("-")
            previous_was_separator = True
    return "".join(chars).strip("-")


def _normalize_field_name(field_name: str) -> str:
    with_word_boundaries = re.sub(r"(?<!^)(?=[A-Z])", "_", field_name)
    return with_word_boundaries.lower().replace("-", "_").replace(" ", "_")


def _dedupe(raw_values: Iterable[str]) -> tuple[str, ...]:
    values: list[str] = []
    seen: set[str] = set()
    for raw_value in raw_values:
        if raw_value not in seen:
            seen.add(raw_value)
            values.append(raw_value)
    return tuple(values)
