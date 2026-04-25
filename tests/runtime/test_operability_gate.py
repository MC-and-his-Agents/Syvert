from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from syvert.operability_gate import (
    FAIL_VERDICT,
    PASS_VERDICT,
    POLICY_SNAPSHOT,
    mandatory_operability_case_ids,
    orchestrate_operability_gate,
)
from tests.runtime.render_operability_gate_artifact import assert_revision_is_current_head, build_gate_input_from_source_evidence


class OperabilityGateTests(unittest.TestCase):
    def test_operability_gate_passes_with_complete_mandatory_matrix(self) -> None:
        result = self.pass_result()

        self.assertEqual(result["verdict"], PASS_VERDICT)
        self.assertTrue(result["safe_to_release"])
        self.assertEqual(result["release"], "v0.6.0")
        self.assertEqual(result["fr_item_key"], "FR-0019-v0-6-operability-release-gate")
        self.assertEqual(result["baseline_gate_ref"], "FR-0007:version_gate:v0.6.0:baseline:test-head-sha")
        self.assertEqual(set(result["normative_dependencies"]), {"FR-0007", "FR-0016", "FR-0017", "FR-0018"})
        self.assertEqual(result["policy_snapshot"], POLICY_SNAPSHOT)
        self.assertEqual({case["case_id"] for case in result["cases"]}, set(mandatory_operability_case_ids()))
        self.assertEqual(result["summary"]["fail_case_total"], 0)
        self.assertGreaterEqual(result["metrics_snapshot"]["submit_total"], 1)
        self.assertGreaterEqual(result["metrics_snapshot"]["same_path_case_total"], 4)
        json.dumps(result)

    def test_missing_baseline_gate_ref_fails_closed(self) -> None:
        result = self.pass_result(baseline_gate_ref="")

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertFalse(result["safe_to_release"])
        self.assertIn("missing_baseline_gate_ref", self.failure_codes(result))

    def test_invalid_baseline_gate_ref_fails_closed(self) -> None:
        result = self.pass_result(baseline_gate_ref="not-fr-0007-at-all:test-head-sha")

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("invalid_baseline_gate_ref", self.failure_codes(result))

    def test_missing_baseline_gate_result_fails_closed(self) -> None:
        result = self.pass_result(baseline_gate_result=None)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("missing_baseline_gate_result", self.failure_codes(result))

    def test_non_pass_baseline_gate_result_fails_closed(self) -> None:
        baseline = self.valid_baseline_gate_result()
        baseline["verdict"] = "fail"
        baseline["safe_to_release"] = False

        result = self.pass_result(baseline_gate_result=baseline)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("baseline_gate_not_passed", self.failure_codes(result))

    def test_baseline_gate_result_ref_must_match_requested_ref(self) -> None:
        baseline = self.valid_baseline_gate_result()
        baseline["baseline_gate_ref"] = "FR-0007:version_gate:v0.6.0:baseline:other-head"

        result = self.pass_result(baseline_gate_result=baseline)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("baseline_gate_ref_mismatch", self.failure_codes(result))

    def test_baseline_gate_ref_rejects_substring_forgery(self) -> None:
        result = self.pass_result(baseline_gate_ref="garbage-prefix-FR-0007-garbage:test-head-sha")

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("invalid_baseline_gate_ref", self.failure_codes(result))

    def test_baseline_gate_ref_rejects_wrong_release(self) -> None:
        result = self.pass_result(baseline_gate_ref="FR-0007:version_gate:v0.5.0:baseline:test-head-sha")

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("baseline_gate_ref_mismatch", self.failure_codes(result))

    def test_baseline_gate_ref_rejects_wrong_tail_segment_or_revision(self) -> None:
        wrong_tail = self.pass_result(baseline_gate_ref="FR-0007:version_gate:v0.6.0:other:test-head-sha")
        wrong_revision = self.pass_result(baseline_gate_ref="FR-0007:version_gate:v0.6.0:baseline:other-head")

        self.assertEqual(wrong_tail["verdict"], FAIL_VERDICT)
        self.assertEqual(wrong_revision["verdict"], FAIL_VERDICT)
        self.assertIn("baseline_gate_ref_mismatch", self.failure_codes(wrong_tail))
        self.assertIn("baseline_gate_ref_mismatch", self.failure_codes(wrong_revision))

    def test_reviewable_non_private_baseline_ref_is_allowed_when_resolved_result_matches(self) -> None:
        baseline = self.valid_baseline_gate_result()
        baseline["baseline_gate_ref"] = "gate:test-head-sha:FR-0007:v0.6.0:baseline"

        result = self.pass_result(baseline_gate_ref=baseline["baseline_gate_ref"], baseline_gate_result=baseline)

        self.assertEqual(result["verdict"], PASS_VERDICT)

    def test_baseline_gate_ref_must_match_execution_revision(self) -> None:
        baseline = self.valid_baseline_gate_result()
        baseline["baseline_gate_ref"] = "gate:old-head:FR-0007:v0.6.0:baseline"

        result = self.pass_result(baseline_gate_ref=baseline["baseline_gate_ref"], baseline_gate_result=baseline)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("baseline_gate_ref_revision_mismatch", self.failure_codes(result))

    def test_baseline_gate_ref_rejects_near_fr_number_forgery(self) -> None:
        baseline = self.valid_baseline_gate_result()
        forged = "FR-00070:version_gate:v0.6.0:test-head-sha:baseline"
        baseline["baseline_gate_ref"] = forged

        result = self.pass_result(baseline_gate_ref=forged, baseline_gate_result=baseline)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("invalid_baseline_gate_ref", self.failure_codes(result))

    def test_reviewable_ci_log_metrics_evidence_refs_are_allowed(self) -> None:
        cases = self.valid_cases()
        cases[0]["evidence_refs"] = ["ci:test-head-sha:fr-0019:trc-timeout-platform-control-code"]
        cases[0]["upstream_refs"] = ["log:test-head-sha:tests.runtime.test_execution_control"]

        result = self.pass_result(
            cases=cases,
            evidence_refs=["metrics:test-head-sha:fr-0019:summary"],
        )

        self.assertEqual(result["verdict"], PASS_VERDICT)

    def test_gate_id_and_matrix_version_are_frozen(self) -> None:
        result = self.pass_result(gate_id="totally-different-gate", matrix_version="scratch-matrix")

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("gate_id_mismatch", self.failure_codes(result))
        self.assertIn("matrix_version_mismatch", self.failure_codes(result))

    def test_missing_mandatory_case_fails_closed(self) -> None:
        cases = self.valid_cases()
        cases = [case for case in cases if case["case_id"] != "same-path-terminal-result-read"]

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("missing_mandatory_cases", self.failure_codes(result))
        missing_failure = next(item for item in result["failures"] if item["code"] == "missing_mandatory_cases")
        self.assertEqual(missing_failure["details"]["missing_case_ids"], ["same-path-terminal-result-read"])

    def test_invalid_case_entries_are_reflected_in_summary(self) -> None:
        result = self.pass_result(cases=[{}])

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("missing_case_id", self.failure_codes(result))
        self.assertGreaterEqual(result["summary"]["fail_case_total"], 1)
        self.assertIn("invalid-case-0", result["summary"]["failed_case_ids"])

    def test_generated_cases_have_reviewable_preconditions(self) -> None:
        cases = self.valid_cases()

        for case in cases:
            self.assertNotIn(f"precondition:{case['case_id']}", case["preconditions"])
            self.assertIn("capability=content_detail_by_url", case["preconditions"])

    def test_invalid_metrics_snapshot_fails_closed(self) -> None:
        metrics = self.valid_metrics()
        metrics.pop("timeout_total")
        metrics["retry_attempt_total"] = -1

        result = self.pass_result(metrics_snapshot=metrics)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("invalid_metrics_snapshot_field", self.failure_codes(result))
        self.assertEqual(result["metrics_snapshot"]["timeout_total"], 0)

    def test_semantically_wrong_metrics_fail_closed(self) -> None:
        metrics = dict.fromkeys(self.valid_metrics(), 0)

        result = self.pass_result(metrics_snapshot=metrics)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("metrics_snapshot_value_insufficient", self.failure_codes(result))

    def test_policy_snapshot_drift_fails_closed(self) -> None:
        policy = deepcopy(POLICY_SNAPSHOT)
        policy["concurrency"]["max_in_flight"] = 2

        result = self.pass_result(policy_snapshot=policy)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("policy_snapshot_mismatch", self.failure_codes(result))

    def test_case_local_policy_drift_fails_closed(self) -> None:
        cases = self.valid_cases()
        target = next(case for case in cases if case["case_id"] == "trc-timeout-platform-control-code")
        target["actual_result"]["policy"]["retry"]["max_attempts"] = 999

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("actual_result_snapshot_mismatch", self.failure_codes(result))

    def test_case_policy_assertions_use_gate_snapshot_not_case_forgery(self) -> None:
        cases = self.valid_cases()
        target = next(case for case in cases if case["case_id"] == "trc-timeout-platform-control-code")
        target["actual_result"]["policy"]["timeout_ms"] = 99999
        target["actual_result"]["policy"]["retry"]["max_attempts"] = 999
        policy = deepcopy(POLICY_SNAPSHOT)
        policy["timeout_ms"] = 99999
        policy["retry"]["max_attempts"] = 999

        result = self.pass_result(policy_snapshot=policy, cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("policy_snapshot_mismatch", self.failure_codes(result))
        self.assertIn("actual_result_field_mismatch", self.failure_codes(result))

    def test_case_local_metrics_drift_fails_closed(self) -> None:
        cases = self.valid_cases()
        target = next(case for case in cases if case["case_id"] == "flm-success-observable")
        target["actual_result"]["metrics"]["success_total"] = 0

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("actual_result_snapshot_mismatch", self.failure_codes(result))

    def test_case_metrics_assertions_use_gate_snapshot_not_case_forgery(self) -> None:
        cases = self.valid_cases()
        target = next(case for case in cases if case["case_id"] == "flm-success-observable")
        target["actual_result"]["metrics"]["success_total"] = 99
        metrics = self.valid_metrics()
        metrics["success_total"] = 0

        result = self.pass_result(metrics_snapshot=metrics, cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("metrics_snapshot_value_insufficient", self.failure_codes(result))
        self.assertIn("actual_result_field_mismatch", self.failure_codes(result))

    def test_case_policy_and_metrics_assertions_require_case_observation(self) -> None:
        cases = self.valid_cases()
        policy_case = next(case for case in cases if case["case_id"] == "trc-timeout-platform-control-code")
        metrics_case = next(case for case in cases if case["case_id"] == "flm-success-observable")
        policy_case["actual_result"].pop("policy")
        metrics_case["actual_result"].pop("metrics")

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("actual_result_field_missing", self.failure_codes(result))

    def test_mandatory_case_expected_field_drift_fails_closed(self) -> None:
        cases = self.valid_cases()
        target = next(case for case in cases if case["case_id"] == "trc-timeout-platform-control-code")
        target["expected_result"]["fields"] = [
            field for field in target["expected_result"]["fields"] if field["path"] != "error.category"
        ]

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("mandatory_case_expected_fields_missing", self.failure_codes(result))

    def test_missing_side_effects_fail_closed(self) -> None:
        cases = self.valid_cases()
        target = next(case for case in cases if case["case_id"] == "trc-timeout-platform-control-code")
        target["actual_result"].pop("side_effects")

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("actual_result_side_effects_missing", self.failure_codes(result))

    def test_missing_forbidden_mutation_proof_fails_closed(self) -> None:
        cases = self.valid_cases()
        target = next(case for case in cases if case["case_id"] == "trc-concurrent-result-shared-truth")
        target["actual_result"]["forbidden_mutations_absent"] = ["shadow_status"]

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("actual_result_forbidden_mutation_proof_missing", self.failure_codes(result))

    def test_mandatory_forbidden_mutation_drift_fails_closed(self) -> None:
        cases = self.valid_cases()
        target = next(case for case in cases if case["case_id"] == "trc-concurrent-result-shared-truth")
        target["expected_result"]["forbidden_mutations"] = []
        target["actual_result"]["forbidden_mutations_absent"] = []

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("mandatory_case_forbidden_mutations_mismatch", self.failure_codes(result))

    def test_case_verdict_is_derived_from_validator_failures(self) -> None:
        cases = self.valid_cases()
        target = next(case for case in cases if case["case_id"] == "trc-timeout-platform-control-code")
        target["actual_result"]["error"]["category"] = "runtime_contract"

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("actual_result_field_mismatch", self.failure_codes(result))
        self.assertEqual(result["summary"]["fail_case_total"], 1)
        self.assertEqual(result["summary"]["failed_case_ids"], ["trc-timeout-platform-control-code"])
        result_case = next(case for case in result["cases"] if case["case_id"] == "trc-timeout-platform-control-code")
        self.assertEqual(result_case["verdict"], FAIL_VERDICT)

    def test_missing_non_empty_field_fails_closed(self) -> None:
        cases = self.valid_cases()
        target = next(case for case in cases if case["case_id"] == "trc-pre-accept-concurrency-reject")
        target["actual_result"].pop("request_ref")

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("actual_result_field_missing", self.failure_codes(result))

    def test_missing_path_to_path_values_fail_closed(self) -> None:
        cases = self.valid_cases()
        target = next(case for case in cases if case["case_id"] == "same-path-terminal-result-read")
        target["actual_result"]["cli"]["result"].pop("task_id")
        target["actual_result"]["http"]["result"].pop("task_id")

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("actual_result_field_missing", self.failure_codes(result))

    def test_missing_envelope_ref_fails_closed(self) -> None:
        cases = self.valid_cases()
        target = next(case for case in cases if case["case_id"] == "http-submit-status-result-shared-truth")
        target["actual_result"]["result"].pop("envelope_ref")

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("actual_result_field_missing", self.failure_codes(result))

    def test_malformed_greater_than_expected_value_fails_closed(self) -> None:
        cases = self.valid_cases()
        target = next(case for case in cases if case["case_id"] == "flm-success-observable")
        for field in target["expected_result"]["fields"]:
            if field["operator"] == ">=":
                field["value"] = "not-a-number"

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("invalid_expected_result_field_value", self.failure_codes(result))

    def test_malformed_in_expected_value_fails_closed(self) -> None:
        cases = self.valid_cases()
        target = next(case for case in cases if case["case_id"] == "flm-business-failure-observable")
        for field in target["expected_result"]["fields"]:
            if field["operator"] == "in":
                field["value"] = 123

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("invalid_expected_result_field_value", self.failure_codes(result))

    def test_zero_metrics_are_reflected_in_failed_case_summary(self) -> None:
        metrics = dict.fromkeys(self.valid_metrics(), 0)

        result = self.pass_result(metrics_snapshot=metrics)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("metrics_snapshot_value_insufficient", self.failure_codes(result))

    def test_dimension_or_capability_drift_fails_closed(self) -> None:
        cases = self.valid_cases()
        target = next(case for case in cases if case["case_id"] == "http-submit-status-result-shared-truth")
        target["dimension"] = "cli_api_same_path"
        target["capability"] = "creator_detail"

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("case_dimension_mismatch", self.failure_codes(result))
        self.assertIn("invalid_case_capability", self.failure_codes(result))

    def test_failed_mandatory_case_fails_overall_gate(self) -> None:
        cases = self.valid_cases()
        cases[0]["verdict"] = FAIL_VERDICT

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertEqual(result["summary"]["fail_case_total"], 1)
        self.assertEqual(result["summary"]["failed_case_ids"], [cases[0]["case_id"]])
        self.assertIn("mandatory_case_failed", self.failure_codes(result))

    def test_case_missing_actual_result_or_evidence_fails_closed(self) -> None:
        cases = self.valid_cases()
        cases[0]["actual_result_ref"] = ""
        cases[0]["evidence_refs"] = []

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("missing_actual_result_ref", self.failure_codes(result))
        self.assertIn("missing_evidence_refs", self.failure_codes(result))

    def test_case_missing_evidence_refs_field_fails_closed(self) -> None:
        cases = self.valid_cases()
        cases[0].pop("evidence_refs")

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("missing_case_evidence_refs", self.failure_codes(result))

    def test_case_scoped_metadata_failures_update_case_verdict(self) -> None:
        cases = self.valid_cases()
        cases[0]["entrypoints"] = ["core", ""]

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("invalid_entrypoints", self.failure_codes(result))
        self.assertEqual(result["summary"]["fail_case_total"], 1)
        self.assertEqual(result["summary"]["failed_case_ids"], [cases[0]["case_id"]])
        result_case = next(case for case in result["cases"] if case["case_id"] == cases[0]["case_id"])
        self.assertEqual(result_case["verdict"], FAIL_VERDICT)

    def test_execution_revision_must_be_bound_to_evidence_refs(self) -> None:
        result = self.pass_result(execution_revision="other-head")

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("execution_revision_evidence_mismatch", self.failure_codes(result))

    def test_execution_revision_binding_rejects_substring_overlap(self) -> None:
        cases = self.valid_cases()
        for case in cases:
            case["actual_result_ref"] = f"operability:otherhead:{case['case_id']}"
            case["evidence_refs"] = [f"operability:otherhead:{case['case_id']}"]

        result = self.pass_result(
            execution_revision="head",
            baseline_gate_ref="FR-0007:version_gate:v0.6.0:baseline:otherhead",
            cases=cases,
            evidence_refs=["FR-0007:version_gate:v0.6.0:baseline:otherhead"],
        )

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("execution_revision_evidence_mismatch", self.failure_codes(result))

    def test_case_upstream_refs_must_match_execution_revision(self) -> None:
        cases = self.valid_cases()
        cases[0]["upstream_refs"] = ["tests:other-rev:tests.runtime.test_execution_control"]

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("upstream_refs_revision_mismatch", self.failure_codes(result))
        self.assertIn("execution_revision_evidence_mismatch", self.failure_codes(result))

    def test_renderer_rejects_non_head_execution_revision(self) -> None:
        with self.assertRaises(SystemExit):
            assert_revision_is_current_head("not-current-head")

    def test_renderer_missing_source_evidence_fails_closed_as_gate_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "source.json"
            source_path.write_text(json.dumps({"cases": []}), encoding="utf-8")

            gate_input = build_gate_input_from_source_evidence(revision="test-head-sha", source_path=source_path)
            result = orchestrate_operability_gate(**gate_input)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("baseline_gate_not_passed", self.failure_codes(result))
        self.assertIn("missing_mandatory_cases", self.failure_codes(result))

    def test_renderer_partial_source_evidence_fails_closed_as_gate_result(self) -> None:
        valid_source = json.loads(Path("docs/exec-plans/artifacts/CHORE-0158-operability-source-evidence.json").read_text())
        valid_source["cases"] = valid_source["cases"][:-1]
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "source.json"
            source_path.write_text(json.dumps(valid_source), encoding="utf-8")

            gate_input = build_gate_input_from_source_evidence(revision="test-head-sha", source_path=source_path)
            result = orchestrate_operability_gate(**gate_input)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("missing_mandatory_cases", self.failure_codes(result))

    def test_renderer_case_without_id_or_upstream_modules_fails_closed(self) -> None:
        valid_source = json.loads(Path("docs/exec-plans/artifacts/CHORE-0158-operability-source-evidence.json").read_text())
        valid_source["cases"][0].pop("case_id")
        valid_source["cases"][1].pop("upstream_modules")
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "source.json"
            source_path.write_text(json.dumps(valid_source), encoding="utf-8")

            gate_input = build_gate_input_from_source_evidence(revision="test-head-sha", source_path=source_path)
            result = orchestrate_operability_gate(**gate_input)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("missing_mandatory_cases", self.failure_codes(result))

    def test_external_actual_result_ref_fails_closed(self) -> None:
        cases = self.valid_cases()
        cases[0]["actual_result_ref"] = "https://example.invalid/not-reviewable"

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("invalid_actual_result_ref", self.failure_codes(result))

    def test_unapproved_extra_dimension_fails_closed(self) -> None:
        cases = self.valid_cases()
        extra_case = deepcopy(cases[0])
        extra_case["case_id"] = "experimental-extra-case"
        extra_case["dimension"] = "totally_new_dimension"
        extra_case["evidence_refs"] = ["operability:test-head-sha:experimental-extra-case"]
        cases.append(extra_case)

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("invalid_case_dimension", self.failure_codes(result))

    def test_unapproved_entrypoint_fails_closed_for_extension_case(self) -> None:
        cases = self.valid_cases()
        extra_case = deepcopy(cases[0])
        extra_case["case_id"] = "extension-case"
        extra_case["dimension"] = "failure_log_metrics"
        extra_case["entrypoints"] = ["ssh"]
        extra_case["evidence_refs"] = ["test_evidence:test-head-sha:extension-case"]
        extra_case["actual_result_ref"] = "operability:test-head-sha:extension-case"
        cases.append(extra_case)

        result = self.pass_result(cases=cases)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("invalid_case_entrypoints", self.failure_codes(result))

    def test_external_evidence_refs_fail_closed(self) -> None:
        cases = self.valid_cases()
        cases[0]["evidence_refs"] = ["https://dashboard.example.invalid/test-head-sha/case"]

        result = self.pass_result(
            cases=cases,
            evidence_refs=["https://dashboard.example.invalid/test-head-sha/baseline"],
        )

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("invalid_evidence_ref", self.failure_codes(result))

    def test_normative_dependency_drift_fails_closed(self) -> None:
        result = self.pass_result(normative_dependencies=["FR-0007", "FR-0016", "FR-0018"])

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("missing_normative_dependencies", self.failure_codes(result))

    def pass_result(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = build_gate_input_from_source_evidence(revision="test-head-sha")
        payload.update(overrides)
        return orchestrate_operability_gate(**payload)

    def valid_cases(self) -> list[dict[str, object]]:
        return build_gate_input_from_source_evidence(revision="test-head-sha")["cases"]

    def valid_baseline_gate_result(self) -> dict[str, object]:
        return build_gate_input_from_source_evidence(revision="test-head-sha")["baseline_gate_result"]

    def valid_metrics(self) -> dict[str, int]:
        return {
            "submit_total": 2,
            "success_total": 2,
            "failure_total": 8,
            "timeout_total": 1,
            "retry_attempt_total": 0,
            "concurrency_case_total": 3,
            "concurrency_case_failure_total": 1,
            "same_path_case_total": 4,
            "same_path_case_failure_total": 1,
        }

    def failure_codes(self, result: dict[str, object]) -> set[str]:
        return {str(item["code"]) for item in result["failures"]}


if __name__ == "__main__":
    unittest.main()
