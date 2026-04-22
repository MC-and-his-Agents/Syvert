from __future__ import annotations

from dataclasses import dataclass


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
            "technical_binding_candidate=browser_state",
        ),
        candidate_abstract_capability="browser_state",
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
            "technical_binding_candidate=browser_state",
        ),
        candidate_abstract_capability="browser_state",
        shared_status="rejected",
        evidence_refs=(
            "fr-0015:douyin:content-detail:url:hybrid:account-material",
        ),
        decision="reject_for_v0_5_0",
    ),
)


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
    return _FROZEN_EVIDENCE_REFERENCE_ENTRIES



def frozen_dual_reference_resource_capability_evidence_records() -> tuple[DualReferenceResourceCapabilityEvidenceRecord, ...]:
    return _FROZEN_DUAL_REFERENCE_RESOURCE_CAPABILITY_EVIDENCE_RECORDS



def approved_resource_capability_vocabulary_entries() -> tuple[ApprovedResourceCapabilityVocabularyEntry, ...]:
    return _APPROVED_RESOURCE_CAPABILITY_VOCABULARY_ENTRIES



def approved_resource_capability_ids() -> frozenset[str]:
    return frozenset(entry.capability_id for entry in approved_resource_capability_vocabulary_entries())



def validate_frozen_resource_capability_evidence_contract() -> None:
    evidence_entries = frozen_evidence_reference_entries()
    evidence_entry_index = {entry.evidence_ref: entry for entry in evidence_entries}
    if len(evidence_entry_index) != len(evidence_entries):
        raise ValueError("frozen evidence reference entries must use unique evidence_ref values")

    for entry in evidence_entries:
        _require_non_empty_string(entry.evidence_ref, field_name="evidence_ref")
        _require_non_empty_string(entry.source_file, field_name="source_file")
        _require_non_empty_string(entry.source_symbol, field_name="source_symbol")
        _require_non_empty_string(entry.summary, field_name="summary")

    records = frozen_dual_reference_resource_capability_evidence_records()
    if not records:
        raise ValueError("frozen evidence records must not be empty")

    shared_records_by_capability: dict[str, list[DualReferenceResourceCapabilityEvidenceRecord]] = {}
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
        if record.shared_status == "shared":
            shared_record_key = (record.candidate_abstract_capability, record.adapter_key)
            if shared_record_key in shared_record_keys:
                raise ValueError("shared evidence records must not duplicate capability/adapter pairs")
            shared_record_keys.add(shared_record_key)
            shared_records_by_capability.setdefault(record.candidate_abstract_capability, []).append(record)

    vocabulary_entries = approved_resource_capability_vocabulary_entries()
    vocabulary_index = {entry.capability_id: entry for entry in vocabulary_entries}
    if len(vocabulary_index) != len(vocabulary_entries):
        raise ValueError("approved capability vocabulary entries must use unique capability_id values")
    approved_capability_ids = approved_resource_capability_ids()
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
