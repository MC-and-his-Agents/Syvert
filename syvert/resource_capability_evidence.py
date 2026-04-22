from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re


_ALLOWED_ADAPTER_KEYS = frozenset({"xhs", "douyin"})
_ALLOWED_CAPABILITY_FAMILIES = frozenset({"content_detail"})
_ALLOWED_SHARED_STATUSES = frozenset({"shared", "adapter_only", "rejected"})
_ALLOWED_DECISIONS = frozenset({"approve_for_v0_5_0", "keep_adapter_local", "reject_for_v0_5_0"})
_ALLOWED_SHARED_STATUS_TO_DECISION = {
    "shared": "approve_for_v0_5_0",
    "adapter_only": "keep_adapter_local",
    "rejected": "reject_for_v0_5_0",
}
_ALLOWED_APPROVAL_STATUS = frozenset({"approved"})
_APPROVED_RESOURCE_CAPABILITY_IDS = ("account", "proxy")
_FROZEN_EXECUTION_PATH = {
    "operation": "content_detail_by_url",
    "target_type": "url",
    "collection_mode": "hybrid",
}
_REPO_ROOT = Path(__file__).resolve().parent.parent
_FORMAL_RESEARCH_PATH = (
    _REPO_ROOT / "docs/specs/FR-0015-dual-reference-resource-capability-evidence/research.md"
)


@dataclass(frozen=True)
class ExecutionPathDescriptor:
    operation: str
    target_type: str
    collection_mode: str


@dataclass(frozen=True)
class EvidenceReferenceEntry:
    evidence_ref: str
    source_file: str
    source_symbol: str
    summary: str


@dataclass(frozen=True)
class DualReferenceResourceCapabilityEvidenceRecord:
    adapter_key: str
    capability: str
    execution_path: ExecutionPathDescriptor
    resource_signals: tuple[str, ...]
    candidate_abstract_capability: str
    shared_status: str
    evidence_refs: tuple[str, ...]
    decision: str


@dataclass(frozen=True)
class ApprovedResourceCapabilityVocabularyEntry:
    capability_id: str
    approval_basis_evidence_refs: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class FormalResearchEvidenceReferenceEntry:
    evidence_ref: str
    source_file: str
    source_symbol: str


@dataclass(frozen=True)
class FormalResearchApprovedCapabilityEntry:
    capability_id: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class FormalResearchEvidenceRecordEntry:
    adapter_key: str
    capability: str
    execution_path: ExecutionPathDescriptor
    candidate_abstract_capability: str
    shared_status: str
    decision: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class FormalResearchBaseline:
    evidence_reference_entries: tuple[FormalResearchEvidenceReferenceEntry, ...]
    approved_capability_entries: tuple[FormalResearchApprovedCapabilityEntry, ...]
    evidence_record_entries: tuple[FormalResearchEvidenceRecordEntry, ...]


_FROZEN_EVIDENCE_REFERENCE_ENTRIES = (
    EvidenceReferenceEntry(
        evidence_ref="fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
        source_file="syvert/runtime.py",
        source_symbol="RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE",
        summary="共享 Core 路径在 content_detail_by_url + hybrid 上统一请求 account 与 proxy 两个受管资源 slot。",
    ),
    EvidenceReferenceEntry(
        evidence_ref="fr-0015:xhs:content-detail:url:hybrid:account-material",
        source_file="syvert/adapters/xhs.py",
        source_symbol="build_session_config_from_context",
        summary="xhs adapter 在共享路径上从 resource_bundle.account.material 消费 cookies、user_agent、sign_base_url、timeout_seconds。",
    ),
    EvidenceReferenceEntry(
        evidence_ref="fr-0015:douyin:content-detail:url:hybrid:account-material",
        source_file="syvert/adapters/douyin.py",
        source_symbol="build_session_config_from_context",
        summary="douyin adapter 在共享路径上从 resource_bundle.account.material 消费 cookies、user_agent、verify_fp、ms_token、webid、sign_base_url、timeout_seconds。",
    ),
    EvidenceReferenceEntry(
        evidence_ref="fr-0015:xhs:content-detail:url:hybrid:url-request-tokens",
        source_file="syvert/adapters/xhs.py",
        source_symbol="build_detail_body",
        summary="xhs adapter 只在平台私有 detail body 中透传 xsec_token 与 xsec_source 两个 URL / request token。",
    ),
    EvidenceReferenceEntry(
        evidence_ref="fr-0015:douyin:content-detail:url:hybrid:request-signature-token",
        source_file="syvert/adapters/douyin.py",
        source_symbol="DouyinAdapter._build_detail_params",
        summary="douyin adapter 在平台私有签名步骤中生成并注入 a_bogus 请求 token。",
    ),
    EvidenceReferenceEntry(
        evidence_ref="fr-0015:xhs:content-detail:url:hybrid:page-state-fallback",
        source_file="syvert/adapters/xhs.py",
        source_symbol="XhsAdapter._recover_note_card_from_html",
        summary="xhs adapter 在 detail / html 路径失败时会退回 browser page-state 恢复链路，这属于技术绑定回退。",
    ),
    EvidenceReferenceEntry(
        evidence_ref="fr-0015:douyin:content-detail:url:hybrid:page-state-fallback",
        source_file="syvert/adapters/douyin.py",
        source_symbol="DouyinAdapter._recover_aweme_detail_from_page_state",
        summary="douyin adapter 在 detail 路径失败时会退回 browser page-state 恢复链路，这属于技术绑定回退。",
    ),
    EvidenceReferenceEntry(
        evidence_ref="fr-0015:regression:xhs:managed-proxy-seed",
        source_file="syvert/real_adapter_regression.py",
        source_symbol="seed_reference_regression_resources",
        summary="xhs 真实适配器回归基线在共享路径上同时种入 account 与 proxy。",
    ),
    EvidenceReferenceEntry(
        evidence_ref="fr-0015:regression:douyin:managed-proxy-seed",
        source_file="syvert/real_adapter_regression.py",
        source_symbol="seed_reference_regression_resources",
        summary="douyin 真实适配器回归基线在共享路径上同时种入 account 与 proxy。",
    ),
)


