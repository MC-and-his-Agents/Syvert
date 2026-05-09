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

COMMENT_COLLECTION_OPERATION = "comment_collection"
COMMENT_COLLECTION_TARGET_TYPE = "content"
COMMENT_VISIBILITY_STATUSES = frozenset({"visible", "deleted", "invisible", "unavailable"})
COMMENT_COLLECTION_FAILURE_CLASSIFICATIONS = frozenset(
    {
        "target_not_found",
        "rate_limited",
        "permission_denied",
        "platform_failed",
        "provider_or_network_blocked",
        "cursor_invalid_or_expired",
        "credential_invalid",
        "verification_required",
        "signature_or_request_invalid",
    }
)
COMMENT_PLACEHOLDER_SOURCE_ID_PREFIX = "public-placeholder:"

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


@dataclass(frozen=True)
class CommentContinuation:
    continuation_token: str
    continuation_family: str
    resume_target_ref: str
    resume_comment_ref: str | None = None
    issued_at: str | None = None


@dataclass(frozen=True)
class CommentReplyCursor:
    reply_cursor_token: str
    reply_cursor_family: str
    resume_target_ref: str
    resume_comment_ref: str
    issued_at: str | None = None


@dataclass(frozen=True)
class CommentRequestCursor:
    page_continuation: CommentContinuation | None = None
    reply_cursor: CommentReplyCursor | None = None


@dataclass(frozen=True)
class NormalizedCommentItem:
    source_platform: str
    source_type: str
    source_id: str
    canonical_ref: str
    body_text_hint: str
    root_comment_ref: str
    author_ref: str | None = None
    parent_comment_ref: str | None = None
    target_comment_ref: str | None = None
    published_at: str | None = None


@dataclass(frozen=True)
class CommentItemEnvelope:
    item_type: str
    dedup_key: str
    source_id: str
    source_ref: str
    visibility_status: str
    normalized: NormalizedCommentItem
    raw_payload_ref: str
    source_trace: SourceTrace
    reply_cursor: CommentReplyCursor | None = None


@dataclass(frozen=True)
class CommentCollectionResultEnvelope:
    operation: str
    target: CollectionTarget
    items: tuple[CommentItemEnvelope, ...]
    has_more: bool
    next_continuation: CommentContinuation | None
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
    if target.operation == COMMENT_COLLECTION_OPERATION and target.target_type != COMMENT_COLLECTION_TARGET_TYPE:
        raise CollectionContractError(
            "parse_failed",
            "comment_collection 的 target_type 必须为 content",
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


def _read_comment_continuation(payload: Any, *, field_name: str) -> CommentContinuation | None:
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
            "resume_comment_ref",
            "issued_at",
        ),
    )
    return CommentContinuation(
        continuation_token=_ensure_non_empty_string(
            raw_continuation["continuation_token"], f"{field_name}.continuation_token"
        ),
        continuation_family=_ensure_non_empty_string(
            raw_continuation["continuation_family"], f"{field_name}.continuation_family"
        ),
        resume_target_ref=_ensure_non_empty_string(
            raw_continuation["resume_target_ref"], f"{field_name}.resume_target_ref"
        ),
        resume_comment_ref=_ensure_optional_non_empty_string(
            raw_continuation.get("resume_comment_ref"), f"{field_name}.resume_comment_ref"
        ),
        issued_at=_ensure_optional_non_empty_string(raw_continuation.get("issued_at"), f"{field_name}.issued_at"),
    )


def _read_comment_reply_cursor(payload: Any, *, field_name: str) -> CommentReplyCursor | None:
    if payload is None:
        return None
    raw_cursor = _ensure_mapping(payload, field_name=field_name)
    _ensure_strict_fields(
        raw_cursor,
        field_name=field_name,
        required=("reply_cursor_token", "reply_cursor_family", "resume_target_ref", "resume_comment_ref"),
        allowed=(
            "reply_cursor_token",
            "reply_cursor_family",
            "resume_target_ref",
            "resume_comment_ref",
            "issued_at",
        ),
    )
    return CommentReplyCursor(
        reply_cursor_token=_ensure_non_empty_string(raw_cursor["reply_cursor_token"], f"{field_name}.reply_cursor_token"),
        reply_cursor_family=_ensure_non_empty_string(
            raw_cursor["reply_cursor_family"], f"{field_name}.reply_cursor_family"
        ),
        resume_target_ref=_ensure_non_empty_string(raw_cursor["resume_target_ref"], f"{field_name}.resume_target_ref"),
        resume_comment_ref=_ensure_non_empty_string(raw_cursor["resume_comment_ref"], f"{field_name}.resume_comment_ref"),
        issued_at=_ensure_optional_non_empty_string(raw_cursor.get("issued_at"), f"{field_name}.issued_at"),
    )


