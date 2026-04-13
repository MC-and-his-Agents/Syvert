from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


MISSING = object()


class RegistryError(Exception):
    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})


@dataclass(frozen=True)
class AdapterDeclaration:
    adapter_key: str
    adapter: Any
    supported_capabilities: frozenset[str]
    supported_targets: frozenset[str]
    supported_collection_modes: frozenset[str]


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


def _build_adapter_declaration(adapter_key: str, adapter: Any) -> AdapterDeclaration:
    _validate_adapter_execute(adapter_key, adapter)
    capabilities = _get_adapter_attribute(adapter, "supported_capabilities")
    targets = _get_adapter_attribute(adapter, "supported_targets")
    collection_modes = _get_adapter_attribute(adapter, "supported_collection_modes")

    supported_capabilities = _validate_supported_capabilities(capabilities)
    supported_targets = _validate_supported_targets(targets)
    supported_collection_modes = _validate_supported_collection_modes(collection_modes)

    return AdapterDeclaration(
        adapter_key=adapter_key,
        adapter=adapter,
        supported_capabilities=supported_capabilities,
        supported_targets=supported_targets,
        supported_collection_modes=supported_collection_modes,
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