_FROZEN_DUAL_REFERENCE_RESOURCE_CAPABILITY_EVIDENCE_RECORDS = (
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="xhs",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "runtime_requested_slots=account,proxy",
            "adapter_consumes_account_material=cookies,user_agent,sign_base_url,timeout_seconds",
        ),
        candidate_abstract_capability="account",
        shared_status="shared",
        evidence_refs=(
            "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
            "fr-0015:xhs:content-detail:url:hybrid:account-material",
        ),
        decision="approve_for_v0_5_0",
    ),
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="douyin",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "runtime_requested_slots=account,proxy",
            "adapter_consumes_account_material=cookies,user_agent,verify_fp,ms_token,webid,sign_base_url,timeout_seconds",
        ),
        candidate_abstract_capability="account",
        shared_status="shared",
        evidence_refs=(
            "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
            "fr-0015:douyin:content-detail:url:hybrid:account-material",
        ),
        decision="approve_for_v0_5_0",
    ),
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="xhs",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "runtime_requested_slots=account,proxy",
            "regression_seeded_resources=account,proxy",
        ),
        candidate_abstract_capability="proxy",
        shared_status="shared",
        evidence_refs=(
            "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
            "fr-0015:regression:xhs:managed-proxy-seed",
        ),
        decision="approve_for_v0_5_0",
    ),
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="douyin",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "runtime_requested_slots=account,proxy",
            "regression_seeded_resources=account,proxy",
        ),
        candidate_abstract_capability="proxy",
        shared_status="shared",
        evidence_refs=(
            "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
            "fr-0015:regression:douyin:managed-proxy-seed",
        ),
        decision="approve_for_v0_5_0",
    ),
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="douyin",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "adapter_private_account_field=verify_fp",
        ),
        candidate_abstract_capability="verify_fp",
        shared_status="adapter_only",
        evidence_refs=(
            "fr-0015:douyin:content-detail:url:hybrid:account-material",
        ),
        decision="keep_adapter_local",
    ),
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="douyin",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "adapter_private_account_field=ms_token",
        ),
        candidate_abstract_capability="ms_token",
        shared_status="adapter_only",
        evidence_refs=(
            "fr-0015:douyin:content-detail:url:hybrid:account-material",
        ),
        decision="keep_adapter_local",
    ),
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="douyin",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "adapter_private_account_field=webid",
        ),
        candidate_abstract_capability="webid",
        shared_status="adapter_only",
        evidence_refs=(
            "fr-0015:douyin:content-detail:url:hybrid:account-material",
        ),
        decision="keep_adapter_local",
    ),
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="douyin",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "adapter_private_request_token=a_bogus",
        ),
        candidate_abstract_capability="a_bogus",
        shared_status="rejected",
        evidence_refs=(
            "fr-0015:douyin:content-detail:url:hybrid:request-signature-token",
        ),
        decision="reject_for_v0_5_0",
    ),
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="xhs",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "adapter_private_request_token=xsec_token",
        ),
        candidate_abstract_capability="xsec_token",
        shared_status="rejected",
        evidence_refs=(
            "fr-0015:xhs:content-detail:url:hybrid:url-request-tokens",
        ),
        decision="reject_for_v0_5_0",
    ),
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="xhs",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "adapter_private_request_token=xsec_source",
        ),
        candidate_abstract_capability="xsec_source",
        shared_status="rejected",
        evidence_refs=(
            "fr-0015:xhs:content-detail:url:hybrid:url-request-tokens",
        ),
        decision="reject_for_v0_5_0",
    ),
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="xhs",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "technical_binding_field=sign_base_url",
        ),
        candidate_abstract_capability="sign_base_url",
        shared_status="rejected",
        evidence_refs=(
            "fr-0015:xhs:content-detail:url:hybrid:account-material",
        ),
        decision="reject_for_v0_5_0",
    ),
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="douyin",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "technical_binding_field=sign_base_url",
        ),
        candidate_abstract_capability="sign_base_url",
        shared_status="rejected",
        evidence_refs=(
            "fr-0015:douyin:content-detail:url:hybrid:account-material",
        ),
        decision="reject_for_v0_5_0",
    ),
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="xhs",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "account_material_field=cookies",
        ),
        candidate_abstract_capability="cookies",
        shared_status="rejected",
        evidence_refs=(
            "fr-0015:xhs:content-detail:url:hybrid:account-material",
        ),
        decision="reject_for_v0_5_0",
    ),
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="douyin",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "account_material_field=cookies",
        ),
        candidate_abstract_capability="cookies",
        shared_status="rejected",
        evidence_refs=(
            "fr-0015:douyin:content-detail:url:hybrid:account-material",
        ),
        decision="reject_for_v0_5_0",
    ),
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="xhs",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "account_material_field=user_agent",
        ),
        candidate_abstract_capability="user_agent",
        shared_status="rejected",
        evidence_refs=(
            "fr-0015:xhs:content-detail:url:hybrid:account-material",
        ),
        decision="reject_for_v0_5_0",
    ),
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="douyin",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "account_material_field=user_agent",
        ),
        candidate_abstract_capability="user_agent",
        shared_status="rejected",
        evidence_refs=(
            "fr-0015:douyin:content-detail:url:hybrid:account-material",
        ),
        decision="reject_for_v0_5_0",
    ),
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="xhs",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "technical_binding_candidate=browser_state",
        ),
        candidate_abstract_capability="browser_state",
        shared_status="rejected",
        evidence_refs=(
            "fr-0015:xhs:content-detail:url:hybrid:page-state-fallback",
        ),
        decision="reject_for_v0_5_0",
    ),
    DualReferenceResourceCapabilityEvidenceRecord(
        adapter_key="douyin",
        capability="content_detail",
        execution_path=ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH),
        resource_signals=(
            "technical_binding_candidate=browser_state",
        ),
        candidate_abstract_capability="browser_state",
        shared_status="rejected",
        evidence_refs=(
            "fr-0015:douyin:content-detail:url:hybrid:page-state-fallback",
        ),
        decision="reject_for_v0_5_0",
    ),
)

