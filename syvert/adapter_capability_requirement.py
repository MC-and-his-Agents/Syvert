from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import re
from typing import Any

from syvert.registry import (
    AdapterRegistry,
    AdapterResourceRequirementDeclarationV2,
    RegistryError,
)
from syvert.runtime import (
    MATCH_STATUS_MATCHED,
    MATCH_STATUS_UNMATCHED,
    ResourceCapabilityMatcherContractError,
    ResourceCapabilityMatcherInput,
    match_resource_capabilities,
)
from syvert.operation_taxonomy import stable_operation_entry


ADAPTER_REQUIREMENT_STATUS_DECLARED = "declared"
ADAPTER_REQUIREMENT_STATUS_UNMATCHED = "unmatched"
ADAPTER_REQUIREMENT_STATUS_INVALID = "invalid"

ADAPTER_REQUIREMENT_ERROR_INVALID_RESOURCE_REQUIREMENT = "invalid_resource_requirement"
ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT = ADAPTER_REQUIREMENT_ERROR_INVALID_RESOURCE_REQUIREMENT

APPROVED_OPERATION_TAXONOMY_ENTRY = stable_operation_entry(
    operation="content_detail_by_url",
    target_type="url",
    collection_mode="hybrid",
)
APPROVED_ADAPTER_CAPABILITY = APPROVED_OPERATION_TAXONOMY_ENTRY.capability_family
APPROVED_EXECUTION_REQUIREMENT = {
    "operation": APPROVED_OPERATION_TAXONOMY_ENTRY.operation,
    "target_type": APPROVED_OPERATION_TAXONOMY_ENTRY.target_type,
    "collection_mode": APPROVED_OPERATION_TAXONOMY_ENTRY.collection_mode,
}
REQUIRED_REQUIREMENT_FIELDS = frozenset(
    {
        "adapter_key",
        "capability",
        "execution_requirement",
        "resource_requirement",
        "evidence",
        "lifecycle",
        "observability",
        "fail_closed",
    }
)
EXECUTION_REQUIREMENT_FIELDS = frozenset(APPROVED_EXECUTION_REQUIREMENT)
EVIDENCE_FIELDS = frozenset(
    {
        "resource_profile_evidence_refs",
        "capability_requirement_evidence_refs",
    }
)
CAPABILITY_REQUIREMENT_EVIDENCE_REF_PREFIXES = (
    "fr-0024:formal-spec:",
    "fr-0024:manifest-fixture-validator:",
    "fr-0024:reference-adapter-migration:",
    "fr-0024:parent-closeout:",
)
LIFECYCLE_FIELDS = frozenset(
    {
        "requires_core_resource_bundle",
        "resource_profiles_drive_admission",
        "uses_existing_disposition_hint",
    }
)
OBSERVABILITY_FIELDS = frozenset(
    {
        "requirement_id",
        "profile_keys",
        "proof_refs",
        "admission_outcome_fields",
    }
)
REQUIRED_ADMISSION_OUTCOME_FIELDS = (
    "match_status",
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
FORBIDDEN_REQUIREMENT_FIELDS = frozenset(
    {
        "provider_offer",
        "provider_key",
        "provider_selection",
        "provider_selector",
        "provider_priority",
        "provider_routing",
        "provider_capability_offer",
        "compatibility_decision",
        "compatibility_status",
        "priority",
        "fallback",
        "fallback_order",
        "fallback_outcome",
        "preferred_profile",
        "preferred_profiles",
        "optional_capabilities",
        "external_provider_ref",
        "resource_provider",
        "native_provider",
    }
).union(FORBIDDEN_CREDENTIAL_SESSION_FIELDS)
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
        "provider",
        "selector",
        "fallback",
        "priority",
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


@dataclass(frozen=True)
class AdapterCapabilityExecutionRequirement:
    operation: str
    target_type: str
    collection_mode: str


@dataclass(frozen=True)
class AdapterCapabilityRequirementEvidence:
    resource_profile_evidence_refs: tuple[str, ...]
    capability_requirement_evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class AdapterCapabilityLifecycleExpectation:
    requires_core_resource_bundle: bool
    resource_profiles_drive_admission: bool
    uses_existing_disposition_hint: bool


@dataclass(frozen=True)
class AdapterCapabilityObservabilityExpectation:
    requirement_id: str
    profile_keys: tuple[str, ...]
    proof_refs: tuple[str, ...]
    admission_outcome_fields: tuple[str, ...]


@dataclass(frozen=True)
class AdapterCapabilityRequirement:
    adapter_key: str
    capability: str
    execution_requirement: AdapterCapabilityExecutionRequirement
    resource_requirement: AdapterResourceRequirementDeclarationV2
    evidence: AdapterCapabilityRequirementEvidence
    lifecycle: AdapterCapabilityLifecycleExpectation
    observability: AdapterCapabilityObservabilityExpectation
    fail_closed: bool


@dataclass(frozen=True)
class AdapterCapabilityRequirementValidationInput:
    requirement: AdapterCapabilityRequirement | Mapping[str, Any]
    available_resource_capabilities: tuple[str, ...] = ()


@dataclass(frozen=True)
class AdapterCapabilityRequirementValidationResult:
    adapter_key: str | None
    capability: str | None
    status: str
    failure_category: str | None = None
    error_code: str | None = None
    message: str | None = None
    details: Mapping[str, Any] | None = None


class AdapterCapabilityRequirementContractError(Exception):
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


class _RequirementValidationAdapter:
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def __init__(
        self,
        *,
        supported_capability: str,
        resource_requirement: Any,
    ) -> None:
        self.supported_capabilities = frozenset({supported_capability})
        self.resource_requirement_declarations = (resource_requirement,)

    def execute(self) -> None:
        raise AssertionError("requirement validation must not execute adapters")


def baseline_adapter_capability_requirement(
    *,
    adapter_key: str,
    resource_requirement: AdapterResourceRequirementDeclarationV2,
) -> AdapterCapabilityRequirement:
    profile_keys = tuple(profile.profile_key for profile in resource_requirement.resource_requirement_profiles)
    resource_profile_evidence_refs = tuple(
        evidence_ref
        for profile in resource_requirement.resource_requirement_profiles
        for evidence_ref in profile.evidence_refs
    )
    return AdapterCapabilityRequirement(
        adapter_key=adapter_key,
        capability=APPROVED_ADAPTER_CAPABILITY,
        execution_requirement=AdapterCapabilityExecutionRequirement(
            operation=APPROVED_EXECUTION_REQUIREMENT["operation"],
            target_type=APPROVED_EXECUTION_REQUIREMENT["target_type"],
            collection_mode=APPROVED_EXECUTION_REQUIREMENT["collection_mode"],
        ),
        resource_requirement=resource_requirement,
        evidence=AdapterCapabilityRequirementEvidence(
            resource_profile_evidence_refs=resource_profile_evidence_refs,
            capability_requirement_evidence_refs=(
                "fr-0024:reference-adapter-migration:xhs-douyin-content-detail",
            ),
        ),
        lifecycle=AdapterCapabilityLifecycleExpectation(
            requires_core_resource_bundle=True,
            resource_profiles_drive_admission=True,
            uses_existing_disposition_hint=True,
        ),
        observability=AdapterCapabilityObservabilityExpectation(
            requirement_id=(
                f"{adapter_key}:{APPROVED_ADAPTER_CAPABILITY}:"
                f"{APPROVED_EXECUTION_REQUIREMENT['operation']}:"
                f"{APPROVED_EXECUTION_REQUIREMENT['target_type']}:"
                f"{APPROVED_EXECUTION_REQUIREMENT['collection_mode']}"
            ),
            profile_keys=profile_keys,
            proof_refs=resource_profile_evidence_refs,
            admission_outcome_fields=REQUIRED_ADMISSION_OUTCOME_FIELDS,
        ),
        fail_closed=True,
    )


def validate_adapter_capability_requirement(
    input_value: AdapterCapabilityRequirementValidationInput | AdapterCapabilityRequirement | Mapping[str, Any],
) -> AdapterCapabilityRequirementValidationResult:
    validation_input = _normalize_validation_input(input_value)
    try:
        requirement = _normalize_requirement(validation_input.requirement)
        _validate_requirement_contract(requirement)
        match_result = match_resource_capabilities(
            ResourceCapabilityMatcherInput(
                task_id=_requirement_id(requirement),
                adapter_key=requirement.adapter_key,
                capability=requirement.capability,
                requirement_declaration=requirement.resource_requirement,
                available_resource_capabilities=validation_input.available_resource_capabilities,
            )
        )
    except AdapterCapabilityRequirementContractError as error:
        return AdapterCapabilityRequirementValidationResult(
            adapter_key=_best_effort_string(validation_input.requirement, "adapter_key"),
            capability=_best_effort_string(validation_input.requirement, "capability"),
            status=ADAPTER_REQUIREMENT_STATUS_INVALID,
            failure_category="runtime_contract",
            error_code=error.code,
            message=error.message,
            details=error.details,
        )
    except ResourceCapabilityMatcherContractError as error:
        return AdapterCapabilityRequirementValidationResult(
            adapter_key=_best_effort_string(validation_input.requirement, "adapter_key"),
            capability=_best_effort_string(validation_input.requirement, "capability"),
            status=ADAPTER_REQUIREMENT_STATUS_INVALID,
            failure_category="runtime_contract",
            error_code=ADAPTER_REQUIREMENT_ERROR_INVALID_RESOURCE_REQUIREMENT,
            message=error.message,
            details=error.details,
        )

    if match_result.match_status == MATCH_STATUS_UNMATCHED:
        return AdapterCapabilityRequirementValidationResult(
            adapter_key=requirement.adapter_key,
            capability=requirement.capability,
            status=ADAPTER_REQUIREMENT_STATUS_UNMATCHED,
            details={
                "match_status": MATCH_STATUS_UNMATCHED,
                "requirement_id": _requirement_id(requirement),
            },
        )
    if match_result.match_status != MATCH_STATUS_MATCHED:
        return AdapterCapabilityRequirementValidationResult(
            adapter_key=requirement.adapter_key,
            capability=requirement.capability,
            status=ADAPTER_REQUIREMENT_STATUS_INVALID,
            failure_category="runtime_contract",
            error_code=ADAPTER_REQUIREMENT_ERROR_INVALID_RESOURCE_REQUIREMENT,
            message="resource matcher returned an unsupported match status",
            details={"match_status": match_result.match_status},
        )
    return AdapterCapabilityRequirementValidationResult(
        adapter_key=requirement.adapter_key,
        capability=requirement.capability,
        status=ADAPTER_REQUIREMENT_STATUS_DECLARED,
        details={
            "match_status": MATCH_STATUS_MATCHED,
            "requirement_id": _requirement_id(requirement),
        },
    )


def _normalize_validation_input(
    input_value: AdapterCapabilityRequirementValidationInput | AdapterCapabilityRequirement | Mapping[str, Any],
) -> AdapterCapabilityRequirementValidationInput:
    if type(input_value) is AdapterCapabilityRequirementValidationInput:
        available_capabilities = _normalize_string_tuple(
            input_value.available_resource_capabilities,
            field_name="available_resource_capabilities",
            allow_empty=True,
        )
        return AdapterCapabilityRequirementValidationInput(
            requirement=input_value.requirement,
            available_resource_capabilities=available_capabilities,
        )
    return AdapterCapabilityRequirementValidationInput(requirement=input_value)


def _normalize_requirement(raw_value: AdapterCapabilityRequirement | Mapping[str, Any]) -> AdapterCapabilityRequirement:
    if type(raw_value) is AdapterCapabilityRequirement:
        adapter_key = _require_non_empty_string(raw_value.adapter_key, field_name="adapter_key")
        capability = _require_non_empty_string(raw_value.capability, field_name="capability")
        execution_requirement = _normalize_execution_requirement(raw_value.execution_requirement)
        evidence = _normalize_evidence(raw_value.evidence)
        lifecycle = _normalize_lifecycle(raw_value.lifecycle)
        observability = _normalize_observability(raw_value.observability)
        fail_closed = raw_value.fail_closed
        if type(fail_closed) is not bool:
            raise AdapterCapabilityRequirementContractError(
                ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
                "AdapterCapabilityRequirement.fail_closed must be a boolean",
                details={"actual_type": type(fail_closed).__name__},
            )
        _validate_top_level_slice(
            capability=capability,
            execution_requirement=execution_requirement,
            fail_closed=fail_closed,
        )
        resource_requirement = _normalize_resource_requirement(
            raw_value.resource_requirement,
            adapter_key=adapter_key,
            capability=capability,
        )
        return AdapterCapabilityRequirement(
            adapter_key=adapter_key,
            capability=capability,
            execution_requirement=execution_requirement,
            resource_requirement=resource_requirement,
            evidence=evidence,
            lifecycle=lifecycle,
            observability=observability,
            fail_closed=fail_closed,
        )
    if not isinstance(raw_value, Mapping):
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            "AdapterCapabilityRequirement carrier must be a mapping or canonical dataclass",
            details={"actual_type": type(raw_value).__name__},
        )

    raw_keys = _require_string_keys(raw_value, carrier_name="AdapterCapabilityRequirement")
    forbidden_fields = _find_forbidden_fields(raw_value)
    if forbidden_fields:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            "AdapterCapabilityRequirement must not contain provider, priority, fallback, or decision fields",
            details={"forbidden_fields": forbidden_fields},
        )
    _require_exact_fields(
        raw_keys,
        required_fields=REQUIRED_REQUIREMENT_FIELDS,
        carrier_name="AdapterCapabilityRequirement",
    )

    adapter_key = _require_non_empty_string(raw_value["adapter_key"], field_name="adapter_key")
    capability = _require_non_empty_string(raw_value["capability"], field_name="capability")
    execution_requirement = _normalize_execution_requirement(raw_value["execution_requirement"])
    evidence = _normalize_evidence(raw_value["evidence"])
    lifecycle = _normalize_lifecycle(raw_value["lifecycle"])
    observability = _normalize_observability(raw_value["observability"])
    fail_closed = raw_value["fail_closed"]
    if type(fail_closed) is not bool:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            "AdapterCapabilityRequirement.fail_closed must be a boolean",
            details={"actual_type": type(fail_closed).__name__},
        )
    _validate_top_level_slice(
        capability=capability,
        execution_requirement=execution_requirement,
        fail_closed=fail_closed,
    )
    resource_requirement = _normalize_resource_requirement(
        raw_value["resource_requirement"],
        adapter_key=adapter_key,
        capability=capability,
    )

    return AdapterCapabilityRequirement(
        adapter_key=adapter_key,
        capability=capability,
        execution_requirement=execution_requirement,
        resource_requirement=resource_requirement,
        evidence=evidence,
        lifecycle=lifecycle,
        observability=observability,
        fail_closed=fail_closed,
    )


