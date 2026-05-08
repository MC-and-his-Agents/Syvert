from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import re
from typing import Any

from syvert.adapter_capability_requirement import (
    ADAPTER_REQUIREMENT_STATUS_INVALID,
    AdapterCapabilityRequirement,
    AdapterCapabilityRequirementValidationInput,
    validate_adapter_capability_requirement,
    _normalize_requirement,
)
from syvert.provider_capability_offer import (
    PROVIDER_OFFER_STATUS_INVALID,
    ProviderCapabilityOffer,
    validate_provider_capability_offer,
    _normalize_offer,
)
from syvert.operation_taxonomy import stable_operation_entry
from syvert.resource_capability_evidence import approved_shared_resource_requirement_profile_evidence_entries


COMPATIBILITY_DECISION_STATUS_MATCHED = "matched"
COMPATIBILITY_DECISION_STATUS_UNMATCHED = "unmatched"
COMPATIBILITY_DECISION_STATUS_INVALID_CONTRACT = "invalid_contract"

COMPATIBILITY_DECISION_ERROR_INVALID_REQUIREMENT_CONTRACT = "invalid_requirement_contract"
COMPATIBILITY_DECISION_ERROR_INVALID_PROVIDER_OFFER_CONTRACT = "invalid_provider_offer_contract"
COMPATIBILITY_DECISION_ERROR_INVALID_COMPATIBILITY_CONTRACT = "invalid_compatibility_contract"
COMPATIBILITY_DECISION_ERROR_PROVIDER_LEAKAGE_DETECTED = "provider_leakage_detected"

APPROVED_CONTRACT_VERSION = "v0.8.0"
APPROVED_REQUIREMENT_CONTRACT_REF = "FR-0024"
APPROVED_OFFER_CONTRACT_REF = "FR-0025"
APPROVED_RESOURCE_PROFILE_CONTRACT_REF = "FR-0027"
APPROVED_PROVIDER_PORT_BOUNDARY_REF = "FR-0021"
APPROVED_COMPATIBILITY_DECISION_EVIDENCE_REF = (
    "fr-0026:runtime-tests:adapter-provider-compatibility-decision"
)
APPROVED_OPERATION_TAXONOMY_ENTRY = stable_operation_entry(
    operation="content_detail_by_url",
    target_type="url",
    collection_mode="hybrid",
)
APPROVED_CAPABILITY = APPROVED_OPERATION_TAXONOMY_ENTRY.capability_family
APPROVED_OPERATION = APPROVED_OPERATION_TAXONOMY_ENTRY.operation
APPROVED_TARGET_TYPE = APPROVED_OPERATION_TAXONOMY_ENTRY.target_type
APPROVED_COLLECTION_MODE = APPROVED_OPERATION_TAXONOMY_ENTRY.collection_mode
APPROVED_RESOURCE_CAPABILITY_ORDER = ("account", "proxy")
CONTRACT_VALIDATION_CAPABILITIES = APPROVED_RESOURCE_CAPABILITY_ORDER

REQUIRED_INPUT_FIELDS = frozenset({"requirement", "offer", "decision_context"})
REQUIRED_CONTEXT_FIELDS = frozenset(
    {
        "decision_id",
        "contract_version",
        "requirement_contract_ref",
        "offer_contract_ref",
        "resource_profile_contract_ref",
        "provider_port_boundary_ref",
        "fail_closed",
    }
)
FORBIDDEN_DECISION_TOKENS = frozenset(
    {
        "authorization",
        "cookie",
        "cookies",
        "credential_freshness",
        "credential_material",
        "headers",
        "health_sla",
        "ms_token",
        "provider_key",
        "offer_id",
        "selected_provider",
        "provider_selection",
        "provider_selector",
        "provider_routing",
        "routing_policy",
        "core_routing",
        "core_provider_registry",
        "core_provider_discovery",
        "priority",
        "rank",
        "score",
        "ranking",
        "preferred_profile",
        "preferred_profiles",
        "fallback",
        "fallback_order",
        "marketplace",
        "provider_product_support",
        "native_xhs",
        "native_douyin",
        "xiaohongshu",
        "douyin",
        "xhs",
        "sla",
        "resource_supply",
        "resource_pool",
        "provider_lifecycle",
        "task_record_provider_field",
        "playwright",
        "cdp",
        "chromium",
        "browser",
        "network",
        "session",
        "session_health",
        "session_object",
        "token",
        "transport",
        "verify_fp",
        "xsec_token",
    }
)
CORE_PROJECTION_ALLOWED_FIELDS = frozenset(
    {
        "decision_id",
        "adapter_key",
        "capability",
        "decision_status",
        "error_code",
        "failure_category",
        "fail_closed",
    }
)


@dataclass(frozen=True)
class CompatibilityExecutionSlice:
    operation: str
    target_type: str
    collection_mode: str


@dataclass(frozen=True)
class CompatibilityDecisionContext:
    decision_id: str
    contract_version: str
    requirement_contract_ref: str
    offer_contract_ref: str
    resource_profile_contract_ref: str
    provider_port_boundary_ref: str
    fail_closed: bool


@dataclass(frozen=True)
class AdapterProviderCompatibilityDecisionInput:
    requirement: AdapterCapabilityRequirement | Mapping[str, Any]
    offer: ProviderCapabilityOffer | Mapping[str, Any]
    decision_context: CompatibilityDecisionContext | Mapping[str, Any]


@dataclass(frozen=True)
class MatchedCompatibilityProfile:
    requirement_profile_key: str
    offer_profile_key: str
    resource_dependency_mode: str
    required_capabilities: tuple[str, ...]
    requirement_profile_evidence_ref: str
    offer_profile_evidence_ref: str


@dataclass(frozen=True)
class ProfileEvidenceCarrierRef:
    ref: str
    adapter_key: str | None
    capability: str | None
    operation: str | None
    target_type: str | None
    collection_mode: str | None
    resource_dependency_mode: str | None
    required_capabilities: tuple[str, ...]


