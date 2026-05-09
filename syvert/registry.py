from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from syvert.resource_capability_evidence import (
    ApprovedSharedResourceRequirementProfileEvidenceEntry,
    approved_resource_capability_ids,
    approved_shared_resource_requirement_profile_evidence_entries,
)
from syvert.resource_capability_evidence import frozen_dual_reference_resource_capability_evidence_records


MISSING = object()
RESOURCE_DEPENDENCY_MODE_NONE = "none"
RESOURCE_DEPENDENCY_MODE_REQUIRED = "required"
_ALLOWED_RESOURCE_DEPENDENCY_MODES = frozenset(
    {
        RESOURCE_DEPENDENCY_MODE_NONE,
        RESOURCE_DEPENDENCY_MODE_REQUIRED,
    }
)
_DECLARATION_FIELD_NAMES = frozenset(
    {
        "adapter_key",
        "capability",
        "resource_dependency_mode",
        "required_capabilities",
        "evidence_refs",
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
_FORBIDDEN_RESOURCE_REQUIREMENT_KEYS = frozenset(
    {
        "preferred_capabilities",
        "optional_capabilities",
        "fallback",
        "priority",
        "provider_selection",
        "provider_key",
        "provider_priority",
        "fallback_order",
        "external_provider_ref",
        "resource_provider",
        "provider_capabilities",
        "native_provider",
        "playwright",
        "cdp",
        "chromium",
        "browser_provider",
        "sign_service",
        "preferred_profiles",
        "provider_offer",
    }
)
_FROZEN_REQUIRED_CAPABILITY_IDS = ("account", "proxy")
_REQUIRED_CAPABILITY_ORDER = _FROZEN_REQUIRED_CAPABILITY_IDS
_APPROVED_RESOURCE_CAPABILITY_IDS = approved_resource_capability_ids()
if _APPROVED_RESOURCE_CAPABILITY_IDS != frozenset(_FROZEN_REQUIRED_CAPABILITY_IDS):
    raise ValueError("FR-0013 required capability vocabulary must stay frozen to account and proxy")
_APPROVED_FROZEN_RESOURCE_CAPABILITY_RECORDS = tuple(
    record
    for record in frozen_dual_reference_resource_capability_evidence_records()
    if (
        record.candidate_abstract_capability in _APPROVED_RESOURCE_CAPABILITY_IDS
        and record.capability == "content_detail"
    )
)
_ALLOWED_RESOURCE_REQUIREMENT_CAPABILITIES = frozenset({"content_detail", "content_search", "content_list"})
_APPROVED_RESOURCE_REQUIREMENT_EVIDENCE_REFS = frozenset(
    evidence_ref
    for record in _APPROVED_FROZEN_RESOURCE_CAPABILITY_RECORDS
    for evidence_ref in record.evidence_refs
)
_FROZEN_RESOURCE_CAPABILITY_RECORD_INDEX = {
    (record.adapter_key, record.capability, record.candidate_abstract_capability): record
    for record in _APPROVED_FROZEN_RESOURCE_CAPABILITY_RECORDS
}


class RegistryError(Exception):
    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})


@dataclass(frozen=True)
class AdapterResourceRequirementDeclaration:
    adapter_key: str
    capability: str
    resource_dependency_mode: str
    required_capabilities: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class AdapterResourceRequirementProfile:
    profile_key: str
    resource_dependency_mode: str
    required_capabilities: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class AdapterResourceRequirementDeclarationV2:
    adapter_key: str
    capability: str
    resource_requirement_profiles: tuple[AdapterResourceRequirementProfile, ...]


AdapterResourceRequirementDeclarationCarrier = (
    AdapterResourceRequirementDeclaration | AdapterResourceRequirementDeclarationV2
)


@dataclass(frozen=True)
class AdapterDeclaration:
    adapter_key: str
    adapter: Any
    supported_capabilities: frozenset[str]
    supported_targets: frozenset[str]
    supported_collection_modes: frozenset[str]
    resource_requirement_declarations: tuple[
        AdapterResourceRequirementDeclaration | AdapterResourceRequirementDeclarationV2,
        ...
    ]


