from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
import re
from typing import Any

from syvert.adapter_provider_compatibility_decision import AdapterProviderCompatibilityDecision


PROVIDER_NO_LEAKAGE_STATUS_PASSED = "passed"
PROVIDER_NO_LEAKAGE_STATUS_FAILED = "failed"
PROVIDER_NO_LEAKAGE_ERROR_PROVIDER_LEAKAGE_DETECTED = "provider_leakage_detected"

PROVIDER_IDENTITY_CARRIER_TOKENS = frozenset(
    {"provider", "provider_id", "provider_key", "offer", "offer_id"}
)

PROVIDER_METADATA_CARRIER_TOKENS = frozenset(
    {
        "provider_capability",
        "provider_capabilities",
        "provider_profile",
        "provider_registry",
        "provider_registry_entry",
        "external_provider_ref",
        "native_provider",
        "browser_provider",
        "resource_provider",
        "core_provider_registry",
        "core_provider_discovery",
    }
)

PROVIDER_DECISION_CARRIER_TOKENS = frozenset(
    {
        "compatibility_decision",
        "compatibility_status",
        "decision_detail",
        "decision_details",
        "provider_offer",
    }
)

PROVIDER_SELECTION_ROUTING_TOKENS = frozenset(
    {
        "selected_provider",
        "selected_profile",
        "provider_selector",
        "provider_selection",
        "provider_routing",
        "selector",
        "routing",
        "routing_policy",
        "priority",
        "rank",
        "ranking",
        "score",
        "fallback",
        "fallback_order",
        "fallback_outcome",
        "optional_capabilities",
        "preferred_profile",
        "preferred_profiles",
        "preferred_capabilities",
    }
)

PROVIDER_MARKETPLACE_PRODUCT_TOKENS = frozenset(
    {
        "marketplace",
        "marketplace_listing",
        "provider_product_allowlist",
        "provider_product_support",
        "sla",
        "availability_sla",
    }
)

PROVIDER_RESOURCE_LIFECYCLE_TOKENS = frozenset(
    {
        "provider_lifecycle",
        "provider_lease",
        "resource_supply",
        "resource_pool",
        "account_pool",
        "proxy_pool",
        "task_record_provider_field",
    }
)

RUNTIME_TECHNICAL_TOKENS = frozenset(
    {
        "playwright",
        "cdp",
        "chromium",
        "browser",
        "browser_profile",
        "network",
        "network_tier",
        "transport",
        "sign_service",
    }
)

CREDENTIAL_SESSION_PRIVATE_TOKENS = frozenset(
    {
        "authorization",
        "cookie",
        "cookies",
        "credential_freshness",
        "credential_material",
        "headers",
        "health_sla",
        "ms_token",
        "session",
        "session_health",
        "session_object",
        "token",
        "verify_fp",
        "xsec_token",
    }
)

PROVIDER_FAILURE_VALUE_TOKENS = frozenset(
    {"provider_failure", "provider_unavailable", "provider_contract_violation", "invalid_provider_offer"}
)

FORBIDDEN_CORE_PROVIDER_FIELD_TOKENS = frozenset().union(
    PROVIDER_IDENTITY_CARRIER_TOKENS,
    PROVIDER_METADATA_CARRIER_TOKENS,
    PROVIDER_DECISION_CARRIER_TOKENS,
    PROVIDER_SELECTION_ROUTING_TOKENS,
    PROVIDER_MARKETPLACE_PRODUCT_TOKENS,
    PROVIDER_RESOURCE_LIFECYCLE_TOKENS,
    RUNTIME_TECHNICAL_TOKENS,
    CREDENTIAL_SESSION_PRIVATE_TOKENS,
)

FORBIDDEN_CORE_PROVIDER_VALUE_SEMANTIC_TOKENS = FORBIDDEN_CORE_PROVIDER_FIELD_TOKENS

FORBIDDEN_CORE_PROVIDER_VALUE_EXACT_TOKENS = PROVIDER_IDENTITY_CARRIER_TOKENS.union(
    PROVIDER_DECISION_CARRIER_TOKENS,
    {
        "availability_sla",
        "browser",
        "cdp",
        "chromium",
        "decision_detail",
        "decision_details",
        "fallback",
        "marketplace",
        "network",
        "offer",
        "playwright",
        "priority",
        "rank",
        "ranking",
        "routing",
        "score",
        "selector",
        "sla",
        "session",
        "transport",
    },
    CREDENTIAL_SESSION_PRIVATE_TOKENS,
)

