from __future__ import annotations

from collections.abc import Mapping
import unittest
from typing import Iterator, Tuple

from syvert.registry import AdapterRegistry, RegistryError


class SuccessfulAdapter:
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})


class DiscoveryOnlyAdapter:
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self) -> None:
        raise AssertionError("registry discovery must not execute adapters")


class MissingCapabilitiesAdapter:
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})


class MissingTargetsAdapter:
    supported_capabilities = frozenset({"content_detail"})
    supported_collection_modes = frozenset({"hybrid"})


class MissingCollectionModesAdapter:
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})


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

    def test_registry_discovery_is_side_effect_free(self) -> None:
        registry = AdapterRegistry.from_mapping({"stub": DiscoveryOnlyAdapter()})

        self.assertEqual(registry.discover_capabilities("stub"), frozenset({"content_detail"}))
        self.assertEqual(registry.discover_targets("stub"), frozenset({"url"}))
        self.assertEqual(registry.discover_collection_modes("stub"), frozenset({"hybrid"}))

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


if __name__ == "__main__":
    unittest.main()
