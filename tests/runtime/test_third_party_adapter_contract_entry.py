from __future__ import annotations

import copy
import unittest

from syvert.registry import AdapterResourceRequirementDeclarationV2
from tests.runtime.contract_harness.third_party_entry import (
    ThirdPartyContractEntryError,
    run_third_party_adapter_contract_test,
    validate_third_party_adapter_manifest,
)
from tests.runtime.contract_harness.third_party_fixtures import (
    THIRD_PARTY_ERROR_MAPPING_FIXTURE_ID,
    THIRD_PARTY_FIXTURE_ADAPTER_KEY,
    THIRD_PARTY_SUCCESS_FIXTURE_ID,
    ThirdPartyContractFixtureAdapter,
    minimal_third_party_adapter_fixtures,
    minimal_third_party_adapter_manifest,
)


class AdapterMissingSdkContractMetadata(ThirdPartyContractFixtureAdapter):
    sdk_contract_id = ""


class AdapterWithProviderFacingMetadata(ThirdPartyContractFixtureAdapter):
    provider_key = "native-provider"
    selector = "runtime-selector"


class AdapterWithUserIdTargetMetadata(ThirdPartyContractFixtureAdapter):
    supported_targets = frozenset({"user_id"})


class AdapterWithDriftedErrorMapping(ThirdPartyContractFixtureAdapter):
    error_mapping = {
        "content_not_found": {
            "category": "platform",
            "code": "drifted_content_not_found",
            "message": "drifted mapping",
        },
    }


def _none_profile_resource_requirement_declarations() -> tuple[dict[str, object], ...]:
    return (
        {
            "adapter_key": THIRD_PARTY_FIXTURE_ADAPTER_KEY,
            "capability": "content_detail",
            "resource_requirement_profiles": (
                {
                    "profile_key": "none",
                    "resource_dependency_mode": "none",
                    "required_capabilities": (),
                    "evidence_refs": ("fr-0027:profile:content-detail-by-url-hybrid:none",),
                },
            ),
        },
    )


class AdapterWithNoneResourceProfile(ThirdPartyContractFixtureAdapter):
    resource_requirement_declarations = _none_profile_resource_requirement_declarations()


