from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any

from syvert.resource_lifecycle import (
    MANAGED_ACCOUNT_ADAPTER_KEY_FIELD,
    ReleaseRequest,
    ResourceLease,
    ResourceRecord,
    ResourceReleaseResult,
    ResourceLifecycleStore,
    ResourceLifecycleContractError,
    load_snapshot_from_store,
    now_rfc3339_utc,
    parse_rfc3339_utc_datetime,
    release,
    validate_snapshot,
)
from syvert.runtime import failure_envelope, runtime_contract_error
from syvert.task_record import TaskRecordContractError, normalize_json_value


SESSION_HEALTH_HEALTHY = "healthy"
SESSION_HEALTH_STALE = "stale"
SESSION_HEALTH_INVALID = "invalid"
SESSION_HEALTH_UNKNOWN = "unknown"
SESSION_HEALTH_VALUES = frozenset(
    {
        SESSION_HEALTH_HEALTHY,
        SESSION_HEALTH_STALE,
        SESSION_HEALTH_INVALID,
        SESSION_HEALTH_UNKNOWN,
    }
)

RESOURCE_HEALTH_EVIDENCE_STATUSES = frozenset(
    {
        SESSION_HEALTH_HEALTHY,
        SESSION_HEALTH_STALE,
        SESSION_HEALTH_INVALID,
    }
)
RESOURCE_HEALTH_PROVENANCE_VALUES = frozenset(
    {
        "core_validation",
        "adapter_diagnostic",
        "provider_response_projection",
        "operator_assertion",
    }
)
RESOURCE_ADMISSION_DECISION_ADMITTED = "admitted"
RESOURCE_ADMISSION_DECISION_REJECTED = "rejected"
RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT = "invalid_contract"
RESOURCE_INVALIDATION_REASON_CREDENTIAL_SESSION_INVALID = "credential_session_invalid"
RESOURCE_HEALTH_CONTRACT_INVALID_REASON = "health_evidence_contract_invalid"
RESOURCE_HEALTH_EVIDENCE_FIELDS = frozenset(
    {
        "evidence_id",
        "resource_id",
        "resource_type",
        "status",
        "observed_at",
        "provenance",
        "reason",
        "redaction_status",
        "expires_at",
        "freshness_policy_ref",
        "task_id",
        "lease_id",
        "bundle_id",
        "adapter_key",
        "capability",
        "operation",
        "diagnostic_ref",
    }
)

_PRIVATE_CREDENTIAL_TOKENS = frozenset(
    {
        "authorization",
        "cookie",
        "cookies",
        "header",
        "headers",
        "ms_token",
        "session_dump",
        "token",
        "verify_fp",
        "xsec_token",
    }
)
_PRIVATE_ASSIGNMENT_RE = re.compile(
    r"\b(authorization|cookie|cookies|header|headers|ms_token|session_dump|token|verify_fp|xsec_token)\b\s*[:=]",
    re.IGNORECASE,
)
_UNREDACTED_MARKERS = frozenset({"leak", "leaked", "raw", "secret", "unredacted"})


class ResourceHealthContractError(ValueError):
    pass


@dataclass(frozen=True)
class CredentialMaterial:
    resource_id: str
    adapter_key: str
    material: Mapping[str, Any]


@dataclass(frozen=True)
class ResourceHealthEvidence:
    evidence_id: str
    resource_id: str
    resource_type: str
    status: str
    observed_at: str
    provenance: str
    reason: str
    redaction_status: str
    expires_at: str | None = None
    freshness_policy_ref: str | None = None
    task_id: str | None = None
    lease_id: str | None = None
    bundle_id: str | None = None
    adapter_key: str | None = None
    capability: str | None = None
    operation: str | None = None
    diagnostic_ref: str | None = None


@dataclass(frozen=True)
class ResourceAdmissionDecision:
    decision_id: str
    task_id: str
    adapter_key: str
    capability: str
    operation: str | None
    requested_slots: tuple[str, ...]
    resource_ids: tuple[str, ...]
    health_evidence_refs: tuple[str, ...]
    evaluated_at: str
    projected_session_health: str
    decision_status: str
    failure_reason: str | None
    fail_closed: bool


