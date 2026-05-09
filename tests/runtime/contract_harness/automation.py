from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
import tempfile
from typing import Any

from syvert.resource_lifecycle import ResourceRecord
from syvert.resource_lifecycle_store import LocalResourceLifecycleStore
from tests.runtime.contract_harness.fake_adapter import FakeContractAdapter
from tests.runtime.contract_harness.host import HarnessExecutionInput, execute_harness_sample
from tests.runtime.contract_harness.samples import CONTRACT_SAMPLES, ContractSample, ExpectedVerdict
from tests.runtime.contract_harness.validation_tool import (
    ContractSampleDefinition,
    HarnessExecutionResult,
    validate_contract_samples,
)
from tests.runtime.resource_fixtures import generic_account_material, managed_account_material, proxy_material

_EXPECTED_OUTCOME_BY_VERDICT = {
    ExpectedVerdict.PASS: "success",
    ExpectedVerdict.LEGAL_FAILURE: "legal_failure",
    ExpectedVerdict.CONTRACT_VIOLATION: "contract_violation",
}


def build_contract_sample_definitions(
    samples: Iterable[ContractSample],
) -> list[ContractSampleDefinition]:
    return [
        ContractSampleDefinition(
            sample_id=sample.sample_id,
            expected_outcome=_EXPECTED_OUTCOME_BY_VERDICT[sample.expected_verdict],
            target_type="url",
            target_value=sample.input.target_url,
        )
        for sample in samples
        if sample.expected_verdict != ExpectedVerdict.EXECUTION_PRECONDITION_NOT_MET
    ]


def execute_harness_samples(
    samples: Iterable[ContractSample],
) -> dict[str, HarnessExecutionResult]:
    execution_results: dict[str, HarnessExecutionResult] = {}
    for sample in samples:
        _store_unique_sample_id(execution_results, sample.sample_id)
        execution_results[sample.sample_id] = _execute_single_sample(sample)
    return execution_results


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
    results_by_sample_id = {result["sample_id"]: result for result in validation_results}
    fail_closed_results: list[dict[str, Any]] = []
    for sample in samples:
        result = results_by_sample_id.get(sample.sample_id)
        execution_result = execution_results.get(sample.sample_id)
        if (
            sample.expected_verdict == ExpectedVerdict.EXECUTION_PRECONDITION_NOT_MET
        ):
            if execution_result is not None and execution_result.runtime_envelope is not None:
                fail_closed_results.append(
                    {
                        "sample_id": sample.sample_id,
                        "verdict": "contract_violation",
                        "reason": {
                            "code": "precondition_sample_unexpectedly_reached_runtime",
                            "message": "precondition sample unexpectedly produced runtime envelope",
                        },
                        "observed_status": None,
                        "observed_error": None,
                    }
                )
                continue
            if execution_result is not None and execution_result.precondition_code:
                fail_closed_results.append(
                    {
                        "sample_id": sample.sample_id,
                        "verdict": "execution_precondition_not_met",
                        "reason": {
                            "code": execution_result.precondition_code,
                            "message": execution_result.precondition_message
                            or "harness precondition is not met",
                        },
                        "observed_status": None,
                        "observed_error": None,
                    }
                )
                continue
            fail_closed_results.append(
                {
                    "sample_id": sample.sample_id,
                    "verdict": "execution_precondition_not_met",
                    "reason": {
                        "code": "missing_harness_execution_result",
                        "message": "sample has no harness execution result",
                    },
                    "observed_status": None,
                    "observed_error": None,
                }
            )
            continue
        if result is not None:
            fail_closed_results.append(result)
    return fail_closed_results


def build_expected_verdict_index(
    samples: Iterable[ContractSample],
) -> Mapping[str, str]:
    verdict_index: dict[str, str] = {}
    for sample in samples:
        _store_unique_sample_id(verdict_index, sample.sample_id)
        verdict_index[sample.sample_id] = sample.expected_verdict.value
    return verdict_index


def build_sample_index(
    samples: Iterable[ContractSample],
) -> Mapping[str, ContractSample]:
    sample_index: dict[str, ContractSample] = {}
    for sample in samples:
        _store_unique_sample_id(sample_index, sample.sample_id)
        sample_index[sample.sample_id] = sample
    return sample_index


def _execute_single_sample(sample: ContractSample) -> HarnessExecutionResult:
    if sample.adapter_profile is None:
        return HarnessExecutionResult(
            precondition_code="fake_adapter_not_registered",
            precondition_message="fake adapter is intentionally not registered for this sample",
        )

    profile = sample.adapter_profile
    metadata_error = _validate_sample_metadata(sample)
    if metadata_error is not None:
        return HarnessExecutionResult(
            precondition_code=metadata_error["code"],
            precondition_message=metadata_error["message"],
        )

    adapter = FakeContractAdapter(scenario=profile.scenario)
    adapter.supported_capabilities = frozenset(profile.declared_capabilities)
    adapter.supported_targets = frozenset(profile.supported_targets)
    adapter.supported_collection_modes = frozenset(profile.supported_collection_modes)
    with tempfile.TemporaryDirectory(prefix=f"syvert-harness-{sample.sample_id}-") as temp_dir:
        resource_store = LocalResourceLifecycleStore(Path(temp_dir) / "resource-lifecycle.json")
        resource_store.seed_resources(
            [
                ResourceRecord(
                    resource_id="fake-account-001",
                    resource_type="account",
                    status="AVAILABLE",
                    material=managed_account_material(generic_account_material(), adapter_key=sample.input.adapter_key),
                ),
                ResourceRecord(
                    resource_id="fake-proxy-001",
                    resource_type="proxy",
                    status="AVAILABLE",
                    material=proxy_material(),
                ),
            ]
        )
        envelope = execute_harness_sample(
            HarnessExecutionInput(
                sample_id=sample.sample_id,
                url=sample.input.target_url,
                adapter_key=sample.input.adapter_key,
                capability=sample.input.capability,
            ),
            adapters={sample.input.adapter_key: adapter},
            task_id=f"task-{sample.sample_id}",
            resource_lifecycle_store=resource_store,
        )
    return HarnessExecutionResult(runtime_envelope=envelope)


def _validate_sample_metadata(sample: ContractSample) -> dict[str, str] | None:
    profile = sample.adapter_profile
    if profile is None:
        return {
            "code": "missing_fake_adapter_profile",
            "message": "sample requires adapter profile before harness execution",
        }
    if sample.input.adapter_key != profile.adapter_key:
        return {
            "code": "sample_adapter_key_mismatch",
            "message": "sample input adapter_key does not match adapter profile",
        }
    return None


def _store_unique_sample_id(index: Mapping[str, object], sample_id: str) -> None:
    if sample_id in index:
        raise ValueError(f"duplicate contract sample_id: {sample_id}")
