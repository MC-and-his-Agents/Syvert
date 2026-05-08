from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import re
from typing import Any

from syvert.operation_taxonomy import stable_operation_entry
from syvert.resource_capability_evidence import approved_shared_resource_requirement_profile_evidence_entries


PROVIDER_OFFER_STATUS_DECLARED = "declared"
PROVIDER_OFFER_STATUS_INVALID = "invalid"

PROVIDER_OFFER_ERROR_INVALID_OFFER = "invalid_provider_offer"

APPROVED_OPERATION_TAXONOMY_ENTRY = stable_operation_entry(
    operation="content_detail_by_url",
    target_type="url",
    collection_mode="hybrid",
)
APPROVED_PROVIDER_CAPABILITY = APPROVED_OPERATION_TAXONOMY_ENTRY.capability_family
APPROVED_CAPABILITY_OFFER = {
    "capability": APPROVED_PROVIDER_CAPABILITY,
    "operation": APPROVED_OPERATION_TAXONOMY_ENTRY.operation,
    "target_type": APPROVED_OPERATION_TAXONOMY_ENTRY.target_type,
    "collection_mode": APPROVED_OPERATION_TAXONOMY_ENTRY.collection_mode,
}
APPROVED_CONTRACT_VERSION = "v0.8.0"
REQUIRED_VALIDATION_OUTCOME_FIELDS = (
    "validation_status",
    "error_code",
    "failure_category",
)
FORBIDDEN_CREDENTIAL_SESSION_FIELDS = frozenset(
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

REQUIRED_OFFER_FIELDS = frozenset(
    {
        "provider_key",
        "adapter_binding",
        "capability_offer",
        "resource_support",
        "error_carrier",
        "version",
        "evidence",
        "lifecycle",
        "observability",
        "fail_closed",
    }
)
ADAPTER_BINDING_FIELDS = frozenset({"adapter_key", "binding_scope", "provider_port_ref"})
CAPABILITY_OFFER_FIELDS = frozenset(APPROVED_CAPABILITY_OFFER)
RESOURCE_SUPPORT_FIELDS = frozenset({"supported_profiles", "resource_profile_contract_ref"})
SUPPORTED_PROFILE_FIELDS = frozenset(
    {
        "profile_key",
        "resource_dependency_mode",
        "required_capabilities",
        "evidence_refs",
    }
)
ERROR_CARRIER_FIELDS = frozenset(
    {
        "invalid_offer_code",
        "provider_unavailable_code",
        "contract_violation_code",
        "adapter_mapping_required",
    }
)
VERSION_FIELDS = frozenset(
    {
        "contract_version",
        "requirement_contract_ref",
        "resource_profile_contract_ref",
        "provider_port_boundary_ref",
    }
)
EVIDENCE_FIELDS = frozenset(
    {
        "provider_offer_evidence_refs",
        "resource_profile_evidence_refs",
        "adapter_binding_evidence_refs",
    }
)
LIFECYCLE_FIELDS = frozenset(
    {
        "invoked_by_adapter_only",
        "core_discovery_allowed",
        "consumes_adapter_execution_context",
        "uses_existing_resource_bundle_view",
        "adapter_error_mapping_required",
    }
)
OBSERVABILITY_FIELDS = frozenset(
    {
        "offer_id",
        "provider_key",
        "adapter_key",
        "capability",
        "operation",
        "profile_keys",
        "proof_refs",
        "contract_version",
        "validation_outcome_fields",
    }
)
PROVIDER_OFFER_EVIDENCE_REF_PREFIXES = (
    "fr-0025:formal-spec:",
    "fr-0025:offer-manifest-fixture-validator:",
    "fr-0025:sdk-docs:",
    "fr-0025:parent-closeout:",
)
ADAPTER_BINDING_EVIDENCE_REF_PREFIXES = (
    "fr-0021:adapter-provider-port-boundary:",
    "fr-0025:offer-manifest-fixture-validator:",
)
FORBIDDEN_OFFER_FIELDS = frozenset(
    {
        "compatibility_decision",
        "compatibility_status",
        "selected_provider",
        "selected_profile",
        "provider_selection",
        "provider_selector",
        "provider_routing",
        "routing_policy",
        "core_routing",
        "core_provider_registry",
        "core_provider_discovery",
        "provider_registry",
        "global_provider_key",
        "priority",
        "score",
        "ranking",
        "fallback",
        "fallback_order",
        "fallback_outcome",
        "preferred_profile",
        "preferred_profiles",
        "marketplace",
        "marketplace_listing",
        "provider_product_support",
        "sla",
        "availability_sla",
        "resource_supply",
        "resource_pool",
        "account_pool",
        "proxy_pool",
        "provider_lifecycle",
        "task_record_provider_field",
        "playwright",
        "cdp",
        "chromium",
        "browser_profile",
        "network_tier",
        "transport",
    }
).union(FORBIDDEN_CREDENTIAL_SESSION_FIELDS)
FORBIDDEN_PROVIDER_KEY_TOKENS = frozenset({"core", "global", "marketplace", "registry", "routing"})
FORBIDDEN_OBSERVABILITY_TOKENS = frozenset(
    {
        "authorization",
        "cookie",
        "cookies",
        "credential_freshness",
        "credential_material",
        "headers",
        "health_sla",
        "ms_token",
        "selector",
        "routing",
        "fallback",
        "priority",
        "marketplace",
        "product_support",
        "core_registry",
        "task_record",
        "playwright",
        "cdp",
        "chromium",
        "browser",
        "network",
        "transport",
        "session",
        "session_health",
        "session_object",
        "token",
        "verify_fp",
        "xsec_token",
    }
)
REQUIRED_CAPABILITY_ORDER = ("account", "proxy")
ALLOWED_REQUIRED_CAPABILITIES = frozenset(REQUIRED_CAPABILITY_ORDER)
ALLOWED_RESOURCE_DEPENDENCY_MODES = frozenset({"none", "required"})


@dataclass(frozen=True)
class ProviderAdapterBinding:
    adapter_key: str
    binding_scope: str
    provider_port_ref: str


@dataclass(frozen=True)
class ProviderCapabilityOfferDescriptor:
    capability: str
    operation: str
    target_type: str
    collection_mode: str


@dataclass(frozen=True)
class ProviderSupportedResourceProfile:
    profile_key: str
    resource_dependency_mode: str
    required_capabilities: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class ProviderResourceSupport:
    supported_profiles: tuple[ProviderSupportedResourceProfile, ...]
    resource_profile_contract_ref: str


@dataclass(frozen=True)
class ProviderOfferErrorCarrier:
    invalid_offer_code: str
    provider_unavailable_code: str
    contract_violation_code: str
    adapter_mapping_required: bool


@dataclass(frozen=True)
class ProviderOfferVersion:
    contract_version: str
    requirement_contract_ref: str
    resource_profile_contract_ref: str
    provider_port_boundary_ref: str


@dataclass(frozen=True)
class ProviderOfferEvidence:
    provider_offer_evidence_refs: tuple[str, ...]
    resource_profile_evidence_refs: tuple[str, ...]
    adapter_binding_evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class ProviderOfferLifecycleExpectation:
    invoked_by_adapter_only: bool
    core_discovery_allowed: bool
    consumes_adapter_execution_context: bool
    uses_existing_resource_bundle_view: bool
    adapter_error_mapping_required: bool


@dataclass(frozen=True)
class ProviderOfferObservabilityExpectation:
    offer_id: str
    provider_key: str
    adapter_key: str
    capability: str
    operation: str
    profile_keys: tuple[str, ...]
    proof_refs: tuple[str, ...]
    contract_version: str
    validation_outcome_fields: tuple[str, ...]


@dataclass(frozen=True)
class ProviderCapabilityOffer:
    provider_key: str
    adapter_binding: ProviderAdapterBinding
    capability_offer: ProviderCapabilityOfferDescriptor
    resource_support: ProviderResourceSupport
    error_carrier: ProviderOfferErrorCarrier
    version: ProviderOfferVersion
    evidence: ProviderOfferEvidence
    lifecycle: ProviderOfferLifecycleExpectation
    observability: ProviderOfferObservabilityExpectation
    fail_closed: bool


@dataclass(frozen=True)
class ProviderCapabilityOfferValidationResult:
    provider_key: str | None
    adapter_key: str | None
    capability: str | None
    status: str
    failure_category: str | None = None
    error_code: str | None = None
    message: str | None = None
    details: Mapping[str, Any] | None = None


class ProviderCapabilityOfferContractError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})