def comment_request_cursor_from_dict(payload: Mapping[str, Any] | Any | None) -> CommentRequestCursor:
    if payload is None:
        return CommentRequestCursor()
    raw_cursor = _ensure_mapping(payload, field_name="comment_request_cursor")
    _ensure_strict_fields(
        raw_cursor,
        field_name="comment_request_cursor",
        required=(),
        allowed=("page_continuation", "reply_cursor"),
    )
    return CommentRequestCursor(
        page_continuation=_read_comment_continuation(
            raw_cursor.get("page_continuation"), field_name="comment_request_cursor.page_continuation"
        ),
        reply_cursor=_read_comment_reply_cursor(
            raw_cursor.get("reply_cursor"), field_name="comment_request_cursor.reply_cursor"
        ),
    )


def validate_comment_request_cursor(
    payload: Mapping[str, Any] | CommentRequestCursor | None,
    *,
    target_ref: str,
) -> dict[str, Any] | None:
    try:
        cursor = payload if isinstance(payload, CommentRequestCursor) else comment_request_cursor_from_dict(payload)
        target_ref = _ensure_non_empty_string(target_ref, "target_ref")
        if cursor.page_continuation is not None and cursor.reply_cursor is not None:
            return _contract_error(
                "signature_or_request_invalid",
                "comment request cursor 不能同时携带 page_continuation 与 reply_cursor",
                details={"field": "comment_request_cursor"},
            )
        if cursor.page_continuation is not None and cursor.page_continuation.resume_target_ref != target_ref:
            return _contract_error(
                "cursor_invalid_or_expired",
                "page_continuation.resume_target_ref 必须与 target_ref 一致",
                details={
                    "field": "comment_request_cursor.page_continuation.resume_target_ref",
                    "target_ref": target_ref,
                    "resume_target_ref": cursor.page_continuation.resume_target_ref,
                },
            )
        if cursor.reply_cursor is not None and cursor.reply_cursor.resume_target_ref != target_ref:
            return _contract_error(
                "cursor_invalid_or_expired",
                "reply_cursor.resume_target_ref 必须与 target_ref 一致",
                details={
                    "field": "comment_request_cursor.reply_cursor.resume_target_ref",
                    "target_ref": target_ref,
                    "resume_target_ref": cursor.reply_cursor.resume_target_ref,
                },
            )
        return None
    except CollectionContractError as error:
        return {"code": error.code, "message": error.message, "details": dict(error.details)}


def comment_request_cursor_to_dict(cursor: CommentRequestCursor) -> dict[str, Any]:
    if not isinstance(cursor, CommentRequestCursor):
        raise ValueError("comment_request_cursor_to_dict 只接受 CommentRequestCursor")
    return {
        "page_continuation": _comment_continuation_to_dict(cursor.page_continuation),
        "reply_cursor": _comment_reply_cursor_to_dict(cursor.reply_cursor),
    }