@dataclass(frozen=True)
class CompatibilityDecisionError:
    failure_category: str
    error_code: str
    source_contract_ref: str
    adapter_mapping_required: bool


@dataclass(frozen=True)
class AdapterBoundProviderEvidence:
    provider_key: str
    offer_id: str


@dataclass(frozen=True)
class InvalidCompatibilityContractEvidence:
    source_contract_ref: str
    violated_rule: str
    unresolved_refs: tuple[str, ...]
    resolved_profile_evidence_refs: tuple[str, ...]
    observed_values: Mapping[str, Any]


@dataclass(frozen=True)
class CompatibilityDecisionEvidence:
    requirement_evidence_refs: tuple[str, ...]
    offer_evidence_refs: tuple[str, ...]
    resource_profile_evidence_refs: tuple[str, ...]
    compatibility_decision_evidence_refs: tuple[str, ...]
    adapter_bound_provider_evidence: AdapterBoundProviderEvidence | None
    invalid_contract_evidence: InvalidCompatibilityContractEvidence | None


@dataclass(frozen=True)
class CompatibilityDecisionObservability:
    decision_id: str
    adapter_key: str | None
    requirement_id: str | None
    capability: str | None
    operation: str | None
    matched_profile_keys: tuple[str, ...]
    decision_status: str
    error_code: str | None
    contract_refs: tuple[str, ...]
    proof_refs: tuple[str, ...]


@dataclass(frozen=True)
class CompatibilityNoLeakageAssertion:
    core_registry_provider_fields_allowed: bool
    core_routing_provider_fields_allowed: bool
    task_record_provider_fields_allowed: bool
    resource_lifecycle_provider_fields_allowed: bool
    adapter_bound_evidence_provider_fields_allowed: bool


@dataclass(frozen=True)
class AdapterProviderCompatibilityDecision:
    decision_id: str
    adapter_key: str | None
    capability: str | None
    execution_slice: CompatibilityExecutionSlice | None
    decision_status: str
    matched_profiles: tuple[MatchedCompatibilityProfile, ...]
    error: CompatibilityDecisionError | None
    evidence: CompatibilityDecisionEvidence
    observability: CompatibilityDecisionObservability
    no_leakage: CompatibilityNoLeakageAssertion
    fail_closed: bool


def baseline_compatibility_decision_context(*, decision_id: str = "compatibility-decision-001") -> CompatibilityDecisionContext:
    return CompatibilityDecisionContext(
        decision_id=decision_id,
        contract_version=APPROVED_CONTRACT_VERSION,
        requirement_contract_ref=APPROVED_REQUIREMENT_CONTRACT_REF,
        offer_contract_ref=APPROVED_OFFER_CONTRACT_REF,
        resource_profile_contract_ref=APPROVED_RESOURCE_PROFILE_CONTRACT_REF,
        provider_port_boundary_ref=APPROVED_PROVIDER_PORT_BOUNDARY_REF,
        fail_closed=True,
    )


