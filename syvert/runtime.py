from __future__ import annotations

from collections.abc import Iterable
import copy
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import queue
import re
import threading
import time
from typing import TYPE_CHECKING, Any, Callable, Mapping
from uuid import uuid4

from syvert.registry import (
    AdapterRegistry,
    AdapterResourceRequirementDeclaration,
    AdapterResourceRequirementDeclarationV2,
    AdapterResourceRequirementProfile,
    RegistryError,
    RESOURCE_DEPENDENCY_MODE_NONE,
    approved_resource_requirement_evidence_refs_for,
)
from syvert.resource_capability_evidence import approved_resource_capability_ids
from syvert.operation_taxonomy import stable_operation_entry
from syvert.read_side_collection import (
    COMMENT_COLLECTION_OPERATION,
    CommentRequestCursor,
    CollectionContractError,
    READ_SIDE_COLLECTION_OPERATIONS,
    comment_collection_result_envelope_from_dict,
    comment_collection_result_envelope_to_dict,
    comment_request_cursor_to_dict,
    collection_result_envelope_from_dict,
    collection_result_envelope_to_dict,
    validate_comment_request_cursor,
)
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
CONTENT_SEARCH_BY_KEYWORD = "content_search_by_keyword"
CONTENT_LIST_BY_CREATOR = "content_list_by_creator"
COMMENT_COLLECTION = COMMENT_COLLECTION_OPERATION
CONTENT_DETAIL = "content_detail"
CONTENT_SEARCH = "content_search"
CONTENT_LIST = "content_list"
COMMENT_COLLECTION_FAMILY = "comment_collection"
LEGACY_COLLECTION_MODE = "hybrid"
PAGINATED_COLLECTION_MODE = "paginated"
ALLOWED_TARGET_TYPES = frozenset({"url", "content", "content_id", "creator", "creator_id", "keyword"})
ALLOWED_COLLECTION_MODES = frozenset({"public", "authenticated", "hybrid", "paginated"})
ALLOWED_EXECUTION_CONTROL_CONCURRENCY_SCOPES = frozenset({"global", "adapter", "adapter_capability"})
CAPABILITY_FAMILY_BY_OPERATION = {
    CONTENT_DETAIL_BY_URL: CONTENT_DETAIL,
    CONTENT_SEARCH_BY_KEYWORD: CONTENT_SEARCH,
    CONTENT_LIST_BY_CREATOR: CONTENT_LIST,
    COMMENT_COLLECTION: COMMENT_COLLECTION_FAMILY,
}
ALLOWED_CONTENT_TYPES = {"video", "image_post", "mixed_media", "unknown"}
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE = {
    (CONTENT_DETAIL_BY_URL, LEGACY_COLLECTION_MODE): ("account", "proxy"),
    (CONTENT_SEARCH_BY_KEYWORD, PAGINATED_COLLECTION_MODE): ("account", "proxy"),
    (CONTENT_LIST_BY_CREATOR, PAGINATED_COLLECTION_MODE): ("account", "proxy"),
    (COMMENT_COLLECTION, PAGINATED_COLLECTION_MODE): ("account", "proxy"),
}
DEFAULT_BUNDLE_VALIDATION_RELEASE_REASON = "host_side_bundle_validation_failed"
DEFAULT_SUCCESS_RELEASE_REASON = "adapter_completed_without_disposition_hint"
DEFAULT_FAILURE_RELEASE_REASON = "adapter_failed_without_disposition_hint"
DEFAULT_INVALID_HINT_RELEASE_REASON = "invalid_resource_disposition_hint"
MATCH_STATUS_MATCHED = "matched"
MATCH_STATUS_UNMATCHED = "unmatched"
EXECUTION_CONTROL_EVENT_ADMISSION_CONCURRENCY_REJECTED = "admission_concurrency_rejected"
EXECUTION_CONTROL_EVENT_RETRY_CONCURRENCY_REJECTED = "retry_concurrency_rejected"
EXECUTION_CONTROL_EVENT_RETRY_EXHAUSTED = "retry_exhausted"
EXECUTION_CONTROL_CODE_CONCURRENCY_LIMIT_EXCEEDED = "concurrency_limit_exceeded"
EXECUTION_CONTROL_CODE_EXECUTION_TIMEOUT = "execution_timeout"
EXECUTION_CONTROL_CODE_EXECUTION_CONTROL_STATE_INVALID = "execution_control_state_invalid"
EXECUTION_CONTROL_CODE_RETRY_EXHAUSTED = "retry_exhausted"
EXECUTION_TIMEOUT_CLOSEOUT_GRACE_SECONDS = 0.1
_ALLOWED_MATCH_STATUSES = frozenset({MATCH_STATUS_MATCHED, MATCH_STATUS_UNMATCHED})
_ALLOWED_MATCHER_CAPABILITIES = frozenset({CONTENT_DETAIL, CONTENT_SEARCH, CONTENT_LIST, COMMENT_COLLECTION_FAMILY})
_APPROVED_RESOURCE_CAPABILITY_IDS = approved_resource_capability_ids()
_EXECUTION_CONCURRENCY_LOCK = threading.Lock()
_EXECUTION_CONCURRENCY_IN_FLIGHT: dict[tuple[str, ...], int] = {}
_EXECUTION_CONCURRENCY_ADMISSION_GUARDS: dict[tuple[str, ...], threading.Lock] = {}

if TYPE_CHECKING:
    from syvert.resource_lifecycle import ResourceBundle
    from syvert.resource_lifecycle_store import LocalResourceLifecycleStore
    from syvert.resource_trace_store import LocalResourceTraceStore


@dataclass(frozen=True)
class TaskInput:
    url: str | None = None
    content_ref: str | None = None
    keyword: str | None = None
    creator_id: str | None = None
    continuation_token: str | None = None
    comment_request_cursor: Mapping[str, Any] | None = None


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
class ExecutionTimeoutPolicy:
    timeout_ms: int


@dataclass(frozen=True)
class ExecutionRetryPolicy:
    max_attempts: int
    backoff_ms: int


@dataclass(frozen=True)
class ExecutionConcurrencyPolicy:
    scope: str
    max_in_flight: int
    on_limit: str


@dataclass(frozen=True)
class ExecutionControlPolicy:
    timeout: ExecutionTimeoutPolicy
    retry: ExecutionRetryPolicy
    concurrency: ExecutionConcurrencyPolicy


def default_execution_control_policy() -> ExecutionControlPolicy:
    return ExecutionControlPolicy(
        timeout=ExecutionTimeoutPolicy(timeout_ms=30000),
        retry=ExecutionRetryPolicy(max_attempts=1, backoff_ms=0),
        concurrency=ExecutionConcurrencyPolicy(scope="global", max_in_flight=1, on_limit="reject"),
    )


@dataclass(frozen=True)
class CoreTaskRequest:
    target: InputTarget
    policy: CollectionPolicy
    execution_control_policy: ExecutionControlPolicy | None = None
    request_cursor: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class TaskRequest:
    adapter_key: str
    capability: str
    input: TaskInput
    execution_control_policy: ExecutionControlPolicy | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class AdapterTaskRequest:
    capability: str
    target_type: str
    target_value: str
    collection_mode: str
    request_cursor: Mapping[str, Any] | None = None

    @property
    def input(self) -> TaskInput:
        if self.target_type == "url":
            return TaskInput(url=self.target_value)
        if self.target_type == "keyword":
            return TaskInput(keyword=self.target_value)
        if self.target_type == "content":
            return TaskInput(content_ref=self.target_value, comment_request_cursor=self.request_cursor)
        if self.target_type == "creator":
            return TaskInput(creator_id=self.target_value)
        return TaskInput()


@dataclass(frozen=True)
class ResourceDispositionHint:
    lease_id: str
    target_status_after_release: str
    reason: str


@dataclass(frozen=True)
class AdapterExecutionContext:
    request: AdapterTaskRequest
    resource_bundle: "ResourceBundle | None"
    execution_control_policy: ExecutionControlPolicy | None = None

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
class ExecutionConcurrencySlot:
    scope_key: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionConcurrencyAdmissionGuard:
    scope_key: tuple[str, ...]
    lock: threading.Lock


@dataclass(frozen=True)
class AdapterAttemptResult:
    envelope: dict[str, Any]
    attempt_outcome_ref: dict[str, Any] | None
    execution_control_event: dict[str, Any] | None = None
    core_timeout_outcome: bool = False


def comment_collection_request_error_envelope(
    request: Any,
    *,
    task_id: str,
    adapter_key: str,
    capability: str,
    contract_error: Mapping[str, Any],
) -> dict[str, Any] | None:
    if capability != COMMENT_COLLECTION:
        return None
    if isinstance(request, TaskRequest) and type(request.input) is TaskInput:
        target_ref = request.input.content_ref
    elif isinstance(request, CoreTaskRequest) and request.target.capability == COMMENT_COLLECTION:
        if request.target.target_type != "content" or request.policy.collection_mode != PAGINATED_COLLECTION_MODE:
            return None
        target_ref = request.target.target_value
    else:
        return None
    if not isinstance(target_ref, str) or not target_ref:
        return None
    error_code = contract_error.get("code")
    if error_code not in {"signature_or_request_invalid", "cursor_invalid_or_expired", "parse_failed"}:
        return None
    return {
        "task_id": task_id,
        "adapter_key": adapter_key,
        "capability": capability,
        "status": "success",
        "operation": COMMENT_COLLECTION,
        "target": {
            "operation": COMMENT_COLLECTION,
            "target_type": "content",
            "target_ref": target_ref,
        },
        "items": [],
        "has_more": False,
        "next_continuation": None,
        "result_status": "complete",
        "error_classification": str(error_code),
        "raw_payload_ref": f"failure://comment_collection/{error_code}",
        "source_trace": {
            "adapter_key": adapter_key,
            "provider_path": "core.runtime",
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "evidence_alias": f"comment_collection_request_cursor_{error_code}",
        },
        "audit": {
            "fail_closed": True,
            "failure_phase": "request_cursor_validation",
        },
    }


def finalize_pre_admission_comment_collection_result(
    request: Any,
    *,
    task_id: str,
    adapter_key: str,
    capability: str,
    envelope: dict[str, Any],
    task_record_store: TaskRecordStore | None,
) -> TaskExecutionResult:
    target_type = envelope["target"]["target_type"]
    target_value = envelope["target"]["target_ref"]
    snapshot_request = CoreTaskRequest(
        target=InputTarget(
            adapter_key=adapter_key,
            capability=capability,
            target_type=target_type,
            target_value=target_value,
        ),
        policy=CollectionPolicy(collection_mode=PAGINATED_COLLECTION_MODE),
        execution_control_policy=request.execution_control_policy if isinstance(request, (TaskRequest, CoreTaskRequest)) else None,
    )
    try:
        record = create_task_record(task_id, build_task_request_snapshot(snapshot_request))
        persisted_record, persistence_error = persist_task_record(
            task_id,
            adapter_key,
            capability,
            record,
            stage="accepted",
            task_record_store=task_record_store,
        )
        if persistence_error is not None:
            return persistence_error
        record = persisted_record or record
        record = start_task_record(record)
        persisted_record, persistence_error = persist_task_record(
            task_id,
            adapter_key,
            capability,
            record,
            stage="running",
            task_record_store=task_record_store,
        )
        if persistence_error is not None:
            return persistence_error
        record = persisted_record or record
        record = finish_task_record(record, envelope)
        persisted_record, persistence_error = persist_task_record(
            task_id,
            adapter_key,
            capability,
            record,
            stage="completion",
            task_record_store=task_record_store,
        )
        if persistence_error is not None:
            return persistence_error
        return TaskExecutionResult(envelope, persisted_record or record)
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


