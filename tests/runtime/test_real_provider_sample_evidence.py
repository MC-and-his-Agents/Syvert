from __future__ import annotations

from copy import deepcopy
import json
import tempfile
import unittest
from unittest.mock import patch

from syvert import real_provider_sample_evidence as evidence_module
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
    build_required_validation_evidence,
    build_real_provider_sample_evidence_report,
    external_provider_capability_offer,
    external_provider_decision_input,
    external_provider_invalid_contract_decision_input,
    external_provider_sample_manifest,
    external_provider_unmatched_decision_input,
    run_external_provider_sample_runtime_execution,
)


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
        self.assertTrue(evidence["raw_payload_present"])
        self.assertEqual(evidence["raw_payload"]["sample_id"], "v0.9.0-external-provider-sample-content-detail")
        self.assertEqual(evidence["raw_payload_ref"], "external-fixture://content-detail/success#raw")
        self.assertTrue(evidence["normalized_result_present"])
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
        self.assertIsNone(evidence["resource_lifecycle_disposition_hint"])
        self.assertEqual(
            evidence["resource_lifecycle_release_reason"],
            "adapter_completed_without_disposition_hint",
        )
        self.assertEqual(
            evidence["resource_lifecycle_failure_release_reason"],
            "adapter_failed_without_disposition_hint",
        )
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

    def test_adapter_bound_execution_evidence_fails_closed_when_success_payloads_are_missing(self) -> None:
        decision = decide_adapter_provider_compatibility(external_provider_decision_input())
        execution = run_external_provider_sample_runtime_execution()
        execution["success"]["envelope"].pop("raw")
        execution["success"]["envelope"].pop("normalized")

        evidence = build_adapter_bound_execution_evidence(decision, execution_override=execution)

        self.assertEqual(evidence["status"], "fail")
        self.assertFalse(evidence["raw_payload_present"])
        self.assertFalse(evidence["normalized_result_present"])

    def test_adapter_bound_execution_evidence_fails_closed_for_bad_execution_shape(self) -> None:
        decision = decide_adapter_provider_compatibility(external_provider_decision_input())

        evidence = build_adapter_bound_execution_evidence(decision, execution_override={"success": {}})

        self.assertEqual(evidence["status"], "fail")
        self.assertIn("runtime_execution_ref_missing", evidence["fail_closed_reason"])
        self.assertIn("success_envelope_missing", evidence["fail_closed_reason"])
        self.assertIn("failure_execution_missing", evidence["fail_closed_reason"])

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
        self.assertEqual(
            report["external_provider_sample"]["provenance_artifact_ref"],
            "syvert/fixtures/v0_9_external_provider_sample_provenance.json",
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
        self.assertEqual(
            report["evidence_snapshot_sha256"],
            "31974bc000995d0f746d6b9132afa818dc85e7971ace8b0e355c918a66f9ba76",
        )
        self.assertEqual(report["validation_evidence"]["status"], "pass")
        self.assertEqual(
            report["validation_evidence"]["artifact_ref"],
            "docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-validation.json",
        )
        self.assertEqual(report["validation_evidence"]["report_snapshot_sha256"], report["evidence_snapshot_sha256"])
        self.assertEqual(len(report["validation_evidence"]["commands"]), 3)
        self.assertIn("resource_trace", report["core_surface_no_leakage"]["surfaces"])
        self.assertIn("task_record", report["core_surface_no_leakage"]["surfaces"])
        self.assertTrue(report["not_provider_product_support"])
        self.assertNotIn("fail_closed_reason", report["decision_matrix"])

    def test_validation_evidence_consumes_machine_readable_artifact(self) -> None:
        evidence = build_required_validation_evidence()

        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(
            evidence["artifact_ref"],
            "docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-validation.json",
        )
        self.assertEqual(evidence["run_id"], "local-CHORE-0358-v0-9-external-provider-sample-evidence")
        self.assertEqual(
            evidence["validated_source_sha256"],
            evidence_module._validation_source_binding_sha256(),
        )
        self.assertEqual(
            evidence["report_snapshot_sha256"],
            "31974bc000995d0f746d6b9132afa818dc85e7971ace8b0e355c918a66f9ba76",
        )
        self.assertEqual(
            tuple(command["command"] for command in evidence["commands"]),
            (
                "python3 -m unittest tests.runtime.test_real_provider_sample_evidence",
                "python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard tests.runtime.test_real_provider_sample_evidence",
                "python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_cli_http_same_path",
            ),
        )
        self.assertTrue(all(command["status"] == "pass" for command in evidence["commands"]))

    def test_required_validation_commands_are_bound_to_repo_modules(self) -> None:
        required_modules = {
            module
            for _, modules in evidence_module.REQUIRED_VALIDATION_COMMANDS
            for module in modules
        }

        self.assertEqual(required_modules, set(evidence_module.VALIDATION_MODULE_PATHS))

    def test_validation_evidence_fails_closed_for_structured_artifact_drift(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json") as artifact:
            json.dump(
                {
                    "report_id": "CHORE-0358-v0-9-external-provider-sample-evidence",
                    "release": "v0.9.0",
                    "fr_ref": "FR-0355",
                    "consumed_gate_ref": "FR-0351:wrong-gate",
                    "status": "pass",
                    "commands": [
                        {
                            "validation": "external provider sample evidence",
                            "command": "python3 -m unittest tests.runtime.test_real_provider_sample_evidence",
                            "status": "pass",
                        },
                        {
                            "validation": "compatibility decision / no-leakage / sample",
                            "command": "python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard tests.runtime.test_real_provider_sample_evidence",
                            "status": "pass",
                        },
                        {
                            "validation": "dual reference / third-party entry / API CLI same path",
                            "command": "python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_cli_http_same_path",
                            "status": "pass",
                        },
                    ],
                },
                artifact,
            )
            artifact.flush()

            with patch.object(evidence_module, "VALIDATION_EVIDENCE_ARTIFACT_PATH", artifact.name):
                evidence = evidence_module.build_required_validation_evidence()

        self.assertEqual(evidence["status"], "fail")

    def test_evidence_artifact_binding_fails_closed_for_runtime_snapshot_drift(self) -> None:
        report = build_real_provider_sample_evidence_report()
        mutated_report = deepcopy(report)
        mutated_report["decision_matrix"]["matched_case_ref"] = "fr-0355:decision-matrix:drift"

        reasons = evidence_module._evidence_ref_fail_closed_reasons(mutated_report)

        self.assertIn("evidence_artifact_structured_snapshot_drift", reasons)

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

    def test_report_fails_closed_for_missing_required_manifest_fields(self) -> None:
        manifest = external_provider_sample_manifest()
        manifest.pop("manifest_id")
        manifest.pop("provenance_ref")
        manifest.pop("provenance_artifact_ref")
        manifest.pop("author_path")

        report = build_real_provider_sample_evidence_report(manifest_override=manifest)

        self.assertEqual(report["status"], "fail")
        self.assertIsNone(report["external_provider_sample"]["manifest_id"])
        self.assertIsNone(report["external_provider_sample"]["provenance_ref"])
        self.assertIsNone(report["external_provider_sample"]["provenance_artifact_ref"])
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
            "manifest_required_field_missing:provenance_artifact_ref",
            report["decision_matrix"]["fail_closed_reason"],
        )
        self.assertIn(
            "manifest_required_field_missing:author_path",
            report["decision_matrix"]["fail_closed_reason"],
        )

    def test_report_fails_closed_for_provenance_artifact_ref_drift(self) -> None:
        manifest = external_provider_sample_manifest()
        manifest["provenance_artifact_ref"] = "syvert/fixtures/missing-provenance.json"

        report = build_real_provider_sample_evidence_report(manifest_override=manifest)

        self.assertEqual(report["status"], "fail")
        self.assertIn(
            "manifest_provenance_artifact_ref_not_canonical_fixture",
            report["decision_matrix"]["fail_closed_reason"],
        )
        self.assertIn("provenance_artifact_ref_drift", report["decision_matrix"]["fail_closed_reason"])

    def test_no_leakage_evidence_reports_identity_presence_when_surface_leaks(self) -> None:
        decision = decide_adapter_provider_compatibility(external_provider_decision_input())
        evidence = build_core_surface_no_leakage_evidence(
            decision,
            surface_overrides={"task_record": {"provider_key": EXTERNAL_PROVIDER_KEY}},
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertTrue(evidence["provider_identity_in_core_surface"])
        self.assertFalse(evidence["all_forbidden_paths_empty"])
