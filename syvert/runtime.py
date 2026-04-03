from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Callable, Mapping
from uuid import uuid4


CONTENT_DETAIL_BY_URL = "content_detail_by_url"
ALLOWED_CONTENT_TYPES = {"video", "image_post", "mixed_media", "unknown"}
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


@dataclass(frozen=True)
class TaskRequest:
    adapter_key: str
    capability: str
    input: "TaskInput"


@dataclass(frozen=True)
class TaskInput:
    url: str


@dataclass
class PlatformAdapterError(Exception):
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__init__(self.message)


def default_task_id_factory() -> str:
    return f"task-{uuid4().hex}"


def execute_task(
    request: TaskRequest,
    *,
    adapters: Mapping[str, Any],
    task_id_factory: Callable[[], str] | None = None,
) -> dict[str, Any]:
    task_id, task_id_error = resolve_task_id(task_id_factory)
    if task_id_error is not None:
        return failure_envelope(task_id, request.adapter_key, request.capability, task_id_error)

    contract_error = validate_request(request)
    if contract_error is not None:
        return failure_envelope(task_id, request.adapter_key, request.capability, contract_error)

    adapter = adapters.get(request.adapter_key)
    if adapter is None:
        return failure_envelope(
            task_id,
            request.adapter_key,
            request.capability,
            {
                "category": "runtime_contract",
                "code": "adapter_not_found",
                "message": f"adapter `{request.adapter_key}` 不存在",
                "details": {},
            },
        )

    supported_capabilities = getattr(adapter, "supported_capabilities", frozenset())
    if request.capability not in supported_capabilities:
        return failure_envelope(
            task_id,
            request.adapter_key,
            request.capability,
            {
                "category": "runtime_contract",
                "code": "capability_not_supported",
                "message": f"adapter `{request.adapter_key}` 不支持 `{request.capability}`",
                "details": {
                    "supported_capabilities": sorted(supported_capabilities),
                },
            },
        )

    try:
        payload = adapter.execute(request)
        payload_error = validate_success_payload(payload)
        if payload_error is not None:
            return failure_envelope(task_id, request.adapter_key, request.capability, payload_error)
    except PlatformAdapterError as error:
        return failure_envelope(
            task_id,
            request.adapter_key,
            request.capability,
            {
                "category": "platform",
                "code": error.code,
                "message": error.message,
                "details": error.details,
            },
        )
    except Exception as error:
        return failure_envelope(
            task_id,
            request.adapter_key,
            request.capability,
            runtime_contract_error(
                "adapter_execution_error",
                str(error) or error.__class__.__name__,
            ),
        )

    return {
        "task_id": task_id,
        "adapter_key": request.adapter_key,
        "capability": request.capability,
        "status": "success",
        "raw": payload["raw"],
        "normalized": payload["normalized"],
    }


def validate_request(request: TaskRequest) -> dict[str, Any] | None:
    if type(request) is not TaskRequest:
        return runtime_contract_error("invalid_task_request", "task_request 顶层形状不合法")
    if not request.adapter_key:
        return runtime_contract_error("invalid_task_request", "adapter_key 不能为空")
    if request.capability != CONTENT_DETAIL_BY_URL:
        return runtime_contract_error(
            "invalid_capability",
            f"v0.1.0 仅支持 `{CONTENT_DETAIL_BY_URL}`",
        )
    if type(request.input) is not TaskInput:
        return runtime_contract_error("invalid_task_request", "input 必须为对象")
    if not isinstance(request.input.url, str) or not request.input.url:
        return runtime_contract_error("invalid_task_request", "input.url 不能为空")
    return None


def resolve_task_id(task_id_factory: Callable[[], str] | None) -> tuple[str, dict[str, Any] | None]:
    try:
        generated = (task_id_factory or default_task_id_factory)()
    except Exception as error:
        fallback = default_task_id_factory()
        return (
            fallback,
            runtime_contract_error(
                "invalid_task_id",
                "task_id 必须为非空字符串",
                details={"reason": "task_id_factory_raised", "error_type": error.__class__.__name__},
            ),
        )
    if isinstance(generated, str) and generated:
        return generated, None
    fallback = default_task_id_factory()
    return (
        fallback,
        runtime_contract_error(
            "invalid_task_id",
            "task_id 必须为非空字符串",
            details={"actual_type": type(generated).__name__},
        ),
    )


