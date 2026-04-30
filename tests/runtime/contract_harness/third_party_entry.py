from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
import re
from typing import Any, Literal

from syvert.registry import AdapterResourceRequirementDeclarationV2, AdapterResourceRequirementProfile
from syvert.resource_capability_evidence import (
    approved_shared_resource_requirement_profile_evidence_entries,
    frozen_resource_requirement_profile_evidence_records,
)
from syvert.runtime import AdapterExecutionContext, AdapterTaskRequest, PlatformAdapterError
from tests.runtime.contract_harness.validation_tool import (
    ContractSampleDefinition,
    HarnessExecutionResult,
    validate_contract_sample,
)
from tests.runtime.resource_fixtures import build_managed_resource_bundle

ADAPTER_ONLY_CONTENT_DETAIL_PROFILE = "adapter_only_content_detail_v0_8"

_REQUIRED_MANIFEST_FIELDS = frozenset(
    {
        "adapter_key",
        "sdk_contract_id",
        "supported_capabilities",
        "supported_targets",
        "supported_collection_modes",
        "resource_requirement_declarations",
        "result_contract",
        "error_mapping",
        "fixture_refs",
        "contract_test_profile",
    }
)
_FORBIDDEN_MANIFEST_FIELDS = frozenset(
    {
        "compatibility_decision",
        "fallback",
        "marketplace",
        "priority",
        "provider_fallback",
        "provider_key",
        "provider_marketplace",
        "provider_offer",
        "provider_priority",
        "provider_product_allowlist",
        "provider_registry",
        "provider_score",
        "provider_selector",
        "score",
        "selector",
    }
)
_DECLARATION_V2_FIELD_NAMES = frozenset(
    {
        "adapter_key",
        "capability",
        "resource_requirement_profiles",
    }
)
_PROFILE_FIELD_NAMES = frozenset(
    {
        "profile_key",
        "resource_dependency_mode",
        "required_capabilities",
        "evidence_refs",
    }
)
_ALLOWED_ERROR_MAPPING_CATEGORIES = frozenset(
    {"invalid_input", "unsupported", "platform"}
)
_ALLOWED_RESOURCE_DEPENDENCY_MODES = frozenset({"none", "required"})
_RESERVED_RUNTIME_ENVELOPE_FIELDS = frozenset(
    {
        "adapter_key",
        "capability",
        "error",
        "status",
        "task_id",
    }
)
_APPROVED_PROFILE_PROOF_BY_REF = {
    entry.profile_ref: entry
    for entry in approved_shared_resource_requirement_profile_evidence_entries()
}
_APPROVED_PROFILE_PROOF_BY_REF.update(
    {
        entry.profile_ref: entry
        for entry in frozen_resource_requirement_profile_evidence_records()
        if entry.resource_dependency_mode == "none" and not entry.required_capabilities
    }
)
_FORBIDDEN_ADAPTER_KEY_FRAGMENTS = frozenset(
    {
        "account",
        "acct",
        "dev",
        "douyin",
        "env",
        "fallback",
        "marketplace",
        "priority",
        "prod",
        "provider",
        "route",
        "routing",
        "score",
        "selector",
        "staging",
        "xhs",
    }
)
_APPROVED_CONTRACT_CAPABILITIES = frozenset({"content_detail"})
_MISSING = object()


class ThirdPartyContractEntryError(ValueError):
    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})


@dataclass(frozen=True)
class ThirdPartyAdapterManifest:
    adapter_key: str
    sdk_contract_id: str
    supported_capabilities: tuple[str, ...]
    supported_targets: tuple[str, ...]
    supported_collection_modes: tuple[str, ...]
    resource_requirement_declarations: tuple[Any, ...]
    result_contract: Mapping[str, Any]
    error_mapping: Mapping[str, Any]
    fixture_refs: tuple[str, ...]
    contract_test_profile: str


@dataclass(frozen=True)
class AdapterContractFixture:
    fixture_id: str
    manifest_ref: str
    case_type: Literal["success", "error_mapping"]
    input: Mapping[str, Any]
    expected: Mapping[str, Any]


def run_third_party_adapter_contract_test(
    *,
    manifest: Mapping[str, Any],
    fixtures: Sequence[Mapping[str, Any]],
    adapter: Any,
) -> list[dict[str, Any]]:
    normalized_manifest = validate_third_party_adapter_manifest(manifest)
    normalized_fixtures = validate_third_party_adapter_fixtures(
        normalized_manifest,
        fixtures,
    )
    _validate_adapter_public_metadata(normalized_manifest, adapter)

    results: list[dict[str, Any]] = []
    for fixture in normalized_fixtures:
        result = _execute_and_validate_fixture(normalized_manifest, fixture, adapter)
        results.append(result)
    return results