def credential_material_from_account_resource(record: ResourceRecord) -> CredentialMaterial:
    if record.resource_type != "account":
        raise ResourceHealthContractError("CredentialMaterial 只能绑定 account resource")
    if not isinstance(record.material, Mapping):
        raise ResourceHealthContractError("account resource material 必须是对象")
    adapter_key = record.material.get(MANAGED_ACCOUNT_ADAPTER_KEY_FIELD)
    if not isinstance(adapter_key, str) or not adapter_key:
        raise ResourceHealthContractError("account resource material 缺少 managed adapter key")
    material = _normalize_json_mapping(record.material, field="CredentialMaterial.material")
    return CredentialMaterial(resource_id=record.resource_id, adapter_key=adapter_key, material=material)


def credential_material_public_projection(credential: CredentialMaterial) -> dict[str, Any]:
    return {
        "resource_id": credential.resource_id,
        "adapter_key": credential.adapter_key,
        "material_boundary": "account_credential_material",
        "redaction_status": "redacted",
        "material_field_count": len(credential.material),
        "material_fields_redacted": True,
    }


def resource_health_evidence_to_dict(evidence: ResourceHealthEvidence) -> dict[str, Any]:
    validate_resource_health_evidence(evidence)
    payload = {
        "evidence_id": evidence.evidence_id,
        "resource_id": evidence.resource_id,
        "resource_type": evidence.resource_type,
        "status": evidence.status,
        "observed_at": evidence.observed_at,
        "provenance": evidence.provenance,
        "reason": evidence.reason,
        "redaction_status": evidence.redaction_status,
    }
    for field in (
        "expires_at",
        "freshness_policy_ref",
        "task_id",
        "lease_id",
        "bundle_id",
        "adapter_key",
        "capability",
        "operation",
        "diagnostic_ref",
    ):
        value = getattr(evidence, field)
        if value is not None:
            payload[field] = value
    return payload


def resource_health_evidence_from_dict(payload: Mapping[str, Any]) -> ResourceHealthEvidence:
    if not isinstance(payload, Mapping):
        raise ResourceHealthContractError("ResourceHealthEvidence 必须是对象")
    raw_keys = set(payload)
    unknown_fields = tuple(sorted(str(key) for key in raw_keys.difference(RESOURCE_HEALTH_EVIDENCE_FIELDS)))
    if unknown_fields:
        raise ResourceHealthContractError("ResourceHealthEvidence 不允许未知字段")
    evidence = ResourceHealthEvidence(
        evidence_id=_require_non_empty_string(payload.get("evidence_id"), field="evidence_id"),
        resource_id=_require_non_empty_string(payload.get("resource_id"), field="resource_id"),
        resource_type=_require_non_empty_string(payload.get("resource_type"), field="resource_type"),
        status=_require_non_empty_string(payload.get("status"), field="status"),
        observed_at=_require_non_empty_string(payload.get("observed_at"), field="observed_at"),
        provenance=_require_non_empty_string(payload.get("provenance"), field="provenance"),
        reason=_require_non_empty_string(payload.get("reason"), field="reason"),
        redaction_status=_require_non_empty_string(payload.get("redaction_status"), field="redaction_status"),
        expires_at=_optional_non_empty_string(payload.get("expires_at"), field="expires_at"),
        freshness_policy_ref=_optional_non_empty_string(payload.get("freshness_policy_ref"), field="freshness_policy_ref"),
        task_id=_optional_non_empty_string(payload.get("task_id"), field="task_id"),
        lease_id=_optional_non_empty_string(payload.get("lease_id"), field="lease_id"),
        bundle_id=_optional_non_empty_string(payload.get("bundle_id"), field="bundle_id"),
        adapter_key=_optional_non_empty_string(payload.get("adapter_key"), field="adapter_key"),
        capability=_optional_non_empty_string(payload.get("capability"), field="capability"),
        operation=_optional_non_empty_string(payload.get("operation"), field="operation"),
        diagnostic_ref=_optional_non_empty_string(payload.get("diagnostic_ref"), field="diagnostic_ref"),
    )
    validate_resource_health_evidence(evidence)
    return evidence