def validate_provider_capability_offer(
    input_value: ProviderCapabilityOffer | Mapping[str, Any],
) -> ProviderCapabilityOfferValidationResult:
    try:
        offer = _normalize_offer(input_value)
        _validate_offer_contract(offer)
    except ProviderCapabilityOfferContractError as error:
        return ProviderCapabilityOfferValidationResult(
            provider_key=_best_effort_string(input_value, "provider_key"),
            adapter_key=_best_effort_nested_string(input_value, "adapter_binding", "adapter_key"),
            capability=_best_effort_nested_string(input_value, "capability_offer", "capability"),
            status=PROVIDER_OFFER_STATUS_INVALID,
            failure_category="runtime_contract",
            error_code=error.code,
            message=error.message,
            details=error.details,
        )
    return ProviderCapabilityOfferValidationResult(
        provider_key=offer.provider_key,
        adapter_key=offer.adapter_binding.adapter_key,
        capability=offer.capability_offer.capability,
        status=PROVIDER_OFFER_STATUS_DECLARED,
        details={
            "validation_status": PROVIDER_OFFER_STATUS_DECLARED,
            "offer_id": offer.observability.offer_id,
        },
    )


def _normalize_offer(raw_value: ProviderCapabilityOffer | Mapping[str, Any]) -> ProviderCapabilityOffer:
    if type(raw_value) is ProviderCapabilityOffer:
        provider_key = _require_non_empty_string(raw_value.provider_key, field_name="provider_key")
        adapter_binding = _normalize_adapter_binding(raw_value.adapter_binding)
        capability_offer = _normalize_capability_offer(raw_value.capability_offer)
        resource_support = _normalize_resource_support(raw_value.resource_support)
        error_carrier = _normalize_error_carrier(raw_value.error_carrier)
        version = _normalize_version(raw_value.version)
        evidence = _normalize_evidence(raw_value.evidence)
        lifecycle = _normalize_lifecycle(raw_value.lifecycle)
        observability = _normalize_observability(raw_value.observability)
        fail_closed = _require_bool(raw_value.fail_closed, field_name="fail_closed")
        return ProviderCapabilityOffer(
            provider_key=provider_key,
            adapter_binding=adapter_binding,
            capability_offer=capability_offer,
            resource_support=resource_support,
            error_carrier=error_carrier,
            version=version,
            evidence=evidence,
            lifecycle=lifecycle,
            observability=observability,
            fail_closed=fail_closed,
        )
    if not isinstance(raw_value, Mapping):
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "ProviderCapabilityOffer carrier must be a mapping or canonical dataclass",
            details={"actual_type": type(raw_value).__name__},
        )

    raw_keys = _require_string_keys(raw_value, carrier_name="ProviderCapabilityOffer")
    forbidden_fields = _find_forbidden_fields(raw_value)
    if forbidden_fields:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "ProviderCapabilityOffer must not contain decision, selector, routing, "
            "priority, fallback, marketplace, Core routing, or provider leakage fields",
            details={"forbidden_fields": forbidden_fields},
        )
    _require_exact_fields(
        raw_keys,
        required_fields=REQUIRED_OFFER_FIELDS,
        carrier_name="ProviderCapabilityOffer",
    )

    return ProviderCapabilityOffer(
        provider_key=_require_non_empty_string(raw_value["provider_key"], field_name="provider_key"),
        adapter_binding=_normalize_adapter_binding(raw_value["adapter_binding"]),
        capability_offer=_normalize_capability_offer(raw_value["capability_offer"]),
        resource_support=_normalize_resource_support(raw_value["resource_support"]),
        error_carrier=_normalize_error_carrier(raw_value["error_carrier"]),
        version=_normalize_version(raw_value["version"]),
        evidence=_normalize_evidence(raw_value["evidence"]),
        lifecycle=_normalize_lifecycle(raw_value["lifecycle"]),
        observability=_normalize_observability(raw_value["observability"]),
        fail_closed=_require_bool(raw_value["fail_closed"], field_name="fail_closed"),
    )


