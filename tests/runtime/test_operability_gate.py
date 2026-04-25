from __future__ import annotations

from copy import deepcopy
import json
import unittest

from syvert.operability_gate import (
    FAIL_VERDICT,
    PASS_VERDICT,
    POLICY_SNAPSHOT,
    build_mandatory_operability_cases,
    mandatory_operability_case_ids,
    orchestrate_operability_gate,
)


class OperabilityGateTests(unittest.TestCase):
    def test_operability_gate_passes_with_complete_mandatory_matrix(self) -> None:
        result = self.pass_result()

        self.assertEqual(result["verdict"], PASS_VERDICT)
        self.assertTrue(result["safe_to_release"])
        self.assertEqual(result["release"], "v0.6.0")
        self.assertEqual(result["fr_item_key"], "FR-0019-v0-6-operability-release-gate")
        self.assertEqual(result["baseline_gate_ref"], "FR-0007:version_gate:v0.6.0:baseline")
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

    def test_baseline_gate_ref_rejects_substring_forgery(self) -> None:
        result = self.pass_result(baseline_gate_ref="garbage-prefix-FR-0007-garbage:test-head-sha")

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("invalid_baseline_gate_ref", self.failure_codes(result))

    def test_baseline_gate_ref_rejects_wrong_release(self) -> None:
        result = self.pass_result(baseline_gate_ref="FR-0007:version_gate:v0.5.0:baseline:test-head-sha")

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("invalid_baseline_gate_ref", self.failure_codes(result))

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
        self.assertIn("actual_result_field_mismatch", self.failure_codes(result))

    def test_policy_snapshot_drift_fails_closed(self) -> None:
        policy = deepcopy(POLICY_SNAPSHOT)
        policy["concurrency"]["max_in_flight"] = 2

        result = self.pass_result(policy_snapshot=policy)

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("policy_snapshot_mismatch", self.failure_codes(result))

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
        self.assertGreater(result["summary"]["fail_case_total"], 0)
        self.assertIn("http-submit-status-result-shared-truth", result["summary"]["failed_case_ids"])

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

    def test_normative_dependency_drift_fails_closed(self) -> None:
        result = self.pass_result(normative_dependencies=["FR-0007", "FR-0016", "FR-0018"])

        self.assertEqual(result["verdict"], FAIL_VERDICT)
        self.assertIn("missing_normative_dependencies", self.failure_codes(result))

    def pass_result(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "execution_revision": "test-head-sha",
            "baseline_gate_ref": "FR-0007:version_gate:v0.6.0:baseline",
            "cases": self.valid_cases(),
            "metrics_snapshot": self.valid_metrics(),
            "evidence_refs": ["FR-0007:version_gate:v0.6.0:baseline:test-head-sha"],
        }
        payload.update(overrides)
        return orchestrate_operability_gate(**payload)

    def valid_cases(self) -> list[dict[str, object]]:
        cases = build_mandatory_operability_cases()
        for case in cases:
            case["actual_result_ref"] = f"operability:test-head-sha:{case['case_id']}"
            case["evidence_refs"] = [f"operability:test-head-sha:{case['case_id']}"]
            case["actual_result"] = self.actual_result_for_case(case)
        return cases

    def actual_result_for_case(self, case: dict[str, object]) -> dict[str, object]:
        expected_result = case["expected_result"]
        actual_result: dict[str, object] = {"case": {"id": case["case_id"]}}
        for field in expected_result["fields"]:
            path = field["path"]
            operator = field["operator"]
            value = field["value"]
            if isinstance(value, str) and "." in value and operator == "==":
                shared_value = f"tests.runtime.test_operability_gate:{case['case_id']}:{path}"
                self.set_path(actual_result, path, shared_value)
                self.set_path(actual_result, value, shared_value)
            elif operator == "!=":
                self.set_path(actual_result, path, f"tests.runtime.test_operability_gate:{case['case_id']}:ref")
            elif operator == "in":
                self.set_path(actual_result, path, list(value)[0])
            else:
                self.set_path(actual_result, path, deepcopy(value))
        actual_result["side_effects"] = list(expected_result["side_effects"])
        actual_result["forbidden_mutations_absent"] = list(expected_result["forbidden_mutations"])
        return actual_result

    def set_path(self, mapping: dict[str, object], path: str, value: object) -> None:
        current = mapping
        segments = path.split(".")
        for segment in segments[:-1]:
            child = current.get(segment)
            if not isinstance(child, dict):
                child = {}
                current[segment] = child
            current = child
        current[segments[-1]] = value

    def valid_metrics(self) -> dict[str, int]:
        return {
            "submit_total": 2,
            "success_total": 2,
            "failure_total": 8,
            "timeout_total": 1,
            "retry_attempt_total": 0,
            "concurrency_case_total": 3,
            "concurrency_case_failure_total": 0,
            "same_path_case_total": 4,
            "same_path_case_failure_total": 1,
        }

    def failure_codes(self, result: dict[str, object]) -> set[str]:
        return {str(item["code"]) for item in result["failures"]}


if __name__ == "__main__":
    unittest.main()
