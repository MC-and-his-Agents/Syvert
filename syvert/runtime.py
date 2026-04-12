from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import re
from typing import Any, Callable, Mapping
from uuid import uuid4


CONTENT_DETAIL_BY_URL = "content_detail_by_url"
LEGACY_COLLECTION_MODE = "hybrid"
ALLOWED_TARGET_TYPES = frozenset({"url", "content_id", "creator_id", "keyword"})
ALLOWED_COLLECTION_MODES = frozenset({"public", "authenticated", "hybrid"})
ALLOWED_CONTENT_TYPES = {"video", "image_post", "mixed_media", "unknown"}
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
MISSING = object()


@dataclass(frozen=True)
class TaskInput:
    url: str


@dataclass(frozen=True)
class InputTarget:
    adapter_key: str
    capability: str
    target_type: str
    target_value: str


@dataclass(frozen=True)
class CollectionPolicy:
    collection_mode: str


@dataclass(frozen=True)
class CoreTaskRequest:
    target: InputTarget
    policy: CollectionPolicy


@dataclass(frozen=True)
class TaskRequest:
    adapter_key: str
    capability: str
    input: TaskInput


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
    request: TaskRequest | CoreTaskRequest,
    *,
    adapters: Mapping[str, Any],
    task_id_factory: Callable[[], str] | None = None,
) -> dict[str, Any]:
    adapter_key, capability = extract_request_context(request)
    task_id, task_id_error = resolve_task_id(task_id_factory)
    if task_id_error is not None:
        return failure_envelope(task_id, adapter_key, capability, task_id_error)

    normalized_request, contract_error = normalize_request(request)
    if contract_error is not None:
        return failure_envelope(task_id, adapter_key, capability, contract_error)
    if normalized_request is None:
        return failure_envelope(
            task_id,
            adapter_key,
            capability,
            runtime_contract_error("invalid_task_request", "task_request 顶层形状不合法"),
        )

    adapter_key = normalized_request.target.adapter_key
    capability = normalized_request.target.capability

    adapter, adapter_error = get_adapter(adapters, adapter_key)
    if adapter_error is not None:
        return failure_envelope(task_id, adapter_key, capability, adapter_error)
    if adapter is None:
        return failure_envelope(
            task_id,
            adapter_key,
            capability,
            {
                "category": "runtime_contract",
                "code": "adapter_not_found",
                "message": f"adapter `{adapter_key}` 不存在",
                "details": {},
            },
        )

    supported_capabilities, capability_error = validate_supported_capabilities(
        get_adapter_supported_capabilities(adapter)
    )
    if capability_error is not None:
        return failure_envelope(task_id, adapter_key, capability, capability_error)
    if capability not in supported_capabilities:
        return failure_envelope(
            task_id,
            adapter_key,
            capability,
            {
                "category": "runtime_contract",
                "code": "capability_not_supported",
                "message": f"adapter `{adapter_key}` 不支持 `{capability}`",
                "details": {
                    "supported_capabilities": sorted(supported_capabilities),
                },
            },
        )

    adapter_request, projection_error = project_to_adapter_request(normalized_request)
    if projection_error is not None:
        return failure_envelope(task_id, adapter_key, capability, projection_error)

    try:
        payload = adapter.execute(adapter_request)
        payload_error = validate_success_payload(payload)
        if payload_error is not None:
            return failure_envelope(task_id, adapter_key, capability, payload_error)
    except PlatformAdapterError as error:
        return failure_envelope(
            task_id,
            adapter_key,
            capability,
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
            adapter_key,
            capability,
            runtime_contract_error(
                "adapter_execution_error",
                str(error) or error.__class__.__name__,
            ),
        )

    return {
        "task_id": task_id,
        "adapter_key": adapter_key,
        "capability": capability,
        "status": "success",
        "raw": payload["raw"],
        "normalized": payload["normalized"],
    }


def validate_request(request: Any) -> dict[str, Any] | None:
    _, error = normalize_request(request)
    return error


def normalize_request(request: Any) -> tuple[CoreTaskRequest | None, dict[str, Any] | None]:
    if type(request) is TaskRequest:
        if not isinstance(request.adapter_key, str) or not request.adapter_key:
            return None, runtime_contract_error("invalid_task_request", "adapter_key 不能为空")
        if request.capability != CONTENT_DETAIL_BY_URL:
            return None, runtime_contract_error(
                "invalid_capability",
                f"v0.1.0 仅支持 `{CONTENT_DETAIL_BY_URL}`",
            )
        if type(request.input) is not TaskInput:
            return None, runtime_contract_error("invalid_task_request", "input 必须为对象")
        if not isinstance(request.input.url, str) or not request.input.url:
            return None, runtime_contract_error("invalid_task_request", "input.url 不能为空")
        return (
            CoreTaskRequest(
                target=InputTarget(
                    adapter_key=request.adapter_key,
                    capability=request.capability,
                    target_type="url",
                    target_value=request.input.url,
                ),
                policy=CollectionPolicy(collection_mode=LEGACY_COLLECTION_MODE),
            ),
            None,
        )
    if type(request) is not CoreTaskRequest:
        return None, runtime_contract_error("invalid_task_request", "task_request 顶层形状不合法")
    if type(request.target) is not InputTarget:
        return None, runtime_contract_error("invalid_task_request", "target 必须为对象")
    if type(request.policy) is not CollectionPolicy:
        return None, runtime_contract_error("invalid_task_request", "policy 必须为对象")

    target = request.target
    policy = request.policy
    if not isinstance(target.adapter_key, str) or not target.adapter_key:
        return None, runtime_contract_error("invalid_task_request", "adapter_key 不能为空")
    if target.capability != CONTENT_DETAIL_BY_URL:
        return None, runtime_contract_error(
            "invalid_capability",
            f"v0.1.0 仅支持 `{CONTENT_DETAIL_BY_URL}`",
        )
    if not isinstance(target.target_value, str) or not target.target_value:
        return None, runtime_contract_error("invalid_task_request", "target_value 不能为空")
    if not isinstance(target.target_type, str) or target.target_type not in ALLOWED_TARGET_TYPES:
        return None, runtime_contract_error("invalid_task_request", "target_type 不合法")
    if not isinstance(policy.collection_mode, str) or policy.collection_mode not in ALLOWED_COLLECTION_MODES:
        return None, runtime_contract_error("invalid_task_request", "collection_mode 不合法")
    return request, None