_EXPECTED_FROZEN_RECORD_BASELINE = {
    ("xhs", "account"): {
        "resource_signals": (
            "runtime_requested_slots=account,proxy",
            "adapter_consumes_account_material=cookies,user_agent,sign_base_url,timeout_seconds",
        ),
        "shared_status": "shared",
        "evidence_refs": (
            "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
            "fr-0015:xhs:content-detail:url:hybrid:account-material",
        ),
        "decision": "approve_for_v0_5_0",
    },
    ("douyin", "account"): {
        "resource_signals": (
            "runtime_requested_slots=account,proxy",
            "adapter_consumes_account_material=cookies,user_agent,verify_fp,ms_token,webid,sign_base_url,timeout_seconds",
        ),
        "shared_status": "shared",
        "evidence_refs": (
            "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
            "fr-0015:douyin:content-detail:url:hybrid:account-material",
        ),
        "decision": "approve_for_v0_5_0",
    },
    ("xhs", "proxy"): {
        "resource_signals": (
            "runtime_requested_slots=account,proxy",
            "regression_seeded_resources=account,proxy",
        ),
        "shared_status": "shared",
        "evidence_refs": (
            "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
            "fr-0015:regression:xhs:managed-proxy-seed",
        ),
        "decision": "approve_for_v0_5_0",
    },
    ("douyin", "proxy"): {
        "resource_signals": (
            "runtime_requested_slots=account,proxy",
            "regression_seeded_resources=account,proxy",
        ),
        "shared_status": "shared",
        "evidence_refs": (
            "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
            "fr-0015:regression:douyin:managed-proxy-seed",
        ),
        "decision": "approve_for_v0_5_0",
    },
    ("douyin", "verify_fp"): {
        "resource_signals": ("adapter_private_account_field=verify_fp",),
        "shared_status": "adapter_only",
        "evidence_refs": ("fr-0015:douyin:content-detail:url:hybrid:account-material",),
        "decision": "keep_adapter_local",
    },
    ("douyin", "ms_token"): {
        "resource_signals": ("adapter_private_account_field=ms_token",),
        "shared_status": "adapter_only",
        "evidence_refs": ("fr-0015:douyin:content-detail:url:hybrid:account-material",),
        "decision": "keep_adapter_local",
    },
    ("douyin", "webid"): {
        "resource_signals": ("adapter_private_account_field=webid",),
        "shared_status": "adapter_only",
        "evidence_refs": ("fr-0015:douyin:content-detail:url:hybrid:account-material",),
        "decision": "keep_adapter_local",
    },
    ("douyin", "a_bogus"): {
        "resource_signals": ("adapter_private_request_token=a_bogus",),
        "shared_status": "rejected",
        "evidence_refs": ("fr-0015:douyin:content-detail:url:hybrid:request-signature-token",),
        "decision": "reject_for_v0_5_0",
    },
    ("xhs", "xsec_token"): {
        "resource_signals": ("adapter_private_request_token=xsec_token",),
        "shared_status": "rejected",
        "evidence_refs": ("fr-0015:xhs:content-detail:url:hybrid:url-request-tokens",),
        "decision": "reject_for_v0_5_0",
    },
    ("xhs", "xsec_source"): {
        "resource_signals": ("adapter_private_request_token=xsec_source",),
        "shared_status": "rejected",
        "evidence_refs": ("fr-0015:xhs:content-detail:url:hybrid:url-request-tokens",),
        "decision": "reject_for_v0_5_0",
    },
    ("xhs", "sign_base_url"): {
        "resource_signals": ("technical_binding_field=sign_base_url",),
        "shared_status": "rejected",
        "evidence_refs": ("fr-0015:xhs:content-detail:url:hybrid:account-material",),
        "decision": "reject_for_v0_5_0",
    },
    ("douyin", "sign_base_url"): {
        "resource_signals": ("technical_binding_field=sign_base_url",),
        "shared_status": "rejected",
        "evidence_refs": ("fr-0015:douyin:content-detail:url:hybrid:account-material",),
        "decision": "reject_for_v0_5_0",
    },
    ("xhs", "cookies"): {
        "resource_signals": ("account_material_field=cookies",),
        "shared_status": "rejected",
        "evidence_refs": ("fr-0015:xhs:content-detail:url:hybrid:account-material",),
        "decision": "reject_for_v0_5_0",
    },
    ("douyin", "cookies"): {
        "resource_signals": ("account_material_field=cookies",),
        "shared_status": "rejected",
        "evidence_refs": ("fr-0015:douyin:content-detail:url:hybrid:account-material",),
        "decision": "reject_for_v0_5_0",
    },
    ("xhs", "user_agent"): {
        "resource_signals": ("account_material_field=user_agent",),
        "shared_status": "rejected",
        "evidence_refs": ("fr-0015:xhs:content-detail:url:hybrid:account-material",),
        "decision": "reject_for_v0_5_0",
    },
    ("douyin", "user_agent"): {
        "resource_signals": ("account_material_field=user_agent",),
        "shared_status": "rejected",
        "evidence_refs": ("fr-0015:douyin:content-detail:url:hybrid:account-material",),
        "decision": "reject_for_v0_5_0",
    },
    ("xhs", "browser_state"): {
        "resource_signals": ("technical_binding_candidate=browser_state",),
        "shared_status": "rejected",
        "evidence_refs": ("fr-0015:xhs:content-detail:url:hybrid:page-state-fallback",),
        "decision": "reject_for_v0_5_0",
    },
    ("douyin", "browser_state"): {
        "resource_signals": ("technical_binding_candidate=browser_state",),
        "shared_status": "rejected",
        "evidence_refs": ("fr-0015:douyin:content-detail:url:hybrid:page-state-fallback",),
        "decision": "reject_for_v0_5_0",
    },
}


