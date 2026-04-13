from __future__ import annotations

import unittest

from tests.runtime.contract_harness import (
    ContractSampleDefinition,
    HarnessExecutionResult,
    validate_contract_sample,
    validate_contract_samples,
)

def build_success_envelope() -> dict[str, object]:
    return {
        "task_id": "task-success",
        "adapter_key": "fake",
        "capability": "content_detail_by_url",
        "status": "success",
        "raw": {"content_id": "raw-1"},
        "normalized": {
            "platform": "fake",
            "content_id": "content-1",
            "content_type": "unknown",
            "canonical_url": "https://example.com/content/1",
            "title": "",
            "body_text": "",
            "published_at": None,
            "author": {
                "author_id": None,
                "display_name": None,
                "avatar_url": None,
            },
            "stats": {
                "like_count": None,
                "comment_count": None,
                "share_count": None,
                "collect_count": None,
            },
            "media": {
                "cover_url": None,
                "video_url": None,
                "image_urls": [],
            },
        },
    }


def build_failed_envelope(category: str) -> dict[str, object]:
    return {
        "task_id": "task-failed",
        "adapter_key": "fake",
        "capability": "content_detail_by_url",
        "status": "failed",
        "error": {
            "category": category,
            "code": "error-code",
            "message": "error message",
            "details": {"reason": "fixture"},
        },
    }


class ContractHarnessValidationToolTests(unittest.TestCase):
    def test_returns_pass_for_success_sample_with_success_envelope(self) -> None:
        sample = ContractSampleDefinition(sample_id="sample-success", expected_outcome="success")
        execution_result = HarnessExecutionResult(runtime_envelope=build_success_envelope())

        result = validate_contract_sample(sample, execution_result)

        self.assertEqual(result["sample_id"], "sample-success")
        self.assertEqual(result["verdict"], "pass")
        self.assertEqual(result["reason"]["code"], "success_envelope_observed")
        self.assertEqual(result["observed_status"], "success")
        self.assertIsNone(result["observed_error"])

    def test_success_sample_with_missing_normalized_result_is_contract_violation(self) -> None:
        sample = ContractSampleDefinition(sample_id="sample-success", expected_outcome="success")
        runtime_envelope = build_success_envelope()
        del runtime_envelope["normalized"]
        execution_result = HarnessExecutionResult(runtime_envelope=runtime_envelope)

        result = validate_contract_sample(sample, execution_result)

        self.assertEqual(result["verdict"], "contract_violation")
        self.assertEqual(result["reason"]["code"], "invalid_adapter_success_payload")

    def test_returns_legal_failure_for_fr0005_failed_envelope(self) -> None:
        sample = ContractSampleDefinition(sample_id="sample-legal-failure", expected_outcome="legal_failure")
        runtime_envelope = build_failed_envelope("unsupported")
        runtime_envelope["error"]["code"] = "capability_not_supported"
        runtime_envelope["error"]["message"] = "unsupported capability"
        execution_result = HarnessExecutionResult(runtime_envelope=runtime_envelope)

        result = validate_contract_sample(sample, execution_result)

        self.assertEqual(result["verdict"], "legal_failure")
        self.assertEqual(result["reason"]["code"], "legal_failed_envelope_observed")
        self.assertEqual(result["observed_status"], "failed")
        self.assertEqual(result["observed_error"]["category"], "unsupported")
        self.assertEqual(result["observed_error"]["code"], "capability_not_supported")

    def test_returns_contract_violation_for_contract_violation_sample(self) -> None:
        sample = ContractSampleDefinition(sample_id="sample-contract-violation", expected_outcome="contract_violation")
        runtime_envelope = build_failed_envelope("runtime_contract")
        runtime_envelope["error"]["code"] = "invalid_adapter_payload"
        runtime_envelope["error"]["message"] = "adapter payload shape mismatch"
        execution_result = HarnessExecutionResult(runtime_envelope=runtime_envelope)

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
        runtime_envelope = build_failed_envelope("invalid_input")
        runtime_envelope["error"]["code"] = "invalid_task_request"
        runtime_envelope["error"]["message"] = "target_type is invalid"
        execution_result = HarnessExecutionResult(runtime_envelope=runtime_envelope)

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
        runtime_envelope = build_failed_envelope("platform")
        del runtime_envelope["error"]["category"]
        execution_result = HarnessExecutionResult(runtime_envelope=runtime_envelope)

        result = validate_contract_sample(sample, execution_result)

        self.assertEqual(result["verdict"], "contract_violation")
        self.assertEqual(result["reason"]["code"], "invalid_runtime_error_category")
        self.assertEqual(result["observed_status"], "failed")

    def test_runtime_contract_failure_does_not_count_as_legal_failure(self) -> None:
        sample = ContractSampleDefinition(sample_id="sample-runtime-contract", expected_outcome="legal_failure")
        runtime_envelope = build_failed_envelope("runtime_contract")
        runtime_envelope["error"]["code"] = "invalid_adapter_payload"
        runtime_envelope["error"]["message"] = "adapter payload shape mismatch"
        execution_result = HarnessExecutionResult(runtime_envelope=runtime_envelope)

        result = validate_contract_sample(sample, execution_result)

        self.assertEqual(result["verdict"], "contract_violation")
        self.assertEqual(result["reason"]["code"], "runtime_contract_failure_observed")

    def test_legal_failure_requires_runtime_context_fields_and_error_details(self) -> None:
        sample = ContractSampleDefinition(sample_id="sample-malformed-failure", expected_outcome="legal_failure")
        runtime_envelope = build_failed_envelope("platform")
        runtime_envelope["task_id"] = ""
        del runtime_envelope["error"]["details"]
        execution_result = HarnessExecutionResult(runtime_envelope=runtime_envelope)

        result = validate_contract_sample(sample, execution_result)

        self.assertEqual(result["verdict"], "contract_violation")
        self.assertEqual(result["reason"]["code"], "invalid_runtime_task_id")


if __name__ == "__main__":
    unittest.main()