@dataclass(frozen=True)
class ResourceCapabilityMatcherInput:
    task_id: str
    adapter_key: str
    capability: str
    requirement_declaration: AdapterResourceRequirementDeclaration | AdapterResourceRequirementDeclarationV2
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
        return TaskExecutionResult(pre_accepted_failure_envelope(task_id, adapter_key, capability, task_id_error), None)

    normalized_request, contract_error = normalize_request(request)
    if contract_error is not None:
        comment_fail_closed = comment_collection_request_error_envelope(
            request,
            task_id=task_id,
            adapter_key=adapter_key,
            capability=capability,
            contract_error=contract_error,
        )
        if comment_fail_closed is not None:
            return finalize_pre_admission_comment_collection_result(
                request,
                task_id=task_id,
                adapter_key=adapter_key,
                capability=capability,
                envelope=comment_fail_closed,
                task_record_store=store,
            )
        return TaskExecutionResult(pre_accepted_failure_envelope(task_id, adapter_key, capability, contract_error), None)
    if normalized_request is None:
        return TaskExecutionResult(
            pre_accepted_failure_envelope(
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
        return TaskExecutionResult(
            pre_accepted_failure_envelope(task_id, adapter_key, capability, capability_family_error),
            None,
        )
    if capability_family is None:
        return TaskExecutionResult(
            pre_accepted_failure_envelope(
                task_id,
                adapter_key,
                capability,
                invalid_input_error("invalid_capability", "capability 无法投影到 adapter-facing family"),
            ),
            None,
        )

    projection_axis_error = validate_projection_axes_for_current_runtime(normalized_request)
    if projection_axis_error is not None:
        return TaskExecutionResult(
            pre_accepted_failure_envelope(task_id, adapter_key, capability, projection_axis_error),
            None,
        )

    try:
        registry = AdapterRegistry.from_mapping(adapters)
    except RegistryError as error:
        requested_resource_requirement_error = _requested_adapter_resource_requirement_error(
            adapters=adapters,
            adapter_key=adapter_key,
            error=error,
        )
        if requested_resource_requirement_error is not None:
            return TaskExecutionResult(
                pre_accepted_failure_envelope(
                    task_id,
                    adapter_key,
                    capability,
                    requested_resource_requirement_error,
                ),
                None,
            )
        return TaskExecutionResult(
            pre_accepted_failure_envelope(
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
            pre_accepted_failure_envelope(
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
            pre_accepted_failure_envelope(
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
            pre_accepted_failure_envelope(
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
            pre_accepted_failure_envelope(
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

    if capability == COMMENT_COLLECTION:
        cursor_error = validate_comment_request_cursor(
            normalized_request.request_cursor,
            target_ref=normalized_request.target.target_value,
        )
        if cursor_error is not None:
            comment_fail_closed = comment_collection_request_error_envelope(
                normalized_request,
                task_id=task_id,
                adapter_key=adapter_key,
                capability=capability,
                contract_error=invalid_input_error(
                    cursor_error["code"],
                    cursor_error["message"],
                    details=cursor_error.get("details", {}),
                ),
            )
            if comment_fail_closed is not None:
                return finalize_pre_admission_comment_collection_result(
                    normalized_request,
                    task_id=task_id,
                    adapter_key=adapter_key,
                    capability=capability,
                    envelope=comment_fail_closed,
                    task_record_store=store,
                )

    required_resource_slots = RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE.get(
        (normalized_request.target.capability, normalized_request.policy.collection_mode),
        (),
    )
    matcher_input: ResourceCapabilityMatcherInput | None = None
    if required_resource_slots:
        resource_requirement_declaration = registry.lookup_resource_requirement(adapter_key, capability_family)
        if resource_requirement_declaration is None:
            return TaskExecutionResult(
                pre_accepted_failure_envelope(
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
                pre_accepted_failure_envelope(
                    task_id,
                    adapter_key,
                    capability,
                    invalid_resource_requirement_error(error.message, details=error.details),
                ),
                None,
            )

    adapter_request, projection_error = project_to_adapter_request(normalized_request, capability_family)
    if projection_error is not None:
        return TaskExecutionResult(
            pre_accepted_failure_envelope(task_id, adapter_key, capability, projection_error),
            None,
        )
    request_cursor_validation_snapshot = (
        clone_request_cursor(normalized_request.request_cursor) if capability == COMMENT_COLLECTION else None
    )

    execution_control_policy = normalized_request.execution_control_policy
    if execution_control_policy is None:
        return TaskExecutionResult(
            pre_accepted_failure_envelope(
                task_id,
                adapter_key,
                capability,
                runtime_contract_error(
                    "execution_control_state_invalid",
                    "Core 未能物化默认执行控制策略",
                    details={"stage": "pre_execution", "control_context": "default_execution_control_policy"},
                ),
            ),
            None,
        )
    admission_guard = acquire_execution_concurrency_admission_guard(
        execution_control_policy.concurrency,
        adapter_key=adapter_key,
        capability=capability,
    )
    if not is_execution_concurrency_slot_available(
        execution_control_policy.concurrency,
        adapter_key=adapter_key,
        capability=capability,
    ):
        release_execution_concurrency_admission_guard(admission_guard)
        event = build_execution_control_event(
            task_id,
            adapter_key,
            capability,
            event_type=EXECUTION_CONTROL_EVENT_ADMISSION_CONCURRENCY_REJECTED,
            attempt_count=0,
            control_code=EXECUTION_CONTROL_CODE_CONCURRENCY_LIMIT_EXCEEDED,
            task_record_ref="none",
            policy=execution_control_policy,
        )
        envelope = pre_accepted_failure_envelope(
            task_id,
            adapter_key,
            capability,
            invalid_input_error(
                EXECUTION_CONTROL_CODE_CONCURRENCY_LIMIT_EXCEEDED,
                "执行控制并发限制拒绝本次任务提交",
                details={
                    "scope": execution_control_policy.concurrency.scope,
                    "max_in_flight": execution_control_policy.concurrency.max_in_flight,
                    "on_limit": execution_control_policy.concurrency.on_limit,
                    "task_record_ref": "none",
                    "execution_control_event": event,
                },
            ),
        )
        return TaskExecutionResult(
            with_runtime_observability(envelope, [event], [event]),
            None,
        )

    def release_admission_guard_or_failure(stage: str) -> TaskExecutionResult | None:
        release_error = release_execution_concurrency_admission_guard(admission_guard)
        if release_error is None:
            return None
        release_details = dict(release_error.get("details", {}))
        release_details["stage"] = stage
        release_details.setdefault(
            "task_record_ref",
            "none" if stage in {"create_task_record", "persist_accepted"} else f"task_record:{task_id}",
        )
        release_error = dict(release_error)
        release_error["details"] = release_details
        return TaskExecutionResult(
            with_failure_observability(failure_envelope(task_id, adapter_key, capability, release_error)),
            None,
        )

    try:
        record = create_task_record(task_id, build_task_request_snapshot(normalized_request))
    except TaskRecordContractError as error:
        release_failure = release_admission_guard_or_failure("create_task_record")
        if release_failure is not None:
            return release_failure
        return TaskExecutionResult(
            pre_accepted_failure_envelope(
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
        release_failure = release_admission_guard_or_failure("persist_accepted")
        if release_failure is not None:
            return release_failure
        return persistence_error
    if persisted_record is not None:
        record = persisted_record

    try:
        record = start_task_record(record)
    except TaskRecordContractError as error:
        release_failure = release_admission_guard_or_failure("start_task_record")
        if release_failure is not None:
            return finalize_task_execution_result(
                task_id,
                adapter_key,
                capability,
                record,
                release_failure.envelope,
                preserve_envelope_on_record_error=preserve_envelope_on_record_error,
                task_record_store=store,
            )
        return finalize_task_execution_result(
            task_id,
            adapter_key,
            capability,
            record,
            failure_envelope(
                task_id,
                adapter_key,
                capability,
                runtime_contract_error("invalid_task_record", str(error)),
            ),
            preserve_envelope_on_record_error=preserve_envelope_on_record_error,
            task_record_store=store,
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
        release_failure = release_admission_guard_or_failure("persist_running")
        if release_failure is not None:
            return finalize_task_execution_result(
                task_id,
                adapter_key,
                capability,
                record,
                release_failure.envelope,
                preserve_envelope_on_record_error=preserve_envelope_on_record_error,
                task_record_store=store,
            )
        return persistence_error
    if persisted_record is not None:
        record = persisted_record

    match_result = match_resource_capabilities(matcher_input) if matcher_input is not None else None
    if match_result is not None and match_result.match_status == MATCH_STATUS_UNMATCHED:
        release_failure = release_admission_guard_or_failure("resource_capability_match")
        if release_failure is not None:
            return finalize_task_execution_result(
                task_id,
                adapter_key,
                capability,
                record,
                release_failure.envelope,
                preserve_envelope_on_record_error=preserve_envelope_on_record_error,
                task_record_store=store,
            )
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
                        **_resource_requirement_unmatched_details(matcher_input.requirement_declaration),
                        "available_resource_capabilities": list(matcher_input.available_resource_capabilities),
                    },
                ),
            ),
            preserve_envelope_on_record_error=preserve_envelope_on_record_error,
            task_record_store=store,
        )

    envelope = execute_controlled_adapter_attempts(
        task_id=task_id,
        adapter_key=adapter_key,
        capability=capability,
        adapter_request=adapter_request,
        request_cursor_validation_snapshot=request_cursor_validation_snapshot,
        adapter=adapter_declaration.adapter,
        policy=execution_control_policy,
        initial_admission_guard=admission_guard,
        resource_lifecycle_store=resource_lifecycle_store,
        resource_trace_store=resource_trace_store,
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


def _resource_requirement_unmatched_details(
    declaration: AdapterResourceRequirementDeclaration | AdapterResourceRequirementDeclarationV2,
) -> dict[str, Any]:
    if type(declaration) is AdapterResourceRequirementDeclarationV2:
        return {
            "resource_requirement_profiles": [
                {
                    "profile_key": profile.profile_key,
                    "resource_dependency_mode": profile.resource_dependency_mode,
                    "required_capabilities": list(profile.required_capabilities),
                    "evidence_refs": list(profile.evidence_refs),
                }
                for profile in declaration.resource_requirement_profiles
            ]
        }
    return {"required_capabilities": list(declaration.required_capabilities)}


def execute_controlled_adapter_attempts(
    *,
    task_id: str,
    adapter_key: str,
    capability: str,
    adapter_request: AdapterTaskRequest,
    request_cursor_validation_snapshot: Mapping[str, Any] | None,
    adapter: Any,
    policy: ExecutionControlPolicy,
    initial_admission_guard: ExecutionConcurrencyAdmissionGuard,
    resource_lifecycle_store: "LocalResourceLifecycleStore | None",
    resource_trace_store: "LocalResourceTraceStore | None",
) -> dict[str, Any]:
    attempt_index = 1
    admission_guard: ExecutionConcurrencyAdmissionGuard | None = initial_admission_guard
    last_failed_envelope: dict[str, Any] | None = None
    runtime_result_refs: list[dict[str, Any]] = []
    execution_control_events: list[dict[str, Any]] = []
    failure_signals: list[dict[str, Any]] = []
    structured_log_events: list[dict[str, Any]] = []
    metric_samples: list[dict[str, Any]] = []

    while True:
        attempt = execute_single_controlled_adapter_attempt(
            task_id=task_id,
            adapter_key=adapter_key,
            capability=capability,
            adapter_request=adapter_request,
            request_cursor_validation_snapshot=request_cursor_validation_snapshot,
            adapter=adapter,
            policy=policy,
            attempt_index=attempt_index,
            admission_guard=admission_guard,
            resource_lifecycle_store=resource_lifecycle_store,
            resource_trace_store=resource_trace_store,
        )
        admission_guard = None
        envelope = attempt.envelope
        if attempt.attempt_outcome_ref is not None:
            runtime_result_refs.append(attempt.attempt_outcome_ref)
            attempt_log_events, attempt_metric_samples = build_attempt_lifecycle_observability(attempt.attempt_outcome_ref)
            structured_log_events.extend(attempt_log_events)
            metric_samples.extend(attempt_metric_samples)
        if attempt.execution_control_event is not None:
            execution_control_events.append(attempt.execution_control_event)
            runtime_result_refs.append(attempt.execution_control_event)
            if last_failed_envelope is not None and is_synthetic_retry_concurrency_rejection(envelope):
                envelope = with_failed_envelope_control_details(
                    last_failed_envelope,
                    event=attempt.execution_control_event,
                    details={
                        "retry_concurrency_rejected": True,
                        "attempt_count": attempt_index - 1,
                        "scope": policy.concurrency.scope,
                        "max_in_flight": policy.concurrency.max_in_flight,
                    },
                )
            return with_runtime_observability(
                envelope,
                runtime_result_refs,
                execution_control_events,
                failure_signals,
                structured_log_events,
                metric_samples,
            )
        envelope = with_runtime_observability(
            envelope,
            runtime_result_refs,
            execution_control_events,
            failure_signals,
            structured_log_events,
            metric_samples,
        )
        if envelope.get("status") == "success":
            return envelope

        last_failed_envelope = envelope
        failure_signal = envelope.get("runtime_failure_signal")
        if isinstance(failure_signal, Mapping):
            failure_signals.append(dict(failure_signal))
        retryable = is_retryable_attempt_outcome(
            envelope,
            capability=capability,
            core_timeout_outcome=attempt.core_timeout_outcome,
        )
        if not retryable:
            return envelope
        if attempt_index >= policy.retry.max_attempts:
            event = build_execution_control_event(
                task_id,
                adapter_key,
                capability,
                event_type=EXECUTION_CONTROL_EVENT_RETRY_EXHAUSTED,
                attempt_count=attempt_index,
                control_code=EXECUTION_CONTROL_CODE_RETRY_EXHAUSTED,
                task_record_ref=f"task_record:{task_id}",
                policy=policy,
            )
            execution_control_events.append(event)
            runtime_result_refs.append(event)
            exhausted_envelope = with_failed_envelope_control_details(
                last_failed_envelope,
                event=event,
                details={
                    "retry_exhausted": True,
                    "attempt_count": attempt_index,
                    "max_attempts": policy.retry.max_attempts,
                    "last_attempt_outcome_ref": attempt.attempt_outcome_ref,
                },
            )
            return with_runtime_observability(
                exhausted_envelope,
                runtime_result_refs,
                execution_control_events,
                failure_signals,
                structured_log_events,
                metric_samples,
            )
        retry_result_refs = [attempt.attempt_outcome_ref] if attempt.attempt_outcome_ref is not None else []
        retry_log_event, retry_metric_sample = build_retry_scheduled_observability(
            task_id=task_id,
            adapter_key=adapter_key,
            capability=capability,
            attempt_index=attempt_index,
            next_attempt_index=attempt_index + 1,
            failure_signal_id=str(envelope.get("runtime_failure_signal", {}).get("signal_id", "")),
            error_category=str(envelope.get("runtime_failure_signal", {}).get("error_category", "")),
            error_code=str(envelope.get("runtime_failure_signal", {}).get("error_code", "")),
            failure_phase=str(envelope.get("runtime_failure_signal", {}).get("failure_phase", "")),
            resource_trace_refs=list(
                envelope.get("runtime_failure_signal", {}).get("resource_trace_refs", [])
                if isinstance(envelope.get("runtime_failure_signal", {}).get("resource_trace_refs"), list)
                else []
            ),
            runtime_result_refs=retry_result_refs,
            policy=policy,
        )
        structured_log_events.append(retry_log_event)
        metric_samples.append(retry_metric_sample)
        if policy.retry.backoff_ms:
            time.sleep(policy.retry.backoff_ms / 1000)
        admission_guard = acquire_execution_concurrency_admission_guard(
            policy.concurrency,
            adapter_key=adapter_key,
            capability=capability,
        )
        if not is_execution_concurrency_slot_available(
            policy.concurrency,
            adapter_key=adapter_key,
            capability=capability,
        ):
            release_execution_concurrency_admission_guard(admission_guard)
            admission_guard = None
            event = build_execution_control_event(
                task_id,
                adapter_key,
                capability,
                event_type=EXECUTION_CONTROL_EVENT_RETRY_CONCURRENCY_REJECTED,
                attempt_count=attempt_index,
                control_code=EXECUTION_CONTROL_CODE_CONCURRENCY_LIMIT_EXCEEDED,
                task_record_ref=f"task_record:{task_id}",
                policy=policy,
            )
            execution_control_events.append(event)
            runtime_result_refs.append(event)
            rejected_envelope = with_failed_envelope_control_details(
                last_failed_envelope,
                event=event,
                details={
                    "retry_concurrency_rejected": True,
                    "attempt_count": attempt_index,
                    "scope": policy.concurrency.scope,
                    "max_in_flight": policy.concurrency.max_in_flight,
                },
            )
            return with_runtime_observability(
                rejected_envelope,
                runtime_result_refs,
                execution_control_events,
                failure_signals,
                structured_log_events,
                metric_samples,
            )
        attempt_index += 1


def execute_single_controlled_adapter_attempt(
    *,
    task_id: str,
    adapter_key: str,
    capability: str,
    adapter_request: AdapterTaskRequest,
    request_cursor_validation_snapshot: Mapping[str, Any] | None,
    adapter: Any,
    policy: ExecutionControlPolicy,
    attempt_index: int,
    admission_guard: ExecutionConcurrencyAdmissionGuard,
    resource_lifecycle_store: "LocalResourceLifecycleStore | None",
    resource_trace_store: "LocalResourceTraceStore | None",
) -> AdapterAttemptResult:
    requested_slots = resolve_requested_resource_slots(
        CoreTaskRequest(
            target=InputTarget(
                adapter_key=adapter_key,
                capability=capability,
                target_type=adapter_request.target_type,
                target_value=adapter_request.target_value,
            ),
            policy=CollectionPolicy(collection_mode=adapter_request.collection_mode),
            execution_control_policy=policy,
        )
    )
    managed_resource_store = None
    managed_trace_store = None
    resource_bundle = None
    live_resource_lease = None
    disposition_hint: ResourceDispositionHint | None = None
    default_release_reason = DEFAULT_SUCCESS_RELEASE_REASON
    started_at = datetime.now(timezone.utc)
    slot: ExecutionConcurrencySlot | None = None
    admission_guard_released = False
    slot_released = False

    def release_attempt_admission_guard() -> dict[str, Any] | None:
        nonlocal admission_guard_released
        if admission_guard_released:
            return None
        admission_guard_released = True
        return release_execution_concurrency_admission_guard(admission_guard)

    def finish_attempt(envelope: dict[str, Any], *, core_timeout_outcome: bool = False) -> AdapterAttemptResult:
        nonlocal slot_released
        trace_refs = resource_trace_refs_for_bundle(resource_bundle)
        if trace_refs:
            envelope = with_failed_envelope_resource_trace_refs(envelope, trace_refs)
        guard_release_error = release_attempt_admission_guard()
        if guard_release_error is not None:
            envelope = failure_envelope(task_id, adapter_key, capability, guard_release_error)
            core_timeout_outcome = False
        if slot is not None and not slot_released:
            release_error = release_execution_concurrency_slot(slot)
            slot_released = True
            if release_error is not None:
                envelope = failure_envelope(task_id, adapter_key, capability, release_error)
                core_timeout_outcome = False
        ended_at = datetime.now(timezone.utc)
        return AdapterAttemptResult(
            envelope,
            build_attempt_outcome_ref(
                task_id,
                adapter_key,
                capability,
                attempt_index,
                envelope,
                started_at=started_at,
                ended_at=ended_at,
                core_timeout_outcome=core_timeout_outcome,
            ),
            core_timeout_outcome=core_timeout_outcome,
        )

    try:
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
                envelope = dict(acquire_result)
                return finish_attempt(envelope)
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
                return finish_attempt(envelope)

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
                return finish_attempt(envelope)

        adapter_context = AdapterExecutionContext(
            request=adapter_request,
            resource_bundle=resource_bundle,
            execution_control_policy=policy,
        )
        slot = acquire_execution_concurrency_slot(
            policy.concurrency,
            adapter_key=adapter_key,
            capability=capability,
        )
        if slot is None:
            event = None
            if attempt_index > 1:
                event = build_execution_control_event(
                    task_id,
                    adapter_key,
                    capability,
                    event_type=EXECUTION_CONTROL_EVENT_RETRY_CONCURRENCY_REJECTED,
                    attempt_count=attempt_index - 1,
                    control_code=EXECUTION_CONTROL_CODE_CONCURRENCY_LIMIT_EXCEEDED,
                    task_record_ref=f"task_record:{task_id}",
                    policy=policy,
                )
            cleanup_envelope = None
            if resource_bundle is not None and managed_resource_store is not None and live_resource_lease is not None:
                cleanup_envelope = settle_managed_resource_bundle(
                    lease_id=live_resource_lease.lease_id,
                    task_id=task_id,
                    resource_lifecycle_store=managed_resource_store,
                    resource_trace_store=managed_trace_store,
                    default_reason=DEFAULT_BUNDLE_VALIDATION_RELEASE_REASON,
                    hint=None,
                )
            envelope = cleanup_envelope or failure_envelope(
                task_id,
                adapter_key,
                capability,
                runtime_contract_error(
                    EXECUTION_CONTROL_CODE_EXECUTION_CONTROL_STATE_INVALID,
                    "execution concurrency slot became unavailable after guarded admission",
                    details={
                        "control_code": EXECUTION_CONTROL_CODE_CONCURRENCY_LIMIT_EXCEEDED,
                        "stage": "pre_execution",
                        "control_context": "guarded_admission",
                        "scope": policy.concurrency.scope,
                        "max_in_flight": policy.concurrency.max_in_flight,
                    },
                ),
            )
            guard_release_error = release_attempt_admission_guard()
            if guard_release_error is not None:
                envelope = failure_envelope(task_id, adapter_key, capability, guard_release_error)
                event = None
            return AdapterAttemptResult(envelope, None, execution_control_event=event)
        guard_release_error = release_attempt_admission_guard()
        if guard_release_error is not None:
            release_error = release_execution_concurrency_slot(slot)
            slot_released = True
            envelope = failure_envelope(task_id, adapter_key, capability, guard_release_error)
            if release_error is not None:
                envelope = failure_envelope(task_id, adapter_key, capability, release_error)
            return finish_attempt(envelope)
        (
            envelope,
            disposition_hint,
            default_release_reason,
            slot_release_deferred,
            core_timeout_outcome,
        ) = run_adapter_attempt_with_timeout(
            task_id=task_id,
            adapter_key=adapter_key,
            capability=capability,
            adapter=adapter,
            adapter_context=adapter_context,
            request_cursor_validation_snapshot=request_cursor_validation_snapshot,
            timeout_ms=policy.timeout.timeout_ms,
            resource_bundle=resource_bundle,
            slot=slot,
        )
        if slot_release_deferred:
            slot_released = True

        if resource_bundle is not None and managed_resource_store is not None and live_resource_lease is not None:
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
                core_timeout_outcome = False
        if slot_release_deferred:
            return AdapterAttemptResult(envelope, None)
        return finish_attempt(envelope, core_timeout_outcome=core_timeout_outcome)
    finally:
        if not admission_guard_released:
            release_attempt_admission_guard()
        if slot is not None and not slot_released:
            release_execution_concurrency_slot(slot)


def run_adapter_attempt_with_timeout(
    *,
    task_id: str,
    adapter_key: str,
    capability: str,
    adapter: Any,
    adapter_context: AdapterExecutionContext,
    request_cursor_validation_snapshot: Mapping[str, Any] | None,
    timeout_ms: int,
    resource_bundle: Any,
    slot: ExecutionConcurrencySlot | None,
) -> tuple[dict[str, Any], ResourceDispositionHint | None, str, bool, bool]:
    result_queue: queue.Queue[tuple[str, Any]] = queue.Queue(maxsize=1)

    def invoke_adapter() -> None:
        try:
            result_queue.put(("payload", adapter.execute(adapter_context)))
        except BaseException as error:
            result_queue.put(("error", error))

    thread = threading.Thread(target=invoke_adapter, daemon=True)
    thread.start()
    try:
        kind, value = result_queue.get(timeout=timeout_ms / 1000)
    except queue.Empty:
        thread.join(timeout=EXECUTION_TIMEOUT_CLOSEOUT_GRACE_SECONDS)
        if thread.is_alive():
            slot_release_deferred = False
            if slot is not None:
                def release_slot_after_adapter_exit() -> None:
                    thread.join()
                    release_execution_concurrency_slot(slot)

                threading.Thread(target=release_slot_after_adapter_exit, daemon=True).start()
                slot_release_deferred = True
            envelope = failure_envelope(
                task_id,
                adapter_key,
                capability,
                {
                    "category": "runtime_contract",
                    "code": EXECUTION_CONTROL_CODE_EXECUTION_CONTROL_STATE_INVALID,
                    "message": "adapter execution timeout closeout could not be proven within bounded quarantine",
                    "details": {
                        "control_code": EXECUTION_CONTROL_CODE_EXECUTION_TIMEOUT,
                        "timeout_ms": timeout_ms,
                        "closeout_grace_seconds": EXECUTION_TIMEOUT_CLOSEOUT_GRACE_SECONDS,
                        "retryable": False,
                        "resource_quarantine": "INVALID",
                    },
                },
            )
            disposition_hint = (
                ResourceDispositionHint(
                    lease_id=resource_bundle.lease_id,
                    target_status_after_release="INVALID",
                    reason="execution_timeout_closeout_unproven",
                )
                if resource_bundle is not None
                else None
            )
            return envelope, disposition_hint, "execution_timeout_closeout_unproven", slot_release_deferred, False
        envelope = failure_envelope(
            task_id,
            adapter_key,
            capability,
            {
                "category": "platform",
                "code": EXECUTION_CONTROL_CODE_EXECUTION_TIMEOUT,
                "message": "adapter execution attempt exceeded execution_control_policy timeout",
                "details": {
                    "control_code": EXECUTION_CONTROL_CODE_EXECUTION_TIMEOUT,
                    "timeout_ms": timeout_ms,
                    "retryable": True,
                },
            },
        )
        late_disposition_hint: ResourceDispositionHint | None = None
        try:
            late_kind, late_value = result_queue.get_nowait()
        except queue.Empty:
            late_kind = ""
            late_value = None
        if late_kind == "payload" and isinstance(late_value, Mapping):
            late_disposition_hint, hint_error = extract_internal_resource_disposition_hint(
                late_value.get("resource_disposition_hint"),
                expected_lease_id=resource_bundle.lease_id if resource_bundle is not None else None,
            )
            if hint_error is not None:
                return (
                    timeout_closeout_invalid_hint_envelope(task_id, adapter_key, capability, timeout_ms, hint_error),
                    timeout_closeout_invalid_resource_hint(resource_bundle),
                    "timeout_closeout_invalid_resource_disposition_hint",
                    False,
                    False,
                )
        elif late_kind == "error" and isinstance(late_value, PlatformAdapterError):
            late_disposition_hint, hint_error = extract_internal_resource_disposition_hint(
                late_value.resource_disposition_hint,
                expected_lease_id=resource_bundle.lease_id if resource_bundle is not None else None,
            )
            if hint_error is not None:
                return (
                    timeout_closeout_invalid_hint_envelope(task_id, adapter_key, capability, timeout_ms, hint_error),
                    timeout_closeout_invalid_resource_hint(resource_bundle),
                    "timeout_closeout_invalid_resource_disposition_hint",
                    False,
                    False,
                )
        return envelope, late_disposition_hint, DEFAULT_FAILURE_RELEASE_REASON, False, True

    disposition_hint: ResourceDispositionHint | None = None
    default_release_reason = DEFAULT_SUCCESS_RELEASE_REASON
    if kind == "payload":
        payload = value
        payload_error = validate_success_payload(
            payload,
            capability=capability,
            target_type=adapter_context.target_type,
            target_value=adapter_context.target_value,
            request_cursor=request_cursor_validation_snapshot,
        )
        if payload_error is not None:
            return failure_envelope(task_id, adapter_key, capability, payload_error), None, DEFAULT_FAILURE_RELEASE_REASON, False, False
        disposition_hint, hint_error = extract_internal_resource_disposition_hint(
            payload.get("resource_disposition_hint"),
            expected_lease_id=resource_bundle.lease_id if resource_bundle is not None else None,
        )
        if hint_error is not None:
            return failure_envelope(task_id, adapter_key, capability, hint_error), None, DEFAULT_INVALID_HINT_RELEASE_REASON, False, False
        success_envelope = {
            "task_id": task_id,
            "adapter_key": adapter_key,
            "capability": capability,
            "status": "success",
        }
        if capability in READ_SIDE_COLLECTION_OPERATIONS:
            success_envelope.update(collection_result_envelope_to_dict(collection_result_envelope_from_dict(payload)))
        elif capability == COMMENT_COLLECTION:
            success_envelope.update(
                comment_collection_result_envelope_to_dict(comment_collection_result_envelope_from_dict(payload))
            )
        else:
            success_envelope.update({"raw": payload["raw"], "normalized": payload["normalized"]})
        return (success_envelope, disposition_hint, default_release_reason, False, False)

    error = value
    if isinstance(error, PlatformAdapterError):
        disposition_hint, hint_error = extract_internal_resource_disposition_hint(
            error.resource_disposition_hint,
            expected_lease_id=resource_bundle.lease_id if resource_bundle is not None else None,
        )
        if hint_error is not None:
            return failure_envelope(task_id, adapter_key, capability, hint_error), None, DEFAULT_INVALID_HINT_RELEASE_REASON, False, False
        return (
            failure_envelope(task_id, adapter_key, capability, classify_adapter_error(error)),
            disposition_hint,
            DEFAULT_FAILURE_RELEASE_REASON,
            False,
            False,
        )
    return (
        failure_envelope(
            task_id,
            adapter_key,
            capability,
            runtime_contract_error(
                "adapter_execution_error",
                str(error) or error.__class__.__name__,
            ),
        ),
        None,
        DEFAULT_FAILURE_RELEASE_REASON,
        False,
        False,
    )


def timeout_closeout_invalid_hint_envelope(
    task_id: str,
    adapter_key: str,
    capability: str,
    timeout_ms: int,
    hint_error: Mapping[str, Any],
) -> dict[str, Any]:
    return failure_envelope(
        task_id,
        adapter_key,
        capability,
        runtime_contract_error(
            EXECUTION_CONTROL_CODE_EXECUTION_CONTROL_STATE_INVALID,
            "timeout closeout late resource disposition hint is invalid",
            details={
                "control_code": EXECUTION_CONTROL_CODE_EXECUTION_TIMEOUT,
                "timeout_ms": timeout_ms,
                "closeout_error": dict(hint_error),
                "resource_quarantine": "INVALID",
                "retryable": False,
            },
        ),
    )


def timeout_closeout_invalid_resource_hint(resource_bundle: Any) -> ResourceDispositionHint | None:
    if resource_bundle is None:
        return None
    return ResourceDispositionHint(
        lease_id=resource_bundle.lease_id,
        target_status_after_release="INVALID",
        reason="timeout_closeout_invalid_resource_disposition_hint",
    )


def acquire_execution_concurrency_admission_guard(
    policy: ExecutionConcurrencyPolicy,
    *,
    adapter_key: str,
    capability: str,
) -> ExecutionConcurrencyAdmissionGuard:
    scope_key = execution_concurrency_scope_key(policy, adapter_key=adapter_key, capability=capability)
    with _EXECUTION_CONCURRENCY_LOCK:
        guard_lock = _EXECUTION_CONCURRENCY_ADMISSION_GUARDS.get(scope_key)
        if guard_lock is None:
            guard_lock = threading.Lock()
            _EXECUTION_CONCURRENCY_ADMISSION_GUARDS[scope_key] = guard_lock
    guard_lock.acquire()
    return ExecutionConcurrencyAdmissionGuard(scope_key=scope_key, lock=guard_lock)


def release_execution_concurrency_admission_guard(
    guard: ExecutionConcurrencyAdmissionGuard | None,
) -> dict[str, Any] | None:
    if guard is None:
        return None
    try:
        guard.lock.release()
    except RuntimeError:
        return runtime_contract_error(
            EXECUTION_CONTROL_CODE_EXECUTION_CONTROL_STATE_INVALID,
            "execution concurrency admission guard release underflow",
            details={
                "control_code": EXECUTION_CONTROL_CODE_EXECUTION_CONTROL_STATE_INVALID,
                "scope_key": list(guard.scope_key),
            },
        )
    return None


def acquire_execution_concurrency_slot(
    policy: ExecutionConcurrencyPolicy,
    *,
    adapter_key: str,
    capability: str,
) -> ExecutionConcurrencySlot | None:
    scope_key = execution_concurrency_scope_key(policy, adapter_key=adapter_key, capability=capability)
    with _EXECUTION_CONCURRENCY_LOCK:
        in_flight = _EXECUTION_CONCURRENCY_IN_FLIGHT.get(scope_key, 0)
        if in_flight >= policy.max_in_flight:
            return None
        _EXECUTION_CONCURRENCY_IN_FLIGHT[scope_key] = in_flight + 1
    return ExecutionConcurrencySlot(scope_key=scope_key)


def is_execution_concurrency_slot_available(
    policy: ExecutionConcurrencyPolicy,
    *,
    adapter_key: str,
    capability: str,
) -> bool:
    scope_key = execution_concurrency_scope_key(policy, adapter_key=adapter_key, capability=capability)
    with _EXECUTION_CONCURRENCY_LOCK:
        return _EXECUTION_CONCURRENCY_IN_FLIGHT.get(scope_key, 0) < policy.max_in_flight


def release_execution_concurrency_slot(slot: ExecutionConcurrencySlot | None) -> dict[str, Any] | None:
    if slot is None:
        return None
    with _EXECUTION_CONCURRENCY_LOCK:
        in_flight = _EXECUTION_CONCURRENCY_IN_FLIGHT.get(slot.scope_key, 0)
        if in_flight <= 0:
            return runtime_contract_error(
                EXECUTION_CONTROL_CODE_EXECUTION_CONTROL_STATE_INVALID,
                "execution concurrency slot release underflow",
                details={
                    "control_code": EXECUTION_CONTROL_CODE_EXECUTION_CONTROL_STATE_INVALID,
                    "scope_key": list(slot.scope_key),
                    "in_flight": in_flight,
                },
            )
        if in_flight == 1:
            _EXECUTION_CONCURRENCY_IN_FLIGHT.pop(slot.scope_key, None)
        else:
            _EXECUTION_CONCURRENCY_IN_FLIGHT[slot.scope_key] = in_flight - 1
    return None


def execution_concurrency_scope_key(
    policy: ExecutionConcurrencyPolicy,
    *,
    adapter_key: str,
    capability: str,
) -> tuple[str, ...]:
    if policy.scope == "global":
        return ("global",)
    if policy.scope == "adapter":
        return ("adapter", adapter_key)
    return ("adapter_capability", adapter_key, capability)


def is_retryable_attempt_outcome(
    envelope: Mapping[str, Any],
    *,
    capability: str,
    core_timeout_outcome: bool,
) -> bool:
    if capability != CONTENT_DETAIL_BY_URL or envelope.get("status") != "failed":
        return False
    error = envelope.get("error")
    if not isinstance(error, Mapping):
        return False
    details = error.get("details")
    if not isinstance(details, Mapping):
        details = {}
    if core_timeout_outcome:
        return True
    return error.get("category") == "platform" and details.get("retryable") is True


def build_attempt_outcome_ref(
    task_id: str,
    adapter_key: str,
    capability: str,
    attempt_index: int,
    envelope: Mapping[str, Any],
    *,
    started_at: datetime,
    ended_at: datetime,
    core_timeout_outcome: bool,
) -> dict[str, Any]:
    status = envelope.get("status")
    if status == "success":
        outcome = "succeeded"
        control_code = ""
    else:
        error = envelope.get("error") if isinstance(envelope.get("error"), Mapping) else {}
        details = error.get("details") if isinstance(error.get("details"), Mapping) else {}
        control_code = str(details.get("control_code") or "") if core_timeout_outcome else ""
        outcome = "timeout" if core_timeout_outcome else "failed"
    terminal_envelope = dict(envelope)
    terminal_envelope.pop("runtime_result_refs", None)
    terminal_envelope.pop("execution_control_events", None)
    terminal_envelope.pop("runtime_failure_signal", None)
    terminal_envelope.pop("runtime_structured_log_events", None)
    terminal_envelope.pop("runtime_execution_metric_samples", None)
    terminal_envelope.pop("_runtime_failure_signals", None)
    terminal_envelope.pop("_runtime_structured_log_events", None)
    terminal_envelope.pop("_runtime_execution_metric_samples", None)
    ref = {
        "ref_type": "ExecutionAttemptOutcome",
        "ref_id": f"{task_id}:attempt:{attempt_index}",
        "task_id": task_id,
        "adapter_key": adapter_key,
        "capability": capability,
        "attempt_index": attempt_index,
        "started_at": started_at.isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "ended_at": ended_at.isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "outcome": outcome,
        "terminal_envelope": terminal_envelope,
    }
    if control_code:
        ref["control_code"] = control_code
    return ref


def build_execution_control_event(
    task_id: str,
    adapter_key: str,
    capability: str,
    *,
    event_type: str,
    attempt_count: int,
    control_code: str,
    task_record_ref: str,
    policy: ExecutionControlPolicy,
) -> dict[str, Any]:
    return {
        "ref_type": "ExecutionControlEvent",
        "ref_id": f"{task_id}:{event_type}:{attempt_count}",
        "task_id": task_id,
        "event_type": event_type,
        "adapter_key": adapter_key,
        "capability": capability,
        "attempt_count": attempt_count,
        "control_code": control_code,
        "task_record_ref": task_record_ref,
        "policy": {
            "timeout": {"timeout_ms": policy.timeout.timeout_ms},
            "retry": {"max_attempts": policy.retry.max_attempts, "backoff_ms": policy.retry.backoff_ms},
            "concurrency": {
                "scope": policy.concurrency.scope,
                "max_in_flight": policy.concurrency.max_in_flight,
                "on_limit": policy.concurrency.on_limit,
            },
        },
        "occurred_at": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
    }


def with_runtime_observability(
    envelope: Mapping[str, Any],
    runtime_result_refs: list[dict[str, Any]],
    execution_control_events: list[dict[str, Any]],
    failure_signals: list[dict[str, Any]] | None = None,
    structured_log_events: list[dict[str, Any]] | None = None,
    metric_samples: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    enriched = dict(envelope)
    if enriched.get("status") == "success":
        if runtime_result_refs and (len(runtime_result_refs) > 1 or execution_control_events):
            enriched["runtime_result_refs"] = list(runtime_result_refs)
        if failure_signals:
            enriched["_runtime_failure_signals"] = list(failure_signals)
        if structured_log_events:
            enriched["_runtime_structured_log_events"] = list(structured_log_events)
        if metric_samples:
            enriched["_runtime_execution_metric_samples"] = list(metric_samples)
        return enriched
    if runtime_result_refs and (enriched.get("status") == "failed" or len(runtime_result_refs) > 1 or execution_control_events):
        enriched["runtime_result_refs"] = list(runtime_result_refs)
    if execution_control_events:
        enriched["execution_control_events"] = list(execution_control_events)
    if failure_signals:
        enriched["_runtime_failure_signals"] = list(failure_signals)
    if structured_log_events:
        enriched["runtime_structured_log_events"] = list(structured_log_events)
    if metric_samples:
        enriched["runtime_execution_metric_samples"] = list(metric_samples)
    if enriched.get("status") == "failed" and runtime_result_refs:
        current_error = enriched.get("error") if isinstance(enriched.get("error"), Mapping) else {}
        current_details = current_error.get("details") if isinstance(current_error.get("details"), Mapping) else {}
        current_task_record_ref = current_details.get("task_record_ref")
        if current_task_record_ref != "none":
            enriched = with_failed_envelope_task_record_ref(enriched, f"task_record:{enriched.get('task_id')}")
    if enriched.get("status") == "failed":
        enriched = with_failure_observability(enriched)
    return enriched


def public_task_execution_envelope(envelope: Mapping[str, Any]) -> dict[str, Any]:
    public_envelope = dict(envelope)
    public_envelope.pop("_runtime_failure_signals", None)
    public_envelope.pop("_runtime_structured_log_events", None)
    public_envelope.pop("_runtime_execution_metric_samples", None)
    return public_envelope


def pre_accepted_failure_envelope(
    task_id: str,
    adapter_key: str,
    capability: str,
    error: Mapping[str, Any],
) -> dict[str, Any]:
    enriched_error = dict(error)
    current_details = dict(enriched_error.get("details") if isinstance(enriched_error.get("details"), Mapping) else {})
    current_details["task_record_ref"] = "none"
    current_details.setdefault("stage", "pre_admission")
    enriched_error["details"] = current_details
    return with_failure_observability(failure_envelope(
        task_id,
        adapter_key,
        capability,
        enriched_error,
    ))


def with_failed_envelope_resource_trace_refs(envelope: Mapping[str, Any], refs: list[dict[str, Any]]) -> dict[str, Any]:
    if envelope.get("status") != "failed" or not refs:
        return dict(envelope)
    enriched = dict(envelope)
    error = dict(enriched.get("error") if isinstance(enriched.get("error"), Mapping) else {})
    current_details = dict(error.get("details") if isinstance(error.get("details"), Mapping) else {})
    current_details.setdefault("resource_trace_refs", refs)
    error["details"] = current_details
    enriched["error"] = error
    return enriched


def with_failed_envelope_task_record_ref(envelope: Mapping[str, Any], task_record_ref: str) -> dict[str, Any]:
    if envelope.get("status") != "failed":
        return dict(envelope)
    enriched = dict(envelope)
    error = dict(enriched.get("error") if isinstance(enriched.get("error"), Mapping) else {})
    current_details = dict(error.get("details") if isinstance(error.get("details"), Mapping) else {})
    current_details["task_record_ref"] = task_record_ref
    error["details"] = current_details
    enriched["error"] = error
    return enriched


def resource_trace_refs_for_bundle(resource_bundle: Any) -> list[dict[str, Any]]:
    if resource_bundle is None:
        return []
    lease_id = getattr(resource_bundle, "lease_id", "")
    bundle_id = getattr(resource_bundle, "bundle_id", "")
    refs: list[dict[str, Any]] = []
    for slot_name in ("account", "proxy"):
        resource = getattr(resource_bundle, slot_name, None)
        resource_id = getattr(resource, "resource_id", "")
        resource_type = getattr(resource, "resource_type", slot_name)
        if not lease_id or not bundle_id or not resource_id:
            continue
        refs.append(
            {
                "event_id": f"acquired:{lease_id}:{resource_id}",
                "ref_type": "ResourceTraceEvent",
                "lease_id": lease_id,
                "bundle_id": bundle_id,
                "resource_id": resource_id,
                "resource_type": resource_type,
            }
        )
    return refs


def build_retry_scheduled_observability(
    *,
    task_id: str,
    adapter_key: str,
    capability: str,
    attempt_index: int,
    next_attempt_index: int,
    failure_signal_id: str,
    error_category: str,
    error_code: str,
    failure_phase: str,
    resource_trace_refs: list[dict[str, Any]],
    runtime_result_refs: list[dict[str, Any]],
    policy: ExecutionControlPolicy,
) -> tuple[dict[str, Any], dict[str, Any]]:
    occurred_at = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    log_event = {
        "event_id": f"runtime_log:{task_id}:retry_scheduled:{attempt_index}:{next_attempt_index}",
        "task_id": task_id,
        "adapter_key": adapter_key,
        "capability": capability,
        "event_type": "retry_scheduled",
        "level": "info",
        "attempt_index": attempt_index,
        "failure_signal_id": failure_signal_id,
        "resource_trace_refs": list(resource_trace_refs),
        "runtime_result_refs": list(runtime_result_refs),
        "message": f"retry scheduled after attempt {attempt_index}",
        "occurred_at": occurred_at,
    }
    metric_sample = {
        "metric_id": f"runtime_metric:{task_id}:retry_scheduled_total:{attempt_index}:{next_attempt_index}",
        "task_id": task_id,
        "metric_name": "retry_scheduled_total",
        "metric_value": 1,
        "unit": "count",
        "adapter_key": adapter_key,
        "capability": capability,
        "error_category": error_category,
        "error_code": error_code,
        "failure_phase": failure_phase,
        "attempt_index": attempt_index,
        "policy": {
            "retry": {"max_attempts": policy.retry.max_attempts, "backoff_ms": policy.retry.backoff_ms},
        },
        "occurred_at": occurred_at,
    }
    return log_event, metric_sample


def build_attempt_lifecycle_observability(
    attempt_outcome_ref: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    task_id = str(attempt_outcome_ref.get("task_id") or "")
    adapter_key = str(attempt_outcome_ref.get("adapter_key") or "")
    capability = str(attempt_outcome_ref.get("capability") or "")
    attempt_index = attempt_outcome_ref.get("attempt_index")
    if isinstance(attempt_index, bool) or not isinstance(attempt_index, int) or attempt_index < 0:
        attempt_index = 0
    started_at = str(attempt_outcome_ref.get("started_at") or "")
    ended_at = str(attempt_outcome_ref.get("ended_at") or started_at)
    outcome = str(attempt_outcome_ref.get("outcome") or "")
    duration_ms = 0
    try:
        started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        ended = datetime.fromisoformat(ended_at.replace("Z", "+00:00"))
        duration_ms = max(0, int((ended - started).total_seconds() * 1000))
    except ValueError:
        duration_ms = 0
    runtime_refs = [dict(attempt_outcome_ref)]
    log_events = [
        {
            "event_id": f"runtime_log:{task_id}:attempt_started:{attempt_index}",
            "task_id": task_id,
            "adapter_key": adapter_key,
            "capability": capability,
            "event_type": "attempt_started",
            "level": "info",
            "attempt_index": attempt_index,
            "failure_signal_id": "",
            "resource_trace_refs": [],
            "runtime_result_refs": runtime_refs,
            "message": f"attempt {attempt_index} started",
            "occurred_at": started_at,
        },
        {
            "event_id": f"runtime_log:{task_id}:attempt_finished:{attempt_index}",
            "task_id": task_id,
            "adapter_key": adapter_key,
            "capability": capability,
            "event_type": "attempt_finished",
            "level": "error" if outcome in {"failed", "timeout"} else "info",
            "attempt_index": attempt_index,
            "failure_signal_id": "",
            "resource_trace_refs": [],
            "runtime_result_refs": runtime_refs,
            "message": f"attempt {attempt_index} finished: {outcome or 'unknown'}",
            "occurred_at": ended_at,
        },
    ]
    metric_samples = [
        {
            "metric_id": f"runtime_metric:{task_id}:attempt_started_total:{attempt_index}",
            "task_id": task_id,
            "metric_name": "attempt_started_total",
            "metric_value": 1,
            "unit": "count",
            "adapter_key": adapter_key,
            "capability": capability,
            "error_category": "",
            "error_code": "",
            "failure_phase": "",
            "attempt_index": attempt_index,
            "occurred_at": started_at,
        },
        {
            "metric_id": f"runtime_metric:{task_id}:execution_duration_ms:{attempt_index}",
            "task_id": task_id,
            "metric_name": "execution_duration_ms",
            "metric_value": duration_ms,
            "unit": "ms",
            "adapter_key": adapter_key,
            "capability": capability,
            "error_category": "",
            "error_code": "",
            "failure_phase": "",
            "attempt_index": attempt_index,
            "occurred_at": ended_at,
        },
    ]
    return log_events, metric_samples


def with_observability_write_failed(
    envelope: Mapping[str, Any],
    *,
    stage: str,
    reason: str,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    enriched = dict(envelope)
    task_id = str(enriched.get("task_id") or "")
    adapter_key = str(enriched.get("adapter_key") or "")
    capability = str(enriched.get("capability") or "")
    failure_signal = enriched.get("runtime_failure_signal") if isinstance(enriched.get("runtime_failure_signal"), Mapping) else {}
    resource_trace_refs = list(
        failure_signal.get("resource_trace_refs") if isinstance(failure_signal.get("resource_trace_refs"), list) else []
    )
    occurred_at = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    event = {
        "event_id": f"runtime_log:{task_id}:observability_write_failed:{stage}",
        "task_id": task_id,
        "adapter_key": adapter_key,
        "capability": capability,
        "event_type": "observability_write_failed",
        "level": "error",
        "attempt_index": infer_attempt_index(
            list(enriched.get("runtime_result_refs") if isinstance(enriched.get("runtime_result_refs"), list) else [])
        ),
        "failure_signal_id": str(failure_signal.get("signal_id") or ""),
        "resource_trace_refs": resource_trace_refs,
        "runtime_result_refs": list(
            enriched.get("runtime_result_refs") if isinstance(enriched.get("runtime_result_refs"), list) else []
        ),
        "message": f"observability write failed during {stage}: {reason}",
        "details": dict(details or {}),
        "occurred_at": occurred_at,
    }
    existing_events = list(
        enriched.get("runtime_structured_log_events")
        if isinstance(enriched.get("runtime_structured_log_events"), list)
        else []
    )
    enriched["runtime_structured_log_events"] = [*existing_events, event]
    return enriched


def with_failure_observability(envelope: Mapping[str, Any]) -> dict[str, Any]:
    if envelope.get("status") != "failed" or not isinstance(envelope.get("error"), Mapping):
        return dict(envelope)

    enriched = dict(envelope)
    error = dict(enriched["error"])
    details = dict(error.get("details") if isinstance(error.get("details"), Mapping) else {})
    task_id = str(enriched.get("task_id") or "")
    adapter_key = str(enriched.get("adapter_key") or "")
    capability = str(enriched.get("capability") or "")
    error_category = str(error.get("category") or "")
    error_code = str(error.get("code") or "")
    task_record_ref = details.get("task_record_ref")
    if not isinstance(task_record_ref, str) or not task_record_ref:
        task_record_ref = "none"
    runtime_result_refs = list(enriched.get("runtime_result_refs") if isinstance(enriched.get("runtime_result_refs"), list) else [])
    resource_trace_refs = list(details.get("resource_trace_refs") if isinstance(details.get("resource_trace_refs"), list) else [])
    failure_phase = infer_failure_phase(error_category=error_category, error_code=error_code, details=details)
    event_type = infer_failure_log_event_type(
        error_category=error_category,
        error_code=error_code,
        details=details,
        task_record_ref=task_record_ref,
    )
    metric_name = infer_failure_metric_name(event_type=event_type, failure_phase=failure_phase)
    attempt_index = infer_attempt_index(runtime_result_refs)
    signal_id = f"runtime_failure_signal:{task_id}:{error_category}:{error_code}:{failure_phase}:{attempt_index}"
    envelope_ref = f"failed_envelope:{task_id}:{error_category}:{error_code}:{attempt_index}"
    existing_failure_signal = (
        enriched.get("runtime_failure_signal") if isinstance(enriched.get("runtime_failure_signal"), Mapping) else {}
    )
    existing_log_events = list(
        enriched.get("runtime_structured_log_events")
        if isinstance(enriched.get("runtime_structured_log_events"), list)
        else []
    )
    existing_metric_samples = list(
        enriched.get("runtime_execution_metric_samples")
        if isinstance(enriched.get("runtime_execution_metric_samples"), list)
        else []
    )
    signal_occurred_at = stable_observability_occurred_at(
        existing_failure_signal,
        id_field="signal_id",
        entry_id=signal_id,
    )
    log_id = f"runtime_log:{task_id}:task_failed:{error_category}:{error_code}:{attempt_index}"
    metric_id = f"runtime_metric:{task_id}:{metric_name}:{error_category}:{error_code}:{attempt_index}"
    log_occurred_at = stable_observability_occurred_at(
        next((event for event in existing_log_events if isinstance(event, Mapping) and event.get("event_id") == log_id), {}),
        id_field="event_id",
        entry_id=log_id,
    )
    metric_occurred_at = stable_observability_occurred_at(
        next((metric for metric in existing_metric_samples if isinstance(metric, Mapping) and metric.get("metric_id") == metric_id), {}),
        id_field="metric_id",
        entry_id=metric_id,
    )
    failure_signal = {
        "signal_id": signal_id,
        "task_id": task_id,
        "adapter_key": adapter_key,
        "capability": capability,
        "status": "failed",
        "error_category": error_category,
        "error_code": error_code,
        "failure_phase": failure_phase,
        "envelope_ref": envelope_ref,
        "task_record_ref": task_record_ref,
        "resource_trace_refs": resource_trace_refs,
        "runtime_result_refs": runtime_result_refs,
        "occurred_at": signal_occurred_at,
    }
    log_event = {
        "event_id": log_id,
        "task_id": task_id,
        "adapter_key": adapter_key,
        "capability": capability,
        "event_type": event_type,
        "level": "error",
        "attempt_index": attempt_index,
        "failure_signal_id": signal_id,
        "resource_trace_refs": resource_trace_refs,
        "runtime_result_refs": runtime_result_refs,
        "message": f"task failed: {error_category}/{error_code}",
        "occurred_at": log_occurred_at,
    }
    metric_sample = {
        "metric_id": metric_id,
        "task_id": task_id,
        "metric_name": metric_name,
        "metric_value": 1,
        "unit": "count",
        "adapter_key": adapter_key,
        "capability": capability,
        "error_category": error_category,
        "error_code": error_code,
        "failure_phase": failure_phase,
        "attempt_index": attempt_index,
        "occurred_at": metric_occurred_at,
    }
    enriched["runtime_failure_signal"] = failure_signal
    retained_log_events = [
        event
        for event in existing_log_events
        if isinstance(event, Mapping)
        and event.get("event_type")
        in {"attempt_started", "attempt_finished", "retry_scheduled", "observability_write_failed"}
    ]
    retained_metric_samples = [
        metric
        for metric in existing_metric_samples
        if isinstance(metric, Mapping)
        and metric.get("metric_name") in {"attempt_started_total", "execution_duration_ms", "retry_scheduled_total"}
    ]
    enriched["runtime_structured_log_events"] = [*retained_log_events, log_event]
    enriched["runtime_execution_metric_samples"] = [*retained_metric_samples, metric_sample]
    return enriched


def stable_observability_occurred_at(entry: Mapping[str, Any], *, id_field: str, entry_id: str) -> str:
    if entry.get(id_field) == entry_id and isinstance(entry.get("occurred_at"), str) and entry["occurred_at"]:
        return str(entry["occurred_at"])
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def infer_failure_phase(*, error_category: str, error_code: str, details: Mapping[str, Any]) -> str:
    event = details.get("execution_control_event")
    if isinstance(event, Mapping):
        event_type = event.get("event_type")
        if event_type in {EXECUTION_CONTROL_EVENT_ADMISSION_CONCURRENCY_REJECTED, EXECUTION_CONTROL_EVENT_RETRY_CONCURRENCY_REJECTED}:
            return "concurrency_rejected"
        if event_type == EXECUTION_CONTROL_EVENT_RETRY_EXHAUSTED:
            return "retry_exhausted"
    if details.get("retry_exhausted") is True:
        return "retry_exhausted"
    if error_code == EXECUTION_CONTROL_CODE_CONCURRENCY_LIMIT_EXCEEDED:
        return "concurrency_rejected"
    if error_code == EXECUTION_CONTROL_CODE_EXECUTION_CONTROL_STATE_INVALID:
        if details.get("control_context") == "guarded_admission" or (
            details.get("control_code") == EXECUTION_CONTROL_CODE_CONCURRENCY_LIMIT_EXCEEDED
        ):
            return "concurrency_rejected"
        if details.get("stage") == "pre_execution" or details.get("control_context") == "default_execution_control_policy":
            return "pre_execution"
    if details.get("stage") == "pre_admission":
        return "admission"
    if details.get("stage") == "pre_execution":
        return "pre_execution"
    if is_normal_execution_timeout_failure(error_category=error_category, error_code=error_code, details=details):
        return "timeout"
    if error_code in {"resource_unavailable", "invalid_resource_requirement"}:
        return "resource_acquire"
    if error_code in {"envelope_not_json_serializable", "task_record_conflict", "task_record_persistence_failed"}:
        return "persistence"
    if details.get("stage") in {"accepted", "running", "completion", "persist_accepted", "persist_running"}:
        return "persistence"
    if error_code in {"adapter_not_found", "capability_not_supported", "target_type_not_supported", "collection_mode_not_supported"}:
        return "admission"
    if error_code in {"invalid_adapter_success_payload", "adapter_execution_error"}:
        return "adapter_execution"
    if error_category == "runtime_contract":
        return "adapter_execution"
    return "adapter_execution"


def is_normal_execution_timeout_failure(*, error_category: str, error_code: str, details: Mapping[str, Any]) -> bool:
    return (
        error_category == "platform"
        and error_code == EXECUTION_CONTROL_CODE_EXECUTION_TIMEOUT
        and details.get("control_code") == EXECUTION_CONTROL_CODE_EXECUTION_TIMEOUT
    )


def infer_failure_log_event_type(*, error_category: str, error_code: str, details: Mapping[str, Any], task_record_ref: str) -> str:
    event = details.get("execution_control_event")
    if isinstance(event, Mapping):
        event_type = event.get("event_type")
        if event_type in {
            EXECUTION_CONTROL_EVENT_ADMISSION_CONCURRENCY_REJECTED,
            EXECUTION_CONTROL_EVENT_RETRY_CONCURRENCY_REJECTED,
        }:
            return str(event_type)
    if error_code == EXECUTION_CONTROL_CODE_CONCURRENCY_LIMIT_EXCEEDED and task_record_ref == "none":
        return EXECUTION_CONTROL_EVENT_ADMISSION_CONCURRENCY_REJECTED
    if is_normal_execution_timeout_failure(error_category=error_category, error_code=error_code, details=details):
        return "timeout_triggered"
    return "task_failed"


def infer_failure_metric_name(*, event_type: str, failure_phase: str) -> str:
    if event_type == EXECUTION_CONTROL_EVENT_ADMISSION_CONCURRENCY_REJECTED:
        return "admission_concurrency_rejected_total"
    if event_type == EXECUTION_CONTROL_EVENT_RETRY_CONCURRENCY_REJECTED:
        return "retry_concurrency_rejected_total"
    if failure_phase == "timeout":
        return "timeout_total"
    return "task_failed_total"


def infer_attempt_index(runtime_result_refs: list[Any]) -> int:
    for entry in reversed(runtime_result_refs):
        if isinstance(entry, Mapping):
            attempt_index = entry.get("attempt_index")
            if isinstance(attempt_index, int) and attempt_index >= 0:
                return attempt_index
    return 0


def with_failed_envelope_control_details(
    envelope: Mapping[str, Any],
    *,
    event: Mapping[str, Any],
    details: Mapping[str, Any],
) -> dict[str, Any]:
    enriched = dict(envelope)
    error = dict(enriched.get("error") if isinstance(enriched.get("error"), Mapping) else {})
    current_details = dict(error.get("details") if isinstance(error.get("details"), Mapping) else {})
    current_details.update(details)
    current_details["execution_control_event"] = dict(event)
    error["details"] = current_details
    enriched["error"] = error
    return enriched


def is_synthetic_retry_concurrency_rejection(envelope: Mapping[str, Any]) -> bool:
    error = envelope.get("error") if isinstance(envelope.get("error"), Mapping) else {}
    details = error.get("details") if isinstance(error.get("details"), Mapping) else {}
    return (
        error.get("category") == "runtime_contract"
        and error.get("code") == EXECUTION_CONTROL_CODE_EXECUTION_CONTROL_STATE_INVALID
        and details.get("control_context") == "guarded_admission"
        and details.get("control_code") == EXECUTION_CONTROL_CODE_CONCURRENCY_LIMIT_EXCEEDED
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
    envelope = (
        with_failure_observability(
            with_failed_envelope_task_record_ref(envelope, record.task_record_ref or f"task_record:{task_id}")
        )
        if envelope.get("status") == "failed"
        else dict(envelope)
    )
    try:
        terminal_record = finish_task_record(record, envelope)
    except TaskRecordContractError as error:
        invalidation_details: dict[str, Any] = {}
        try:
            task_record_store.mark_invalid(task_id, stage="completion", reason=str(error))
        except (AttributeError, TaskRecordContractError, TaskRecordStoreError, OSError) as invalidation_error:
            invalidation_details["invalidation_reason"] = str(invalidation_error)
        except Exception as invalidation_error:
            invalidation_details["invalidation_reason"] = str(invalidation_error)
        if preserve_envelope_on_record_error and task_record_store is None:
            return TaskExecutionResult(public_task_execution_envelope(envelope), None)
        if envelope.get("status") == "failed":
            return TaskExecutionResult(
                with_observability_write_failed(envelope, stage="completion", reason=str(error), details=invalidation_details),
                None,
            )
        failed_envelope = failure_envelope(
            task_id,
            adapter_key,
            capability,
            runtime_contract_error(
                "envelope_not_json_serializable",
                "共享终态结果无法收口为 JSON-safe TaskRecord",
                details={"reason": str(error), **invalidation_details},
            ),
        )
        return TaskExecutionResult(
            with_failure_observability(
                with_failed_envelope_task_record_ref(
                    failed_envelope,
                    record.task_record_ref or f"task_record:{task_id}",
                )
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
        if envelope.get("status") == "failed":
            reason = persistence_error.envelope.get("error", {}).get("details", {}).get("reason", "")
            return TaskExecutionResult(
                with_observability_write_failed(
                    envelope,
                    stage="completion",
                    reason=str(reason),
                    details=dict(persistence_error.envelope.get("error", {}).get("details", {})),
                ),
                None,
            )
        return persistence_error
    return TaskExecutionResult(public_task_execution_envelope(envelope), persisted_record or terminal_record)


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
        envelope = failure_envelope(
            task_id,
            adapter_key,
            capability,
            runtime_contract_error(
                "task_record_conflict",
                "共享任务记录写入与既有 durable truth 冲突",
                details={"stage": stage, "reason": str(error)},
            ),
        )
        if stage in {"running", "completion"}:
            envelope = with_failed_envelope_task_record_ref(envelope, record.task_record_ref or f"task_record:{task_id}")
        return None, TaskExecutionResult(
            with_failure_observability(envelope),
            None,
        )
    except (TaskRecordContractError, TaskRecordStoreError, OSError) as error:
        return _fail_closed_task_record_persistence(
            task_id,
            adapter_key,
            capability,
            stage=stage,
            task_record_store=task_record_store,
            task_record_ref=record.task_record_ref or f"task_record:{task_id}" if stage in {"running", "completion"} else None,
            error=error,
        )
    except Exception as error:
        return _fail_closed_task_record_persistence(
            task_id,
            adapter_key,
            capability,
            stage=stage,
            task_record_store=task_record_store,
            task_record_ref=record.task_record_ref or f"task_record:{task_id}" if stage in {"running", "completion"} else None,
            error=error,
        )


def _fail_closed_task_record_persistence(
    task_id: str,
    adapter_key: str,
    capability: str,
    *,
    stage: str,
    task_record_store: TaskRecordStore,
    task_record_ref: str | None,
    error: Exception,
) -> tuple[TaskRecord | None, TaskExecutionResult | None]:
    invalidation_details: dict[str, Any] = {}
    try:
        task_record_store.mark_invalid(task_id, stage=stage, reason=str(error))
    except (AttributeError, TaskRecordContractError, TaskRecordStoreError, OSError) as invalidation_error:
        invalidation_details["invalidation_reason"] = str(invalidation_error)
    except Exception as invalidation_error:
        invalidation_details["invalidation_reason"] = str(invalidation_error)
    details = {"stage": stage, "reason": str(error), **invalidation_details}
    if task_record_ref:
        details["task_record_ref"] = task_record_ref
    return None, TaskExecutionResult(
        with_failure_observability(failure_envelope(
            task_id,
            adapter_key,
            capability,
            runtime_contract_error(
                "task_record_persistence_failed",
                "共享任务记录无法可靠写入本地稳定存储",
                details=details,
            ),
        )),
        None,
    )


def validate_request(request: Any) -> dict[str, Any] | None:
    _, error = normalize_request(request)
    return error


def normalize_request(request: Any) -> tuple[CoreTaskRequest | None, dict[str, Any] | None]:
    if type(request) is TaskRequest:
        if not isinstance(request.adapter_key, str) or not request.adapter_key:
            return None, invalid_input_error("invalid_task_request", "adapter_key 不能为空")
        if type(request.input) is not TaskInput:
            return None, invalid_input_error("invalid_task_request", "input 必须为对象")
        operation_error = _validate_runtime_operation(request.capability)
        if operation_error is not None:
            return None, operation_error
        execution_control_error = validate_execution_control_policy(request.execution_control_policy)
        if execution_control_error is not None:
            return None, execution_control_error
        execution_control_policy = request.execution_control_policy or default_execution_control_policy()
        target, policy, input_error = _project_task_input_to_target(
            adapter_key=request.adapter_key,
            capability=request.capability,
            input_value=request.input,
        )
        if input_error is not None:
            return None, input_error
        return (
            CoreTaskRequest(
                target=target,
                policy=policy,
                execution_control_policy=execution_control_policy,
                request_cursor=request.input.comment_request_cursor if request.capability == COMMENT_COLLECTION else None,
            ),
            None,
        )
    if type(request) is not CoreTaskRequest:
        return None, invalid_input_error("invalid_task_request", "task_request 顶层形状不合法")
    if type(request.target) is not InputTarget:
        return None, invalid_input_error("invalid_task_request", "target 必须为对象")
    if type(request.policy) is not CollectionPolicy:
        return None, invalid_input_error("invalid_task_request", "policy 必须为对象")
    execution_control_error = validate_execution_control_policy(request.execution_control_policy)
    if execution_control_error is not None:
        return None, execution_control_error

    target = request.target
    policy = request.policy
    if not isinstance(target.adapter_key, str) or not target.adapter_key:
        return None, invalid_input_error("invalid_task_request", "adapter_key 不能为空")
    capability_error = _validate_runtime_operation(target.capability)
    if capability_error is not None:
        return None, capability_error
    if not isinstance(target.target_value, str) or not target.target_value:
        return None, invalid_input_error("invalid_task_request", "target_value 不能为空")
    if not isinstance(target.target_type, str) or target.target_type not in ALLOWED_TARGET_TYPES:
        return None, invalid_input_error("invalid_task_request", "target_type 不合法")
    if not isinstance(policy.collection_mode, str) or policy.collection_mode not in ALLOWED_COLLECTION_MODES:
        return None, invalid_input_error("invalid_task_request", "collection_mode 不合法")
    execution_control_policy = request.execution_control_policy or default_execution_control_policy()
    if execution_control_policy is request.execution_control_policy:
        return request, None
    return (
        CoreTaskRequest(
            target=request.target,
            policy=request.policy,
            execution_control_policy=execution_control_policy,
            request_cursor=request.request_cursor,
        ),
        None,
    )


def validate_execution_control_policy(policy: Any) -> dict[str, Any] | None:
    if policy is None:
        return None
    if type(policy) is not ExecutionControlPolicy:
        return invalid_input_error("invalid_execution_control_policy", "execution_control_policy 必须为共享 ExecutionControlPolicy")
    if type(policy.timeout) is not ExecutionTimeoutPolicy:
        return invalid_input_error("invalid_execution_control_policy", "execution_control_policy.timeout 必须为对象")
    if type(policy.retry) is not ExecutionRetryPolicy:
        return invalid_input_error("invalid_execution_control_policy", "execution_control_policy.retry 必须为对象")
    if type(policy.concurrency) is not ExecutionConcurrencyPolicy:
        return invalid_input_error("invalid_execution_control_policy", "execution_control_policy.concurrency 必须为对象")
    if isinstance(policy.timeout.timeout_ms, bool) or not isinstance(policy.timeout.timeout_ms, int) or policy.timeout.timeout_ms <= 0:
        return invalid_input_error("invalid_execution_control_policy", "execution_control_policy.timeout.timeout_ms 必须为正整数")
    if (
        isinstance(policy.retry.max_attempts, bool)
        or not isinstance(policy.retry.max_attempts, int)
        or policy.retry.max_attempts < 1
    ):
        return invalid_input_error("invalid_execution_control_policy", "execution_control_policy.retry.max_attempts 必须为正整数")
    if isinstance(policy.retry.backoff_ms, bool) or not isinstance(policy.retry.backoff_ms, int) or policy.retry.backoff_ms < 0:
        return invalid_input_error("invalid_execution_control_policy", "execution_control_policy.retry.backoff_ms 必须为非负整数")
    if (
        not isinstance(policy.concurrency.scope, str)
        or policy.concurrency.scope not in ALLOWED_EXECUTION_CONTROL_CONCURRENCY_SCOPES
    ):
        return invalid_input_error(
            "invalid_execution_control_policy",
            "execution_control_policy.concurrency.scope 不在共享 contract 批准值域内",
            details={"allowed_scopes": sorted(ALLOWED_EXECUTION_CONTROL_CONCURRENCY_SCOPES)},
        )
    if (
        isinstance(policy.concurrency.max_in_flight, bool)
        or not isinstance(policy.concurrency.max_in_flight, int)
        or policy.concurrency.max_in_flight < 1
    ):
        return invalid_input_error(
            "invalid_execution_control_policy",
            "execution_control_policy.concurrency.max_in_flight 必须为正整数",
        )
    if not isinstance(policy.concurrency.on_limit, str) or policy.concurrency.on_limit != "reject":
        return invalid_input_error("invalid_execution_control_policy", "execution_control_policy.concurrency.on_limit 当前仅支持 reject")
    return None


def resolve_capability_family(capability: str) -> tuple[str | None, dict[str, Any] | None]:
    mapped = CAPABILITY_FAMILY_BY_OPERATION.get(capability)
    if mapped is None:
        return (
            None,
            invalid_input_error(
                "invalid_capability",
                "capability 不在当前稳定 runtime contract 允许值范围内",
                details={"allowed_capabilities": sorted(CAPABILITY_FAMILY_BY_OPERATION)},
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
            request_cursor=clone_request_cursor(request.request_cursor) if request.target.capability == COMMENT_COLLECTION else None,
        ),
        None,
    )


def clone_request_cursor(request_cursor: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    if request_cursor is None:
        return None
    if isinstance(request_cursor, CommentRequestCursor):
        return comment_request_cursor_to_dict(request_cursor)
    return copy.deepcopy(request_cursor)


def validate_projection_axes_for_current_runtime(request: CoreTaskRequest) -> dict[str, Any] | None:
    try:
        stable = stable_operation_entry(
            operation=request.target.capability,
            target_type=request.target.target_type,
            collection_mode=request.policy.collection_mode,
        )
    except Exception:
        return invalid_input_error(
            "invalid_task_request",
            "请求执行切片不在当前稳定 runtime contract 内",
            details={
                "operation": request.target.capability,
                "target_type": request.target.target_type,
                "collection_mode": request.policy.collection_mode,
            },
        )
    if not stable.runtime_delivery:
        return invalid_input_error(
            "invalid_task_request",
            "请求执行切片尚未进入 runtime stable delivery",
            details={
                "operation": stable.operation,
                "target_type": stable.target_type,
                "collection_mode": stable.collection_mode,
            },
        )
    return None


def _validate_runtime_operation(capability: str) -> dict[str, Any] | None:
    if capability in CAPABILITY_FAMILY_BY_OPERATION:
        return None
    return invalid_input_error(
        "invalid_capability",
        "capability 不在当前稳定 runtime contract 允许值范围内",
        details={"allowed_capabilities": sorted(CAPABILITY_FAMILY_BY_OPERATION)},
    )


def _project_task_input_to_target(
    *,
    adapter_key: str,
    capability: str,
    input_value: TaskInput,
) -> tuple[InputTarget, CollectionPolicy, dict[str, Any] | None]:
    if capability == CONTENT_DETAIL_BY_URL:
        if not isinstance(input_value.url, str) or not input_value.url:
            return (
                InputTarget(adapter_key=adapter_key, capability=capability, target_type="url", target_value=""),
                CollectionPolicy(collection_mode=LEGACY_COLLECTION_MODE),
                invalid_input_error("invalid_task_request", "input.url 不能为空"),
            )
        return (
            InputTarget(adapter_key=adapter_key, capability=capability, target_type="url", target_value=input_value.url),
            CollectionPolicy(collection_mode=LEGACY_COLLECTION_MODE),
            None,
        )
    if capability == CONTENT_SEARCH_BY_KEYWORD:
        if not isinstance(input_value.keyword, str) or not input_value.keyword:
            return (
                InputTarget(adapter_key=adapter_key, capability=capability, target_type="keyword", target_value=""),
                CollectionPolicy(collection_mode=PAGINATED_COLLECTION_MODE),
                invalid_input_error("invalid_task_request", "input.keyword 不能为空"),
            )
        return (
            InputTarget(adapter_key=adapter_key, capability=capability, target_type="keyword", target_value=input_value.keyword),
            CollectionPolicy(collection_mode=PAGINATED_COLLECTION_MODE),
            None,
        )
    if capability == CONTENT_LIST_BY_CREATOR:
        if not isinstance(input_value.creator_id, str) or not input_value.creator_id:
            return (
                InputTarget(adapter_key=adapter_key, capability=capability, target_type="creator", target_value=""),
                CollectionPolicy(collection_mode=PAGINATED_COLLECTION_MODE),
                invalid_input_error("invalid_task_request", "input.creator_id 不能为空"),
            )
        return (
            InputTarget(adapter_key=adapter_key, capability=capability, target_type="creator", target_value=input_value.creator_id),
            CollectionPolicy(collection_mode=PAGINATED_COLLECTION_MODE),
            None,
        )
    if capability == COMMENT_COLLECTION:
        if not isinstance(input_value.content_ref, str) or not input_value.content_ref:
            return (
                InputTarget(adapter_key=adapter_key, capability=capability, target_type="content", target_value=""),
                CollectionPolicy(collection_mode=PAGINATED_COLLECTION_MODE),
                invalid_input_error("invalid_task_request", "input.content_ref 不能为空"),
            )
        return (
            InputTarget(
                adapter_key=adapter_key,
                capability=capability,
                target_type="content",
                target_value=input_value.content_ref,
            ),
            CollectionPolicy(collection_mode=PAGINATED_COLLECTION_MODE),
            None,
        )
    return (
        InputTarget(adapter_key=adapter_key, capability=capability, target_type="", target_value=""),
        CollectionPolicy(collection_mode=LEGACY_COLLECTION_MODE),
        invalid_input_error("invalid_capability", "capability 不在当前稳定 runtime contract 允许值范围内"),
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
    available_resource_capabilities = frozenset(validated_input.available_resource_capabilities)
    if _requirement_declaration_is_satisfied(
        validated_input.requirement_declaration,
        available_resource_capabilities=available_resource_capabilities,
    ):
        match_status = MATCH_STATUS_MATCHED
    else:
        match_status = MATCH_STATUS_UNMATCHED
    return ResourceCapabilityMatchResult(
        task_id=validated_input.task_id,
        adapter_key=validated_input.adapter_key,
        capability=validated_input.capability,
        match_status=match_status,
    )


def _requirement_declaration_is_satisfied(
    declaration: AdapterResourceRequirementDeclaration | AdapterResourceRequirementDeclarationV2,
    *,
    available_resource_capabilities: frozenset[str],
) -> bool:
    if type(declaration) is AdapterResourceRequirementDeclarationV2:
        return any(
            _requirement_profile_is_satisfied(
                profile,
                available_resource_capabilities=available_resource_capabilities,
            )
            for profile in declaration.resource_requirement_profiles
        )
    required_capabilities = frozenset(declaration.required_capabilities)
    return required_capabilities.issubset(available_resource_capabilities)


def _requirement_profile_is_satisfied(
    profile: AdapterResourceRequirementProfile,
    *,
    available_resource_capabilities: frozenset[str],
) -> bool:
    if profile.resource_dependency_mode == RESOURCE_DEPENDENCY_MODE_NONE:
        return True
    return frozenset(profile.required_capabilities).issubset(available_resource_capabilities)


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


def validate_success_payload(
    payload: Mapping[str, Any],
    *,
    capability: str | None = None,
    target_type: str | None = None,
    target_value: str | None = None,
    request_cursor: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not isinstance(payload, Mapping):
        return runtime_contract_error(
            "invalid_adapter_success_payload",
            "adapter 成功结果必须是对象",
        )
    if capability in READ_SIDE_COLLECTION_OPERATIONS:
        if target_type is None or target_value is None:
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                "collection success validation requires target_type and target_value",
            )
        try:
            envelope = collection_result_envelope_from_dict(payload)
        except CollectionContractError as error:
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                error.message,
                details={"reason": error.code, **error.details},
            )
        if envelope.operation != capability:
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                "collection result.operation 必须与请求 capability 一致",
                details={"operation": envelope.operation, "capability": capability},
            )
        if envelope.target.target_type != target_type:
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                "collection result.target.target_type 必须与请求一致",
                details={"target_type": envelope.target.target_type, "expected_target_type": target_type},
            )
        if envelope.target.target_ref != target_value:
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                "collection result.target.target_ref 必须与请求 target_value 一致",
                details={"target_ref": envelope.target.target_ref, "expected_target_ref": target_value},
            )
        return None
    if capability == COMMENT_COLLECTION:
        if target_type is None or target_value is None:
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                "comment collection success validation requires target_type and target_value",
            )
        try:
            envelope = comment_collection_result_envelope_from_dict(payload)
        except CollectionContractError as error:
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                error.message,
                details={"reason": error.code, **error.details},
            )
        if envelope.operation != capability:
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                "comment collection result.operation 必须与请求 capability 一致",
                details={"operation": envelope.operation, "capability": capability},
            )
        if envelope.target.target_type != target_type:
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                "comment collection result.target.target_type 必须与请求一致",
                details={"target_type": envelope.target.target_type, "expected_target_type": target_type},
            )
        if envelope.target.target_ref != target_value:
            return runtime_contract_error(
                "invalid_adapter_success_payload",
                "comment collection result.target.target_ref 必须与请求 target_value 一致",
                details={"target_ref": envelope.target.target_ref, "expected_target_ref": target_value},
            )
        cursor_thread_ref = _comment_request_cursor_thread_ref(request_cursor)
        if cursor_thread_ref is None and _comment_request_cursor_is_top_level_page(request_cursor):
            if envelope.next_continuation is not None and envelope.next_continuation.resume_comment_ref is not None:
                return runtime_contract_error(
                    "invalid_adapter_success_payload",
                    "top-level comment page cursor 不得切换为 reply thread continuation",
                    details={
                        "reason": "cursor_invalid_or_expired",
                        "resume_comment_ref": envelope.next_continuation.resume_comment_ref,
                    },
                )
        if cursor_thread_ref is not None:
            if envelope.next_continuation is not None and envelope.next_continuation.resume_comment_ref is None:
                return runtime_contract_error(
                    "invalid_adapter_success_payload",
                    "comment collection next_continuation 必须保留请求 cursor 的 comment thread",
                    details={
                        "reason": "invalid_comment_collection_contract",
                        "resume_comment_ref": cursor_thread_ref,
                    },
                )
            drifted_items = tuple(
                item.normalized.canonical_ref
                for item in envelope.items
                if not _comment_item_binds_resume_comment_ref(item, cursor_thread_ref)
            )
            if drifted_items:
                return runtime_contract_error(
                    "invalid_adapter_success_payload",
                    "comment collection result items 必须绑定请求 cursor 的 comment thread",
                    details={
                        "reason": "cursor_invalid_or_expired",
                        "resume_comment_ref": cursor_thread_ref,
                        "drifted_item_refs": drifted_items,
                    },
                )
            if (
                envelope.next_continuation is not None
                and envelope.next_continuation.resume_comment_ref is not None
                and envelope.next_continuation.resume_comment_ref != cursor_thread_ref
            ):
                return runtime_contract_error(
                    "invalid_adapter_success_payload",
                    "comment collection next_continuation 必须绑定请求 cursor 的 comment thread",
                    details={
                        "reason": "cursor_invalid_or_expired",
                        "resume_comment_ref": cursor_thread_ref,
                        "next_resume_comment_ref": envelope.next_continuation.resume_comment_ref,
                    },
                )
        return None

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


def _comment_item_binds_resume_comment_ref(item: Any, resume_comment_ref: str) -> bool:
    normalized = item.normalized
    return (
        normalized.root_comment_ref == resume_comment_ref
        or normalized.parent_comment_ref == resume_comment_ref
        or (
            normalized.parent_comment_ref != normalized.root_comment_ref
            and normalized.target_comment_ref == resume_comment_ref
        )
    )


def _comment_request_cursor_is_top_level_page(request_cursor: Any | None) -> bool:
    if request_cursor is None:
        return True
    if isinstance(request_cursor, Mapping):
        page_continuation = request_cursor.get("page_continuation")
        reply_cursor = request_cursor.get("reply_cursor")
    else:
        page_continuation = getattr(request_cursor, "page_continuation", None)
        reply_cursor = getattr(request_cursor, "reply_cursor", None)
    if reply_cursor is not None:
        return False
    if page_continuation is None:
        return True
    if isinstance(page_continuation, Mapping):
        value = page_continuation.get("resume_comment_ref")
    else:
        value = getattr(page_continuation, "resume_comment_ref", None)
    return value is None


def _comment_request_cursor_thread_ref(request_cursor: Any | None) -> str | None:
    if isinstance(request_cursor, Mapping):
        reply_cursor = request_cursor.get("reply_cursor")
        page_continuation = request_cursor.get("page_continuation")
    else:
        reply_cursor = getattr(request_cursor, "reply_cursor", None)
        page_continuation = getattr(request_cursor, "page_continuation", None)
    if isinstance(reply_cursor, Mapping):
        value = reply_cursor.get("resume_comment_ref")
        return value if isinstance(value, str) and value else None
    value = getattr(reply_cursor, "resume_comment_ref", None)
    if isinstance(value, str) and value:
        return value
    if isinstance(page_continuation, Mapping):
        value = page_continuation.get("resume_comment_ref")
        return value if isinstance(value, str) and value else None
    value = getattr(page_continuation, "resume_comment_ref", None)
    if isinstance(value, str) and value:
        return value
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
) -> AdapterResourceRequirementDeclaration | AdapterResourceRequirementDeclarationV2:
    if type(raw_value) not in {AdapterResourceRequirementDeclaration, AdapterResourceRequirementDeclarationV2}:
        raise ResourceCapabilityMatcherContractError(
            "matcher requirement_declaration 必须是 canonical AdapterResourceRequirementDeclaration carrier",
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

    if type(raw_value) is AdapterResourceRequirementDeclarationV2:
        return _validate_matcher_requirement_declaration_v2(
            raw_value,
            expected_adapter_key=expected_adapter_key,
            expected_capability=expected_capability,
            task_id=task_id,
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
        approved_evidence_refs = approved_resource_requirement_evidence_refs_for(
            adapter_key=adapter_key,
            capability=capability,
        )
        unknown_evidence_refs = tuple(
            evidence_ref
            for evidence_ref in evidence_refs
            if evidence_ref not in approved_evidence_refs
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


def _validate_matcher_requirement_declaration_v2(
    raw_value: AdapterResourceRequirementDeclarationV2,
    *,
    expected_adapter_key: str,
    expected_capability: str,
    task_id: str,
) -> AdapterResourceRequirementDeclarationV2:
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
            "matcher requirement_declaration 必须满足 FR-0027 canonical contract",
            details={
                "task_id": task_id,
                "adapter_key": expected_adapter_key,
                "capability": expected_capability,
                "registry_error_code": error.code,
                **error.details,
            },
        ) from error

    validated_requirement = registry.lookup_resource_requirement(expected_adapter_key, expected_capability)
    if type(validated_requirement) is not AdapterResourceRequirementDeclarationV2:
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


def _requested_adapter_resource_requirement_error(
    *,
    adapters: Mapping[str, Any],
    adapter_key: str,
    error: RegistryError,
) -> dict[str, Any] | None:
    if error.code != "invalid_adapter_resource_requirements":
        return None
    if error.details.get("adapter_key") == adapter_key:
        return invalid_resource_requirement_error(
            error.message,
            details={"registry_error_code": error.code, **error.details},
        )

    try:
        requested_adapter = adapters[adapter_key]
    except Exception:
        return None

    try:
        AdapterRegistry.from_mapping({adapter_key: requested_adapter})
    except RegistryError as requested_error:
        if requested_error.code != "invalid_adapter_resource_requirements":
            return None
        return invalid_resource_requirement_error(
            requested_error.message,
            details={
                "registry_error_code": requested_error.code,
                **requested_error.details,
            },
        )
    return None


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
