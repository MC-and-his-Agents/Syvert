from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
import json
from typing import Any
from urllib.parse import unquote

from syvert.runtime import (
    CONTENT_DETAIL_BY_URL,
    ExecutionConcurrencyPolicy,
    ExecutionControlPolicy,
    ExecutionRetryPolicy,
    ExecutionTimeoutPolicy,
    ALLOWED_EXECUTION_CONTROL_CONCURRENCY_SCOPES,
    TaskInput,
    TaskRequest,
    execute_task_with_record,
    failure_envelope,
    invalid_input_error,
    resolve_task_id,
    runtime_contract_error,
)
from syvert.task_record import TaskRecord, TaskRecordContractError, task_record_to_dict, validate_task_record
from syvert.task_record_store import (
    TaskRecordPersistenceError,
    TaskRecordStore,
    TaskRecordStoreError,
    default_task_record_store,
)


JSON_HEADERS = (("Content-Type", "application/json; charset=utf-8"),)
HTTP_STATUS_TEXT = {
    200: "OK",
    202: "Accepted",
    400: "Bad Request",
    404: "Not Found",
    409: "Conflict",
    500: "Internal Server Error",
}
SUBMIT_FIELDS = frozenset({"adapter_key", "capability", "target", "execution_control_policy"})


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    body: dict[str, Any]
    headers: tuple[tuple[str, str], ...] = JSON_HEADERS