def validate_resource_health_evidence(evidence: ResourceHealthEvidence) -> None:
    _require_non_empty_string(evidence.evidence_id, field="evidence_id")
    _require_non_empty_string(evidence.resource_id, field="resource_id")
    if evidence.resource_type != "account":
        raise ResourceHealthContractError("ResourceHealthEvidence.resource_type 当前只允许 account")
    if evidence.status not in RESOURCE_HEALTH_EVIDENCE_STATUSES:
        raise ResourceHealthContractError("ResourceHealthEvidence.status 不在允许值范围内")
    parse_rfc3339_utc_datetime(evidence.observed_at, field="observed_at")
    if evidence.expires_at is not None:
        expires_at = parse_rfc3339_utc_datetime(evidence.expires_at, field="expires_at")
        observed_at = parse_rfc3339_utc_datetime(evidence.observed_at, field="observed_at")
        if expires_at <= observed_at:
            raise ResourceHealthContractError("ResourceHealthEvidence.expires_at 必须晚于 observed_at")
    if evidence.status == SESSION_HEALTH_HEALTHY:
        _require_non_empty_string(evidence.expires_at, field="expires_at")
        _require_non_empty_string(evidence.freshness_policy_ref, field="freshness_policy_ref")
    if evidence.provenance not in RESOURCE_HEALTH_PROVENANCE_VALUES:
        raise ResourceHealthContractError("ResourceHealthEvidence.provenance 不在允许值范围内")
    if evidence.redaction_status != "redacted":
        raise ResourceHealthContractError("ResourceHealthEvidence 必须已脱敏")
    _require_non_empty_string(evidence.reason, field="reason")
    for field in (
        "task_id",
        "lease_id",
        "bundle_id",
        "adapter_key",
        "capability",
        "operation",
        "diagnostic_ref",
    ):
        _optional_non_empty_string(getattr(evidence, field), field=field)
    _reject_private_tokens("reason", evidence.reason)
    if evidence.diagnostic_ref is not None:
        _reject_private_tokens("diagnostic_ref", evidence.diagnostic_ref)


def decide_resource_health_admission(
    *,
    decision_id: str,
    task_id: str,
    adapter_key: str,
    capability: str,
    requested_slots: Sequence[str],
    resources: Sequence[ResourceRecord],
    evidence: Sequence[ResourceHealthEvidence | Mapping[str, Any]],
    evaluated_at: str,
    operation: str | None = None,
    require_fresh_account_session: bool = True,
) -> ResourceAdmissionDecision:
    normalized_resources = tuple(resources)
    account_resources = tuple(record for record in normalized_resources if record.resource_type == "account")
    normalized_requested_slots = tuple(requested_slots)
    health_gated = require_fresh_account_session and "account" in normalized_requested_slots
    evidence_refs: list[str] = []
    projected_health = SESSION_HEALTH_HEALTHY
    decision_status = RESOURCE_ADMISSION_DECISION_ADMITTED
    failure_reason: str | None = None
    fail_closed = False

    try:
        evaluated_at_dt = parse_rfc3339_utc_datetime(evaluated_at, field="evaluated_at")
        if health_gated:
            normalized_evidence = tuple(_coerce_evidence(item) for item in evidence)
            evidence_refs = [item.evidence_id for item in normalized_evidence]
            for item in normalized_evidence:
                _validate_evidence_context(
                    item,
                    task_id=task_id,
                    adapter_key=adapter_key,
                    capability=capability,
                    operation=operation,
                )
            if not account_resources:
                projected_health = SESSION_HEALTH_UNKNOWN
                decision_status = RESOURCE_ADMISSION_DECISION_REJECTED
                failure_reason = "credential_session_unknown"
                fail_closed = True
            else:
                account_resource_ids = {account.resource_id for account in account_resources}
                for item in normalized_evidence:
                    if item.resource_id not in account_resource_ids:
                        raise ResourceHealthContractError("ResourceHealthEvidence.resource_id 与当前 account context 不一致")
                for account_resource in account_resources:
                    credential = credential_material_from_account_resource(account_resource)
                    if credential.adapter_key != adapter_key:
                        raise ResourceHealthContractError("CredentialMaterial.adapter_key 与当前 context 不一致")
                projected_health = _project_account_resources_health(
                    account_resources=account_resources,
                    evidence=normalized_evidence,
                    evaluated_at=evaluated_at_dt,
                )
                decision_status, failure_reason, fail_closed = _decision_for_projected_health(projected_health)
    except ResourceHealthContractError as error:
        projected_health = SESSION_HEALTH_UNKNOWN
        decision_status = RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT
        failure_reason = (
            "credential_material_contract_invalid"
            if _is_credential_material_contract_error(error)
            else RESOURCE_HEALTH_CONTRACT_INVALID_REASON
        )
        fail_closed = True
        evidence_refs = []

    return ResourceAdmissionDecision(
        decision_id=decision_id,
        task_id=task_id,
        adapter_key=adapter_key,
        capability=capability,
        operation=operation,
        requested_slots=normalized_requested_slots,
        resource_ids=tuple(record.resource_id for record in normalized_resources),
        health_evidence_refs=tuple(evidence_refs),
        evaluated_at=evaluated_at,
        projected_session_health=projected_health,
        decision_status=decision_status,
        failure_reason=failure_reason,
        fail_closed=fail_closed,
    )