def _normalize_adapter_binding(raw_value: Any) -> ProviderAdapterBinding:
    if type(raw_value) is ProviderAdapterBinding:
        return ProviderAdapterBinding(
            adapter_key=_require_non_empty_string(raw_value.adapter_key, field_name="adapter_binding.adapter_key"),
            binding_scope=_require_non_empty_string(
                raw_value.binding_scope,
                field_name="adapter_binding.binding_scope",
            ),
            provider_port_ref=_require_non_empty_string(
                raw_value.provider_port_ref,
                field_name="adapter_binding.provider_port_ref",
            ),
        )
    if not isinstance(raw_value, Mapping):
        raise _contract_error("adapter_binding must be a mapping or canonical dataclass", raw_value)
    raw_keys = _require_string_keys(raw_value, carrier_name="adapter_binding")
    _require_exact_fields(raw_keys, required_fields=ADAPTER_BINDING_FIELDS, carrier_name="adapter_binding")
    return ProviderAdapterBinding(
        adapter_key=_require_non_empty_string(raw_value["adapter_key"], field_name="adapter_binding.adapter_key"),
        binding_scope=_require_non_empty_string(
            raw_value["binding_scope"],
            field_name="adapter_binding.binding_scope",
        ),
        provider_port_ref=_require_non_empty_string(
            raw_value["provider_port_ref"],
            field_name="adapter_binding.provider_port_ref",
        ),
    )


def _normalize_capability_offer(raw_value: Any) -> ProviderCapabilityOfferDescriptor:
    if type(raw_value) is ProviderCapabilityOfferDescriptor:
        return ProviderCapabilityOfferDescriptor(
            capability=_require_non_empty_string(raw_value.capability, field_name="capability_offer.capability"),
            operation=_require_non_empty_string(raw_value.operation, field_name="capability_offer.operation"),
            target_type=_require_non_empty_string(raw_value.target_type, field_name="capability_offer.target_type"),
            collection_mode=_require_non_empty_string(
                raw_value.collection_mode,
                field_name="capability_offer.collection_mode",
            ),
        )
    if not isinstance(raw_value, Mapping):
        raise _contract_error("capability_offer must be a mapping or canonical dataclass", raw_value)
    raw_keys = _require_string_keys(raw_value, carrier_name="capability_offer")
    _require_exact_fields(raw_keys, required_fields=CAPABILITY_OFFER_FIELDS, carrier_name="capability_offer")
    return ProviderCapabilityOfferDescriptor(
        capability=_require_non_empty_string(raw_value["capability"], field_name="capability_offer.capability"),
        operation=_require_non_empty_string(raw_value["operation"], field_name="capability_offer.operation"),
        target_type=_require_non_empty_string(raw_value["target_type"], field_name="capability_offer.target_type"),
        collection_mode=_require_non_empty_string(
            raw_value["collection_mode"],
            field_name="capability_offer.collection_mode",
        ),
    )


def _normalize_resource_support(raw_value: Any) -> ProviderResourceSupport:
    if type(raw_value) is ProviderResourceSupport:
        return ProviderResourceSupport(
            supported_profiles=_normalize_supported_profiles(raw_value.supported_profiles),
            resource_profile_contract_ref=_require_non_empty_string(
                raw_value.resource_profile_contract_ref,
                field_name="resource_support.resource_profile_contract_ref",
            ),
        )
    if not isinstance(raw_value, Mapping):
        raise _contract_error("resource_support must be a mapping or canonical dataclass", raw_value)
    raw_keys = _require_string_keys(raw_value, carrier_name="resource_support")
    _require_exact_fields(raw_keys, required_fields=RESOURCE_SUPPORT_FIELDS, carrier_name="resource_support")
    return ProviderResourceSupport(
        supported_profiles=_normalize_supported_profiles(raw_value["supported_profiles"]),
        resource_profile_contract_ref=_require_non_empty_string(
            raw_value["resource_profile_contract_ref"],
            field_name="resource_support.resource_profile_contract_ref",
        ),
    )


def _normalize_supported_profiles(raw_value: Any) -> tuple[ProviderSupportedResourceProfile, ...]:
    if isinstance(raw_value, (str, bytes)) or isinstance(raw_value, Mapping):
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "resource_support.supported_profiles must be a non-empty array",
            details={"actual_type": type(raw_value).__name__},
        )
    try:
        iterator: Iterable[Any] = iter(raw_value)
    except TypeError as error:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "resource_support.supported_profiles must be a non-empty array",
            details={"actual_type": type(raw_value).__name__},
        ) from error

    profiles = tuple(_normalize_supported_profile(profile) for profile in iterator)
    if not profiles:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "resource_support.supported_profiles must not be empty",
        )
    return profiles


def _normalize_supported_profile(raw_value: Any) -> ProviderSupportedResourceProfile:
    if type(raw_value) is ProviderSupportedResourceProfile:
        required_capabilities = _normalize_required_capabilities(raw_value.required_capabilities)
        return ProviderSupportedResourceProfile(
            profile_key=_require_non_empty_string(
                raw_value.profile_key,
                field_name="resource_support.supported_profiles.profile_key",
            ),
            resource_dependency_mode=_require_non_empty_string(
                raw_value.resource_dependency_mode,
                field_name="resource_support.supported_profiles.resource_dependency_mode",
            ),
            required_capabilities=required_capabilities,
            evidence_refs=_normalize_string_tuple(
                raw_value.evidence_refs,
                field_name="resource_support.supported_profiles.evidence_refs",
                allow_empty=False,
            ),
        )
    if not isinstance(raw_value, Mapping):
        raise _contract_error(
            "resource_support.supported_profiles entries must be mappings or canonical dataclasses",
            raw_value,
        )
    raw_keys = _require_string_keys(raw_value, carrier_name="resource_support.supported_profiles")
    _require_exact_fields(
        raw_keys,
        required_fields=SUPPORTED_PROFILE_FIELDS,
        carrier_name="resource_support.supported_profiles",
    )
    return ProviderSupportedResourceProfile(
        profile_key=_require_non_empty_string(
            raw_value["profile_key"],
            field_name="resource_support.supported_profiles.profile_key",
        ),
        resource_dependency_mode=_require_non_empty_string(
            raw_value["resource_dependency_mode"],
            field_name="resource_support.supported_profiles.resource_dependency_mode",
        ),
        required_capabilities=_normalize_required_capabilities(raw_value["required_capabilities"]),
        evidence_refs=_normalize_string_tuple(
            raw_value["evidence_refs"],
            field_name="resource_support.supported_profiles.evidence_refs",
            allow_empty=False,
        ),
    )