def _normalize_execution_requirement(raw_value: Any) -> AdapterCapabilityExecutionRequirement:
    if type(raw_value) is AdapterCapabilityExecutionRequirement:
        return AdapterCapabilityExecutionRequirement(
            operation=_require_non_empty_string(raw_value.operation, field_name="execution_requirement.operation"),
            target_type=_require_non_empty_string(raw_value.target_type, field_name="execution_requirement.target_type"),
            collection_mode=_require_non_empty_string(
                raw_value.collection_mode,
                field_name="execution_requirement.collection_mode",
            ),
        )
    if not isinstance(raw_value, Mapping):
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            "execution_requirement must be a mapping or canonical dataclass",
            details={"actual_type": type(raw_value).__name__},
        )
    raw_keys = _require_string_keys(raw_value, carrier_name="execution_requirement")
    _require_exact_fields(
        raw_keys,
        required_fields=EXECUTION_REQUIREMENT_FIELDS,
        carrier_name="execution_requirement",
    )
    return AdapterCapabilityExecutionRequirement(
        operation=_require_non_empty_string(raw_value["operation"], field_name="execution_requirement.operation"),
        target_type=_require_non_empty_string(raw_value["target_type"], field_name="execution_requirement.target_type"),
        collection_mode=_require_non_empty_string(
            raw_value["collection_mode"],
            field_name="execution_requirement.collection_mode",
        ),
    )