def resource_admission_decision_to_dict(decision: ResourceAdmissionDecision) -> dict[str, Any]:
    if decision.projected_session_health not in SESSION_HEALTH_VALUES:
        raise ResourceHealthContractError("ResourceAdmissionDecision.projected_session_health 不合法")
    if decision.decision_status not in {
        RESOURCE_ADMISSION_DECISION_ADMITTED,
        RESOURCE_ADMISSION_DECISION_REJECTED,
        RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT,
    }:
        raise ResourceHealthContractError("ResourceAdmissionDecision.decision_status 不合法")
    parse_rfc3339_utc_datetime(decision.evaluated_at, field="evaluated_at")
    return {
        "decision_id": decision.decision_id,
        "task_id": decision.task_id,
        "adapter_key": decision.adapter_key,
        "capability": decision.capability,
        "operation": decision.operation,
        "requested_slots": list(decision.requested_slots),
        "resource_ids": list(decision.resource_ids),
        "health_evidence_refs": list(decision.health_evidence_refs),
        "evaluated_at": decision.evaluated_at,
        "projected_session_health": decision.projected_session_health,
        "decision_status": decision.decision_status,
        "failure_reason": decision.failure_reason,
        "fail_closed": decision.fail_closed,
    }


def invalidate_active_lease_from_health_evidence(
    *,
    evidence: ResourceHealthEvidence | Mapping[str, Any],
    store: ResourceLifecycleStore,
    task_context_task_id: str,
    operation: str | None = None,
    resource_trace_store=None,
) -> ResourceReleaseResult | ResourceAdmissionDecision:
    normalized_evidence = _coerce_evidence(evidence)
    if normalized_evidence.status != SESSION_HEALTH_INVALID:
        raise ResourceHealthContractError("只有 invalid health evidence 可以触发 resource invalidation")
    if _missing_active_context_binding(normalized_evidence):
        return _invalid_contract_decision(normalized_evidence, task_context_task_id)
    if normalized_evidence.task_id != task_context_task_id:
        return _invalid_contract_decision(normalized_evidence, task_context_task_id)
    if operation is None or normalized_evidence.operation != operation:
        return _invalid_contract_decision(normalized_evidence, task_context_task_id)
    try:
        snapshot = load_snapshot_from_store(store)
        validate_snapshot(snapshot)
    except ResourceLifecycleContractError as error:
        return failure_envelope(
            task_context_task_id,
            normalized_evidence.adapter_key or "",
            normalized_evidence.capability or "",
            runtime_contract_error(
                "resource_state_conflict",
                "resource health invalidation 无法读取有效 resource lifecycle truth",
                details={"reason": str(error)},
            ),
        )
    active_lease = _find_active_lease(snapshot.leases, lease_id=normalized_evidence.lease_id)
    if active_lease is None:
        existing_lease = _find_lease(snapshot.leases, lease_id=normalized_evidence.lease_id)
        if existing_lease is not None and _evidence_mismatches_lease_context(normalized_evidence, existing_lease):
            return _invalid_contract_decision(normalized_evidence, task_context_task_id)
        active_lease_for_resource = _find_active_lease_for_resource(snapshot.leases, resource_id=normalized_evidence.resource_id)
        if active_lease_for_resource is not None:
            return _invalid_contract_decision(normalized_evidence, task_context_task_id)
        return _invalidation_rejected_decision(normalized_evidence, task_context_task_id)
    resources_by_id = {resource.resource_id: resource for resource in snapshot.resources}
    bound_resource = resources_by_id.get(normalized_evidence.resource_id)
    if normalized_evidence.resource_id not in active_lease.resource_ids or bound_resource is None:
        return _invalid_contract_decision(normalized_evidence, task_context_task_id)
    if bound_resource.resource_type != "account":
        return _invalid_contract_decision(normalized_evidence, task_context_task_id)
    if task_context_task_id != active_lease.task_id:
        return _invalid_contract_decision(normalized_evidence, task_context_task_id)
    if active_lease.task_id != normalized_evidence.task_id:
        return _invalid_contract_decision(normalized_evidence, task_context_task_id)
    if normalized_evidence.bundle_id is not None and normalized_evidence.bundle_id != active_lease.bundle_id:
        return _invalid_contract_decision(normalized_evidence, task_context_task_id)
    if normalized_evidence.adapter_key != active_lease.adapter_key:
        return _invalid_contract_decision(normalized_evidence, task_context_task_id)
    if normalized_evidence.capability != active_lease.capability:
        return _invalid_contract_decision(normalized_evidence, task_context_task_id)
    return release(
        ReleaseRequest(
            lease_id=active_lease.lease_id,
            task_id=active_lease.task_id,
            target_status_after_release="INVALID",
            reason=RESOURCE_INVALIDATION_REASON_CREDENTIAL_SESSION_INVALID,
        ),
        store,
        task_context_task_id,
        resource_trace_store,
    )


