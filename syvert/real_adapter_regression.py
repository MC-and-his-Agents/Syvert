from __future__ import annotations

import functools
from collections.abc import Mapping
from typing import Any

from syvert.adapters.douyin import DouyinAdapter, default_page_state_transport
from syvert.adapters.xhs import XhsAdapter
from syvert.runtime import TaskInput, TaskRequest, execute_task
from syvert.version_gate import validate_real_adapter_regression_source_report


_REFERENCE_PAIR = ("xhs", "douyin")
_SEMANTIC_OPERATION = "content_detail_by_url"
_TARGET_TYPE = "url"
_EXPECTED_OUTCOMES = frozenset({"success", "allowed_failure"})
_REFERENCE_ADAPTER_TYPES = {
    "xhs": XhsAdapter,
    "douyin": DouyinAdapter,
}
_FROZEN_REFERENCE_ADAPTER_FIELDS = ("adapter_key", "supported_capabilities", "supported_targets", "supported_collection_modes")
_FROZEN_REFERENCE_ADAPTER_SURFACE_BY_VERSION = {
    "v0.2.0": {
        "xhs": {
            "adapter_key": "xhs",
            "supported_capabilities": frozenset({"content_detail"}),
            "supported_targets": frozenset({"url"}),
            "supported_collection_modes": frozenset({"hybrid"}),
        },
        "douyin": {
            "adapter_key": "douyin",
            "supported_capabilities": frozenset({"content_detail"}),
            "supported_targets": frozenset({"url"}),
            "supported_collection_modes": frozenset({"hybrid"}),
        },
    }
}
_DISALLOWED_REFERENCE_ADAPTER_OVERRIDES = frozenset(
    {
        "execute",
        "adapter_key",
        "supported_capabilities",
        "supported_targets",
        "supported_collection_modes",
    }
)

_REGRESSION_MATRIX = {
    "xhs": (
        {
            "case_id": "xhs-success",
            "expected_outcome": "success",
            "url": "https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8?xsec_token=token-1&xsec_source=pc_search",
            "evidence_ref": "regression:xhs:success",
        },
        {
            "case_id": "xhs-invalid-input",
            "expected_outcome": "allowed_failure",
            "url": "https://example.com/not-xhs",
            "evidence_ref": "regression:xhs:invalid-input",
        },
    ),
    "douyin": (
        {
            "case_id": "douyin-success",
            "expected_outcome": "success",
            "url": "https://www.douyin.com/video/7580570616932224282",
            "evidence_ref": "regression:douyin:success",
        },
        {
            "case_id": "douyin-platform",
            "expected_outcome": "allowed_failure",
            "url": "https://www.douyin.com/video/7580570616932224283",
            "evidence_ref": "regression:douyin:platform",
        },
    ),
}


class ReferenceAdapterBindingError(ValueError):
    def __init__(self, *, code: str, message: str, details: Mapping[str, Any]) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details)


def build_real_adapter_regression_payload(
    *,
    version: str,
    adapters: Mapping[str, Any],
) -> dict[str, Any]:
    reference_adapters = resolve_reference_adapters(version=version, adapters=adapters)
    evidence_refs: list[str] = []
    adapter_results: list[dict[str, Any]] = []

    for adapter_key in _REFERENCE_PAIR:
        cases: list[dict[str, Any]] = []
        for case_definition in _REGRESSION_MATRIX[adapter_key]:
            expected_outcome = str(case_definition["expected_outcome"])
            if expected_outcome not in _EXPECTED_OUTCOMES:
                raise ValueError(f"unsupported expected_outcome: {expected_outcome}")
            envelope = execute_task(
                TaskRequest(
                    adapter_key=adapter_key,
                    capability=_SEMANTIC_OPERATION,
                    input=TaskInput(url=str(case_definition["url"])),
                ),
                adapters=reference_adapters,
                task_id_factory=lambda case_id=str(case_definition["case_id"]): f"task-regression-{case_id}",
            )
            cases.append(build_regression_case_from_envelope(case_definition=case_definition, envelope=envelope))
            evidence_refs.append(str(case_definition["evidence_ref"]))
        adapter_results.append({"adapter_key": adapter_key, "cases": cases})

    return {
        "version": version,
        "reference_pair": list(_REFERENCE_PAIR),
        "operation": _SEMANTIC_OPERATION,
        "target_type": _TARGET_TYPE,
        "evidence_refs": evidence_refs,
        "adapter_results": adapter_results,
    }