def _normalize_resource_requirement(
    raw_value: Any,
    *,
    adapter_key: str,
    capability: str,
) -> AdapterResourceRequirementDeclarationV2:
    try:
        registry = AdapterRegistry.from_mapping(
            {
                adapter_key: _RequirementValidationAdapter(
                    supported_capability=capability,
                    resource_requirement=raw_value,
                )
            }
        )
    except RegistryError as error:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_RESOURCE_REQUIREMENT,
            "resource_requirement must satisfy FR-0027 AdapterResourceRequirementDeclarationV2",
            details={"registry_error_code": error.code, **error.details},
        ) from error
    resource_requirement = registry.lookup_resource_requirement(adapter_key, capability)
    if type(resource_requirement) is not AdapterResourceRequirementDeclarationV2:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_RESOURCE_REQUIREMENT,
            "resource_requirement must use AdapterResourceRequirementDeclarationV2",
            details={"actual_type": type(resource_requirement).__name__},
        )
    return resource_requirement


def _normalize_evidence(raw_value: Any) -> AdapterCapabilityRequirementEvidence:
    if type(raw_value) is AdapterCapabilityRequirementEvidence:
        capability_requirement_evidence_refs = _normalize_string_tuple(
            raw_value.capability_requirement_evidence_refs,
            field_name="evidence.capability_requirement_evidence_refs",
            allow_empty=False,
        )
        _validate_capability_requirement_evidence_refs(capability_requirement_evidence_refs)
        return AdapterCapabilityRequirementEvidence(
            resource_profile_evidence_refs=_normalize_string_tuple(
                raw_value.resource_profile_evidence_refs,
                field_name="evidence.resource_profile_evidence_refs",
                allow_empty=False,
            ),
            capability_requirement_evidence_refs=capability_requirement_evidence_refs,
        )
    if not isinstance(raw_value, Mapping):
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            "evidence must be a mapping or canonical dataclass",
            details={"actual_type": type(raw_value).__name__},
        )
    raw_keys = _require_string_keys(raw_value, carrier_name="evidence")
    _require_exact_fields(raw_keys, required_fields=EVIDENCE_FIELDS, carrier_name="evidence")
    capability_requirement_evidence_refs = _normalize_string_tuple(
        raw_value["capability_requirement_evidence_refs"],
        field_name="evidence.capability_requirement_evidence_refs",
        allow_empty=False,
    )
    _validate_capability_requirement_evidence_refs(capability_requirement_evidence_refs)
    return AdapterCapabilityRequirementEvidence(
        resource_profile_evidence_refs=_normalize_string_tuple(
            raw_value["resource_profile_evidence_refs"],
            field_name="evidence.resource_profile_evidence_refs",
            allow_empty=False,
        ),
        capability_requirement_evidence_refs=capability_requirement_evidence_refs,
    )