class AdapterRegistry:
    def __init__(self, entries: Mapping[str, AdapterDeclaration]) -> None:
        self._entries = dict(entries)

    @classmethod
    def from_mapping(cls, adapters: Mapping[str, Any]) -> AdapterRegistry:
        if not isinstance(adapters, Mapping):
            raise RegistryError(
                "invalid_adapter_registry",
                "adapters 必须是 mapping",
                details={"actual_type": type(adapters).__name__},
            )
        try:
            items = adapters.items()
        except Exception as error:
            raise RegistryError(
                "invalid_adapter_registry",
                "adapters 无法遍历",
                details={"error_type": error.__class__.__name__},
            ) from error

        entries: dict[str, AdapterDeclaration] = {}
        seen: set[str] = set()
        try:
            for adapter_key, adapter in items:
                if not isinstance(adapter_key, str) or not adapter_key:
                    raise RegistryError(
                        "invalid_adapter_registry",
                        "adapter_key 必须为非空字符串",
                        details={"adapter_key": adapter_key},
                    )
                if adapter_key in seen:
                    raise RegistryError(
                        "invalid_adapter_registry",
                        "adapter registry 存在重复 adapter_key",
                        details={"adapter_key": adapter_key},
                    )
                seen.add(adapter_key)
                declaration = _build_adapter_declaration(adapter_key, adapter)
                entries[adapter_key] = declaration
        except RegistryError:
            raise
        except Exception as error:
            raise RegistryError(
                "invalid_adapter_registry",
                "adapters 无法遍历",
                details={"error_type": error.__class__.__name__},
            ) from error

        return cls(entries)

    def lookup(self, adapter_key: str) -> AdapterDeclaration | None:
        return self._entries.get(adapter_key)

    def discover_capabilities(self, adapter_key: str) -> frozenset[str] | None:
        declaration = self.lookup(adapter_key)
        if declaration is None:
            return None
        return declaration.supported_capabilities

    def discover_targets(self, adapter_key: str) -> frozenset[str] | None:
        declaration = self.lookup(adapter_key)
        if declaration is None:
            return None
        return declaration.supported_targets

    def discover_collection_modes(self, adapter_key: str) -> frozenset[str] | None:
        declaration = self.lookup(adapter_key)
        if declaration is None:
            return None
        return declaration.supported_collection_modes

    def discover_resource_requirements(
        self,
        adapter_key: str,
    ) -> tuple[AdapterResourceRequirementDeclarationCarrier, ...] | None:
        declaration = self.lookup(adapter_key)
        if declaration is None:
            return None
        return declaration.resource_requirement_declarations

    def lookup_resource_requirement(
        self,
        adapter_key: str,
        capability: str,
    ) -> AdapterResourceRequirementDeclarationCarrier | None:
        declaration = self.lookup(adapter_key)
        if declaration is None:
            return None
        for resource_requirement in declaration.resource_requirement_declarations:
            if resource_requirement.capability == capability:
                return resource_requirement
        return None


def baseline_required_resource_requirement_declaration(
    *,
    adapter_key: str,
    capability: str,
) -> AdapterResourceRequirementDeclaration:
    required_capabilities = _REQUIRED_CAPABILITY_ORDER
    return AdapterResourceRequirementDeclaration(
        adapter_key=adapter_key,
        capability=capability,
        resource_dependency_mode=RESOURCE_DEPENDENCY_MODE_REQUIRED,
        required_capabilities=required_capabilities,
        evidence_refs=_canonical_required_evidence_refs(
            adapter_key=adapter_key,
            capability=capability,
            required_capabilities=required_capabilities,
        ),
    )


def baseline_multi_profile_resource_requirement_declaration(
    *,
    adapter_key: str,
    capability: str,
) -> AdapterResourceRequirementDeclarationV2:
    return AdapterResourceRequirementDeclarationV2(
        adapter_key=adapter_key,
        capability=capability,
        resource_requirement_profiles=(
            AdapterResourceRequirementProfile(
                profile_key="account_proxy",
                resource_dependency_mode=RESOURCE_DEPENDENCY_MODE_REQUIRED,
                required_capabilities=("account", "proxy"),
                evidence_refs=("fr-0027:profile:content-detail-by-url-hybrid:account-proxy",),
            ),
            AdapterResourceRequirementProfile(
                profile_key="account",
                resource_dependency_mode=RESOURCE_DEPENDENCY_MODE_REQUIRED,
                required_capabilities=("account",),
                evidence_refs=("fr-0027:profile:content-detail-by-url-hybrid:account",),
            ),
        ),
    )


def approved_resource_requirement_evidence_refs() -> frozenset[str]:
    return _APPROVED_RESOURCE_REQUIREMENT_EVIDENCE_REFS


def approved_resource_requirement_evidence_refs_for(
    *,
    adapter_key: str,
    capability: str,
) -> frozenset[str]:
    return frozenset(
        evidence_ref
        for record in _APPROVED_FROZEN_RESOURCE_CAPABILITY_RECORDS
        if record.adapter_key == adapter_key and record.capability == capability
        for evidence_ref in record.evidence_refs
    )


def _build_adapter_declaration(adapter_key: str, adapter: Any) -> AdapterDeclaration:
    _validate_adapter_execute(adapter_key, adapter)
    capabilities = _get_adapter_attribute(adapter, "supported_capabilities")
    targets = _get_adapter_attribute(adapter, "supported_targets")
    collection_modes = _get_adapter_attribute(adapter, "supported_collection_modes")
    resource_requirements = _get_adapter_attribute(adapter, "resource_requirement_declarations")

    supported_capabilities = _validate_supported_capabilities(capabilities)
    supported_targets = _validate_supported_targets(targets)
    supported_collection_modes = _validate_supported_collection_modes(collection_modes)
    resource_requirement_declarations = _validate_resource_requirement_declarations(
        adapter_key,
        resource_requirements,
        supported_capabilities=supported_capabilities,
    )

    return AdapterDeclaration(
        adapter_key=adapter_key,
        adapter=adapter,
        supported_capabilities=supported_capabilities,
        supported_targets=supported_targets,
        supported_collection_modes=supported_collection_modes,
        resource_requirement_declarations=resource_requirement_declarations,
    )