def validate_third_party_adapter_manifest(manifest: Mapping[str, Any]) -> ThirdPartyAdapterManifest:
    if not isinstance(manifest, Mapping):
        raise ThirdPartyContractEntryError(
            "invalid_manifest_shape",
            "third-party adapter manifest must be a mapping",
            details={"actual_type": type(manifest).__name__},
        )
    raw_keys = {key for key in manifest}
    if any(not isinstance(key, str) for key in raw_keys):
        raise ThirdPartyContractEntryError(
            "invalid_manifest_shape",
            "third-party adapter manifest field names must be strings",
            details={"actual_keys": tuple(sorted(str(key) for key in raw_keys))},
        )

    forbidden_fields = tuple(sorted(raw_keys & _FORBIDDEN_MANIFEST_FIELDS))
    if forbidden_fields:
        raise ThirdPartyContractEntryError(
            "forbidden_adapter_manifest_fields",
            "third-party adapter manifest must not carry provider or compatibility fields",
            details={"forbidden_fields": forbidden_fields},
        )
    missing_fields = tuple(sorted(_REQUIRED_MANIFEST_FIELDS - raw_keys))
    extra_fields = tuple(sorted(raw_keys - _REQUIRED_MANIFEST_FIELDS))
    if missing_fields or extra_fields:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_shape",
            "third-party adapter manifest must keep the FR-0023 fixed field set",
            details={"missing_fields": missing_fields, "extra_fields": extra_fields},
        )

    adapter_key = _require_non_empty_string(
        manifest["adapter_key"],
        code="invalid_manifest_public_metadata",
        field="adapter_key",
    )
    _validate_adapter_key_boundary(adapter_key)
    sdk_contract_id = _require_non_empty_string(
        manifest["sdk_contract_id"],
        code="invalid_manifest_public_metadata",
        field="sdk_contract_id",
    )
    if "provider" in sdk_contract_id or "compatibility" in sdk_contract_id:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_public_metadata",
            "sdk_contract_id must describe the Adapter SDK/runtime contract only",
            details={"field": "sdk_contract_id", "value": sdk_contract_id},
        )

    normalized_manifest = ThirdPartyAdapterManifest(
        adapter_key=adapter_key,
        sdk_contract_id=sdk_contract_id,
        supported_capabilities=_require_non_empty_string_tuple(
            manifest["supported_capabilities"],
            field="supported_capabilities",
        ),
        supported_targets=_require_non_empty_string_tuple(
            manifest["supported_targets"],
            field="supported_targets",
        ),
        supported_collection_modes=_require_non_empty_string_tuple(
            manifest["supported_collection_modes"],
            field="supported_collection_modes",
        ),
        resource_requirement_declarations=_require_non_string_sequence(
            manifest["resource_requirement_declarations"],
            field="resource_requirement_declarations",
        ),
        result_contract=_require_mapping(manifest["result_contract"], field="result_contract"),
        error_mapping=_require_mapping(manifest["error_mapping"], field="error_mapping"),
        fixture_refs=_require_non_empty_string_tuple(
            manifest["fixture_refs"],
            field="fixture_refs",
        ),
        contract_test_profile=_require_non_empty_string(
            manifest["contract_test_profile"],
            code="invalid_manifest_public_metadata",
            field="contract_test_profile",
        ),
    )
    _validate_contract_test_profile(normalized_manifest.contract_test_profile)
    _validate_result_contract(normalized_manifest.result_contract)
    _validate_error_mapping(normalized_manifest.error_mapping)
    resource_declarations = _normalize_manifest_resource_declarations(normalized_manifest)
    normalized_manifest = replace(
        normalized_manifest,
        resource_requirement_declarations=resource_declarations,
    )
    _validate_manifest_capability_coverage(normalized_manifest)
    return normalized_manifest


def validate_third_party_adapter_fixtures(
    manifest: ThirdPartyAdapterManifest,
    fixtures: Sequence[Mapping[str, Any]],
) -> tuple[AdapterContractFixture, ...]:
    if isinstance(fixtures, (str, bytes)) or not isinstance(fixtures, Sequence):
        raise ThirdPartyContractEntryError(
            "invalid_fixture_collection",
            "third-party adapter contract fixtures must be a sequence",
            details={"actual_type": type(fixtures).__name__},
        )
    normalized = tuple(_normalize_fixture(manifest, fixture) for fixture in fixtures)
    fixture_index: dict[str, AdapterContractFixture] = {}
    for fixture in normalized:
        if fixture.fixture_id in fixture_index:
            raise ThirdPartyContractEntryError(
                "duplicate_fixture_id",
                "third-party adapter fixtures must not repeat fixture_id",
                details={"fixture_id": fixture.fixture_id},
            )
        fixture_index[fixture.fixture_id] = fixture

    missing_refs = tuple(ref for ref in manifest.fixture_refs if ref not in fixture_index)
    if missing_refs:
        raise ThirdPartyContractEntryError(
            "unresolvable_fixture_refs",
            "manifest fixture_refs must resolve to provided fixtures",
            details={"missing_refs": missing_refs},
        )
    unreferenced_fixtures = tuple(
        fixture.fixture_id for fixture in normalized if fixture.fixture_id not in manifest.fixture_refs
    )
    if unreferenced_fixtures:
        raise ThirdPartyContractEntryError(
            "unreferenced_fixtures",
            "provided fixtures must be explicitly listed in manifest fixture_refs",
            details={"unreferenced_fixtures": unreferenced_fixtures},
        )

    covered_case_types = frozenset(fixture.case_type for fixture in normalized)
    missing_case_types = tuple(sorted({"success", "error_mapping"} - covered_case_types))
    if missing_case_types:
        raise ThirdPartyContractEntryError(
            "missing_fixture_case_coverage",
            "third-party adapter fixtures must cover success and error_mapping cases",
            details={"missing_case_types": missing_case_types},
        )
    return normalized


def _normalize_manifest_resource_declarations(manifest: ThirdPartyAdapterManifest) -> tuple[Any, ...]:
    return _normalize_third_party_resource_requirement_declarations(
        manifest.resource_requirement_declarations,
        adapter_key=manifest.adapter_key,
        supported_capabilities=manifest.supported_capabilities,
        source="manifest",
    )


def _validate_manifest_capability_coverage(manifest: ThirdPartyAdapterManifest) -> None:
    unsupported_capabilities = tuple(
        sorted(set(manifest.supported_capabilities) - _APPROVED_CONTRACT_CAPABILITIES)
    )
    if unsupported_capabilities:
        raise ThirdPartyContractEntryError(
            "unsupported_manifest_capabilities",
            "third-party adapter manifest cannot approve capabilities outside the current FR-0023 slice",
            details={"adapter_key": manifest.adapter_key, "unsupported_capabilities": unsupported_capabilities},
        )
    declaration_capabilities = frozenset(
        declaration.capability
        for declaration in manifest.resource_requirement_declarations
    )
    missing_declarations = tuple(
        sorted(set(manifest.supported_capabilities) - declaration_capabilities)
    )
    if missing_declarations:
        raise ThirdPartyContractEntryError(
            "missing_resource_declaration_for_capability",
            "each manifest supported_capability must have resource_requirement_declarations coverage",
            details={"adapter_key": manifest.adapter_key, "missing_capabilities": missing_declarations},
        )