def _normalize_lifecycle(raw_value: Any) -> AdapterCapabilityLifecycleExpectation:
    if type(raw_value) is AdapterCapabilityLifecycleExpectation:
        return AdapterCapabilityLifecycleExpectation(
            requires_core_resource_bundle=_require_bool(
                raw_value.requires_core_resource_bundle,
                field_name="lifecycle.requires_core_resource_bundle",
            ),
            resource_profiles_drive_admission=_require_bool(
                raw_value.resource_profiles_drive_admission,
                field_name="lifecycle.resource_profiles_drive_admission",
            ),
            uses_existing_disposition_hint=_require_bool(
                raw_value.uses_existing_disposition_hint,
                field_name="lifecycle.uses_existing_disposition_hint",
            ),
        )
    if not isinstance(raw_value, Mapping):
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            "lifecycle must be a mapping or canonical dataclass",
            details={"actual_type": type(raw_value).__name__},
        )
    raw_keys = _require_string_keys(raw_value, carrier_name="lifecycle")
    _require_exact_fields(raw_keys, required_fields=LIFECYCLE_FIELDS, carrier_name="lifecycle")
    return AdapterCapabilityLifecycleExpectation(
        requires_core_resource_bundle=_require_bool(
            raw_value["requires_core_resource_bundle"],
            field_name="lifecycle.requires_core_resource_bundle",
        ),
        resource_profiles_drive_admission=_require_bool(
            raw_value["resource_profiles_drive_admission"],
            field_name="lifecycle.resource_profiles_drive_admission",
        ),
        uses_existing_disposition_hint=_require_bool(
            raw_value["uses_existing_disposition_hint"],
            field_name="lifecycle.uses_existing_disposition_hint",
        ),
    )