def _normalize_error_carrier(raw_value: Any) -> ProviderOfferErrorCarrier:
    if type(raw_value) is ProviderOfferErrorCarrier:
        return ProviderOfferErrorCarrier(
            invalid_offer_code=_require_non_empty_string(
                raw_value.invalid_offer_code,
                field_name="error_carrier.invalid_offer_code",
            ),
            provider_unavailable_code=_require_non_empty_string(
                raw_value.provider_unavailable_code,
                field_name="error_carrier.provider_unavailable_code",
            ),
            contract_violation_code=_require_non_empty_string(
                raw_value.contract_violation_code,
                field_name="error_carrier.contract_violation_code",
            ),
            adapter_mapping_required=_require_bool(
                raw_value.adapter_mapping_required,
                field_name="error_carrier.adapter_mapping_required",
            ),
        )
    if not isinstance(raw_value, Mapping):
        raise _contract_error("error_carrier must be a mapping or canonical dataclass", raw_value)
    raw_keys = _require_string_keys(raw_value, carrier_name="error_carrier")
    _require_exact_fields(raw_keys, required_fields=ERROR_CARRIER_FIELDS, carrier_name="error_carrier")
    return ProviderOfferErrorCarrier(
        invalid_offer_code=_require_non_empty_string(
            raw_value["invalid_offer_code"],
            field_name="error_carrier.invalid_offer_code",
        ),
        provider_unavailable_code=_require_non_empty_string(
            raw_value["provider_unavailable_code"],
            field_name="error_carrier.provider_unavailable_code",
        ),
        contract_violation_code=_require_non_empty_string(
            raw_value["contract_violation_code"],
            field_name="error_carrier.contract_violation_code",
        ),
        adapter_mapping_required=_require_bool(
            raw_value["adapter_mapping_required"],
            field_name="error_carrier.adapter_mapping_required",
        ),
    )


def _normalize_version(raw_value: Any) -> ProviderOfferVersion:
    if type(raw_value) is ProviderOfferVersion:
        return ProviderOfferVersion(
            contract_version=_require_non_empty_string(
                raw_value.contract_version,
                field_name="version.contract_version",
            ),
            requirement_contract_ref=_require_non_empty_string(
                raw_value.requirement_contract_ref,
                field_name="version.requirement_contract_ref",
            ),
            resource_profile_contract_ref=_require_non_empty_string(
                raw_value.resource_profile_contract_ref,
                field_name="version.resource_profile_contract_ref",
            ),
            provider_port_boundary_ref=_require_non_empty_string(
                raw_value.provider_port_boundary_ref,
                field_name="version.provider_port_boundary_ref",
            ),
        )
    if not isinstance(raw_value, Mapping):
        raise _contract_error("version must be a mapping or canonical dataclass", raw_value)
    raw_keys = _require_string_keys(raw_value, carrier_name="version")
    _require_exact_fields(raw_keys, required_fields=VERSION_FIELDS, carrier_name="version")
    return ProviderOfferVersion(
        contract_version=_require_non_empty_string(
            raw_value["contract_version"],
            field_name="version.contract_version",
        ),
        requirement_contract_ref=_require_non_empty_string(
            raw_value["requirement_contract_ref"],
            field_name="version.requirement_contract_ref",
        ),
        resource_profile_contract_ref=_require_non_empty_string(
            raw_value["resource_profile_contract_ref"],
            field_name="version.resource_profile_contract_ref",
        ),
        provider_port_boundary_ref=_require_non_empty_string(
            raw_value["provider_port_boundary_ref"],
            field_name="version.provider_port_boundary_ref",
        ),
    )


def _normalize_evidence(raw_value: Any) -> ProviderOfferEvidence:
    if type(raw_value) is ProviderOfferEvidence:
        return ProviderOfferEvidence(
            provider_offer_evidence_refs=_normalize_string_tuple(
                raw_value.provider_offer_evidence_refs,
                field_name="evidence.provider_offer_evidence_refs",
                allow_empty=False,
            ),
            resource_profile_evidence_refs=_normalize_string_tuple(
                raw_value.resource_profile_evidence_refs,
                field_name="evidence.resource_profile_evidence_refs",
                allow_empty=False,
            ),
            adapter_binding_evidence_refs=_normalize_string_tuple(
                raw_value.adapter_binding_evidence_refs,
                field_name="evidence.adapter_binding_evidence_refs",
                allow_empty=False,
            ),
        )
    if not isinstance(raw_value, Mapping):
        raise _contract_error("evidence must be a mapping or canonical dataclass", raw_value)
    raw_keys = _require_string_keys(raw_value, carrier_name="evidence")
    _require_exact_fields(raw_keys, required_fields=EVIDENCE_FIELDS, carrier_name="evidence")
    return ProviderOfferEvidence(
        provider_offer_evidence_refs=_normalize_string_tuple(
            raw_value["provider_offer_evidence_refs"],
            field_name="evidence.provider_offer_evidence_refs",
            allow_empty=False,
        ),
        resource_profile_evidence_refs=_normalize_string_tuple(
            raw_value["resource_profile_evidence_refs"],
            field_name="evidence.resource_profile_evidence_refs",
            allow_empty=False,
        ),
        adapter_binding_evidence_refs=_normalize_string_tuple(
            raw_value["adapter_binding_evidence_refs"],
            field_name="evidence.adapter_binding_evidence_refs",
            allow_empty=False,
        ),
    )


