from __future__ import annotations

from dataclasses import replace
import unittest

from tests.runtime.contract_harness import (
    CONTRACT_SAMPLES,
    HarnessExecutionResult,
    build_expected_verdict_index,
    build_sample_index,
    execute_harness_samples,
    run_contract_harness_automation,
    validate_contract_harness_run,
)


class ContractHarnessAutomationTests(unittest.TestCase):
    def test_catalog_covers_four_fr0006_stable_sample_classes(self) -> None:
        self.assertEqual(
            [sample.sample_id for sample in CONTRACT_SAMPLES],
            [
                "success-full-envelope",
                "legal-failure-platform-envelope",
                "contract-violation-missing-normalized",
                "execution-precondition-not-met",
            ],
        )

    def test_automation_returns_expected_verdicts_for_all_samples(self) -> None:
        results = run_contract_harness_automation()

        observed = {result["sample_id"]: result["verdict"] for result in results}

        self.assertEqual(observed, build_expected_verdict_index(CONTRACT_SAMPLES))

    def test_automation_preserves_expected_runtime_status_and_error_categories(self) -> None:
        samples_by_id = build_sample_index(CONTRACT_SAMPLES)
        execution_results = execute_harness_samples(CONTRACT_SAMPLES)
        verdicts = {
            result["sample_id"]: result
            for result in run_contract_harness_automation()
        }

        for sample_id, sample in samples_by_id.items():
            execution_result = execution_results[sample_id]
            verdict = verdicts[sample_id]
            self.assertEqual(verdict["observed_status"], sample.expected_runtime_status)
            if sample.expected_runtime_error_category is None:
                self.assertIsNone(verdict["observed_error"])
                if sample.expected_runtime_status is None:
                    self.assertIsNone(execution_result.runtime_envelope)
                else:
                    self.assertIsNotNone(execution_result.runtime_envelope)
                continue
            self.assertIsNotNone(execution_result.runtime_envelope)
            self.assertIsNotNone(verdict["observed_error"])
            self.assertEqual(
                verdict["observed_error"]["category"],
                sample.expected_runtime_error_category,
            )

    def test_success_sample_keeps_raw_and_normalized_envelope(self) -> None:
        execution_results = execute_harness_samples(CONTRACT_SAMPLES)

        success_envelope = execution_results["success-full-envelope"].runtime_envelope

        self.assertIsNotNone(success_envelope)
        self.assertEqual(success_envelope["status"], "success")
        self.assertIn("raw", success_envelope)
        self.assertIn("normalized", success_envelope)

    def test_precondition_sample_that_unexpectedly_reaches_runtime_fails_closed(self) -> None:
        samples_by_id = build_sample_index(CONTRACT_SAMPLES)
        sample = replace(
            samples_by_id["execution-precondition-not-met"],
            adapter_profile=samples_by_id["success-full-envelope"].adapter_profile,
            input=samples_by_id["success-full-envelope"].input,
        )
        success_runtime = execute_harness_samples([samples_by_id["success-full-envelope"]])[
            "success-full-envelope"
        ]

        results = validate_contract_harness_run(
            [sample],
            {"execution-precondition-not-met": HarnessExecutionResult(runtime_envelope=success_runtime.runtime_envelope)},
        )

        self.assertEqual(results[0]["verdict"], "contract_violation")
        self.assertEqual(
            results[0]["reason"]["code"],
            "precondition_sample_unexpectedly_reached_runtime",
        )


if __name__ == "__main__":
    unittest.main()