def _normalize_observability(raw_value: Any) -> AdapterCapabilityObservabilityExpectation:
    if type(raw_value) is AdapterCapabilityObservabilityExpectation:
        return AdapterCapabilityObservabilityExpectation(
            requirement_id=_require_non_empty_string(
                raw_value.requirement_id,
                field_name="observability.requirement_id",
            ),
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
            admission_outcome_fields=_normalize_string_tuple(
                raw_value.admission_outcome_fields,
                field_name="observability.admission_outcome_fields",
                allow_empty=False,
            ),
        )
    if not isinstance(raw_value, Mapping):
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            "observability must be a mapping or canonical dataclass",
            details={"actual_type": type(raw_value).__name__},
        )
    raw_keys = _require_string_keys(raw_value, carrier_name="observability")
    _require_exact_fields(raw_keys, required_fields=OBSERVABILITY_FIELDS, carrier_name="observability")
    return AdapterCapabilityObservabilityExpectation(
        requirement_id=_require_non_empty_string(
            raw_value["requirement_id"],
            field_name="observability.requirement_id",
        ),
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
        admission_outcome_fields=_normalize_string_tuple(
            raw_value["admission_outcome_fields"],
            field_name="observability.admission_outcome_fields",
            allow_empty=False,
        ),
    )


