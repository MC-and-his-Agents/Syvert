from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import re
from typing import Any, Callable, Mapping
from uuid import uuid4

from syvert.registry import AdapterRegistry, RegistryError
from syvert.task_record import (
    TaskRecord,
    TaskRecordContractError,
    build_task_request_snapshot,
    create_task_record,
    finish_task_record,
    start_task_record,
)
from syvert.task_record_store import TaskRecordStore, TaskRecordStoreError, default_task_record_store

CONTENT_DETAIL_BY_URL = "content_detail_by_url"
CONTENT_DETAIL = "content_detail"
LEGACY_COLLECTION_MODE = "hybrid"
ALLOWED_TARGET_TYPES = frozenset({"url", "content_id", "creator_id", "keyword"})
ALLOWED_COLLECTION_MODES = frozenset({"public", "authenticated", "hybrid"})
CAPABILITY_FAMILY_BY_OPERATION = {CONTENT_DETAIL_BY_URL: CONTENT_DETAIL}
ALLOWED_CONTENT_TYPES = {"video", "image_post", "mixed_media", "unknown"}
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")


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


@dataclass(frozen=True)
class AdapterTaskRequest:
    capability: str
    target_type: str
    target_value: str
    collection_mode: str

    @property
    def input(self) -> TaskInput:
        return TaskInput(url=self.target_value)


@dataclass
class PlatformAdapterError(Exception):
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    category: str = "platform"

    def __post_init__(self) -> None:
        super().__init__(self.message)


def default_task_id_factory() -> str:
    return f"task-{uuid4().hex}"


@dataclass(frozen=True)
class TaskExecutionResult:
    envelope: dict[str, Any]
    task_record: TaskRecord | None


def execute_task(
    request: TaskRequest | CoreTaskRequest,
    *,
    adapters: Mapping[str, Any],
    task_id_factory: Callable[[], str] | None = None,
) -> dict[str, Any]:
    return execute_task_internal(
        request,
        adapters=adapters,
        task_id_factory=task_id_factory,
        preserve_envelope_on_record_error=True,
    ).envelope


def execute_task_with_record(
    request: TaskRequest | CoreTaskRequest,
    *,
    adapters: Mapping[str, Any],
    task_id_factory: Callable[[], str] | None = None,
    task_record_store: TaskRecordStore | None = None,
) -> TaskExecutionResult:
    store = task_record_store if task_record_store is not None else default_task_record_store()
    return execute_task_internal(
        request,
        adapters=adapters,
        task_id_factory=task_id_factory,
        preserve_envelope_on_record_error=False,
        task_record_store=store,
    )


