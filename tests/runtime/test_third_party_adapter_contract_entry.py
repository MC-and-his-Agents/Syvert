from __future__ import annotations

import copy
import unittest

from syvert.registry import AdapterResourceRequirementDeclarationV2
from syvert.runtime import PlatformAdapterError
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


class AdapterWithExtendedProviderFacingMetadata(ThirdPartyContractFixtureAdapter):
    browser_provider = "browser-provider"
    external_provider_ref = "external-provider"
    native_provider = "native-provider"
    provider_capabilities = ("content_detail",)
    provider_selection = "runtime-selector"


class AdapterWithUserIdTargetMetadata(ThirdPartyContractFixtureAdapter):
    supported_targets = frozenset({"user_id"})


class AdapterWithOverclaimedTargetAndMode(ThirdPartyContractFixtureAdapter):
    supported_targets = frozenset({"url", "user_id"})
    supported_collection_modes = frozenset({"hybrid", "public"})


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


class AdapterWithUnexpectedException(ThirdPartyContractFixtureAdapter):
    def execute(self, request):  # type: ignore[no-untyped-def]
        raise RuntimeError("unexpected adapter bug")


class AdapterWithCallCount(ThirdPartyContractFixtureAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.execute_calls = 0

    def execute(self, request):  # type: ignore[no-untyped-def]
        self.execute_calls += 1
        return super().execute(request)


class AdapterWithInvalidPlatformErrorDetails(ThirdPartyContractFixtureAdapter):
    def __init__(self, *, details) -> None:  # type: ignore[no-untyped-def]
        super().__init__()
        self._details = details

    def execute(self, request):  # type: ignore[no-untyped-def]
        raise PlatformAdapterError(
            code="content_not_found",
            message="content is unavailable or deleted",
            details=self._details,  # type: ignore[arg-type]
        )


class AdapterWithUnsupportedCategoryPlatformError(ThirdPartyContractFixtureAdapter):
    def execute(self, request):  # type: ignore[no-untyped-def]
        if "content-not-found" in request.target_value:
            raise PlatformAdapterError(
                code="content_not_found",
                message="content is unavailable or deleted",
                details={"source_error": "content_not_found"},
                category="unsupported",
            )
        return super().execute(request)


class AdapterWithMismatchedSourceErrorDetails(ThirdPartyContractFixtureAdapter):
    def execute(self, request):  # type: ignore[no-untyped-def]
        if "content-not-found" in request.target_value:
            raise PlatformAdapterError(
                code="content_not_found",
                message="content is unavailable or deleted",
                details={"source_error": "different_source_error"},
            )
        return super().execute(request)


class AdapterWithMismatchedErrorMessage(ThirdPartyContractFixtureAdapter):
    def execute(self, request):  # type: ignore[no-untyped-def]
        if "content-not-found" in request.target_value:
            raise PlatformAdapterError(
                code="content_not_found",
                message="different error message",
                details={"source_error": "content_not_found"},
            )
        return super().execute(request)


class AdapterWithInvalidFixtureRefs(ThirdPartyContractFixtureAdapter):
    fixture_refs = (
        THIRD_PARTY_SUCCESS_FIXTURE_ID,
        1,
    )


class AdapterWithReorderedPublicMetadata(ThirdPartyContractFixtureAdapter):
    fixture_refs = (
        THIRD_PARTY_ERROR_MAPPING_FIXTURE_ID,
        THIRD_PARTY_SUCCESS_FIXTURE_ID,
    )
    resource_requirement_declarations = (
        {
            "adapter_key": THIRD_PARTY_FIXTURE_ADAPTER_KEY,
            "capability": "content_detail",
            "resource_requirement_profiles": (
                {
                    "profile_key": "account",
                    "resource_dependency_mode": "required",
                    "required_capabilities": ("account",),
                    "evidence_refs": ("fr-0027:profile:content-detail-by-url-hybrid:account",),
                },
                {
                    "profile_key": "account_proxy",
                    "resource_dependency_mode": "required",
                    "required_capabilities": ("account", "proxy"),
                    "evidence_refs": ("fr-0027:profile:content-detail-by-url-hybrid:account-proxy",),
                },
            ),
        },
    )


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
        self.assertEqual(results[0]["observed_capability"], "content_detail")
        self.assertEqual(results[1]["observed_capability"], "content_detail")
        self.assertEqual(adapter.last_request_capability, "content_detail")
        self.assertEqual(adapter.last_resource_bundle_capability, "content_detail")
        self.assertEqual(adapter.last_resource_slots, ("account",))

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

    def test_rejects_fr0027_none_resource_profile_rejected_by_current_truth(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        manifest["resource_requirement_declarations"] = _none_profile_resource_requirement_declarations()

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            validate_third_party_adapter_manifest(manifest)

        self.assertEqual(context.exception.code, "invalid_manifest_resource_requirement_declarations")
        self.assertEqual(context.exception.details["profile_key"], "none")

    def test_rejects_nested_provider_fields_in_result_contract(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        manifest["result_contract"] = {
            **manifest["result_contract"],
            "provider_offer": "must-not-pass",
        }

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            validate_third_party_adapter_manifest(manifest)

        self.assertEqual(context.exception.code, "invalid_result_contract")
        self.assertEqual(context.exception.details["field"], "result_contract")
        self.assertEqual(context.exception.details["forbidden_fields"], ("provider_offer",))

    def test_rejects_nested_provider_fields_in_error_mapping(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        manifest["error_mapping"] = {
            "content_not_found": {
                **manifest["error_mapping"]["content_not_found"],
                "provider_selector": "must-not-pass",
            },
        }

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            validate_third_party_adapter_manifest(manifest)

        self.assertEqual(context.exception.code, "invalid_error_mapping")
        self.assertEqual(context.exception.details["field"], "error_mapping.content_not_found")
        self.assertEqual(context.exception.details["forbidden_fields"], ("provider_selector",))

    def test_accepts_adapter_metadata_sets_with_different_ordering(self) -> None:
        results = run_third_party_adapter_contract_test(
            manifest=minimal_third_party_adapter_manifest(),
            fixtures=minimal_third_party_adapter_fixtures(),
            adapter=AdapterWithReorderedPublicMetadata(),
        )

        self.assertEqual(results[0]["verdict"], "pass")
        self.assertEqual(results[1]["verdict"], "legal_failure")

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
            "provider_selection",
            "provider_capabilities",
            "external_provider_ref",
            "native_provider",
            "browser_provider",
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

    def test_rejects_provider_fields_in_resource_declarations_fail_closed(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        declarations = copy.deepcopy(manifest["resource_requirement_declarations"])
        declarations[0]["native_provider"] = "must-not-pass"
        manifest["resource_requirement_declarations"] = declarations

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            validate_third_party_adapter_manifest(manifest)

        self.assertEqual(context.exception.code, "invalid_manifest_resource_requirement_declarations")
        self.assertEqual(context.exception.details["forbidden_fields"], ("native_provider",))

    def test_rejects_sdk_contract_id_with_provider_or_compatibility_case_insensitive(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        manifest["sdk_contract_id"] = "Syvert-Adapter-Provider-Compatibility-v0.8.0"

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            validate_third_party_adapter_manifest(manifest)

        self.assertEqual(context.exception.code, "invalid_manifest_public_metadata")
        self.assertEqual(context.exception.details["field"], "sdk_contract_id")

    def test_rejects_adapter_key_with_provider_account_or_runtime_strategy_semantics(self) -> None:
        invalid_adapter_keys = (
            "provider-xhs",
            "xhs-prod-account-1",
            "xhs-selector-fallback",
            "xhsadapter",
            "douyinadapter",
            "xiaohongshu_adapter",
            "communityxhscontent",
            "communitydouyincontent",
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

    def test_rejects_error_mapping_category_not_preserved_by_runtime(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        manifest["error_mapping"] = {
            "content_not_found": {
                "category": "unsupported",
                "code": "content_not_found",
                "message": "content is unavailable or deleted",
            },
        }

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            validate_third_party_adapter_manifest(manifest)

        self.assertEqual(context.exception.code, "invalid_error_mapping")
        self.assertEqual(context.exception.details["category"], "unsupported")

    def test_rejects_mapping_where_manifest_requires_explicit_sequence(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        manifest["supported_capabilities"] = {"content_detail": True}

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            validate_third_party_adapter_manifest(manifest)

        self.assertEqual(context.exception.code, "invalid_manifest_public_metadata")
        self.assertEqual(context.exception.details["field"], "supported_capabilities")
        self.assertEqual(context.exception.details["actual_type"], "dict")

    def test_rejects_third_party_adapter_key_without_matching_resource_proof_admission(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        manifest["resource_proof_admission_refs"] = ()
        manifest["resource_proof_admissions"] = ()

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            validate_third_party_adapter_manifest(manifest)

        self.assertEqual(context.exception.code, "invalid_manifest_resource_requirement_declarations")
        self.assertEqual(context.exception.details["adapter_key"], THIRD_PARTY_FIXTURE_ADAPTER_KEY)
        self.assertEqual(context.exception.details["reference_adapters"], ("xhs", "douyin"))
        self.assertEqual(context.exception.details["matching_admission_count"], 0)

    def test_rejects_resource_proof_admission_evidence_outside_current_contract_entry(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        admissions = copy.deepcopy(manifest["resource_proof_admissions"])
        admissions[0]["admission_evidence_refs"] = (
            *admissions[0]["admission_evidence_refs"],
            "fr-0023:fixture:other_adapter:third-party-content-detail-success",
        )
        manifest["resource_proof_admissions"] = admissions

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=manifest,
                fixtures=minimal_third_party_adapter_fixtures(),
                adapter=ThirdPartyContractFixtureAdapter(),
            )

        self.assertEqual(context.exception.code, "invalid_manifest_resource_requirement_declarations")
        self.assertEqual(
            context.exception.details["evidence_ref"],
            "fr-0023:fixture:other_adapter:third-party-content-detail-success",
        )

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

    def test_rejects_manifest_public_metadata_not_covered_by_fixtures(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        manifest["supported_targets"] = ("url", "user_id")
        manifest["supported_collection_modes"] = ("hybrid", "public")

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=manifest,
                fixtures=minimal_third_party_adapter_fixtures(),
                adapter=AdapterWithOverclaimedTargetAndMode(),
            )

        self.assertEqual(context.exception.code, "invalid_fixture_metadata_coverage")
        self.assertEqual(context.exception.details["missing_targets"], ("user_id",))
        self.assertEqual(context.exception.details["missing_collection_modes"], ("public",))

    def test_rejects_fixture_input_provider_fields_fail_closed(self) -> None:
        fixtures = copy.deepcopy(minimal_third_party_adapter_fixtures())
        fixtures[0]["input"]["provider_selector"] = "must-not-pass"

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=minimal_third_party_adapter_manifest(),
                fixtures=fixtures,
                adapter=ThirdPartyContractFixtureAdapter(),
            )

        self.assertEqual(context.exception.code, "invalid_fixture_input")
        self.assertEqual(context.exception.details["field"], "fixture.input")
        self.assertEqual(context.exception.details["forbidden_fields"], ("provider_selector",))

    def test_rejects_fixture_expected_provider_fields_fail_closed(self) -> None:
        fixtures = copy.deepcopy(minimal_third_party_adapter_fixtures())
        fixtures[0]["expected"]["provider_offer"] = "must-not-pass"

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=minimal_third_party_adapter_manifest(),
                fixtures=fixtures,
                adapter=ThirdPartyContractFixtureAdapter(),
            )

        self.assertEqual(context.exception.code, "invalid_fixture_expected_contract")
        self.assertEqual(context.exception.details["field"], "fixture.expected")
        self.assertEqual(context.exception.details["forbidden_fields"], ("provider_offer",))

    def test_rejects_fixture_expected_error_provider_fields_fail_closed(self) -> None:
        fixtures = copy.deepcopy(minimal_third_party_adapter_fixtures())
        fixtures[1]["expected"]["error"]["provider_key"] = "must-not-pass"

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=minimal_third_party_adapter_manifest(),
                fixtures=fixtures,
                adapter=ThirdPartyContractFixtureAdapter(),
            )

        self.assertEqual(context.exception.code, "invalid_fixture_expected_contract")
        self.assertEqual(context.exception.details["field"], "fixture.expected.error")
        self.assertEqual(context.exception.details["forbidden_fields"], ("provider_key",))

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
        self.assertEqual(context.exception.details["field"], "fixture.input")
        self.assertEqual(context.exception.details["missing_fields"], ("resource_profile_key",))

    def test_rejects_invalid_resource_profile_before_adapter_execute(self) -> None:
        fixtures = copy.deepcopy(minimal_third_party_adapter_fixtures())
        fixtures[1]["input"]["resource_profile_key"] = "missing-profile"
        adapter = AdapterWithCallCount()

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=minimal_third_party_adapter_manifest(),
                fixtures=fixtures,
                adapter=adapter,
            )

        self.assertEqual(context.exception.code, "invalid_fixture_resource_profile")
        self.assertEqual(context.exception.details["fixture_id"], THIRD_PARTY_ERROR_MAPPING_FIXTURE_ID)
        self.assertEqual(adapter.execute_calls, 0)

    def test_rejects_declared_resource_profile_not_exercised_by_fixtures(self) -> None:
        fixtures = copy.deepcopy(minimal_third_party_adapter_fixtures())
        fixtures[1]["input"]["resource_profile_key"] = "account_proxy"

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=minimal_third_party_adapter_manifest(),
                fixtures=fixtures,
                adapter=ThirdPartyContractFixtureAdapter(),
            )

        self.assertEqual(context.exception.code, "invalid_fixture_resource_profile")
        self.assertEqual(context.exception.details["missing_profiles"], (("content_detail", "account"),))

    def test_rejects_resource_profile_proof_path_mismatch_before_adapter_execute(self) -> None:
        manifest = minimal_third_party_adapter_manifest()
        manifest["supported_collection_modes"] = ("hybrid", "public")
        fixtures = copy.deepcopy(minimal_third_party_adapter_fixtures())
        fixtures[1]["input"]["collection_mode"] = "public"
        adapter = AdapterWithCallCount()

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=manifest,
                fixtures=fixtures,
                adapter=adapter,
            )

        self.assertEqual(context.exception.code, "invalid_fixture_resource_profile")
        self.assertEqual(context.exception.details["fixture_id"], THIRD_PARTY_ERROR_MAPPING_FIXTURE_ID)
        self.assertEqual(adapter.execute_calls, 0)

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

    def test_rejects_extended_adapter_public_metadata_provider_facing_fields(self) -> None:
        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=minimal_third_party_adapter_manifest(),
                fixtures=minimal_third_party_adapter_fixtures(),
                adapter=AdapterWithExtendedProviderFacingMetadata(),
            )

        self.assertEqual(context.exception.code, "forbidden_adapter_public_metadata_fields")
        self.assertEqual(
            context.exception.details["forbidden_fields"],
            (
                "browser_provider",
                "external_provider_ref",
                "native_provider",
                "provider_capabilities",
                "provider_selection",
            ),
        )

    def test_rejects_invalid_adapter_fixture_refs_without_unhandled_exception(self) -> None:
        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=minimal_third_party_adapter_manifest(),
                fixtures=minimal_third_party_adapter_fixtures(),
                adapter=AdapterWithInvalidFixtureRefs(),
            )

        self.assertEqual(context.exception.code, "adapter_manifest_metadata_mismatch")
        fixture_ref_mismatch = context.exception.details["mismatches"]["fixture_refs"]
        self.assertEqual(fixture_ref_mismatch["actual"], "invalid")
        self.assertEqual(fixture_ref_mismatch["error_code"], "invalid_manifest_public_metadata")

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

    def test_rejects_fixture_top_level_non_string_field_names(self) -> None:
        fixtures = list(copy.deepcopy(minimal_third_party_adapter_fixtures()))
        fixtures[0][1] = "must-not-pass"

        with self.assertRaises(ThirdPartyContractEntryError) as context:
            run_third_party_adapter_contract_test(
                manifest=minimal_third_party_adapter_manifest(),
                fixtures=fixtures,
                adapter=ThirdPartyContractFixtureAdapter(),
            )

        self.assertEqual(context.exception.code, "invalid_fixture_shape")
        self.assertIn("1", context.exception.details["actual_keys"])

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

    def test_reports_reserved_runtime_fields_in_success_payload_as_contract_violation(self) -> None:
        results = run_third_party_adapter_contract_test(
            manifest=minimal_third_party_adapter_manifest(),
            fixtures=minimal_third_party_adapter_fixtures(),
            adapter=ThirdPartyContractFixtureAdapter(success_payload_shape="reserved_runtime_fields"),
        )

        success_result = results[0]
        self.assertEqual(success_result["sample_id"], THIRD_PARTY_SUCCESS_FIXTURE_ID)
        self.assertEqual(success_result["verdict"], "contract_violation")
        self.assertEqual(success_result["reason"]["code"], "unexpected_failed_envelope")
        self.assertEqual(success_result["observed_error"]["category"], "runtime_contract")
        self.assertEqual(success_result["observed_error"]["code"], "adapter_payload_reserved_runtime_fields")
        self.assertEqual(
            success_result["observed_error"]["details"]["reserved_fields"],
            ("adapter_key", "capability", "status"),
        )

    def test_reports_success_payload_that_ignores_fixture_target_as_contract_violation(self) -> None:
        results = run_third_party_adapter_contract_test(
            manifest=minimal_third_party_adapter_manifest(),
            fixtures=minimal_third_party_adapter_fixtures(),
            adapter=ThirdPartyContractFixtureAdapter(success_payload_shape="static_target"),
        )

        success_result = results[0]
        self.assertEqual(success_result["sample_id"], THIRD_PARTY_SUCCESS_FIXTURE_ID)
        self.assertEqual(success_result["verdict"], "contract_violation")
        self.assertEqual(success_result["reason"]["code"], "success_payload_target_mismatch")

    def test_reports_unexpected_adapter_exception_as_structured_contract_violation(self) -> None:
        results = run_third_party_adapter_contract_test(
            manifest=minimal_third_party_adapter_manifest(),
            fixtures=minimal_third_party_adapter_fixtures(),
            adapter=AdapterWithUnexpectedException(),
        )

        success_result = results[0]
        self.assertEqual(success_result["sample_id"], THIRD_PARTY_SUCCESS_FIXTURE_ID)
        self.assertEqual(success_result["verdict"], "contract_violation")
        self.assertEqual(success_result["reason"]["code"], "unexpected_failed_envelope")
        self.assertEqual(success_result["observed_error"]["category"], "runtime_contract")
        self.assertEqual(success_result["observed_error"]["code"], "adapter_execution_exception")

    def test_reports_platform_adapter_error_with_none_details_as_structured_contract_violation(self) -> None:
        results = run_third_party_adapter_contract_test(
            manifest=minimal_third_party_adapter_manifest(),
            fixtures=minimal_third_party_adapter_fixtures(),
            adapter=AdapterWithInvalidPlatformErrorDetails(details=None),
        )

        success_result = results[0]
        error_result = results[1]
        self.assertEqual(success_result["verdict"], "contract_violation")
        self.assertEqual(success_result["reason"]["code"], "unexpected_failed_envelope")
        self.assertEqual(success_result["observed_error"]["category"], "runtime_contract")
        self.assertEqual(success_result["observed_error"]["code"], "adapter_platform_error_details_invalid")
        self.assertEqual(success_result["observed_error"]["details"]["details_type"], "NoneType")
        self.assertEqual(error_result["verdict"], "contract_violation")
        self.assertEqual(error_result["reason"]["code"], "runtime_contract_failure_observed")

    def test_reports_platform_adapter_error_with_non_mapping_details_as_structured_contract_violation(self) -> None:
        results = run_third_party_adapter_contract_test(
            manifest=minimal_third_party_adapter_manifest(),
            fixtures=minimal_third_party_adapter_fixtures(),
            adapter=AdapterWithInvalidPlatformErrorDetails(details=("not", "mapping")),
        )

        success_result = results[0]
        self.assertEqual(success_result["verdict"], "contract_violation")
        self.assertEqual(success_result["observed_error"]["category"], "runtime_contract")
        self.assertEqual(success_result["observed_error"]["code"], "adapter_platform_error_details_invalid")
        self.assertEqual(success_result["observed_error"]["details"]["details_type"], "tuple")

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

    def test_reports_adapter_error_mapping_source_error_mismatch(self) -> None:
        results = run_third_party_adapter_contract_test(
            manifest=minimal_third_party_adapter_manifest(),
            fixtures=minimal_third_party_adapter_fixtures(),
            adapter=AdapterWithMismatchedSourceErrorDetails(),
        )

        success_result = results[0]
        error_result = results[1]
        self.assertEqual(success_result["verdict"], "pass")
        self.assertEqual(error_result["sample_id"], THIRD_PARTY_ERROR_MAPPING_FIXTURE_ID)
        self.assertEqual(error_result["verdict"], "contract_violation")
        self.assertEqual(error_result["reason"]["code"], "error_mapping_source_error_mismatch")

    def test_reports_adapter_error_mapping_message_mismatch(self) -> None:
        results = run_third_party_adapter_contract_test(
            manifest=minimal_third_party_adapter_manifest(),
            fixtures=minimal_third_party_adapter_fixtures(),
            adapter=AdapterWithMismatchedErrorMessage(),
        )

        error_result = results[1]
        self.assertEqual(error_result["sample_id"], THIRD_PARTY_ERROR_MAPPING_FIXTURE_ID)
        self.assertEqual(error_result["verdict"], "contract_violation")
        self.assertEqual(error_result["reason"]["code"], "error_mapping_mismatch")

    def test_normalizes_platform_adapter_error_category_through_runtime_classifier(self) -> None:
        results = run_third_party_adapter_contract_test(
            manifest=minimal_third_party_adapter_manifest(),
            fixtures=minimal_third_party_adapter_fixtures(),
            adapter=AdapterWithUnsupportedCategoryPlatformError(),
        )

        error_result = results[1]
        self.assertEqual(error_result["verdict"], "legal_failure")
        self.assertEqual(error_result["observed_error"]["category"], "platform")


if __name__ == "__main__":
    unittest.main()