def _validate_requirement_contract(requirement: AdapterCapabilityRequirement) -> None:
    _validate_top_level_slice(
        capability=requirement.capability,
        execution_requirement=requirement.execution_requirement,
        fail_closed=requirement.fail_closed,
    )
    if requirement.resource_requirement.adapter_key != requirement.adapter_key:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_RESOURCE_REQUIREMENT,
            "resource_requirement.adapter_key must match AdapterCapabilityRequirement.adapter_key",
            details={
                "adapter_key": requirement.adapter_key,
                "resource_requirement_adapter_key": requirement.resource_requirement.adapter_key,
            },
        )
    if requirement.resource_requirement.capability != requirement.capability:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_RESOURCE_REQUIREMENT,
            "resource_requirement.capability must match AdapterCapabilityRequirement.capability",
            details={
                "capability": requirement.capability,
                "resource_requirement_capability": requirement.resource_requirement.capability,
            },
        )

    resource_profile_evidence_refs = tuple(
        evidence_ref
        for profile in requirement.resource_requirement.resource_requirement_profiles
        for evidence_ref in profile.evidence_refs
    )
    if requirement.evidence.resource_profile_evidence_refs != resource_profile_evidence_refs:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_RESOURCE_REQUIREMENT,
            "evidence.resource_profile_evidence_refs must align with resource_requirement profile proofs",
            details={
                "expected_resource_profile_evidence_refs": resource_profile_evidence_refs,
                "actual_resource_profile_evidence_refs": requirement.evidence.resource_profile_evidence_refs,
            },
        )
    if not requirement.lifecycle.resource_profiles_drive_admission:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            "lifecycle.resource_profiles_drive_admission must be true",
        )

    profile_keys = tuple(
        profile.profile_key
        for profile in requirement.resource_requirement.resource_requirement_profiles
    )
    if requirement.observability.profile_keys != profile_keys:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            "observability.profile_keys must align with resource_requirement profile keys",
            details={
                "expected_profile_keys": profile_keys,
                "actual_profile_keys": requirement.observability.profile_keys,
            },
        )
    if requirement.observability.proof_refs != requirement.evidence.resource_profile_evidence_refs:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            "observability.proof_refs must align with evidence.resource_profile_evidence_refs",
            details={
                "expected_proof_refs": requirement.evidence.resource_profile_evidence_refs,
                "actual_proof_refs": requirement.observability.proof_refs,
            },
        )
    if requirement.observability.admission_outcome_fields != REQUIRED_ADMISSION_OUTCOME_FIELDS:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            "observability.admission_outcome_fields must stay frozen to approved public outcome fields",
            details={
                "expected_admission_outcome_fields": REQUIRED_ADMISSION_OUTCOME_FIELDS,
                "actual_admission_outcome_fields": requirement.observability.admission_outcome_fields,
            },
        )
    _reject_observability_leakage(requirement.observability)