def execute_task_internal(
    request: TaskRequest | CoreTaskRequest,
    *,
    adapters: Mapping[str, Any],
    task_id_factory: Callable[[], str] | None = None,
    preserve_envelope_on_record_error: bool,
    task_record_store: TaskRecordStore | None = None,
) -> TaskExecutionResult:
    store = task_record_store
    adapter_key, capability = extract_request_context(request)
    task_id, task_id_error = resolve_task_id(task_id_factory)
    if task_id_error is not None:
        return TaskExecutionResult(failure_envelope(task_id, adapter_key, capability, task_id_error), None)

    normalized_request, contract_error = normalize_request(request)
    if contract_error is not None:
        return TaskExecutionResult(failure_envelope(task_id, adapter_key, capability, contract_error), None)
    if normalized_request is None:
        return TaskExecutionResult(
            failure_envelope(
                task_id,
                adapter_key,
                capability,
                invalid_input_error("invalid_task_request", "task_request 顶层形状不合法"),
            ),
            None,
        )

    adapter_key = normalized_request.target.adapter_key
    capability = normalized_request.target.capability
    capability_family, capability_family_error = resolve_capability_family(capability)
    if capability_family_error is not None:
        return TaskExecutionResult(failure_envelope(task_id, adapter_key, capability, capability_family_error), None)
    if capability_family is None:
        return TaskExecutionResult(
            failure_envelope(
                task_id,
                adapter_key,
                capability,
                invalid_input_error("invalid_capability", "capability 无法投影到 adapter-facing family"),
            ),
            None,
        )

    projection_axis_error = validate_projection_axes_for_current_runtime(normalized_request)
    if projection_axis_error is not None:
        return TaskExecutionResult(failure_envelope(task_id, adapter_key, capability, projection_axis_error), None)

    try:
        registry = AdapterRegistry.from_mapping(adapters)
    except RegistryError as error:
        return TaskExecutionResult(
            failure_envelope(
                task_id,
                adapter_key,
                capability,
                runtime_contract_error(
                    error.code,
                    error.message,
                    details=error.details,
                ),
            ),
            None,
        )

    declaration = registry.lookup(adapter_key)
    if declaration is None:
        return TaskExecutionResult(
            failure_envelope(
                task_id,
                adapter_key,
                capability,
                unsupported_error("adapter_not_found", f"adapter `{adapter_key}` 不存在"),
            ),
            None,
        )

    supported_capabilities = declaration.supported_capabilities
    if capability_family not in supported_capabilities:
        return TaskExecutionResult(
            failure_envelope(
                task_id,
                adapter_key,
                capability,
                unsupported_error(
                    "capability_not_supported",
                    f"adapter `{adapter_key}` 不支持 `{capability_family}`",
                    details={
                        "supported_capabilities": sorted(supported_capabilities),
                        "capability_family": capability_family,
                    },
                ),
            ),
            None,
        )

    supported_targets = declaration.supported_targets
    if normalized_request.target.target_type not in supported_targets:
        return TaskExecutionResult(
            failure_envelope(
                task_id,
                adapter_key,
                capability,
                invalid_input_error(
                    "target_type_not_supported",
                    f"adapter `{adapter_key}` 不支持 target_type `{normalized_request.target.target_type}`",
                    details={"supported_targets": sorted(supported_targets)},
                ),
            ),
            None,
        )

    supported_collection_modes = declaration.supported_collection_modes
    if normalized_request.policy.collection_mode not in supported_collection_modes:
        return TaskExecutionResult(
            failure_envelope(
                task_id,
                adapter_key,
                capability,
                invalid_input_error(
                    "collection_mode_not_supported",
                    f"adapter `{adapter_key}` 不支持 collection_mode `{normalized_request.policy.collection_mode}`",
                    details={"supported_collection_modes": sorted(supported_collection_modes)},
                ),
            ),
            None,
        )

    adapter_request, projection_error = project_to_adapter_request(normalized_request, capability_family)
    if projection_error is not None:
        return TaskExecutionResult(failure_envelope(task_id, adapter_key, capability, projection_error), None)

    try:
        record = create_task_record(task_id, build_task_request_snapshot(normalized_request))
    except TaskRecordContractError as error:
        return TaskExecutionResult(
            failure_envelope(
                task_id,
                adapter_key,
                capability,
                runtime_contract_error("invalid_task_record", str(error)),
            ),
            None,
        )
    persisted_record, persistence_error = persist_task_record(
        task_id,
        adapter_key,
        capability,
        record,
        stage="accepted",
        task_record_store=store,
    )
    if persistence_error is not None:
        return persistence_error
    if persisted_record is not None:
        record = persisted_record

    try:
        payload = declaration.adapter.execute(adapter_request)
        payload_error = validate_success_payload(payload)
        if payload_error is not None:
            envelope = failure_envelope(task_id, adapter_key, capability, payload_error)
            return finalize_task_execution_result(
                task_id,
                adapter_key,
                capability,
                record,
                envelope,
                preserve_envelope_on_record_error=preserve_envelope_on_record_error,
                task_record_store=store,
            )
    except PlatformAdapterError as error:
        envelope = failure_envelope(task_id, adapter_key, capability, classify_adapter_error(error))
        return finalize_task_execution_result(
            task_id,
            adapter_key,
            capability,
            record,
            envelope,
            preserve_envelope_on_record_error=preserve_envelope_on_record_error,
            task_record_store=store,
        )
    except Exception as error:
        envelope = failure_envelope(
            task_id,
            adapter_key,
            capability,
            runtime_contract_error(
                "adapter_execution_error",
                str(error) or error.__class__.__name__,
            ),
        )
        return finalize_task_execution_result(
            task_id,
            adapter_key,
            capability,
            record,
            envelope,
            preserve_envelope_on_record_error=preserve_envelope_on_record_error,
            task_record_store=store,
        )

    envelope = {
        "task_id": task_id,
        "adapter_key": adapter_key,
        "capability": capability,
        "status": "success",
        "raw": payload["raw"],
        "normalized": payload["normalized"],
    }
    return finalize_task_execution_result(
        task_id,
        adapter_key,
        capability,
        record,
        envelope,
        preserve_envelope_on_record_error=preserve_envelope_on_record_error,
        task_record_store=store,
    )