_APPROVED_RESOURCE_CAPABILITY_VOCABULARY_ENTRIES = (
    ApprovedResourceCapabilityVocabularyEntry(
        capability_id="account",
        approval_basis_evidence_refs=(
            "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
            "fr-0015:xhs:content-detail:url:hybrid:account-material",
            "fr-0015:douyin:content-detail:url:hybrid:account-material",
        ),
        status="approved",
    ),
    ApprovedResourceCapabilityVocabularyEntry(
        capability_id="proxy",
        approval_basis_evidence_refs=(
            "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
            "fr-0015:regression:xhs:managed-proxy-seed",
            "fr-0015:regression:douyin:managed-proxy-seed",
        ),
        status="approved",
    ),
)


def frozen_evidence_reference_entries() -> tuple[EvidenceReferenceEntry, ...]:
    _validate_internal_frozen_resource_capability_evidence_baseline()
    return _FROZEN_EVIDENCE_REFERENCE_ENTRIES



def frozen_dual_reference_resource_capability_evidence_records() -> tuple[DualReferenceResourceCapabilityEvidenceRecord, ...]:
    _validate_internal_frozen_resource_capability_evidence_baseline()
    return _FROZEN_DUAL_REFERENCE_RESOURCE_CAPABILITY_EVIDENCE_RECORDS



def approved_resource_capability_vocabulary_entries() -> tuple[ApprovedResourceCapabilityVocabularyEntry, ...]:
    _validate_internal_frozen_resource_capability_evidence_baseline()
    return _APPROVED_RESOURCE_CAPABILITY_VOCABULARY_ENTRIES