def _validate_top_level_slice(
    *,
    capability: str,
    execution_requirement: AdapterCapabilityExecutionRequirement,
    fail_closed: bool,
) -> None:
    try:
        stable = stable_operation_entry(
            operation=execution_requirement.operation,
            target_type=execution_requirement.target_type,
            collection_mode=execution_requirement.collection_mode,
        )
    except Exception as error:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            "execution_requirement 必须命中 stable + runtime_delivery taxonomy slice",
            details={"reason": str(error), "actual_execution_requirement": dict(execution_requirement.__dict__)},
        )
    if not stable.runtime_delivery or capability != stable.capability_family:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            "AdapterCapabilityRequirement.capability 与 execution_requirement 必须共同命中 stable runtime slice",
            details={"capability": capability, "stable_capability_family": stable.capability_family},
        )
    if not fail_closed:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            "AdapterCapabilityRequirement.fail_closed must be true",
            details={"fail_closed": fail_closed},
        )


def _validate_capability_requirement_evidence_refs(evidence_refs: tuple[str, ...]) -> None:
    unsupported_refs = tuple(
        evidence_ref
        for evidence_ref in evidence_refs
        if not _is_capability_requirement_evidence_ref(evidence_ref)
    )
    if unsupported_refs:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            "evidence.capability_requirement_evidence_refs must point to FR-0024 requirement evidence",
            details={
                "unsupported_capability_requirement_evidence_refs": unsupported_refs,
                "allowed_capability_requirement_evidence_ref_prefixes": CAPABILITY_REQUIREMENT_EVIDENCE_REF_PREFIXES,
            },
        )


def _is_capability_requirement_evidence_ref(evidence_ref: str) -> bool:
    for prefix in CAPABILITY_REQUIREMENT_EVIDENCE_REF_PREFIXES:
        if evidence_ref.startswith(prefix) and evidence_ref != prefix:
            return True
    return False


def _reject_observability_leakage(observability: AdapterCapabilityObservabilityExpectation) -> None:
    inspected_values = (
        observability.requirement_id,
        *observability.profile_keys,
        *observability.proof_refs,
        *observability.admission_outcome_fields,
    )
    leaked_values = tuple(
        value
        for value in inspected_values
        if _contains_forbidden_observability_token(value)
    )
    if leaked_values:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            "observability must not expose provider, selector, fallback, browser, or transport fields",
            details={"leaked_values": leaked_values},
        )


def _contains_forbidden_observability_token(value: str) -> bool:
    normalized = value.lower().replace("-", "_")
    return any(token in normalized for token in FORBIDDEN_OBSERVABILITY_TOKENS)