def _project_account_resources_health(
    *,
    account_resources: Sequence[ResourceRecord],
    evidence: Sequence[ResourceHealthEvidence],
    evaluated_at: datetime,
) -> str:
    projected = SESSION_HEALTH_HEALTHY
    for account in account_resources:
        account_evidence = tuple(item for item in evidence if item.resource_id == account.resource_id)
        if not account_evidence:
            return SESSION_HEALTH_UNKNOWN
        latest = max(
            account_evidence,
            key=lambda item: (
                parse_rfc3339_utc_datetime(item.observed_at, field="observed_at"),
                _session_health_severity(item.status),
            ),
        )
        if latest.status == SESSION_HEALTH_INVALID:
            return SESSION_HEALTH_INVALID
        if latest.status == SESSION_HEALTH_STALE:
            projected = SESSION_HEALTH_STALE
            continue
        if latest.expires_at is None:
            raise ResourceHealthContractError("healthy evidence 缺少 expires_at")
        expires_at = parse_rfc3339_utc_datetime(latest.expires_at, field="expires_at")
        if evaluated_at >= expires_at:
            projected = SESSION_HEALTH_STALE
    return projected


def _session_health_severity(status: str) -> int:
    if status == SESSION_HEALTH_INVALID:
        return 3
    if status == SESSION_HEALTH_STALE:
        return 2
    if status == SESSION_HEALTH_HEALTHY:
        return 1
    return 0


def _decision_for_projected_health(projected_health: str) -> tuple[str, str | None, bool]:
    if projected_health == SESSION_HEALTH_HEALTHY:
        return RESOURCE_ADMISSION_DECISION_ADMITTED, None, False
    if projected_health == SESSION_HEALTH_STALE:
        return RESOURCE_ADMISSION_DECISION_REJECTED, "credential_session_stale", True
    if projected_health == SESSION_HEALTH_INVALID:
        return RESOURCE_ADMISSION_DECISION_REJECTED, "pre_admission_session_invalid", True
    return RESOURCE_ADMISSION_DECISION_REJECTED, "credential_session_unknown", True


def _coerce_evidence(value: ResourceHealthEvidence | Mapping[str, Any]) -> ResourceHealthEvidence:
    if isinstance(value, ResourceHealthEvidence):
        validate_resource_health_evidence(value)
        return value
    if isinstance(value, Mapping):
        return resource_health_evidence_from_dict(value)
    raise ResourceHealthContractError("ResourceHealthEvidence 必须是对象")


def _validate_evidence_context(
    evidence: ResourceHealthEvidence,
    *,
    task_id: str,
    adapter_key: str,
    capability: str,
    operation: str | None,
) -> None:
    if evidence.task_id != task_id:
        raise ResourceHealthContractError("ResourceHealthEvidence.task_id 与当前 context 不一致")
    if evidence.adapter_key != adapter_key:
        raise ResourceHealthContractError("ResourceHealthEvidence.adapter_key 与当前 context 不一致")
    if evidence.capability != capability:
        raise ResourceHealthContractError("ResourceHealthEvidence.capability 与当前 context 不一致")
    if operation is None or evidence.operation != operation:
        raise ResourceHealthContractError("ResourceHealthEvidence.operation 与当前 context 不一致")