def approved_resource_capability_ids() -> frozenset[str]:
    _validate_internal_frozen_resource_capability_evidence_baseline()
    return frozenset(entry.capability_id for entry in _APPROVED_RESOURCE_CAPABILITY_VOCABULARY_ENTRIES)



def _validate_internal_frozen_resource_capability_evidence_baseline() -> tuple[
    dict[str, EvidenceReferenceEntry],
    dict[tuple[str, str], DualReferenceResourceCapabilityEvidenceRecord],
    dict[str, ApprovedResourceCapabilityVocabularyEntry],
]:
    evidence_entries = _FROZEN_EVIDENCE_REFERENCE_ENTRIES
    evidence_entry_index = {entry.evidence_ref: entry for entry in evidence_entries}
    if len(evidence_entry_index) != len(evidence_entries):
        raise ValueError("frozen evidence reference entries must use unique evidence_ref values")
    for entry in evidence_entries:
        _require_non_empty_string(entry.evidence_ref, field_name="evidence_ref")
        _require_non_empty_string(entry.source_file, field_name="source_file")
        _require_non_empty_string(entry.source_symbol, field_name="source_symbol")
        _require_non_empty_string(entry.summary, field_name="summary")

    records = _FROZEN_DUAL_REFERENCE_RESOURCE_CAPABILITY_EVIDENCE_RECORDS
    if not records:
        raise ValueError("frozen evidence records must not be empty")

    shared_records_by_capability: dict[str, list[DualReferenceResourceCapabilityEvidenceRecord]] = {}
    record_index: dict[tuple[str, str], DualReferenceResourceCapabilityEvidenceRecord] = {}
    shared_record_keys: set[tuple[str, str]] = set()
    for record in records:
        if record.adapter_key not in _ALLOWED_ADAPTER_KEYS:
            raise ValueError(f"unsupported adapter_key in frozen evidence record: {record.adapter_key}")
        if record.capability not in _ALLOWED_CAPABILITY_FAMILIES:
            raise ValueError(f"unsupported capability family in frozen evidence record: {record.capability}")
        if record.execution_path != ExecutionPathDescriptor(**_FROZEN_EXECUTION_PATH):
            raise ValueError("frozen evidence records must all bind to the approved execution path")
        if record.shared_status not in _ALLOWED_SHARED_STATUSES:
            raise ValueError(f"unsupported shared_status in frozen evidence record: {record.shared_status}")
        if record.decision not in _ALLOWED_DECISIONS:
            raise ValueError(f"unsupported decision in frozen evidence record: {record.decision}")
        if _ALLOWED_SHARED_STATUS_TO_DECISION[record.shared_status] != record.decision:
            raise ValueError("shared_status and decision mapping must stay canonical")
        _require_non_empty_string(record.candidate_abstract_capability, field_name="candidate_abstract_capability")
        _require_unique_non_empty_strings(record.resource_signals, field_name="resource_signals")
        _require_unique_non_empty_strings(record.evidence_refs, field_name="evidence_refs")
        if any(ref not in evidence_entry_index for ref in record.evidence_refs):
            raise ValueError("frozen evidence record references unknown evidence_ref")
        record_key = (record.adapter_key, record.candidate_abstract_capability)
        if record_key in record_index:
            raise ValueError("frozen evidence records must not duplicate candidate/adapter pairs")
        record_index[record_key] = record
        if record.shared_status == "shared":
            shared_record_key = (record.candidate_abstract_capability, record.adapter_key)
            if shared_record_key in shared_record_keys:
                raise ValueError("shared evidence records must not duplicate capability/adapter pairs")
            shared_record_keys.add(shared_record_key)
            shared_records_by_capability.setdefault(record.candidate_abstract_capability, []).append(record)

    if frozenset(record_index) != frozenset(_EXPECTED_FROZEN_RECORD_BASELINE):
        raise ValueError("frozen evidence records must keep the full canonical candidate matrix")
    for record_key, expected_record in _EXPECTED_FROZEN_RECORD_BASELINE.items():
        record = record_index[record_key]
        if (
            record.resource_signals != expected_record["resource_signals"]
            or record.shared_status != expected_record["shared_status"]
            or record.evidence_refs != expected_record["evidence_refs"]
            or record.decision != expected_record["decision"]
        ):
            raise ValueError("frozen evidence records must keep canonical signals, evidence refs, and outcomes")

    vocabulary_entries = _APPROVED_RESOURCE_CAPABILITY_VOCABULARY_ENTRIES
    vocabulary_index = {entry.capability_id: entry for entry in vocabulary_entries}
    if len(vocabulary_index) != len(vocabulary_entries):
        raise ValueError("approved capability vocabulary entries must use unique capability_id values")
    approved_capability_ids = frozenset(entry.capability_id for entry in vocabulary_entries)
    if approved_capability_ids != frozenset(_APPROVED_RESOURCE_CAPABILITY_IDS):
        raise ValueError("approved capability ids must stay frozen to account and proxy")
    shared_capability_ids = frozenset(shared_records_by_capability)
    if shared_capability_ids != approved_capability_ids:
        raise ValueError("shared evidence records must stay frozen to the approved capability ids")
    expected_shared_record_keys = {
        (capability_id, adapter_key)
        for capability_id in _APPROVED_RESOURCE_CAPABILITY_IDS
        for adapter_key in _ALLOWED_ADAPTER_KEYS
    }
    if shared_record_keys != expected_shared_record_keys:
        raise ValueError("shared evidence records must stay frozen to one xhs and one douyin record per approved capability")

    rejected_or_adapter_only = {
        record.candidate_abstract_capability
        for record in records
        if record.shared_status != "shared"
    }
    if approved_capability_ids & rejected_or_adapter_only:
        raise ValueError("adapter_only or rejected candidates must not leak into approved capability ids")

    expected_vocabulary_entries = _expected_approved_vocabulary_entries(shared_records_by_capability)
    if vocabulary_entries != expected_vocabulary_entries:
        raise ValueError("approved capability vocabulary entries must stay equal to the canonical mapping derived from shared evidence records")

    for capability_id, vocabulary_entry in vocabulary_index.items():
        if vocabulary_entry.status not in _ALLOWED_APPROVAL_STATUS:
            raise ValueError(f"unsupported approval status: {vocabulary_entry.status}")
        _require_unique_non_empty_strings(
            vocabulary_entry.approval_basis_evidence_refs,
            field_name="approval_basis_evidence_refs",
        )
        if any(ref not in evidence_entry_index for ref in vocabulary_entry.approval_basis_evidence_refs):
            raise ValueError("approved vocabulary entry references unknown evidence_ref")
        shared_records = shared_records_by_capability.get(capability_id, [])
        shared_adapters = {record.adapter_key for record in shared_records}
        if shared_adapters != _ALLOWED_ADAPTER_KEYS:
            raise ValueError("approved capability ids must be backed by shared xhs and douyin evidence records")

    return evidence_entry_index, record_index, vocabulary_index



