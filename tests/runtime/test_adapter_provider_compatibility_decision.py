from __future__ import annotations

import unittest

from syvert.adapter_provider_compatibility_decision import (
    COMPATIBILITY_DECISION_ERROR_INVALID_COMPATIBILITY_CONTRACT,
    COMPATIBILITY_DECISION_ERROR_INVALID_PROVIDER_OFFER_CONTRACT,
    COMPATIBILITY_DECISION_ERROR_INVALID_REQUIREMENT_CONTRACT,
    COMPATIBILITY_DECISION_ERROR_PROVIDER_LEAKAGE_DETECTED,
    COMPATIBILITY_DECISION_STATUS_INVALID_CONTRACT,
    COMPATIBILITY_DECISION_STATUS_MATCHED,
    COMPATIBILITY_DECISION_STATUS_UNMATCHED,
    AdapterProviderCompatibilityDecisionInput,
    baseline_compatibility_decision_context,
    decide_adapter_provider_compatibility,
    project_compatibility_decision_for_core,
)
from tests.runtime.adapter_provider_compatibility_decision_fixtures import (
    copy_decision_input,
    valid_compatibility_decision_input,
)


class AdapterProviderCompatibilityDecisionTests(unittest.TestCase):
    def test_decision_returns_matched_for_legal_requirement_and_offer_profile_tuple_intersection(self) -> None:
        decision = decide_adapter_provider_compatibility(valid_compatibility_decision_input())

        self.assertEqual(decision.decision_status, COMPATIBILITY_DECISION_STATUS_MATCHED)
        self.assertEqual(decision.adapter_key, "xhs")
        self.assertEqual(decision.capability, "content_detail")
        self.assertEqual(decision.execution_slice.operation, "content_detail_by_url")
        self.assertEqual(decision.error, None)
        self.assertEqual(
            tuple(profile.requirement_profile_key for profile in decision.matched_profiles),
            ("account_proxy", "account"),
        )
        self.assertEqual(
            tuple(profile.offer_profile_key for profile in decision.matched_profiles),
            ("account_proxy", "account"),
        )
        self.assertEqual(
            tuple(
                (
                    profile.resource_dependency_mode,
                    profile.required_capabilities,
                    profile.requirement_profile_evidence_ref,
                    profile.offer_profile_evidence_ref,
                )
                for profile in decision.matched_profiles
            ),
            (
                (
                    "required",
                    ("account", "proxy"),
                    "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                    "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                ),
                (
                    "required",
                    ("account",),
                    "fr-0027:profile:content-detail-by-url-hybrid:account",
                    "fr-0027:profile:content-detail-by-url-hybrid:account",
                ),
            ),
        )
        self.assertEqual(
            decision.evidence.resource_profile_evidence_refs,
            (
                "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                "fr-0027:profile:content-detail-by-url-hybrid:account",
            ),
        )
        self.assertEqual(decision.observability.proof_refs, decision.evidence.resource_profile_evidence_refs)
        self.assertEqual(decision.observability.matched_profile_keys, ("account_proxy", "account"))
        self.assertEqual(
            decision.evidence.adapter_bound_provider_evidence.provider_key,
            "native_xhs_detail",
        )
        self.assert_no_provider_leakage(decision)

    def test_decision_accepts_canonical_input_dataclass(self) -> None:
        raw_input = valid_compatibility_decision_input(adapter_key="douyin", provider_key="native_douyin_detail")
        decision = decide_adapter_provider_compatibility(
            AdapterProviderCompatibilityDecisionInput(
                requirement=raw_input["requirement"],
                offer=raw_input["offer"],
                decision_context=baseline_compatibility_decision_context(decision_id="opaque-decision-002"),
            )
        )

        self.assertEqual(decision.decision_status, COMPATIBILITY_DECISION_STATUS_MATCHED)
        self.assertEqual(decision.decision_id, "opaque-decision-002")
        self.assertEqual(decision.adapter_key, "douyin")
        self.assert_no_provider_leakage(decision)

    def test_decision_returns_unmatched_when_legal_inputs_have_no_profile_tuple_intersection(self) -> None:
        input_value = copy_decision_input()
        offer = input_value["offer"]
        offer["resource_support"]["supported_profiles"] = [offer["resource_support"]["supported_profiles"][1]]
        offer["evidence"]["resource_profile_evidence_refs"] = [
            "fr-0027:profile:content-detail-by-url-hybrid:account"
        ]
        offer["observability"]["profile_keys"] = ["account"]
        offer["observability"]["proof_refs"] = ["fr-0027:profile:content-detail-by-url-hybrid:account"]
        requirement = input_value["requirement"]
        requirement["resource_requirement"]["resource_requirement_profiles"] = [
            requirement["resource_requirement"]["resource_requirement_profiles"][0]
        ]
        requirement["evidence"]["resource_profile_evidence_refs"] = [
            "fr-0027:profile:content-detail-by-url-hybrid:account-proxy"
        ]
        requirement["observability"]["profile_keys"] = ["account_proxy"]
        requirement["observability"]["proof_refs"] = [
            "fr-0027:profile:content-detail-by-url-hybrid:account-proxy"
        ]

        decision = decide_adapter_provider_compatibility(input_value)

        self.assertEqual(decision.decision_status, COMPATIBILITY_DECISION_STATUS_UNMATCHED)
        self.assertEqual(decision.error, None)
        self.assertEqual(decision.matched_profiles, ())
        self.assertEqual(
            decision.evidence.resource_profile_evidence_refs,
            (
                "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                "fr-0027:profile:content-detail-by-url-hybrid:account",
            ),
        )
        self.assertEqual(decision.observability.proof_refs, decision.evidence.resource_profile_evidence_refs)
        self.assert_no_provider_leakage(decision)

    def test_decision_uses_canonical_tuple_not_profile_key_for_unmatched(self) -> None:
        input_value = copy_decision_input()
        requirement = input_value["requirement"]
        requirement["resource_requirement"]["resource_requirement_profiles"] = [
            requirement["resource_requirement"]["resource_requirement_profiles"][0]
        ]
        requirement["evidence"]["resource_profile_evidence_refs"] = [
            "fr-0027:profile:content-detail-by-url-hybrid:account-proxy"
        ]
        requirement["observability"]["profile_keys"] = ["account_proxy"]
        requirement["observability"]["proof_refs"] = [
            "fr-0027:profile:content-detail-by-url-hybrid:account-proxy"
        ]
        offer = input_value["offer"]
        offer["resource_support"]["supported_profiles"] = [
            {
                "profile_key": "account_proxy",
                "resource_dependency_mode": "required",
                "required_capabilities": ["account"],
                "evidence_refs": ["fr-0027:profile:content-detail-by-url-hybrid:account"],
            }
        ]
        offer["evidence"]["resource_profile_evidence_refs"] = [
            "fr-0027:profile:content-detail-by-url-hybrid:account"
        ]
        offer["observability"]["profile_keys"] = ["account_proxy"]
        offer["observability"]["proof_refs"] = ["fr-0027:profile:content-detail-by-url-hybrid:account"]

        decision = decide_adapter_provider_compatibility(input_value)

        self.assertEqual(decision.decision_status, COMPATIBILITY_DECISION_STATUS_UNMATCHED)
        self.assertEqual(decision.matched_profiles, ())
        self.assertEqual(
            decision.evidence.resource_profile_evidence_refs,
            (
                "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                "fr-0027:profile:content-detail-by-url-hybrid:account",
            ),
        )
        self.assert_no_provider_leakage(decision)

    def test_decision_returns_invalid_contract_for_invalid_requirement_without_routing(self) -> None:
        input_value = copy_decision_input()
        input_value["requirement"]["fail_closed"] = False

        decision = decide_adapter_provider_compatibility(input_value)

        self.assert_invalid(decision, COMPATIBILITY_DECISION_ERROR_INVALID_REQUIREMENT_CONTRACT)
        self.assertEqual(decision.error.source_contract_ref, "FR-0024")
        self.assertEqual(decision.evidence.adapter_bound_provider_evidence.provider_key, "native_xhs_detail")
        self.assert_no_provider_leakage(decision)

    def test_decision_returns_invalid_contract_for_invalid_offer_without_routing(self) -> None:
        input_value = copy_decision_input()
        input_value["offer"]["fail_closed"] = False

        decision = decide_adapter_provider_compatibility(input_value)

        self.assert_invalid(decision, COMPATIBILITY_DECISION_ERROR_INVALID_PROVIDER_OFFER_CONTRACT)
        self.assertEqual(decision.error.source_contract_ref, "FR-0025")
        self.assert_no_provider_leakage(decision)

    def test_decision_returns_invalid_contract_for_cross_adapter_offer(self) -> None:
        input_value = copy_decision_input()
        input_value["offer"] = valid_compatibility_decision_input(
            adapter_key="douyin",
            provider_key="native_douyin_detail",
        )["offer"]

        decision = decide_adapter_provider_compatibility(input_value)

        self.assert_invalid(decision, COMPATIBILITY_DECISION_ERROR_INVALID_COMPATIBILITY_CONTRACT)
        self.assertEqual(decision.adapter_key, None)
        self.assertEqual(
            decision.evidence.invalid_contract_evidence.observed_values["requirement_adapter_key"],
            "xhs",
        )
        self.assertEqual(
            decision.evidence.invalid_contract_evidence.observed_values["offer_adapter_key"],
            "douyin",
        )
        self.assertEqual(
            decision.evidence.resource_profile_evidence_refs,
            (
                "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                "fr-0027:profile:content-detail-by-url-hybrid:account",
            ),
        )
        self.assertEqual(decision.evidence.invalid_contract_evidence.unresolved_refs, ())
        self.assert_no_provider_leakage(decision)

    def test_decision_returns_invalid_contract_for_offer_execution_slice_mismatch(self) -> None:
        input_value = copy_decision_input()
        input_value["offer"]["capability_offer"]["operation"] = "search_by_keyword"

        decision = decide_adapter_provider_compatibility(input_value)

        self.assert_invalid(decision, COMPATIBILITY_DECISION_ERROR_INVALID_PROVIDER_OFFER_CONTRACT)
        self.assertEqual(decision.error.source_contract_ref, "FR-0025")
        self.assert_no_provider_leakage(decision)

    def test_requirement_slice_and_capability_drift_fail_closed(self) -> None:
        cases = (
            ("capability", "search"),
            ("operation", "search_by_keyword"),
            ("target_type", "keyword"),
            ("collection_mode", "api_only"),
        )
        for field_name, value in cases:
            with self.subTest(field_name=field_name):
                input_value = copy_decision_input()
                if field_name == "capability":
                    input_value["requirement"]["capability"] = value
                else:
                    input_value["requirement"]["execution_requirement"][field_name] = value

                decision = decide_adapter_provider_compatibility(input_value)

                self.assert_invalid(decision, COMPATIBILITY_DECISION_ERROR_INVALID_REQUIREMENT_CONTRACT)
                self.assertEqual(decision.error.source_contract_ref, "FR-0024")
                self.assertEqual(decision.adapter_key, None)
                self.assertEqual(decision.capability, None)
                self.assertEqual(decision.execution_slice, None)
                self.assert_no_provider_leakage(decision)

    def test_offer_capability_slice_version_and_error_carrier_drift_fail_closed(self) -> None:
        cases = (
            ("capability_offer", "capability", "search"),
            ("capability_offer", "operation", "search_by_keyword"),
            ("capability_offer", "target_type", "keyword"),
            ("capability_offer", "collection_mode", "api_only"),
            ("version", "contract_version", "v0.9.0"),
            ("error_carrier", "adapter_mapping_required", False),
        )
        for section, field_name, value in cases:
            with self.subTest(section=section, field_name=field_name):
                input_value = copy_decision_input()
                input_value["offer"][section][field_name] = value

                decision = decide_adapter_provider_compatibility(input_value)

                self.assert_invalid(decision, COMPATIBILITY_DECISION_ERROR_INVALID_PROVIDER_OFFER_CONTRACT)
                self.assertEqual(decision.error.source_contract_ref, "FR-0025")
                self.assertEqual(decision.adapter_key, None)
                self.assertEqual(decision.capability, None)
                self.assertEqual(decision.execution_slice, None)
                self.assert_no_provider_leakage(decision)

    def test_decision_returns_invalid_contract_for_profile_proof_not_covering_adapter(self) -> None:
        input_value = copy_decision_input()
        input_value["requirement"] = valid_compatibility_decision_input(adapter_key="external_adapter")[
            "requirement"
        ]
        input_value["offer"] = valid_compatibility_decision_input(adapter_key="external_adapter")["offer"]
        input_value["offer"]["adapter_binding"]["provider_port_ref"] = (
            "external_adapter:adapter-owned-provider-port"
        )
        input_value["offer"]["observability"]["offer_id"] = (
            "external_adapter:native_xhs_detail:content_detail:content_detail_by_url:url:hybrid:v0.8.0"
        )
        input_value["offer"]["observability"]["adapter_key"] = "external_adapter"

        decision = decide_adapter_provider_compatibility(input_value)

        self.assertEqual(decision.decision_status, COMPATIBILITY_DECISION_STATUS_INVALID_CONTRACT)
        self.assertEqual(decision.error.error_code, COMPATIBILITY_DECISION_ERROR_INVALID_REQUIREMENT_CONTRACT)
        self.assertEqual(decision.error.source_contract_ref, "FR-0024")
        requirement_details = decision.evidence.invalid_contract_evidence.observed_values["requirement_details"]
        self.assertEqual(requirement_details["adapter_key"], "external_adapter")
        self.assertEqual(requirement_details["profile_key"], "account_proxy")
        self.assertEqual(
            decision.evidence.resource_profile_evidence_refs,
            (
                "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                "fr-0027:profile:content-detail-by-url-hybrid:account",
            ),
        )
        self.assertEqual(decision.evidence.invalid_contract_evidence.unresolved_refs, ())
        self.assertEqual(
            decision.evidence.invalid_contract_evidence.resolved_profile_evidence_refs,
            decision.evidence.resource_profile_evidence_refs,
        )
        self.assert_no_provider_leakage(decision)

    def test_decision_returns_invalid_contract_for_offer_profile_proof_not_covering_adapter(self) -> None:
        input_value = copy_decision_input()
        input_value["offer"] = valid_compatibility_decision_input(adapter_key="external_adapter")["offer"]
        input_value["offer"]["adapter_binding"]["provider_port_ref"] = (
            "external_adapter:adapter-owned-provider-port"
        )
        input_value["offer"]["observability"]["offer_id"] = (
            "external_adapter:native_xhs_detail:content_detail:content_detail_by_url:url:hybrid:v0.8.0"
        )
        input_value["offer"]["observability"]["adapter_key"] = "external_adapter"

        decision = decide_adapter_provider_compatibility(input_value)

        self.assert_invalid(decision, COMPATIBILITY_DECISION_ERROR_INVALID_PROVIDER_OFFER_CONTRACT)
        self.assertEqual(decision.error.source_contract_ref, "FR-0025")
        offer_details = decision.evidence.invalid_contract_evidence.observed_values["offer_details"]
        self.assertEqual(offer_details["adapter_key"], "external_adapter")
        self.assertEqual(offer_details["reference_adapters"], ("xhs", "douyin"))
        self.assertEqual(
            decision.evidence.invalid_contract_evidence.resolved_profile_evidence_refs,
            (
                "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                "fr-0027:profile:content-detail-by-url-hybrid:account",
            ),
        )
        self.assertEqual(
            decision.evidence.resource_profile_evidence_refs,
            (
                "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                "fr-0027:profile:content-detail-by-url-hybrid:account",
            ),
        )
        self.assertEqual(decision.evidence.invalid_contract_evidence.unresolved_refs, ())
        self.assert_no_provider_leakage(decision)

    def test_decision_returns_provider_leakage_for_decision_context_selector_or_priority(self) -> None:
        cases = (
            ("provider_selector", "native_xhs_detail"),
            ("priority", 1),
            ("fallback_order", ["native_xhs_detail"]),
            ("routing_policy", "try-provider"),
        )
        for field_name, value in cases:
            with self.subTest(field_name=field_name):
                input_value = copy_decision_input()
                input_value["decision_context"][field_name] = value

                decision = decide_adapter_provider_compatibility(input_value)

                self.assert_invalid(decision, COMPATIBILITY_DECISION_ERROR_PROVIDER_LEAKAGE_DETECTED)
                self.assertEqual(decision.error.source_contract_ref, "FR-0026")
                self.assert_no_provider_leakage(decision)

    def test_decision_returns_provider_leakage_for_top_level_input_drift(self) -> None:
        cases = (
            ("priority", 1),
            ("routing_policy", "try-provider"),
            ("selected_provider", "native_xhs_detail"),
            ("fallback_order", ["native_xhs_detail"]),
        )
        for field_name, value in cases:
            with self.subTest(field_name=field_name):
                input_value = copy_decision_input()
                input_value[field_name] = value

                decision = decide_adapter_provider_compatibility(input_value)

                self.assert_invalid(decision, COMPATIBILITY_DECISION_ERROR_PROVIDER_LEAKAGE_DETECTED)
                self.assertEqual(decision.error.source_contract_ref, "FR-0026")
                self.assertEqual(
                    decision.evidence.invalid_contract_evidence.observed_values["extra_fields"],
                    (field_name,),
                )
                self.assert_no_provider_leakage(decision)

    def test_decision_rejects_provider_derived_decision_id_before_core_projection(self) -> None:
        cases = (
            "xhs:native_xhs_detail:content_detail:content_detail_by_url:url:hybrid:v0.8.0",
            "native-xhs-detail",
        )
        for decision_id in cases:
            with self.subTest(decision_id=decision_id):
                input_value = copy_decision_input()
                input_value["decision_context"]["decision_id"] = decision_id

                decision = decide_adapter_provider_compatibility(input_value)
                projection = project_compatibility_decision_for_core(decision)

                self.assert_invalid(decision, COMPATIBILITY_DECISION_ERROR_PROVIDER_LEAKAGE_DETECTED)
                self.assertEqual(decision.error.source_contract_ref, "FR-0026")
                self.assertEqual(projection["decision_status"], COMPATIBILITY_DECISION_STATUS_INVALID_CONTRACT)
                self.assertEqual(projection["adapter_key"], None)
                self.assert_no_provider_leakage(decision)

    def test_malformed_decision_context_fails_closed(self) -> None:
        cases = (None, "invalid-context")
        for raw_context in cases:
            with self.subTest(raw_context=raw_context):
                input_value = copy_decision_input()
                input_value["decision_context"] = raw_context

                decision = decide_adapter_provider_compatibility(input_value)

                self.assert_invalid(decision, COMPATIBILITY_DECISION_ERROR_INVALID_COMPATIBILITY_CONTRACT)
                self.assertEqual(decision.error.source_contract_ref, "FR-0026")
                self.assertEqual(decision.adapter_key, None)
                self.assert_no_provider_leakage(decision)

    def test_invalid_unknown_profile_proof_is_unresolved_not_resolved(self) -> None:
        input_value = copy_decision_input()
        unknown_ref = "fr-0027:profile:content-detail-by-url-hybrid:unknown"
        input_value["requirement"]["resource_requirement"]["resource_requirement_profiles"][0][
            "evidence_refs"
        ] = [unknown_ref]
        input_value["requirement"]["evidence"]["resource_profile_evidence_refs"][0] = unknown_ref
        input_value["requirement"]["observability"]["proof_refs"][0] = unknown_ref

        decision = decide_adapter_provider_compatibility(input_value)

        self.assert_invalid(decision, COMPATIBILITY_DECISION_ERROR_INVALID_REQUIREMENT_CONTRACT)
        self.assertIn(unknown_ref, decision.evidence.invalid_contract_evidence.unresolved_refs)
        self.assertNotIn(unknown_ref, decision.evidence.resource_profile_evidence_refs)
        self.assertNotIn(unknown_ref, decision.evidence.invalid_contract_evidence.resolved_profile_evidence_refs)
        self.assert_no_provider_leakage(decision)

    def test_invalid_duplicate_profile_proof_is_unresolved_not_resolved(self) -> None:
        input_value = copy_decision_input()
        duplicate_ref = "fr-0027:profile:content-detail-by-url-hybrid:account"
        input_value["requirement"]["resource_requirement"]["resource_requirement_profiles"][0][
            "evidence_refs"
        ] = [duplicate_ref]
        input_value["requirement"]["evidence"]["resource_profile_evidence_refs"] = [
            duplicate_ref,
            duplicate_ref,
        ]
        input_value["requirement"]["observability"]["proof_refs"] = [
            duplicate_ref,
            duplicate_ref,
        ]

        decision = decide_adapter_provider_compatibility(input_value)

        self.assert_invalid(decision, COMPATIBILITY_DECISION_ERROR_INVALID_REQUIREMENT_CONTRACT)
        self.assertIn(duplicate_ref, decision.evidence.invalid_contract_evidence.unresolved_refs)
        self.assertNotIn(duplicate_ref, decision.evidence.resource_profile_evidence_refs)
        self.assert_no_provider_leakage(decision)

    def test_decision_context_drift_is_attributed_to_fr0026(self) -> None:
        input_value = copy_decision_input()
        input_value["decision_context"]["contract_version"] = "v0.9.0"

        decision = decide_adapter_provider_compatibility(input_value)

        self.assert_invalid(decision, COMPATIBILITY_DECISION_ERROR_INVALID_COMPATIBILITY_CONTRACT)
        self.assertEqual(decision.error.source_contract_ref, "FR-0026")
        self.assert_no_provider_leakage(decision)

    def test_core_projection_is_fail_closed_and_does_not_leak_provider_routing_fields(self) -> None:
        decision = decide_adapter_provider_compatibility(valid_compatibility_decision_input())

        projection = project_compatibility_decision_for_core(decision)

        self.assertEqual(
            projection,
            {
                "decision_id": "compatibility-decision-001",
                "adapter_key": "xhs",
                "capability": "content_detail",
                "decision_status": "matched",
                "error_code": None,
                "failure_category": None,
                "fail_closed": True,
            },
        )
        self.assertNotIn("provider_key", projection)
        self.assertNotIn("offer_id", projection)
        self.assertNotIn("provider_routing", projection)
        self.assertNotIn("fallback", projection)

    def assert_invalid(self, decision, expected_error_code: str) -> None:
        self.assertEqual(decision.decision_status, COMPATIBILITY_DECISION_STATUS_INVALID_CONTRACT)
        self.assertEqual(decision.matched_profiles, ())
        self.assertIsNotNone(decision.error)
        self.assertEqual(decision.error.failure_category, "runtime_contract")
        self.assertEqual(decision.error.error_code, expected_error_code)
        self.assertEqual(decision.error.adapter_mapping_required, True)
        self.assertIsNotNone(decision.evidence.invalid_contract_evidence)
        self.assertEqual(decision.fail_closed, True)

    def assert_no_provider_leakage(self, decision) -> None:
        self.assertFalse(decision.no_leakage.core_registry_provider_fields_allowed)
        self.assertFalse(decision.no_leakage.core_routing_provider_fields_allowed)
        self.assertFalse(decision.no_leakage.task_record_provider_fields_allowed)
        self.assertFalse(decision.no_leakage.resource_lifecycle_provider_fields_allowed)
        self.assertTrue(decision.no_leakage.adapter_bound_evidence_provider_fields_allowed)
        self.assertFalse(hasattr(decision, "provider_key"))
        self.assertFalse(hasattr(decision, "offer_id"))
        self.assertFalse(hasattr(decision.observability, "provider_key"))
        self.assertFalse(hasattr(decision.observability, "offer_id"))


if __name__ == "__main__":
    unittest.main()
