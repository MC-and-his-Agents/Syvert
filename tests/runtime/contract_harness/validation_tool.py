from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Literal

SampleExpectation = Literal["success", "legal_failure", "contract_violation"]
ValidationVerdict = Literal[
    "pass",
    "legal_failure",
    "contract_violation",
    "execution_precondition_not_met",
]

_ALLOWED_RUNTIME_ERROR_CATEGORIES = frozenset(
    {"invalid_input", "unsupported", "runtime_contract", "platform"}
)


@dataclass(frozen=True)
class ContractSampleDefinition:
    sample_id: str
    expected_outcome: SampleExpectation


@dataclass(frozen=True)
class HarnessExecutionResult:
    runtime_envelope: Mapping[str, Any] | None = None
    precondition_code: str | None = None
    precondition_message: str | None = None


def validate_contract_sample(
    sample: ContractSampleDefinition,
    execution_result: HarnessExecutionResult,
) -> dict[str, Any]:
    if execution_result.precondition_code:
        return _build_result(
            sample_id=sample.sample_id,
            verdict="execution_precondition_not_met",
            reason_code=execution_result.precondition_code,
            reason_message=execution_result.precondition_message or "harness precondition is not met",
            observed_status=None,
            observed_error=None,
        )

    envelope = execution_result.runtime_envelope
    if envelope is None:
        return _build_result(
            sample_id=sample.sample_id,
            verdict="contract_violation",
            reason_code="missing_runtime_envelope",
            reason_message="harness execution result is missing runtime envelope",
            observed_status=None,
            observed_error=None,
        )
    if not isinstance(envelope, Mapping):
        return _build_result(
            sample_id=sample.sample_id,
            verdict="contract_violation",
            reason_code="invalid_runtime_envelope_type",
            reason_message="runtime envelope must be a mapping",
            observed_status=None,
            observed_error=None,
        )

    observed_status_raw = envelope.get("status")
    observed_status = observed_status_raw if isinstance(observed_status_raw, str) else None
    observed_error_raw = envelope.get("error")
    observed_error = observed_error_raw if isinstance(observed_error_raw, Mapping) else None

    if observed_status not in {"success", "failed"}:
        return _build_result(
            sample_id=sample.sample_id,
            verdict="contract_violation",
            reason_code="invalid_runtime_status",
            reason_message="runtime envelope has unsupported status value",
            observed_status=observed_status,
            observed_error=observed_error,
        )

    if sample.expected_outcome == "success":
        if observed_status == "success":
            return _build_result(
                sample_id=sample.sample_id,
                verdict="pass",
                reason_code="success_envelope_observed",
                reason_message="sample expected success and observed a valid success envelope",
                observed_status=observed_status,
                observed_error=observed_error,
            )
        return _build_result(
            sample_id=sample.sample_id,
            verdict="contract_violation",
            reason_code="unexpected_failed_envelope",
            reason_message="sample expected success but observed failed envelope",
            observed_status=observed_status,
            observed_error=observed_error,
        )

    if sample.expected_outcome == "legal_failure":
        return _classify_legal_failure_sample(
            sample_id=sample.sample_id,
            observed_status=observed_status,
            observed_error=observed_error,
        )

    return _classify_contract_violation_sample(
        sample_id=sample.sample_id,
        observed_status=observed_status,
        observed_error=observed_error,
    )


def validate_contract_samples(
    samples: Iterable[ContractSampleDefinition],
    execution_results: Mapping[str, HarnessExecutionResult],
) -> list[dict[str, Any]]:
    validation_results: list[dict[str, Any]] = []
    for sample in samples:
        execution_result = execution_results.get(sample.sample_id)
        if execution_result is None:
            validation_results.append(
                _build_result(
                    sample_id=sample.sample_id,
                    verdict="execution_precondition_not_met",
                    reason_code="missing_harness_execution_result",
                    reason_message="sample has no harness execution result",
                    observed_status=None,
                    observed_error=None,
                )
            )
            continue
        validation_results.append(validate_contract_sample(sample, execution_result))
    return validation_results


