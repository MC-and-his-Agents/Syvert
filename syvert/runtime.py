from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping
from uuid import uuid4


CONTENT_DETAIL_BY_URL = "content_detail_by_url"
ALLOWED_CONTENT_TYPES = {"video", "image_post", "mixed_media", "unknown"}


@dataclass(frozen=True)
class TaskRequest:
    adapter_key: str
    capability: str
    input_url: str


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
    task_id = (task_id_factory or default_task_id_factory)()
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

    return {
        "task_id": task_id,
        "adapter_key": request.adapter_key,
        "capability": request.capability,
        "status": "success",
        "raw": payload["raw"],
        "normalized": payload["normalized"],
    }


def validate_request(request: TaskRequest) -> dict[str, Any] | None:
    if not request.adapter_key:
        return runtime_contract_error("invalid_task_request", "adapter_key 不能为空")
    if request.capability != CONTENT_DETAIL_BY_URL:
        return runtime_contract_error(
            "invalid_capability",
            f"v0.1.0 仅支持 `{CONTENT_DETAIL_BY_URL}`",
        )
    if not request.input_url:
        return runtime_contract_error("invalid_task_request", "input.url 不能为空")
    return None


def validate_success_payload(payload: Mapping[str, Any]) -> dict[str, Any] | None:
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

    for field in ("author", "stats", "media"):
        value = normalized.get(field)
        if not isinstance(value, Mapping):
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                f"normalized.{field} 必须存在且为对象",
            )

    image_urls = normalized["media"].get("image_urls")
    if not isinstance(image_urls, list) or not all(isinstance(item, str) for item in image_urls):
        return runtime_contract_error(
            "invalid_adapter_success_payload",
            "normalized.media.image_urls 必须是字符串数组",
        )

    return None


def failure_envelope(task_id: str, adapter_key: str, capability: str, error: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "adapter_key": adapter_key,
        "capability": capability,
        "status": "failed",
        "error": {
            "category": error["category"],
            "code": error["code"],
            "message": error["message"],
            "details": dict(error.get("details", {})),
        },
    }


def runtime_contract_error(code: str, message: str, *, details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        "category": "runtime_contract",
        "code": code,
        "message": message,
        "details": dict(details or {}),
    }
