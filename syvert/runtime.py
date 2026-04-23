from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import re
from typing import TYPE_CHECKING, Any, Callable, Mapping
from uuid import uuid4

from syvert.registry import (
    AdapterRegistry,
    AdapterResourceRequirementDeclaration,
    RegistryError,
    RESOURCE_DEPENDENCY_MODE_NONE,
    approved_resource_requirement_evidence_refs,
)
from syvert.resource_capability_evidence import approved_resource_capability_ids
from syvert.task_record import (
    TaskRecord,
    TaskRecordContractError,
    build_task_request_snapshot,
    create_task_record,
    finish_task_record,
    start_task_record,
)
from syvert.task_record_store import (
    TaskRecordConflictError,
    TaskRecordStore,
    TaskRecordStoreError,
    default_task_record_store,
)

CONTENT_DETAIL_BY_URL = "content_detail_by_url"
CONTENT_DETAIL = "content_detail"
LEGACY_COLLECTION_MODE = "hybrid"
ALLOWED_TARGET_TYPES = frozenset({"url", "content_id", "creator_id", "keyword"})
ALLOWED_COLLECTION_MODES = frozenset({"public", "authenticated", "hybrid"})
CAPABILITY_FAMILY_BY_OPERATION = {CONTENT_DETAIL_BY_URL: CONTENT_DETAIL}
ALLOWED_CONTENT_TYPES = {"video", "image_post", "mixed_media", "unknown"}
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE = {
    (CONTENT_DETAIL_BY_URL, LEGACY_COLLECTION_MODE): ("account", "proxy"),
}
DEFAULT_BUNDLE_VALIDATION_RELEASE_REASON = "host_side_bundle_validation_failed"
DEFAULT_SUCCESS_RELEASE_REASON = "adapter_completed_without_disposition_hint"
DEFAULT_FAILURE_RELEASE_REASON = "adapter_failed_without_disposition_hint"
DEFAULT_INVALID_HINT_RELEASE_REASON = "invalid_resource_disposition_hint"
MATCH_STATUS_MATCHED = "matched"
MATCH_STATUS_UNMATCHED = "unmatched"
_ALLOWED_MATCH_STATUSES = frozenset({MATCH_STATUS_MATCHED, MATCH_STATUS_UNMATCHED})
_ALLOWED_MATCHER_CAPABILITIES = frozenset({CONTENT_DETAIL})
_APPROVED_RESOURCE_CAPABILITY_IDS = approved_resource_capability_ids()
_APPROVED_RESOURCE_REQUIREMENT_EVIDENCE_REFS = approved_resource_requirement_evidence_refs()

if TYPE_CHECKING:
    from syvert.resource_lifecycle import ResourceBundle
    from syvert.resource_lifecycle_store import LocalResourceLifecycleStore
    from syvert.resource_trace_store import LocalResourceTraceStore


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


@dataclass(frozen=True)
class ResourceDispositionHint:
    lease_id: str
    target_status_after_release: str
    reason: str


@dataclass(frozen=True)
class AdapterExecutionContext:
    request: AdapterTaskRequest
    resource_bundle: "ResourceBundle | None"

    @property
    def capability(self) -> str:
        return self.request.capability

    @property
    def target_type(self) -> str:
        return self.request.target_type

    @property
    def target_value(self) -> str:
        return self.request.target_value

    @property
    def collection_mode(self) -> str:
        return self.request.collection_mode

    @property
    def input(self) -> TaskInput:
        return self.request.input


@dataclass
class PlatformAdapterError(Exception):
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    category: str = "platform"
    resource_disposition_hint: ResourceDispositionHint | Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        super().__init__(self.message)


def default_task_id_factory() -> str:
    return f"task-{uuid4().hex}"


@dataclass(frozen=True)
class TaskExecutionResult:
    envelope: dict[str, Any]
    task_record: TaskRecord | None


@dataclass(frozen=True)
class ResourceCapabilityMatcherInput:
    task_id: str
    adapter_key: str
    capability: str
    requirement_declaration: AdapterResourceRequirementDeclaration
    available_resource_capabilities: tuple[str, ...]


@dataclass(frozen=True)
class ResourceCapabilityMatchResult:
    task_id: str
    adapter_key: str
    capability: str
    match_status: str