def _validate_adapter_public_metadata(manifest: ThirdPartyAdapterManifest, adapter: Any) -> None:
    _reject_forbidden_adapter_public_metadata(adapter, manifest.adapter_key)
    execute = _safe_get_adapter_attr(adapter, "execute")
    if not callable(execute):
        raise ThirdPartyContractEntryError(
            "invalid_adapter_public_metadata",
            "adapter public metadata must expose callable execute",
            details={"adapter_key": manifest.adapter_key},
        )
    actual_capabilities = _require_non_empty_string_tuple(
        _safe_get_adapter_attr(adapter, "supported_capabilities"),
        field="adapter.supported_capabilities",
    )
    actual_targets = _require_non_empty_string_tuple(
        _safe_get_adapter_attr(adapter, "supported_targets"),
        field="adapter.supported_targets",
    )
    actual_collection_modes = _require_non_empty_string_tuple(
        _safe_get_adapter_attr(adapter, "supported_collection_modes"),
        field="adapter.supported_collection_modes",
    )
    actual_resource_requirements = _normalize_third_party_resource_requirement_declarations(
        _safe_get_adapter_attr(adapter, "resource_requirement_declarations"),
        adapter_key=manifest.adapter_key,
        supported_capabilities=actual_capabilities,
        source="adapter",
    )
    mismatches: dict[str, Any] = {}
    if tuple(sorted(actual_capabilities)) != tuple(sorted(manifest.supported_capabilities)):
        mismatches["supported_capabilities"] = tuple(sorted(actual_capabilities))
    if tuple(sorted(actual_targets)) != tuple(sorted(manifest.supported_targets)):
        mismatches["supported_targets"] = tuple(sorted(actual_targets))
    if tuple(sorted(actual_collection_modes)) != tuple(sorted(manifest.supported_collection_modes)):
        mismatches["supported_collection_modes"] = tuple(sorted(actual_collection_modes))
    if _resource_requirement_declaration_signatures(
        actual_resource_requirements
    ) != _resource_requirement_declaration_signatures(manifest.resource_requirement_declarations):
        mismatches["resource_requirement_declarations"] = actual_resource_requirements
    _compare_adapter_public_metadata_attr(
        adapter,
        manifest,
        attr_name="adapter_key",
        expected=manifest.adapter_key,
        mismatches=mismatches,
    )
    _compare_adapter_public_metadata_attr(
        adapter,
        manifest,
        attr_name="sdk_contract_id",
        expected=manifest.sdk_contract_id,
        mismatches=mismatches,
    )
    _compare_adapter_public_metadata_attr(
        adapter,
        manifest,
        attr_name="result_contract",
        expected=manifest.result_contract,
        mismatches=mismatches,
    )
    _compare_adapter_public_metadata_attr(
        adapter,
        manifest,
        attr_name="error_mapping",
        expected=manifest.error_mapping,
        mismatches=mismatches,
    )
    _compare_adapter_public_metadata_attr(
        adapter,
        manifest,
        attr_name="fixture_refs",
        expected=manifest.fixture_refs,
        mismatches=mismatches,
    )
    _compare_adapter_public_metadata_attr(
        adapter,
        manifest,
        attr_name="contract_test_profile",
        expected=manifest.contract_test_profile,
        mismatches=mismatches,
    )
    if mismatches:
        raise ThirdPartyContractEntryError(
            "adapter_manifest_metadata_mismatch",
            "adapter public metadata must match the manifest before execution",
            details={"adapter_key": manifest.adapter_key, "mismatches": mismatches},
        )


def _validate_adapter_key_boundary(adapter_key: str) -> None:
    normalized_segments = frozenset(
        segment
        for segment in re.split(r"[-_.:]+", adapter_key.lower())
        if segment
    )
    forbidden_fragments = tuple(
        sorted(fragment for fragment in _FORBIDDEN_ADAPTER_KEY_FRAGMENTS if fragment in normalized_segments)
    )
    if forbidden_fragments:
        raise ThirdPartyContractEntryError(
            "invalid_adapter_key_boundary",
            "adapter_key must not carry provider, account, environment, or routing strategy semantics",
            details={"adapter_key": adapter_key, "forbidden_fragments": forbidden_fragments},
        )


def _reject_forbidden_adapter_public_metadata(adapter: Any, adapter_key: str) -> None:
    exposed_fields: list[str] = []
    for field in sorted(_FORBIDDEN_MANIFEST_FIELDS):
        try:
            getattr(adapter, field)
        except AttributeError:
            continue
        except Exception:
            exposed_fields.append(field)
            continue
        exposed_fields.append(field)
    if exposed_fields:
        raise ThirdPartyContractEntryError(
            "forbidden_adapter_public_metadata_fields",
            "adapter public metadata must not expose provider or compatibility fields",
            details={"adapter_key": adapter_key, "forbidden_fields": tuple(exposed_fields)},
        )


