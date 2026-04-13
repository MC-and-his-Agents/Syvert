"""Contract harness sample catalog for FR-0006."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence

from syvert.runtime import CONTENT_DETAIL_BY_URL, LEGACY_COLLECTION_MODE


class ExpectedVerdict(Enum):
    PASS = "pass"
    LEGAL_FAILURE = "legal_failure"
    CONTRACT_VIOLATION = "contract_violation"
    EXECUTION_PRECONDITION_NOT_MET = "execution_precondition_not_met"


@dataclass(frozen=True)
class FakeAdapterProfile:
    adapter_key: str
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
    expected_runtime_category: str | None
    adapter_profile: FakeAdapterProfile | None = None
    adapter_response_shape: Mapping[str, object] | None = None
    precondition_notes: Sequence[str] = field(default_factory=tuple)


SUCCESS_PROFILE = FakeAdapterProfile(
    adapter_key="fake:contract-success",
    declared_capabilities=("content_detail",),
    supported_targets=("url",),
    supported_collection_modes=(LEGACY_COLLECTION_MODE,),
)

LEGAL_FAILURE_PROFILE = FakeAdapterProfile(
    adapter_key="fake:contract-legal-failure",
    declared_capabilities=("content_detail",),
    supported_targets=("url",),
    supported_collection_modes=(LEGACY_COLLECTION_MODE,),
)

VIOLATION_PROFILE = FakeAdapterProfile(
    adapter_key="fake:contract-violation",
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
        expected_runtime_category="success",
        adapter_profile=SUCCESS_PROFILE,
        adapter_response_shape={
            "raw": {"id": "success-1", "payload": {"detail": "ok"}},
            "normalized": {
                "platform": "fake",
                "content_id": "success-1",
                "content_type": "unknown",
                "canonical_url": "https://contract-host/success",
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
        },
    ),
    ContractSample(
        sample_id="legal-failure-invalid-input",
        description="请求进入 Core 后返回 FR-0005 允许的 invalid_input failed envelope。",
        input=SampleInput(
            adapter_key=LEGAL_FAILURE_PROFILE.adapter_key,
            target_url="https://contract-host/invalid-input",
            target_type="content_id",
        ),
        expected_verdict=ExpectedVerdict.LEGAL_FAILURE,
        expected_runtime_category="invalid_input",
        adapter_profile=LEGAL_FAILURE_PROFILE,
        precondition_notes=(
            "target_type 非默认 url，使 runtime 在进入 adapter 前返回 invalid_input。",
        ),
    ),
    ContractSample(
        sample_id="contract-violation-missing-normalized",
        description="fake adapter 故意缺失 normalized 字段，触发 runtime_contract 并由 validator 归类为 contract_violation。",
        input=SampleInput(
            adapter_key=VIOLATION_PROFILE.adapter_key,
            target_url="https://contract-host/violation",
        ),
        expected_verdict=ExpectedVerdict.CONTRACT_VIOLATION,
        expected_runtime_category="runtime_contract",
        adapter_profile=VIOLATION_PROFILE,
        adapter_response_shape={
            "raw": {"id": "violation-1", "payload": {"detail": "missing normalized"}},
        },
    ),
    ContractSample(
        sample_id="execution-precondition-not-met",
        description="fake adapter 未注册或夹具缺失，harness 在进入 Core 前中止。",
        input=SampleInput(
            adapter_key="fake:missing-fixture",
            target_url="https://contract-host/missing-fixture",
        ),
        expected_verdict=ExpectedVerdict.EXECUTION_PRECONDITION_NOT_MET,
        expected_runtime_category=None,
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