def _classify_legal_failure_sample(
    *,
    sample_id: str,
    observed_status: str | None,
    observed_error: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if observed_status != "failed":
        return _build_result(
            sample_id=sample_id,
            verdict="contract_violation",
            reason_code="unexpected_success_envelope",
            reason_message="sample expected legal failure but observed success envelope",
            observed_status=observed_status,
            observed_error=observed_error,
        )
    if observed_error is None:
        return _build_result(
            sample_id=sample_id,
            verdict="contract_violation",
            reason_code="missing_error_object",
            reason_message="failed runtime envelope must carry error object",
            observed_status=observed_status,
            observed_error=observed_error,
        )

    error_category = observed_error.get("category")
    if not isinstance(error_category, str) or not error_category:
        return _build_result(
            sample_id=sample_id,
            verdict="contract_violation",
            reason_code="invalid_runtime_error_category",
            reason_message="runtime error category is missing or invalid",
            observed_status=observed_status,
            observed_error=observed_error,
        )
    if error_category not in _ALLOWED_RUNTIME_ERROR_CATEGORIES:
        return _build_result(
            sample_id=sample_id,
            verdict="contract_violation",
            reason_code="unsupported_runtime_error_category",
            reason_message="runtime error category is outside FR-0005 allowed categories",
            observed_status=observed_status,
            observed_error=observed_error,
        )

    error_code = observed_error.get("code")
    if not isinstance(error_code, str) or not error_code:
        return _build_result(
            sample_id=sample_id,
            verdict="contract_violation",
            reason_code="invalid_runtime_error_code",
            reason_message="runtime error code is missing or invalid",
            observed_status=observed_status,
            observed_error=observed_error,
        )

    return _build_result(
        sample_id=sample_id,
        verdict="legal_failure",
        reason_code="legal_failed_envelope_observed",
        reason_message="sample expected legal failure and observed FR-0005 compliant failed envelope",
        observed_status=observed_status,
        observed_error=observed_error,
    )


def _classify_contract_violation_sample(
    *,
    sample_id: str,
    observed_status: str | None,
    observed_error: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if observed_status == "failed" and observed_error is not None:
        error_category = observed_error.get("category")
        if error_category == "runtime_contract":
            return _build_result(
                sample_id=sample_id,
                verdict="contract_violation",
                reason_code="runtime_contract_failure_observed",
                reason_message="runtime contract failure observed for contract violation sample",
                observed_status=observed_status,
                observed_error=observed_error,
            )
        return _build_result(
            sample_id=sample_id,
            verdict="contract_violation",
            reason_code="expected_contract_violation_observed_other_failure",
            reason_message="contract violation sample did not resolve to runtime_contract category",
            observed_status=observed_status,
            observed_error=observed_error,
        )

    if observed_status == "success":
        return _build_result(
            sample_id=sample_id,
            verdict="contract_violation",
            reason_code="expected_contract_violation_but_observed_success",
            reason_message="contract violation sample unexpectedly produced success envelope",
            observed_status=observed_status,
            observed_error=observed_error,
        )

    return _build_result(
        sample_id=sample_id,
        verdict="contract_violation",
        reason_code="invalid_observation_for_contract_violation",
        reason_message="contract violation sample observation is incomplete",
        observed_status=observed_status,
        observed_error=observed_error,
    )


def _build_result(
    *,
    sample_id: str,
    verdict: ValidationVerdict,
    reason_code: str,
    reason_message: str,
    observed_status: str | None,
    observed_error: Mapping[str, Any] | None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "sample_id": sample_id,
        "verdict": verdict,
        "reason": {
            "code": reason_code,
            "message": reason_message,
        },
        "observed_status": observed_status,
        "observed_error": dict(observed_error) if observed_error is not None else None,
    }
    return result