def _normalize_third_party_resource_requirement_declarations(
    raw_declarations: Any,
    *,
    adapter_key: str,
    supported_capabilities: tuple[str, ...],
    source: str,
) -> tuple[AdapterResourceRequirementDeclarationV2, ...]:
    declarations = _require_non_string_sequence(
        raw_declarations,
        field=f"{source}.resource_requirement_declarations",
    )
    if not declarations:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_resource_requirement_declarations",
            "resource_requirement_declarations must not be empty",
            details={"adapter_key": adapter_key, "source": source},
        )

    normalized: list[AdapterResourceRequirementDeclarationV2] = []
    seen_capabilities: set[str] = set()
    for declaration in declarations:
        normalized_declaration = _normalize_third_party_resource_requirement_declaration(
            declaration,
            adapter_key=adapter_key,
            source=source,
        )
        if normalized_declaration.capability in seen_capabilities:
            raise ThirdPartyContractEntryError(
                "invalid_manifest_resource_requirement_declarations",
                "resource_requirement_declarations must not repeat capability",
                details={
                    "adapter_key": adapter_key,
                    "capability": normalized_declaration.capability,
                    "source": source,
                },
            )
        seen_capabilities.add(normalized_declaration.capability)
        normalized.append(normalized_declaration)
    unexpected_capabilities = tuple(sorted(seen_capabilities - set(supported_capabilities)))
    if unexpected_capabilities:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_resource_requirement_declarations",
            "resource_requirement_declarations can only cover supported capabilities",
            details={
                "adapter_key": adapter_key,
                "unexpected_capabilities": unexpected_capabilities,
                "source": source,
            },
        )
    return tuple(normalized)


def _normalize_third_party_resource_requirement_declaration(
    declaration: Any,
    *,
    adapter_key: str,
    source: str,
) -> AdapterResourceRequirementDeclarationV2:
    if isinstance(declaration, AdapterResourceRequirementDeclarationV2):
        raw_adapter_key = declaration.adapter_key
        raw_capability = declaration.capability
        raw_profiles = declaration.resource_requirement_profiles
    elif isinstance(declaration, Mapping):
        raw_keys = {key for key in declaration}
        _reject_forbidden_resource_requirement_fields(raw_keys, adapter_key=adapter_key, source=source)
        missing_fields = tuple(sorted(_DECLARATION_V2_FIELD_NAMES - raw_keys))
        extra_fields = tuple(sorted(raw_keys - _DECLARATION_V2_FIELD_NAMES))
        if missing_fields or extra_fields:
            raise ThirdPartyContractEntryError(
                "invalid_manifest_resource_requirement_declarations",
                "third-party resource declaration must use the FR-0027 V2 field set",
                details={
                    "adapter_key": adapter_key,
                    "missing_fields": missing_fields,
                    "extra_fields": extra_fields,
                    "source": source,
                },
            )
        raw_adapter_key = declaration["adapter_key"]
        raw_capability = declaration["capability"]
        raw_profiles = declaration["resource_requirement_profiles"]
    else:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_resource_requirement_declarations",
            "resource_requirement_declarations must contain V2 mappings or carriers",
            details={"adapter_key": adapter_key, "actual_type": type(declaration).__name__, "source": source},
        )

    declaration_adapter_key = _require_non_empty_string(
        raw_adapter_key,
        code="invalid_manifest_resource_requirement_declarations",
        field=f"{source}.resource_requirement_declarations.adapter_key",
    )
    if declaration_adapter_key != adapter_key:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_resource_requirement_declarations",
            "resource declaration adapter_key must match manifest adapter_key",
            details={"adapter_key": adapter_key, "declaration_adapter_key": declaration_adapter_key, "source": source},
        )
    capability = _require_non_empty_string(
        raw_capability,
        code="invalid_manifest_resource_requirement_declarations",
        field=f"{source}.resource_requirement_declarations.capability",
    )
    profiles = _normalize_third_party_resource_requirement_profiles(
        raw_profiles,
        adapter_key=adapter_key,
        capability=capability,
        source=source,
    )
    return AdapterResourceRequirementDeclarationV2(
        adapter_key=adapter_key,
        capability=capability,
        resource_requirement_profiles=profiles,
    )


def _normalize_third_party_resource_requirement_profiles(
    raw_profiles: Any,
    *,
    adapter_key: str,
    capability: str,
    source: str,
) -> tuple[AdapterResourceRequirementProfile, ...]:
    profiles = _require_non_string_sequence(
        raw_profiles,
        field=f"{source}.resource_requirement_profiles",
    )
    if not profiles:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_resource_requirement_declarations",
            "resource_requirement_profiles must not be empty",
            details={"adapter_key": adapter_key, "capability": capability, "source": source},
        )

    normalized: list[AdapterResourceRequirementProfile] = []
    seen_profile_keys: set[str] = set()
    seen_tuples: set[tuple[str, tuple[str, ...]]] = set()
    for profile in profiles:
        normalized_profile = _normalize_third_party_resource_requirement_profile(
            profile,
            adapter_key=adapter_key,
            capability=capability,
            source=source,
        )
        if normalized_profile.profile_key in seen_profile_keys:
            raise ThirdPartyContractEntryError(
                "invalid_manifest_resource_requirement_declarations",
                "resource_requirement_profiles must not repeat profile_key",
                details={
                    "adapter_key": adapter_key,
                    "capability": capability,
                    "profile_key": normalized_profile.profile_key,
                    "source": source,
                },
            )
        semantic_tuple = (
            normalized_profile.resource_dependency_mode,
            normalized_profile.required_capabilities,
        )
        if semantic_tuple in seen_tuples:
            raise ThirdPartyContractEntryError(
                "invalid_manifest_resource_requirement_declarations",
                "resource_requirement_profiles must not repeat semantic tuples",
                details={
                    "adapter_key": adapter_key,
                    "capability": capability,
                    "profile_key": normalized_profile.profile_key,
                    "source": source,
                },
            )
        seen_profile_keys.add(normalized_profile.profile_key)
        seen_tuples.add(semantic_tuple)
        normalized.append(normalized_profile)
    return tuple(normalized)


