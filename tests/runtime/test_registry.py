from __future__ import annotations

from collections.abc import Mapping
import unittest
from typing import Iterator, Tuple

from syvert.registry import AdapterRegistry, RegistryError, baseline_required_resource_requirement_declaration


class SuccessfulAdapter:
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self) -> None:
        raise AssertionError("registry tests must not execute adapters")


class DiscoveryOnlyAdapter:
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self) -> None:
        raise AssertionError("registry discovery must not execute adapters")


class MissingCapabilitiesAdapter:
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self) -> None:
        raise AssertionError("registry tests must not execute adapters")


class MissingTargetsAdapter:
    supported_capabilities = frozenset({"content_detail"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self) -> None:
        raise AssertionError("registry tests must not execute adapters")


class MissingCollectionModesAdapter:
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})

    def execute(self) -> None:
        raise AssertionError("registry tests must not execute adapters")


class MissingExecuteAdapter:
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})


class ProviderOnlyObject:
    def fetch_content_detail(self) -> None:
        raise AssertionError("provider-only object must not be registered as an adapter")


class DeclarativeAdapter:
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = (
        baseline_required_resource_requirement_declaration(
            adapter_key="xhs",
            capability="content_detail",
        ),
    )

    def execute(self) -> None:
        raise AssertionError("registry tests must not execute adapters")