def _get_adapter_attribute(adapter: Any, name: str) -> Any:
    try:
        return getattr(adapter, name)
    except AttributeError:
        return MISSING
    except Exception:
        return MISSING


def _validate_adapter_execute(adapter_key: str, adapter: Any) -> None:
    execute = _get_adapter_attribute(adapter, "execute")
    if execute is MISSING:
        raise RegistryError(
            "invalid_adapter_declaration",
            "adapter 必须提供可调用的 execute",
            details={"adapter_key": adapter_key, "reason": "missing_execute"},
        )
    if not callable(execute):
        raise RegistryError(
            "invalid_adapter_declaration",
            "adapter 必须提供可调用的 execute",
            details={"adapter_key": adapter_key, "reason": "non_callable_execute"},
        )


def _validate_supported_capabilities(raw_capabilities: Any) -> frozenset[str]:
    return _validate_supported_axis(
        raw_capabilities,
        missing_code="invalid_adapter_capabilities",
        message="supported_capabilities 必须为字符串集合",
    )


def _validate_supported_targets(raw_targets: Any) -> frozenset[str]:
    return _validate_supported_axis(
        raw_targets,
        missing_code="invalid_adapter_targets",
        message="supported_targets 必须为字符串集合",
    )


def _validate_supported_collection_modes(raw_modes: Any) -> frozenset[str]:
    return _validate_supported_axis(
        raw_modes,
        missing_code="invalid_adapter_collection_modes",
        message="supported_collection_modes 必须为字符串集合",
    )


def _validate_resource_requirement_declarations(
    adapter_key: str,
    raw_declarations: Any,
    *,
    supported_capabilities: frozenset[str],
) -> tuple[AdapterResourceRequirementDeclarationCarrier, ...]:
    if raw_declarations is MISSING:
        return ()

    declarations = _validate_resource_requirement_declaration_collection(
        raw_declarations,
        missing_code="invalid_adapter_resource_requirements",
        message="resource_requirement_declarations 必须为 AdapterResourceRequirementDeclaration 集合",
    )
    validated: list[AdapterResourceRequirementDeclarationCarrier] = []
    seen_capabilities: set[str] = set()
    for declaration in declarations:
        validated_declaration = _validate_resource_requirement_declaration(
            adapter_key=adapter_key,
            declaration=declaration,
        )
        if validated_declaration.capability in seen_capabilities:
            raise RegistryError(
                "invalid_adapter_resource_requirements",
                "resource_requirement_declarations 不得为同一 capability 重复声明",
                details={
                    "adapter_key": adapter_key,
                    "capability": validated_declaration.capability,
                },
            )
        seen_capabilities.add(validated_declaration.capability)
        validated.append(validated_declaration)

    declared_capabilities = frozenset(declaration.capability for declaration in validated)
    unexpected_capabilities = tuple(sorted(declared_capabilities - supported_capabilities))
    if unexpected_capabilities:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "resource_requirement_declarations 只能声明 adapter 已支持的 capability",
            details={
                "adapter_key": adapter_key,
                "unexpected_capabilities": unexpected_capabilities,
            },
        )
    return tuple(validated)


def _validate_resource_requirement_declaration_collection(
    raw_values: Any,
    *,
    missing_code: str,
    message: str,
) -> tuple[AdapterResourceRequirementDeclarationCarrier, ...]:
    if raw_values is None:
        raise RegistryError(
            missing_code,
            message,
            details={"actual_type": "NoneType"},
        )
    if isinstance(raw_values, (str, bytes)):
        raise RegistryError(
            missing_code,
            message,
            details={"actual_type": type(raw_values).__name__},
        )
    try:
        iterator = iter(raw_values)
    except TypeError:
        raise RegistryError(
            missing_code,
            message,
            details={"actual_type": type(raw_values).__name__},
        )

    validated: list[AdapterResourceRequirementDeclarationCarrier] = []
    try:
        for value in iterator:
            validated.append(_normalize_resource_requirement_declaration_candidate(value))
    except RegistryError:
        raise
    except Exception as error:
        raise RegistryError(
            missing_code,
            message,
            details={"error_type": error.__class__.__name__},
        ) from error
    return tuple(validated)