def finalize_task_execution_result(
    task_id: str,
    adapter_key: str,
    capability: str,
    record: TaskRecord,
    envelope: Mapping[str, Any],
    *,
    preserve_envelope_on_record_error: bool,
    task_record_store: TaskRecordStore | None,
) -> TaskExecutionResult:
    active_record = record
    if record.status == "accepted":
        try:
            active_record = start_task_record(record)
        except TaskRecordContractError as error:
            invalidation_details: dict[str, Any] = {}
            try:
                task_record_store.mark_invalid(task_id, stage="running", reason=str(error))
            except (AttributeError, TaskRecordStoreError, OSError) as invalidation_error:
                invalidation_details["invalidation_reason"] = str(invalidation_error)
            if preserve_envelope_on_record_error and task_record_store is None:
                return TaskExecutionResult(dict(envelope), None)
            return TaskExecutionResult(
                failure_envelope(
                    task_id,
                    adapter_key,
                    capability,
                    runtime_contract_error(
                        "invalid_task_record",
                        str(error),
                        details=invalidation_details,
                    ),
                ),
                None,
            )
        persisted_record, persistence_error = persist_task_record(
            task_id,
            adapter_key,
            capability,
            active_record,
            stage="running",
            task_record_store=task_record_store,
        )
        if persistence_error is not None:
            return persistence_error
        if persisted_record is not None:
            active_record = persisted_record
    try:
        terminal_record = finish_task_record(active_record, envelope)
    except TaskRecordContractError as error:
        invalidation_details: dict[str, Any] = {}
        try:
            task_record_store.mark_invalid(task_id, stage="completion", reason=str(error))
        except (AttributeError, TaskRecordStoreError, OSError) as invalidation_error:
            invalidation_details["invalidation_reason"] = str(invalidation_error)
        if preserve_envelope_on_record_error and task_record_store is None:
            return TaskExecutionResult(dict(envelope), None)
        return TaskExecutionResult(
            failure_envelope(
                task_id,
                adapter_key,
                capability,
                runtime_contract_error(
                    "envelope_not_json_serializable",
                    "共享终态结果无法收口为 JSON-safe TaskRecord",
                    details={"reason": str(error), **invalidation_details},
                ),
            ),
            None,
        )
    persisted_record, persistence_error = persist_task_record(
        task_id,
        adapter_key,
        capability,
        terminal_record,
        stage="completion",
        task_record_store=task_record_store,
    )
    if persistence_error is not None:
        return persistence_error
    return TaskExecutionResult(dict(envelope), persisted_record or terminal_record)


def persist_task_record(
    task_id: str,
    adapter_key: str,
    capability: str,
    record: TaskRecord,
    *,
    stage: str,
    task_record_store: TaskRecordStore | None,
) -> tuple[TaskRecord | None, TaskExecutionResult | None]:
    if task_record_store is None:
        return record, None
    try:
        return task_record_store.write(record), None
    except (TaskRecordStoreError, OSError) as error:
        invalidation_details: dict[str, Any] = {}
        try:
            task_record_store.mark_invalid(task_id, stage=stage, reason=str(error))
        except (AttributeError, TaskRecordStoreError, OSError) as invalidation_error:
            invalidation_details["invalidation_reason"] = str(invalidation_error)
        return None, TaskExecutionResult(
            failure_envelope(
                task_id,
                adapter_key,
                capability,
                runtime_contract_error(
                    "task_record_persistence_failed",
                    "共享任务记录无法可靠写入本地稳定存储",
                    details={"stage": stage, "reason": str(error), **invalidation_details},
                ),
            ),
            None,
        )