def run_real_adapter_regression(
    *,
    version: str,
    adapters: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        payload = build_real_adapter_regression_payload(version=version, adapters=adapters)
    except ReferenceAdapterBindingError as error:
        return build_reference_adapter_binding_failure_report(version=version, error=error)
    return validate_real_adapter_regression_source_report(
        payload,
        version=version,
        reference_pair=_REFERENCE_PAIR,
        operation=_SEMANTIC_OPERATION,
        target_type=_TARGET_TYPE,
    )


def resolve_reference_adapters(*, version: str, adapters: Mapping[str, Any]) -> dict[str, object]:
    if not isinstance(adapters, Mapping):
        raise ReferenceAdapterBindingError(
            code="invalid_reference_adapter_mapping",
            message="real adapter regression adapters 必须为对象映射",
            details={"actual_type": type(adapters).__name__},
        )

    validated: dict[str, object] = {}
    frozen_surface = _FROZEN_REFERENCE_ADAPTER_SURFACE_BY_VERSION.get(version)
    if frozen_surface is None:
        raise ReferenceAdapterBindingError(
            code="missing_frozen_reference_adapter_surface",
            message="real adapter regression 缺少版本绑定的冻结 reference adapter surface",
            details={"version": version},
        )
    for adapter_key, expected_type in _REFERENCE_ADAPTER_TYPES.items():
        adapter = adapters.get(adapter_key)
        if adapter is None:
            raise ReferenceAdapterBindingError(
                code="missing_reference_adapter",
                message="real adapter regression 缺少冻结 reference adapter 绑定",
                details={"adapter_key": adapter_key},
            )
        if type(adapter) is not expected_type:
            raise ReferenceAdapterBindingError(
                code="invalid_reference_adapter_identity",
                message="real adapter regression 仅接受真实参考适配器实现",
                details={
                    "adapter_key": adapter_key,
                    "expected_adapter_type": expected_type.__name__,
                    "actual_adapter_type": type(adapter).__name__,
                },
            )
        validate_reference_adapter_surface(
            adapter_key=adapter_key,
            adapter=adapter,
            frozen_surface=frozen_surface[adapter_key],
        )
        validate_reference_adapter_runtime_binding(adapter_key=adapter_key, adapter=adapter)
        validated[adapter_key] = adapter
    return validated


def validate_reference_adapter_surface(
    *,
    adapter_key: str,
    adapter: object,
    frozen_surface: Mapping[str, Any],
) -> None:
    for field_name in _FROZEN_REFERENCE_ADAPTER_FIELDS:
        expected_value = frozen_surface[field_name]
        actual_value = getattr(adapter, field_name, None)
        if actual_value != expected_value:
            raise ReferenceAdapterBindingError(
                code="unexpected_reference_adapter_surface",
                message="real adapter regression reference adapter 公开 surface 必须保持冻结",
                details={
                    "adapter_key": adapter_key,
                    "field": field_name,
                    "expected_value": _normalize_identity_value(expected_value),
                    "actual_value": _normalize_identity_value(actual_value),
                },
            )

    instance_dict = getattr(adapter, "__dict__", None)
    if isinstance(instance_dict, Mapping):
        overridden_fields = sorted(_DISALLOWED_REFERENCE_ADAPTER_OVERRIDES & set(instance_dict))
        if overridden_fields:
            raise ReferenceAdapterBindingError(
                code="overridden_reference_adapter_interface",
                message="real adapter regression reference adapter 不允许覆盖冻结公开接口字段",
                details={
                    "adapter_key": adapter_key,
                    "overridden_fields": overridden_fields,
                },
            )


def validate_reference_adapter_runtime_binding(*, adapter_key: str, adapter: object) -> None:
    if adapter_key != "douyin":
        return
    if _references_default_page_state_transport(getattr(adapter, "_page_state_transport", None)):
        raise ReferenceAdapterBindingError(
            code="non_hermetic_reference_adapter_binding",
            message="real adapter regression 的 douyin allowed-failure case 必须禁用默认 browser recovery",
            details={"adapter_key": adapter_key, "field": "_page_state_transport"},
        )


def build_regression_case_from_envelope(
    *,
    case_definition: Mapping[str, Any],
    envelope: Mapping[str, Any],
) -> dict[str, Any]:
    observed_status = envelope.get("status")
    observed_error_category = None
    error = envelope.get("error")
    if isinstance(error, Mapping):
        category = error.get("category")
        if isinstance(category, str) and category:
            observed_error_category = category
    return {
        "case_id": str(case_definition["case_id"]),
        "evidence_ref": str(case_definition["evidence_ref"]),
        "expected_outcome": str(case_definition["expected_outcome"]),
        "observed_status": observed_status,
        "observed_error_category": observed_error_category,
    }


def build_reference_adapter_binding_failure_report(
    *,
    version: str,
    error: ReferenceAdapterBindingError,
) -> dict[str, Any]:
    evidence_refs = [build_reference_adapter_binding_evidence_ref(error)]
    report = validate_real_adapter_regression_source_report(
        {
            "version": version,
            "reference_pair": list(_REFERENCE_PAIR),
            "operation": _SEMANTIC_OPERATION,
            "target_type": _TARGET_TYPE,
            "evidence_refs": evidence_refs,
            "adapter_results": [],
        },
        version=version,
        reference_pair=_REFERENCE_PAIR,
        operation=_SEMANTIC_OPERATION,
        target_type=_TARGET_TYPE,
    )
    failures = [build_reference_adapter_binding_failure(error)]
    failures.extend(report["details"]["failures"])
    report["verdict"] = "fail"
    report["summary"] = f"real adapter regression failed for version `{version or 'unknown'}`"
    report["evidence_refs"] = evidence_refs
    report["details"] = {
        **report["details"],
        "failures": failures,
    }
    return report


def build_reference_adapter_binding_failure(error: ReferenceAdapterBindingError) -> dict[str, Any]:
    return {
        "source": "real_adapter_regression",
        "code": error.code,
        "message": error.message,
        "details": dict(error.details),
    }


def build_reference_adapter_binding_evidence_ref(error: ReferenceAdapterBindingError) -> str:
    adapter_key = str(error.details.get("adapter_key") or "unknown")
    return f"real_adapter_regression:binding:{adapter_key}:{error.code}"


def _normalize_identity_value(value: Any) -> Any:
    if isinstance(value, frozenset):
        return sorted(value)
    return value


def _references_default_page_state_transport(value: Any, *, _seen: set[int] | None = None) -> bool:
    if value is default_page_state_transport:
        return True

    if _seen is None:
        _seen = set()
    object_id = id(value)
    if object_id in _seen:
        return False
    _seen.add(object_id)

    if isinstance(value, functools.partial):
        return _references_default_page_state_transport(value.func, _seen=_seen) or any(
            _references_default_page_state_transport(item, _seen=_seen)
            for item in (*value.args, *(value.keywords or {}).values())
        )

    wrapped = getattr(value, "__wrapped__", None)
    if wrapped is not None and _references_default_page_state_transport(wrapped, _seen=_seen):
        return True

    bound_func = getattr(value, "__func__", None)
    if bound_func is not None and _references_default_page_state_transport(bound_func, _seen=_seen):
        return True

    closure = getattr(value, "__closure__", None)
    if closure:
        for cell in closure:
            try:
                cell_value = cell.cell_contents
            except ValueError:
                continue
            if _references_default_page_state_transport(cell_value, _seen=_seen):
                return True

    code = getattr(value, "__code__", None)
    globals_dict = getattr(value, "__globals__", None)
    if code is not None and isinstance(globals_dict, Mapping):
        for name in getattr(code, "co_names", ()):
            if name not in globals_dict:
                continue
            referenced_value = globals_dict[name]
            if referenced_value is default_page_state_transport:
                return True
            if referenced_value is not value and _references_default_page_state_transport(referenced_value, _seen=_seen):
                return True

    return False