def _require_exact_fields(
    actual_fields: frozenset[str],
    *,
    required_fields: frozenset[str],
    carrier_name: str,
) -> None:
    missing_fields = tuple(sorted(required_fields - actual_fields))
    extra_fields = tuple(sorted(actual_fields - required_fields))
    if missing_fields or extra_fields:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            f"{carrier_name} must keep the canonical field set",
            details={
                "missing_fields": missing_fields,
                "extra_fields": extra_fields,
            },
        )


def _require_string_keys(raw_value: Mapping[Any, Any], *, carrier_name: str) -> frozenset[str]:
    raw_keys = frozenset(raw_value)
    invalid_keys = tuple(sorted(str(key) for key in raw_keys if not isinstance(key, str)))
    if invalid_keys:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            f"{carrier_name} field names must be strings",
            details={"invalid_keys": invalid_keys},
        )
    return frozenset(key for key in raw_keys if isinstance(key, str))


def _find_forbidden_fields(raw_value: Any) -> tuple[str, ...]:
    found: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, nested_value in value.items():
                if isinstance(key, str) and _contains_forbidden_requirement_field_token(key):
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


def _contains_forbidden_requirement_field_token(field_name: str) -> bool:
    normalized = _normalize_field_name(field_name)
    return any(
        normalized == token
        or normalized.startswith(f"{token}_")
        or normalized.endswith(f"_{token}")
        or f"_{token}_" in normalized
        for token in FORBIDDEN_REQUIREMENT_FIELDS
    )


def _normalize_field_name(field_name: str) -> str:
    with_word_boundaries = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", field_name)
    with_word_boundaries = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", with_word_boundaries)
    return re.sub(r"[^a-z0-9]+", "_", with_word_boundaries.lower()).strip("_")


def _require_non_empty_string(raw_value: Any, *, field_name: str) -> str:
    if not isinstance(raw_value, str) or not raw_value:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            f"{field_name} must be a non-empty string",
            details={"field_name": field_name, "actual_type": type(raw_value).__name__},
        )
    return raw_value


def _require_bool(raw_value: Any, *, field_name: str) -> bool:
    if type(raw_value) is not bool:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            f"{field_name} must be a boolean",
            details={"field_name": field_name, "actual_type": type(raw_value).__name__},
        )
    return raw_value


def _normalize_string_tuple(raw_values: Any, *, field_name: str, allow_empty: bool) -> tuple[str, ...]:
    if raw_values is None:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            f"{field_name} must be a deduplicated string collection",
            details={"actual_type": "NoneType"},
        )
    if isinstance(raw_values, (str, bytes)):
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            f"{field_name} must be a deduplicated string collection",
            details={"actual_type": type(raw_values).__name__},
        )
    if isinstance(raw_values, Mapping):
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            f"{field_name} must be a string array, not a mapping",
            details={"actual_type": type(raw_values).__name__},
        )
    try:
        iterator: Iterable[Any] = iter(raw_values)
    except TypeError as error:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            f"{field_name} must be a deduplicated string collection",
            details={"actual_type": type(raw_values).__name__},
        ) from error

    values: list[str] = []
    seen: set[str] = set()
    for raw_value in iterator:
        if not isinstance(raw_value, str) or not raw_value:
            raise AdapterCapabilityRequirementContractError(
                ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
                f"{field_name} values must be non-empty strings",
                details={"invalid_value": raw_value},
            )
        if raw_value in seen:
            raise AdapterCapabilityRequirementContractError(
                ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
                f"{field_name} must not contain duplicate values",
                details={"duplicate_value": raw_value},
            )
        seen.add(raw_value)
        values.append(raw_value)
    if not allow_empty and not values:
        raise AdapterCapabilityRequirementContractError(
            ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
            f"{field_name} must not be empty",
        )
    return tuple(values)


def _requirement_id(requirement: AdapterCapabilityRequirement) -> str:
    return requirement.observability.requirement_id


def _best_effort_string(raw_value: Any, field_name: str) -> str | None:
    if isinstance(raw_value, Mapping):
        value = raw_value.get(field_name)
        return value if isinstance(value, str) else None
    value = getattr(raw_value, field_name, None)
    return value if isinstance(value, str) else None