def _normalize_resource_requirement_declaration_candidate(
    raw_value: Any,
) -> AdapterResourceRequirementDeclarationCarrier:
    if isinstance(raw_value, (AdapterResourceRequirementDeclaration, AdapterResourceRequirementDeclarationV2)):
        return raw_value
    if not isinstance(raw_value, Mapping):
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "resource_requirement_declarations 只能包含 canonical declaration carrier",
            details={"invalid_value_type": type(raw_value).__name__},
        )

    raw_keys = {key for key in raw_value}
    if any(not isinstance(key, str) for key in raw_keys):
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "AdapterResourceRequirementDeclaration 字段名必须为字符串",
            details={"actual_keys": tuple(sorted(str(key) for key in raw_keys))},
        )

    forbidden_keys = tuple(sorted(raw_keys & _FORBIDDEN_RESOURCE_REQUIREMENT_KEYS))
    if forbidden_keys:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "AdapterResourceRequirementDeclaration 禁止包含 fallback/priority/provider-selection 等扩张字段",
            details={"forbidden_fields": forbidden_keys},
        )

    if "resource_requirement_profiles" in raw_keys:
        missing_fields = tuple(sorted(_DECLARATION_V2_FIELD_NAMES - raw_keys))
        extra_fields = tuple(sorted(raw_keys - _DECLARATION_V2_FIELD_NAMES))
        if missing_fields or extra_fields:
            raise RegistryError(
                "invalid_adapter_resource_requirements",
                "AdapterResourceRequirementDeclarationV2 必须保持固定字段集合",
                details={
                    "missing_fields": missing_fields,
                    "extra_fields": extra_fields,
                },
            )
        return AdapterResourceRequirementDeclarationV2(
            adapter_key=raw_value["adapter_key"],
            capability=raw_value["capability"],
            resource_requirement_profiles=tuple(
                _normalize_resource_requirement_profile_candidate(profile)
                for profile in raw_value["resource_requirement_profiles"]
            ),
        )

    missing_fields = tuple(sorted(_DECLARATION_FIELD_NAMES - raw_keys))
    extra_fields = tuple(sorted(raw_keys - _DECLARATION_FIELD_NAMES))
    if missing_fields or extra_fields:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "AdapterResourceRequirementDeclaration 必须保持固定字段集合",
            details={
                "missing_fields": missing_fields,
                "extra_fields": extra_fields,
            },
        )

    return AdapterResourceRequirementDeclaration(
        adapter_key=raw_value["adapter_key"],
        capability=raw_value["capability"],
        resource_dependency_mode=raw_value["resource_dependency_mode"],
        required_capabilities=tuple(raw_value["required_capabilities"]),
        evidence_refs=tuple(raw_value["evidence_refs"]),
    )


def _normalize_resource_requirement_profile_candidate(raw_value: Any) -> AdapterResourceRequirementProfile:
    if isinstance(raw_value, AdapterResourceRequirementProfile):
        return raw_value
    if not isinstance(raw_value, Mapping):
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "AdapterResourceRequirementProfile 只能使用 canonical profile carrier",
            details={"invalid_value_type": type(raw_value).__name__},
        )
    raw_keys = {key for key in raw_value}
    if any(not isinstance(key, str) for key in raw_keys):
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "AdapterResourceRequirementProfile 字段名必须为字符串",
            details={"actual_keys": tuple(sorted(str(key) for key in raw_keys))},
        )
    forbidden_keys = tuple(sorted(raw_keys & _FORBIDDEN_RESOURCE_REQUIREMENT_KEYS))
    if forbidden_keys:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "AdapterResourceRequirementProfile 禁止包含 fallback/priority/provider-selection 等扩张字段",
            details={"forbidden_fields": forbidden_keys},
        )
    missing_fields = tuple(sorted(_PROFILE_FIELD_NAMES - raw_keys))
    extra_fields = tuple(sorted(raw_keys - _PROFILE_FIELD_NAMES))
    if missing_fields or extra_fields:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "AdapterResourceRequirementProfile 必须保持固定字段集合",
            details={
                "missing_fields": missing_fields,
                "extra_fields": extra_fields,
            },
        )
    return AdapterResourceRequirementProfile(
        profile_key=raw_value["profile_key"],
        resource_dependency_mode=raw_value["resource_dependency_mode"],
        required_capabilities=tuple(raw_value["required_capabilities"]),
        evidence_refs=tuple(raw_value["evidence_refs"]),
    )


