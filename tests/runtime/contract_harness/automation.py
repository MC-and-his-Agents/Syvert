from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from tests.runtime.contract_harness.fake_adapter import FakeContractAdapter
from tests.runtime.contract_harness.host import HarnessExecutionInput, execute_harness_sample
from tests.runtime.contract_harness.samples import CONTRACT_SAMPLES, ContractSample, ExpectedVerdict
from tests.runtime.contract_harness.validation_tool import (
    ContractSampleDefinition,
    HarnessExecutionResult,
    validate_contract_samples,
)

_EXPECTED_OUTCOME_BY_VERDICT = {
    ExpectedVerdict.PASS: "success",
    ExpectedVerdict.LEGAL_FAILURE: "legal_failure",
    ExpectedVerdict.CONTRACT_VIOLATION: "contract_violation",
    ExpectedVerdict.EXECUTION_PRECONDITION_NOT_MET: "success",
}


def build_contract_sample_definitions(
    samples: Iterable[ContractSample],
) -> list[ContractSampleDefinition]:
    return [
        ContractSampleDefinition(
            sample_id=sample.sample_id,
            expected_outcome=_EXPECTED_OUTCOME_BY_VERDICT[sample.expected_verdict],
        )
        for sample in samples
    ]


def execute_harness_samples(
    samples: Iterable[ContractSample],
) -> dict[str, HarnessExecutionResult]:
    return {
        sample.sample_id: _execute_single_sample(sample)
        for sample in samples
    }


def run_contract_harness_automation(
    samples: Sequence[ContractSample] = CONTRACT_SAMPLES,
) -> list[dict[str, Any]]:
    execution_results = execute_harness_samples(samples)
    return validate_contract_harness_run(samples, execution_results)


def validate_contract_harness_run(
    samples: Sequence[ContractSample],
    execution_results: Mapping[str, HarnessExecutionResult],
) -> list[dict[str, Any]]:
    definitions = build_contract_sample_definitions(samples)
    validation_results = validate_contract_samples(definitions, execution_results)
    sample_index = build_sample_index(samples)
    fail_closed_results: list[dict[str, Any]] = []
    for result in validation_results:
        sample = sample_index[result["sample_id"]]
        execution_result = execution_results.get(sample.sample_id)
        if (
            sample.expected_verdict == ExpectedVerdict.EXECUTION_PRECONDITION_NOT_MET
            and execution_result is not None
            and execution_result.runtime_envelope is not None
        ):
            fail_closed_results.append(
                {
                    "sample_id": sample.sample_id,
                    "verdict": "contract_violation",
                    "reason": {
                        "code": "precondition_sample_unexpectedly_reached_runtime",
                        "message": "precondition sample unexpectedly produced runtime envelope",
                    },
                    "observed_status": result["observed_status"],
                    "observed_error": result["observed_error"],
                }
            )
            continue
        fail_closed_results.append(result)
    return fail_closed_results


def build_expected_verdict_index(
    samples: Iterable[ContractSample],
) -> Mapping[str, str]:
    return {sample.sample_id: sample.expected_verdict.value for sample in samples}


def build_sample_index(
    samples: Iterable[ContractSample],
) -> Mapping[str, ContractSample]:
    return {sample.sample_id: sample for sample in samples}


def _execute_single_sample(sample: ContractSample) -> HarnessExecutionResult:
    if sample.expected_verdict == ExpectedVerdict.EXECUTION_PRECONDITION_NOT_MET:
        return HarnessExecutionResult(
            precondition_code="fake_adapter_not_registered",
            precondition_message="fake adapter is intentionally not registered for this sample",
        )

    profile = sample.adapter_profile
    if profile is None:
        return HarnessExecutionResult(
            precondition_code="missing_fake_adapter_profile",
            precondition_message="sample requires adapter profile before harness execution",
        )

    adapter = FakeContractAdapter(scenario=profile.scenario)
    envelope = execute_harness_sample(
        HarnessExecutionInput(
            sample_id=sample.sample_id,
            url=sample.input.target_url,
            adapter_key=sample.input.adapter_key,
            capability=sample.input.capability,
        ),
        adapters={sample.input.adapter_key: adapter},
        task_id=f"task-{sample.sample_id}",
    )
    return HarnessExecutionResult(runtime_envelope=envelope)