class TaskHttpService:
    def __init__(
        self,
        adapters: Mapping[str, Any],
        *,
        task_record_store: TaskRecordStore | None = None,
        task_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._adapters = adapters
        self._task_record_store = task_record_store if task_record_store is not None else default_task_record_store()
        self._task_id_factory = task_id_factory

    def submit(self, payload: Mapping[str, Any]) -> HttpResponse:
        request, validation_error = self._build_task_request(payload)
        if validation_error is not None:
            return self._submit_failure(validation_error, status_code=400)

        task_id, task_id_error = self._resolve_http_task_id()
        if task_id_error is not None:
            return HttpResponse(500, self._task_failure("", task_id_error))
        outcome = execute_task_with_record(
            request,
            adapters=self._adapters,
            task_id_factory=lambda: task_id,
            task_record_store=self._task_record_store,
        )
        if outcome.task_record is not None:
            if outcome.task_record.task_id != task_id:
                return HttpResponse(
                    500,
                    self._task_failure(
                        task_id,
                        runtime_contract_error(
                            "invalid_task_id",
                            "Core 返回的 task_id 与 HTTP admission 预分配值不一致",
                            details={"reason": "task_id_mismatch"},
                        ),
                        record=outcome.task_record,
                    ),
                )
            return HttpResponse(
                202,
                {
                    "task_id": outcome.task_record.task_id,
                    "status": outcome.task_record.status,
                },
            )
        return HttpResponse(self._submit_failure_status_code(outcome.envelope), outcome.envelope)

    def status(self, task_id: str) -> HttpResponse:
        task_id_error = self._validate_task_id(task_id)
        if task_id_error is not None:
            return HttpResponse(400, self._task_failure(_envelope_task_id(task_id), task_id_error))

        record_response = self._load_record(task_id)
        if isinstance(record_response, HttpResponse):
            return record_response
        if isinstance(record_response, TaskRecord) and record_response.task_id != task_id:
            return self._record_unavailable_response(task_id, "task_record_id_mismatch", record=record_response)
        try:
            return HttpResponse(200, task_record_to_dict(record_response))
        except (AttributeError, TaskRecordContractError, TypeError, ValueError, OSError) as error:
            return self._record_unavailable_response(task_id, str(error) or error.__class__.__name__, record=record_response)

    def result(self, task_id: str) -> HttpResponse:
        task_id_error = self._validate_task_id(task_id)
        if task_id_error is not None:
            return HttpResponse(400, self._task_failure(_envelope_task_id(task_id), task_id_error))

        record_response = self._load_record(task_id)
        if isinstance(record_response, HttpResponse):
            return record_response
        record = record_response
        if isinstance(record, TaskRecord) and record.task_id != task_id:
            return self._record_unavailable_response(task_id, "task_record_id_mismatch", record=record)
        try:
            validate_task_record(record)
        except (AttributeError, TaskRecordContractError, TypeError, ValueError, OSError) as error:
            return self._record_unavailable_response(task_id, str(error) or error.__class__.__name__, record=record)
        if record.status in {"accepted", "running"}:
            return HttpResponse(
                409,
                self._task_failure(
                    task_id,
                    invalid_input_error(
                        "result_not_ready",
                        f"task_id `{task_id}` 尚未产生终态结果",
                    ),
                    record=record,
                ),
            )
        if record.result is None:
            return HttpResponse(
                500,
                self._task_failure(
                    task_id,
                    runtime_contract_error(
                        "task_record_unavailable",
                        f"task_id `{task_id}` 对应的持久化任务记录不可用",
                        details={"reason": "terminal_record_missing_result"},
                    ),
                    record=record,
                ),
            )
        return HttpResponse(200, _envelope_with_record_observability(record))

    def _build_task_request(self, payload: Mapping[str, Any]) -> tuple[TaskRequest | None, dict[str, Any] | None]:
        if not isinstance(payload, Mapping):
            return None, invalid_input_error("invalid_http_task_request", "HTTP task request 必须是 JSON object")
        unknown_fields = sorted(str(field) for field in payload.keys() if field not in SUBMIT_FIELDS)
        if unknown_fields:
            return None, invalid_input_error(
                "invalid_http_task_request",
                "HTTP task request 包含未批准字段",
                details={"unknown_fields": unknown_fields},
            )
        if "execution_control_policy" in payload:
            execution_control_policy, execution_control_error = _project_execution_control_policy(
                payload["execution_control_policy"]
            )
            if execution_control_error is not None:
                return None, execution_control_error
        else:
            execution_control_policy = None
        adapter_key = payload.get("adapter_key")
        if not isinstance(adapter_key, str) or not adapter_key:
            return None, invalid_input_error("invalid_http_task_request", "adapter_key 必须为非空字符串")
        capability = payload.get("capability")
        if capability != CONTENT_DETAIL_BY_URL:
            return None, invalid_input_error(
                "invalid_capability",
                f"HTTP submit 当前仅支持 `{CONTENT_DETAIL_BY_URL}`",
            )
        target_payload = payload.get("target")
        if not isinstance(target_payload, Mapping):
            return None, invalid_input_error("invalid_http_task_request", "target 必须为对象")
        target_unknown_fields = sorted(str(field) for field in target_payload.keys() if field != "url")
        if target_unknown_fields:
            return None, invalid_input_error(
                "invalid_http_task_request",
                "target 包含未批准字段",
                details={"unknown_fields": target_unknown_fields},
            )
        url = target_payload.get("url")
        if not isinstance(url, str) or not url:
            return None, invalid_input_error("invalid_http_task_request", "target.url 必须为非空字符串")
        return (
            TaskRequest(
                adapter_key=adapter_key,
                capability=capability,
                input=TaskInput(url=url),
                execution_control_policy=execution_control_policy,
            ),
            None,
        )

    def _load_record(self, task_id: str) -> TaskRecord | HttpResponse:
        try:
            return self._task_record_store.load(task_id)
        except FileNotFoundError:
            return HttpResponse(
                404,
                self._task_failure(
                    task_id,
                    invalid_input_error(
                        "task_record_not_found",
                        f"task_id `{task_id}` 对应的持久化任务记录不存在",
                    ),
                ),
            )
        except (TaskRecordContractError, TaskRecordPersistenceError, TaskRecordStoreError, OSError) as error:
            return self._record_unavailable_response(task_id, str(error) or error.__class__.__name__)
        except Exception as error:
            return self._record_unavailable_response(task_id, str(error) or error.__class__.__name__)

    def _submit_failure(self, error: Mapping[str, Any], *, status_code: int) -> HttpResponse:
        task_id, task_id_error = self._resolve_http_task_id()
        failure_error = task_id_error or error
        effective_status_code = 500 if task_id_error is not None else status_code
        return HttpResponse(effective_status_code, failure_envelope(task_id if task_id_error is None else "", "", "", failure_error))

    def _resolve_http_task_id(self) -> tuple[str, dict[str, Any] | None]:
        task_id, task_id_error = resolve_task_id(self._task_id_factory)
        if task_id_error is not None:
            return "", task_id_error
        task_id_error = self._validate_task_id(task_id)
        if task_id_error is not None:
            return "", runtime_contract_error(
                "invalid_task_id",
                "生成的 task_id 无法安全投影为 HTTP path segment",
                details={"reason": task_id_error.get("code", "invalid_task_id")},
            )
        return task_id, None

    def _submit_failure_status_code(self, envelope: Mapping[str, Any]) -> int:
        error = envelope.get("error")
        code = error.get("code") if isinstance(error, Mapping) else None
        category = error.get("category") if isinstance(error, Mapping) else None
        if code in {"concurrency_limit_exceeded", "result_not_ready"}:
            return 409
        if code in {"task_record_persistence_failed", "task_record_conflict", "invalid_task_record"}:
            return 500
        if category in {"invalid_input", "unsupported"}:
            return 400
        return 500

    def _validate_task_id(self, task_id: str) -> dict[str, Any] | None:
        if not isinstance(task_id, str):
            return runtime_contract_error("invalid_task_id", "task_id 必须为非空字符串")
        if not task_id:
            return invalid_input_error("missing_task_id", "task_id 不得为空")
        if "/" in task_id:
            return runtime_contract_error("invalid_task_id", "task_id 必须来自单个 path segment")
        return None

    def _task_failure(
        self,
        task_id: str,
        error: Mapping[str, Any],
        *,
        record: TaskRecord | None = None,
    ) -> dict[str, Any]:
        adapter_key, capability = _record_failure_identity(record)
        return failure_envelope(
            task_id,
            adapter_key,
            capability,
            error,
        )

    def _record_unavailable_response(self, task_id: str, reason: str, *, record: Any = None) -> HttpResponse:
        return HttpResponse(
            500,
            self._task_failure(
                task_id,
                runtime_contract_error(
                    "task_record_unavailable",
                    f"task_id `{task_id}` 对应的持久化任务记录不可用",
                    details={"reason": reason},
                ),
                record=record,
            ),
        )


def build_wsgi_app(service: TaskHttpService) -> Callable[[Mapping[str, Any], Callable[..., Any]], Iterable[bytes]]:
    def app(environ: Mapping[str, Any], start_response: Callable[..., Any]) -> Iterable[bytes]:
        response = dispatch_wsgi_request(service, environ)
        try:
            payload = json.dumps(response.body, ensure_ascii=False).encode("utf-8")
        except (TypeError, ValueError):
            response = HttpResponse(
                500,
                failure_envelope(
                    "",
                    "",
                    "",
                    runtime_contract_error(
                        "http_response_not_json_serializable",
                        "HTTP response body 无法序列化为 JSON",
                    ),
                ),
            )
            payload = json.dumps(response.body, ensure_ascii=False).encode("utf-8")
        status_line = f"{response.status_code} {HTTP_STATUS_TEXT.get(response.status_code, 'Unknown')}"
        headers = tuple(response.headers) + (("Content-Length", str(len(payload))),)
        start_response(status_line, list(headers))
        return [payload]

    return app


def dispatch_wsgi_request(service: TaskHttpService, environ: Mapping[str, Any]) -> HttpResponse:
    method = str(environ.get("REQUEST_METHOD") or "").upper()
    path = str(environ.get("PATH_INFO") or "")
    if environ.get("QUERY_STRING"):
        return _route_failure(
            "query parameters are not supported",
            status_code=400,
            task_id=_task_id_from_get_path(method, path),
        )

    if method == "POST" and path == "/v0/tasks":
        payload, error = _read_json_body(environ)
        if error is not None:
            return _route_failure(error, status_code=400)
        return service.submit(payload)

    status_prefix = "/v0/tasks/"
    result_suffix = "/result"
    if method == "GET" and path.startswith(status_prefix):
        remainder = path[len(status_prefix) :]
        if remainder.endswith(result_suffix):
            raw_task_id = remainder[: -len(result_suffix)]
            if "/" in raw_task_id:
                return _route_failure(
                    "invalid result endpoint",
                    status_code=400,
                    task_id=_first_path_task_id(remainder),
                )
            return service.result(unquote(raw_task_id))
        if "/" in remainder:
            return _route_failure(
                "invalid status endpoint",
                status_code=400,
                task_id=_first_path_task_id(remainder),
            )
        return service.status(unquote(remainder))

    return _route_failure("endpoint not found", status_code=404)


def _read_json_body(environ: Mapping[str, Any]) -> tuple[Any | None, str | None]:
    try:
        content_length = int(str(environ.get("CONTENT_LENGTH") or "0"))
    except ValueError:
        return None, "CONTENT_LENGTH must be an integer"
    if content_length < 0:
        return None, "CONTENT_LENGTH must be non-negative"
    body_stream = environ.get("wsgi.input")
    if body_stream is None:
        raw_body = b""
    else:
        try:
            raw_body = body_stream.read(content_length)
        except OSError:
            return None, "request body could not be read"
    try:
        return json.loads(raw_body.decode("utf-8") if isinstance(raw_body, bytes) else str(raw_body)), None
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "request body must be valid JSON"


def _project_execution_control_policy(payload: Any) -> tuple[ExecutionControlPolicy | None, dict[str, Any] | None]:
    if not isinstance(payload, Mapping):
        return None, invalid_input_error("invalid_execution_control_policy", "execution_control_policy 必须为对象")
    unknown_fields = sorted(str(field) for field in payload.keys() if field not in {"timeout", "retry", "concurrency"})
    if unknown_fields:
        return None, invalid_input_error(
            "invalid_execution_control_policy",
            "execution_control_policy 包含未批准字段",
            details={"unknown_fields": unknown_fields},
        )
    missing_fields = sorted(field for field in ("timeout", "retry", "concurrency") if field not in payload)
    if missing_fields:
        return None, invalid_input_error(
            "invalid_execution_control_policy",
            "execution_control_policy 缺少必需字段",
            details={"missing_fields": missing_fields},
        )

    timeout, timeout_error = _project_timeout_policy(payload["timeout"])
    if timeout_error is not None:
        return None, timeout_error
    retry, retry_error = _project_retry_policy(payload["retry"])
    if retry_error is not None:
        return None, retry_error
    concurrency, concurrency_error = _project_concurrency_policy(payload["concurrency"])
    if concurrency_error is not None:
        return None, concurrency_error
    return ExecutionControlPolicy(timeout=timeout, retry=retry, concurrency=concurrency), None


def _envelope_with_record_observability(record: TaskRecord) -> dict[str, Any]:
    assert record.result is not None
    envelope = dict(record.result.envelope)
    if record.task_record_ref is not None and "task_record_ref" not in envelope:
        envelope["task_record_ref"] = record.task_record_ref
    if record.runtime_result_refs and "runtime_result_refs" not in envelope:
        envelope["runtime_result_refs"] = list(record.runtime_result_refs)
    if record.execution_control_events and "execution_control_events" not in envelope:
        envelope["execution_control_events"] = list(record.execution_control_events)
    return envelope


def _record_failure_identity(record: Any) -> tuple[str, str]:
    if not isinstance(record, TaskRecord):
        return "", ""
    request = getattr(record, "request", None)
    adapter_key = getattr(request, "adapter_key", "")
    capability = getattr(request, "capability", "")
    return (
        adapter_key if isinstance(adapter_key, str) else "",
        capability if isinstance(capability, str) else "",
    )


def _project_timeout_policy(payload: Any) -> tuple[ExecutionTimeoutPolicy | None, dict[str, Any] | None]:
    if not isinstance(payload, Mapping):
        return None, invalid_input_error("invalid_execution_control_policy", "execution_control_policy.timeout 必须为对象")
    unknown_fields = sorted(str(field) for field in payload.keys() if field != "timeout_ms")
    if unknown_fields:
        return None, invalid_input_error(
            "invalid_execution_control_policy",
            "execution_control_policy.timeout 包含未批准字段",
            details={"unknown_fields": unknown_fields},
        )
    timeout_ms = payload.get("timeout_ms")
    if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int) or timeout_ms <= 0:
        return None, invalid_input_error(
            "invalid_execution_control_policy",
            "execution_control_policy.timeout.timeout_ms 必须为正整数",
        )
    return ExecutionTimeoutPolicy(timeout_ms=timeout_ms), None