def _read_normalized_comment_item(payload: Any, *, field_name: str) -> NormalizedCommentItem:
    raw_item = _ensure_mapping(payload, field_name=field_name)
    _ensure_strict_fields(
        raw_item,
        field_name=field_name,
        required=(
            "source_platform",
            "source_type",
            "source_id",
            "canonical_ref",
            "body_text_hint",
            "root_comment_ref",
        ),
        allowed=(
            "source_platform",
            "source_type",
            "source_id",
            "canonical_ref",
            "body_text_hint",
            "root_comment_ref",
            "author_ref",
            "parent_comment_ref",
            "target_comment_ref",
            "published_at",
        ),
    )
    published_at = _ensure_optional_non_empty_string(raw_item.get("published_at"), f"{field_name}.published_at")
    if published_at is not None:
        _ensure_rfc3339_timestamp(published_at, f"{field_name}.published_at")
    return NormalizedCommentItem(
        source_platform=_ensure_non_empty_string(raw_item["source_platform"], f"{field_name}.source_platform"),
        source_type=_ensure_non_empty_string(raw_item["source_type"], f"{field_name}.source_type"),
        source_id=_ensure_non_empty_string(raw_item["source_id"], f"{field_name}.source_id"),
        canonical_ref=_ensure_non_empty_string(raw_item["canonical_ref"], f"{field_name}.canonical_ref"),
        body_text_hint=_ensure_non_empty_string(raw_item["body_text_hint"], f"{field_name}.body_text_hint"),
        root_comment_ref=_ensure_non_empty_string(raw_item["root_comment_ref"], f"{field_name}.root_comment_ref"),
        author_ref=_ensure_optional_non_empty_string(raw_item.get("author_ref"), f"{field_name}.author_ref"),
        parent_comment_ref=_ensure_optional_non_empty_string(
            raw_item.get("parent_comment_ref"), f"{field_name}.parent_comment_ref"
        ),
        target_comment_ref=_ensure_optional_non_empty_string(
            raw_item.get("target_comment_ref"), f"{field_name}.target_comment_ref"
        ),
        published_at=published_at,
    )


def _read_comment_item(payload: Any, *, field_name: str) -> CommentItemEnvelope:
    raw_item = _ensure_mapping(payload, field_name=field_name)
    _ensure_strict_fields(
        raw_item,
        field_name=field_name,
        required=(
            "item_type",
            "dedup_key",
            "source_id",
            "source_ref",
            "visibility_status",
            "normalized",
            "raw_payload_ref",
            "source_trace",
        ),
        allowed=(
            "item_type",
            "dedup_key",
            "source_id",
            "source_ref",
            "visibility_status",
            "normalized",
            "raw_payload_ref",
            "source_trace",
            "reply_cursor",
        ),
    )
    return CommentItemEnvelope(
        item_type=_ensure_non_empty_string(raw_item["item_type"], f"{field_name}.item_type"),
        dedup_key=_ensure_non_empty_string(raw_item["dedup_key"], f"{field_name}.dedup_key"),
        source_id=_ensure_non_empty_string(raw_item["source_id"], f"{field_name}.source_id"),
        source_ref=_ensure_non_empty_string(raw_item["source_ref"], f"{field_name}.source_ref"),
        visibility_status=_ensure_non_empty_string(raw_item["visibility_status"], f"{field_name}.visibility_status"),
        normalized=_read_normalized_comment_item(raw_item["normalized"], field_name=f"{field_name}.normalized"),
        raw_payload_ref=_ensure_non_empty_string(raw_item["raw_payload_ref"], f"{field_name}.raw_payload_ref"),
        source_trace=_read_source_trace(raw_item["source_trace"], field_name=f"{field_name}.source_trace"),
        reply_cursor=_read_comment_reply_cursor(raw_item.get("reply_cursor"), field_name=f"{field_name}.reply_cursor"),
    )


def _read_comment_items(payload: Any, *, field_name: str) -> tuple[CommentItemEnvelope, ...]:
    if not isinstance(payload, (list, tuple)):
        raise CollectionContractError("parse_failed", f"{field_name} 必须为数组", details={"field": field_name})
    return tuple(_read_comment_item(item, field_name=f"{field_name}[{index}]") for index, item in enumerate(payload))