def validate_frozen_resource_capability_evidence_contract() -> None:
    evidence_entry_index, record_index, vocabulary_index = _validate_internal_frozen_resource_capability_evidence_baseline()
    formal_research_baseline = _load_formal_research_baseline()
    formal_evidence_entry_index = {
        entry.evidence_ref: entry for entry in formal_research_baseline.evidence_reference_entries
    }
    if frozenset(evidence_entry_index) != frozenset(formal_evidence_entry_index):
        raise ValueError("frozen evidence reference entries must stay aligned with the formal research registry")
    parsed_source_trees: dict[Path, ast.AST] = {}
    for evidence_ref, entry in evidence_entry_index.items():
        formal_entry = formal_evidence_entry_index[evidence_ref]
        if (
            entry.source_file != formal_entry.source_file
            or entry.source_symbol != formal_entry.source_symbol
        ):
            raise ValueError("frozen evidence reference entries must keep canonical source pointers from the formal research registry")
        _validate_traceable_evidence_source(entry, parsed_source_trees)

    formal_record_index = {
        (record.adapter_key, record.candidate_abstract_capability): record
        for record in formal_research_baseline.evidence_record_entries
    }
    if frozenset(record_index) != frozenset(formal_record_index):
        raise ValueError("frozen evidence records must stay aligned with the formal research baseline")
    for record_key, formal_record in formal_record_index.items():
        record = record_index[record_key]
        if (
            record.capability != formal_record.capability
            or record.execution_path != formal_record.execution_path
            or record.shared_status != formal_record.shared_status
            or record.decision != formal_record.decision
            or record.evidence_refs != formal_record.evidence_refs
        ):
            raise ValueError("frozen evidence records must stay aligned with the formal research baseline")

    approved_capability_ids = frozenset(vocabulary_index)
    formal_approved_capability_index = {
        entry.capability_id: entry for entry in formal_research_baseline.approved_capability_entries
    }
    if approved_capability_ids != frozenset(formal_approved_capability_index):
        raise ValueError("approved capability ids must stay aligned with the formal research baseline")
    for capability_id, vocabulary_entry in vocabulary_index.items():
        formal_capability_entry = formal_approved_capability_index[capability_id]
        if vocabulary_entry.approval_basis_evidence_refs != formal_capability_entry.evidence_refs:
            raise ValueError("approved capability vocabulary entries must stay aligned with the formal research baseline")