def _normalize_lifecycle(raw_value: Any) -> ProviderOfferLifecycleExpectation:
    if type(raw_value) is ProviderOfferLifecycleExpectation:
        return ProviderOfferLifecycleExpectation(
            invoked_by_adapter_only=_require_bool(
                raw_value.invoked_by_adapter_only,
                field_name="lifecycle.invoked_by_adapter_only",
            ),
            core_discovery_allowed=_require_bool(
                raw_value.core_discovery_allowed,
                field_name="lifecycle.core_discovery_allowed",
            ),
            consumes_adapter_execution_context=_require_bool(
                raw_value.consumes_adapter_execution_context,
                field_name="lifecycle.consumes_adapter_execution_context",
            ),
            uses_existing_resource_bundle_view=_require_bool(
                raw_value.uses_existing_resource_bundle_view,
                field_name="lifecycle.uses_existing_resource_bundle_view",
            ),
            adapter_error_mapping_required=_require_bool(
                raw_value.adapter_error_mapping_required,
                field_name="lifecycle.adapter_error_mapping_required",
            ),
        )
    if not isinstance(raw_value, Mapping):
        raise _contract_error("lifecycle must be a mapping or canonical dataclass", raw_value)
    raw_keys = _require_string_keys(raw_value, carrier_name="lifecycle")
    _require_exact_fields(raw_keys, required_fields=LIFECYCLE_FIELDS, carrier_name="lifecycle")
    return ProviderOfferLifecycleExpectation(
        invoked_by_adapter_only=_require_bool(
            raw_value["invoked_by_adapter_only"],
            field_name="lifecycle.invoked_by_adapter_only",
        ),
        core_discovery_allowed=_require_bool(
            raw_value["core_discovery_allowed"],
            field_name="lifecycle.core_discovery_allowed",
        ),
        consumes_adapter_execution_context=_require_bool(
            raw_value["consumes_adapter_execution_context"],
            field_name="lifecycle.consumes_adapter_execution_context",
        ),
        uses_existing_resource_bundle_view=_require_bool(
            raw_value["uses_existing_resource_bundle_view"],
            field_name="lifecycle.uses_existing_resource_bundle_view",
        ),
        adapter_error_mapping_required=_require_bool(
            raw_value["adapter_error_mapping_required"],
            field_name="lifecycle.adapter_error_mapping_required",
        ),
    )


def _normalize_observability(raw_value: Any) -> ProviderOfferObservabilityExpectation:
    if type(raw_value) is ProviderOfferObservabilityExpectation:
        return ProviderOfferObservabilityExpectation(
            offer_id=_require_non_empty_string(raw_value.offer_id, field_name="observability.offer_id"),
            provider_key=_require_non_empty_string(raw_value.provider_key, field_name="observability.provider_key"),
            adapter_key=_require_non_empty_string(raw_value.adapter_key, field_name="observability.adapter_key"),
            capability=_require_non_empty_string(raw_value.capability, field_name="observability.capability"),
            operation=_require_non_empty_string(raw_value.operation, field_name="observability.operation"),
            profile_keys=_normalize_string_tuple(
                raw_value.profile_keys,
                field_name="observability.profile_keys",
                allow_empty=False,
            ),
            proof_refs=_normalize_string_tuple(
                raw_value.proof_refs,
                field_name="observability.proof_refs",
                allow_empty=False,
            ),
            contract_version=_require_non_empty_string(
                raw_value.contract_version,
                field_name="observability.contract_version",
            ),
            validation_outcome_fields=_normalize_string_tuple(
                raw_value.validation_outcome_fields,
                field_name="observability.validation_outcome_fields",
                allow_empty=False,
            ),
        )
    if not isinstance(raw_value, Mapping):
        raise _contract_error("observability must be a mapping or canonical dataclass", raw_value)
    raw_keys = _require_string_keys(raw_value, carrier_name="observability")
    _require_exact_fields(raw_keys, required_fields=OBSERVABILITY_FIELDS, carrier_name="observability")
    return ProviderOfferObservabilityExpectation(
        offer_id=_require_non_empty_string(raw_value["offer_id"], field_name="observability.offer_id"),
        provider_key=_require_non_empty_string(raw_value["provider_key"], field_name="observability.provider_key"),
        adapter_key=_require_non_empty_string(raw_value["adapter_key"], field_name="observability.adapter_key"),
        capability=_require_non_empty_string(raw_value["capability"], field_name="observability.capability"),
        operation=_require_non_empty_string(raw_value["operation"], field_name="observability.operation"),
        profile_keys=_normalize_string_tuple(
            raw_value["profile_keys"],
            field_name="observability.profile_keys",
            allow_empty=False,
        ),
        proof_refs=_normalize_string_tuple(
            raw_value["proof_refs"],
            field_name="observability.proof_refs",
            allow_empty=False,
        ),
        contract_version=_require_non_empty_string(
            raw_value["contract_version"],
            field_name="observability.contract_version",
        ),
        validation_outcome_fields=_normalize_string_tuple(
            raw_value["validation_outcome_fields"],
            field_name="observability.validation_outcome_fields",
            allow_empty=False,
        ),
    )


def _validate_offer_contract(offer: ProviderCapabilityOffer) -> None:
    _validate_provider_key(offer.provider_key)
    _validate_adapter_binding(offer.adapter_binding)
    _validate_capability_offer(offer.capability_offer)
    _validate_resource_support(
        offer.resource_support,
        adapter_key=offer.adapter_binding.adapter_key,
        capability_offer=offer.capability_offer,
    )
    _validate_error_carrier(offer.error_carrier)
    _validate_version(offer.version)
    _validate_evidence(offer.evidence, resource_support=offer.resource_support)
    _validate_lifecycle(offer.lifecycle, resource_support=offer.resource_support)
    _validate_observability(offer.observability, offer=offer)
    if not offer.fail_closed:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "ProviderCapabilityOffer.fail_closed must be true",
            details={"fail_closed": offer.fail_closed},
        )


def _validate_provider_key(provider_key: str) -> None:
    normalized = _normalize_token_text(provider_key)
    leaked_tokens = tuple(token for token in FORBIDDEN_PROVIDER_KEY_TOKENS if token in normalized)
    if leaked_tokens:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "provider_key must remain adapter-bound and must not claim Core, "
            "global, marketplace, registry, or routing identity",
            details={"provider_key": provider_key, "leaked_tokens": leaked_tokens},
        )