def _validate_resource_requirement_declaration(
    *,
    adapter_key: str,
    declaration: AdapterResourceRequirementDeclarationCarrier,
) -> AdapterResourceRequirementDeclarationCarrier:
    if type(declaration) is AdapterResourceRequirementDeclarationV2:
        return _validate_resource_requirement_declaration_v2(adapter_key=adapter_key, declaration=declaration)
    if type(declaration) is not AdapterResourceRequirementDeclaration:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "resource_requirement_declarations 只能包含 canonical declaration carrier",
            details={"adapter_key": adapter_key, "actual_type": type(declaration).__name__},
        )
    normalized_adapter_key = _require_non_empty_string(
        declaration.adapter_key,
        code="invalid_adapter_resource_requirements",
        message="AdapterResourceRequirementDeclaration.adapter_key 必须为非空字符串",
        details={"adapter_key": adapter_key},
    )
    if normalized_adapter_key != adapter_key:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "AdapterResourceRequirementDeclaration.adapter_key 必须与 adapter_key 一致",
            details={
                "adapter_key": adapter_key,
                "declaration_adapter_key": normalized_adapter_key,
            },
        )

    capability = _require_non_empty_string(
        declaration.capability,
        code="invalid_adapter_resource_requirements",
        message="AdapterResourceRequirementDeclaration.capability 必须为非空字符串",
        details={"adapter_key": adapter_key},
    )
    if capability not in _ALLOWED_RESOURCE_REQUIREMENT_CAPABILITIES:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "AdapterResourceRequirementDeclaration.capability 未被共享证据批准",
            details={
                "adapter_key": adapter_key,
                "capability": capability,
            },
        )

    resource_dependency_mode = _require_non_empty_string(
        declaration.resource_dependency_mode,
        code="invalid_adapter_resource_requirements",
        message="AdapterResourceRequirementDeclaration.resource_dependency_mode 必须为非空字符串",
        details={"adapter_key": adapter_key, "capability": capability},
    )
    if resource_dependency_mode not in _ALLOWED_RESOURCE_DEPENDENCY_MODES:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "AdapterResourceRequirementDeclaration.resource_dependency_mode 仅允许 none|required",
            details={
                "adapter_key": adapter_key,
                "capability": capability,
                "resource_dependency_mode": resource_dependency_mode,
            },
        )

    required_capabilities = _validate_unique_string_tuple(
        declaration.required_capabilities,
        code="invalid_adapter_resource_requirements",
        message="AdapterResourceRequirementDeclaration.required_capabilities 必须为去重字符串数组",
        details={"adapter_key": adapter_key, "capability": capability},
    )
    unknown_required_capabilities = tuple(
        resource_capability
        for resource_capability in required_capabilities
        if resource_capability not in _APPROVED_RESOURCE_CAPABILITY_IDS
    )
    if unknown_required_capabilities:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "AdapterResourceRequirementDeclaration.required_capabilities 只能使用 FR-0015 已批准 capability ids",
            details={
                "adapter_key": adapter_key,
                "capability": capability,
                "unknown_required_capabilities": unknown_required_capabilities,
            },
        )
    if resource_dependency_mode == RESOURCE_DEPENDENCY_MODE_NONE and required_capabilities:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "resource_dependency_mode=none 时 required_capabilities 必须为空",
            details={"adapter_key": adapter_key, "capability": capability},
        )
    if resource_dependency_mode == RESOURCE_DEPENDENCY_MODE_REQUIRED and not required_capabilities:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "resource_dependency_mode=required 时 required_capabilities 必须非空",
            details={"adapter_key": adapter_key, "capability": capability},
        )

    evidence_refs = _validate_unique_string_tuple(
        declaration.evidence_refs,
        code="invalid_adapter_resource_requirements",
        message="AdapterResourceRequirementDeclaration.evidence_refs 必须为非空去重字符串数组",
        details={"adapter_key": adapter_key, "capability": capability},
    )
    if not evidence_refs:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "AdapterResourceRequirementDeclaration.evidence_refs 不得为空",
            details={"adapter_key": adapter_key, "capability": capability},
        )
    unknown_evidence_refs = tuple(
        evidence_ref
        for evidence_ref in evidence_refs
        if evidence_ref not in _APPROVED_RESOURCE_REQUIREMENT_EVIDENCE_REFS
    )
    if unknown_evidence_refs:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "AdapterResourceRequirementDeclaration.evidence_refs 必须绑定到 FR-0015 frozen evidence refs",
            details={
                "adapter_key": adapter_key,
                "capability": capability,
                "unknown_evidence_refs": unknown_evidence_refs,
            },
        )
    canonical_evidence_refs = _canonical_declaration_evidence_refs(
        adapter_key=adapter_key,
        capability=capability,
        resource_dependency_mode=resource_dependency_mode,
        required_capabilities=required_capabilities,
    )
    if evidence_refs != canonical_evidence_refs:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "AdapterResourceRequirementDeclaration.evidence_refs 必须等于当前声明的 FR-0015 frozen baseline",
            details={
                "adapter_key": adapter_key,
                "capability": capability,
                "resource_dependency_mode": resource_dependency_mode,
                "expected_evidence_refs": canonical_evidence_refs,
                "actual_evidence_refs": evidence_refs,
            },
        )

    return AdapterResourceRequirementDeclaration(
        adapter_key=normalized_adapter_key,
        capability=capability,
        resource_dependency_mode=resource_dependency_mode,
        required_capabilities=required_capabilities,
        evidence_refs=evidence_refs,
    )


