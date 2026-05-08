from __future__ import annotations

import unittest

from syvert.adapter_provider_compatibility_decision import (
    COMPATIBILITY_DECISION_STATUS_INVALID_CONTRACT,
    COMPATIBILITY_DECISION_STATUS_MATCHED,
    COMPATIBILITY_DECISION_STATUS_UNMATCHED,
    decide_adapter_provider_compatibility,
)
from syvert.provider_capability_offer import validate_provider_capability_offer
from syvert.real_provider_sample_evidence import (
    EXTERNAL_PROVIDER_KEY,
    build_adapter_bound_execution_evidence,
    build_core_surface_no_leakage_evidence,
    build_real_provider_sample_evidence_report,
    external_provider_capability_offer,
    external_provider_decision_input,
    external_provider_invalid_contract_decision_input,
    external_provider_unmatched_decision_input,
)


class RealProviderSampleEvidenceTests(unittest.TestCase):
    def test_external_provider_offer_is_declared_without_native_provider_identity(self) -> None:
        offer = external_provider_capability_offer()
        result = validate_provider_capability_offer(offer)

        self.assertEqual(result.status, "declared")
        self.assertEqual(offer["provider_key"], EXTERNAL_PROVIDER_KEY)
        self.assertNotIn("native_xhs_detail", offer["provider_key"])
        self.assertEqual(offer["adapter_binding"]["binding_scope"], "adapter_bound")

    def test_external_provider_sample_decision_returns_matched(self) -> None:
        decision = decide_adapter_provider_compatibility(external_provider_decision_input())

        self.assertEqual(decision.decision_status, COMPATIBILITY_DECISION_STATUS_MATCHED)
        self.assertEqual(decision.capability, "content_detail")
        self.assertEqual(decision.execution_slice.operation, "content_detail_by_url")
        self.assertEqual(
            decision.evidence.adapter_bound_provider_evidence.provider_key,
            EXTERNAL_PROVIDER_KEY,
        )

    def test_external_provider_sample_decision_returns_unmatched_for_legal_profile_miss(self) -> None:
        decision = decide_adapter_provider_compatibility(external_provider_unmatched_decision_input())

        self.assertEqual(decision.decision_status, COMPATIBILITY_DECISION_STATUS_UNMATCHED)
        self.assertEqual(decision.error, None)
        self.assertEqual(decision.matched_profiles, ())

    def test_external_provider_sample_decision_returns_invalid_contract_for_forbidden_selector(self) -> None:
        decision = decide_adapter_provider_compatibility(external_provider_invalid_contract_decision_input())

        self.assertEqual(decision.decision_status, COMPATIBILITY_DECISION_STATUS_INVALID_CONTRACT)
        self.assertIsNotNone(decision.error)

    def test_adapter_bound_execution_evidence_covers_result_resource_lifecycle_and_observability(self) -> None:
        decision = decide_adapter_provider_compatibility(external_provider_decision_input())
        evidence = build_adapter_bound_execution_evidence(decision)

        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(evidence["raw_payload"]["provider_key"], EXTERNAL_PROVIDER_KEY)
        self.assertEqual(evidence["normalized_result"]["platform"], "xhs")
        self.assertTrue(evidence["provider_error_mapping_checked"])
        self.assertTrue(evidence["resource_profile_consumption_checked"])
        self.assertTrue(evidence["resource_lifecycle_disposition_checked"])
        self.assertTrue(evidence["observability_carrier_checked"])
        self.assertNotIn("provider_key", evidence["core_surface_projection"])

    def test_core_surface_no_leakage_evidence_passes_for_external_provider_sample(self) -> None:
        decision = decide_adapter_provider_compatibility(external_provider_decision_input())
        evidence = build_core_surface_no_leakage_evidence(decision)

        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(
            sorted(evidence["surfaces"]),
            [
                "core_facing_failed_envelope",
                "core_projection",
                "core_routing",
                "registry_discovery",
                "resource_lifecycle",
                "task_record",
            ],
        )

    def test_report_can_feed_fr0351_provider_compatibility_sample_gate(self) -> None:
        report = build_real_provider_sample_evidence_report()

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["release"], "v0.9.0")
        self.assertEqual(report["sample_origin"], "external_provider_sample")
        self.assertEqual(report["provider_support_claim"], False)
        self.assertEqual(report["consumed_gate_ref"], "FR-0351:provider_compatibility_sample")
        self.assertEqual(report["decision_matrix"]["matched_case"]["decision_status"], "matched")
        self.assertEqual(report["decision_matrix"]["unmatched_case"]["decision_status"], "unmatched")
        self.assertEqual(
            report["decision_matrix"]["invalid_contract_case"]["decision_status"],
            "invalid_contract",
        )
        self.assertEqual(report["adapter_bound_execution"]["status"], "pass")
        self.assertEqual(report["core_surface_no_leakage"]["status"], "pass")
        self.assertTrue(report["not_provider_product_support"])
