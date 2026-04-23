from __future__ import annotations

import unittest

from syvert.registry import AdapterRegistry, RegistryError, baseline_required_resource_requirement_declaration
from syvert.resource_capability_evidence import frozen_evidence_reference_entries


class StubDeclarativeAdapter:
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def __init__(self, *, resource_requirement_declarations: tuple[object, ...]) -> None:
        self.resource_requirement_declarations = resource_requirement_declarations

    def execute(self) -> None:
        raise AssertionError("declaration tests must not execute adapters")


class AdapterResourceRequirementDeclarationTests(unittest.TestCase):
    def test_baseline_helper_materializes_required_account_and_proxy(self) -> None:
        xhs_declaration = baseline_required_resource_requirement_declaration(
            adapter_key="xhs",
            capability="content_detail",
        )
        douyin_declaration = baseline_required_resource_requirement_declaration(
            adapter_key="douyin",
            capability="content_detail",
        )

        self.assertEqual(xhs_declaration.resource_dependency_mode, "required")
        self.assertEqual(douyin_declaration.resource_dependency_mode, "required")
        self.assertEqual(xhs_declaration.required_capabilities, ("account", "proxy"))
        self.assertEqual(douyin_declaration.required_capabilities, ("account", "proxy"))
        self.assertEqual(
            xhs_declaration.evidence_refs,
            (
                "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                "fr-0015:xhs:content-detail:url:hybrid:account-material",
                "fr-0015:regression:xhs:managed-proxy-seed",
            ),
        )
        self.assertEqual(
            douyin_declaration.evidence_refs,
            (
                "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                "fr-0015:douyin:content-detail:url:hybrid:account-material",
                "fr-0015:regression:douyin:managed-proxy-seed",
            ),
        )

    def test_registry_materializes_mapping_shaped_required_declaration(self) -> None:
        registry = AdapterRegistry.from_mapping(
            {
                "xhs": StubDeclarativeAdapter(
                    resource_requirement_declarations=(
                        {
                            "adapter_key": "xhs",
                            "capability": "content_detail",
                            "resource_dependency_mode": "required",
                            "required_capabilities": ["account", "proxy"],
                            "evidence_refs": (
                                "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                                "fr-0015:xhs:content-detail:url:hybrid:account-material",
                                "fr-0015:regression:xhs:managed-proxy-seed",
                            ),
                        },
                    ),
                )
            }
        )

        declaration = registry.lookup_resource_requirement("xhs", "content_detail")

        self.assertIsNotNone(declaration)
        assert declaration is not None
        self.assertEqual(declaration.required_capabilities, ("account", "proxy"))
        self.assertEqual(declaration.resource_dependency_mode, "required")

    def test_registry_accepts_none_mode_with_empty_required_capabilities(self) -> None:
        registry = AdapterRegistry.from_mapping(
            {
                "stub": StubDeclarativeAdapter(
                    resource_requirement_declarations=(
                        {
                            "adapter_key": "stub",
                            "capability": "content_detail",
                            "resource_dependency_mode": "none",
                            "required_capabilities": (),
                            "evidence_refs": (frozen_evidence_reference_entries()[0].evidence_ref,),
                        },
                    ),
                )
            }
        )

        declaration = registry.lookup_resource_requirement("stub", "content_detail")

        self.assertIsNotNone(declaration)
        assert declaration is not None
        self.assertEqual(declaration.resource_dependency_mode, "none")
        self.assertEqual(declaration.required_capabilities, ())

    def test_registry_rejects_invalid_resource_dependency_mode(self) -> None:
        with self.assertRaises(RegistryError) as context:
            AdapterRegistry.from_mapping(
                {
                    "stub": StubDeclarativeAdapter(
                        resource_requirement_declarations=(
                            {
                                "adapter_key": "stub",
                                "capability": "content_detail",
                                "resource_dependency_mode": "optional",
                                "required_capabilities": (),
                                "evidence_refs": (frozen_evidence_reference_entries()[0].evidence_ref,),
                            },
                        ),
                    )
                }
            )

        self.assertEqual(context.exception.code, "invalid_adapter_resource_requirements")

    def test_registry_rejects_unknown_required_capability(self) -> None:
        with self.assertRaises(RegistryError) as context:
            AdapterRegistry.from_mapping(
                {
                    "xhs": StubDeclarativeAdapter(
                        resource_requirement_declarations=(
                            {
                                "adapter_key": "xhs",
                                "capability": "content_detail",
                                "resource_dependency_mode": "required",
                                "required_capabilities": ("account", "browser_state"),
                                "evidence_refs": (
                                    "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                                    "fr-0015:xhs:content-detail:url:hybrid:account-material",
                                    "fr-0015:regression:xhs:managed-proxy-seed",
                                ),
                            },
                        ),
                    )
                }
            )

        self.assertEqual(context.exception.code, "invalid_adapter_resource_requirements")

    def test_registry_rejects_duplicate_required_capabilities(self) -> None:
        with self.assertRaises(RegistryError) as context:
            AdapterRegistry.from_mapping(
                {
                    "xhs": StubDeclarativeAdapter(
                        resource_requirement_declarations=(
                            {
                                "adapter_key": "xhs",
                                "capability": "content_detail",
                                "resource_dependency_mode": "required",
                                "required_capabilities": ("account", "account"),
                                "evidence_refs": (
                                    "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                                    "fr-0015:xhs:content-detail:url:hybrid:account-material",
                                    "fr-0015:regression:xhs:managed-proxy-seed",
                                ),
                            },
                        ),
                    )
                }
            )

        self.assertEqual(context.exception.code, "invalid_adapter_resource_requirements")

    def test_registry_rejects_missing_evidence_refs(self) -> None:
        with self.assertRaises(RegistryError) as context:
            AdapterRegistry.from_mapping(
                {
                    "xhs": StubDeclarativeAdapter(
                        resource_requirement_declarations=(
                            {
                                "adapter_key": "xhs",
                                "capability": "content_detail",
                                "resource_dependency_mode": "required",
                                "required_capabilities": ("account", "proxy"),
                            },
                        ),
                    )
                }
            )

        self.assertEqual(context.exception.code, "invalid_adapter_resource_requirements")

    def test_registry_rejects_duplicate_evidence_refs(self) -> None:
        with self.assertRaises(RegistryError) as context:
            AdapterRegistry.from_mapping(
                {
                    "xhs": StubDeclarativeAdapter(
                        resource_requirement_declarations=(
                            {
                                "adapter_key": "xhs",
                                "capability": "content_detail",
                                "resource_dependency_mode": "required",
                                "required_capabilities": ("account", "proxy"),
                                "evidence_refs": (
                                    "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                                    "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                                    "fr-0015:regression:xhs:managed-proxy-seed",
                                ),
                            },
                        ),
                    )
                }
            )

        self.assertEqual(context.exception.code, "invalid_adapter_resource_requirements")

    def test_registry_rejects_unknown_evidence_refs(self) -> None:
        with self.assertRaises(RegistryError) as context:
            AdapterRegistry.from_mapping(
                {
                    "xhs": StubDeclarativeAdapter(
                        resource_requirement_declarations=(
                            {
                                "adapter_key": "xhs",
                                "capability": "content_detail",
                                "resource_dependency_mode": "required",
                                "required_capabilities": ("account", "proxy"),
                                "evidence_refs": (
                                    "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                                    "fr-0015:regression:xhs:managed-proxy-seed",
                                    "fr-0015:unknown-evidence",
                                ),
                            },
                        ),
                    )
                }
            )

        self.assertEqual(context.exception.code, "invalid_adapter_resource_requirements")

    def test_registry_rejects_forbidden_fallback_field(self) -> None:
        with self.assertRaises(RegistryError) as context:
            AdapterRegistry.from_mapping(
                {
                    "xhs": StubDeclarativeAdapter(
                        resource_requirement_declarations=(
                            {
                                "adapter_key": "xhs",
                                "capability": "content_detail",
                                "resource_dependency_mode": "required",
                                "required_capabilities": ("account", "proxy"),
                                "evidence_refs": (
                                    "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                                    "fr-0015:xhs:content-detail:url:hybrid:account-material",
                                    "fr-0015:regression:xhs:managed-proxy-seed",
                                ),
                                "fallback": "proxy_only",
                            },
                        ),
                    )
                }
            )

        self.assertEqual(context.exception.code, "invalid_adapter_resource_requirements")