def _validate_resource_requirement_declaration_v2(
    *,
    adapter_key: str,
    declaration: AdapterResourceRequirementDeclarationV2,
) -> AdapterResourceRequirementDeclarationV2:
    normalized_adapter_key = _require_non_empty_string(
        declaration.adapter_key,
        code="invalid_adapter_resource_requirements",
        message="AdapterResourceRequirementDeclarationV2.adapter_key 必须为非空字符串",
        details={"adapter_key": adapter_key},
    )
    if normalized_adapter_key != adapter_key:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "AdapterResourceRequirementDeclarationV2.adapter_key 必须与 adapter_key 一致",
            details={"adapter_key": adapter_key, "declaration_adapter_key": normalized_adapter_key},
        )
    capability = _require_non_empty_string(
        declaration.capability,
        code="invalid_adapter_resource_requirements",
        message="AdapterResourceRequirementDeclarationV2.capability 必须为非空字符串",
        details={"adapter_key": adapter_key},
    )
    if capability not in _ALLOWED_RESOURCE_REQUIREMENT_CAPABILITIES:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "AdapterResourceRequirementDeclarationV2.capability 未被共享证据批准",
            details={"adapter_key": adapter_key, "capability": capability},
        )
    profiles = _validate_profile_collection(
        declaration.resource_requirement_profiles,
        adapter_key=adapter_key,
        capability=capability,
    )
    return AdapterResourceRequirementDeclarationV2(
        adapter_key=normalized_adapter_key,
        capability=capability,
        resource_requirement_profiles=profiles,
    )