def _normalize_third_party_resource_requirement_profile(
    profile: Any,
    *,
    adapter_key: str,
    capability: str,
    source: str,
) -> AdapterResourceRequirementProfile:
    if isinstance(profile, AdapterResourceRequirementProfile):
        raw_profile_key = profile.profile_key
        raw_dependency_mode = profile.resource_dependency_mode
        raw_required_capabilities = profile.required_capabilities
        raw_evidence_refs = profile.evidence_refs
    elif isinstance(profile, Mapping):
        raw_keys = {key for key in profile}
        _reject_forbidden_resource_requirement_fields(raw_keys, adapter_key=adapter_key, source=source)
        missing_fields = tuple(sorted(_PROFILE_FIELD_NAMES - raw_keys))
        extra_fields = tuple(sorted(raw_keys - _PROFILE_FIELD_NAMES))
        if missing_fields or extra_fields:
            raise ThirdPartyContractEntryError(
                "invalid_manifest_resource_requirement_declarations",
                "third-party resource profile must use the FR-0027 profile field set",
                details={
                    "adapter_key": adapter_key,
                    "capability": capability,
                    "missing_fields": missing_fields,
                    "extra_fields": extra_fields,
                    "source": source,
                },
            )
        raw_profile_key = profile["profile_key"]
        raw_dependency_mode = profile["resource_dependency_mode"]
        raw_required_capabilities = profile["required_capabilities"]
        raw_evidence_refs = profile["evidence_refs"]
    else:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_resource_requirement_declarations",
            "resource_requirement_profiles must contain mappings or carriers",
            details={"adapter_key": adapter_key, "capability": capability, "actual_type": type(profile).__name__},
        )

    profile_key = _require_non_empty_string(
        raw_profile_key,
        code="invalid_manifest_resource_requirement_declarations",
        field=f"{source}.resource_requirement_profiles.profile_key",
    )
    resource_dependency_mode = _require_non_empty_string(
        raw_dependency_mode,
        code="invalid_manifest_resource_requirement_declarations",
        field=f"{source}.resource_requirement_profiles.resource_dependency_mode",
    )
    if resource_dependency_mode not in _ALLOWED_RESOURCE_DEPENDENCY_MODES:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_resource_requirement_declarations",
            "resource_dependency_mode must be none or required",
            details={
                "adapter_key": adapter_key,
                "capability": capability,
                "profile_key": profile_key,
                "resource_dependency_mode": resource_dependency_mode,
                "source": source,
            },
        )
    required_capabilities = _require_string_tuple(
        raw_required_capabilities,
        field=f"{source}.resource_requirement_profiles.required_capabilities",
        allow_empty=resource_dependency_mode == "none",
    )
    if resource_dependency_mode == "required" and not required_capabilities:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_resource_requirement_declarations",
            "required resource profiles must declare at least one capability",
            details={"adapter_key": adapter_key, "capability": capability, "profile_key": profile_key, "source": source},
        )
    evidence_refs = _require_non_empty_string_tuple(
        raw_evidence_refs,
        field=f"{source}.resource_requirement_profiles.evidence_refs",
    )
    if len(evidence_refs) != 1:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_resource_requirement_declarations",
            "third-party resource profile must bind exactly one FR-0027 profile proof",
            details={"adapter_key": adapter_key, "capability": capability, "profile_key": profile_key, "source": source},
        )
    proof = _APPROVED_PROFILE_PROOF_BY_REF.get(evidence_refs[0])
    if proof is None:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_resource_requirement_declarations",
            "resource profile evidence_refs must bind an approved FR-0027 profile proof",
            details={"adapter_key": adapter_key, "capability": capability, "profile_key": profile_key, "source": source},
        )
    if (
        proof.capability != capability
        or proof.resource_dependency_mode != resource_dependency_mode
        or proof.required_capabilities != required_capabilities
    ):
        raise ThirdPartyContractEntryError(
            "invalid_manifest_resource_requirement_declarations",
            "resource profile tuple must align with the FR-0027 profile proof",
            details={
                "adapter_key": adapter_key,
                "capability": capability,
                "profile_key": profile_key,
                "proof_profile_ref": proof.profile_ref,
                "source": source,
            },
        )
    return AdapterResourceRequirementProfile(
        profile_key=profile_key,
        resource_dependency_mode=resource_dependency_mode,
        required_capabilities=required_capabilities,
        evidence_refs=evidence_refs,
    )


def _reject_forbidden_resource_requirement_fields(
    raw_keys: set[Any],
    *,
    adapter_key: str,
    source: str,
) -> None:
    if any(not isinstance(key, str) for key in raw_keys):
        raise ThirdPartyContractEntryError(
            "invalid_manifest_resource_requirement_declarations",
            "resource requirement field names must be strings",
            details={"adapter_key": adapter_key, "actual_keys": tuple(sorted(str(key) for key in raw_keys))},
        )
    forbidden_fields = tuple(sorted(raw_keys & _FORBIDDEN_MANIFEST_FIELDS))
    if forbidden_fields:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_resource_requirement_declarations",
            "resource requirements must not carry provider or compatibility fields",
            details={"adapter_key": adapter_key, "forbidden_fields": forbidden_fields, "source": source},
        )


def _safe_get_adapter_attr(adapter: Any, attr_name: str) -> Any:
    try:
        return getattr(adapter, attr_name)
    except Exception:
        return _MISSING


def _compare_adapter_public_metadata_attr(
    adapter: Any,
    manifest: ThirdPartyAdapterManifest,
    *,
    attr_name: str,
    expected: Any,
    mismatches: dict[str, Any],
) -> None:
    try:
        actual = getattr(adapter, attr_name)
    except Exception:
        actual = _MISSING
    if attr_name == "fixture_refs" and actual is not _MISSING:
        try:
            actual = tuple(actual)
        except TypeError:
            pass
        if isinstance(actual, tuple) and tuple(sorted(actual)) == tuple(sorted(expected)):
            return
    if actual != expected:
        mismatches[attr_name] = {
            "expected": expected,
            "actual": "missing" if actual is _MISSING else actual,
            "adapter_key": manifest.adapter_key,
        }


def _resource_requirement_declaration_signatures(
    declarations: tuple[AdapterResourceRequirementDeclarationV2, ...],
) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        sorted(
            (
                declaration.adapter_key,
                declaration.capability,
                tuple(
                    sorted(
                        (
                            profile.profile_key,
                            profile.resource_dependency_mode,
                            profile.required_capabilities,
                            profile.evidence_refs,
                        )
                        for profile in declaration.resource_requirement_profiles
                    )
                ),
            )
            for declaration in declarations
        )
    )