def decide_adapter_provider_compatibility(
    input_value: AdapterProviderCompatibilityDecisionInput | Mapping[str, Any],
) -> AdapterProviderCompatibilityDecision:
    input_error = _validate_input_surface(input_value)
    raw_requirement, raw_offer, raw_context, context = _normalize_input(input_value)
    if input_error is not None:
        return _invalid_decision(
            context=context,
            raw_requirement=raw_requirement,
            raw_offer=raw_offer,
            source_contract_ref="FR-0026",
            error_code=input_error[0],
            violated_rule=input_error[1],
            observed_values=input_error[2],
        )
    context_provider_identity_error = _validate_context_provider_identity(context, raw_offer)
    if context_provider_identity_error is not None:
        return _invalid_decision(
            context=context,
            raw_requirement=raw_requirement,
            raw_offer=raw_offer,
            source_contract_ref="FR-0026",
            error_code=context_provider_identity_error[0],
            violated_rule=context_provider_identity_error[1],
            observed_values=context_provider_identity_error[2],
        )
    context_surface_error = _validate_context_surface(raw_context)
    if context_surface_error is not None:
        return _invalid_decision(
            context=context,
            raw_requirement=raw_requirement,
            raw_offer=raw_offer,
            source_contract_ref="FR-0026",
            error_code=context_surface_error[0],
            violated_rule=context_surface_error[1],
            observed_values=context_surface_error[2],
        )
    context_leakage = _detect_provider_leakage(raw_context)
    if context_leakage:
        return _invalid_decision(
            context=context,
            raw_requirement=raw_requirement,
            raw_offer=raw_offer,
            source_contract_ref="FR-0026",
            error_code=COMPATIBILITY_DECISION_ERROR_PROVIDER_LEAKAGE_DETECTED,
            violated_rule="decision context must not contain provider routing or provider identity fields",
            observed_values=_forbidden_semantics_observed_values(context_leakage),
        )
    context_error = _validate_context(context)
    if context_error is not None:
        return _invalid_decision(
            context=context,
            raw_requirement=raw_requirement,
            raw_offer=raw_offer,
            source_contract_ref="FR-0026",
            error_code=context_error[0],
            violated_rule=context_error[1],
            observed_values=context_error[2],
        )

    requirement_result = validate_adapter_capability_requirement(
        AdapterCapabilityRequirementValidationInput(
            requirement=raw_requirement,
            available_resource_capabilities=CONTRACT_VALIDATION_CAPABILITIES,
        )
    )
    if requirement_result.status == ADAPTER_REQUIREMENT_STATUS_INVALID:
        return _invalid_decision(
            context=context,
            raw_requirement=raw_requirement,
            raw_offer=raw_offer,
            source_contract_ref=APPROVED_REQUIREMENT_CONTRACT_REF,
            error_code=COMPATIBILITY_DECISION_ERROR_INVALID_REQUIREMENT_CONTRACT,
            violated_rule="requirement carrier failed FR-0024 validation",
            observed_values=_upstream_validation_observed_values(
                surface="requirement",
                error_code=requirement_result.error_code,
                details=requirement_result.details,
            ),
        )

    offer_result = validate_provider_capability_offer(raw_offer)
    if offer_result.status == PROVIDER_OFFER_STATUS_INVALID:
        return _invalid_decision(
            context=context,
            raw_requirement=raw_requirement,
            raw_offer=raw_offer,
            source_contract_ref=APPROVED_OFFER_CONTRACT_REF,
            error_code=COMPATIBILITY_DECISION_ERROR_INVALID_PROVIDER_OFFER_CONTRACT,
            violated_rule="provider offer carrier failed FR-0025 validation",
            observed_values=_upstream_validation_observed_values(
                surface="offer",
                error_code=offer_result.error_code,
                details=offer_result.details,
            ),
        )

    requirement = _normalize_requirement(raw_requirement)
    offer = _normalize_offer(raw_offer)

    leakage_error = _detect_provider_leakage(context)
    if leakage_error:
        return _invalid_decision(
            context=context,
            raw_requirement=raw_requirement,
            raw_offer=raw_offer,
            source_contract_ref="FR-0026",
            error_code=COMPATIBILITY_DECISION_ERROR_PROVIDER_LEAKAGE_DETECTED,
            violated_rule="decision context must not contain provider routing or provider identity fields",
            observed_values=_forbidden_semantics_observed_values(leakage_error),
        )

    if requirement.adapter_key != offer.adapter_binding.adapter_key:
        return _invalid_decision(
            context=context,
            raw_requirement=raw_requirement,
            raw_offer=raw_offer,
            source_contract_ref="FR-0026",
            error_code=COMPATIBILITY_DECISION_ERROR_INVALID_COMPATIBILITY_CONTRACT,
            violated_rule="requirement.adapter_key must match offer.adapter_binding.adapter_key",
            observed_values={
                "requirement_adapter_key": requirement.adapter_key,
                "offer_adapter_key": offer.adapter_binding.adapter_key,
            },
        )
    if requirement.capability != offer.capability_offer.capability:
        return _invalid_decision(
            context=context,
            raw_requirement=raw_requirement,
            raw_offer=raw_offer,
            source_contract_ref="FR-0026",
            error_code=COMPATIBILITY_DECISION_ERROR_INVALID_COMPATIBILITY_CONTRACT,
            violated_rule="requirement capability must match offer capability",
            observed_values={
                "requirement_capability": requirement.capability,
                "offer_capability": offer.capability_offer.capability,
            },
        )
    requirement_slice = CompatibilityExecutionSlice(**requirement.execution_requirement.__dict__)
    offer_slice = CompatibilityExecutionSlice(
        operation=offer.capability_offer.operation,
        target_type=offer.capability_offer.target_type,
        collection_mode=offer.capability_offer.collection_mode,
    )
    if requirement_slice != offer_slice:
        return _invalid_decision(
            context=context,
            raw_requirement=raw_requirement,
            raw_offer=raw_offer,
            source_contract_ref="FR-0026",
            error_code=COMPATIBILITY_DECISION_ERROR_INVALID_COMPATIBILITY_CONTRACT,
            violated_rule="requirement execution slice must match offer capability_offer execution slice",
            observed_values={
                "requirement_execution_slice": requirement_slice.__dict__,
                "offer_execution_slice": offer_slice.__dict__,
            },
        )

    matched_profiles = _match_profiles(requirement, offer)
    status = (
        COMPATIBILITY_DECISION_STATUS_MATCHED
        if matched_profiles
        else COMPATIBILITY_DECISION_STATUS_UNMATCHED
    )
    adapter_bound_provider_evidence = AdapterBoundProviderEvidence(
        provider_key=offer.provider_key,
        offer_id=offer.observability.offer_id,
    )
    return AdapterProviderCompatibilityDecision(
        decision_id=context.decision_id,
        adapter_key=requirement.adapter_key,
        capability=requirement.capability,
        execution_slice=requirement_slice,
        decision_status=status,
        matched_profiles=matched_profiles,
        error=None,
        evidence=CompatibilityDecisionEvidence(
            requirement_evidence_refs=requirement.evidence.capability_requirement_evidence_refs,
            offer_evidence_refs=offer.evidence.provider_offer_evidence_refs,
            resource_profile_evidence_refs=_dedupe(
                (
                    *requirement.evidence.resource_profile_evidence_refs,
                    *offer.evidence.resource_profile_evidence_refs,
                )
            ),
            compatibility_decision_evidence_refs=(APPROVED_COMPATIBILITY_DECISION_EVIDENCE_REF,),
            adapter_bound_provider_evidence=adapter_bound_provider_evidence,
            invalid_contract_evidence=None,
        ),
        observability=_observability(
            context=context,
            adapter_key=requirement.adapter_key,
            requirement_id=requirement.observability.requirement_id,
            capability=requirement.capability,
            operation=requirement.execution_requirement.operation,
            matched_profiles=matched_profiles,
            decision_status=status,
            error_code=None,
            proof_refs=_dedupe(
                (
                    *requirement.evidence.resource_profile_evidence_refs,
                    *offer.evidence.resource_profile_evidence_refs,
                )
            ),
        ),
        no_leakage=_no_leakage_assertion(),
        fail_closed=True,
    )


def project_compatibility_decision_for_core(
    decision: AdapterProviderCompatibilityDecision,
) -> Mapping[str, Any]:
    projection = {
        "decision_id": decision.decision_id,
        "adapter_key": decision.adapter_key,
        "capability": decision.capability,
        "decision_status": decision.decision_status,
        "error_code": decision.error.error_code if decision.error is not None else None,
        "failure_category": decision.error.failure_category if decision.error is not None else None,
        "fail_closed": decision.fail_closed,
    }
    forbidden_fields = tuple(sorted(set(projection) - CORE_PROJECTION_ALLOWED_FIELDS))
    if forbidden_fields:
        raise AssertionError(f"Core projection leaked provider fields: {forbidden_fields}")
    return projection