def _validate_profile_collection(
    raw_profiles: Any,
    *,
    adapter_key: str,
    capability: str,
) -> tuple[AdapterResourceRequirementProfile, ...]:
    if raw_profiles is None:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "resource_requirement_profiles 必须为非空 AdapterResourceRequirementProfile 集合",
            details={"adapter_key": adapter_key, "capability": capability, "actual_type": "NoneType"},
        )
    if isinstance(raw_profiles, (str, bytes)):
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "resource_requirement_profiles 必须为非空 AdapterResourceRequirementProfile 集合",
            details={"adapter_key": adapter_key, "capability": capability, "actual_type": type(raw_profiles).__name__},
        )
    try:
        iterator = iter(raw_profiles)
    except TypeError:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "resource_requirement_profiles 必须为非空 AdapterResourceRequirementProfile 集合",
            details={"adapter_key": adapter_key, "capability": capability, "actual_type": type(raw_profiles).__name__},
        )
    profiles = tuple(_normalize_resource_requirement_profile_candidate(profile) for profile in iterator)
    if not profiles:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "resource_requirement_profiles 不得为空",
            details={"adapter_key": adapter_key, "capability": capability},
        )

    approved_profile_entries = {
        entry.profile_ref: entry
        for entry in approved_shared_resource_requirement_profile_evidence_entries()
    }
    validated: list[AdapterResourceRequirementProfile] = []
    seen_profile_keys: set[str] = set()
    seen_tuples: set[tuple[str, tuple[str, ...]]] = set()
    for profile in profiles:
        profile_key = _require_non_empty_string(
            profile.profile_key,
            code="invalid_adapter_resource_requirements",
            message="AdapterResourceRequirementProfile.profile_key 必须为非空字符串",
            details={"adapter_key": adapter_key, "capability": capability},
        )
        if profile_key in seen_profile_keys:
            raise RegistryError(
                "invalid_adapter_resource_requirements",
                "resource_requirement_profiles 不得重复 profile_key",
                details={"adapter_key": adapter_key, "capability": capability, "profile_key": profile_key},
            )
        seen_profile_keys.add(profile_key)

        resource_dependency_mode = _require_non_empty_string(
            profile.resource_dependency_mode,
            code="invalid_adapter_resource_requirements",
            message="AdapterResourceRequirementProfile.resource_dependency_mode 必须为非空字符串",
            details={"adapter_key": adapter_key, "capability": capability, "profile_key": profile_key},
        )
        if resource_dependency_mode not in _ALLOWED_RESOURCE_DEPENDENCY_MODES:
            raise RegistryError(
                "invalid_adapter_resource_requirements",
                "AdapterResourceRequirementProfile.resource_dependency_mode 仅允许 none|required",
                details={"adapter_key": adapter_key, "capability": capability, "profile_key": profile_key},
            )
        required_capabilities = _validate_unique_string_tuple(
            profile.required_capabilities,
            code="invalid_adapter_resource_requirements",
            message="AdapterResourceRequirementProfile.required_capabilities 必须为去重字符串数组",
            details={"adapter_key": adapter_key, "capability": capability, "profile_key": profile_key},
        )
        unknown_required_capabilities = tuple(
            value for value in required_capabilities if value not in _APPROVED_RESOURCE_CAPABILITY_IDS
        )
        if unknown_required_capabilities:
            raise RegistryError(
                "invalid_adapter_resource_requirements",
                "AdapterResourceRequirementProfile.required_capabilities 只能使用 FR-0015 已批准 capability ids",
                details={
                    "adapter_key": adapter_key,
                    "capability": capability,
                    "profile_key": profile_key,
                    "unknown_required_capabilities": unknown_required_capabilities,
                },
            )
        if resource_dependency_mode == RESOURCE_DEPENDENCY_MODE_NONE and required_capabilities:
            raise RegistryError(
                "invalid_adapter_resource_requirements",
                "resource_dependency_mode=none 时 profile.required_capabilities 必须为空",
                details={"adapter_key": adapter_key, "capability": capability, "profile_key": profile_key},
            )
        if resource_dependency_mode == RESOURCE_DEPENDENCY_MODE_REQUIRED and not required_capabilities:
            raise RegistryError(
                "invalid_adapter_resource_requirements",
                "resource_dependency_mode=required 时 profile.required_capabilities 必须非空",
                details={"adapter_key": adapter_key, "capability": capability, "profile_key": profile_key},
            )
        normalized_required_capabilities = _canonicalize_required_capabilities(required_capabilities)
        if required_capabilities != normalized_required_capabilities:
            raise RegistryError(
                "invalid_adapter_resource_requirements",
                "AdapterResourceRequirementProfile.required_capabilities 必须使用 canonical 顺序",
                details={
                    "adapter_key": adapter_key,
                    "capability": capability,
                    "profile_key": profile_key,
                    "expected_required_capabilities": normalized_required_capabilities,
                    "actual_required_capabilities": required_capabilities,
                },
            )
        semantic_tuple = (resource_dependency_mode, normalized_required_capabilities)
        if semantic_tuple in seen_tuples:
            raise RegistryError(
                "invalid_adapter_resource_requirements",
                "resource_requirement_profiles 不得声明语义重复 profile",
                details={"adapter_key": adapter_key, "capability": capability, "profile_key": profile_key},
            )
        seen_tuples.add(semantic_tuple)

        evidence_refs = _validate_unique_string_tuple(
            profile.evidence_refs,
            code="invalid_adapter_resource_requirements",
            message="AdapterResourceRequirementProfile.evidence_refs 必须为非空去重字符串数组",
            details={"adapter_key": adapter_key, "capability": capability, "profile_key": profile_key},
        )
        if len(evidence_refs) != 1:
            raise RegistryError(
                "invalid_adapter_resource_requirements",
                "AdapterResourceRequirementProfile.evidence_refs 当前必须且只能绑定一个 profile proof",
                details={"adapter_key": adapter_key, "capability": capability, "profile_key": profile_key},
            )
        proof = approved_profile_entries.get(evidence_refs[0])
        if proof is None:
            raise RegistryError(
                "invalid_adapter_resource_requirements",
                "AdapterResourceRequirementProfile.evidence_refs 必须绑定到 FR-0027 approved shared profile proof",
                details={"adapter_key": adapter_key, "capability": capability, "profile_key": profile_key},
            )
        _validate_profile_proof_alignment(
            proof,
            adapter_key=adapter_key,
            capability=capability,
            profile_key=profile_key,
            resource_dependency_mode=resource_dependency_mode,
            required_capabilities=normalized_required_capabilities,
        )
        validated.append(
            AdapterResourceRequirementProfile(
                profile_key=profile_key,
                resource_dependency_mode=resource_dependency_mode,
                required_capabilities=normalized_required_capabilities,
                evidence_refs=evidence_refs,
            )
        )
    return tuple(validated)


def _validate_profile_proof_alignment(
    proof: ApprovedSharedResourceRequirementProfileEvidenceEntry,
    *,
    adapter_key: str,
    capability: str,
    profile_key: str,
    resource_dependency_mode: str,
    required_capabilities: tuple[str, ...],
) -> None:
    if proof.capability != capability and capability not in {"content_search", "content_list"}:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "profile proof capability 必须与 declaration capability 完全一致",
            details={"adapter_key": adapter_key, "capability": capability, "profile_key": profile_key},
        )
    if adapter_key not in proof.reference_adapters:
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "profile proof reference_adapters 必须覆盖 declaration adapter_key",
            details={"adapter_key": adapter_key, "capability": capability, "profile_key": profile_key},
        )
    if (
        proof.resource_dependency_mode != resource_dependency_mode
        or proof.required_capabilities != required_capabilities
    ):
        raise RegistryError(
            "invalid_adapter_resource_requirements",
            "profile proof 必须与 declaration profile tuple 完全一致",
            details={
                "adapter_key": adapter_key,
                "capability": capability,
                "profile_key": profile_key,
                "proof_profile_ref": proof.profile_ref,
            },
        )