class PartialDeclarationAdapter:
    supported_capabilities = frozenset({"content_detail", "creator_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = (
        baseline_required_resource_requirement_declaration(
            adapter_key="xhs",
            capability="content_detail",
        ),
    )

    def execute(self) -> None:
        raise AssertionError("registry tests must not execute adapters")


class UnsupportedDeclarationAdapter:
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = (
        {
            "adapter_key": "stub",
            "capability": "creator_detail",
            "resource_dependency_mode": "none",
            "required_capabilities": (),
            "evidence_refs": ("fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",),
        },
    )

    def execute(self) -> None:
        raise AssertionError("registry tests must not execute adapters")


class ProviderFieldDeclarationAdapter:
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = (
        {
            "adapter_key": "xhs",
            "capability": "content_detail",
            "resource_dependency_mode": "required",
            "required_capabilities": ("account", "proxy"),
            "evidence_refs": ("fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",),
            "native_provider": "native-xhs",
        },
    )

    def execute(self) -> None:
        raise AssertionError("registry tests must not execute adapters")


class DuplicateAdapterRegistry(Mapping[str, object]):
    def __init__(self, adapter: object) -> None:
        self._adapter = adapter

    def __iter__(self) -> Iterator[str]:
        return iter(("stub", "stub"))

    def __len__(self) -> int:
        return 2

    def __getitem__(self, key: str) -> object:
        if key != "stub":
            raise KeyError(key)
        return self._adapter

    def items(self) -> Iterator[Tuple[str, object]]:
        return iter((("stub", self._adapter), ("stub", self._adapter)))


class RegistryTests(unittest.TestCase):
    def test_registry_materializes_declaration(self) -> None:
        registry = AdapterRegistry.from_mapping({"stub": SuccessfulAdapter()})

        declaration = registry.lookup("stub")
        self.assertIsNotNone(declaration)
        assert declaration is not None
        self.assertEqual(declaration.adapter_key, "stub")
        self.assertIn("content_detail", declaration.supported_capabilities)
        self.assertIn("url", declaration.supported_targets)
        self.assertIn("hybrid", declaration.supported_collection_modes)
        self.assertEqual(declaration.resource_requirement_declarations, ())

    def test_registry_discovery_is_side_effect_free(self) -> None:
        registry = AdapterRegistry.from_mapping({"stub": DiscoveryOnlyAdapter()})

        self.assertEqual(registry.discover_capabilities("stub"), frozenset({"content_detail"}))
        self.assertEqual(registry.discover_targets("stub"), frozenset({"url"}))
        self.assertEqual(registry.discover_collection_modes("stub"), frozenset({"hybrid"}))
        self.assertEqual(registry.discover_resource_requirements("stub"), ())

    def test_registry_materializes_resource_requirement_declaration(self) -> None:
        registry = AdapterRegistry.from_mapping({"xhs": DeclarativeAdapter()})

        declaration = registry.lookup_resource_requirement("xhs", "content_detail")

        self.assertIsNotNone(declaration)
        assert declaration is not None
        self.assertEqual(declaration.adapter_key, "xhs")
        self.assertEqual(declaration.capability, "content_detail")
        self.assertEqual(declaration.resource_dependency_mode, "required")
        self.assertEqual(declaration.required_capabilities, ("account", "proxy"))
        self.assertEqual(
            registry.discover_resource_requirements("xhs"),
            (declaration,),
        )

    def test_registry_materializes_real_reference_adapters_without_provider_fields(self) -> None:
        from syvert.adapters.douyin import DouyinAdapter
        from syvert.adapters.xhs import XhsAdapter

        registry = AdapterRegistry.from_mapping({"xhs": XhsAdapter(), "douyin": DouyinAdapter()})

        for adapter_key in ("xhs", "douyin"):
            declaration = registry.lookup(adapter_key)
            self.assertIsNotNone(declaration)
            assert declaration is not None
            self.assertFalse(hasattr(declaration, "provider"))
            self.assertFalse(hasattr(declaration, "native_provider"))
            self.assertEqual(declaration.supported_capabilities, frozenset({"content_detail"}))
            self.assertEqual(declaration.supported_targets, frozenset({"url"}))
            self.assertEqual(declaration.supported_collection_modes, frozenset({"hybrid"}))
            requirements = registry.discover_resource_requirements(adapter_key)
            self.assertIsNotNone(requirements)
            assert requirements is not None
            self.assertEqual(len(requirements), 1)
            requirement = requirements[0]
            self.assertFalse(hasattr(requirement, "provider"))
            self.assertFalse(hasattr(requirement, "native_provider"))
            self.assertEqual(requirement.required_capabilities, ("account", "proxy"))

    def test_registry_allows_partial_resource_requirement_coverage(self) -> None:
        registry = AdapterRegistry.from_mapping({"xhs": PartialDeclarationAdapter()})

        declaration = registry.lookup("xhs")

        self.assertIsNotNone(declaration)
        assert declaration is not None
        self.assertEqual(
            declaration.resource_requirement_declarations,
            (
                baseline_required_resource_requirement_declaration(
                    adapter_key="xhs",
                    capability="content_detail",
                ),
            ),
        )

    def test_registry_rejects_declaration_for_unsupported_capability(self) -> None:
        with self.assertRaises(RegistryError) as context:
            AdapterRegistry.from_mapping({"stub": UnsupportedDeclarationAdapter()})

        self.assertEqual(context.exception.code, "invalid_adapter_resource_requirements")

    def test_registry_rejects_duplicate_keys(self) -> None:
        with self.assertRaises(RegistryError) as context:
            AdapterRegistry.from_mapping(DuplicateAdapterRegistry(SuccessfulAdapter()))

        self.assertEqual(context.exception.code, "invalid_adapter_registry")

    def test_registry_rejects_missing_capabilities(self) -> None:
        with self.assertRaises(RegistryError) as context:
            AdapterRegistry.from_mapping({"stub": MissingCapabilitiesAdapter()})

        self.assertEqual(context.exception.code, "invalid_adapter_capabilities")

    def test_registry_rejects_missing_targets(self) -> None:
        with self.assertRaises(RegistryError) as context:
            AdapterRegistry.from_mapping({"stub": MissingTargetsAdapter()})

        self.assertEqual(context.exception.code, "invalid_adapter_targets")

    def test_registry_rejects_missing_collection_modes(self) -> None:
        with self.assertRaises(RegistryError) as context:
            AdapterRegistry.from_mapping({"stub": MissingCollectionModesAdapter()})

        self.assertEqual(context.exception.code, "invalid_adapter_collection_modes")

    def test_registry_rejects_missing_execute_contract(self) -> None:
        with self.assertRaises(RegistryError) as context:
            AdapterRegistry.from_mapping({"stub": MissingExecuteAdapter()})

        self.assertEqual(context.exception.code, "invalid_adapter_declaration")

    def test_registry_rejects_provider_only_object_as_adapter(self) -> None:
        with self.assertRaises(RegistryError) as context:
            AdapterRegistry.from_mapping({"xhs": ProviderOnlyObject()})

        self.assertEqual(context.exception.code, "invalid_adapter_declaration")

    def test_registry_rejects_provider_fields_in_resource_requirement_declarations(self) -> None:
        with self.assertRaises(RegistryError) as context:
            AdapterRegistry.from_mapping({"xhs": ProviderFieldDeclarationAdapter()})

        self.assertEqual(context.exception.code, "invalid_adapter_resource_requirements")
        self.assertEqual(context.exception.details["forbidden_fields"], ("native_provider",))


if __name__ == "__main__":
    unittest.main()
