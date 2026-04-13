"""Contract harness sample catalog for FR-0006."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

from syvert.runtime import CONTENT_DETAIL_BY_URL, LEGACY_COLLECTION_MODE
from tests.runtime.contract_harness.fake_adapter import FakeAdapterScenario


class ExpectedVerdict(Enum):
    PASS = "pass"
    LEGAL_FAILURE = "legal_failure"
    CONTRACT_VIOLATION = "contract_violation"
    EXECUTION_PRECONDITION_NOT_MET = "execution_precondition_not_met"


@dataclass(frozen=True)
class FakeAdapterProfile:
    adapter_key: str
    scenario: FakeAdapterScenario
    declared_capabilities: Sequence[str]
    supported_targets: Sequence[str]
    supported_collection_modes: Sequence[str]


@dataclass(frozen=True)
class SampleInput:
    adapter_key: str
    capability: str = CONTENT_DETAIL_BY_URL
    target_url: str = "https://example.com/resource"
    target_type: str = "url"
    collection_mode: str = LEGACY_COLLECTION_MODE


@dataclass(frozen=True)
class ContractSample:
    sample_id: str
    description: str
    input: SampleInput
    expected_verdict: ExpectedVerdict
    expected_runtime_status: str | None
    expected_runtime_error_category: str | None
    adapter_profile: FakeAdapterProfile | None = None
    precondition_notes: Sequence[str] = field(default_factory=tuple)


SUCCESS_PROFILE = FakeAdapterProfile(
    adapter_key="fake:contract-success",
    scenario="success",
    declared_capabilities=("content_detail",),
    supported_targets=("url",),
    supported_collection_modes=(LEGACY_COLLECTION_MODE,),
)

LEGAL_FAILURE_PROFILE = FakeAdapterProfile(
    adapter_key="fake:contract-legal-failure",
    scenario="legal_failure",
    declared_capabilities=("content_detail",),
    supported_targets=("url",),
    supported_collection_modes=(LEGACY_COLLECTION_MODE,),
)

VIOLATION_PROFILE = FakeAdapterProfile(
    adapter_key="fake:contract-violation",
    scenario="illegal_payload",
    declared_capabilities=("content_detail",),
    supported_targets=("url",),
    supported_collection_modes=(LEGACY_COLLECTION_MODE,),
)

CONTRACT_SAMPLES: Sequence[ContractSample] = (
    ContractSample(
        sample_id="success-full-envelope",
        description="完整 success envelope，经 Core 返回 raw 与 normalized。",
        input=SampleInput(
            adapter_key=SUCCESS_PROFILE.adapter_key,
            target_url="https://contract-host/success",
        ),
        expected_verdict=ExpectedVerdict.PASS,
        expected_runtime_status="success",
        expected_runtime_error_category=None,
        adapter_profile=SUCCESS_PROFILE,
    ),
    ContractSample(
        sample_id="legal-failure-platform-envelope",
        description="fake adapter 受控返回平台失败 envelope，并由 validator 判定为合法失败。",
        input=SampleInput(
            adapter_key=LEGAL_FAILURE_PROFILE.adapter_key,
            target_url="https://contract-host/legal-failure",
        ),
        expected_verdict=ExpectedVerdict.LEGAL_FAILURE,
        expected_runtime_status="failed",
        expected_runtime_error_category="platform",
        adapter_profile=LEGAL_FAILURE_PROFILE,
    ),
    ContractSample(
        sample_id="contract-violation-missing-normalized",
        description="fake adapter 故意缺失 normalized 字段，触发 runtime_contract 并由 validator 归类为 contract_violation。",
        input=SampleInput(
            adapter_key=VIOLATION_PROFILE.adapter_key,
            target_url="https://contract-host/violation",
        ),
        expected_verdict=ExpectedVerdict.CONTRACT_VIOLATION,
        expected_runtime_status="failed",
        expected_runtime_error_category="runtime_contract",
        adapter_profile=VIOLATION_PROFILE,
    ),
    ContractSample(
        sample_id="execution-precondition-not-met",
        description="fake adapter 未注册或夹具缺失，harness 在进入 Core 前中止。",
        input=SampleInput(
            adapter_key="fake:missing-fixture",
            target_url="https://contract-host/missing-fixture",
        ),
        expected_verdict=ExpectedVerdict.EXECUTION_PRECONDITION_NOT_MET,
        expected_runtime_status=None,
        expected_runtime_error_category=None,
        precondition_notes=(
            "fake adapter 未注册到 AdapterRegistry，必须由 harness 先判定。",
        ),
    ),
)

__all__ = [
    "CONTRACT_SAMPLES",
    "ContractSample",
    "ExpectedVerdict",
    "FakeAdapterProfile",
    "SampleInput",
]