def validate_success_payload(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    if not isinstance(payload, Mapping):
        return runtime_contract_error(
            "invalid_adapter_success_payload",
            "adapter 成功结果必须是对象",
        )

    if "raw" not in payload or "normalized" not in payload:
        return runtime_contract_error(
            "invalid_adapter_success_payload",
            "成功结果必须同时包含 raw 与 normalized",
        )

    normalized = payload["normalized"]
    if not isinstance(normalized, Mapping):
        return runtime_contract_error(
            "invalid_adapter_success_payload",
            "normalized 必须是对象",
        )

    required_non_empty = ("platform", "content_id", "content_type", "canonical_url")
    for field in required_non_empty:
        value = normalized.get(field)
        if not isinstance(value, str) or not value:
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                f"normalized.{field} 必须为非空字符串",
            )

    if normalized["content_type"] not in ALLOWED_CONTENT_TYPES:
        return runtime_contract_error(
            "invalid_adapter_success_payload",
            "normalized.content_type 不在允许值范围内",
        )

    for field in ("title", "body_text"):
        value = normalized.get(field)
        if not isinstance(value, str):
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                f"normalized.{field} 必须存在且为字符串",
            )

    published_at = normalized.get("published_at")
    if published_at is not None and (not isinstance(published_at, str) or not is_valid_rfc3339_utc(published_at)):
        return runtime_contract_error(
            "invalid_adapter_success_payload",
            "normalized.published_at 必须为 RFC3339 UTC 或 null",
        )

    for field in ("author", "stats", "media"):
        value = normalized.get(field)
        if not isinstance(value, Mapping):
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                f"normalized.{field} 必须存在且为对象",
            )

    author = normalized["author"]
    stats = normalized["stats"]
    media = normalized["media"]

    for field in ("author_id", "display_name", "avatar_url"):
        if field not in author:
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                f"normalized.author.{field} 不得缺失",
            )

    for field in ("like_count", "comment_count", "share_count", "collect_count"):
        if field not in stats:
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                f"normalized.stats.{field} 不得缺失",
            )

    for field in ("cover_url", "video_url", "image_urls"):
        if field not in media:
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                f"normalized.media.{field} 不得缺失",
            )

    avatar_url = author.get("avatar_url")
    author_id = author.get("author_id")
    display_name = author.get("display_name")

    if author_id is not None and (not isinstance(author_id, str) or not author_id):
        return runtime_contract_error(
            "invalid_adapter_success_payload",
            "normalized.author.author_id 必须为非空字符串或 null",
        )
    if display_name is not None and (not isinstance(display_name, str) or not display_name):
        return runtime_contract_error(
            "invalid_adapter_success_payload",
            "normalized.author.display_name 必须为非空字符串或 null",
        )
    if avatar_url is not None and not isinstance(avatar_url, str):
        return runtime_contract_error(
            "invalid_adapter_success_payload",
            "normalized.author.avatar_url 必须为字符串或 null",
        )

    for field in ("like_count", "comment_count", "share_count", "collect_count"):
        value = stats.get(field)
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                f"normalized.stats.{field} 必须为整数或 null",
            )

    for field in ("cover_url", "video_url"):
        value = media.get(field)
        if value is not None and not isinstance(value, str):
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                f"normalized.media.{field} 必须为字符串或 null",
            )

    image_urls = media.get("image_urls")
    if not isinstance(image_urls, list) or not all(isinstance(item, str) for item in image_urls):
        return runtime_contract_error(
            "invalid_adapter_success_payload",
            "normalized.media.image_urls 必须是字符串数组",
        )

    return None


def is_valid_rfc3339_utc(value: str) -> bool:
    if not RFC3339_UTC_RE.fullmatch(value):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo == timezone.utc


def failure_envelope(task_id: str, adapter_key: str, capability: str, error: Mapping[str, Any]) -> dict[str, Any]:
    details = error.get("details", {})
    if not isinstance(details, Mapping):
        details = {}
    return {
        "task_id": task_id,
        "adapter_key": adapter_key,
        "capability": capability,
        "status": "failed",
        "error": {
            "category": error["category"],
            "code": error["code"],
            "message": error["message"],
            "details": dict(details),
        },
    }


def runtime_contract_error(code: str, message: str, *, details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        "category": "runtime_contract",
        "code": code,
        "message": message,
        "details": dict(details or {}),
    }
