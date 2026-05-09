from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any

READ_SIDE_COLLECTION_RESULT_STATUSES = frozenset(
    {
        "complete",
        "empty",
        "partial_result",
    }
)

COLLECTION_ERROR_CLASSIFICATIONS = frozenset(
    {
        "empty_result",
        "target_not_found",
        "rate_limited",
        "permission_denied",
        "platform_failed",
        "provider_or_network_blocked",
        "cursor_invalid_or_expired",
        "parse_failed",
        "partial_result",
        "credential_invalid",
        "verification_required",
        "signature_or_request_invalid",
    }
)

READ_SIDE_COLLECTION_OPERATIONS = frozenset(
    {
        "content_search_by_keyword",
        "content_list_by_creator",
    }
)

RFC3339_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


class CollectionContractError(ValueError):
    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})


@dataclass(frozen=True)
class SourceTrace:
    adapter_key: str
    provider_path: str
    fetched_at: str
    evidence_alias: str
    resource_profile_ref: str | None = None


@dataclass(frozen=True)
class CollectionTarget:
    operation: str
    target_type: str
    target_ref: str
    target_display_hint: str | None = None
    policy_ref: str | None = None


@dataclass(frozen=True)
class CollectionContinuation:
    continuation_token: str
    continuation_family: str
    resume_target_ref: str
    issued_at: str | None = None


@dataclass(frozen=True)
class NormalizedCollectionItem:
    source_platform: str
    source_type: str
    source_id: str
    canonical_ref: str
    title_or_text_hint: str
    creator_ref: str | None = None
    published_at: str | None = None
    media_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class CollectionItemEnvelope:
    item_type: str
    dedup_key: str
    source_id: str
    source_ref: str
    normalized: NormalizedCollectionItem
    raw_payload_ref: str
    source_trace: SourceTrace


@dataclass(frozen=True)
class CollectionResultEnvelope:
    operation: str
    target: CollectionTarget
    items: tuple[CollectionItemEnvelope, ...]
    has_more: bool
    next_continuation: CollectionContinuation | None
    result_status: str
    error_classification: str
    raw_payload_ref: str
    source_trace: SourceTrace
    audit: Mapping[str, Any]