def _normalize_input(
    input_value: AdapterProviderCompatibilityDecisionInput | Mapping[str, Any],
) -> tuple[Any, Any, Any, CompatibilityDecisionContext]:
    if type(input_value) is AdapterProviderCompatibilityDecisionInput:
        return (
            input_value.requirement,
            input_value.offer,
            input_value.decision_context,
            _normalize_context(input_value.decision_context),
        )
    if not isinstance(input_value, Mapping):
        synthetic_context = baseline_compatibility_decision_context(decision_id="invalid-input")
        return input_value, None, synthetic_context, synthetic_context
    raw_keys = _require_string_keys(input_value)
    if raw_keys != REQUIRED_INPUT_FIELDS:
        raw_context = input_value.get("decision_context", baseline_compatibility_decision_context())
        context = _normalize_context(raw_context)
        return (
            input_value.get("requirement"),
            input_value.get("offer"),
            raw_context,
            CompatibilityDecisionContext(
                decision_id=context.decision_id,
                contract_version=context.contract_version,
                requirement_contract_ref=context.requirement_contract_ref,
                offer_contract_ref=context.offer_contract_ref,
                resource_profile_contract_ref=context.resource_profile_contract_ref,
                provider_port_boundary_ref=context.provider_port_boundary_ref,
                fail_closed=context.fail_closed,
            ),
        )
    return (
        input_value["requirement"],
        input_value["offer"],
        input_value["decision_context"],
        _normalize_context(input_value["decision_context"]),
    )


def _validate_input_surface(
    input_value: AdapterProviderCompatibilityDecisionInput | Mapping[str, Any],
) -> tuple[str, str, Mapping[str, Any]] | None:
    if type(input_value) is AdapterProviderCompatibilityDecisionInput:
        return None
    if not isinstance(input_value, Mapping):
        return (
            COMPATIBILITY_DECISION_ERROR_INVALID_COMPATIBILITY_CONTRACT,
            "AdapterProviderCompatibilityDecisionInput must be a mapping or canonical dataclass",
            {"actual_type": type(input_value).__name__},
        )
    raw_keys = _require_string_keys(input_value)
    missing_fields = tuple(sorted(REQUIRED_INPUT_FIELDS - raw_keys))
    extra_fields = tuple(sorted(raw_keys - REQUIRED_INPUT_FIELDS))
    non_string_extra_count = _non_string_key_count(input_value)
    if missing_fields or extra_fields or non_string_extra_count:
        leakage = _detect_provider_leakage(_surface_extra_values(input_value, extra_fields))
        error_code = (
            COMPATIBILITY_DECISION_ERROR_PROVIDER_LEAKAGE_DETECTED
            if leakage
            else COMPATIBILITY_DECISION_ERROR_INVALID_COMPATIBILITY_CONTRACT
        )
        return (
            error_code,
            "AdapterProviderCompatibilityDecisionInput must keep the canonical field set",
            _surface_drift_observed_values(
                surface="decision_input",
                missing_count=len(missing_fields),
                extra_count=len(extra_fields) + non_string_extra_count,
                forbidden_semantics_count=len(leakage),
            ),
        )
    return None


def _validate_context_surface(raw_context: Any) -> tuple[str, str, Mapping[str, Any]] | None:
    if type(raw_context) is CompatibilityDecisionContext:
        return None
    if not isinstance(raw_context, Mapping):
        return (
            COMPATIBILITY_DECISION_ERROR_INVALID_COMPATIBILITY_CONTRACT,
            "decision_context must be a mapping or canonical dataclass",
            {"surface": "decision_context", "actual_type": type(raw_context).__name__},
        )
    raw_keys = _require_string_keys(raw_context)
    missing_fields = tuple(sorted(REQUIRED_CONTEXT_FIELDS - raw_keys))
    extra_fields = tuple(sorted(raw_keys - REQUIRED_CONTEXT_FIELDS))
    non_string_extra_count = _non_string_key_count(raw_context)
    if missing_fields or extra_fields or non_string_extra_count:
        leakage = _detect_provider_leakage(_surface_extra_values(raw_context, extra_fields))
        error_code = (
            COMPATIBILITY_DECISION_ERROR_PROVIDER_LEAKAGE_DETECTED
            if leakage
            else COMPATIBILITY_DECISION_ERROR_INVALID_COMPATIBILITY_CONTRACT
        )
        return (
            error_code,
            "decision_context must keep the canonical field set",
            _surface_drift_observed_values(
                surface="decision_context",
                missing_count=len(missing_fields),
                extra_count=len(extra_fields) + non_string_extra_count,
                forbidden_semantics_count=len(leakage),
            ),
        )
    return None


def _normalize_context(raw_value: CompatibilityDecisionContext | Mapping[str, Any]) -> CompatibilityDecisionContext:
    if type(raw_value) is CompatibilityDecisionContext:
        return CompatibilityDecisionContext(
            decision_id=_require_non_empty_string(raw_value.decision_id),
            contract_version=_require_non_empty_string(raw_value.contract_version),
            requirement_contract_ref=_require_non_empty_string(raw_value.requirement_contract_ref),
            offer_contract_ref=_require_non_empty_string(raw_value.offer_contract_ref),
            resource_profile_contract_ref=_require_non_empty_string(raw_value.resource_profile_contract_ref),
            provider_port_boundary_ref=_require_non_empty_string(raw_value.provider_port_boundary_ref),
            fail_closed=raw_value.fail_closed if type(raw_value.fail_closed) is bool else False,
        )
    if not isinstance(raw_value, Mapping):
        return CompatibilityDecisionContext(
            decision_id="invalid-context",
            contract_version="",
            requirement_contract_ref="",
            offer_contract_ref="",
            resource_profile_contract_ref="",
            provider_port_boundary_ref="",
            fail_closed=False,
        )
    raw_keys = _require_string_keys(raw_value)
    if raw_keys != REQUIRED_CONTEXT_FIELDS:
        return CompatibilityDecisionContext(
            decision_id=_best_effort_string(raw_value, "decision_id") or "invalid-context",
            contract_version=_best_effort_string(raw_value, "contract_version") or "",
            requirement_contract_ref=_best_effort_string(raw_value, "requirement_contract_ref") or "",
            offer_contract_ref=_best_effort_string(raw_value, "offer_contract_ref") or "",
            resource_profile_contract_ref=_best_effort_string(raw_value, "resource_profile_contract_ref") or "",
            provider_port_boundary_ref=_best_effort_string(raw_value, "provider_port_boundary_ref") or "",
            fail_closed=raw_value.get("fail_closed") if type(raw_value.get("fail_closed")) is bool else False,
        )
    return CompatibilityDecisionContext(
        decision_id=_require_non_empty_string(raw_value["decision_id"]),
        contract_version=_require_non_empty_string(raw_value["contract_version"]),
        requirement_contract_ref=_require_non_empty_string(raw_value["requirement_contract_ref"]),
        offer_contract_ref=_require_non_empty_string(raw_value["offer_contract_ref"]),
        resource_profile_contract_ref=_require_non_empty_string(raw_value["resource_profile_contract_ref"]),
        provider_port_boundary_ref=_require_non_empty_string(raw_value["provider_port_boundary_ref"]),
        fail_closed=raw_value["fail_closed"] if type(raw_value["fail_closed"]) is bool else False,
    )