class ResourceCapabilityMatcherContractError(Exception):
    def __init__(self, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = "invalid_resource_requirement"
        self.message = message
        self.details = dict(details or {})


def execute_task(
    request: TaskRequest | CoreTaskRequest,
    *,
    adapters: Mapping[str, Any],
    task_id_factory: Callable[[], str] | None = None,
    resource_lifecycle_store: "LocalResourceLifecycleStore | None" = None,
    resource_trace_store: "LocalResourceTraceStore | None" = None,
) -> dict[str, Any]:
    return execute_task_internal(
        request,
        adapters=adapters,
        task_id_factory=task_id_factory,
        preserve_envelope_on_record_error=True,
        resource_lifecycle_store=resource_lifecycle_store,
        resource_trace_store=resource_trace_store,
    ).envelope


def execute_task_with_record(
    request: TaskRequest | CoreTaskRequest,
    *,
    adapters: Mapping[str, Any],
    task_id_factory: Callable[[], str] | None = None,
    task_record_store: TaskRecordStore | None = None,
    resource_lifecycle_store: "LocalResourceLifecycleStore | None" = None,
    resource_trace_store: "LocalResourceTraceStore | None" = None,
) -> TaskExecutionResult:
    store = task_record_store if task_record_store is not None else default_task_record_store()
    return execute_task_internal(
        request,
        adapters=adapters,
        task_id_factory=task_id_factory,
        preserve_envelope_on_record_error=False,
        task_record_store=store,
        resource_lifecycle_store=resource_lifecycle_store,
        resource_trace_store=resource_trace_store,
    )


def execute_task_internal(
    request: TaskRequest | CoreTaskRequest,
    *,
    adapters: Mapping[str, Any],
    task_id_factory: Callable[[], str] | None = None,
    preserve_envelope_on_record_error: bool,
    task_record_store: TaskRecordStore | None = None,
    resource_lifecycle_store: "LocalResourceLifecycleStore | None" = None,
    resource_trace_store: "LocalResourceTraceStore | None" = None,
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
        if error.code == "invalid_adapter_resource_requirements":
            # Runtime only admits declarations that registry can materialize.
            # Pure matcher-only `none` semantics stay unreachable here until FR-0013
            # freezes a canonical runtime declaration baseline for that mode.
            return TaskExecutionResult(
                failure_envelope(
                    task_id,
                    adapter_key,
                    capability,
                    invalid_resource_requirement_error(
                        error.message,
                        details={
                            "registry_error_code": error.code,
                            **error.details,
                        },
                    ),
                ),
                None,
            )
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

    adapter_declaration = registry.lookup(adapter_key)
    if adapter_declaration is None:
        return TaskExecutionResult(
            failure_envelope(
                task_id,
                adapter_key,
                capability,
                unsupported_error("adapter_not_found", f"adapter `{adapter_key}` 不存在"),
            ),
            None,
        )

    supported_capabilities = adapter_declaration.supported_capabilities
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

    supported_targets = adapter_declaration.supported_targets
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

    supported_collection_modes = adapter_declaration.supported_collection_modes
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

    resource_requirement_declaration = registry.lookup_resource_requirement(adapter_key, capability_family)
    if resource_requirement_declaration is None:
        return TaskExecutionResult(
            failure_envelope(
                task_id,
                adapter_key,
                capability,
                invalid_resource_requirement_error(
                    f"adapter `{adapter_key}` 缺少 `{capability_family}` 的资源需求声明",
                    details={"adapter_key": adapter_key, "capability": capability_family},
                ),
            ),
            None,
        )

    try:
        available_resource_capabilities = resolve_runtime_available_resource_capabilities(normalized_request)
        matcher_input = validate_resource_capability_matcher_input(
            ResourceCapabilityMatcherInput(
                task_id=task_id,
                adapter_key=adapter_key,
                capability=capability_family,
                requirement_declaration=resource_requirement_declaration,
                available_resource_capabilities=available_resource_capabilities,
            )
        )
    except ResourceCapabilityMatcherContractError as error:
        return TaskExecutionResult(
            failure_envelope(
                task_id,
                adapter_key,
                capability,
                invalid_resource_requirement_error(error.message, details=error.details),
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
        record = start_task_record(record)
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
        stage="running",
        task_record_store=store,
    )
    if persistence_error is not None:
        return persistence_error
    if persisted_record is not None:
        record = persisted_record

    match_result = match_resource_capabilities(matcher_input)
    if match_result.match_status == MATCH_STATUS_UNMATCHED:
        return finalize_task_execution_result(
            task_id,
            adapter_key,
            capability,
            record,
            failure_envelope(
                task_id,
                adapter_key,
                capability,
                resource_unavailable_error(
                    f"adapter `{adapter_key}` 的资源能力声明与当前 runtime 能力集合不匹配",
                    details={
                        "adapter_key": adapter_key,
                        "capability": capability_family,
                        "match_status": match_result.match_status,
                        "required_capabilities": list(matcher_input.requirement_declaration.required_capabilities),
                        "available_resource_capabilities": list(matcher_input.available_resource_capabilities),
                    },
                ),
            ),
            preserve_envelope_on_record_error=preserve_envelope_on_record_error,
            task_record_store=store,
        )

    requested_slots = resolve_requested_resource_slots(normalized_request)
    managed_resource_store = None
    managed_trace_store = None
    resource_bundle = None
    if requested_slots is not None:
        managed_resource_store = resource_lifecycle_store or default_runtime_resource_lifecycle_store()
        managed_trace_store = resource_trace_store or default_runtime_resource_trace_store(managed_resource_store)
        acquire_result = acquire_runtime_resource_bundle(
            task_id=task_id,
            adapter_key=adapter_key,
            capability=capability,
            requested_slots=requested_slots,
            resource_lifecycle_store=managed_resource_store,
            resource_trace_store=managed_trace_store,
        )
        if isinstance(acquire_result, Mapping):
            return finalize_task_execution_result(
                task_id,
                adapter_key,
                capability,
                record,
                dict(acquire_result),
                preserve_envelope_on_record_error=preserve_envelope_on_record_error,
                task_record_store=store,
            )
        resource_bundle = acquire_result
        live_resource_lease, live_resources_by_id, live_lease_error = resolve_host_resource_lease(
            task_id=task_id,
            adapter_key=adapter_key,
            capability=capability,
            resource_lifecycle_store=managed_resource_store,
        )
        if live_lease_error is not None:
            cleanup_envelope = settle_managed_resource_bundle(
                lease_id=resource_bundle.lease_id,
                task_id=task_id,
                resource_lifecycle_store=managed_resource_store,
                resource_trace_store=managed_trace_store,
                default_reason=DEFAULT_BUNDLE_VALIDATION_RELEASE_REASON,
                hint=None,
            )
            envelope = cleanup_envelope or failure_envelope(task_id, adapter_key, capability, live_lease_error)
            return finalize_task_execution_result(
                task_id,
                adapter_key,
                capability,
                record,
                envelope,
                preserve_envelope_on_record_error=preserve_envelope_on_record_error,
                task_record_store=store,
            )

        bundle_error = validate_host_resource_bundle(
            resource_bundle,
            task_id=task_id,
            adapter_key=adapter_key,
            capability=capability,
            requested_slots=requested_slots,
            live_resource_lease=live_resource_lease,
            live_resources_by_id=live_resources_by_id,
        )
        if bundle_error is not None:
            cleanup_envelope = settle_managed_resource_bundle(
                lease_id=live_resource_lease.lease_id,
                task_id=task_id,
                resource_lifecycle_store=managed_resource_store,
                resource_trace_store=managed_trace_store,
                default_reason=DEFAULT_BUNDLE_VALIDATION_RELEASE_REASON,
                hint=None,
            )
            envelope = cleanup_envelope or failure_envelope(task_id, adapter_key, capability, bundle_error)
            return finalize_task_execution_result(
                task_id,
                adapter_key,
                capability,
                record,
                envelope,
                preserve_envelope_on_record_error=preserve_envelope_on_record_error,
                task_record_store=store,
            )

    adapter_context = AdapterExecutionContext(
        request=adapter_request,
        resource_bundle=resource_bundle,
    )
    disposition_hint: ResourceDispositionHint | None = None
    default_release_reason = DEFAULT_SUCCESS_RELEASE_REASON
    try:
        payload = adapter_declaration.adapter.execute(adapter_context)
        payload_error = validate_success_payload(payload)
        if payload_error is not None:
            envelope = failure_envelope(task_id, adapter_key, capability, payload_error)
            default_release_reason = DEFAULT_FAILURE_RELEASE_REASON
        else:
            disposition_hint, hint_error = extract_internal_resource_disposition_hint(
                payload.get("resource_disposition_hint"),
                expected_lease_id=resource_bundle.lease_id if resource_bundle is not None else None,
            )
            if hint_error is not None:
                envelope = failure_envelope(task_id, adapter_key, capability, hint_error)
                default_release_reason = DEFAULT_INVALID_HINT_RELEASE_REASON
            else:
                envelope = {
                    "task_id": task_id,
                    "adapter_key": adapter_key,
                    "capability": capability,
                    "status": "success",
                    "raw": payload["raw"],
                    "normalized": payload["normalized"],
                }
    except PlatformAdapterError as error:
        disposition_hint, hint_error = extract_internal_resource_disposition_hint(
            error.resource_disposition_hint,
            expected_lease_id=resource_bundle.lease_id if resource_bundle is not None else None,
        )
        if hint_error is not None:
            envelope = failure_envelope(task_id, adapter_key, capability, hint_error)
            default_release_reason = DEFAULT_INVALID_HINT_RELEASE_REASON
        else:
            envelope = failure_envelope(task_id, adapter_key, capability, classify_adapter_error(error))
            default_release_reason = DEFAULT_FAILURE_RELEASE_REASON
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
        default_release_reason = DEFAULT_FAILURE_RELEASE_REASON

    if resource_bundle is not None and managed_resource_store is not None:
        cleanup_envelope = settle_managed_resource_bundle(
            lease_id=live_resource_lease.lease_id,
            task_id=task_id,
            resource_lifecycle_store=managed_resource_store,
            resource_trace_store=managed_trace_store,
            default_reason=default_release_reason,
            hint=disposition_hint,
        )
        if cleanup_envelope is not None:
            envelope = cleanup_envelope

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
    try:
        terminal_record = finish_task_record(record, envelope)
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
    except TaskRecordConflictError as error:
        return None, TaskExecutionResult(
            failure_envelope(
                task_id,
                adapter_key,
                capability,
                runtime_contract_error(
                    "task_record_conflict",
                    "共享任务记录写入与既有 durable truth 冲突",
                    details={"stage": stage, "reason": str(error)},
                ),
            ),
            None,
        )
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


def match_resource_capabilities(input_value: ResourceCapabilityMatcherInput) -> ResourceCapabilityMatchResult:
    validated_input = validate_resource_capability_matcher_input(input_value)
    required_capabilities = frozenset(validated_input.requirement_declaration.required_capabilities)
    available_resource_capabilities = frozenset(validated_input.available_resource_capabilities)
    if validated_input.requirement_declaration.resource_dependency_mode == RESOURCE_DEPENDENCY_MODE_NONE:
        match_status = MATCH_STATUS_MATCHED
    elif required_capabilities.issubset(available_resource_capabilities):
        match_status = MATCH_STATUS_MATCHED
    else:
        match_status = MATCH_STATUS_UNMATCHED
    return ResourceCapabilityMatchResult(
        task_id=validated_input.task_id,
        adapter_key=validated_input.adapter_key,
        capability=validated_input.capability,
        match_status=match_status,
    )


def validate_resource_capability_matcher_input(
    input_value: ResourceCapabilityMatcherInput,
) -> ResourceCapabilityMatcherInput:
    if type(input_value) is not ResourceCapabilityMatcherInput:
        raise ResourceCapabilityMatcherContractError(
            "matcher 输入必须为 ResourceCapabilityMatcherInput",
            details={"actual_type": type(input_value).__name__},
        )

    task_id = _require_matcher_non_empty_string(
        input_value.task_id,
        field_name="task_id",
        details={"field_name": "task_id"},
    )
    adapter_key = _require_matcher_non_empty_string(
        input_value.adapter_key,
        field_name="adapter_key",
        details={"task_id": task_id},
    )
    capability = _require_matcher_non_empty_string(
        input_value.capability,
        field_name="capability",
        details={"task_id": task_id, "adapter_key": adapter_key},
    )
    if capability not in _ALLOWED_MATCHER_CAPABILITIES:
        raise ResourceCapabilityMatcherContractError(
            "matcher capability 必须是当前已冻结的 adapter-facing capability",
            details={
                "task_id": task_id,
                "adapter_key": adapter_key,
                "capability": capability,
            },
        )

    requirement_declaration = _validate_matcher_requirement_declaration(
        input_value.requirement_declaration,
        expected_adapter_key=adapter_key,
        expected_capability=capability,
        task_id=task_id,
    )
    available_resource_capabilities = _normalize_available_resource_capabilities(
        input_value.available_resource_capabilities,
        task_id=task_id,
        adapter_key=adapter_key,
        capability=capability,
    )

    return ResourceCapabilityMatcherInput(
        task_id=task_id,
        adapter_key=adapter_key,
        capability=capability,
        requirement_declaration=requirement_declaration,
        available_resource_capabilities=available_resource_capabilities,
    )


def resolve_requested_resource_slots(request: CoreTaskRequest) -> tuple[str, ...] | None:
    slots = RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE.get(
        (request.target.capability, request.policy.collection_mode)
    )
    if slots is None:
        return None
    return tuple(slots)


def resolve_runtime_available_resource_capabilities(request: CoreTaskRequest) -> tuple[str, ...]:
    requested_slots = resolve_requested_resource_slots(request)
    raw_capabilities: tuple[str, ...] | Iterable[str]
    if requested_slots is None:
        raw_capabilities = ()
    else:
        raw_capabilities = requested_slots
    return _normalize_available_resource_capabilities(
        raw_capabilities,
        task_id="",
        adapter_key=request.target.adapter_key,
        capability=CAPABILITY_FAMILY_BY_OPERATION.get(request.target.capability, request.target.capability),
    )


def default_runtime_resource_lifecycle_store():
    from syvert.resource_lifecycle_store import default_resource_lifecycle_store

    return default_resource_lifecycle_store()


def default_runtime_resource_trace_store(resource_lifecycle_store=None):
    from pathlib import Path

    from syvert.resource_trace_store import LocalResourceTraceStore, default_resource_trace_store

    store_path = getattr(resource_lifecycle_store, "path", None)
    if isinstance(store_path, Path):
        return LocalResourceTraceStore(store_path.with_name("resource-trace-events.jsonl"))

    return default_resource_trace_store()


def acquire_runtime_resource_bundle(
    *,
    task_id: str,
    adapter_key: str,
    capability: str,
    requested_slots: tuple[str, ...],
    resource_lifecycle_store,
    resource_trace_store,
):
    from syvert.resource_lifecycle import AcquireRequest, acquire

    return acquire(
        AcquireRequest(
            task_id=task_id,
            adapter_key=adapter_key,
            capability=capability,
            requested_slots=requested_slots,
        ),
        resource_lifecycle_store,
        task_id,
        resource_trace_store,
    )


def validate_host_resource_bundle(
    resource_bundle,
    *,
    task_id: str,
    adapter_key: str,
    capability: str,
    requested_slots: tuple[str, ...],
    live_resource_lease,
    live_resources_by_id: Mapping[str, Any],
) -> dict[str, Any] | None:
    from syvert.resource_lifecycle import ResourceLifecycleContractError, validate_resource_bundle

    try:
        validate_resource_bundle(resource_bundle)
    except ResourceLifecycleContractError as error:
        return runtime_contract_error(
            "invalid_resource_bundle",
            "resource_bundle 不满足共享 contract",
            details={"reason": str(error)},
        )
    if resource_bundle.task_id != task_id:
        return runtime_contract_error(
            "invalid_resource_bundle",
            "resource_bundle.task_id 与当前 task 不一致",
        )
    if resource_bundle.adapter_key != adapter_key:
        return runtime_contract_error(
            "invalid_resource_bundle",
            "resource_bundle.adapter_key 与当前请求不一致",
        )
    if resource_bundle.capability != capability:
        return runtime_contract_error(
            "invalid_resource_bundle",
            "resource_bundle.capability 与当前请求不一致",
        )
    if tuple(resource_bundle.requested_slots) != tuple(requested_slots):
        return runtime_contract_error(
            "invalid_resource_bundle",
            "resource_bundle.requested_slots 与当前请求不一致",
        )
    if resource_bundle.acquired_at != live_resource_lease.acquired_at:
        return runtime_contract_error(
            "invalid_resource_bundle",
            "resource_bundle.acquired_at 与当前 active lease 不一致",
        )
    if resource_bundle.bundle_id != live_resource_lease.bundle_id:
        return runtime_contract_error(
            "invalid_resource_bundle",
            "resource_bundle.bundle_id 与当前 active lease 不一致",
        )
    if resource_bundle.lease_id != live_resource_lease.lease_id:
        return runtime_contract_error(
            "invalid_resource_bundle",
            "resource_bundle.lease_id 与当前 active lease 不一致",
        )
    bundle_resource_ids = tuple(
        getattr(resource_bundle, slot).resource_id
        for slot in requested_slots
        if getattr(resource_bundle, slot) is not None
    )
    if bundle_resource_ids != tuple(live_resource_lease.resource_ids):
        return runtime_contract_error(
            "invalid_resource_bundle",
            "resource_bundle slots 与当前 active lease 绑定资源不一致",
        )
    for slot in requested_slots:
        resource = getattr(resource_bundle, slot)
        if resource is None:
            continue
        live_resource = live_resources_by_id.get(resource.resource_id)
        if live_resource is None:
            return runtime_contract_error(
                "invalid_resource_bundle",
                "resource_bundle slot 绑定了 host-side truth 中不存在的资源",
            )
        if resource != live_resource:
            return runtime_contract_error(
                "invalid_resource_bundle",
                "resource_bundle slot 内容与 host-side resource truth 不一致",
            )
    return None


def extract_internal_resource_disposition_hint(
    raw_hint: ResourceDispositionHint | Mapping[str, Any] | None,
    *,
    expected_lease_id: str | None,
) -> tuple[ResourceDispositionHint | None, dict[str, Any] | None]:
    def invalid_hint_error(message: str) -> dict[str, Any]:
        return invalid_input_error("invalid_resource_disposition_hint", message)

    if raw_hint is None:
        return None, None
    if expected_lease_id is None:
        return (
            None,
            invalid_hint_error("非资源路径不得返回 resource_disposition_hint"),
        )
    if isinstance(raw_hint, ResourceDispositionHint):
        hint = raw_hint
    elif isinstance(raw_hint, Mapping):
        lease_id = raw_hint.get("lease_id")
        target_status_after_release = raw_hint.get("target_status_after_release")
        reason = raw_hint.get("reason")
        hint = ResourceDispositionHint(
            lease_id=lease_id if isinstance(lease_id, str) else "",
            target_status_after_release=target_status_after_release if isinstance(target_status_after_release, str) else "",
            reason=reason if isinstance(reason, str) else "",
        )
    else:
        return (
            None,
            invalid_hint_error("resource_disposition_hint 必须是对象"),
        )

    if not hint.lease_id:
        return None, invalid_hint_error("resource_disposition_hint.lease_id 不能为空")
    if hint.lease_id != expected_lease_id:
        return (
            None,
            invalid_hint_error("resource_disposition_hint.lease_id 与注入 bundle 不一致"),
        )
    if hint.target_status_after_release not in {"AVAILABLE", "INVALID"}:
        return (
            None,
            invalid_hint_error("resource_disposition_hint.target_status_after_release 不在允许值范围内"),
        )
    if not hint.reason:
        return None, invalid_hint_error("resource_disposition_hint.reason 不能为空")
    return hint, None


def resolve_host_resource_lease(
    *,
    task_id: str,
    adapter_key: str,
    capability: str,
    resource_lifecycle_store,
):
    from syvert.resource_lifecycle import ResourceLifecycleContractError, validate_snapshot

    try:
        snapshot = resource_lifecycle_store.load_snapshot()
        validate_snapshot(snapshot)
    except ResourceLifecycleContractError as error:
        return (
            None,
            {},
            runtime_contract_error(
                "invalid_resource_bundle",
                "host-side resource lifecycle truth 不满足共享 contract",
                details={"reason": str(error)},
            ),
        )

    candidates = [
        lease
        for lease in snapshot.leases
        if lease.released_at is None
        and lease.task_id == task_id
        and lease.adapter_key == adapter_key
        and lease.capability == capability
    ]
    if len(candidates) != 1:
        return (
            None,
            {},
            runtime_contract_error(
                "invalid_resource_bundle",
                "当前 task 缺少唯一 active lease truth",
                details={"active_lease_count": len(candidates)},
            ),
        )
    resources_by_id = {record.resource_id: record for record in snapshot.resources}
    return candidates[0], resources_by_id, None


def settle_managed_resource_bundle(
    *,
    lease_id: str,
    task_id: str,
    resource_lifecycle_store,
    resource_trace_store,
    default_reason: str,
    hint: ResourceDispositionHint | None,
) -> dict[str, Any] | None:
    from syvert.resource_lifecycle import ReleaseRequest, release

    release_result = release(
        ReleaseRequest(
            lease_id=lease_id,
            task_id=task_id,
            target_status_after_release=(
                hint.target_status_after_release if hint is not None else "AVAILABLE"
            ),
            reason=hint.reason if hint is not None else default_reason,
        ),
        resource_lifecycle_store,
        task_id,
        resource_trace_store,
    )
    if isinstance(release_result, Mapping):
        return dict(release_result)
    return None


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


def invalid_resource_requirement_error(message: str, *, details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return runtime_contract_error("invalid_resource_requirement", message, details=details)


def resource_unavailable_error(message: str, *, details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return runtime_contract_error("resource_unavailable", message, details=details)


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


def _require_matcher_non_empty_string(
    raw_value: Any,
    *,
    field_name: str,
    details: Mapping[str, Any] | None = None,
) -> str:
    if not isinstance(raw_value, str) or not raw_value:
        raise ResourceCapabilityMatcherContractError(
            f"matcher 输入字段 `{field_name}` 必须为非空字符串",
            details=details,
        )
    return raw_value


def _validate_matcher_requirement_declaration(
    raw_value: Any,
    *,
    expected_adapter_key: str,
    expected_capability: str,
    task_id: str,
) -> AdapterResourceRequirementDeclaration:
    if type(raw_value) is not AdapterResourceRequirementDeclaration:
        raise ResourceCapabilityMatcherContractError(
            "matcher requirement_declaration 必须是 AdapterResourceRequirementDeclaration",
            details={"task_id": task_id, "actual_type": type(raw_value).__name__},
        )

    adapter_key = _require_matcher_non_empty_string(
        raw_value.adapter_key,
        field_name="requirement_declaration.adapter_key",
        details={"task_id": task_id},
    )
    capability = _require_matcher_non_empty_string(
        raw_value.capability,
        field_name="requirement_declaration.capability",
        details={"task_id": task_id, "adapter_key": adapter_key},
    )
    if capability not in _ALLOWED_MATCHER_CAPABILITIES:
        raise ResourceCapabilityMatcherContractError(
            "matcher requirement_declaration.capability 未被批准",
            details={"task_id": task_id, "adapter_key": adapter_key, "capability": capability},
        )
    if adapter_key != expected_adapter_key or capability != expected_capability:
        raise ResourceCapabilityMatcherContractError(
            "matcher 输入上下文必须与 requirement_declaration 保持一致",
            details={
                "task_id": task_id,
                "expected_adapter_key": expected_adapter_key,
                "actual_adapter_key": adapter_key,
                "expected_capability": expected_capability,
                "actual_capability": capability,
            },
        )

    resource_dependency_mode = _require_matcher_non_empty_string(
        raw_value.resource_dependency_mode,
        field_name="requirement_declaration.resource_dependency_mode",
        details={"task_id": task_id, "adapter_key": adapter_key, "capability": capability},
    )
    if resource_dependency_mode == RESOURCE_DEPENDENCY_MODE_NONE:
        required_capabilities = _normalize_available_resource_capabilities(
            raw_value.required_capabilities,
            task_id=task_id,
            adapter_key=adapter_key,
            capability=capability,
            field_name="requirement_declaration.required_capabilities",
        )
        if required_capabilities:
            raise ResourceCapabilityMatcherContractError(
                "matcher requirement_declaration 在 none 模式下不得声明 required_capabilities",
                details={"task_id": task_id, "adapter_key": adapter_key, "capability": capability},
            )
        evidence_refs = _normalize_non_empty_string_tuple(
            raw_value.evidence_refs,
            task_id=task_id,
            adapter_key=adapter_key,
            capability=capability,
            field_name="requirement_declaration.evidence_refs",
            allow_empty=False,
        )
        unknown_evidence_refs = tuple(
            evidence_ref
            for evidence_ref in evidence_refs
            if evidence_ref not in _APPROVED_RESOURCE_REQUIREMENT_EVIDENCE_REFS
        )
        if unknown_evidence_refs:
            raise ResourceCapabilityMatcherContractError(
                "matcher requirement_declaration.evidence_refs 必须绑定到 FR-0015 已批准共享证据",
                details={
                    "task_id": task_id,
                    "adapter_key": adapter_key,
                    "capability": capability,
                    "unknown_evidence_refs": unknown_evidence_refs,
                },
            )
        return AdapterResourceRequirementDeclaration(
            adapter_key=adapter_key,
            capability=capability,
            resource_dependency_mode=resource_dependency_mode,
            required_capabilities=required_capabilities,
            evidence_refs=evidence_refs,
        )

    try:
        registry = AdapterRegistry.from_mapping(
            {
                expected_adapter_key: _MatcherRequirementValidationAdapter(
                    supported_capability=expected_capability,
                    requirement_declaration=raw_value,
                )
            }
        )
    except RegistryError as error:
        raise ResourceCapabilityMatcherContractError(
            "matcher requirement_declaration 必须满足 FR-0013 canonical contract",
            details={
                "task_id": task_id,
                "adapter_key": expected_adapter_key,
                "capability": expected_capability,
                "registry_error_code": error.code,
                **error.details,
            },
        ) from error

    validated_requirement = registry.lookup_resource_requirement(expected_adapter_key, expected_capability)
    if validated_requirement is None:
        raise ResourceCapabilityMatcherContractError(
            "matcher requirement_declaration 必须与当前 adapter/capability 上下文对齐",
            details={
                "task_id": task_id,
                "adapter_key": expected_adapter_key,
                "capability": expected_capability,
            },
        )
    return validated_requirement


def _normalize_available_resource_capabilities(
    raw_values: Any,
    *,
    task_id: str,
    adapter_key: str,
    capability: str,
    field_name: str = "available_resource_capabilities",
) -> tuple[str, ...]:
    capabilities = _normalize_non_empty_string_tuple(
        raw_values,
        task_id=task_id,
        adapter_key=adapter_key,
        capability=capability,
        field_name=field_name,
        allow_empty=True,
    )
    unknown_capabilities = tuple(
        value for value in capabilities if value not in _APPROVED_RESOURCE_CAPABILITY_IDS
    )
    if unknown_capabilities:
        raise ResourceCapabilityMatcherContractError(
            f"matcher `{field_name}` 只能使用 FR-0015 已批准的 resource capability ids",
            details={
                "task_id": task_id,
                "adapter_key": adapter_key,
                "capability": capability,
                "unknown_capabilities": unknown_capabilities,
            },
        )
    return capabilities


def _normalize_non_empty_string_tuple(
    raw_values: Any,
    *,
    task_id: str,
    adapter_key: str,
    capability: str,
    field_name: str,
    allow_empty: bool,
) -> tuple[str, ...]:
    if raw_values is None:
        raise ResourceCapabilityMatcherContractError(
            f"matcher `{field_name}` 必须为去重字符串集合",
            details={
                "task_id": task_id,
                "adapter_key": adapter_key,
                "capability": capability,
                "actual_type": "NoneType",
            },
        )
    if isinstance(raw_values, (str, bytes)):
        raise ResourceCapabilityMatcherContractError(
            f"matcher `{field_name}` 必须为去重字符串集合",
            details={
                "task_id": task_id,
                "adapter_key": adapter_key,
                "capability": capability,
                "actual_type": type(raw_values).__name__,
            },
        )
    try:
        iterator = iter(raw_values)
    except TypeError as error:
        raise ResourceCapabilityMatcherContractError(
            f"matcher `{field_name}` 必须为去重字符串集合",
            details={
                "task_id": task_id,
                "adapter_key": adapter_key,
                "capability": capability,
                "actual_type": type(raw_values).__name__,
                "error_type": error.__class__.__name__,
            },
        ) from error

    values: list[str] = []
    seen: set[str] = set()
    for raw_value in iterator:
        if not isinstance(raw_value, str) or not raw_value:
            raise ResourceCapabilityMatcherContractError(
                f"matcher `{field_name}` 只能包含非空字符串",
                details={
                    "task_id": task_id,
                    "adapter_key": adapter_key,
                    "capability": capability,
                    "invalid_value": raw_value,
                },
            )
        if raw_value in seen:
            raise ResourceCapabilityMatcherContractError(
                f"matcher `{field_name}` 不得包含重复 capability",
                details={
                    "task_id": task_id,
                    "adapter_key": adapter_key,
                    "capability": capability,
                    "duplicate_value": raw_value,
                },
            )
        seen.add(raw_value)
        values.append(raw_value)

    if not allow_empty and not values:
        raise ResourceCapabilityMatcherContractError(
            f"matcher `{field_name}` 不得为空",
            details={"task_id": task_id, "adapter_key": adapter_key, "capability": capability},
        )
    return tuple(values)


class _MatcherRequirementValidationAdapter:
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({LEGACY_COLLECTION_MODE})

    def __init__(
        self,
        *,
        supported_capability: str,
        requirement_declaration: AdapterResourceRequirementDeclaration,
    ) -> None:
        self.supported_capabilities = frozenset({supported_capability})
        self.resource_requirement_declarations = (requirement_declaration,)

    def execute(self, request: Any) -> dict[str, Any]:
        raise AssertionError("matcher validation adapter must never execute")