def _invalidation_rejected_decision(
    evidence: ResourceHealthEvidence,
    task_context_task_id: str,
) -> ResourceAdmissionDecision:
    return ResourceAdmissionDecision(
        decision_id=f"resource-invalidation:{evidence.evidence_id}",
        task_id=evidence.task_id or task_context_task_id,
        adapter_key=evidence.adapter_key or "",
        capability=evidence.capability or "",
        operation=evidence.operation,
        requested_slots=("account",),
        resource_ids=(evidence.resource_id,),
        health_evidence_refs=(evidence.evidence_id,),
        evaluated_at=now_rfc3339_utc(),
        projected_session_health=SESSION_HEALTH_INVALID,
        decision_status=RESOURCE_ADMISSION_DECISION_REJECTED,
        failure_reason="pre_admission_session_invalid",
        fail_closed=True,
    )


def _invalid_contract_decision(
    evidence: ResourceHealthEvidence,
    task_context_task_id: str,
) -> ResourceAdmissionDecision:
    return ResourceAdmissionDecision(
        decision_id=f"resource-invalidation:{evidence.evidence_id}",
        task_id=evidence.task_id or task_context_task_id,
        adapter_key=evidence.adapter_key or "",
        capability=evidence.capability or "",
        operation=evidence.operation,
        requested_slots=("account",),
        resource_ids=(evidence.resource_id,),
        health_evidence_refs=(evidence.evidence_id,),
        evaluated_at=now_rfc3339_utc(),
        projected_session_health=SESSION_HEALTH_UNKNOWN,
        decision_status=RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT,
        failure_reason=RESOURCE_HEALTH_CONTRACT_INVALID_REASON,
        fail_closed=True,
    )


def _find_active_lease(leases: Sequence[ResourceLease], *, lease_id: str) -> ResourceLease | None:
    for lease in leases:
        if lease.lease_id == lease_id and lease.released_at is None:
            return lease
    return None


def _find_active_lease_for_resource(leases: Sequence[ResourceLease], *, resource_id: str) -> ResourceLease | None:
    for lease in leases:
        if lease.released_at is None and resource_id in lease.resource_ids:
            return lease
    return None


def _missing_active_context_binding(evidence: ResourceHealthEvidence) -> bool:
    return (
        evidence.task_id is None
        or evidence.lease_id is None
        or evidence.bundle_id is None
        or evidence.adapter_key is None
        or evidence.capability is None
        or evidence.operation is None
    )


def _find_lease(leases: Sequence[ResourceLease], *, lease_id: str) -> ResourceLease | None:
    for lease in leases:
        if lease.lease_id == lease_id:
            return lease
    return None


def _evidence_mismatches_lease_context(evidence: ResourceHealthEvidence, lease: ResourceLease) -> bool:
    if evidence.resource_id not in lease.resource_ids:
        return True
    if evidence.task_id != lease.task_id:
        return True
    if evidence.bundle_id != lease.bundle_id:
        return True
    if evidence.adapter_key != lease.adapter_key:
        return True
    if evidence.capability != lease.capability:
        return True
    return False


def _is_credential_material_contract_error(error: ResourceHealthContractError) -> bool:
    message = str(error)
    return "CredentialMaterial" in message or "account resource material" in message


def _normalize_json_mapping(value: Mapping[str, Any], *, field: str) -> Mapping[str, Any]:
    try:
        normalized = normalize_json_value(dict(value), field=field)
    except TaskRecordContractError as error:
        raise ResourceHealthContractError(str(error)) from error
    if not isinstance(normalized, Mapping):
        raise ResourceHealthContractError(f"{field} 必须是对象")
    return normalized


def _require_non_empty_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ResourceHealthContractError(f"{field} 必须为非空字符串")
    return value


def _optional_non_empty_string(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ResourceHealthContractError(f"{field} 必须为非空字符串或 null")
    return value


def _reject_private_tokens(field: str, value: str) -> None:
    normalized = value.lower()
    has_private_token_name = any(token in normalized for token in _PRIVATE_CREDENTIAL_TOKENS)
    has_unredacted_marker = any(marker in normalized for marker in _UNREDACTED_MARKERS)
    if _PRIVATE_ASSIGNMENT_RE.search(value) or (has_private_token_name and has_unredacted_marker):
        raise ResourceHealthContractError(f"{field} 不得包含 credential/session 私有字段")