def _execute_and_validate_fixture(
    manifest: ThirdPartyAdapterManifest,
    fixture: AdapterContractFixture,
    adapter: Any,
) -> dict[str, Any]:
    expected_outcome = "success" if fixture.case_type == "success" else "legal_failure"
    sample = ContractSampleDefinition(sample_id=fixture.fixture_id, expected_outcome=expected_outcome)
    task_id = f"task-{fixture.fixture_id}"
    fixture_input = _normalize_fixture_input(manifest, fixture)
    resource_profile = _resource_profile_for_fixture(manifest, fixture, fixture_input["resource_profile_key"])
    resource_bundle = build_managed_resource_bundle(
        adapter_key=manifest.adapter_key,
        task_id=task_id,
        capability=fixture_input["capability"],
        requested_slots=resource_profile.required_capabilities,
    )
    try:
        payload = adapter.execute(
            AdapterExecutionContext(
                request=AdapterTaskRequest(
                    capability=fixture_input["capability"],
                    target_type=fixture_input["target_type"],
                    target_value=fixture_input["target_value"],
                    collection_mode=fixture_input["collection_mode"],
                ),
                resource_bundle=resource_bundle,
            )
        )
        runtime_envelope = _build_success_runtime_envelope(
            task_id=task_id,
            adapter_key=manifest.adapter_key,
            capability=fixture_input["capability"],
            payload=payload,
        )
    except PlatformAdapterError as error:
        runtime_envelope = {
            "task_id": task_id,
            "adapter_key": manifest.adapter_key,
            "capability": fixture_input["capability"],
            "status": "failed",
            "error": {
                "category": error.category,
                "code": error.code,
                "message": error.message,
                "details": dict(error.details),
            },
        }
    except Exception as error:
        runtime_envelope = {
            "task_id": task_id,
            "adapter_key": manifest.adapter_key,
            "capability": fixture_input["capability"],
            "status": "failed",
            "error": {
                "category": "runtime_contract",
                "code": "adapter_execution_exception",
                "message": "adapter raised an unexpected exception during contract execution",
                "details": {"error_type": error.__class__.__name__},
            },
        }
    result = validate_contract_sample(sample, HarnessExecutionResult(runtime_envelope=runtime_envelope))
    result["observed_capability"] = runtime_envelope.get("capability")
    if result["verdict"] == "legal_failure":
        return _validate_error_mapping_observation(fixture, result)
    return result


def _build_success_runtime_envelope(
    *,
    task_id: str,
    adapter_key: str,
    capability: str,
    payload: Any,
) -> dict[str, Any]:
    envelope = {
        "task_id": task_id,
        "adapter_key": adapter_key,
        "capability": capability,
        "status": "success",
    }
    if isinstance(payload, Mapping):
        reserved_fields = tuple(sorted(set(payload) & _RESERVED_RUNTIME_ENVELOPE_FIELDS))
        if reserved_fields:
            return {
                **envelope,
                "status": "failed",
                "error": {
                    "category": "runtime_contract",
                    "code": "adapter_payload_reserved_runtime_fields",
                    "message": "adapter success payload must not carry runtime envelope context fields",
                    "details": {"reserved_fields": reserved_fields},
                },
            }
        return {**envelope, **payload}
    return {
        **envelope,
        "non_mapping_payload_type": type(payload).__name__,
    }


def _normalize_fixture(
    manifest: ThirdPartyAdapterManifest,
    fixture: Mapping[str, Any],
) -> AdapterContractFixture:
    if not isinstance(fixture, Mapping):
        raise ThirdPartyContractEntryError(
            "invalid_fixture_shape",
            "third-party adapter fixture must be a mapping",
            details={"actual_type": type(fixture).__name__},
        )
    raw_keys = {key for key in fixture}
    required_fields = frozenset({"fixture_id", "manifest_ref", "case_type", "input", "expected"})
    missing_fields = tuple(sorted(required_fields - raw_keys))
    extra_fields = tuple(sorted(raw_keys - required_fields))
    if missing_fields or extra_fields:
        raise ThirdPartyContractEntryError(
            "invalid_fixture_shape",
            "third-party adapter fixture must keep the fixed field set",
            details={"missing_fields": missing_fields, "extra_fields": extra_fields},
        )
    fixture_id = _require_non_empty_string(
        fixture["fixture_id"],
        code="invalid_fixture_shape",
        field="fixture_id",
    )
    manifest_ref = _require_non_empty_string(
        fixture["manifest_ref"],
        code="invalid_fixture_shape",
        field="manifest_ref",
    )
    if manifest_ref != manifest.adapter_key:
        raise ThirdPartyContractEntryError(
            "fixture_manifest_ref_mismatch",
            "fixture manifest_ref must match manifest adapter_key",
            details={"fixture_id": fixture_id, "manifest_ref": manifest_ref, "adapter_key": manifest.adapter_key},
        )
    case_type = _require_non_empty_string(
        fixture["case_type"],
        code="invalid_fixture_shape",
        field="case_type",
    )
    if case_type not in {"success", "error_mapping"}:
        raise ThirdPartyContractEntryError(
            "invalid_fixture_case_type",
            "fixture case_type must be success or error_mapping",
            details={"fixture_id": fixture_id, "case_type": case_type},
        )
    normalized = AdapterContractFixture(
        fixture_id=fixture_id,
        manifest_ref=manifest_ref,
        case_type=case_type,  # type: ignore[arg-type]
        input=_require_mapping(fixture["input"], field="input"),
        expected=_require_mapping(fixture["expected"], field="expected"),
    )
    _validate_fixture_expected_contract(manifest, normalized)
    return normalized


