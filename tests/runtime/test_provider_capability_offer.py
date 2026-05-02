from __future__ import annotations

import unittest

from syvert.provider_capability_offer import (
    PROVIDER_OFFER_ERROR_INVALID_OFFER,
    PROVIDER_OFFER_STATUS_DECLARED,
    PROVIDER_OFFER_STATUS_INVALID,
    ProviderAdapterBinding,
    ProviderCapabilityOffer,
    ProviderCapabilityOfferDescriptor,
    ProviderOfferErrorCarrier,
    ProviderOfferEvidence,
    ProviderOfferLifecycleExpectation,
    ProviderOfferObservabilityExpectation,
    ProviderOfferVersion,
    ProviderResourceSupport,
    ProviderSupportedResourceProfile,
    validate_provider_capability_offer,
)
from tests.runtime.provider_capability_offer_fixtures import copy_offer, valid_provider_capability_offer


class ProviderCapabilityOfferTests(unittest.TestCase):
    def test_validator_accepts_legal_offer_as_declared(self) -> None:
        result = validate_provider_capability_offer(valid_provider_capability_offer())

        self.assertEqual(result.status, PROVIDER_OFFER_STATUS_DECLARED)
        self.assertEqual(result.provider_key, "native_xhs_detail")
        self.assertEqual(result.adapter_key, "xhs")
        self.assertEqual(result.capability, "content_detail")
        self.assertEqual(result.error_code, None)
        self.assertEqual(
            result.details,
            {
                "validation_status": "declared",
                "offer_id": "xhs:native_xhs_detail:content_detail:content_detail_by_url:url:hybrid:v0.8.0",
            },
        )
        self.assertNotIn("compatibility_decision", result.details)
        self.assertNotIn("selected_provider", result.details)

    def test_validator_accepts_canonical_dataclass_offer(self) -> None:
        raw_offer = valid_provider_capability_offer(adapter_key="douyin", provider_key="native_douyin_detail")
        offer = ProviderCapabilityOffer(
            provider_key=raw_offer["provider_key"],
            adapter_binding=ProviderAdapterBinding(**raw_offer["adapter_binding"]),
            capability_offer=ProviderCapabilityOfferDescriptor(**raw_offer["capability_offer"]),
            resource_support=ProviderResourceSupport(
                supported_profiles=tuple(
                    ProviderSupportedResourceProfile(
                        profile_key=profile["profile_key"],
                        resource_dependency_mode=profile["resource_dependency_mode"],
                        required_capabilities=tuple(profile["required_capabilities"]),
                        evidence_refs=tuple(profile["evidence_refs"]),
                    )
                    for profile in raw_offer["resource_support"]["supported_profiles"]
                ),
                resource_profile_contract_ref=raw_offer["resource_support"]["resource_profile_contract_ref"],
            ),
            error_carrier=ProviderOfferErrorCarrier(**raw_offer["error_carrier"]),
            version=ProviderOfferVersion(**raw_offer["version"]),
            evidence=ProviderOfferEvidence(
                provider_offer_evidence_refs=tuple(raw_offer["evidence"]["provider_offer_evidence_refs"]),
                resource_profile_evidence_refs=tuple(raw_offer["evidence"]["resource_profile_evidence_refs"]),
                adapter_binding_evidence_refs=tuple(raw_offer["evidence"]["adapter_binding_evidence_refs"]),
            ),
            lifecycle=ProviderOfferLifecycleExpectation(**raw_offer["lifecycle"]),
            observability=ProviderOfferObservabilityExpectation(
                offer_id=raw_offer["observability"]["offer_id"],
                provider_key=raw_offer["observability"]["provider_key"],
                adapter_key=raw_offer["observability"]["adapter_key"],
                capability=raw_offer["observability"]["capability"],
                operation=raw_offer["observability"]["operation"],
                profile_keys=tuple(raw_offer["observability"]["profile_keys"]),
                proof_refs=tuple(raw_offer["observability"]["proof_refs"]),
                contract_version=raw_offer["observability"]["contract_version"],
                validation_outcome_fields=tuple(raw_offer["observability"]["validation_outcome_fields"]),
            ),
            fail_closed=raw_offer["fail_closed"],
        )

        result = validate_provider_capability_offer(offer)

        self.assertEqual(result.status, PROVIDER_OFFER_STATUS_DECLARED)
        self.assertEqual(result.adapter_key, "douyin")

    def test_validator_rejects_missing_required_field_as_invalid_provider_offer(self) -> None:
        offer = copy_offer()
        del offer["capability_offer"]

        result = validate_provider_capability_offer(offer)

        self.assert_invalid(result)
        self.assertEqual(result.details["missing_fields"], ("capability_offer",))

    def test_validator_rejects_fail_closed_not_true_as_invalid_provider_offer(self) -> None:
        offer = copy_offer()
        offer["fail_closed"] = False

        result = validate_provider_capability_offer(offer)

        self.assert_invalid(result)
        self.assertEqual(result.details["fail_closed"], False)

    def test_validator_rejects_provider_key_that_claims_global_or_core_identity(self) -> None:
        for provider_key in ("global_native_provider", "core_registry_provider", "marketplace_listing"):
            with self.subTest(provider_key=provider_key):
                offer = copy_offer(valid_provider_capability_offer(provider_key=provider_key))

                result = validate_provider_capability_offer(offer)

                self.assert_invalid(result)
                self.assertEqual(result.details["provider_key"], provider_key)

    def test_validator_rejects_adapter_binding_outside_adapter_bound_scope(self) -> None:
        offer = copy_offer()
        offer["adapter_binding"]["binding_scope"] = "core_bound"

        result = validate_provider_capability_offer(offer)

        self.assert_invalid(result)
        self.assertEqual(result.details["binding_scope"], "core_bound")

    def test_validator_rejects_capability_offer_outside_approved_slice(self) -> None:
        cases = (
            ("capability", "search"),
            ("operation", "search_by_keyword"),
            ("target_type", "keyword"),
            ("collection_mode", "api_only"),
        )
        for field_name, value in cases:
            with self.subTest(field_name=field_name, value=value):
                offer = copy_offer()
                offer["capability_offer"][field_name] = value

                result = validate_provider_capability_offer(offer)

                self.assert_invalid(result)

    def test_validator_rejects_proof_not_covering_adapter_binding(self) -> None:
        offer = copy_offer(valid_provider_capability_offer(adapter_key="external_adapter"))
        offer["adapter_binding"]["provider_port_ref"] = "external_adapter:adapter-owned-provider-port"
        offer["observability"]["offer_id"] = (
            "external_adapter:native_xhs_detail:content_detail:"
            "content_detail_by_url:url:hybrid:v0.8.0"
        )
        offer["observability"]["adapter_key"] = "external_adapter"

        result = validate_provider_capability_offer(offer)

        self.assert_invalid(result)
        self.assertEqual(result.details["adapter_key"], "external_adapter")
        self.assertEqual(result.details["reference_adapters"], ("xhs", "douyin"))

    def test_validator_rejects_unapproved_or_tuple_mismatched_profile_proof(self) -> None:
        offer = copy_offer()
        offer["resource_support"]["supported_profiles"][0]["evidence_refs"] = [
            "fr-0027:profile:content-detail-by-url-hybrid:proxy"
        ]
        offer["evidence"]["resource_profile_evidence_refs"][0] = "fr-0027:profile:content-detail-by-url-hybrid:proxy"
        offer["observability"]["proof_refs"][0] = "fr-0027:profile:content-detail-by-url-hybrid:proxy"

        result = validate_provider_capability_offer(offer)

        self.assert_invalid(result)
        self.assertEqual(
            result.details["proof_ref"],
            "fr-0027:profile:content-detail-by-url-hybrid:proxy",
        )

    def test_validator_rejects_resource_support_contract_ref_and_duplicate_profiles(self) -> None:
        offer = copy_offer()
        offer["resource_support"]["resource_profile_contract_ref"] = "FR-0015"

        result = validate_provider_capability_offer(offer)

        self.assert_invalid(result)
        self.assertEqual(result.details["resource_profile_contract_ref"], "FR-0015")

        offer = copy_offer()
        offer["resource_support"]["supported_profiles"][1]["profile_key"] = "account_proxy"

        result = validate_provider_capability_offer(offer)

        self.assert_invalid(result)
        self.assertEqual(result.details["profile_key"], "account_proxy")

        offer = copy_offer()
        offer["resource_support"]["supported_profiles"][1]["profile_key"] = "account_proxy_duplicate"
        offer["resource_support"]["supported_profiles"][1]["required_capabilities"] = ["proxy", "account"]
        offer["resource_support"]["supported_profiles"][1]["evidence_refs"] = [
            "fr-0027:profile:content-detail-by-url-hybrid:account-proxy"
        ]
        offer["evidence"]["resource_profile_evidence_refs"][1] = (
            "fr-0027:profile:content-detail-by-url-hybrid:account-proxy"
        )
        offer["observability"]["profile_keys"][1] = "account_proxy_duplicate"
        offer["observability"]["proof_refs"][1] = "fr-0027:profile:content-detail-by-url-hybrid:account-proxy"

        result = validate_provider_capability_offer(offer)

        self.assert_invalid(result)
        self.assertEqual(
            result.details["duplicate_value"],
            "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
        )

    def test_validator_rejects_resource_support_profile_priority_fallback_and_selection(self) -> None:
        cases = (
            ("priority", 1),
            ("fallback_order", ["account", "account_proxy"]),
            ("preferred_profile", "account"),
            ("selected_profile", "account_proxy"),
            ("provider_selection", "native"),
        )
        for field_name, value in cases:
            with self.subTest(field_name=field_name):
                offer = copy_offer()
                offer["resource_support"]["supported_profiles"][0][field_name] = value

                result = validate_provider_capability_offer(offer)

                self.assert_invalid(result)
                self.assertEqual(result.details["forbidden_fields"], (field_name,))

    def test_validator_rejects_top_level_decision_marketplace_core_routing_and_provider_leakage_fields(self) -> None:
        cases = (
            "compatibility_decision",
            "provider_selector",
            "provider_routing",
            "routing_policy",
            "core_routing",
            "core_provider_registry",
            "marketplace_listing",
            "provider_product_support",
            "task_record_provider_field",
        )
        for field_name in cases:
            with self.subTest(field_name=field_name):
                offer = copy_offer()
                offer[field_name] = "forbidden"

                result = validate_provider_capability_offer(offer)

                self.assert_invalid(result)
                self.assertEqual(result.details["forbidden_fields"], (field_name,))

    def test_validator_rejects_resource_profile_evidence_refs_that_do_not_match_profile_proofs(self) -> None:
        offer = copy_offer()
        offer["evidence"]["resource_profile_evidence_refs"] = [
            "fr-0027:profile:content-detail-by-url-hybrid:account",
            "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
        ]

        result = validate_provider_capability_offer(offer)

        self.assert_invalid(result)
        self.assertEqual(
            result.details["expected_resource_profile_evidence_refs"],
            (
                "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                "fr-0027:profile:content-detail-by-url-hybrid:account",
            ),
        )

    def test_validator_rejects_mapping_payloads_for_string_array_fields(self) -> None:
        cases = (
            ("resource_support", "supported_profiles", 0, "required_capabilities"),
            ("resource_support", "supported_profiles", 0, "evidence_refs"),
            ("evidence", "provider_offer_evidence_refs"),
            ("evidence", "resource_profile_evidence_refs"),
            ("evidence", "adapter_binding_evidence_refs"),
            ("observability", "profile_keys"),
            ("observability", "proof_refs"),
            ("observability", "validation_outcome_fields"),
        )
        for case in cases:
            with self.subTest(case=case):
                offer = copy_offer()
                if len(case) == 4:
                    section, list_name, index, field_name = case
                    offer[section][list_name][index][field_name] = {"account": True}
                else:
                    section, field_name = case
                    offer[section][field_name] = {"account": True}

                result = validate_provider_capability_offer(offer)

                self.assert_invalid(result)
                self.assertEqual(result.details["actual_type"], "dict")

    def test_validator_rejects_evidence_refs_outside_approved_categories(self) -> None:
        cases = (
            ("provider_offer_evidence_refs", "tmp:runtime-log"),
            ("adapter_binding_evidence_refs", "fr-0024:manifest-fixture-validator:requirement"),
        )
        for field_name, evidence_ref in cases:
            with self.subTest(field_name=field_name):
                offer = copy_offer()
                offer["evidence"][field_name] = [evidence_ref]

                result = validate_provider_capability_offer(offer)

                self.assert_invalid(result)
                self.assertEqual(result.details["unsupported_refs"], (evidence_ref,))

    def test_validator_rejects_error_carrier_version_and_lifecycle_drift(self) -> None:
        cases = (
            ("error_carrier", "invalid_offer_code", "invalid_contract"),
            ("error_carrier", "adapter_mapping_required", False),
            ("version", "contract_version", "v0.9.0"),
            ("version", "requirement_contract_ref", "FR-9999"),
            ("lifecycle", "invoked_by_adapter_only", False),
            ("lifecycle", "core_discovery_allowed", True),
            ("lifecycle", "uses_existing_resource_bundle_view", False),
            ("lifecycle", "adapter_error_mapping_required", False),
        )
        for section, field_name, value in cases:
            with self.subTest(section=section, field_name=field_name):
                offer = copy_offer()
                offer[section][field_name] = value

                result = validate_provider_capability_offer(offer)

                self.assert_invalid(result)

    def test_validator_rejects_observability_alignment_drift(self) -> None:
        cases = (
            ("offer_id", "xhs:native_xhs_detail:content_detail:content_detail_by_url:url:hybrid:v0.9.0"),
            ("provider_key", "other_provider"),
            ("adapter_key", "douyin"),
            ("capability", "search"),
            ("operation", "search_by_keyword"),
            ("contract_version", "v0.9.0"),
        )
        for field_name, value in cases:
            with self.subTest(field_name=field_name):
                offer = copy_offer()
                offer["observability"][field_name] = value

                result = validate_provider_capability_offer(offer)

                self.assert_invalid(result)

    def test_validator_rejects_observability_profile_proof_and_outcome_field_drift(self) -> None:
        cases = (
            ("profile_keys", ["account", "account_proxy"]),
            (
                "proof_refs",
                [
                    "fr-0027:profile:content-detail-by-url-hybrid:account",
                    "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                ],
            ),
            ("validation_outcome_fields", ["validation_status", "error_code"]),
            (
                "validation_outcome_fields",
                ["validation_status", "error_code", "failure_category", "compatibility_decision"],
            ),
        )
        for field_name, value in cases:
            with self.subTest(field_name=field_name):
                offer = copy_offer()
                offer["observability"][field_name] = value

                result = validate_provider_capability_offer(offer)

                self.assert_invalid(result)

    def test_validator_rejects_observability_selector_fallback_marketplace_and_technical_leakage(self) -> None:
        leaked_values = (
            "selectorOutcome",
            "routingPolicy",
            "fallbackResult",
            "marketplaceListing",
            "taskRecordProviderField",
            "browserProfile",
            "networkTier",
            "transportMode",
        )
        for leaked_value in leaked_values:
            with self.subTest(leaked_value=leaked_value):
                offer = copy_offer()
                offer["observability"]["profile_keys"] = ["account_proxy", leaked_value]

                result = validate_provider_capability_offer(offer)

                self.assert_invalid(result)

    def test_legal_offer_does_not_emit_compatibility_or_core_routing_fields(self) -> None:
        result = validate_provider_capability_offer(valid_provider_capability_offer())

        self.assertEqual(result.status, PROVIDER_OFFER_STATUS_DECLARED)
        self.assertNotIn("compatibility_status", result.details)
        self.assertNotIn("provider_routing", result.details)
        self.assertNotIn("core_routing", result.details)

    def assert_invalid(self, result) -> None:
        self.assertEqual(result.status, PROVIDER_OFFER_STATUS_INVALID)
        self.assertEqual(result.failure_category, "runtime_contract")
        self.assertEqual(result.error_code, PROVIDER_OFFER_ERROR_INVALID_OFFER)


if __name__ == "__main__":
    unittest.main()