def _validate_adapter_binding(adapter_binding: ProviderAdapterBinding) -> None:
    if adapter_binding.binding_scope != "adapter_bound":
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "adapter_binding.binding_scope must be adapter_bound",
            details={"binding_scope": adapter_binding.binding_scope},
        )
    expected_prefix = f"{adapter_binding.adapter_key}:"
    if not adapter_binding.provider_port_ref.startswith(expected_prefix):
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "adapter_binding.provider_port_ref must be owned by adapter_binding.adapter_key",
            details={
                "adapter_key": adapter_binding.adapter_key,
                "provider_port_ref": adapter_binding.provider_port_ref,
                "expected_prefix": expected_prefix,
            },
        )
    normalized_port_ref = _normalize_token_text(adapter_binding.provider_port_ref)
    forbidden_tokens = (
        "core",
        "global",
        "public_sdk",
        "marketplace",
        "registry",
        "routing",
    )
    leaked_tokens = tuple(token for token in forbidden_tokens if token in normalized_port_ref)
    if leaked_tokens:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "adapter_binding.provider_port_ref must not point at Core or global provider surfaces",
            details={
                "provider_port_ref": adapter_binding.provider_port_ref,
                "leaked_tokens": leaked_tokens,
            },
        )


def _validate_capability_offer(capability_offer: ProviderCapabilityOfferDescriptor) -> None:
    actual_offer = dict(capability_offer.__dict__)
    if actual_offer != APPROVED_CAPABILITY_OFFER:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "capability_offer must stay frozen to content_detail_by_url + url + hybrid",
            details={
                "expected_capability_offer": APPROVED_CAPABILITY_OFFER,
                "actual_capability_offer": actual_offer,
            },
        )


def _validate_resource_support(
    resource_support: ProviderResourceSupport,
    *,
    adapter_key: str,
    capability_offer: ProviderCapabilityOfferDescriptor,
) -> None:
    if resource_support.resource_profile_contract_ref != "FR-0027":
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "resource_support.resource_profile_contract_ref must be FR-0027",
            details={"resource_profile_contract_ref": resource_support.resource_profile_contract_ref},
        )

    seen_profile_keys: set[str] = set()
    seen_semantic_tuples: set[tuple[str, tuple[str, ...]]] = set()
    approved_profile_entries = {
        entry.profile_ref: entry
        for entry in approved_shared_resource_requirement_profile_evidence_entries()
    }
    for profile in resource_support.supported_profiles:
        if profile.profile_key in seen_profile_keys:
            raise ProviderCapabilityOfferContractError(
                PROVIDER_OFFER_ERROR_INVALID_OFFER,
                "resource_support.supported_profiles must not repeat profile_key",
                details={"profile_key": profile.profile_key},
            )
        seen_profile_keys.add(profile.profile_key)
        if profile.resource_dependency_mode not in ALLOWED_RESOURCE_DEPENDENCY_MODES:
            raise ProviderCapabilityOfferContractError(
                PROVIDER_OFFER_ERROR_INVALID_OFFER,
                "resource_dependency_mode must be none or required",
                details={
                    "profile_key": profile.profile_key,
                    "resource_dependency_mode": profile.resource_dependency_mode,
                },
            )
        if profile.resource_dependency_mode == "none" and profile.required_capabilities:
            raise ProviderCapabilityOfferContractError(
                PROVIDER_OFFER_ERROR_INVALID_OFFER,
                "resource_dependency_mode=none requires empty required_capabilities",
                details={"profile_key": profile.profile_key},
            )
        if profile.resource_dependency_mode == "required" and not profile.required_capabilities:
            raise ProviderCapabilityOfferContractError(
                PROVIDER_OFFER_ERROR_INVALID_OFFER,
                "resource_dependency_mode=required requires non-empty required_capabilities",
                details={"profile_key": profile.profile_key},
            )
        semantic_tuple = (profile.resource_dependency_mode, profile.required_capabilities)
        if semantic_tuple in seen_semantic_tuples:
            raise ProviderCapabilityOfferContractError(
                PROVIDER_OFFER_ERROR_INVALID_OFFER,
                "resource_support.supported_profiles must not repeat semantic profile tuples",
                details={"profile_key": profile.profile_key},
            )
        seen_semantic_tuples.add(semantic_tuple)
        if len(profile.evidence_refs) != 1:
            raise ProviderCapabilityOfferContractError(
                PROVIDER_OFFER_ERROR_INVALID_OFFER,
                "resource_support.supported_profiles.evidence_refs must bind exactly one FR-0027 profile proof",
                details={"profile_key": profile.profile_key, "evidence_refs": profile.evidence_refs},
            )
        proof_ref = profile.evidence_refs[0]
        proof = approved_profile_entries.get(proof_ref)
        if proof is None:
            raise ProviderCapabilityOfferContractError(
                PROVIDER_OFFER_ERROR_INVALID_OFFER,
                "resource_support.supported_profiles.evidence_refs must bind to an "
                "approved FR-0027 shared profile proof",
                details={"profile_key": profile.profile_key, "proof_ref": proof_ref},
            )
        if adapter_key not in proof.reference_adapters:
            raise ProviderCapabilityOfferContractError(
                PROVIDER_OFFER_ERROR_INVALID_OFFER,
                "profile proof reference_adapters must cover adapter_binding.adapter_key",
                details={
                    "profile_key": profile.profile_key,
                    "adapter_key": adapter_key,
                    "reference_adapters": proof.reference_adapters,
                },
            )
        if (
            proof.capability != capability_offer.capability
            or proof.execution_path.operation != capability_offer.operation
            or proof.execution_path.target_type != capability_offer.target_type
            or proof.execution_path.collection_mode != capability_offer.collection_mode
            or proof.resource_dependency_mode != profile.resource_dependency_mode
            or proof.required_capabilities != profile.required_capabilities
        ):
            raise ProviderCapabilityOfferContractError(
                PROVIDER_OFFER_ERROR_INVALID_OFFER,
                "profile proof must align with capability_offer and supported profile tuple",
                details={"profile_key": profile.profile_key, "proof_ref": proof_ref},
            )


def _validate_error_carrier(error_carrier: ProviderOfferErrorCarrier) -> None:
    expected = ProviderOfferErrorCarrier(
        invalid_offer_code=PROVIDER_OFFER_ERROR_INVALID_OFFER,
        provider_unavailable_code="provider_unavailable",
        contract_violation_code="provider_contract_violation",
        adapter_mapping_required=True,
    )
    if error_carrier != expected:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "error_carrier must stay frozen to Adapter-mapped Provider offer error codes",
            details={"expected_error_carrier": expected.__dict__, "actual_error_carrier": error_carrier.__dict__},
        )