def _validate_supported_axis(
    raw_values: Any,
    *,
    missing_code: str,
    message: str,
) -> frozenset[str]:
    if raw_values is MISSING:
        raise RegistryError(
            missing_code,
            message,
            details={"reason": "missing"},
        )
    if raw_values is None:
        raise RegistryError(
            missing_code,
            message,
            details={"actual_type": "NoneType"},
        )
    if isinstance(raw_values, (str, bytes)):
        raise RegistryError(
            missing_code,
            message,
            details={"actual_type": type(raw_values).__name__},
        )
    try:
        iterator = iter(raw_values)
    except TypeError:
        raise RegistryError(
            missing_code,
            message,
            details={"actual_type": type(raw_values).__name__},
        )
    validated: list[str] = []
    try:
        for value in iterator:
            if not isinstance(value, str):
                raise RegistryError(
                    missing_code,
                    message,
                    details={"invalid_value_type": type(value).__name__},
                )
            validated.append(value)
    except RegistryError:
        raise
    except Exception as error:
        raise RegistryError(
            missing_code,
            message,
            details={"error_type": error.__class__.__name__},
        ) from error
    return frozenset(validated)


def _validate_unique_string_tuple(
    raw_values: Any,
    *,
    code: str,
    message: str,
    details: Mapping[str, Any],
) -> tuple[str, ...]:
    if raw_values is MISSING:
        raise RegistryError(
            code,
            message,
            details={**details, "reason": "missing"},
        )
    if raw_values is None:
        raise RegistryError(
            code,
            message,
            details={**details, "actual_type": "NoneType"},
        )
    if isinstance(raw_values, (str, bytes)):
        raise RegistryError(
            code,
            message,
            details={**details, "actual_type": type(raw_values).__name__},
        )
    try:
        iterator = iter(raw_values)
    except TypeError:
        raise RegistryError(
            code,
            message,
            details={**details, "actual_type": type(raw_values).__name__},
        )

    validated: list[str] = []
    seen: set[str] = set()
    try:
        for value in iterator:
            normalized_value = _require_non_empty_string(
                value,
                code=code,
                message=message,
                details=details,
            )
            if normalized_value in seen:
                raise RegistryError(
                    code,
                    message,
                    details={**details, "duplicate_value": normalized_value},
                )
            seen.add(normalized_value)
            validated.append(normalized_value)
    except RegistryError:
        raise
    except Exception as error:
        raise RegistryError(
            code,
            message,
            details={**details, "error_type": error.__class__.__name__},
        ) from error
    return tuple(validated)


def _require_non_empty_string(
    value: Any,
    *,
    code: str,
    message: str,
    details: Mapping[str, Any],
) -> str:
    if not isinstance(value, str) or not value:
        raise RegistryError(
            code,
            message,
            details={
                **details,
                "actual_type": type(value).__name__,
            },
        )
    return value


def _canonical_required_evidence_refs(
    *,
    adapter_key: str,
    capability: str,
    required_capabilities: tuple[str, ...],
) -> tuple[str, ...]:
    ordered_required_capabilities = [
        capability_id
        for capability_id in _REQUIRED_CAPABILITY_ORDER
        if capability_id in frozenset(required_capabilities)
    ]
    ordered_refs: list[str] = []
    for required_capability in ordered_required_capabilities:
        record = _FROZEN_RESOURCE_CAPABILITY_RECORD_INDEX.get((adapter_key, capability, required_capability))
        if record is None and capability in {"content_search", "content_list"}:
            record = _FROZEN_RESOURCE_CAPABILITY_RECORD_INDEX.get((adapter_key, "content_detail", required_capability))
        if record is None:
            raise RegistryError(
                "invalid_adapter_resource_requirements",
                "required declaration 缺少可追溯到 FR-0015 的 frozen evidence baseline",
                details={
                    "adapter_key": adapter_key,
                    "capability": capability,
                    "required_capability": required_capability,
                },
            )
        for evidence_ref in record.evidence_refs:
            if evidence_ref not in ordered_refs:
                ordered_refs.append(evidence_ref)
    return tuple(ordered_refs)


def _canonicalize_required_capabilities(required_capabilities: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        capability_id
        for capability_id in _REQUIRED_CAPABILITY_ORDER
        if capability_id in frozenset(required_capabilities)
    )


def _canonical_declaration_evidence_refs(
    *,
    adapter_key: str,
    capability: str,
    resource_dependency_mode: str,
    required_capabilities: tuple[str, ...],
) -> tuple[str, ...]:
    if resource_dependency_mode == RESOURCE_DEPENDENCY_MODE_REQUIRED:
        return _canonical_required_evidence_refs(
            adapter_key=adapter_key,
            capability=capability,
            required_capabilities=required_capabilities,
        )
    raise RegistryError(
        "invalid_adapter_resource_requirements",
        "resource_dependency_mode=none 当前缺少可追溯到 FR-0015 的 frozen evidence baseline",
        details={
            "adapter_key": adapter_key,
            "capability": capability,
            "resource_dependency_mode": resource_dependency_mode,
        },
    )
