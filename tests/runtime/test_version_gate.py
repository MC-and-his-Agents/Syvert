from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from syvert.platform_leakage import run_platform_leakage_check
import syvert.version_gate as version_gate_module

from tests.runtime.contract_harness.automation import run_contract_harness_automation

from syvert.runtime import PlatformAdapterError
from syvert.real_adapter_regression import run_real_adapter_regression

from syvert.version_gate import (
    build_harness_source_report,
    orchestrate_version_gate as _orchestrate_version_gate,
    validate_platform_leakage_source_report,
    validate_real_adapter_regression_source_report,
)


DEFAULT_REQUIRED_HARNESS_SAMPLE_IDS = ["sample-success", "sample-legal-failure"]


def orchestrate_version_gate(**kwargs: object) -> dict[str, object]:
    kwargs.setdefault("required_harness_sample_ids", DEFAULT_REQUIRED_HARNESS_SAMPLE_IDS)
    return version_gate_module.orchestrate_version_gate(**kwargs)


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
        for source, source_report in report["source_reports"].items():
            self.assert_source_report_contract_shape(source, source_report)

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

    def test_harness_fail_closed_output_keeps_non_empty_version(self) -> None:
        report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertEqual(report["version"], "unknown")

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
        self.assertTrue(report["evidence_refs"])

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

    def test_harness_rejects_unhashable_verdict_fail_closed(self) -> None:
        malformed = [
            {
                "sample_id": "sample-success",
                "verdict": {"bad": 1},
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
        json.dumps(report)

    def test_harness_rejects_unhashable_observed_status_fail_closed(self) -> None:
        malformed = [
            {
                "sample_id": "sample-success",
                "verdict": "pass",
                "reason": {"code": "ok", "message": "ok"},
                "observed_status": {"bad": 1},
                "observed_error": None,
            }
        ]

        report = build_harness_source_report(
            malformed,
            required_sample_ids=["sample-success"],
            version="v0.2.0",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("invalid_observed_status", {item["code"] for item in report["details"]["failures"]})
        json.dumps(report)

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

    def test_harness_accepted_report_is_json_serializable_with_non_json_observed_error_details(self) -> None:
        results = self.valid_harness_results()
        results[1]["observed_error"]["details"] = {"nested_set": {1, 2}}

        report = build_harness_source_report(
            results,
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )

        self.assertEqual(report["verdict"], "pass")
        json.dumps(report)

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
        self.assertEqual(report["details"]["operation"], "content_detail_by_url")

    def test_real_regression_accepts_reordered_frozen_reference_pair(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["reference_pair"] = ["douyin", "xhs"]

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["douyin", "xhs"],
        )

        self.assertEqual(report["verdict"], "pass")

    def test_real_regression_accepts_fr0004_projected_operation_surface(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["operation"] = "content_detail"
        payload["target_type"] = "url"

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            operation="content_detail",
            target_type="url",
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["operation"], "content_detail")
        self.assertEqual(report["details"]["target_type"], "url")
        self.assertEqual(report["details"]["semantic_operation"], "content_detail_by_url")

    def test_real_regression_rejects_projected_payload_when_public_entry_expects_semantic_surface(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["operation"] = "content_detail"
        payload["target_type"] = "url"

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            operation="content_detail_by_url",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("operation_surface_mismatch", {item["code"] for item in report["details"]["failures"]})

    def test_real_regression_rejects_semantic_payload_when_public_entry_expects_projected_surface(self) -> None:
        payload = self.valid_real_adapter_regression_payload()

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            operation="content_detail",
            target_type="url",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("operation_surface_mismatch", {item["code"] for item in report["details"]["failures"]})

    def test_real_regression_rejects_projected_operation_without_target_type(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["operation"] = "content_detail"
        payload.pop("target_type", None)

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            operation="content_detail",
            target_type=None,
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("operation_not_frozen_for_version", {item["code"] for item in report["details"]["failures"]})
        self.assertIn("operation_mismatch", {item["code"] for item in report["details"]["failures"]})

    def test_real_regression_rejects_malformed_target_type(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["target_type"] = {"bad": 1}

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            operation="content_detail_by_url",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("operation_mismatch", {item["code"] for item in report["details"]["failures"]})

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

    def test_real_regression_rejects_empty_version(self) -> None:
        report = validate_real_adapter_regression_source_report(
            self.valid_real_adapter_regression_payload(),
            version="",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertEqual(report["version"], "unknown")
        self.assertIn("missing_version", {item["code"] for item in report["details"]["failures"]})

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
                "evidence_ref": "regression:xhs:invalid-input",
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
                "evidence_ref": "regression:xhs:success",
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
        self.assertTrue(report["evidence_refs"])

    def test_real_regression_rejects_missing_case_evidence_ref(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["adapter_results"][0]["cases"][0]["evidence_ref"] = ""

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("invalid_case_evidence_ref", {item["code"] for item in report["details"]["failures"]})

    def test_real_regression_rejects_case_evidence_mismatch(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["evidence_refs"] = [
            "regression:xhs:success",
            "regression:douyin:success",
            "regression:xhs:invalid-input",
            "regression:douyin:platform",
        ]

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("case_evidence_refs_mismatch", {item["code"] for item in report["details"]["failures"]})

    def test_real_regression_rejects_case_matrix_drift(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["adapter_results"][1]["cases"][1]["case_id"] = "douyin-alt-platform"

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("case_matrix_mismatch", {item["code"] for item in report["details"]["failures"]})

    def test_real_regression_rejects_unhashable_case_enums(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["adapter_results"][0]["cases"][0]["expected_outcome"] = {"bad": 1}
        payload["adapter_results"][1]["cases"][0]["observed_status"] = {"bad": 2}

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("invalid_expected_outcome", {item["code"] for item in report["details"]["failures"]})
        self.assertIn("invalid_observed_status", {item["code"] for item in report["details"]["failures"]})
        json.dumps(report)

    def test_real_regression_fail_closed_output_is_json_serializable(self) -> None:
        report = validate_real_adapter_regression_source_report(
            self.valid_real_adapter_regression_payload(),
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            operation={"bad": {1, 2}},
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("operation_not_frozen_for_version", {item["code"] for item in report["details"]["failures"]})
        json.dumps(report)

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
        self.assertTrue(report["evidence_refs"])

    def test_platform_leakage_rejects_out_of_scope_boundary(self) -> None:
        payload = self.valid_platform_leakage_payload()
        payload["verdict"] = "fail"
        payload["findings"] = [
            {
                "code": "adapter_private_note",
                "message": "platform semantic stayed in adapter private impl",
                "boundary": "adapter_private_impl",
                "evidence_ref": "leakage:adapter-private:1",
            }
        ]

        report = validate_platform_leakage_source_report(payload, version="v0.2.0")

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("unsupported_leakage_finding_boundary", {item["code"] for item in report["details"]["failures"]})
        self.assertNotIn("adapter_private_note", {item["code"] for item in report["details"]["failures"]})

    def test_platform_leakage_rejects_pass_report_with_findings(self) -> None:
        payload = self.valid_platform_leakage_payload()
        payload["findings"] = [
            {
                "code": "shared_result_contract_leak",
                "message": "platform-only field leaked into shared result contract",
                "boundary": "shared_result_contract",
                "evidence_ref": "leakage:shared-result:1",
            }
        ]

        report = validate_platform_leakage_source_report(payload, version="v0.2.0")

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("pass_report_with_findings", {item["code"] for item in report["details"]["failures"]})
        self.assertEqual(report["summary"], "platform leakage failed for version `v0.2.0`")

    def test_platform_leakage_rejects_missing_boundary_scope(self) -> None:
        payload = self.valid_platform_leakage_payload()
        payload["boundary_scope"] = payload["boundary_scope"][:-1]

        report = validate_platform_leakage_source_report(payload, version="v0.2.0")

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("missing_boundary_scope", {item["code"] for item in report["details"]["failures"]})

    def test_platform_leakage_rejects_unexpected_boundary_scope(self) -> None:
        payload = self.valid_platform_leakage_payload()
        payload["boundary_scope"] = [*payload["boundary_scope"], "adapter_private_impl"]

        report = validate_platform_leakage_source_report(payload, version="v0.2.0")

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("unexpected_boundary_scope", {item["code"] for item in report["details"]["failures"]})

    def test_platform_leakage_rejects_missing_findings_field(self) -> None:
        payload = self.valid_platform_leakage_payload()
        payload.pop("findings")

        report = validate_platform_leakage_source_report(payload, version="v0.2.0")

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("missing_leakage_findings", {item["code"] for item in report["details"]["failures"]})

    def test_platform_leakage_rejects_empty_version(self) -> None:
        report = validate_platform_leakage_source_report(
            {
                **self.valid_platform_leakage_payload(),
                "version": "",
            },
            version="",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertEqual(report["version"], "unknown")
        self.assertIn("missing_version", {item["code"] for item in report["details"]["failures"]})

    def test_platform_leakage_rejects_unhashable_verdict_fail_closed(self) -> None:
        payload = self.valid_platform_leakage_payload()
        payload["verdict"] = {"bad": {1, 2}}

        report = validate_platform_leakage_source_report(payload, version="v0.2.0")

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("invalid_leakage_verdict", {item["code"] for item in report["details"]["failures"]})
        json.dumps(report)

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

    def test_orchestrator_fail_closed_output_keeps_non_empty_version_and_reference_pair(self) -> None:
        report = orchestrate_version_gate(
            version="",
            reference_pair=["xhs", "douyin"],
            harness_report=build_harness_source_report(
                self.valid_harness_results(),
                required_sample_ids=["sample-success", "sample-legal-failure"],
                version="",
            ),
            real_adapter_regression_report=validate_real_adapter_regression_source_report(
                self.valid_real_adapter_regression_payload(),
                version="",
                reference_pair=["xhs", "douyin"],
            ),
            platform_leakage_report=validate_platform_leakage_source_report(
                {
                    **self.valid_platform_leakage_payload(),
                    "version": "",
                },
                version="",
            ),
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertEqual(report["version"], "unknown")
        self.assertTrue(report["reference_pair"])
        for source, source_report in report["source_reports"].items():
            self.assert_source_report_contract_shape(source, source_report)

    def test_public_source_reports_remain_contract_shaped_on_fail_closed_paths(self) -> None:
        harness_report = build_harness_source_report(
            [
                {
                    "verdict": "pass",
                    "reason": {"code": "ok", "message": "ok"},
                    "observed_status": "success",
                    "observed_error": None,
                }
            ],
            required_sample_ids=["sample-success"],
            version="",
        )
        self.assert_source_report_contract_shape("harness", harness_report)

        real_regression_report = validate_real_adapter_regression_source_report(
            self.valid_real_adapter_regression_payload(),
            version="",
            reference_pair=["xhs", "douyin"],
        )
        self.assert_source_report_contract_shape("real_adapter_regression", real_regression_report)

        platform_leakage_report = validate_platform_leakage_source_report(
            {
                **self.valid_platform_leakage_payload(),
                "version": "",
                "evidence_refs": [],
            },
            version="",
        )
        self.assert_source_report_contract_shape("platform_leakage", platform_leakage_report)

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

    def test_orchestrator_rejects_source_mismatch(self) -> None:
        forged_harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )
        forged_harness_report["source"] = "platform_leakage"

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

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("source_mismatch", {item["code"] for item in report["failures"]})

    def test_orchestrator_rejects_source_report_version_mismatch(self) -> None:
        forged_harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.1",
        )

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

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("source_report_version_mismatch", {item["code"] for item in report["failures"]})

    def test_orchestrator_rejects_source_report_with_empty_summary(self) -> None:
        forged_harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )
        forged_harness_report["summary"] = ""

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

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("missing_source_summary", {item["code"] for item in report["failures"]})

    def test_orchestrator_rejects_harness_report_missing_observed_sample_ids(self) -> None:
        forged_harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )
        forged_harness_report["details"].pop("observed_sample_ids")

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

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("missing_harness_details", {item["code"] for item in report["failures"]})

    def test_orchestrator_rejects_harness_report_with_malformed_observed_sample_ids(self) -> None:
        forged_harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )
        forged_harness_report["details"]["observed_sample_ids"] = {"forged": True}

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

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("invalid_harness_observed_sample_ids", {item["code"] for item in report["failures"]})

    def test_orchestrator_rejects_harness_report_with_mismatched_observed_sample_ids(self) -> None:
        forged_harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )
        forged_harness_report["details"]["observed_sample_ids"] = ["sample-success"]

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

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("harness_observed_sample_ids_mismatch", {item["code"] for item in report["failures"]})

    def test_orchestrator_rejects_harness_report_with_forged_evidence_refs(self) -> None:
        forged_harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )
        forged_harness_report["evidence_refs"] = ["forged:1"]

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

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("harness_evidence_refs_mismatch", {item["code"] for item in report["failures"]})

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
            required_harness_sample_ids=["sample-valid", "sample-success"],
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

    def test_orchestrator_preserves_malformed_harness_failure_reason(self) -> None:
        malformed_harness_report = build_harness_source_report(
            [
                {
                    "verdict": "pass",
                    "reason": {"code": "ok", "message": "ok"},
                    "observed_status": "success",
                    "observed_error": None,
                }
            ],
            required_sample_ids=["sample-success"],
            version="v0.2.0",
        )

        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=malformed_harness_report,
            real_adapter_regression_report=validate_real_adapter_regression_source_report(
                self.valid_real_adapter_regression_payload(),
                version="v0.2.0",
                reference_pair=["xhs", "douyin"],
            ),
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
            required_harness_sample_ids=["sample-success"],
        )

        self.assertIn("invalid_sample_id", {item["code"] for item in report["failures"]})
        self.assertNotIn("missing_source_evidence_refs", {item["code"] for item in report["failures"]})

    def test_orchestrator_preserves_failed_harness_evidence_refs(self) -> None:
        malformed_harness_report = build_harness_source_report(
            [
                {
                    "verdict": "pass",
                    "reason": {"code": "ok", "message": "ok"},
                    "observed_status": "success",
                    "observed_error": None,
                }
            ],
            required_sample_ids=["sample-success"],
            version="v0.2.0",
        )

        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=malformed_harness_report,
            real_adapter_regression_report=validate_real_adapter_regression_source_report(
                self.valid_real_adapter_regression_payload(),
                version="v0.2.0",
                reference_pair=["xhs", "douyin"],
            ),
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
            required_harness_sample_ids=["sample-success"],
        )

        self.assertEqual(report["source_reports"]["harness"]["evidence_refs"], ["synthetic:harness:invalid_sample_id"])

    def test_orchestrator_deduplicates_failed_harness_failures(self) -> None:
        failed_harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure", "sample-missing"],
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
            required_harness_sample_ids=["sample-success", "sample-legal-failure", "sample-missing"],
        )

        self.assertEqual(
            sum(1 for item in report["failures"] if item["code"] == "missing_required_harness_samples"),
            1,
        )

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

    def test_orchestrator_rebinds_failed_real_regression_evidence_refs_to_frozen_case_order(self) -> None:
        forged_real_regression_report = validate_real_adapter_regression_source_report(
            self.valid_real_adapter_regression_payload(),
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )
        forged_real_regression_report["verdict"] = "fail"
        forged_real_regression_report["summary"] = "forged failed regression report"
        forged_real_regression_report["evidence_refs"] = [
            "regression:douyin:platform",
            "regression:xhs:success",
        ]

        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=build_harness_source_report(
                self.valid_harness_results(),
                required_sample_ids=["sample-success", "sample-legal-failure"],
                version="v0.2.0",
            ),
            real_adapter_regression_report=forged_real_regression_report,
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
        )

        source_report = report["source_reports"]["real_adapter_regression"]
        self.assertEqual(source_report["verdict"], "fail")
        self.assertEqual(
            source_report["evidence_refs"],
            [
                "regression:xhs:success",
                "regression:xhs:invalid-input",
                "regression:douyin:success",
                "regression:douyin:platform",
            ],
        )
        self.assertNotEqual(source_report["evidence_refs"], forged_real_regression_report["evidence_refs"])
        self.assertIn("case_evidence_refs_mismatch", {item["code"] for item in report["failures"]})

    def test_orchestrator_rejects_real_regression_report_missing_projection_details(self) -> None:
        forged_report = validate_real_adapter_regression_source_report(
            self.valid_real_adapter_regression_payload(),
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )
        forged_report["details"].pop("target_type")
        forged_report["details"].pop("semantic_operation")

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
        self.assertIn("missing_real_regression_details", {item["code"] for item in report["failures"]})

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

    def test_orchestrator_fail_closes_on_non_json_failure_details(self) -> None:
        forged_harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )
        forged_harness_report["verdict"] = "fail"
        forged_harness_report["details"]["failures"] = [
            {
                "code": "forged_non_json_failure",
                "message": "forged non json details",
                "details": {"bad": {"nested_set": {1, 2}}},
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

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("forged_non_json_failure", {item["code"] for item in report["failures"]})

    def test_orchestrator_rejects_unhashable_source_report_verdict(self) -> None:
        forged_harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )
        forged_harness_report["verdict"] = {"bad": 1}

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

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("invalid_source_verdict", {item["code"] for item in report["failures"]})
        json.dumps(report)

    def test_orchestrator_preserves_real_regression_validator_failure_reason(self) -> None:
        payload = self.valid_real_adapter_regression_payload()
        payload["evidence_refs"] = {"forged:1": True}
        failed_real_regression_report = validate_real_adapter_regression_source_report(
            payload,
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

        self.assertIn("invalid_evidence_refs", {item["code"] for item in report["failures"]})
        self.assertNotIn("missing_source_evidence_refs", {item["code"] for item in report["failures"]})

    def test_orchestrator_preserves_platform_leakage_validator_failure_reason(self) -> None:
        payload = self.valid_platform_leakage_payload()
        payload["evidence_refs"] = []
        failed_platform_leakage_report = validate_platform_leakage_source_report(
            payload,
            version="v0.2.0",
        )

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
            platform_leakage_report=failed_platform_leakage_report,
        )

        self.assertIn("missing_evidence_refs", {item["code"] for item in report["failures"]})
        self.assertNotIn("missing_source_evidence_refs", {item["code"] for item in report["failures"]})

    def test_orchestrator_round_trips_failed_platform_leakage_report(self) -> None:
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
        failed_platform_leakage_report = validate_platform_leakage_source_report(
            payload,
            version="v0.2.0",
        )

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
            platform_leakage_report=failed_platform_leakage_report,
        )

        self.assertIn("platform_branch_in_core", {item["code"] for item in report["failures"]})
        self.assertNotIn("invalid_leakage_finding_boundary", {item["code"] for item in report["failures"]})
        self.assertNotIn("failure_report_without_findings", {item["code"] for item in report["failures"]})

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
                "target_type": "url",
                "semantic_operation": "content_detail_by_url",
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

    def test_orchestrator_accepts_platform_leakage_checker_output(self) -> None:
        leakage_report = run_platform_leakage_check(
            version="v0.2.0",
            repo_root=Path(__file__).resolve().parents[2],
        )

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
            platform_leakage_report=leakage_report,
        )

        self.assertEqual(leakage_report["source"], "platform_leakage")
        self.assertEqual(leakage_report["verdict"], "pass")
        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["source_reports"]["platform_leakage"]["details"]["report_verdict"], "pass")
        self.assertEqual(report["source_reports"]["platform_leakage"]["details"]["findings"], [])

    def test_orchestrator_round_trips_checker_detected_multiline_platform_branch(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            for relative_name in ("syvert/runtime.py", "syvert/registry.py", "syvert/version_gate.py"):
                source_path = repo_root / relative_name
                target_path = fixture_root / relative_name
                target_path.parent.mkdir(parents=True, exist_ok=True)
                contents = source_path.read_text(encoding="utf-8")
                if relative_name == "syvert/runtime.py":
                    contents = contents.replace(
                        "    adapter_key, capability = extract_request_context(request)\n",
                        '    adapter_key, capability = extract_request_context(request)\n'
                        "    if (\n"
                        "        adapter_key\n"
                        '        == "weibo"\n'
                        "    ):\n"
                        "        return None\n\n",
                        1,
                    )
                target_path.write_text(contents, encoding="utf-8")

            leakage_report = run_platform_leakage_check(
                version="v0.2.0",
                repo_root=fixture_root,
            )

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
            platform_leakage_report=leakage_report,
        )

        self.assertEqual(leakage_report["verdict"], "fail")
        self.assertEqual(report["source_reports"]["platform_leakage"]["details"]["report_verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["failures"]})

    def test_orchestrator_round_trips_checker_parse_failure(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            for relative_name in ("syvert/runtime.py", "syvert/registry.py", "syvert/version_gate.py"):
                source_path = repo_root / relative_name
                target_path = fixture_root / relative_name
                target_path.parent.mkdir(parents=True, exist_ok=True)
                contents = source_path.read_text(encoding="utf-8")
                if relative_name == "syvert/runtime.py":
                    contents = contents.replace(
                        "    adapter_key, capability = extract_request_context(request)\n",
                        "    adapter_key, capability = extract_request_context(request)\n    if (\n",
                        1,
                    )
                target_path.write_text(contents, encoding="utf-8")

            leakage_report = run_platform_leakage_check(
                version="v0.2.0",
                repo_root=fixture_root,
            )

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
            platform_leakage_report=leakage_report,
        )

        self.assertEqual(leakage_report["verdict"], "fail")
        self.assertEqual(report["source_reports"]["platform_leakage"]["details"]["report_verdict"], "fail")
        self.assertIn("scan_parse_failure", {item["code"] for item in report["failures"]})

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

    def test_orchestrator_pass_result_is_json_serializable_with_non_json_harness_observed_error_details(self) -> None:
        harness_results = self.valid_harness_results()
        harness_results[1]["observed_error"]["details"] = {"nested_set": {1, 2}}
        harness_report = build_harness_source_report(
            harness_results,
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )

        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=harness_report,
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

        self.assertEqual(report["verdict"], "pass")
        json.dumps(report)

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

    def test_public_orchestrator_consumes_real_harness_output_end_to_end(self) -> None:
        validation_results = run_contract_harness_automation()
        required_sample_ids = [result["sample_id"] for result in validation_results]
        harness_report = build_harness_source_report(
            validation_results,
            required_sample_ids=required_sample_ids,
            version="v0.2.0",
        )

        report = version_gate_module.orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=harness_report,
            real_adapter_regression_report=validate_real_adapter_regression_source_report(
                self.valid_real_adapter_regression_payload(),
                version="v0.2.0",
                reference_pair=["xhs", "douyin"],
            ),
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
            required_harness_sample_ids=required_sample_ids,
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertFalse(report["safe_to_release"])
        self.assertEqual(report["summary"], "version gate failed for version `v0.2.0` via harness")
        self.assertEqual(
            set(report["source_reports"]),
            {"harness", "real_adapter_regression", "platform_leakage"},
        )
        self.assertTrue(
            {"harness"}.issubset({item["source"] for item in report["failures"]})
        )

        orchestrated_harness_report = report["source_reports"]["harness"]
        self.assertEqual(orchestrated_harness_report["verdict"], "fail")
        self.assertEqual(
            orchestrated_harness_report["details"]["required_sample_ids"],
            required_sample_ids,
        )
        self.assertEqual(
            orchestrated_harness_report["details"]["observed_sample_ids"],
            sorted(required_sample_ids),
        )
        self.assertEqual(
            orchestrated_harness_report["evidence_refs"],
            harness_report["evidence_refs"],
        )
        self.assertTrue(
            {"contract_violation_observed", "execution_precondition_not_met_observed"}.issubset(
                {item["code"] for item in orchestrated_harness_report["details"]["failures"]}
            )
        )

    def test_public_orchestrator_requires_explicit_harness_required_sample_baseline(self) -> None:
        report = _orchestrate_version_gate(
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
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("missing_required_harness_sample_ids", {item["code"] for item in report["failures"]})

    def test_public_orchestrator_accepts_tuple_required_harness_sample_ids(self) -> None:
        report = _orchestrate_version_gate(
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
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
            required_harness_sample_ids=("sample-success", "sample-legal-failure"),
        )

        self.assertEqual(report["verdict"], "pass")

    def test_public_orchestrator_accepts_reordered_required_harness_sample_ids(self) -> None:
        report = _orchestrate_version_gate(
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
            platform_leakage_report=validate_platform_leakage_source_report(
                self.valid_platform_leakage_payload(),
                version="v0.2.0",
            ),
            required_harness_sample_ids=["sample-legal-failure", "sample-success"],
        )

        self.assertEqual(report["verdict"], "pass")

    def test_public_orchestrator_consumes_real_adapter_regression_output_end_to_end(self) -> None:
        harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )
        regression_report = run_real_adapter_regression(
            version="v0.2.0",
            adapters=self.hermetic_real_regression_adapters(),
        )
        leakage_report = validate_platform_leakage_source_report(
            self.valid_platform_leakage_payload(),
            version="v0.2.0",
        )

        report = version_gate_module.orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=harness_report,
            real_adapter_regression_report=regression_report,
            platform_leakage_report=leakage_report,
            required_harness_sample_ids=["sample-success", "sample-legal-failure"],
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["source_reports"]["real_adapter_regression"]["verdict"], "pass")

    def test_public_orchestrator_fails_closed_when_real_regression_uses_spoofed_adapter(self) -> None:
        harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )
        regression_report = run_real_adapter_regression(
            version="v0.2.0",
            adapters=self.spoofed_real_regression_adapters(),
        )
        leakage_report = validate_platform_leakage_source_report(
            self.valid_platform_leakage_payload(),
            version="v0.2.0",
        )

        report = version_gate_module.orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=harness_report,
            real_adapter_regression_report=regression_report,
            platform_leakage_report=leakage_report,
            required_harness_sample_ids=["sample-success", "sample-legal-failure"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn(
            "invalid_reference_adapter_identity",
            {
                item["code"]
                for item in report["source_reports"]["real_adapter_regression"]["details"]["failures"]
            },
        )

    def test_public_orchestrator_rejects_required_harness_sample_ids_override_when_frozen(self) -> None:
        original = version_gate_module._FROZEN_HARNESS_REQUIRED_SAMPLE_IDS_BY_VERSION.get("v0.2.0")
        version_gate_module._FROZEN_HARNESS_REQUIRED_SAMPLE_IDS_BY_VERSION["v0.2.0"] = (
            "sample-success",
            "sample-legal-failure",
        )
        try:
            report = _orchestrate_version_gate(
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
                platform_leakage_report=validate_platform_leakage_source_report(
                    self.valid_platform_leakage_payload(),
                    version="v0.2.0",
                ),
                required_harness_sample_ids=["sample-success"],
            )
        finally:
            if original is None:
                version_gate_module._FROZEN_HARNESS_REQUIRED_SAMPLE_IDS_BY_VERSION.pop("v0.2.0", None)
            else:
                version_gate_module._FROZEN_HARNESS_REQUIRED_SAMPLE_IDS_BY_VERSION["v0.2.0"] = original

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("required_harness_sample_ids_not_frozen_for_version", {item["code"] for item in report["failures"]})

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
            "target_type": "url",
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
                            "evidence_ref": "regression:xhs:success",
                            "expected_outcome": "success",
                            "observed_status": "success",
                            "observed_error_category": None,
                        },
                        {
                            "case_id": "xhs-invalid-input",
                            "evidence_ref": "regression:xhs:invalid-input",
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
                            "evidence_ref": "regression:douyin:success",
                            "expected_outcome": "success",
                            "observed_status": "success",
                            "observed_error_category": None,
                        },
                        {
                            "case_id": "douyin-platform",
                            "evidence_ref": "regression:douyin:platform",
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

    def assert_source_report_contract_shape(self, source: str, report: dict[str, object]) -> None:
        self.assertEqual(report["source"], source)
        self.assertIn(report["verdict"], {"pass", "fail"})
        self.assertTrue(report["version"])
        self.assertTrue(report["summary"])
        self.assertTrue(report["evidence_refs"])
        self.assertIsInstance(report["details"], dict)
        self.assertIn("failures", report["details"])
        self.assertIsInstance(report["details"]["failures"], list)

        if source == "harness":
            self.assertTrue(
                {"required_sample_ids", "observed_sample_ids", "validation_results", "failures"}.issubset(
                    report["details"]
                )
            )
        elif source == "real_adapter_regression":
            self.assertTrue(
                {"reference_pair", "operation", "target_type", "semantic_operation", "adapter_results", "failures"}.issubset(report["details"])
            )
        elif source == "platform_leakage":
            self.assertTrue(
                {"boundary_scope", "report_verdict", "findings", "failures"}.issubset(report["details"])
            )

    @staticmethod
    def hermetic_real_regression_adapters() -> dict[str, object]:
        from tests.runtime.test_real_adapter_regression import (
            build_douyin_aweme_detail,
        )
        from syvert.adapters.douyin import DouyinAdapter, DouyinSessionConfig
        from syvert.adapters.xhs import XhsAdapter, XhsSessionConfig

        xhs_adapter = XhsAdapter(
            session_provider=lambda path: XhsSessionConfig(
                cookies="a=1; b=2",
                user_agent="Mozilla/5.0 TestAgent",
                sign_base_url="http://127.0.0.1:8000",
                timeout_seconds=7,
            ),
            sign_transport=lambda base_url, payload, timeout_seconds: {
                "x_s": "signed-x-s",
                "x_t": "signed-x-t",
                "x_s_common": "signed-x-s-common",
                "x_b3_traceid": "trace-1",
            },
            detail_transport=lambda **kwargs: {
                "success": True,
                "data": {
                    "items": [
                        {
                            "note_card": {
                                "note_id": "66fad51c000000001b0224b8",
                                "type": "video",
                                "title": "测试标题",
                                "desc": "测试正文",
                                "time": 1712304300,
                                "user": {
                                    "user_id": "user-1",
                                    "nickname": "作者甲",
                                    "avatar": "https://cdn.example/avatar.jpg",
                                },
                                "interact_info": {
                                    "liked_count": "11",
                                    "comment_count": "12",
                                    "share_count": "13",
                                    "collected_count": "14",
                                },
                                "image_list": [
                                    {"url_default": "https://cdn.example/image-1.jpg"},
                                    {"url_default": "https://cdn.example/image-2.jpg"},
                                ],
                                "video": {
                                    "consumer": {
                                        "origin_video_key": "video-key-1",
                                    }
                                },
                                "cover": {
                                    "url_default": "https://cdn.example/cover.jpg",
                                },
                            }
                        }
                    ]
                },
            },
        )
        douyin_adapter = DouyinAdapter(
            session_provider=lambda path: DouyinSessionConfig(
                cookies="a=1; b=2",
                user_agent="Mozilla/5.0 TestAgent",
                verify_fp="verify-1",
                ms_token="ms-token-1",
                webid="webid-1",
                sign_base_url="http://127.0.0.1:8000",
                timeout_seconds=5,
            ),
            sign_transport=lambda base_url, payload, timeout_seconds: {"a_bogus": "signed-1"},
            detail_transport=lambda **kwargs: (
                {"status_code": 0, "aweme_detail": build_douyin_aweme_detail()}
                if kwargs["params"]["aweme_id"] == "7580570616932224282"
                else (_ for _ in ()).throw(RuntimeError("detail-failed"))
            ),
            page_state_transport=lambda **kwargs: (_ for _ in ()).throw(
                PlatformAdapterError(
                    code="douyin_browser_target_tab_missing",
                    message="browser recovery disabled for hermetic regression",
                    details={},
                )
            ),
        )
        return {"xhs": xhs_adapter, "douyin": douyin_adapter}

    @staticmethod
    def spoofed_real_regression_adapters() -> dict[str, object]:
        from tests.runtime.test_real_adapter_regression import (
            ShapeContractSpoofAdapter,
        )

        adapters = VersionGateTests.hermetic_real_regression_adapters()
        adapters["xhs"] = ShapeContractSpoofAdapter("xhs")
        return adapters


if __name__ == "__main__":
    unittest.main()