def _validate_context(
    context: CompatibilityDecisionContext,
) -> tuple[str, str, Mapping[str, Any]] | None:
    expected = baseline_compatibility_decision_context(decision_id=context.decision_id)
    if not context.decision_id:
        return (
            COMPATIBILITY_DECISION_ERROR_INVALID_COMPATIBILITY_CONTRACT,
            "decision_context.decision_id must be non-empty",
            {"decision_id": context.decision_id},
        )
    if not _is_opaque_decision_id(context.decision_id):
        return (
            COMPATIBILITY_DECISION_ERROR_PROVIDER_LEAKAGE_DETECTED,
            "decision_context.decision_id must be an opaque non-provider identifier",
            {"surface": "decision_context", "decision_id_opaque": False},
        )
    if context != expected:
        return (
            COMPATIBILITY_DECISION_ERROR_INVALID_COMPATIBILITY_CONTRACT,
            "decision_context must stay frozen to FR-0026 v0.8.0 fail-closed boundaries",
            _context_drift_observed_values(expected=expected, actual=context),
        )
    leakage = _detect_provider_leakage(context)
    if leakage:
        return (
            COMPATIBILITY_DECISION_ERROR_PROVIDER_LEAKAGE_DETECTED,
            "decision_context must not carry provider identity, routing, priority, score, or fallback",
            _forbidden_semantics_observed_values(leakage),
        )
    return None


def _validate_context_provider_identity(
    context: CompatibilityDecisionContext,
    raw_offer: Any,
) -> tuple[str, str, Mapping[str, Any]] | None:
    decision_id_slug = _identity_slug(context.decision_id)
    provider_identity_values = (
        _best_effort_string(raw_offer, "provider_key"),
        _best_effort_nested_string(raw_offer, "observability", "provider_key"),
        _best_effort_nested_string(raw_offer, "observability", "offer_id"),
    )
    for raw_identity in provider_identity_values:
        if raw_identity is None:
            continue
        identity_slug = _identity_slug(raw_identity)
        if identity_slug and _decision_id_contains_provider_identity(decision_id_slug, identity_slug):
            return (
                COMPATIBILITY_DECISION_ERROR_PROVIDER_LEAKAGE_DETECTED,
                "decision_context.decision_id must not be derived from provider identity",
                {"surface": "decision_context", "decision_id_provider_derived": True},
            )
    return None


def _decision_id_contains_provider_identity(decision_id_slug: str, identity_slug: str) -> bool:
    return (
        decision_id_slug == identity_slug
        or decision_id_slug.startswith(f"{identity_slug}-")
        or decision_id_slug.endswith(f"-{identity_slug}")
        or f"-{identity_slug}-" in decision_id_slug
    )


def _identity_slug(raw_value: str) -> str:
    chars: list[str] = []
    previous_was_separator = False
    for char in raw_value.lower():
        if char.isalnum():
            chars.append(char)
            previous_was_separator = False
        elif not previous_was_separator:
            chars.append("-")
            previous_was_separator = True
    return "".join(chars).strip("-")


def _context_drift_observed_values(
    *,
    expected: CompatibilityDecisionContext,
    actual: CompatibilityDecisionContext,
) -> Mapping[str, Any]:
    expected_values = expected.__dict__
    actual_values = actual.__dict__
    mismatched_fields = tuple(
        field_name
        for field_name in REQUIRED_CONTEXT_FIELDS
        if expected_values.get(field_name) != actual_values.get(field_name)
    )
    return {
        "surface": "decision_context",
        "mismatched_field_count": len(mismatched_fields),
    }


def _surface_drift_observed_values(
    *,
    surface: str,
    missing_count: int,
    extra_count: int,
    forbidden_semantics_count: int,
) -> Mapping[str, Any]:
    return {
        "surface": surface,
        "missing_field_count": missing_count,
        "extra_field_count": extra_count,
        "forbidden_semantics_count": forbidden_semantics_count,
    }


def _forbidden_semantics_observed_values(leakage: tuple[str, ...]) -> Mapping[str, Any]:
    return {
        "surface": "decision_context",
        "forbidden_semantics_count": len(leakage),
    }


def _surface_extra_values(raw_value: Mapping[Any, Any], extra_fields: tuple[str, ...]) -> Mapping[str, Any]:
    extra_values: dict[str, Any] = {
        field_name: raw_value.get(field_name)
        for field_name in extra_fields
    }
    non_string_index = 0
    for key, value in raw_value.items():
        if isinstance(key, str):
            continue
        extra_values[f"non_string_extra_key_{non_string_index}"] = value
        non_string_index += 1
    return extra_values


def _non_string_key_count(raw_value: Mapping[Any, Any]) -> int:
    return sum(1 for key in raw_value if not isinstance(key, str))


def _upstream_validation_observed_values(
    *,
    surface: str,
    error_code: str | None,
    details: Mapping[str, Any],
) -> Mapping[str, Any]:
    return {
        "surface": surface,
        "validation_error_code": error_code,
        "detail_count": len(details),
        "forbidden_semantics_count": len(_detect_provider_leakage(details)),
    }


