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
    definitions = build_contract_sample_definitions(samples)
    execution_results = execute_harness_samples(samples)
    return validate_contract_samples(definitions, execution_results)


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