def _validate_contract_test_profile(profile: str) -> None:
    if profile != ADAPTER_ONLY_CONTENT_DETAIL_PROFILE:
        raise ThirdPartyContractEntryError(
            "unsupported_contract_test_profile",
            "contract_test_profile must be adapter_only_content_detail_v0_8",
            details={"contract_test_profile": profile},
        )


def _validate_result_contract(result_contract: Mapping[str, Any]) -> None:
    required_payload_fields = _require_non_empty_string_tuple(
        result_contract.get("success_payload_fields"),
        field="result_contract.success_payload_fields",
    )
    if required_payload_fields != ("raw", "normalized"):
        raise ThirdPartyContractEntryError(
            "invalid_result_contract",
            "result_contract must require raw and normalized success payload fields",
            details={"success_payload_fields": required_payload_fields},
        )
    normalized_owner = _require_non_empty_string(
        result_contract.get("normalized_owner"),
        code="invalid_result_contract",
        field="result_contract.normalized_owner",
    )
    if normalized_owner != "adapter":
        raise ThirdPartyContractEntryError(
            "invalid_result_contract",
            "normalized result must be adapter-owned",
            details={"normalized_owner": normalized_owner},
        )


def _validate_error_mapping(error_mapping: Mapping[str, Any]) -> None:
    if not error_mapping:
        raise ThirdPartyContractEntryError(
            "invalid_error_mapping",
            "error_mapping must not be empty",
        )
    for source_error, mapping in error_mapping.items():
        if not isinstance(source_error, str) or not source_error:
            raise ThirdPartyContractEntryError(
                "invalid_error_mapping",
                "error_mapping source keys must be non-empty strings",
                details={"source_error": source_error},
            )
        normalized_mapping = _require_mapping(mapping, field=f"error_mapping.{source_error}")
        category = _require_non_empty_string(
            normalized_mapping.get("category"),
            code="invalid_error_mapping",
            field=f"error_mapping.{source_error}.category",
        )
        if category not in _ALLOWED_ERROR_MAPPING_CATEGORIES:
            raise ThirdPartyContractEntryError(
                "invalid_error_mapping",
                "error_mapping category must reuse Syvert failed envelope categories",
                details={"source_error": source_error, "category": category},
            )
        _require_non_empty_string(
            normalized_mapping.get("code"),
            code="invalid_error_mapping",
            field=f"error_mapping.{source_error}.code",
        )
        _require_non_empty_string(
            normalized_mapping.get("message"),
            code="invalid_error_mapping",
            field=f"error_mapping.{source_error}.message",
        )


def _validate_fixture_expected_contract(
    manifest: ThirdPartyAdapterManifest,
    fixture: AdapterContractFixture,
) -> None:
    expected_status = _require_non_empty_string(
        fixture.expected.get("status"),
        code="invalid_fixture_expected_contract",
        field="expected.status",
    )
    if fixture.case_type == "success":
        if expected_status != "success":
            raise ThirdPartyContractEntryError(
                "invalid_fixture_expected_contract",
                "success fixture expected.status must be success",
                details={"fixture_id": fixture.fixture_id, "status": expected_status},
            )
        required_payload_fields = _require_non_empty_string_tuple(
            fixture.expected.get("required_payload_fields"),
            field="expected.required_payload_fields",
        )
        if required_payload_fields != ("raw", "normalized"):
            raise ThirdPartyContractEntryError(
                "invalid_fixture_expected_contract",
                "success fixture must require raw and normalized payload fields",
                details={"fixture_id": fixture.fixture_id, "required_payload_fields": required_payload_fields},
            )
        return

    if expected_status != "failed":
        raise ThirdPartyContractEntryError(
            "invalid_fixture_expected_contract",
            "error_mapping fixture expected.status must be failed",
            details={"fixture_id": fixture.fixture_id, "status": expected_status},
        )
    expected_error = _require_mapping(fixture.expected.get("error"), field="expected.error")
    source_error = _require_non_empty_string(
        expected_error.get("source_error"),
        code="invalid_fixture_expected_contract",
        field="expected.error.source_error",
    )
    category = _require_non_empty_string(
        expected_error.get("category"),
        code="invalid_fixture_expected_contract",
        field="expected.error.category",
    )
    code = _require_non_empty_string(
        expected_error.get("code"),
        code="invalid_fixture_expected_contract",
        field="expected.error.code",
    )
    if category not in _ALLOWED_ERROR_MAPPING_CATEGORIES:
        raise ThirdPartyContractEntryError(
            "invalid_fixture_expected_contract",
            "error_mapping fixture must expect an existing Syvert failed envelope category",
            details={"fixture_id": fixture.fixture_id, "category": category, "code": code},
        )
    manifest_error_mapping = manifest.error_mapping.get(source_error)
    if not isinstance(manifest_error_mapping, Mapping):
        raise ThirdPartyContractEntryError(
            "invalid_fixture_expected_contract",
            "error_mapping fixture source_error must exist in manifest error_mapping",
            details={"fixture_id": fixture.fixture_id, "source_error": source_error},
        )
    if (
        manifest_error_mapping.get("category") != category
        or manifest_error_mapping.get("code") != code
    ):
        raise ThirdPartyContractEntryError(
            "fixture_error_mapping_manifest_mismatch",
            "error_mapping fixture expected error must match manifest error_mapping",
            details={
                "fixture_id": fixture.fixture_id,
                "source_error": source_error,
                "manifest_category": manifest_error_mapping.get("category"),
                "manifest_code": manifest_error_mapping.get("code"),
                "fixture_category": category,
                "fixture_code": code,
            },
        )