def _match_profiles(
    requirement: AdapterCapabilityRequirement,
    offer: ProviderCapabilityOffer,
) -> tuple[MatchedCompatibilityProfile, ...]:
    matched: list[MatchedCompatibilityProfile] = []
    for requirement_profile in requirement.resource_requirement.resource_requirement_profiles:
        requirement_tuple = (
            requirement_profile.resource_dependency_mode,
            _normalize_required_capabilities(requirement_profile.required_capabilities),
        )
        for offer_profile in offer.resource_support.supported_profiles:
            offer_tuple = (
                offer_profile.resource_dependency_mode,
                _normalize_required_capabilities(offer_profile.required_capabilities),
            )
            if requirement_tuple == offer_tuple:
                matched.append(
                    MatchedCompatibilityProfile(
                        requirement_profile_key=requirement_profile.profile_key,
                        offer_profile_key=offer_profile.profile_key,
                        resource_dependency_mode=requirement_tuple[0],
                        required_capabilities=requirement_tuple[1],
                        requirement_profile_evidence_ref=requirement_profile.evidence_refs[0],
                        offer_profile_evidence_ref=offer_profile.evidence_refs[0],
                    )
                )
    return tuple(matched)


def _invalid_decision(
    *,
    context: CompatibilityDecisionContext,
    raw_requirement: Any,
    raw_offer: Any,
    source_contract_ref: str,
    error_code: str,
    violated_rule: str,
    observed_values: Mapping[str, Any],
) -> AdapterProviderCompatibilityDecision:
    resolved_proofs, unresolved_proofs = _profile_evidence_ref_report(
        raw_requirement,
        raw_offer,
        source_contract_ref=source_contract_ref,
    )
    error = CompatibilityDecisionError(
        failure_category="runtime_contract",
        error_code=error_code,
        source_contract_ref=source_contract_ref,
        adapter_mapping_required=True,
    )
    return AdapterProviderCompatibilityDecision(
        decision_id=context.decision_id,
        adapter_key=None,
        capability=None,
        execution_slice=None,
        decision_status=COMPATIBILITY_DECISION_STATUS_INVALID_CONTRACT,
        matched_profiles=(),
        error=error,
        evidence=CompatibilityDecisionEvidence(
            requirement_evidence_refs=_best_effort_requirement_evidence_refs(raw_requirement),
            offer_evidence_refs=_best_effort_offer_evidence_refs(raw_offer),
            resource_profile_evidence_refs=resolved_proofs,
            compatibility_decision_evidence_refs=(APPROVED_COMPATIBILITY_DECISION_EVIDENCE_REF,),
            adapter_bound_provider_evidence=_best_effort_provider_evidence(raw_offer),
            invalid_contract_evidence=InvalidCompatibilityContractEvidence(
                source_contract_ref=source_contract_ref,
                violated_rule=violated_rule,
                unresolved_refs=unresolved_proofs,
                resolved_profile_evidence_refs=resolved_proofs,
                observed_values=dict(observed_values),
            ),
        ),
        observability=_observability(
            context=context,
            adapter_key=None,
            requirement_id=None,
            capability=None,
            operation=None,
            matched_profiles=(),
            decision_status=COMPATIBILITY_DECISION_STATUS_INVALID_CONTRACT,
            error_code=error_code,
            proof_refs=resolved_proofs,
        ),
        no_leakage=_no_leakage_assertion(),
        fail_closed=True,
    )


def _observability(
    *,
    context: CompatibilityDecisionContext,
    adapter_key: str | None,
    requirement_id: str | None,
    capability: str | None,
    operation: str | None,
    matched_profiles: tuple[MatchedCompatibilityProfile, ...],
    decision_status: str,
    error_code: str | None,
    proof_refs: tuple[str, ...],
) -> CompatibilityDecisionObservability:
    return CompatibilityDecisionObservability(
        decision_id=context.decision_id,
        adapter_key=adapter_key,
        requirement_id=requirement_id,
        capability=capability,
        operation=operation,
        matched_profile_keys=tuple(profile.requirement_profile_key for profile in matched_profiles),
        decision_status=decision_status,
        error_code=error_code,
        contract_refs=(
            APPROVED_REQUIREMENT_CONTRACT_REF,
            APPROVED_OFFER_CONTRACT_REF,
            APPROVED_RESOURCE_PROFILE_CONTRACT_REF,
            "FR-0026",
        ),
        proof_refs=proof_refs,
    )


def _no_leakage_assertion() -> CompatibilityNoLeakageAssertion:
    return CompatibilityNoLeakageAssertion(
        core_registry_provider_fields_allowed=False,
        core_routing_provider_fields_allowed=False,
        task_record_provider_fields_allowed=False,
        resource_lifecycle_provider_fields_allowed=False,
        adapter_bound_evidence_provider_fields_allowed=True,
    )


def _best_effort_requirement_evidence_refs(raw_requirement: Any) -> tuple[str, ...]:
    refs = _best_effort_nested_string_collection(
        raw_requirement,
        "evidence",
        "capability_requirement_evidence_refs",
    )
    return _dedupe(refs)


def _best_effort_offer_evidence_refs(raw_offer: Any) -> tuple[str, ...]:
    refs = _best_effort_nested_string_collection(raw_offer, "evidence", "provider_offer_evidence_refs")
    return _dedupe(refs)