def _validate_version(version: ProviderOfferVersion) -> None:
    expected = ProviderOfferVersion(
        contract_version=APPROVED_CONTRACT_VERSION,
        requirement_contract_ref="FR-0024",
        resource_profile_contract_ref="FR-0027",
        provider_port_boundary_ref="FR-0021",
    )
    if version != expected:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "version must stay frozen to FR-0025 v0.8.0 contract boundaries",
            details={"expected_version": expected.__dict__, "actual_version": version.__dict__},
        )


def _validate_evidence(
    evidence: ProviderOfferEvidence,
    *,
    resource_support: ProviderResourceSupport,
) -> None:
    _validate_evidence_refs(
        evidence.provider_offer_evidence_refs,
        field_name="evidence.provider_offer_evidence_refs",
        allowed_prefixes=PROVIDER_OFFER_EVIDENCE_REF_PREFIXES,
    )
    _validate_evidence_refs(
        evidence.adapter_binding_evidence_refs,
        field_name="evidence.adapter_binding_evidence_refs",
        allowed_prefixes=ADAPTER_BINDING_EVIDENCE_REF_PREFIXES,
    )
    resource_profile_evidence_refs = tuple(
        evidence_ref
        for profile in resource_support.supported_profiles
        for evidence_ref in profile.evidence_refs
    )
    if evidence.resource_profile_evidence_refs != resource_profile_evidence_refs:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "evidence.resource_profile_evidence_refs must align with resource_support supported profile proofs",
            details={
                "expected_resource_profile_evidence_refs": resource_profile_evidence_refs,
                "actual_resource_profile_evidence_refs": evidence.resource_profile_evidence_refs,
            },
        )


def _validate_lifecycle(
    lifecycle: ProviderOfferLifecycleExpectation,
    *,
    resource_support: ProviderResourceSupport,
) -> None:
    if not lifecycle.invoked_by_adapter_only:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "lifecycle.invoked_by_adapter_only must be true",
        )
    if lifecycle.core_discovery_allowed:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "lifecycle.core_discovery_allowed must be false",
            details={"core_discovery_allowed": lifecycle.core_discovery_allowed},
        )
    if not lifecycle.consumes_adapter_execution_context:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "lifecycle.consumes_adapter_execution_context must be true",
        )
    requires_resources = any(
        profile.resource_dependency_mode == "required"
        for profile in resource_support.supported_profiles
    )
    if requires_resources and not lifecycle.uses_existing_resource_bundle_view:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "lifecycle.uses_existing_resource_bundle_view must be true when supported profiles require resources",
        )
    if not lifecycle.adapter_error_mapping_required:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "lifecycle.adapter_error_mapping_required must be true",
        )


def _validate_observability(
    observability: ProviderOfferObservabilityExpectation,
    *,
    offer: ProviderCapabilityOffer,
) -> None:
    expected_offer_id = _offer_id(offer)
    if observability.offer_id != expected_offer_id:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "observability.offer_id must align with the canonical ProviderCapabilityOffer identity",
            details={"expected_offer_id": expected_offer_id, "actual_offer_id": observability.offer_id},
        )
    expected_values = {
        "provider_key": offer.provider_key,
        "adapter_key": offer.adapter_binding.adapter_key,
        "capability": offer.capability_offer.capability,
        "operation": offer.capability_offer.operation,
        "contract_version": offer.version.contract_version,
    }
    actual_values = {
        "provider_key": observability.provider_key,
        "adapter_key": observability.adapter_key,
        "capability": observability.capability,
        "operation": observability.operation,
        "contract_version": observability.contract_version,
    }
    if actual_values != expected_values:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "observability scalar fields must align with ProviderCapabilityOffer fields",
            details={"expected_values": expected_values, "actual_values": actual_values},
        )
    profile_keys = tuple(profile.profile_key for profile in offer.resource_support.supported_profiles)
    if observability.profile_keys != profile_keys:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "observability.profile_keys must align with resource_support.supported_profiles",
            details={"expected_profile_keys": profile_keys, "actual_profile_keys": observability.profile_keys},
        )
    if observability.proof_refs != offer.evidence.resource_profile_evidence_refs:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "observability.proof_refs must align with evidence.resource_profile_evidence_refs",
            details={
                "expected_proof_refs": offer.evidence.resource_profile_evidence_refs,
                "actual_proof_refs": observability.proof_refs,
            },
        )
    if observability.validation_outcome_fields != REQUIRED_VALIDATION_OUTCOME_FIELDS:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "observability.validation_outcome_fields must stay frozen to approved validation fields",
            details={
                "expected_validation_outcome_fields": REQUIRED_VALIDATION_OUTCOME_FIELDS,
                "actual_validation_outcome_fields": observability.validation_outcome_fields,
            },
        )
    leaked_values = tuple(
        value
        for value in (
            observability.offer_id,
            observability.adapter_key,
            observability.capability,
            observability.operation,
            *observability.profile_keys,
            *observability.proof_refs,
            observability.contract_version,
            *observability.validation_outcome_fields,
        )
        if _contains_forbidden_observability_token(value)
    )
    if leaked_values:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "observability must not expose selector, routing, fallback, marketplace, "
            "Core, TaskRecord, or technical chain fields",
            details={"leaked_values": leaked_values},
        )


def _validate_evidence_refs(
    evidence_refs: tuple[str, ...],
    *,
    field_name: str,
    allowed_prefixes: tuple[str, ...],
) -> None:
    unsupported_refs = tuple(
        evidence_ref
        for evidence_ref in evidence_refs
        if not any(evidence_ref.startswith(prefix) and evidence_ref != prefix for prefix in allowed_prefixes)
    )
    if unsupported_refs:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            f"{field_name} must use approved evidence ref categories",
            details={"unsupported_refs": unsupported_refs, "allowed_prefixes": allowed_prefixes},
        )