def project_to_adapter_request(request: CoreTaskRequest) -> tuple[TaskRequest | None, dict[str, Any] | None]:
    if request.target.target_type != "url":
        return (
            None,
            runtime_contract_error(
                "invalid_task_request",
                "当前运行时过渡路径仅支持 target_type=url",
            ),
        )
    return (
        TaskRequest(
        adapter_key=request.target.adapter_key,
        capability=request.target.capability,
        input=TaskInput(url=request.target.target_value),
        ),
        None,
    )


def extract_request_context(request: Any) -> tuple[str, str]:
    adapter_key: Any = ""
    capability: Any = ""
    if isinstance(request, Mapping):
        try:
            adapter_key = request.get("adapter_key")
        except Exception:
            adapter_key = ""
        try:
            capability = request.get("capability")
        except Exception:
            capability = ""
        if not isinstance(adapter_key, str) or not adapter_key:
            try:
                target = request.get("target")
            except Exception:
                target = None
            if isinstance(target, Mapping):
                try:
                    adapter_key = target.get("adapter_key", "")
                except Exception:
                    adapter_key = ""
                try:
                    capability = target.get("capability", capability)
                except Exception:
                    capability = capability
    else:
        try:
            adapter_key = getattr(request, "adapter_key", "")
        except Exception:
            adapter_key = ""
        try:
            capability = getattr(request, "capability", "")
        except Exception:
            capability = ""
        if (not isinstance(adapter_key, str) or not adapter_key) or (not isinstance(capability, str) or not capability):
            try:
                target = getattr(request, "target", None)
            except Exception:
                target = None
            if target is not None:
                try:
                    adapter_key = getattr(target, "adapter_key", adapter_key)
                except Exception:
                    adapter_key = adapter_key
                try:
                    capability = getattr(target, "capability", capability)
                except Exception:
                    capability = capability
    safe_adapter_key = adapter_key if isinstance(adapter_key, str) else ""
    safe_capability = capability if isinstance(capability, str) else ""
    return safe_adapter_key, safe_capability


def get_adapter(adapters: Mapping[str, Any], adapter_key: str) -> tuple[Any, dict[str, Any] | None]:
    try:
        getter = getattr(adapters, "get")
    except Exception as error:
        return None, runtime_contract_error(
            "invalid_adapter_registry",
            "adapters 必须是支持 get() 的映射对象",
            details={"error_type": error.__class__.__name__},
        )
    if not callable(getter):
        return None, runtime_contract_error(
            "invalid_adapter_registry",
            "adapters 必须是支持 get() 的映射对象",
        )
    try:
        return getter(adapter_key), None
    except Exception as error:
        return None, runtime_contract_error(
            "invalid_adapter_registry",
            "adapters.get() 执行失败",
            details={"error_type": error.__class__.__name__},
        )


def get_adapter_supported_capabilities(adapter: Any) -> Any:
    try:
        return getattr(adapter, "supported_capabilities")
    except AttributeError:
        return MISSING
    except Exception:
        return MISSING


def validate_supported_capabilities(raw_capabilities: Any) -> tuple[frozenset[str], dict[str, Any] | None]:
    if raw_capabilities is MISSING:
        return frozenset(), runtime_contract_error(
            "invalid_adapter_capabilities",
            "supported_capabilities 必须为字符串集合",
            details={"reason": "missing"},
        )
    if raw_capabilities is None:
        return frozenset(), runtime_contract_error(
            "invalid_adapter_capabilities",
            "supported_capabilities 必须为字符串集合",
            details={"actual_type": "NoneType"},
        )
    if isinstance(raw_capabilities, (str, bytes)):
        return frozenset(), runtime_contract_error(
            "invalid_adapter_capabilities",
            "supported_capabilities 必须为字符串集合",
            details={"actual_type": type(raw_capabilities).__name__},
        )
    try:
        iterator = iter(raw_capabilities)
    except TypeError:
        return frozenset(), runtime_contract_error(
            "invalid_adapter_capabilities",
            "supported_capabilities 必须为字符串集合",
            details={"actual_type": type(raw_capabilities).__name__},
        )
    validated: list[str] = []
    try:
        for value in iterator:
            if not isinstance(value, str):
                return frozenset(), runtime_contract_error(
                    "invalid_adapter_capabilities",
                    "supported_capabilities 必须为字符串集合",
                    details={"invalid_value_type": type(value).__name__},
                )
            validated.append(value)
    except Exception as error:
        return frozenset(), runtime_contract_error(
            "invalid_adapter_capabilities",
            "supported_capabilities 必须为字符串集合",
            details={"error_type": error.__class__.__name__},
        )
    return frozenset(validated), None


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
    return parsed.tzinfo is not None and parsed.utcoffset() == timedelta(0)


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
