from __future__ import annotations

import os
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
    NESTED_VALIDATION_ENV,
    build_adapter_bound_execution_evidence,
    build_core_surface_no_leakage_evidence,
    build_real_provider_sample_evidence_report,
    external_provider_capability_offer,
    external_provider_decision_input,
    external_provider_invalid_contract_decision_input,
    external_provider_sample_manifest,
    external_provider_unmatched_decision_input,
)

SKIP_NESTED_REPORT_VALIDATION = os.environ.get(NESTED_VALIDATION_ENV) == "1"


class RealProviderSampleEvidenceTests(unittest.TestCase):
    def test_external_provider_offer_is_declared_without_native_provider_identity(self) -> None:
        manifest = external_provider_sample_manifest()
        offer = external_provider_capability_offer()
        result = validate_provider_capability_offer(offer)

        self.assertEqual(result.status, "declared")
        self.assertTrue(manifest["not_native_provider_self_evidence"])
        self.assertEqual(manifest["provider_key"], EXTERNAL_PROVIDER_KEY)
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
        self.assertEqual(evidence["matched_decision_ref"], "fr-0355:decision-matrix:matched")
        self.assertEqual(evidence["matched_decision_id"], "v0-9-external-provider-sample-matched")
        self.assertNotIn("provider_key", evidence["raw_payload"])
        self.assertEqual(evidence["raw_payload"]["sample_id"], "v0.9.0-external-provider-sample-content-detail")
        self.assertEqual(evidence["raw_payload_ref"], "external-fixture://content-detail/success#raw")
        self.assertEqual(evidence["normalized_result"]["platform"], "xhs")
        self.assertEqual(
            evidence["normalized_result_ref"],
            "external-fixture://content-detail/success#normalized",
        )
        self.assertIn("adapter-mapped-failed-envelope", evidence["adapter_mapped_failed_envelope_ref"])
        self.assertEqual(evidence["adapter_mapped_failed_envelope"]["error"]["category"], "platform")
        self.assertEqual(evidence["adapter_mapped_failed_envelope"]["error"]["code"], "external_sample_unavailable")
        self.assertEqual(evidence["adapter_mapped_failed_envelope"]["capability"], "content_detail_by_url")
        self.assertEqual(evidence["provider_error_mapping"]["provider_side_error_code"], "provider_unavailable")
        self.assertEqual(evidence["provider_error_mapping"]["adapter_mapped_error_code"], "external_sample_unavailable")
        self.assertTrue(evidence["provider_error_mapping_checked"])
        self.assertTrue(evidence["resource_profile_consumption_checked"])
        self.assertTrue(evidence["resource_lifecycle_disposition_checked"])
        self.assertEqual(evidence["resource_lifecycle_disposition_hint"], "release")
        self.assertTrue(evidence["observability_carrier_checked"])
        self.assertEqual(evidence["observability"]["adapter_key"], "xhs")
        self.assertEqual(evidence["observability"]["capability"], "content_detail")
        self.assertEqual(evidence["observability"]["operation"], "content_detail_by_url")
        self.assertEqual(evidence["observability"]["decision_status"], "matched")
        self.assertEqual(
            evidence["observability"]["proof_refs"],
            (
                "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                "fr-0027:profile:content-detail-by-url-hybrid:account",
            ),
        )
        self.assertEqual(evidence["runtime_execution_ref"], "syvert.runtime.execute_task_with_record:v0-9-external-provider-sample")
        self.assertEqual(evidence["success_task_record_ref"], "task_record:task-v0-9-sample-success")
        self.assertEqual(evidence["failure_task_record_ref"], "task_record:task-v0-9-sample-failure")
        self.assertNotIn("provider_key", evidence["core_surface_projection"])

    def test_core_surface_no_leakage_evidence_passes_for_external_provider_sample(self) -> None:
        decision = decide_adapter_provider_compatibility(external_provider_decision_input())
        evidence = build_core_surface_no_leakage_evidence(decision)

        self.assertEqual(evidence["status"], "pass")
        self.assertFalse(evidence["provider_identity_in_core_surface"])
        self.assertTrue(evidence["registry_discovery_checked"])
        self.assertTrue(evidence["core_routing_checked"])
        self.assertTrue(evidence["task_record_checked"])
        self.assertTrue(evidence["resource_lifecycle_checked"])
        self.assertTrue(evidence["failed_envelope_checked"])
        self.assertTrue(evidence["all_forbidden_paths_empty"])
        self.assertEqual(
            sorted(evidence["surfaces"]),
            [
                "core_facing_failed_envelope",
                "core_projection",
                "core_routing",
                "registry_discovery",
                "resource_lifecycle",
                "resource_trace",
                "task_record",
            ],
        )

    def test_no_leakage_fails_closed_when_required_surfaces_are_missing(self) -> None:
        decision = decide_adapter_provider_compatibility(external_provider_decision_input())
        evidence = build_core_surface_no_leakage_evidence(
            decision,
            adapter_bound_execution={"core_runtime_surfaces": {"registry_discovery": {"adapter_key": "xhs"}}},
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertTrue(evidence["registry_discovery_checked"])
        self.assertFalse(evidence["task_record_checked"])
        self.assertFalse(evidence["resource_lifecycle_checked"])
        self.assertFalse(evidence["failed_envelope_checked"])
        self.assertIn("task_record", evidence["missing_required_surfaces"])
        self.assertIn("resource_lifecycle", evidence["missing_required_surfaces"])
        self.assertIn("resource_trace", evidence["missing_required_surfaces"])
        self.assertIn("core_facing_failed_envelope", evidence["missing_required_surfaces"])

    @unittest.skipIf(SKIP_NESTED_REPORT_VALIDATION, "outer report validation owns subprocess execution")
    def test_report_can_feed_fr0351_provider_compatibility_sample_gate(self) -> None:
        report = build_real_provider_sample_evidence_report()

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["release"], "v0.9.0")
        self.assertEqual(report["sample_origin"], "external_provider_sample")
        self.assertEqual(report["provider_support_claim"], False)
        self.assertEqual(report["consumed_gate_ref"], "FR-0351:provider_compatibility_sample")
        self.assertEqual(
            report["external_provider_sample"]["manifest_ref"],
            "syvert/fixtures/v0_9_external_provider_sample_manifest.json",
        )
        self.assertTrue(report["external_provider_sample"]["not_native_provider_self_evidence"])
        self.assertEqual(
            report["external_provider_sample"]["requirement_ref"],
            "fr-0024:reference-adapter-migration:xhs-douyin-content-detail",
        )
        self.assertEqual(
            report["external_provider_sample"]["offer_ref"],
            "fr-0025:offer-manifest-fixture-validator:v0-9-external-provider-sample",
        )
        self.assertEqual(
            report["external_provider_sample"]["adapter_binding_ref"],
            "fr-0025:offer-manifest-fixture-validator:v0-9-external-provider-adapter-binding",
        )
        self.assertEqual(
            report["external_provider_sample"]["decision_ref"],
            "v0-9-external-provider-sample-matched",
        )
        self.assertEqual(
            report["external_provider_sample"]["decision_contract_ref"],
            "fr-0026:runtime-tests:adapter-provider-compatibility-decision",
        )
        self.assertEqual(
            report["external_provider_sample"]["profile_proof_refs"],
            (
                "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                "fr-0027:profile:content-detail-by-url-hybrid:account",
            ),
        )
        self.assertEqual(report["dual_reference_ref"], "tests.runtime.test_real_adapter_regression")
        self.assertEqual(report["third_party_adapter_entry_ref"], "tests.runtime.test_third_party_adapter_contract_entry")
        self.assertEqual(report["api_cli_same_core_path_ref"], "tests.runtime.test_cli_http_same_path")
        self.assertEqual(report["decision_matrix"]["matched_case_ref"], "fr-0355:decision-matrix:matched")
        self.assertEqual(report["decision_matrix"]["unmatched_case_ref"], "fr-0355:decision-matrix:unmatched")
        self.assertEqual(
            report["decision_matrix"]["invalid_contract_case_ref"],
            "fr-0355:decision-matrix:invalid-contract",
        )
        self.assertIn("test_real_provider_sample_evidence", report["decision_matrix"]["validator_commands"][0])
        self.assertEqual(report["decision_matrix"]["matched_case"]["decision_status"], "matched")
        self.assertIn(
            "fr-0025:offer-manifest-fixture-validator:v0-9-external-provider-adapter-binding",
            report["required_evidence_refs"],
        )
        self.assertEqual(report["decision_matrix"]["unmatched_case"]["decision_status"], "unmatched")
        self.assertEqual(
            report["decision_matrix"]["invalid_contract_case"]["decision_status"],
            "invalid_contract",
        )
        self.assertEqual(report["adapter_bound_execution"]["status"], "pass")
        self.assertEqual(report["core_surface_no_leakage"]["status"], "pass")
        self.assertEqual(report["validation_evidence"]["status"], "pass")
        self.assertEqual(len(report["validation_evidence"]["commands"]), 3)
        self.assertIn("resource_trace", report["core_surface_no_leakage"]["surfaces"])
        self.assertIn("task_record", report["core_surface_no_leakage"]["surfaces"])
        self.assertTrue(report["not_provider_product_support"])
        self.assertNotIn("fail_closed_reason", report["decision_matrix"])

    @unittest.skipIf(SKIP_NESTED_REPORT_VALIDATION, "outer report validation owns subprocess execution")
    def test_report_approved_slice_is_not_global_mutable_state(self) -> None:
        report = build_real_provider_sample_evidence_report()
        report["approved_slice"]["capability"] = "mutated"

        self.assertEqual(build_real_provider_sample_evidence_report()["approved_slice"]["capability"], "content_detail")

    def test_adapter_bound_execution_evidence_is_not_global_mutable_state(self) -> None:
        decision = decide_adapter_provider_compatibility(external_provider_decision_input())
        evidence = build_adapter_bound_execution_evidence(decision)
        evidence["raw_payload"]["mutated"] = True
        evidence["adapter_mapped_failed_envelope"]["error"]["code"] = "mutated"

        fresh = build_adapter_bound_execution_evidence(decision)

        self.assertNotIn("mutated", fresh["raw_payload"])
        self.assertEqual(fresh["adapter_mapped_failed_envelope"]["error"]["code"], "external_sample_unavailable")

    @unittest.skipIf(SKIP_NESTED_REPORT_VALIDATION, "outer report validation owns subprocess execution")
    def test_report_fails_closed_for_manifest_drift(self) -> None:
        manifest = external_provider_sample_manifest()
        manifest["provider_support_claim"] = True
        manifest["approved_slice"] = {
            "capability": "content_detail",
            "operation": "search",
            "target_type": "keyword",
            "collection_mode": "list",
        }

        report = build_real_provider_sample_evidence_report(manifest_override=manifest)

        self.assertEqual(report["status"], "fail")
        self.assertIn("manifest_provider_support_claim_not_false", report["decision_matrix"]["fail_closed_reason"])
        self.assertIn("manifest_approved_slice_drift", report["decision_matrix"]["fail_closed_reason"])

    @unittest.skipIf(SKIP_NESTED_REPORT_VALIDATION, "outer report validation owns subprocess execution")
    def test_report_fails_closed_for_manifest_forbidden_claim_semantics(self) -> None:
        manifest = external_provider_sample_manifest()
        manifest["forbidden_claims"] = ["provider_product_support", "fallback"]

        report = build_real_provider_sample_evidence_report(manifest_override=manifest)

        self.assertEqual(report["status"], "fail")
        self.assertIn(
            "manifest_forbidden_claim_present:provider_product_support",
            report["decision_matrix"]["fail_closed_reason"],
        )
        self.assertIn(
            "manifest_forbidden_claim_present:fallback",
            report["decision_matrix"]["fail_closed_reason"],
        )

    @unittest.skipIf(SKIP_NESTED_REPORT_VALIDATION, "outer report validation owns subprocess execution")
    def test_report_fails_closed_for_missing_required_manifest_fields(self) -> None:
        manifest = external_provider_sample_manifest()
        manifest.pop("manifest_id")
        manifest.pop("provenance_ref")
        manifest.pop("author_path")

        report = build_real_provider_sample_evidence_report(manifest_override=manifest)

        self.assertEqual(report["status"], "fail")
        self.assertIsNone(report["external_provider_sample"]["manifest_id"])
        self.assertIsNone(report["external_provider_sample"]["provenance_ref"])
        self.assertIsNone(report["external_provider_sample"]["author_path"])
        self.assertIn(
            "manifest_required_field_missing:manifest_id",
            report["decision_matrix"]["fail_closed_reason"],
        )
        self.assertIn(
            "manifest_required_field_missing:provenance_ref",
            report["decision_matrix"]["fail_closed_reason"],
        )
        self.assertIn(
            "manifest_required_field_missing:author_path",
            report["decision_matrix"]["fail_closed_reason"],
        )

    def test_no_leakage_evidence_reports_identity_presence_when_surface_leaks(self) -> None:
        decision = decide_adapter_provider_compatibility(external_provider_decision_input())
        evidence = build_core_surface_no_leakage_evidence(
            decision,
            surface_overrides={"task_record": {"provider_key": EXTERNAL_PROVIDER_KEY}},
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertTrue(evidence["provider_identity_in_core_surface"])
        self.assertFalse(evidence["all_forbidden_paths_empty"])