def validate_request(request: Any) -> dict[str, Any] | None:
    _, error = normalize_request(request)
    return error


def normalize_request(request: Any) -> tuple[CoreTaskRequest | None, dict[str, Any] | None]:
    if type(request) is TaskRequest:
        if not isinstance(request.adapter_key, str) or not request.adapter_key:
            return None, invalid_input_error("invalid_task_request", "adapter_key 不能为空")
        if request.capability != CONTENT_DETAIL_BY_URL:
            return None, invalid_input_error(
                "invalid_capability",
                f"v0.1.0 仅支持 `{CONTENT_DETAIL_BY_URL}`",
            )
        if type(request.input) is not TaskInput:
            return None, invalid_input_error("invalid_task_request", "input 必须为对象")
        if not isinstance(request.input.url, str) or not request.input.url:
            return None, invalid_input_error("invalid_task_request", "input.url 不能为空")
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
        return None, invalid_input_error("invalid_task_request", "task_request 顶层形状不合法")
    if type(request.target) is not InputTarget:
        return None, invalid_input_error("invalid_task_request", "target 必须为对象")
    if type(request.policy) is not CollectionPolicy:
        return None, invalid_input_error("invalid_task_request", "policy 必须为对象")

    target = request.target
    policy = request.policy
    if not isinstance(target.adapter_key, str) or not target.adapter_key:
        return None, invalid_input_error("invalid_task_request", "adapter_key 不能为空")
    if target.capability != CONTENT_DETAIL_BY_URL:
        return None, invalid_input_error(
            "invalid_capability",
            f"v0.1.0 仅支持 `{CONTENT_DETAIL_BY_URL}`",
        )
    if not isinstance(target.target_value, str) or not target.target_value:
        return None, invalid_input_error("invalid_task_request", "target_value 不能为空")
    if not isinstance(target.target_type, str) or target.target_type not in ALLOWED_TARGET_TYPES:
        return None, invalid_input_error("invalid_task_request", "target_type 不合法")
    if not isinstance(policy.collection_mode, str) or policy.collection_mode not in ALLOWED_COLLECTION_MODES:
        return None, invalid_input_error("invalid_task_request", "collection_mode 不合法")
    return request, None


def resolve_capability_family(capability: str) -> tuple[str | None, dict[str, Any] | None]:
    mapped = CAPABILITY_FAMILY_BY_OPERATION.get(capability)
    if mapped is None:
        return (
            None,
            invalid_input_error(
                "invalid_capability",
                f"v0.1.0 仅支持 `{CONTENT_DETAIL_BY_URL}`",
            ),
        )
    return mapped, None


def project_to_adapter_request(
    request: CoreTaskRequest,
    capability_family: str,
) -> tuple[AdapterTaskRequest | None, dict[str, Any] | None]:
    return (
        AdapterTaskRequest(
            capability=capability_family,
            target_type=request.target.target_type,
            target_value=request.target.target_value,
            collection_mode=request.policy.collection_mode,
        ),
        None,
    )


def validate_projection_axes_for_current_runtime(request: CoreTaskRequest) -> dict[str, Any] | None:
    if request.target.target_type != "url":
        return invalid_input_error(
            "invalid_task_request",
            "当前运行时执行路径仅支持 target_type=url",
        )
    if request.policy.collection_mode != LEGACY_COLLECTION_MODE:
        return invalid_input_error(
            "invalid_task_request",
            "当前运行时执行路径仅支持 collection_mode=hybrid",
        )
    return None


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


def classify_adapter_error(error: PlatformAdapterError) -> dict[str, Any]:
    details = error.details if isinstance(error.details, Mapping) else {}
    if error.category == "invalid_input":
        return invalid_input_error(error.code, error.message, details=details)
    return {
        "category": "platform",
        "code": error.code,
        "message": error.message,
        "details": dict(details),
    }


def invalid_input_error(code: str, message: str, *, details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        "category": "invalid_input",
        "code": code,
        "message": message,
        "details": dict(details or {}),
    }


def unsupported_error(code: str, message: str, *, details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        "category": "unsupported",
        "code": code,
        "message": message,
        "details": dict(details or {}),
    }