def _validate_comment_contract(envelope: CommentCollectionResultEnvelope) -> dict[str, Any] | None:
    if envelope.operation != COMMENT_COLLECTION_OPERATION:
        return _contract_error(
            "invalid_comment_collection_contract",
            "operation 不是 comment_collection",
            details={"field": "operation", "value": envelope.operation},
        )
    if envelope.target.operation != COMMENT_COLLECTION_OPERATION or envelope.target.target_type != COMMENT_COLLECTION_TARGET_TYPE:
        return _contract_error(
            "invalid_comment_collection_contract",
            "target 必须是 comment_collection + content",
            details={
                "target_operation": envelope.target.operation,
                "target_type": envelope.target.target_type,
            },
        )
    if envelope.result_status not in READ_SIDE_COLLECTION_RESULT_STATUSES:
        return _contract_error(
            "invalid_comment_collection_contract",
            "result_status 不在允许范围",
            details={"field": "result_status", "value": envelope.result_status},
        )
    if envelope.error_classification not in COLLECTION_ERROR_CLASSIFICATIONS:
        return _contract_error(
            "invalid_comment_collection_contract",
            "error_classification 不在允许范围",
            details={"field": "error_classification", "value": envelope.error_classification},
        )

    if envelope.result_status == "empty":
        if envelope.error_classification != "empty_result":
            return _contract_error(
                "invalid_comment_collection_contract",
                "empty 结果必须归类为 empty_result",
                details={"field": "error_classification", "value": envelope.error_classification},
            )
        if envelope.items or envelope.has_more or envelope.next_continuation is not None:
            return _contract_error(
                "invalid_comment_collection_contract",
                "empty 结果必须使用无 items、无 has_more、无 next_continuation 的 envelope",
                details={"field": "comment_collection_result_envelope"},
            )
    elif envelope.error_classification == "empty_result":
        return _contract_error(
            "invalid_comment_collection_contract",
            "empty_result 仅用于 result_status=empty",
            details={"field": "error_classification"},
        )

    if envelope.error_classification in COMMENT_COLLECTION_FAILURE_CLASSIFICATIONS:
        if envelope.items or envelope.has_more or envelope.next_continuation is not None:
            return _contract_error(
                "invalid_comment_collection_contract",
                "collection-level failure 必须 fail-closed",
                details={"field": "comment_collection_result_envelope"},
            )
    if envelope.result_status == "partial_result":
        if envelope.error_classification != "parse_failed" or not envelope.items:
            return _contract_error(
                "invalid_comment_collection_contract",
                "partial_result 必须与 parse_failed 配对并保留至少一个 comment item",
                details={"field": "result_status"},
            )
    if (
        envelope.result_status not in {"partial_result", "complete"}
        and envelope.error_classification == "partial_result"
    ):
        return _contract_error(
            "invalid_comment_collection_contract",
            "partial_result error classification 仅可作为继承兼容 entry 用于 non-failure page",
            details={"field": "error_classification"},
        )
    if (
        envelope.result_status == "complete"
        and envelope.error_classification == "partial_result"
        and not envelope.items
    ):
        return _contract_error(
            "invalid_comment_collection_contract",
            "complete + partial_result compatibility entry 必须保留 comment items",
            details={"field": "items"},
        )
    if envelope.error_classification == "parse_failed":
        if envelope.result_status == "partial_result":
            pass
        elif envelope.result_status == "complete" and not envelope.items and not envelope.has_more and envelope.next_continuation is None:
            pass
        else:
            return _contract_error(
                "invalid_comment_collection_contract",
                "parse_failed 必须是 partial page 或零成功 fail-closed envelope",
                details={"field": "error_classification"},
            )

    if envelope.has_more and envelope.next_continuation is None:
        return _contract_error(
            "invalid_comment_collection_contract",
            "has_more=true 时必须返回 next_continuation",
            details={"field": "next_continuation"},
        )
    if not envelope.has_more and envelope.next_continuation is not None:
        return _contract_error(
            "invalid_comment_collection_contract",
            "has_more=false 时不允许返回 next_continuation",
            details={"field": "next_continuation"},
        )
    if envelope.next_continuation is not None and envelope.next_continuation.resume_target_ref != envelope.target.target_ref:
        return _contract_error(
            "invalid_comment_collection_contract",
            "next_continuation.resume_target_ref 必须与 target_ref 一致",
            details={
                "field": "next_continuation.resume_target_ref",
                "target_ref": envelope.target.target_ref,
                "resume_target_ref": envelope.next_continuation.resume_target_ref,
            },
        )
    if envelope.next_continuation is not None and envelope.next_continuation.resume_comment_ref is not None:
        drifted_items = tuple(
            item.normalized.canonical_ref
            for item in envelope.items
            if item.normalized.parent_comment_ref != envelope.next_continuation.resume_comment_ref
        )
        if drifted_items:
            return _contract_error(
                "invalid_comment_collection_contract",
                "reply-window next_continuation.resume_comment_ref 必须绑定当前 reply page 的 parent_comment_ref",
                details={
                    "field": "next_continuation.resume_comment_ref",
                    "resume_comment_ref": envelope.next_continuation.resume_comment_ref,
                    "drifted_item_refs": drifted_items,
                },
            )

    dedup_keys = tuple(item.dedup_key for item in envelope.items)
    if len(dedup_keys) != len(set(dedup_keys)):
        return _contract_error(
            "invalid_comment_collection_contract",
            "CommentItemEnvelope.dedup_key 不能重复",
            details={"field": "items"},
        )
    for index, item in enumerate(envelope.items):
        item_error = _validate_comment_item_contract(item, index=index, target_ref=envelope.target.target_ref)
        if item_error is not None:
            return item_error
    return None


