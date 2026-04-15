from __future__ import annotations

import unittest

import syvert.version_gate as version_gate_module

from tests.runtime.contract_harness.automation import run_contract_harness_automation

from syvert.version_gate import (
    build_harness_source_report,
    orchestrate_version_gate,
    validate_platform_leakage_source_report,
    validate_real_adapter_regression_source_report,
)


class VersionGateTests(unittest.TestCase):
    def test_version_gate_passes_when_all_sources_pass(self) -> None:
        harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )
        regression_report = validate_real_adapter_regression_source_report(
            self.valid_real_adapter_regression_payload(),
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )
        leakage_report = validate_platform_leakage_source_report(
            self.valid_platform_leakage_payload(),
            version="v0.2.0",
        )

        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=harness_report,
            real_adapter_regression_report=regression_report,
            platform_leakage_report=leakage_report,
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertTrue(report["safe_to_release"])
        self.assertEqual(report["failures"], [])
        self.assertEqual(
            set(report["source_reports"]),
            {"harness", "real_adapter_regression", "platform_leakage"},
        )

    def test_harness_contract_violation_fails_closed(self) -> None:
        results = self.valid_harness_results()
        results.append(
            {
                "sample_id": "sample-violation",
                "verdict": "contract_violation",
                "reason": {"code": "runtime_contract_failure_observed", "message": "violation"},
                "observed_status": "failed",
                "observed_error": {
                    "category": "runtime_contract",
                    "code": "invalid_adapter_success_payload",
                    "message": "invalid payload",
                    "details": {},
                },
            }
        )

        report = build_harness_source_report(
            results,
            required_sample_ids=["sample-success", "sample-legal-failure", "sample-violation"],
            version="v0.2.0",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertEqual(report["details"]["failures"][0]["source"], "harness")
        self.assertEqual(report["details"]["failures"][0]["code"], "contract_violation_observed")

    def test_harness_missing_required_sample_fails_closed(self) -> None:
        report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure", "sample-missing"],
            version="v0.2.0",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("missing_required_harness_samples", {item["code"] for item in report["details"]["failures"]})

    def test_harness_rejects_missing_reason_code(self) -> None:
        malformed = [
            {
                "sample_id": "sample-success",
                "verdict": "pass",
                "reason": {"message": "missing code"},
                "observed_status": "success",
                "observed_error": None,
            }
        ]

        report = build_harness_source_report(
            malformed,
            required_sample_ids=["sample-success"],
            version="v0.2.0",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("invalid_reason_fields", {item["code"] for item in report["details"]["failures"]})

    def test_harness_rejects_missing_reason_message(self) -> None:
        malformed = [
            {
                "sample_id": "sample-success",
                "verdict": "pass",
                "reason": {"code": "missing_message"},
                "observed_status": "success",
                "observed_error": None,
            }
        ]

        report = build_harness_source_report(
            malformed,
            required_sample_ids=["sample-success"],
            version="v0.2.0",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("invalid_reason_fields", {item["code"] for item in report["details"]["failures"]})

    def test_harness_rejects_missing_sample_id(self) -> None:
        malformed = [
            {
                "verdict": "pass",
                "reason": {"code": "ok", "message": "ok"},
                "observed_status": "success",
                "observed_error": None,
            }
        ]

        report = build_harness_source_report(
            malformed,
            required_sample_ids=["sample-success"],
            version="v0.2.0",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("invalid_sample_id", {item["code"] for item in report["details"]["failures"]})

    def test_harness_rejects_unknown_verdict(self) -> None:
        malformed = [
            {
                "sample_id": "sample-success",
                "verdict": "maybe",
                "reason": {"code": "unknown", "message": "unknown"},
                "observed_status": "success",
                "observed_error": None,
            }
        ]

        report = build_harness_source_report(
            malformed,
            required_sample_ids=["sample-success"],
            version="v0.2.0",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("invalid_harness_verdict", {item["code"] for item in report["details"]["failures"]})

    def test_harness_rejects_mapping_shaped_required_sample_ids(self) -> None:
        report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids={"sample-success": True},
            version="v0.2.0",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("invalid_required_sample_ids", {item["code"] for item in report["details"]["failures"]})

    def test_harness_builder_generates_deterministic_evidence_refs(self) -> None:
        results = [
            self.valid_harness_results()[1],
            self.valid_harness_results()[0],
        ]

        report = build_harness_source_report(
            results,
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )

        self.assertEqual(
            report["evidence_refs"],
            [
                "harness_validation:sample-legal-failure",
                "harness_validation:sample-success",
            ],
        )

    def test_real_regression_missing_reference_adapter_fails_closed(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["adapter_results"] = [payload["adapter_results"][0]]

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("missing_adapter_result", {item["code"] for item in report["details"]["failures"]})

    def test_real_regression_rejects_non_frozen_reference_pair(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["reference_pair"] = ["xhs", "kuaishou"]

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "kuaishou"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn(
            "reference_pair_not_frozen_for_version",
            {item["code"] for item in report["details"]["failures"]},
        )

    def test_real_regression_rejects_non_frozen_operation_at_public_entry(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["operation"] = "creator_detail"

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            operation="creator_detail",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn(
            "operation_not_frozen_for_version",
            {item["code"] for item in report["details"]["failures"]},
        )
        self.assertIn("operation_mismatch", {item["code"] for item in report["details"]["failures"]})

    def test_real_regression_accepts_reordered_frozen_reference_pair(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["reference_pair"] = ["douyin", "xhs"]

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["douyin", "xhs"],
        )

        self.assertEqual(report["verdict"], "pass")

    def test_real_regression_rejects_unknown_version_without_frozen_pair(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["version"] = "v0.2.1"

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.1",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn(
            "missing_frozen_reference_pair_for_version",
            {item["code"] for item in report["details"]["failures"]},
        )
        self.assertIn(
            "missing_frozen_operation_for_version",
            {item["code"] for item in report["details"]["failures"]},
        )

    def test_real_regression_rejects_unknown_version_without_frozen_operation(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["version"] = "v0.2.1"

        original_pair = version_gate_module._FROZEN_REFERENCE_PAIR_BY_VERSION.get("v0.2.1")
        version_gate_module._FROZEN_REFERENCE_PAIR_BY_VERSION["v0.2.1"] = ("xhs", "douyin")
        try:
            report = validate_real_adapter_regression_source_report(
                payload,
                version="v0.2.1",
                reference_pair=["xhs", "douyin"],
            )
        finally:
            if original_pair is None:
                version_gate_module._FROZEN_REFERENCE_PAIR_BY_VERSION.pop("v0.2.1", None)
            else:
                version_gate_module._FROZEN_REFERENCE_PAIR_BY_VERSION["v0.2.1"] = original_pair

        self.assertEqual(report["verdict"], "fail")
        self.assertIn(
            "missing_frozen_operation_for_version",
            {item["code"] for item in report["details"]["failures"]},
        )

    def test_real_regression_missing_success_coverage_fails_closed(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["adapter_results"][0]["cases"] = [
            {
                "case_id": "xhs-invalid-input",
                "expected_outcome": "allowed_failure",
                "observed_status": "failed",
                "observed_error_category": "invalid_input",
            }
        ]

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("missing_success_coverage", {item["code"] for item in report["details"]["failures"]})

    def test_real_regression_missing_allowed_failure_coverage_fails_closed(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["adapter_results"][0]["cases"] = [
            {
                "case_id": "xhs-success",
                "expected_outcome": "success",
                "observed_status": "success",
                "observed_error_category": None,
            }
        ]

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("missing_allowed_failure_coverage", {item["code"] for item in report["details"]["failures"]})

    def test_real_regression_disallowed_failure_category_fails_closed(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["adapter_results"][0]["cases"][1]["observed_error_category"] = "runtime_contract"

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("disallowed_failure_category", {item["code"] for item in report["details"]["failures"]})

    def test_real_regression_rejects_mapping_shaped_evidence_refs(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["evidence_refs"] = {"forged:1": True}

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("invalid_evidence_refs", {item["code"] for item in report["details"]["failures"]})

    def test_platform_leakage_failure_is_preserved(self) -> None:
        payload = self.valid_platform_leakage_payload()
        payload["verdict"] = "fail"
        payload["findings"] = [
            {
                "code": "platform_branch_in_core",
                "message": "platform-specific branch leaked into core runtime",
                "boundary": "core_runtime",
                "evidence_ref": "leakage:core-runtime:1",
            }
        ]

        report = validate_platform_leakage_source_report(payload, version="v0.2.0")

        self.assertEqual(report["verdict"], "fail")
        self.assertEqual(report["details"]["failures"][0]["source"], "platform_leakage")
        self.assertEqual(report["details"]["failures"][0]["code"], "platform_branch_in_core")

    def test_platform_leakage_missing_evidence_refs_fails_closed(self) -> None:
        payload = self.valid_platform_leakage_payload()
        payload["evidence_refs"] = []

        report = validate_platform_leakage_source_report(payload, version="v0.2.0")

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("missing_evidence_refs", {item["code"] for item in report["details"]["failures"]})

    def test_platform_leakage_rejects_empty_version(self) -> None:
        report = validate_platform_leakage_source_report(
            {
                **self.valid_platform_leakage_payload(),
                "version": "",
            },
            version="",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("missing_version", {item["code"] for item in report["details"]["failures"]})

    def test_platform_leakage_rejects_mapping_shaped_boundary_scope(self) -> None:
        payload = self.valid_platform_leakage_payload()
        payload["boundary_scope"] = {"core_runtime": True}

        report = validate_platform_leakage_source_report(payload, version="v0.2.0")

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("invalid_boundary_scope", {item["code"] for item in report["details"]["failures"]})

    def test_orchestrator_fails_closed_for_missing_version(self) -> None:
        report = orchestrate_version_gate(
            version="",
            reference_pair=["xhs", "douyin"],
            harness_report=build_harness_source_report(
                self.valid_harness_results(),
                required_sample_ids=["sample-success", "sample-legal-failure"],
                version="v0.2.0",
            ),
            real_adapter_regression_report=validate_real_adapter_regression_source_report(
                self.valid_real_adapter_regression_payload(),
                version="v0.2.0",
                reference_pair=["xhs", "douyin"],
            ),
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertFalse(report["safe_to_release"])
        self.assertIn("missing_version", {item["code"] for item in report["failures"]})

    def test_orchestrator_fails_closed_for_invalid_reference_pair(self) -> None:
        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=[],
            harness_report=build_harness_source_report(
                self.valid_harness_results(),
                required_sample_ids=["sample-success", "sample-legal-failure"],
                version="v0.2.0",
            ),
            real_adapter_regression_report=validate_real_adapter_regression_source_report(
                self.valid_real_adapter_regression_payload(),
                version="v0.2.0",
                reference_pair=["xhs", "douyin"],
            ),
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertFalse(report["safe_to_release"])
        self.assertIn("invalid_reference_pair", {item["code"] for item in report["failures"]})

    def test_orchestrator_rejects_mapping_shaped_reference_pair(self) -> None:
        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair={"xhs": True, "douyin": True},
            harness_report=build_harness_source_report(
                self.valid_harness_results(),
                required_sample_ids=["sample-success", "sample-legal-failure"],
                version="v0.2.0",
            ),
            real_adapter_regression_report=validate_real_adapter_regression_source_report(
                self.valid_real_adapter_regression_payload(),
                version="v0.2.0",
                reference_pair=["xhs", "douyin"],
            ),
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("invalid_reference_pair", {item["code"] for item in report["failures"]})

    def test_orchestrator_rejects_unknown_version_without_frozen_pair(self) -> None:
        report = orchestrate_version_gate(
            version="v0.2.1",
            reference_pair=["xhs", "douyin"],
            harness_report=build_harness_source_report(
                self.valid_harness_results(),
                required_sample_ids=["sample-success", "sample-legal-failure"],
                version="v0.2.1",
            ),
            real_adapter_regression_report=validate_real_adapter_regression_source_report(
                {
                    **self.valid_real_adapter_regression_payload(),
                    "version": "v0.2.1",
                },
                version="v0.2.1",
                reference_pair=["xhs", "douyin"],
            ),
            platform_leakage_report=validate_platform_leakage_source_report(
                {
                    **self.valid_platform_leakage_payload(),
                    "version": "v0.2.1",
                },
                version="v0.2.1",
            ),
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertFalse(report["safe_to_release"])
        self.assertIn(
            "missing_frozen_reference_pair_for_version",
            {item["code"] for item in report["failures"]},
        )

    def test_orchestrator_rejects_non_frozen_reference_pair(self) -> None:
        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "kuaishou"],
            harness_report=build_harness_source_report(
                self.valid_harness_results(),
                required_sample_ids=["sample-success", "sample-legal-failure"],
                version="v0.2.0",
            ),
            real_adapter_regression_report=validate_real_adapter_regression_source_report(
                self.valid_real_adapter_regression_payload(),
                version="v0.2.0",
                reference_pair=["xhs", "douyin"],
            ),
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertFalse(report["safe_to_release"])
        self.assertIn(
            "reference_pair_not_frozen_for_version",
            {item["code"] for item in report["failures"]},
        )

    def test_orchestrator_fails_closed_for_missing_source_report(self) -> None:
        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=None,
            real_adapter_regression_report=validate_real_adapter_regression_source_report(
                self.valid_real_adapter_regression_payload(),
                version="v0.2.0",
                reference_pair=["xhs", "douyin"],
            ),
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertFalse(report["safe_to_release"])
        self.assertEqual(report["source_reports"]["harness"]["verdict"], "fail")
        self.assertTrue(report["source_reports"]["harness"]["evidence_refs"])
        self.assertIn("missing_source_report", {item["code"] for item in report["failures"]})

    def test_orchestrator_synthetic_failed_source_reports_remain_contract_shaped(self) -> None:
        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=None,
            real_adapter_regression_report=None,
            platform_leakage_report=None,
        )

        harness_report = report["source_reports"]["harness"]
        self.assertTrue(harness_report["evidence_refs"])
        self.assertTrue(
            {"required_sample_ids", "observed_sample_ids", "validation_results", "failures"}.issubset(
                harness_report["details"]
            )
        )

        regression_report = report["source_reports"]["real_adapter_regression"]
        self.assertTrue(regression_report["evidence_refs"])
        self.assertTrue(
            {"reference_pair", "operation", "adapter_results", "failures"}.issubset(regression_report["details"])
        )

        leakage_report = report["source_reports"]["platform_leakage"]
        self.assertTrue(leakage_report["evidence_refs"])
        self.assertTrue(
            {"boundary_scope", "report_verdict", "findings", "failures"}.issubset(leakage_report["details"])
        )

    def test_orchestrator_revalidates_source_specific_real_regression_contract(self) -> None:
        forged_report = {
            "source": "real_adapter_regression",
            "version": "v0.2.0",
            "verdict": "pass",
            "summary": "forged",
            "evidence_refs": ["forged:1"],
            "details": {"failures": []},
        }

        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=build_harness_source_report(
                self.valid_harness_results(),
                required_sample_ids=["sample-success", "sample-legal-failure"],
                version="v0.2.0",
            ),
            real_adapter_regression_report=forged_report,
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertEqual(report["source_reports"]["real_adapter_regression"]["verdict"], "fail")
        self.assertIn(
            "missing_real_regression_details",
            {item["code"] for item in report["failures"]},
        )

    def test_orchestrator_preserves_failed_harness_source_report(self) -> None:
        failed_harness_report = build_harness_source_report(
            [
                {
                    "sample_id": "sample-valid",
                    "verdict": "pass",
                    "reason": {"code": "success_envelope_observed", "message": "success"},
                    "observed_status": "success",
                    "observed_error": None,
                },
                {
                    "sample_id": "sample-success",
                    "verdict": "pass",
                    "reason": {"code": "success_envelope_observed", "message": "success"},
                    "observed_status": "broken",
                    "observed_error": None,
                }
            ],
            required_sample_ids=["sample-valid", "sample-success"],
            version="v0.2.0",
        )

        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=failed_harness_report,
            real_adapter_regression_report=validate_real_adapter_regression_source_report(
                self.valid_real_adapter_regression_payload(),
                version="v0.2.0",
                reference_pair=["xhs", "douyin"],
            ),
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertEqual(report["source_reports"]["harness"]["verdict"], "fail")
        self.assertIn("invalid_observed_status", {item["code"] for item in report["failures"]})

    def test_orchestrator_preserves_envelope_failed_harness_report_without_failure_payload(self) -> None:
        failed_harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )
        failed_harness_report["verdict"] = "fail"
        failed_harness_report["summary"] = "upstream harness gate already failed"
        failed_harness_report["details"]["failures"] = []

        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=failed_harness_report,
            real_adapter_regression_report=validate_real_adapter_regression_source_report(
                self.valid_real_adapter_regression_payload(),
                version="v0.2.0",
                reference_pair=["xhs", "douyin"],
            ),
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertEqual(report["source_reports"]["harness"]["verdict"], "fail")
        self.assertEqual(report["source_reports"]["harness"]["summary"], "upstream harness gate already failed")
        self.assertIn("upstream_failed_source_report", {item["code"] for item in report["failures"]})

    def test_orchestrator_failed_source_report_does_not_keep_pass_summary(self) -> None:
        failed_harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )
        failed_harness_report["details"]["failures"] = [
            {
                "code": "forged_failure",
                "message": "forged failure",
                "details": {},
            }
        ]

        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=failed_harness_report,
            real_adapter_regression_report=validate_real_adapter_regression_source_report(
                self.valid_real_adapter_regression_payload(),
                version="v0.2.0",
                reference_pair=["xhs", "douyin"],
            ),
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
        )

        self.assertEqual(report["source_reports"]["harness"]["verdict"], "fail")
        self.assertEqual(report["source_reports"]["harness"]["summary"], "harness failed for version `v0.2.0`")

    def test_orchestrator_preserves_failed_real_regression_source_report(self) -> None:
        failed_real_regression_report = validate_real_adapter_regression_source_report(
            {
                **self.valid_real_adapter_regression_payload(),
                "reference_pair": {"forged": True},
            },
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=build_harness_source_report(
                self.valid_harness_results(),
                required_sample_ids=["sample-success", "sample-legal-failure"],
                version="v0.2.0",
            ),
            real_adapter_regression_report=failed_real_regression_report,
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertEqual(report["source_reports"]["real_adapter_regression"]["verdict"], "fail")
        self.assertIn("invalid_report_reference_pair", {item["code"] for item in report["failures"]})

    def test_orchestrator_rewrites_forged_failure_source_to_expected_source(self) -> None:
        forged_harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )
        forged_harness_report["verdict"] = "fail"
        forged_harness_report["details"]["failures"] = [
            {
                "source": "platform_leakage",
                "code": "forged_cross_source_failure",
                "message": "forged failure source",
                "details": {},
            }
        ]

        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=forged_harness_report,
            real_adapter_regression_report=validate_real_adapter_regression_source_report(
                self.valid_real_adapter_regression_payload(),
                version="v0.2.0",
                reference_pair=["xhs", "douyin"],
            ),
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
        )

        forged_failures = [
            item for item in report["failures"] if item["code"] == "forged_cross_source_failure"
        ]
        self.assertEqual(len(forged_failures), 1)
        self.assertEqual(forged_failures[0]["source"], "harness")

    def test_orchestrator_rejects_forged_real_regression_operation(self) -> None:
        forged_report = {
            "source": "real_adapter_regression",
            "version": "v0.2.0",
            "verdict": "pass",
            "summary": "forged",
            "evidence_refs": ["regression:forged:1"],
            "details": {
                "reference_pair": ["xhs", "douyin"],
                "operation": "creator_detail",
                "adapter_results": self.valid_real_adapter_regression_payload()["adapter_results"],
                "failures": [],
            },
        }

        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=build_harness_source_report(
                self.valid_harness_results(),
                required_sample_ids=["sample-success", "sample-legal-failure"],
                version="v0.2.0",
            ),
            real_adapter_regression_report=forged_report,
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertEqual(report["source_reports"]["real_adapter_regression"]["verdict"], "fail")
        self.assertIn("operation_mismatch", {item["code"] for item in report["failures"]})

    def test_orchestrator_revalidates_source_specific_platform_leakage_contract(self) -> None:
        forged_report = {
            "source": "platform_leakage",
            "version": "v0.2.0",
            "verdict": "pass",
            "summary": "forged",
            "evidence_refs": ["forged:1"],
            "details": {"failures": []},
        }

        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=build_harness_source_report(
                self.valid_harness_results(),
                required_sample_ids=["sample-success", "sample-legal-failure"],
                version="v0.2.0",
            ),
            real_adapter_regression_report=validate_real_adapter_regression_source_report(
                self.valid_real_adapter_regression_payload(),
                version="v0.2.0",
                reference_pair=["xhs", "douyin"],
            ),
            platform_leakage_report=forged_report,
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertEqual(report["source_reports"]["platform_leakage"]["verdict"], "fail")
        self.assertIn(
            "missing_platform_leakage_details",
            {item["code"] for item in report["failures"]},
        )

    def test_orchestrator_failures_keep_source_distinction(self) -> None:
        harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure", "sample-missing"],
            version="v0.2.0",
        )
        regression_payload = self.valid_real_adapter_regression_payload()
        regression_payload["adapter_results"] = [regression_payload["adapter_results"][0]]
        regression_report = validate_real_adapter_regression_source_report(
            regression_payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )
        leakage_payload = self.valid_platform_leakage_payload()
        leakage_payload["verdict"] = "fail"
        leakage_payload["findings"] = [
            {
                "code": "shared_result_contract_leak",
                "message": "platform-only field leaked into shared result contract",
                "boundary": "shared_result_contract",
                "evidence_ref": "leakage:shared-result:1",
            }
        ]
        leakage_report = validate_platform_leakage_source_report(
            leakage_payload,
            version="v0.2.0",
        )

        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=harness_report,
            real_adapter_regression_report=regression_report,
            platform_leakage_report=leakage_report,
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertFalse(report["safe_to_release"])
        self.assertTrue(
            {"harness", "real_adapter_regression", "platform_leakage"}.issubset(
                {item["source"] for item in report["failures"]}
            )
        )

    def test_harness_builder_consumes_real_fr0006_output(self) -> None:
        validation_results = run_contract_harness_automation()
        required_sample_ids = [result["sample_id"] for result in validation_results]

        report = build_harness_source_report(
            validation_results,
            required_sample_ids=required_sample_ids,
            version="v0.2.0",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertEqual(
            report["evidence_refs"],
            [
                "harness_validation:contract-violation-missing-normalized",
                "harness_validation:execution-precondition-not-met",
                "harness_validation:legal-failure-platform-envelope",
                "harness_validation:success-full-envelope",
            ],
        )
        self.assertTrue(
            {"contract_violation_observed", "execution_precondition_not_met_observed"}.issubset(
                {item["code"] for item in report["details"]["failures"]}
            )
        )

    def test_harness_rejects_legal_failure_with_success_observation(self) -> None:
        malformed = [
            {
                "sample_id": "sample-legal-failure",
                "verdict": "legal_failure",
                "reason": {"code": "legal_failed_envelope_observed", "message": "legal failure"},
                "observed_status": "success",
                "observed_error": None,
            }
        ]

        report = build_harness_source_report(
            malformed,
            required_sample_ids=["sample-legal-failure"],
            version="v0.2.0",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn(
            "inconsistent_legal_failure_observation",
            {item["code"] for item in report["details"]["failures"]},
        )

    def test_harness_rejects_pass_with_failed_observation(self) -> None:
        malformed = [
            {
                "sample_id": "sample-success",
                "verdict": "pass",
                "reason": {"code": "success_envelope_observed", "message": "success"},
                "observed_status": "failed",
                "observed_error": {
                    "category": "platform",
                    "code": "platform_rejected",
                    "message": "platform rejected request",
                    "details": {},
                },
            }
        ]

        report = build_harness_source_report(
            malformed,
            required_sample_ids=["sample-success"],
            version="v0.2.0",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn(
            "inconsistent_pass_observation",
            {item["code"] for item in report["details"]["failures"]},
        )

    @staticmethod
    def valid_harness_results() -> list[dict[str, object]]:
        return [
            {
                "sample_id": "sample-success",
                "verdict": "pass",
                "reason": {"code": "success_envelope_observed", "message": "success"},
                "observed_status": "success",
                "observed_error": None,
            },
            {
                "sample_id": "sample-legal-failure",
                "verdict": "legal_failure",
                "reason": {"code": "legal_failed_envelope_observed", "message": "legal failure"},
                "observed_status": "failed",
                "observed_error": {
                    "category": "platform",
                    "code": "platform_rejected",
                    "message": "platform rejected request",
                    "details": {},
                },
            },
        ]

    @staticmethod
    def valid_real_adapter_regression_payload() -> dict[str, object]:
        return {
            "version": "v0.2.0",
            "reference_pair": ["xhs", "douyin"],
            "operation": "content_detail_by_url",
            "evidence_refs": [
                "regression:xhs:success",
                "regression:xhs:invalid-input",
                "regression:douyin:success",
                "regression:douyin:platform",
            ],
            "adapter_results": [
                {
                    "adapter_key": "xhs",
                    "cases": [
                        {
                            "case_id": "xhs-success",
                            "expected_outcome": "success",
                            "observed_status": "success",
                            "observed_error_category": None,
                        },
                        {
                            "case_id": "xhs-invalid-input",
                            "expected_outcome": "allowed_failure",
                            "observed_status": "failed",
                            "observed_error_category": "invalid_input",
                        },
                    ],
                },
                {
                    "adapter_key": "douyin",
                    "cases": [
                        {
                            "case_id": "douyin-success",
                            "expected_outcome": "success",
                            "observed_status": "success",
                            "observed_error_category": None,
                        },
                        {
                            "case_id": "douyin-platform",
                            "expected_outcome": "allowed_failure",
                            "observed_status": "failed",
                            "observed_error_category": "platform",
                        },
                    ],
                },
            ],
        }

    @staticmethod
    def valid_platform_leakage_payload() -> dict[str, object]:
        return {
            "version": "v0.2.0",
            "boundary_scope": [
                "core_runtime",
                "shared_input_model",
                "shared_error_model",
                "adapter_registry",
                "shared_result_contract",
                "version_gate_logic",
            ],
            "verdict": "pass",
            "summary": "platform leakage checks are clean",
            "findings": [],
            "evidence_refs": ["leakage:scan:1"],
        }


if __name__ == "__main__":
    unittest.main()
