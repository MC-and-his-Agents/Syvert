from __future__ import annotations

import unittest

from tests.runtime.contract_harness import (
    ContractSampleDefinition,
    HarnessExecutionResult,
    validate_contract_sample,
    validate_contract_samples,
)


class ContractHarnessValidationToolTests(unittest.TestCase):
    def test_returns_pass_for_success_sample_with_success_envelope(self) -> None:
        sample = ContractSampleDefinition(sample_id="sample-success", expected_outcome="success")
        execution_result = HarnessExecutionResult(runtime_envelope={"status": "success"})

        result = validate_contract_sample(sample, execution_result)

        self.assertEqual(result["sample_id"], "sample-success")
        self.assertEqual(result["verdict"], "pass")
        self.assertEqual(result["reason"]["code"], "success_envelope_observed")
        self.assertEqual(result["observed_status"], "success")
        self.assertIsNone(result["observed_error"])

    def test_returns_legal_failure_for_fr0005_failed_envelope(self) -> None:
        sample = ContractSampleDefinition(sample_id="sample-legal-failure", expected_outcome="legal_failure")
        execution_result = HarnessExecutionResult(
            runtime_envelope={
                "status": "failed",
                "error": {
                    "category": "unsupported",
                    "code": "capability_not_supported",
                    "message": "unsupported capability",
                },
            }
        )

        result = validate_contract_sample(sample, execution_result)

        self.assertEqual(result["verdict"], "legal_failure")
        self.assertEqual(result["reason"]["code"], "legal_failed_envelope_observed")
        self.assertEqual(result["observed_status"], "failed")
        self.assertEqual(result["observed_error"]["category"], "unsupported")
        self.assertEqual(result["observed_error"]["code"], "capability_not_supported")

    def test_returns_contract_violation_for_contract_violation_sample(self) -> None:
        sample = ContractSampleDefinition(sample_id="sample-contract-violation", expected_outcome="contract_violation")
        execution_result = HarnessExecutionResult(
            runtime_envelope={
                "status": "failed",
                "error": {
                    "category": "runtime_contract",
                    "code": "invalid_adapter_payload",
                    "message": "adapter payload shape mismatch",
                },
            }
        )

        result = validate_contract_sample(sample, execution_result)

        self.assertEqual(result["verdict"], "contract_violation")
        self.assertEqual(result["reason"]["code"], "runtime_contract_failure_observed")
        self.assertEqual(result["observed_status"], "failed")
        self.assertEqual(result["observed_error"]["category"], "runtime_contract")

    def test_returns_execution_precondition_not_met_before_core_execution(self) -> None:
        sample = ContractSampleDefinition(sample_id="sample-precondition", expected_outcome="success")
        execution_result = HarnessExecutionResult(
            precondition_code="fake_adapter_not_registered",
            precondition_message="fake adapter missing from harness host registry",
        )

        result = validate_contract_sample(sample, execution_result)

        self.assertEqual(result["verdict"], "execution_precondition_not_met")
        self.assertEqual(result["reason"]["code"], "fake_adapter_not_registered")
        self.assertIsNone(result["observed_status"])
        self.assertIsNone(result["observed_error"])

    def test_core_invalid_input_is_classified_as_legal_failure_not_precondition(self) -> None:
        sample = ContractSampleDefinition(sample_id="sample-invalid-input", expected_outcome="legal_failure")
        execution_result = HarnessExecutionResult(
            runtime_envelope={
                "status": "failed",
                "error": {
                    "category": "invalid_input",
                    "code": "invalid_task_request",
                    "message": "target_type is invalid",
                },
            }
        )

        result = validate_contract_sample(sample, execution_result)

        self.assertEqual(result["verdict"], "legal_failure")
        self.assertEqual(result["reason"]["code"], "legal_failed_envelope_observed")
        self.assertEqual(result["observed_error"]["category"], "invalid_input")

    def test_batch_validation_marks_missing_execution_result_as_precondition_not_met(self) -> None:
        samples = [
            ContractSampleDefinition(sample_id="sample-missing", expected_outcome="success"),
        ]

        results = validate_contract_samples(samples, execution_results={})

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["sample_id"], "sample-missing")
        self.assertEqual(results[0]["verdict"], "execution_precondition_not_met")
        self.assertEqual(results[0]["reason"]["code"], "missing_harness_execution_result")

    def test_legal_failure_sample_with_malformed_failed_envelope_is_contract_violation(self) -> None:
        sample = ContractSampleDefinition(sample_id="sample-malformed-failure", expected_outcome="legal_failure")
        execution_result = HarnessExecutionResult(
            runtime_envelope={
                "status": "failed",
                "error": {
                    "code": "missing_category",
                    "message": "category is missing",
                },
            }
        )

        result = validate_contract_sample(sample, execution_result)

        self.assertEqual(result["verdict"], "contract_violation")
        self.assertEqual(result["reason"]["code"], "invalid_runtime_error_category")
        self.assertEqual(result["observed_status"], "failed")


if __name__ == "__main__":
    unittest.main()