def _contract_error(code: str, message: str, *, details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {"code": code, "message": message, "details": dict(details or {})}


def _ensure_mapping(payload: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise CollectionContractError(
            "parse_failed",
            f"{field_name} 必须是对象",
            details={"field": field_name, "type": type(payload).__name__},
        )
    return payload


def _ensure_non_empty_string(payload: Any, field_name: str) -> str:
    if not isinstance(payload, str) or not payload.strip():
        raise CollectionContractError(
            "parse_failed",
            f"{field_name} 必须为非空字符串",
            details={"field": field_name},
        )
    return payload


def _ensure_optional_non_empty_string(payload: Any, field_name: str) -> str | None:
    if payload is None:
        return None
    return _ensure_non_empty_string(payload, field_name)


def _ensure_bool(payload: Any, field_name: str) -> bool:
    if not isinstance(payload, bool):
        raise CollectionContractError(
            "parse_failed",
            f"{field_name} 必须为布尔值",
            details={"field": field_name},
        )
    return payload


def _ensure_tuple_of_non_empty_strings(payload: Any, field_name: str) -> tuple[str, ...]:
    if payload is None:
        return ()
    if not isinstance(payload, (tuple, list)):
        raise CollectionContractError(
            "parse_failed",
            f"{field_name} 必须为字符串数组",
            details={"field": field_name},
        )
    values = tuple(payload)
    for index, value in enumerate(values):
        if not isinstance(value, str) or not value.strip():
            raise CollectionContractError(
                "parse_failed",
                f"{field_name}[{index}] 必须为非空字符串",
                details={"field": f"{field_name}[{index}]"},
            )
    return values


def _ensure_rfc3339_timestamp(payload: Any, field_name: str) -> str:
    value = _ensure_non_empty_string(payload, field_name)
    if not RFC3339_TIMESTAMP_RE.fullmatch(value):
        raise CollectionContractError(
            "parse_failed",
            f"{field_name} 必须为 RFC3339 时间戳",
            details={"field": field_name},
        )
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise CollectionContractError(
            "parse_failed",
            f"{field_name} 无法按 RFC3339 解析",
            details={"field": field_name, "python_error": error.__class__.__name__},
        )
    return value


def _ensure_strict_fields(
    payload: Mapping[str, Any],
    *,
    field_name: str,
    required: tuple[str, ...],
    allowed: tuple[str, ...] | frozenset[str],
) -> None:
    missing = [name for name in required if name not in payload]
    if missing:
        raise CollectionContractError(
            "parse_failed",
            f"{field_name} 缺少字段: {', '.join(missing)}",
            details={"field": field_name, "missing_fields": tuple(missing)},
        )
    unknown = tuple(sorted(set(payload) - set(allowed)))
    if unknown:
        raise CollectionContractError(
            "parse_failed",
            f"{field_name} 包含未知字段",
            details={"field": field_name, "unknown_fields": unknown},
        )


def _read_source_trace(payload: Any, *, field_name: str) -> SourceTrace:
    raw_trace = _ensure_mapping(payload, field_name=field_name)
    _ensure_strict_fields(
        raw_trace,
        field_name=field_name,
        required=("adapter_key", "provider_path", "fetched_at", "evidence_alias"),
        allowed=(
            "adapter_key",
            "provider_path",
            "resource_profile_ref",
            "fetched_at",
            "evidence_alias",
        ),
    )
    return SourceTrace(
        adapter_key=_ensure_non_empty_string(raw_trace["adapter_key"], f"{field_name}.adapter_key"),
        provider_path=_ensure_non_empty_string(raw_trace["provider_path"], f"{field_name}.provider_path"),
        resource_profile_ref=_ensure_optional_non_empty_string(
            raw_trace.get("resource_profile_ref"),
            f"{field_name}.resource_profile_ref",
        ),
        fetched_at=_ensure_rfc3339_timestamp(raw_trace["fetched_at"], f"{field_name}.fetched_at"),
        evidence_alias=_ensure_non_empty_string(raw_trace["evidence_alias"], f"{field_name}.evidence_alias"),
    )


def _read_target(payload: Any, *, field_name: str) -> CollectionTarget:
    raw_target = _ensure_mapping(payload, field_name=field_name)
    _ensure_strict_fields(
        raw_target,
        field_name=field_name,
        required=("operation", "target_type", "target_ref"),
        allowed=(
            "operation",
            "target_type",
            "target_ref",
            "target_display_hint",
            "policy_ref",
        ),
    )
    target = CollectionTarget(
        operation=_ensure_non_empty_string(raw_target["operation"], f"{field_name}.operation"),
        target_type=_ensure_non_empty_string(raw_target["target_type"], f"{field_name}.target_type"),
        target_ref=_ensure_non_empty_string(raw_target["target_ref"], f"{field_name}.target_ref"),
        target_display_hint=_ensure_optional_non_empty_string(
            raw_target.get("target_display_hint"),
            f"{field_name}.target_display_hint",
        ),
        policy_ref=_ensure_optional_non_empty_string(raw_target.get("policy_ref"), f"{field_name}.policy_ref"),
    )
    if target.operation == "content_search_by_keyword" and target.target_type != "keyword":
        raise CollectionContractError(
            "parse_failed",
            "content_search_by_keyword 的 target_type 必须为 keyword",
            details={"field": f"{field_name}.target_type", "value": target.target_type},
        )
    if target.operation == "content_list_by_creator" and target.target_type != "creator":
        raise CollectionContractError(
            "parse_failed",
            "content_list_by_creator 的 target_type 必须为 creator",
            details={"field": f"{field_name}.target_type", "value": target.target_type},
        )
    return target


def _read_continuation(payload: Any, *, field_name: str) -> CollectionContinuation | None:
    if payload is None:
        return None
    raw_continuation = _ensure_mapping(payload, field_name=field_name)
    _ensure_strict_fields(
        raw_continuation,
        field_name=field_name,
        required=("continuation_token", "continuation_family", "resume_target_ref"),
        allowed=(
            "continuation_token",
            "continuation_family",
            "resume_target_ref",
            "issued_at",
        ),
    )
    return CollectionContinuation(
        continuation_token=_ensure_non_empty_string(
            raw_continuation["continuation_token"], f"{field_name}.continuation_token"
        ),
        continuation_family=_ensure_non_empty_string(
            raw_continuation["continuation_family"], f"{field_name}.continuation_family"
        ),
        resume_target_ref=_ensure_non_empty_string(
            raw_continuation["resume_target_ref"], f"{field_name}.resume_target_ref"
        ),
        issued_at=_ensure_optional_non_empty_string(raw_continuation.get("issued_at"), f"{field_name}.issued_at"),
    )


def _read_normalized_item(payload: Any, *, field_name: str) -> NormalizedCollectionItem:
    raw_item = _ensure_mapping(payload, field_name=field_name)
    _ensure_strict_fields(
        raw_item,
        field_name=field_name,
        required=(
            "source_platform",
            "source_type",
            "source_id",
            "canonical_ref",
            "title_or_text_hint",
        ),
        allowed=(
            "source_platform",
            "source_type",
            "source_id",
            "canonical_ref",
            "title_or_text_hint",
            "creator_ref",
            "published_at",
            "media_refs",
        ),
    )
    published_at = _ensure_optional_non_empty_string(raw_item.get("published_at"), f"{field_name}.published_at")
    if published_at is not None:
        _ensure_rfc3339_timestamp(published_at, f"{field_name}.published_at")
    return NormalizedCollectionItem(
        source_platform=_ensure_non_empty_string(raw_item["source_platform"], f"{field_name}.source_platform"),
        source_type=_ensure_non_empty_string(raw_item["source_type"], f"{field_name}.source_type"),
        source_id=_ensure_non_empty_string(raw_item["source_id"], f"{field_name}.source_id"),
        canonical_ref=_ensure_non_empty_string(raw_item["canonical_ref"], f"{field_name}.canonical_ref"),
        title_or_text_hint=_ensure_non_empty_string(raw_item["title_or_text_hint"], f"{field_name}.title_or_text_hint"),
        creator_ref=_ensure_optional_non_empty_string(raw_item.get("creator_ref"), f"{field_name}.creator_ref"),
        published_at=published_at,
        media_refs=_ensure_tuple_of_non_empty_strings(raw_item.get("media_refs"), f"{field_name}.media_refs"),
    )


def _read_item(payload: Any, *, field_name: str) -> CollectionItemEnvelope:
    raw_item = _ensure_mapping(payload, field_name=field_name)
    _ensure_strict_fields(
        raw_item,
        field_name=field_name,
        required=(
            "item_type",
            "dedup_key",
            "source_id",
            "source_ref",
            "normalized",
            "raw_payload_ref",
            "source_trace",
        ),
        allowed=(
            "item_type",
            "dedup_key",
            "source_id",
            "source_ref",
            "normalized",
            "raw_payload_ref",
            "source_trace",
        ),
    )
    return CollectionItemEnvelope(
        item_type=_ensure_non_empty_string(raw_item["item_type"], f"{field_name}.item_type"),
        dedup_key=_ensure_non_empty_string(raw_item["dedup_key"], f"{field_name}.dedup_key"),
        source_id=_ensure_non_empty_string(raw_item["source_id"], f"{field_name}.source_id"),
        source_ref=_ensure_non_empty_string(raw_item["source_ref"], f"{field_name}.source_ref"),
        normalized=_read_normalized_item(raw_item["normalized"], field_name=f"{field_name}.normalized"),
        raw_payload_ref=_ensure_non_empty_string(raw_item["raw_payload_ref"], f"{field_name}.raw_payload_ref"),
        source_trace=_read_source_trace(raw_item["source_trace"], field_name=f"{field_name}.source_trace"),
    )


def _read_items(payload: Any, *, field_name: str) -> tuple[CollectionItemEnvelope, ...]:
    if not isinstance(payload, (list, tuple)):
        raise CollectionContractError(
            "parse_failed",
            f"{field_name} 必须为数组",
            details={"field": field_name},
        )
    return tuple(
        _read_item(item, field_name=f"{field_name}[{index}]")
        for index, item in enumerate(payload)
    )


def _read_audit(payload: Any, *, field_name: str) -> Mapping[str, Any]:
    return _ensure_mapping(payload, field_name=field_name)


def _validate_contract(
    envelope: CollectionResultEnvelope,
) -> dict[str, Any] | None:
    if envelope.operation not in READ_SIDE_COLLECTION_OPERATIONS:
        return _contract_error(
            "invalid_collection_contract",
            "operation 不是已冻结的 read-side collection operation",
            details={"field": "operation", "value": envelope.operation},
        )
    if envelope.operation != envelope.target.operation:
        return _contract_error(
            "invalid_collection_contract",
            "operation 与 target.operation 不一致",
            details={
                "operation": envelope.operation,
                "target_operation": envelope.target.operation,
            },
        )
    if envelope.result_status not in READ_SIDE_COLLECTION_RESULT_STATUSES:
        return _contract_error(
            "invalid_collection_contract",
            "result_status 不在允许范围",
            details={"field": "result_status", "value": envelope.result_status},
        )
    if envelope.error_classification not in COLLECTION_ERROR_CLASSIFICATIONS:
        return _contract_error(
            "invalid_collection_contract",
            "error_classification 不在允许范围",
            details={"field": "error_classification", "value": envelope.error_classification},
        )

    if envelope.result_status == "empty":
        if envelope.error_classification != "empty_result":
            return _contract_error(
                "invalid_collection_contract",
                "empty 结果必须归类为 empty_result",
                details={"field": "error_classification", "value": envelope.error_classification},
            )
        if envelope.items:
            return _contract_error(
                "invalid_collection_contract",
                "empty 结果必须不携带 items",
                details={"field": "items", "count": len(envelope.items)},
            )
        if envelope.has_more:
            return _contract_error(
                "invalid_collection_contract",
                "empty 结果不得设置 has_more=true",
                details={"field": "has_more", "value": envelope.has_more},
            )
        if envelope.next_continuation is not None:
            return _contract_error(
                "invalid_collection_contract",
                "empty 结果不得携带 next_continuation",
                details={"field": "next_continuation"},
            )
    else:
        if envelope.error_classification == "empty_result":
            return _contract_error(
                "invalid_collection_contract",
                "empty_result 仅用于 result_status=empty",
                details={"field": "error_classification"},
            )

    if envelope.result_status == "partial_result" and envelope.error_classification != "parse_failed":
        return _contract_error(
            "invalid_collection_contract",
            "partial_result 必须与 parse_failed 配对",
            details={"field": "result_status", "value": envelope.result_status},
        )
    if envelope.result_status != "partial_result" and envelope.error_classification == "parse_failed":
        return _contract_error(
            "invalid_collection_contract",
            "parse_failed 仅可用于 partial_result",
            details={"field": "error_classification", "value": envelope.error_classification},
        )

    if envelope.has_more and envelope.next_continuation is None:
        return _contract_error(
            "invalid_collection_contract",
            "has_more=true 时必须返回 next_continuation",
            details={"field": "next_continuation"},
        )
    if not envelope.has_more and envelope.next_continuation is not None:
        return _contract_error(
            "invalid_collection_contract",
            "has_more=false 时不允许返回 next_continuation",
            details={"field": "next_continuation"},
        )
    if envelope.next_continuation is not None and envelope.target.target_ref != envelope.next_continuation.resume_target_ref:
        return _contract_error(
            "invalid_collection_contract",
            "next_continuation.resume_target_ref 必须与 target_ref 一致",
            details={
                "field": "next_continuation.resume_target_ref",
                "target_ref": envelope.target.target_ref,
                "resume_target_ref": envelope.next_continuation.resume_target_ref,
            },
        )

    dedup_keys = tuple(item.dedup_key for item in envelope.items)
    if len(dedup_keys) != len(set(dedup_keys)):
        return _contract_error(
            "invalid_collection_contract",
            "CollectionItemEnvelope.dedup_key 不能重复",
            details={"field": "items"},
        )

    return None


def _parse_collection_result_envelope(payload: Mapping[str, Any]) -> CollectionResultEnvelope:
    _ensure_strict_fields(
        payload,
        field_name="collection_result_envelope",
        required=(
            "operation",
            "target",
            "items",
            "has_more",
            "next_continuation",
            "result_status",
            "error_classification",
            "raw_payload_ref",
            "source_trace",
            "audit",
        ),
        allowed=(
            "operation",
            "target",
            "items",
            "has_more",
            "next_continuation",
            "result_status",
            "error_classification",
            "raw_payload_ref",
            "source_trace",
            "audit",
        ),
    )
    target = _read_target(payload["target"], field_name="target")
    raw_payload_ref = _ensure_non_empty_string(payload["raw_payload_ref"], "raw_payload_ref")
    operation = _ensure_non_empty_string(payload["operation"], "operation")
    if operation != target.operation:
        raise CollectionContractError(
            "parse_failed",
            "operation 与 target.operation 不一致",
            details={"field": "operation", "operation": operation, "target_operation": target.operation},
        )

    envelope = CollectionResultEnvelope(
        operation=operation,
        target=target,
        items=_read_items(payload["items"], field_name="items"),
        has_more=_ensure_bool(payload["has_more"], "has_more"),
        next_continuation=_read_continuation(payload["next_continuation"], field_name="next_continuation"),
        result_status=_ensure_non_empty_string(payload["result_status"], "result_status"),
        error_classification=_ensure_non_empty_string(payload["error_classification"], "error_classification"),
        raw_payload_ref=raw_payload_ref,
        source_trace=_read_source_trace(payload["source_trace"], field_name="source_trace"),
        audit=_read_audit(payload["audit"], field_name="audit"),
    )

    validation_error = _validate_contract(envelope)
    if validation_error is not None:
        raise CollectionContractError(
            validation_error["code"],
            validation_error["message"],
            details=validation_error["details"],
        )
    return envelope


def collection_result_envelope_from_dict(payload: Mapping[str, Any] | Any) -> CollectionResultEnvelope:
    if not isinstance(payload, Mapping):
        raise CollectionContractError(
            "parse_failed",
            "collection_result_envelope 输入必须是对象",
            details={"field": "collection_result_envelope", "type": type(payload).__name__},
        )
    return _parse_collection_result_envelope(payload)


def collection_result_envelope_to_dict(envelope: CollectionResultEnvelope) -> dict[str, Any]:
    if not isinstance(envelope, CollectionResultEnvelope):
        raise ValueError("collection_result_envelope_to_dict 只接受 CollectionResultEnvelope")
    validation = validate_collection_result_envelope(envelope)
    if validation is not None:
        raise ValueError(f"invalid collection result envelope: {validation['message']}")

    return {
        "operation": envelope.operation,
        "target": {
            "operation": envelope.target.operation,
            "target_type": envelope.target.target_type,
            "target_ref": envelope.target.target_ref,
            **(
                {"target_display_hint": envelope.target.target_display_hint}
                if envelope.target.target_display_hint is not None
                else {}
            ),
            **(
                {"policy_ref": envelope.target.policy_ref}
                if envelope.target.policy_ref is not None
                else {}
            ),
        },
        "items": [
            {
                "item_type": item.item_type,
                "dedup_key": item.dedup_key,
                "source_id": item.source_id,
                "source_ref": item.source_ref,
                "normalized": {
                    "source_platform": item.normalized.source_platform,
                    "source_type": item.normalized.source_type,
                    "source_id": item.normalized.source_id,
                    "canonical_ref": item.normalized.canonical_ref,
                    "title_or_text_hint": item.normalized.title_or_text_hint,
                    **(
                        {"creator_ref": item.normalized.creator_ref}
                        if item.normalized.creator_ref is not None
                        else {}
                    ),
                    **(
                        {"published_at": item.normalized.published_at}
                        if item.normalized.published_at is not None
                        else {}
                    ),
                    **(
                        {"media_refs": list(item.normalized.media_refs)}
                        if item.normalized.media_refs
                        else {}
                    ),
                },
                "raw_payload_ref": item.raw_payload_ref,
                "source_trace": {
                    "adapter_key": item.source_trace.adapter_key,
                    "provider_path": item.source_trace.provider_path,
                    **(
                        {"resource_profile_ref": item.source_trace.resource_profile_ref}
                        if item.source_trace.resource_profile_ref is not None
                        else {}
                    ),
                    "fetched_at": item.source_trace.fetched_at,
                    "evidence_alias": item.source_trace.evidence_alias,
                },
            }
            for item in envelope.items
        ],
        "has_more": envelope.has_more,
        "next_continuation": (
            None
            if envelope.next_continuation is None
            else {
                "continuation_token": envelope.next_continuation.continuation_token,
                "continuation_family": envelope.next_continuation.continuation_family,
                "resume_target_ref": envelope.next_continuation.resume_target_ref,
                **(
                    {"issued_at": envelope.next_continuation.issued_at}
                    if envelope.next_continuation.issued_at is not None
                    else {}
                ),
            }
        ),
        "result_status": envelope.result_status,
        "error_classification": envelope.error_classification,
        "raw_payload_ref": envelope.raw_payload_ref,
        "source_trace": {
            "adapter_key": envelope.source_trace.adapter_key,
            "provider_path": envelope.source_trace.provider_path,
            **(
                {"resource_profile_ref": envelope.source_trace.resource_profile_ref}
                if envelope.source_trace.resource_profile_ref is not None
                else {}
            ),
            "fetched_at": envelope.source_trace.fetched_at,
            "evidence_alias": envelope.source_trace.evidence_alias,
        },
        "audit": dict(envelope.audit),
    }


def validate_collection_result_envelope(payload: Any) -> dict[str, Any] | None:
    try:
        if isinstance(payload, Mapping):
            _parse_collection_result_envelope(payload)
            return None
        if isinstance(payload, CollectionResultEnvelope):
            return _validate_contract(payload)
        raise TypeError(f"invalid payload type: {type(payload).__name__}")
    except CollectionContractError as error:
        return {
            "code": error.code,
            "message": error.message,
            "details": dict(error.details),
        }
    except TypeError as error:
        return _contract_error("parse_failed", str(error), details={"type": type(payload).__name__})
    except ValueError as error:
        return _contract_error("parse_failed", str(error), details={"type": type(payload).__name__})