class ThirdPartyAdapterContractEntryTests(unittest.TestCase):
    def test_accepts_minimal_manifest_fixtures_and_adapter_execution(self) -> None:
        adapter = ThirdPartyContractFixtureAdapter()

        results = run_third_party_adapter_contract_test(
            manifest=minimal_third_party_adapter_manifest(),
            fixtures=minimal_third_party_adapter_fixtures(),
            adapter=adapter,
        )

        self.assertEqual(
            [result["sample_id"] for result in results],
            [THIRD_PARTY_SUCCESS_FIXTURE_ID, THIRD_PARTY_ERROR_MAPPING_FIXTURE_ID],
        )
        self.assertEqual(results[0]["verdict"], "pass")
        self.assertEqual(results[0]["reason"]["code"], "success_envelope_observed")
        self.assertEqual(results[0]["observed_status"], "success")
        self.assertEqual(results[1]["verdict"], "legal_failure")
        self.assertEqual(results[1]["observed_status"], "failed")
        self.assertEqual(results[1]["observed_error"]["category"], "platform")
        self.assertEqual(results[1]["observed_error"]["code"], "content_not_found")
        self.assertEqual(adapter.last_resource_slots, ("account", "proxy"))

    def test_manifest_resource_declarations_are_normalized_through_fr0027_profile_proof(self) -> None:
        manifest = validate_third_party_adapter_manifest(minimal_third_party_adapter_manifest())

        self.assertEqual(manifest.adapter_key, THIRD_PARTY_FIXTURE_ADAPTER_KEY)
        self.assertEqual(len(manifest.resource_requirement_declarations), 1)
        declaration = manifest.resource_requirement_declarations[0]
        self.assertIsInstance(declaration, AdapterResourceRequirementDeclarationV2)
        assert isinstance(declaration, AdapterResourceRequirementDeclarationV2)
        self.assertEqual(
            [profile.profile_key for profile in declaration.resource_requirement_profiles],
            ["account_proxy", "account"],
        )

    def test_accepts_fr0027_none_resource_profile_without_required_capabilities(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        manifest["resource_requirement_declarations"] = _none_profile_resource_requirement_declarations()
        fixtures = copy.deepcopy(minimal_third_party_adapter_fixtures())
        for fixture in fixtures:
            fixture["input"]["resource_profile_key"] = "none"
        adapter = AdapterWithNoneResourceProfile()

        results = run_third_party_adapter_contract_test(
            manifest=manifest,
            fixtures=fixtures,
            adapter=adapter,
        )

        self.assertEqual(results[0]["verdict"], "pass")
        self.assertEqual(results[1]["verdict"], "legal_failure")
        self.assertEqual(adapter.last_resource_slots, ())

    def test_rejects_missing_required_public_metadata_before_execution(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        del manifest["sdk_contract_id"]

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=manifest,
                fixtures=minimal_third_party_adapter_fixtures(),
                adapter=ThirdPartyContractFixtureAdapter(),
            )

        self.assertEqual(context.exception.code, "invalid_manifest_shape")
        self.assertEqual(context.exception.details["missing_fields"], ("sdk_contract_id",))

    def test_rejects_provider_and_compatibility_manifest_fields_fail_closed(self) -> None:
        forbidden_fields = (
            "provider_offer",
            "compatibility_decision",
            "provider_key",
            "selector",
            "fallback",
            "priority",
            "score",
            "marketplace",
        )
        for field in forbidden_fields:
            with self.subTest(field=field):
                manifest = minimal_third_party_adapter_manifest()
                manifest[field] = "must-not-pass"

                with self.assertRaises(ThirdPartyContractEntryError) as context:
                    validate_third_party_adapter_manifest(manifest)

                self.assertEqual(context.exception.code, "forbidden_adapter_manifest_fields")
                self.assertEqual(context.exception.details["forbidden_fields"], (field,))

    def test_rejects_adapter_key_with_provider_account_or_runtime_strategy_semantics(self) -> None:
        invalid_adapter_keys = (
            "provider-xhs",
            "xhs",
            "douyin",
            "xhs-prod-account-1",
            "xhs-selector-fallback",
        )
        for adapter_key in invalid_adapter_keys:
            with self.subTest(adapter_key=adapter_key):
                manifest = minimal_third_party_adapter_manifest()
                manifest["adapter_key"] = adapter_key

                with self.assertRaises(ThirdPartyContractEntryError) as context:
                    validate_third_party_adapter_manifest(manifest)

                self.assertEqual(context.exception.code, "invalid_adapter_key_boundary")

    def test_rejects_manifest_capability_outside_current_approved_slice(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        manifest["supported_capabilities"] = ("content_detail", "unapproved_capability")

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            validate_third_party_adapter_manifest(manifest)

        self.assertEqual(context.exception.code, "unsupported_manifest_capabilities")
        self.assertEqual(context.exception.details["unsupported_capabilities"], ("unapproved_capability",))

    def test_rejects_mapping_where_manifest_requires_explicit_sequence(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        manifest["supported_capabilities"] = {"content_detail": True}

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            validate_third_party_adapter_manifest(manifest)

        self.assertEqual(context.exception.code, "invalid_manifest_public_metadata")
        self.assertEqual(context.exception.details["field"], "supported_capabilities")
        self.assertEqual(context.exception.details["actual_type"], "dict")

    def test_allows_adapter_key_with_non_semantic_forbidden_letter_sequences(self) -> None:
        allowed_adapter_keys = (
            "adventure_feed",
            "product_review",
            "routerless_content",
        )
        for adapter_key in allowed_adapter_keys:
            with self.subTest(adapter_key=adapter_key):
                manifest = minimal_third_party_adapter_manifest()
                manifest["adapter_key"] = adapter_key
                declarations = copy.deepcopy(manifest["resource_requirement_declarations"])
                declarations[0]["adapter_key"] = adapter_key
                manifest["resource_requirement_declarations"] = declarations

                normalized = validate_third_party_adapter_manifest(manifest)

                self.assertEqual(normalized.adapter_key, adapter_key)

    def test_rejects_invalid_fr0027_resource_declaration_via_registry(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        declarations = copy.deepcopy(manifest["resource_requirement_declarations"])
        declarations[0]["resource_requirement_profiles"][0]["evidence_refs"] = ("fr-0027:profile:unknown",)
        manifest["resource_requirement_declarations"] = declarations

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            validate_third_party_adapter_manifest(manifest)

        self.assertEqual(context.exception.code, "invalid_manifest_resource_requirement_declarations")
        self.assertEqual(context.exception.details["profile_key"], "account_proxy")

    def test_rejects_adapter_public_metadata_that_does_not_match_manifest(self) -> None:
        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=minimal_third_party_adapter_manifest(),
                fixtures=minimal_third_party_adapter_fixtures(),
                adapter=AdapterMissingSdkContractMetadata(),
            )

        self.assertEqual(context.exception.code, "adapter_manifest_metadata_mismatch")
        self.assertIn("sdk_contract_id", context.exception.details["mismatches"])

    def test_rejects_fixture_input_not_declared_by_manifest_target_metadata(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        manifest["supported_targets"] = ("user_id",)

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=manifest,
                fixtures=minimal_third_party_adapter_fixtures(),
                adapter=AdapterWithUserIdTargetMetadata(),
            )

        self.assertEqual(context.exception.code, "invalid_fixture_input_metadata")
        self.assertEqual(context.exception.details["target_type"], "url")

    def test_rejects_fixture_without_resource_profile_input(self) -> None:
        fixtures = copy.deepcopy(minimal_third_party_adapter_fixtures())
        del fixtures[0]["input"]["resource_profile_key"]

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=minimal_third_party_adapter_manifest(),
                fixtures=fixtures,
                adapter=ThirdPartyContractFixtureAdapter(),
            )

        self.assertEqual(context.exception.code, "invalid_fixture_input")
        self.assertEqual(context.exception.details["field"], "input.resource_profile_key")

    def test_rejects_error_mapping_fixture_that_does_not_match_manifest_mapping(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        manifest["error_mapping"] = AdapterWithDriftedErrorMapping.error_mapping

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=manifest,
                fixtures=minimal_third_party_adapter_fixtures(),
                adapter=AdapterWithDriftedErrorMapping(),
            )

        self.assertEqual(context.exception.code, "fixture_error_mapping_manifest_mismatch")
        self.assertEqual(context.exception.details["manifest_code"], "drifted_content_not_found")
        self.assertEqual(context.exception.details["fixture_code"], "content_not_found")

    def test_rejects_adapter_public_metadata_with_provider_facing_fields(self) -> None:
        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=minimal_third_party_adapter_manifest(),
                fixtures=minimal_third_party_adapter_fixtures(),
                adapter=AdapterWithProviderFacingMetadata(),
            )

        self.assertEqual(context.exception.code, "forbidden_adapter_public_metadata_fields")
        self.assertEqual(context.exception.details["forbidden_fields"], ("provider_key", "selector"))

    def test_rejects_fixture_refs_that_do_not_resolve(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        manifest["fixture_refs"] = (
            THIRD_PARTY_SUCCESS_FIXTURE_ID,
            "missing-error-mapping-fixture",
        )

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=manifest,
                fixtures=minimal_third_party_adapter_fixtures(),
                adapter=ThirdPartyContractFixtureAdapter(),
            )

        self.assertEqual(context.exception.code, "unresolvable_fixture_refs")
        self.assertEqual(context.exception.details["missing_refs"], ("missing-error-mapping-fixture",))

    def test_rejects_fixtures_without_success_and_error_mapping_coverage(self) -> None:
        fixtures = tuple(
            fixture
            for fixture in minimal_third_party_adapter_fixtures()
            if fixture["case_type"] == "success"
        )
        manifest = minimal_third_party_adapter_manifest()
        manifest["fixture_refs"] = (THIRD_PARTY_SUCCESS_FIXTURE_ID,)

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=manifest,
                fixtures=fixtures,
                adapter=ThirdPartyContractFixtureAdapter(),
            )

        self.assertEqual(context.exception.code, "missing_fixture_case_coverage")
        self.assertEqual(context.exception.details["missing_case_types"], ("error_mapping",))

    def test_reports_adapter_success_payload_contract_violation(self) -> None:
        results = run_third_party_adapter_contract_test(
            manifest=minimal_third_party_adapter_manifest(),
            fixtures=minimal_third_party_adapter_fixtures(),
            adapter=ThirdPartyContractFixtureAdapter(success_payload_shape="missing_normalized"),
        )

        success_result = results[0]
        self.assertEqual(success_result["sample_id"], THIRD_PARTY_SUCCESS_FIXTURE_ID)
        self.assertEqual(success_result["verdict"], "contract_violation")
        self.assertEqual(success_result["reason"]["code"], "invalid_adapter_success_payload")

    def test_reports_non_mapping_adapter_success_payload_as_contract_violation(self) -> None:
        results = run_third_party_adapter_contract_test(
            manifest=minimal_third_party_adapter_manifest(),
            fixtures=minimal_third_party_adapter_fixtures(),
            adapter=ThirdPartyContractFixtureAdapter(success_payload_shape="non_mapping"),
        )

        success_result = results[0]
        self.assertEqual(success_result["sample_id"], THIRD_PARTY_SUCCESS_FIXTURE_ID)
        self.assertEqual(success_result["verdict"], "contract_violation")
        self.assertEqual(success_result["reason"]["code"], "invalid_adapter_success_payload")

    def test_reports_adapter_error_mapping_mismatch(self) -> None:
        results = run_third_party_adapter_contract_test(
            manifest=minimal_third_party_adapter_manifest(),
            fixtures=minimal_third_party_adapter_fixtures(),
            adapter=ThirdPartyContractFixtureAdapter(error_code="unexpected_error_code"),
        )

        error_result = results[1]
        self.assertEqual(error_result["sample_id"], THIRD_PARTY_ERROR_MAPPING_FIXTURE_ID)
        self.assertEqual(error_result["verdict"], "contract_violation")
        self.assertEqual(error_result["reason"]["code"], "error_mapping_mismatch")


if __name__ == "__main__":
    unittest.main()