def _require_exact_fields(
    actual_fields: frozenset[str],
    *,
    required_fields: frozenset[str],
    carrier_name: str,
) -> None:
    missing_fields = tuple(sorted(required_fields - actual_fields))
    extra_fields = tuple(sorted(actual_fields - required_fields))
    if missing_fields or extra_fields:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            f"{carrier_name} must keep the canonical field set",
            details={"missing_fields": missing_fields, "extra_fields": extra_fields},
        )


def _require_string_keys(raw_value: Mapping[Any, Any], *, carrier_name: str) -> frozenset[str]:
    raw_keys = frozenset(raw_value)
    invalid_keys = tuple(sorted(str(key) for key in raw_keys if not isinstance(key, str)))
    if invalid_keys:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            f"{carrier_name} field names must be strings",
            details={"invalid_keys": invalid_keys},
        )
    return frozenset(key for key in raw_keys if isinstance(key, str))


def _find_forbidden_fields(raw_value: Any) -> tuple[str, ...]:
    found: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, nested_value in value.items():
                if isinstance(key, str) and _contains_forbidden_offer_field_token(key):
                    found.add(key)
                visit(nested_value)
        elif not isinstance(value, (str, bytes)):
            try:
                iterator = iter(value)
            except TypeError:
                return
            for nested_value in iterator:
                visit(nested_value)

    visit(raw_value)
    return tuple(sorted(found))


def _contains_forbidden_offer_field_token(field_name: str) -> bool:
    normalized = _normalize_token_text(field_name)
    return any(
        normalized == token
        or normalized.startswith(f"{token}_")
        or normalized.endswith(f"_{token}")
        or f"_{token}_" in normalized
        for token in FORBIDDEN_OFFER_FIELDS
    )


def _require_non_empty_string(raw_value: Any, *, field_name: str) -> str:
    if not isinstance(raw_value, str) or not raw_value:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            f"{field_name} must be a non-empty string",
            details={"field_name": field_name, "actual_type": type(raw_value).__name__},
        )
    return raw_value


def _require_bool(raw_value: Any, *, field_name: str) -> bool:
    if type(raw_value) is not bool:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            f"{field_name} must be a boolean",
            details={"field_name": field_name, "actual_type": type(raw_value).__name__},
        )
    return raw_value


def _normalize_string_tuple(raw_values: Any, *, field_name: str, allow_empty: bool) -> tuple[str, ...]:
    if raw_values is None:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            f"{field_name} must be a deduplicated string collection",
            details={"actual_type": "NoneType"},
        )
    if isinstance(raw_values, (str, bytes)):
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            f"{field_name} must be a deduplicated string collection",
            details={"actual_type": type(raw_values).__name__},
        )
    if isinstance(raw_values, Mapping):
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            f"{field_name} must be a string array, not a mapping",
            details={"actual_type": type(raw_values).__name__},
        )
    try:
        iterator: Iterable[Any] = iter(raw_values)
    except TypeError as error:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            f"{field_name} must be a deduplicated string collection",
            details={"actual_type": type(raw_values).__name__},
        ) from error

    values: list[str] = []
    seen: set[str] = set()
    for raw_value in iterator:
        if not isinstance(raw_value, str) or not raw_value:
            raise ProviderCapabilityOfferContractError(
                PROVIDER_OFFER_ERROR_INVALID_OFFER,
                f"{field_name} values must be non-empty strings",
                details={"invalid_value": raw_value},
            )
        if raw_value in seen:
            raise ProviderCapabilityOfferContractError(
                PROVIDER_OFFER_ERROR_INVALID_OFFER,
                f"{field_name} must not contain duplicate values",
                details={"duplicate_value": raw_value},
            )
        seen.add(raw_value)
        values.append(raw_value)
    if not allow_empty and not values:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            f"{field_name} must not be empty",
        )
    return tuple(values)


def _normalize_required_capabilities(raw_values: Any) -> tuple[str, ...]:
    values = _normalize_string_tuple(
        raw_values,
        field_name="resource_support.supported_profiles.required_capabilities",
        allow_empty=True,
    )
    unsupported_values = tuple(value for value in values if value not in ALLOWED_REQUIRED_CAPABILITIES)
    if unsupported_values:
        raise ProviderCapabilityOfferContractError(
            PROVIDER_OFFER_ERROR_INVALID_OFFER,
            "required_capabilities must only use FR-0027 approved account/proxy vocabulary",
            details={"unsupported_required_capabilities": unsupported_values},
        )
    return tuple(value for value in REQUIRED_CAPABILITY_ORDER if value in values)


def _offer_id(offer: ProviderCapabilityOffer) -> str:
    return ":".join(
        (
            offer.adapter_binding.adapter_key,
            offer.provider_key,
            offer.capability_offer.capability,
            offer.capability_offer.operation,
            offer.capability_offer.target_type,
            offer.capability_offer.collection_mode,
            offer.version.contract_version,
        )
    )


def _contains_forbidden_observability_token(value: str) -> bool:
    normalized = _normalize_token_text(value)
    return any(token in normalized for token in FORBIDDEN_OBSERVABILITY_TOKENS)


def _normalize_token_text(value: str) -> str:
    with_word_boundaries = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
    with_word_boundaries = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", with_word_boundaries)
    normalized = with_word_boundaries.replace("-", "_").replace(":", "_").lower()
    chars: list[str] = []
    for char in normalized:
        chars.append(char if char.isalnum() or char == "_" else "_")
    return "".join(chars)


def _contract_error(message: str, raw_value: Any) -> ProviderCapabilityOfferContractError:
    return ProviderCapabilityOfferContractError(
        PROVIDER_OFFER_ERROR_INVALID_OFFER,
        message,
        details={"actual_type": type(raw_value).__name__},
    )


def _best_effort_string(raw_value: Any, field_name: str) -> str | None:
    if isinstance(raw_value, Mapping):
        value = raw_value.get(field_name)
        return value if isinstance(value, str) else None
    value = getattr(raw_value, field_name, None)
    return value if isinstance(value, str) else None


def _best_effort_nested_string(raw_value: Any, section_name: str, field_name: str) -> str | None:
    if isinstance(raw_value, Mapping):
        section = raw_value.get(section_name)
        if isinstance(section, Mapping):
            value = section.get(field_name)
            return value if isinstance(value, str) else None
        return None
    section = getattr(raw_value, section_name, None)
    value = getattr(section, field_name, None)
    return value if isinstance(value, str) else None