def _profile_evidence_ref_report(
    raw_requirement: Any,
    raw_offer: Any,
    *,
    source_contract_ref: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    carriers: tuple[
        tuple[
            str,
            tuple[ProfileEvidenceCarrierRef, ...],
            tuple[str, ...],
            tuple[str, ...],
            tuple[str, ...],
        ],
        ...,
    ]
    requirement_carrier = _requirement_profile_evidence_surfaces(raw_requirement)
    offer_carrier = _offer_profile_evidence_surfaces(raw_offer)
    if source_contract_ref == APPROVED_REQUIREMENT_CONTRACT_REF:
        carriers = (requirement_carrier,)
    elif source_contract_ref == APPROVED_OFFER_CONTRACT_REF:
        carriers = (offer_carrier,)
    else:
        carriers = (requirement_carrier, offer_carrier)

    resolved_refs: list[str] = []
    unresolved_refs: list[str] = []
    for _, profile_ref_records, profile_refs, evidence_refs, observability_refs in carriers:
        carrier_resolved, carrier_unresolved = _classify_profile_evidence_refs(
            profile_ref_records=profile_ref_records,
            profile_refs=profile_refs,
            evidence_refs=evidence_refs,
            observability_refs=observability_refs,
        )
        resolved_refs.extend(carrier_resolved)
        unresolved_refs.extend(carrier_unresolved)
    return _dedupe(resolved_refs), _dedupe(unresolved_refs)


def _requirement_profile_evidence_surfaces(
    raw_requirement: Any,
) -> tuple[str, tuple[ProfileEvidenceCarrierRef, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    profile_ref_records = _best_effort_profile_evidence_carrier_refs(
        raw_requirement,
        "resource_requirement",
        "resource_requirement_profiles",
        adapter_key=_best_effort_string(raw_requirement, "adapter_key"),
        capability=_best_effort_string(raw_requirement, "capability"),
        operation=_best_effort_nested_string(raw_requirement, "execution_requirement", "operation"),
        target_type=_best_effort_nested_string(raw_requirement, "execution_requirement", "target_type"),
        collection_mode=_best_effort_nested_string(raw_requirement, "execution_requirement", "collection_mode"),
    )
    return (
        "requirement",
        profile_ref_records,
        tuple(record.ref for record in profile_ref_records),
        _best_effort_nested_string_collection(raw_requirement, "evidence", "resource_profile_evidence_refs"),
        _best_effort_nested_string_collection(raw_requirement, "observability", "proof_refs"),
    )


def _offer_profile_evidence_surfaces(
    raw_offer: Any,
) -> tuple[str, tuple[ProfileEvidenceCarrierRef, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    profile_ref_records = _best_effort_profile_evidence_carrier_refs(
        raw_offer,
        "resource_support",
        "supported_profiles",
        adapter_key=_best_effort_nested_string(raw_offer, "adapter_binding", "adapter_key"),
        capability=_best_effort_nested_string(raw_offer, "capability_offer", "capability"),
        operation=_best_effort_nested_string(raw_offer, "capability_offer", "operation"),
        target_type=_best_effort_nested_string(raw_offer, "capability_offer", "target_type"),
        collection_mode=_best_effort_nested_string(raw_offer, "capability_offer", "collection_mode"),
    )
    return (
        "offer",
        profile_ref_records,
        tuple(record.ref for record in profile_ref_records),
        _best_effort_nested_string_collection(raw_offer, "evidence", "resource_profile_evidence_refs"),
        _best_effort_nested_string_collection(raw_offer, "observability", "proof_refs"),
    )


def _classify_profile_evidence_refs(
    *,
    profile_ref_records: tuple[ProfileEvidenceCarrierRef, ...],
    profile_refs: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    observability_refs: tuple[str, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    approved_refs = _approved_profile_evidence_refs()
    duplicate_refs = (
        _duplicate_values(profile_refs)
        | _duplicate_values(evidence_refs)
        | _duplicate_values(observability_refs)
    )
    aligned_refs = set(profile_refs) & set(evidence_refs) & set(observability_refs)
    refs = (*profile_refs, *evidence_refs, *observability_refs)
    resolved_refs = tuple(
        ref
        for ref in refs
        if ref in approved_refs
        and ref in aligned_refs
        and ref not in duplicate_refs
        and _profile_ref_satisfies_fr0027(ref, profile_ref_records)
    )
    unresolved_refs = tuple(
        ref
        for ref in refs
        if ref not in approved_refs
        or ref not in aligned_refs
        or ref in duplicate_refs
        or not _profile_ref_satisfies_fr0027(ref, profile_ref_records)
    )
    return _dedupe(resolved_refs), _dedupe(unresolved_refs)


def _profile_ref_satisfies_fr0027(
    ref: str,
    profile_ref_records: tuple[ProfileEvidenceCarrierRef, ...],
) -> bool:
    proof = _approved_profile_evidence_entry_by_ref().get(ref)
    if proof is None:
        return False
    matched_records = tuple(record for record in profile_ref_records if record.ref == ref)
    if len(matched_records) != 1:
        return False
    record = matched_records[0]
    return (
        record.adapter_key in proof.reference_adapters
        and record.capability == proof.capability
        and record.operation == proof.execution_path.operation
        and record.target_type == proof.execution_path.target_type
        and record.collection_mode == proof.execution_path.collection_mode
        and record.resource_dependency_mode == proof.resource_dependency_mode
        and record.required_capabilities == proof.required_capabilities
    )


def _best_effort_provider_evidence(raw_offer: Any) -> AdapterBoundProviderEvidence | None:
    provider_key = _best_effort_string(raw_offer, "provider_key")
    offer_id = _best_effort_nested_string(raw_offer, "observability", "offer_id")
    if provider_key is None or offer_id is None:
        return None
    return AdapterBoundProviderEvidence(provider_key=provider_key, offer_id=offer_id)


def _best_effort_profile_evidence_carrier_refs(
    raw_value: Any,
    section: str,
    profiles_field: str,
    *,
    adapter_key: str | None,
    capability: str | None,
    operation: str | None,
    target_type: str | None,
    collection_mode: str | None,
) -> tuple[ProfileEvidenceCarrierRef, ...]:
    if isinstance(raw_value, Mapping):
        section_value = raw_value.get(section)
        profiles = section_value.get(profiles_field) if isinstance(section_value, Mapping) else None
    else:
        section_value = getattr(raw_value, section, None)
        profiles = getattr(section_value, profiles_field, None)
    if isinstance(profiles, (str, bytes, Mapping)) or profiles is None:
        return ()
    try:
        iterator: Iterable[Any] = iter(profiles)
    except TypeError:
        return ()

    refs: list[ProfileEvidenceCarrierRef] = []
    for profile in iterator:
        if isinstance(profile, Mapping):
            raw_refs = profile.get("evidence_refs")
            resource_dependency_mode = profile.get("resource_dependency_mode")
            required_capabilities = profile.get("required_capabilities")
        else:
            raw_refs = getattr(profile, "evidence_refs", None)
            resource_dependency_mode = getattr(profile, "resource_dependency_mode", None)
            required_capabilities = getattr(profile, "required_capabilities", None)
        if isinstance(raw_refs, (str, bytes, Mapping)) or raw_refs is None:
            continue
        try:
            raw_ref_iterator: Iterable[Any] = iter(raw_refs)
        except TypeError:
            continue
        normalized_required_capabilities = _best_effort_canonical_required_capabilities(required_capabilities)
        refs.extend(
            ProfileEvidenceCarrierRef(
                ref=ref,
                adapter_key=adapter_key,
                capability=capability,
                operation=operation,
                target_type=target_type,
                collection_mode=collection_mode,
                resource_dependency_mode=(
                    resource_dependency_mode if isinstance(resource_dependency_mode, str) else None
                ),
                required_capabilities=normalized_required_capabilities,
            )
            for ref in raw_ref_iterator
            if isinstance(ref, str) and ref
        )
    return tuple(refs)


def _best_effort_nested_string_collection(raw_value: Any, section: str, field_name: str) -> tuple[str, ...]:
    if not isinstance(raw_value, Mapping):
        section_value = getattr(raw_value, section, None)
        values = getattr(section_value, field_name, None)
    else:
        section_value = raw_value.get(section)
        values = section_value.get(field_name) if isinstance(section_value, Mapping) else None
    if isinstance(values, (str, bytes, Mapping)) or values is None:
        return ()
    try:
        iterator: Iterable[Any] = iter(values)
    except TypeError:
        return ()
    return tuple(value for value in iterator if isinstance(value, str) and value)


def _best_effort_string_tuple(raw_value: Any) -> tuple[str, ...]:
    if isinstance(raw_value, (str, bytes, Mapping)) or raw_value is None:
        return ()
    try:
        iterator: Iterable[Any] = iter(raw_value)
    except TypeError:
        return ()
    return tuple(value for value in iterator if isinstance(value, str) and value)


def _best_effort_canonical_required_capabilities(raw_value: Any) -> tuple[str, ...]:
    raw_capabilities = _best_effort_string_tuple(raw_value)
    normalized_capabilities = _normalize_required_capabilities(raw_capabilities)
    if len(normalized_capabilities) != len(raw_capabilities):
        return raw_capabilities
    if set(normalized_capabilities) != set(raw_capabilities):
        return raw_capabilities
    return normalized_capabilities


def _best_effort_nested_string(raw_value: Any, section: str, field_name: str) -> str | None:
    if isinstance(raw_value, Mapping):
        section_value = raw_value.get(section)
        value = section_value.get(field_name) if isinstance(section_value, Mapping) else None
    else:
        section_value = getattr(raw_value, section, None)
        value = getattr(section_value, field_name, None)
    return value if isinstance(value, str) and value else None


def _best_effort_string(raw_value: Any, field_name: str) -> str | None:
    if isinstance(raw_value, Mapping):
        value = raw_value.get(field_name)
    else:
        value = getattr(raw_value, field_name, None)
    return value if isinstance(value, str) and value else None


def _normalize_required_capabilities(raw_values: Iterable[str]) -> tuple[str, ...]:
    values = frozenset(raw_values)
    return tuple(value for value in APPROVED_RESOURCE_CAPABILITY_ORDER if value in values)


def _is_opaque_decision_id(decision_id: str) -> bool:
    if ":" in decision_id or "/" in decision_id or "_" in decision_id:
        return False
    if _contains_forbidden_token(decision_id):
        return False
    return all(char.islower() or char.isdigit() or char == "-" for char in decision_id)


def _approved_profile_evidence_refs() -> frozenset[str]:
    return frozenset(entry.profile_ref for entry in approved_shared_resource_requirement_profile_evidence_entries())


def _approved_profile_evidence_entry_by_ref() -> Mapping[str, Any]:
    return {
        entry.profile_ref: entry
        for entry in approved_shared_resource_requirement_profile_evidence_entries()
    }


def _duplicate_values(raw_values: Iterable[str]) -> frozenset[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for raw_value in raw_values:
        if raw_value in seen:
            duplicates.add(raw_value)
        seen.add(raw_value)
    return frozenset(duplicates)


def _detect_provider_leakage(value: Any) -> tuple[str, ...]:
    leaked: set[str] = set()

    def visit(raw_value: Any) -> None:
        if isinstance(raw_value, Mapping):
            for key, nested_value in raw_value.items():
                if isinstance(key, str) and _contains_forbidden_token(key):
                    leaked.add(key)
                visit(nested_value)
        elif isinstance(raw_value, str):
            if _contains_forbidden_token(raw_value):
                leaked.add(raw_value)
        elif not isinstance(raw_value, (bytes, bytearray)):
            try:
                iterator = iter(raw_value)
            except TypeError:
                return
            for nested_value in iterator:
                visit(nested_value)

    visit(value.__dict__ if hasattr(value, "__dict__") else value)
    return tuple(sorted(leaked))


def _contains_forbidden_token(value: str) -> bool:
    normalized = _normalize_token_text(value)
    return any(
        normalized == token
        or normalized.startswith(f"{token}_")
        or normalized.endswith(f"_{token}")
        or f"_{token}_" in normalized
        for token in FORBIDDEN_DECISION_TOKENS
    )


def _normalize_token_text(value: str) -> str:
    with_word_boundaries = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
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


def _require_string_keys(raw_value: Mapping[Any, Any]) -> frozenset[str]:
    return frozenset(key for key in raw_value if isinstance(key, str))


def _require_non_empty_string(raw_value: Any) -> str:
    if not isinstance(raw_value, str) or not raw_value:
        return ""
    return raw_value