FORBIDDEN_CORE_PROVIDER_VALUE_EMBEDDED_TOKENS = FORBIDDEN_CORE_PROVIDER_VALUE_SEMANTIC_TOKENS.difference(
    {
        "provider",
        "offer",
        "decision_detail",
        "decision_details",
        "compatibility_decision",
        "browser",
        "network",
        "sla",
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
            if isinstance(key, str) and _contains_forbidden_provider_field_token(key, path=child_path):
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
        if isinstance(value, str):
            if (
                _contains_provider_identity_value(value, provider_identity_values)
                or _contains_forbidden_provider_value_semantics(value, path=path)
                or _contains_forbidden_provider_failure_value(path, value)
            ):
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


def _contains_forbidden_provider_field_token(field_name: str, *, path: str) -> bool:
    normalized = _normalize_field_name(field_name)
    if _path_allows_credential_material(path) and _contains_credential_session_private_token(normalized):
        return False
    if normalized == "provider":
        return True
    if normalized.startswith("provider_"):
        return True
    return any(
        _contains_normalized_semantic_token(normalized, _normalize_field_name(token))
        for token in FORBIDDEN_CORE_PROVIDER_FIELD_TOKENS
    )


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
    for token in PROVIDER_FAILURE_VALUE_TOKENS:
        normalized_token = _identity_slug(token)
        if (
            normalized_value == normalized_token
            or normalized_value.startswith(f"{normalized_token}-")
            or normalized_value.endswith(f"-{normalized_token}")
            or f"-{normalized_token}-" in normalized_value
            or normalized_value.startswith(f"{normalized_token}_")
            or normalized_value.endswith(f"_{normalized_token}")
            or f"_{normalized_token}_" in normalized_value
        ):
            return True
    return False


def _contains_forbidden_provider_failure_value(path: str, value: str) -> bool:
    normalized_value = _identity_slug(value)
    if _normalize_path_field_name(path) in {"category", "failure_category"}:
        return normalized_value in {"provider", "provider-failure"}
    return False


def _contains_forbidden_provider_value_semantics(value: str, *, path: str) -> bool:
    normalized_value = _normalize_field_name(value)
    if _path_allows_credential_material(path) and _contains_credential_session_private_token(normalized_value):
        return False
    if normalized_value.startswith("provider_"):
        return True
    for token in FORBIDDEN_CORE_PROVIDER_VALUE_EXACT_TOKENS:
        if normalized_value == _normalize_field_name(token):
            return True
    for token in FORBIDDEN_CORE_PROVIDER_VALUE_EMBEDDED_TOKENS:
        normalized_token = _normalize_field_name(token)
        if _contains_normalized_semantic_token(normalized_value, normalized_token):
            return True
    return False


def _contains_credential_session_private_token(normalized_value: str) -> bool:
    return any(
        _contains_normalized_semantic_token(normalized_value, _normalize_field_name(token))
        for token in CREDENTIAL_SESSION_PRIVATE_TOKENS
    )


def _path_allows_credential_material(path: str) -> bool:
    normalized_path = _normalize_field_name(path)
    return normalized_path.startswith("resource_lifecycle") and "_material_" in f"_{normalized_path}_"


def _contains_normalized_semantic_token(normalized_value: str, normalized_token: str) -> bool:
    return (
        normalized_value == normalized_token
        or normalized_value.startswith(f"{normalized_token}_")
        or normalized_value.endswith(f"_{normalized_token}")
        or f"_{normalized_token}_" in normalized_value
    )


def _identity_slug(value: str) -> str:
    return _normalize_field_name(value).replace("_", "-")


def _normalize_path_field_name(path: str) -> str:
    last_segment = path.rsplit(".", maxsplit=1)[-1]
    return _normalize_field_name(re.sub(r"\[\d+\]$", "", last_segment))


def _normalize_field_name(field_name: str) -> str:
    with_word_boundaries = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", field_name)
    with_word_boundaries = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", with_word_boundaries)
    return re.sub(r"[^a-z0-9]+", "_", with_word_boundaries.lower()).strip("_")


def _dedupe(raw_values: Iterable[str]) -> tuple[str, ...]:
    values: list[str] = []
    seen: set[str] = set()
    for raw_value in raw_values:
        if raw_value not in seen:
            seen.add(raw_value)
            values.append(raw_value)
    return tuple(values)