def _project_retry_policy(payload: Any) -> tuple[ExecutionRetryPolicy | None, dict[str, Any] | None]:
    if not isinstance(payload, Mapping):
        return None, invalid_input_error("invalid_execution_control_policy", "execution_control_policy.retry 必须为对象")
    unknown_fields = sorted(str(field) for field in payload.keys() if field not in {"max_attempts", "backoff_ms"})
    if unknown_fields:
        return None, invalid_input_error(
            "invalid_execution_control_policy",
            "execution_control_policy.retry 包含未批准字段",
            details={"unknown_fields": unknown_fields},
        )
    max_attempts = payload.get("max_attempts")
    backoff_ms = payload.get("backoff_ms")
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or max_attempts < 1:
        return None, invalid_input_error(
            "invalid_execution_control_policy",
            "execution_control_policy.retry.max_attempts 必须为正整数",
        )
    if isinstance(backoff_ms, bool) or not isinstance(backoff_ms, int) or backoff_ms < 0:
        return None, invalid_input_error(
            "invalid_execution_control_policy",
            "execution_control_policy.retry.backoff_ms 必须为非负整数",
        )
    return ExecutionRetryPolicy(max_attempts=max_attempts, backoff_ms=backoff_ms), None


def _project_concurrency_policy(payload: Any) -> tuple[ExecutionConcurrencyPolicy | None, dict[str, Any] | None]:
    if not isinstance(payload, Mapping):
        return None, invalid_input_error("invalid_execution_control_policy", "execution_control_policy.concurrency 必须为对象")
    unknown_fields = sorted(str(field) for field in payload.keys() if field not in {"scope", "max_in_flight", "on_limit"})
    if unknown_fields:
        return None, invalid_input_error(
            "invalid_execution_control_policy",
            "execution_control_policy.concurrency 包含未批准字段",
            details={"unknown_fields": unknown_fields},
        )
    scope = payload.get("scope")
    max_in_flight = payload.get("max_in_flight")
    on_limit = payload.get("on_limit")
    if scope not in ALLOWED_EXECUTION_CONTROL_CONCURRENCY_SCOPES:
        return None, invalid_input_error(
            "invalid_execution_control_policy",
            "execution_control_policy.concurrency.scope 不在共享 contract 批准值域内",
            details={"allowed_scopes": sorted(ALLOWED_EXECUTION_CONTROL_CONCURRENCY_SCOPES)},
        )
    if isinstance(max_in_flight, bool) or not isinstance(max_in_flight, int) or max_in_flight < 1:
        return None, invalid_input_error(
            "invalid_execution_control_policy",
            "execution_control_policy.concurrency.max_in_flight 必须为正整数",
        )
    if on_limit != "reject":
        return None, invalid_input_error(
            "invalid_execution_control_policy",
            "execution_control_policy.concurrency.on_limit 当前仅支持 reject",
        )
    return ExecutionConcurrencyPolicy(scope=scope, max_in_flight=max_in_flight, on_limit=on_limit), None


def _route_failure(message: str, *, status_code: int, task_id: str = "") -> HttpResponse:
    error = invalid_input_error("invalid_http_request", message)
    return HttpResponse(status_code, failure_envelope(task_id, "", "", error))


def _envelope_task_id(task_id: Any) -> str:
    return task_id if isinstance(task_id, str) else ""


def _task_id_from_get_path(method: str, path: str) -> str:
    if method != "GET":
        return ""
    status_prefix = "/v0/tasks/"
    if not path.startswith(status_prefix):
        return ""
    return _first_path_task_id(path[len(status_prefix) :])


def _first_path_task_id(remainder: str) -> str:
    raw_task_id = remainder.split("/", 1)[0]
    return unquote(raw_task_id) if raw_task_id else ""