def _validate_comment_item_contract(
    item: CommentItemEnvelope,
    *,
    index: int,
    target_ref: str,
) -> dict[str, Any] | None:
    field = f"items[{index}]"
    if item.item_type != "comment":
        return _contract_error(
            "invalid_comment_collection_contract",
            "CommentItemEnvelope.item_type 必须为 comment",
            details={"field": f"{field}.item_type", "value": item.item_type},
        )
    if item.visibility_status not in COMMENT_VISIBILITY_STATUSES:
        return _contract_error(
            "invalid_comment_collection_contract",
            "visibility_status 不在允许范围",
            details={"field": f"{field}.visibility_status", "value": item.visibility_status},
        )
    if item.source_id != item.normalized.source_id:
        return _contract_error(
            "invalid_comment_collection_contract",
            "CommentItemEnvelope.source_id 必须与 normalized.source_id 一致",
            details={"field": f"{field}.source_id"},
        )
    if item.normalized.source_id.startswith(COMMENT_PLACEHOLDER_SOURCE_ID_PREFIX):
        expected_ref_prefix = f"{COMMENT_PLACEHOLDER_SOURCE_ID_PREFIX}comment:"
        if not item.normalized.canonical_ref.startswith(expected_ref_prefix):
            return _contract_error(
                "invalid_comment_collection_contract",
                "placeholder canonical_ref 必须使用 public placeholder namespace",
                details={"field": f"{field}.normalized.canonical_ref"},
            )
    if item.normalized.parent_comment_ref is None and item.normalized.root_comment_ref != item.normalized.canonical_ref:
        return _contract_error(
            "invalid_comment_collection_contract",
            "top-level comment 的 root_comment_ref 必须等于 canonical_ref",
            details={"field": f"{field}.normalized.root_comment_ref"},
        )
    if item.normalized.parent_comment_ref is not None:
        if item.normalized.root_comment_ref == item.normalized.canonical_ref:
            return _contract_error(
                "invalid_comment_collection_contract",
                "reply comment 的 root_comment_ref 不得等于自身 canonical_ref",
                details={"field": f"{field}.normalized.root_comment_ref"},
            )
        if item.normalized.parent_comment_ref == item.normalized.canonical_ref:
            return _contract_error(
                "invalid_comment_collection_contract",
                "reply comment 的 parent_comment_ref 不得等于自身 canonical_ref",
                details={"field": f"{field}.normalized.parent_comment_ref"},
            )
        if not _comment_ref_stays_in_thread(
            item.normalized.parent_comment_ref,
            root_comment_ref=item.normalized.root_comment_ref,
        ):
            return _contract_error(
                "invalid_comment_collection_contract",
                "reply comment 的 parent_comment_ref 必须可证明属于 root_comment_ref thread",
                details={"field": f"{field}.normalized.parent_comment_ref"},
            )
        if item.normalized.target_comment_ref is not None and not _comment_ref_stays_in_thread(
            item.normalized.target_comment_ref,
            root_comment_ref=item.normalized.root_comment_ref,
        ):
            return _contract_error(
                "invalid_comment_collection_contract",
                "reply comment 的 target_comment_ref 必须可证明属于 root_comment_ref thread",
                details={"field": f"{field}.normalized.target_comment_ref"},
            )
    if item.normalized.parent_comment_ref is None and item.normalized.target_comment_ref is not None:
        return _contract_error(
            "invalid_comment_collection_contract",
            "top-level comment 不得携带 target_comment_ref",
            details={"field": f"{field}.normalized.target_comment_ref"},
        )
    if item.reply_cursor is not None:
        if item.reply_cursor.resume_target_ref != target_ref:
            return _contract_error(
                "invalid_comment_collection_contract",
                "reply_cursor.resume_target_ref 必须与 target_ref 一致",
                details={"field": f"{field}.reply_cursor.resume_target_ref"},
            )
        if item.reply_cursor.resume_comment_ref != item.normalized.canonical_ref:
            return _contract_error(
                "invalid_comment_collection_contract",
                "reply_cursor.resume_comment_ref 必须绑定 normalized.canonical_ref",
                details={"field": f"{field}.reply_cursor.resume_comment_ref"},
            )
    return None