def _validate_error_mapping_observation(
    fixture: AdapterContractFixture,
    result: dict[str, Any],
) -> dict[str, Any]:
    expected_error = _require_mapping(fixture.expected.get("error"), field="expected.error")
    observed_error = result.get("observed_error")
    if not isinstance(observed_error, Mapping):
        return {
            **result,
            "verdict": "contract_violation",
            "reason": {
                "code": "missing_observed_error_mapping",
                "message": "error_mapping fixture did not observe a failed envelope error object",
            },
        }
    expected_category = expected_error["category"]
    expected_code = expected_error["code"]
    if observed_error.get("category") != expected_category or observed_error.get("code") != expected_code:
        return {
            **result,
            "verdict": "contract_violation",
            "reason": {
                "code": "error_mapping_mismatch",
                "message": "observed failed envelope does not match fixture error_mapping expectation",
            },
        }
    return result


def _normalize_fixture_input(
    manifest: ThirdPartyAdapterManifest,
    fixture: AdapterContractFixture,
) -> dict[str, str]:
    input_mapping = fixture.input
    fixture_input = {
        "operation": _require_non_empty_string(
            input_mapping.get("operation"),
            code="invalid_fixture_input",
            field="input.operation",
        ),
        "capability": _require_non_empty_string(
            input_mapping.get("capability"),
            code="invalid_fixture_input",
            field="input.capability",
        ),
        "target_type": _require_non_empty_string(
            input_mapping.get("target_type"),
            code="invalid_fixture_input",
            field="input.target_type",
        ),
        "target_value": _require_non_empty_string(
            input_mapping.get("target_value"),
            code="invalid_fixture_input",
            field="input.target_value",
        ),
        "collection_mode": _require_non_empty_string(
            input_mapping.get("collection_mode"),
            code="invalid_fixture_input",
            field="input.collection_mode",
        ),
        "resource_profile_key": _require_non_empty_string(
            input_mapping.get("resource_profile_key"),
            code="invalid_fixture_input",
            field="input.resource_profile_key",
        ),
    }
    if fixture_input["capability"] not in manifest.supported_capabilities:
        raise ThirdPartyContractEntryError(
            "invalid_fixture_input_metadata",
            "fixture capability must be declared by manifest supported_capabilities",
            details={"fixture_id": fixture.fixture_id, "capability": fixture_input["capability"]},
        )
    if fixture_input["target_type"] not in manifest.supported_targets:
        raise ThirdPartyContractEntryError(
            "invalid_fixture_input_metadata",
            "fixture target_type must be declared by manifest supported_targets",
            details={"fixture_id": fixture.fixture_id, "target_type": fixture_input["target_type"]},
        )
    if fixture_input["collection_mode"] not in manifest.supported_collection_modes:
        raise ThirdPartyContractEntryError(
            "invalid_fixture_input_metadata",
            "fixture collection_mode must be declared by manifest supported_collection_modes",
            details={"fixture_id": fixture.fixture_id, "collection_mode": fixture_input["collection_mode"]},
        )
    return fixture_input


def _resource_profile_for_fixture(
    manifest: ThirdPartyAdapterManifest,
    fixture: AdapterContractFixture,
    profile_key: str,
) -> AdapterResourceRequirementProfile:
    for declaration in manifest.resource_requirement_declarations:
        if declaration.capability != fixture.input.get("capability"):
            continue
        for profile in declaration.resource_requirement_profiles:
            if profile.profile_key == profile_key:
                proof = _APPROVED_PROFILE_PROOF_BY_REF[profile.evidence_refs[0]]
                if (
                    proof.execution_path.operation != fixture.input.get("operation")
                    or proof.execution_path.target_type != fixture.input.get("target_type")
                    or proof.execution_path.collection_mode != fixture.input.get("collection_mode")
                ):
                    raise ThirdPartyContractEntryError(
                        "invalid_fixture_resource_profile",
                        "fixture input must align with the FR-0027 profile proof execution path",
                        details={"fixture_id": fixture.fixture_id, "resource_profile_key": profile_key},
                    )
                return profile
    raise ThirdPartyContractEntryError(
        "invalid_fixture_resource_profile",
        "fixture resource_profile_key must resolve to the manifest resource declaration for its capability",
        details={"fixture_id": fixture.fixture_id, "resource_profile_key": profile_key},
    )


def _require_mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ThirdPartyContractEntryError(
            "invalid_manifest_public_metadata",
            f"{field} must be a mapping",
            details={"field": field, "actual_type": type(value).__name__},
        )
    return value


def _require_non_empty_string(value: Any, *, code: str, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ThirdPartyContractEntryError(
            code,
            f"{field} must be a non-empty string",
            details={"field": field, "actual_type": type(value).__name__},
        )
    return value


def _require_non_string_sequence(value: Any, *, field: str) -> tuple[Any, ...]:
    if value is None or isinstance(value, (str, bytes, Mapping)):
        raise ThirdPartyContractEntryError(
            "invalid_manifest_public_metadata",
            f"{field} must be a non-string sequence",
            details={"field": field, "actual_type": type(value).__name__},
        )
    try:
        return tuple(value)
    except TypeError as error:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_public_metadata",
            f"{field} must be a non-string sequence",
            details={"field": field, "actual_type": type(value).__name__},
        ) from error


def _require_non_empty_string_tuple(value: Any, *, field: str) -> tuple[str, ...]:
    return _require_string_tuple(value, field=field, allow_empty=False)


def _require_string_tuple(value: Any, *, field: str, allow_empty: bool) -> tuple[str, ...]:
    values = _require_non_string_sequence(value, field=field)
    if not values and not allow_empty:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_public_metadata",
            f"{field} must not be empty",
            details={"field": field},
        )
    normalized: list[str] = []
    seen: set[str] = set()
    for item in values:
        if not isinstance(item, str) or not item:
            raise ThirdPartyContractEntryError(
                "invalid_manifest_public_metadata",
                f"{field} must contain only non-empty strings",
                details={"field": field, "actual_type": type(item).__name__},
            )
        if item in seen:
            raise ThirdPartyContractEntryError(
                "invalid_manifest_public_metadata",
                f"{field} must not contain duplicate strings",
                details={"field": field, "duplicate_value": item},
            )
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)