def _require_non_empty_string(value: str, *, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")



def _require_unique_non_empty_strings(values: tuple[str, ...], *, field_name: str) -> None:
    if not isinstance(values, tuple) or not values:
        raise ValueError(f"{field_name} must be a non-empty tuple of strings")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    for value in values:
        _require_non_empty_string(value, field_name=field_name)


def _canonical_approval_basis_evidence_refs(
    shared_records: list[DualReferenceResourceCapabilityEvidenceRecord],
) -> tuple[str, ...]:
    ordered_refs: list[str] = []
    records_by_adapter = {record.adapter_key: record for record in shared_records}
    for adapter_key in ("xhs", "douyin"):
        record = records_by_adapter[adapter_key]
        for evidence_ref in record.evidence_refs:
            if evidence_ref not in ordered_refs:
                ordered_refs.append(evidence_ref)
    return tuple(ordered_refs)


def _expected_approved_vocabulary_entries(
    shared_records_by_capability: dict[str, list[DualReferenceResourceCapabilityEvidenceRecord]],
) -> tuple[ApprovedResourceCapabilityVocabularyEntry, ...]:
    return tuple(
        ApprovedResourceCapabilityVocabularyEntry(
            capability_id=capability_id,
            approval_basis_evidence_refs=_canonical_approval_basis_evidence_refs(
                shared_records_by_capability[capability_id]
            ),
            status="approved",
        )
        for capability_id in _APPROVED_RESOURCE_CAPABILITY_IDS
    )


def _load_formal_research_baseline() -> FormalResearchBaseline:
    if not _FORMAL_RESEARCH_PATH.is_file():
        raise ValueError("formal research registry must resolve to a real file")
    try:
        research_text = _FORMAL_RESEARCH_PATH.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError("formal research registry must be readable") from error

    evidence_reference_entries = tuple(_parse_formal_research_evidence_reference_entries(research_text))
    approved_capability_entries = tuple(_parse_formal_research_approved_capability_entries(research_text))
    evidence_record_entries = tuple(_parse_formal_research_evidence_record_entries(research_text))
    if not evidence_reference_entries:
        raise ValueError("formal research registry must enumerate evidence reference entries")
    if not approved_capability_entries:
        raise ValueError("formal research registry must enumerate approved capabilities")
    if not evidence_record_entries:
        raise ValueError("formal research registry must enumerate evidence records")
    _require_unique_formal_research_rows(
        evidence_reference_entries,
        key_fn=lambda entry: entry.evidence_ref,
        error_message="formal research evidence registry must not duplicate evidence_ref rows",
    )
    _require_unique_formal_research_rows(
        approved_capability_entries,
        key_fn=lambda entry: entry.capability_id,
        error_message="formal research approved capability table must not duplicate capability_id rows",
    )
    _require_unique_formal_research_rows(
        evidence_record_entries,
        key_fn=lambda entry: (entry.adapter_key, entry.candidate_abstract_capability),
        error_message="formal research evidence record table must not duplicate adapter/candidate rows",
    )
    return FormalResearchBaseline(
        evidence_reference_entries=evidence_reference_entries,
        approved_capability_entries=approved_capability_entries,
        evidence_record_entries=evidence_record_entries,
    )


def _parse_formal_research_evidence_reference_entries(
    research_text: str,
) -> list[FormalResearchEvidenceReferenceEntry]:
    entries: list[FormalResearchEvidenceReferenceEntry] = []
    for cells in _read_markdown_table_cells(research_text, heading="## 证据登记项"):
        if len(cells) != 3:
            raise ValueError("formal research evidence registry rows must keep three columns")
        pointer_match = re.fullmatch(r"`([^`]+)` 中 `([^`]+)`", cells[1])
        if pointer_match is None:
            raise ValueError("formal research evidence registry source pointers must stay canonical")
        entries.append(
            FormalResearchEvidenceReferenceEntry(
                evidence_ref=_unwrap_inline_code(cells[0]),
                source_file=pointer_match.group(1),
                source_symbol=pointer_match.group(2).removesuffix("()"),
            )
        )
    return entries


def _parse_formal_research_approved_capability_entries(
    research_text: str,
) -> list[FormalResearchApprovedCapabilityEntry]:
    entries: list[FormalResearchApprovedCapabilityEntry] = []
    for cells in _read_markdown_table_cells(research_text, heading="## 冻结的 `v0.5.0` 最小能力词汇"):
        if len(cells) != 3:
            raise ValueError("formal research approved capability rows must keep three columns")
        if _unwrap_inline_code(cells[1]) != "shared + approve_for_v0_5_0":
            raise ValueError("formal research approved capabilities must stay frozen to shared + approve_for_v0_5_0")
        entries.append(
            FormalResearchApprovedCapabilityEntry(
                capability_id=_unwrap_inline_code(cells[0]),
                evidence_refs=_parse_inline_code_list(cells[2]),
            )
        )
    return entries


def _parse_formal_research_evidence_record_entries(
    research_text: str,
) -> list[FormalResearchEvidenceRecordEntry]:
    entries: list[FormalResearchEvidenceRecordEntry] = []
    for cells in _read_markdown_table_cells(research_text, heading="## 冻结的 evidence record 基线示例"):
        if len(cells) != 7:
            raise ValueError("formal research evidence record rows must keep seven columns")
        entries.append(
            FormalResearchEvidenceRecordEntry(
                adapter_key=_unwrap_inline_code(cells[0]),
                capability=_unwrap_inline_code(cells[1]),
                execution_path=_parse_execution_path_descriptor(_unwrap_inline_code(cells[2])),
                candidate_abstract_capability=_unwrap_inline_code(cells[3]),
                shared_status=_unwrap_inline_code(cells[4]),
                decision=_unwrap_inline_code(cells[5]),
                evidence_refs=_parse_inline_code_list(cells[6]),
            )
        )
    return entries


def _read_markdown_table_cells(research_text: str, *, heading: str) -> list[list[str]]:
    section_match = re.search(
        rf"{re.escape(heading)}\n\n(?P<table>(?:\|.*\n)+?)(?:\n## |\Z)",
        research_text,
        flags=re.MULTILINE,
    )
    if section_match is None:
        raise ValueError(f"formal research registry missing section: {heading}")
    table_lines = [line for line in section_match.group("table").splitlines() if line.strip()]
    if len(table_lines) < 3:
        raise ValueError(f"formal research registry section must keep a header and at least one row: {heading}")
    return [_split_markdown_table_row(line) for line in table_lines[2:]]


def _split_markdown_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        raise ValueError("formal research registry table rows must use markdown table syntax")
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def _unwrap_inline_code(value: str) -> str:
    if not value.startswith("`") or not value.endswith("`"):
        raise ValueError("formal research registry cells must use inline code where required")
    return value[1:-1]


def _parse_inline_code_list(value: str) -> tuple[str, ...]:
    parts = tuple(part.strip() for part in value.split("、") if part.strip())
    if not parts:
        raise ValueError("formal research registry evidence ref lists must not be empty")
    return tuple(_unwrap_inline_code(part) for part in parts)


def _parse_execution_path_descriptor(value: str) -> ExecutionPathDescriptor:
    parts: dict[str, str] = {}
    for segment in value.split(","):
        key, separator, raw_value = segment.strip().partition("=")
        if separator != "=" or not key or not raw_value:
            raise ValueError("formal research execution_path cells must keep key=value segments")
        parts[key] = raw_value
    if frozenset(parts) != frozenset(_FROZEN_EXECUTION_PATH):
        raise ValueError("formal research execution_path cells must stay aligned with the frozen execution path")
    return ExecutionPathDescriptor(
        operation=parts["operation"],
        target_type=parts["target_type"],
        collection_mode=parts["collection_mode"],
    )


def _require_unique_formal_research_rows(
    entries: tuple[object, ...],
    *,
    key_fn,
    error_message: str,
) -> None:
    keys = [key_fn(entry) for entry in entries]
    if len(set(keys)) != len(keys):
        raise ValueError(error_message)


def _validate_traceable_evidence_source(
    entry: EvidenceReferenceEntry,
    parsed_source_trees: dict[Path, ast.AST],
) -> None:
    source_path = (_REPO_ROOT / entry.source_file).resolve()
    if not source_path.is_file():
        raise ValueError("evidence source_file must resolve to a real file")
    syntax_tree = parsed_source_trees.get(source_path)
    if syntax_tree is None:
        try:
            syntax_tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        except (OSError, UnicodeDecodeError, SyntaxError) as error:
            raise ValueError("evidence source_file must be readable as Python source") from error
        parsed_source_trees[source_path] = syntax_tree
    if not _source_symbol_exists(syntax_tree, entry.source_symbol):
        raise ValueError("evidence source_symbol must resolve inside the declared source_file")


def _source_symbol_exists(syntax_tree: ast.AST, source_symbol: str) -> bool:
    symbol_path = tuple(part for part in source_symbol.split(".") if part)
    if not symbol_path:
        return False
    return _symbol_path_exists(getattr(syntax_tree, "body", []), symbol_path)


def _symbol_path_exists(nodes: list[ast.stmt], symbol_path: tuple[str, ...]) -> bool:
    head, *tail = symbol_path
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == head:
            if not tail:
                return True
            return _symbol_path_exists(getattr(node, "body", []), tuple(tail))
        if not tail and isinstance(node, (ast.Assign, ast.AnnAssign)):
            for target_name in _assignment_target_names(node):
                if target_name == head:
                    return True
    return False


def _assignment_target_names(node: ast.Assign | ast.AnnAssign) -> tuple[str, ...]:
    if isinstance(node, ast.Assign):
        targets = node.targets
    else:
        targets = [node.target]

    names: list[str] = []
    for target in targets:
        if isinstance(target, ast.Name):
            names.append(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                if isinstance(element, ast.Name):
                    names.append(element.id)
    return tuple(names)