def _comment_ref_stays_in_thread(comment_ref: str, *, root_comment_ref: str) -> bool:
    return comment_ref == root_comment_ref or comment_ref.startswith(f"{root_comment_ref}:")


def _parse_comment_collection_result_envelope(payload: Mapping[str, Any]) -> CommentCollectionResultEnvelope:
    _ensure_strict_fields(
        payload,
        field_name="comment_collection_result_envelope",
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
    operation = _ensure_non_empty_string(payload["operation"], "operation")
    if operation != target.operation:
        raise CollectionContractError(
            "parse_failed",
            "operation 与 target.operation 不一致",
            details={"field": "operation", "operation": operation, "target_operation": target.operation},
        )
    envelope = CommentCollectionResultEnvelope(
        operation=operation,
        target=target,
        items=_read_comment_items(payload["items"], field_name="items"),
        has_more=_ensure_bool(payload["has_more"], "has_more"),
        next_continuation=_read_comment_continuation(payload["next_continuation"], field_name="next_continuation"),
        result_status=_ensure_non_empty_string(payload["result_status"], "result_status"),
        error_classification=_ensure_non_empty_string(payload["error_classification"], "error_classification"),
        raw_payload_ref=_ensure_non_empty_string(payload["raw_payload_ref"], "raw_payload_ref"),
        source_trace=_read_source_trace(payload["source_trace"], field_name="source_trace"),
        audit=_read_audit(payload["audit"], field_name="audit"),
    )
    validation_error = _validate_comment_contract(envelope)
    if validation_error is not None:
        raise CollectionContractError(
            validation_error["code"],
            validation_error["message"],
            details=validation_error["details"],
        )
    return envelope


def comment_collection_result_envelope_from_dict(payload: Mapping[str, Any] | Any) -> CommentCollectionResultEnvelope:
    if not isinstance(payload, Mapping):
        raise CollectionContractError(
            "parse_failed",
            "comment_collection_result_envelope 输入必须是对象",
            details={"field": "comment_collection_result_envelope", "type": type(payload).__name__},
        )
    return _parse_comment_collection_result_envelope(payload)


def comment_collection_result_envelope_to_dict(envelope: CommentCollectionResultEnvelope) -> dict[str, Any]:
    if not isinstance(envelope, CommentCollectionResultEnvelope):
        raise ValueError("comment_collection_result_envelope_to_dict 只接受 CommentCollectionResultEnvelope")
    validation = validate_comment_collection_result_envelope(envelope)
    if validation is not None:
        raise ValueError(f"invalid comment collection result envelope: {validation['message']}")
    return {
        "operation": envelope.operation,
        "target": _target_to_dict(envelope.target),
        "items": [_comment_item_to_dict(item) for item in envelope.items],
        "has_more": envelope.has_more,
        "next_continuation": _comment_continuation_to_dict(envelope.next_continuation),
        "result_status": envelope.result_status,
        "error_classification": envelope.error_classification,
        "raw_payload_ref": envelope.raw_payload_ref,
        "source_trace": _source_trace_to_dict(envelope.source_trace),
        "audit": dict(envelope.audit),
    }


def validate_comment_collection_result_envelope(payload: Any) -> dict[str, Any] | None:
    try:
        if isinstance(payload, Mapping):
            _parse_comment_collection_result_envelope(payload)
            return None
        if isinstance(payload, CommentCollectionResultEnvelope):
            return _validate_comment_contract(payload)
        raise TypeError(f"invalid payload type: {type(payload).__name__}")
    except CollectionContractError as error:
        return {"code": error.code, "message": error.message, "details": dict(error.details)}
    except TypeError as error:
        return _contract_error("parse_failed", str(error), details={"type": type(payload).__name__})
    except ValueError as error:
        return _contract_error("parse_failed", str(error), details={"type": type(payload).__name__})


def _source_trace_to_dict(source_trace: SourceTrace) -> dict[str, Any]:
    return {
        "adapter_key": source_trace.adapter_key,
        "provider_path": source_trace.provider_path,
        **({"resource_profile_ref": source_trace.resource_profile_ref} if source_trace.resource_profile_ref is not None else {}),
        "fetched_at": source_trace.fetched_at,
        "evidence_alias": source_trace.evidence_alias,
    }


def _target_to_dict(target: CollectionTarget) -> dict[str, Any]:
    return {
        "operation": target.operation,
        "target_type": target.target_type,
        "target_ref": target.target_ref,
        **({"target_display_hint": target.target_display_hint} if target.target_display_hint is not None else {}),
        **({"policy_ref": target.policy_ref} if target.policy_ref is not None else {}),
    }


def _comment_continuation_to_dict(continuation: CommentContinuation | None) -> dict[str, Any] | None:
    if continuation is None:
        return None
    return {
        "continuation_token": continuation.continuation_token,
        "continuation_family": continuation.continuation_family,
        "resume_target_ref": continuation.resume_target_ref,
        **({"resume_comment_ref": continuation.resume_comment_ref} if continuation.resume_comment_ref is not None else {}),
        **({"issued_at": continuation.issued_at} if continuation.issued_at is not None else {}),
    }


def _comment_reply_cursor_to_dict(cursor: CommentReplyCursor | None) -> dict[str, Any] | None:
    if cursor is None:
        return None
    return {
        "reply_cursor_token": cursor.reply_cursor_token,
        "reply_cursor_family": cursor.reply_cursor_family,
        "resume_target_ref": cursor.resume_target_ref,
        "resume_comment_ref": cursor.resume_comment_ref,
        **({"issued_at": cursor.issued_at} if cursor.issued_at is not None else {}),
    }


def _comment_item_to_dict(item: CommentItemEnvelope) -> dict[str, Any]:
    return {
        "item_type": item.item_type,
        "dedup_key": item.dedup_key,
        "source_id": item.source_id,
        "source_ref": item.source_ref,
        "visibility_status": item.visibility_status,
        "normalized": {
            "source_platform": item.normalized.source_platform,
            "source_type": item.normalized.source_type,
            "source_id": item.normalized.source_id,
            "canonical_ref": item.normalized.canonical_ref,
            "body_text_hint": item.normalized.body_text_hint,
            "root_comment_ref": item.normalized.root_comment_ref,
            **({"author_ref": item.normalized.author_ref} if item.normalized.author_ref is not None else {}),
            **(
                {"parent_comment_ref": item.normalized.parent_comment_ref}
                if item.normalized.parent_comment_ref is not None
                else {}
            ),
            **(
                {"target_comment_ref": item.normalized.target_comment_ref}
                if item.normalized.target_comment_ref is not None
                else {}
            ),
            **({"published_at": item.normalized.published_at} if item.normalized.published_at is not None else {}),
        },
        "raw_payload_ref": item.raw_payload_ref,
        "source_trace": _source_trace_to_dict(item.source_trace),
        **({"reply_cursor": _comment_reply_cursor_to_dict(item.reply_cursor)} if item.reply_cursor is not None else {}),
    }
