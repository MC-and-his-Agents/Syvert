from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from syvert.runtime import TaskInput, TaskRequest, execute_task
from syvert.version_gate import validate_real_adapter_regression_source_report


_REFERENCE_PAIR = ("xhs", "douyin")
_SEMANTIC_OPERATION = "content_detail_by_url"
_TARGET_TYPE = "url"
_EXPECTED_OUTCOMES = frozenset({"success", "allowed_failure"})

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


def build_real_adapter_regression_payload(
    *,
    version: str,
    adapters: Mapping[str, Any],
) -> dict[str, Any]:
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
                adapters=adapters,
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
    payload = build_real_adapter_regression_payload(version=version, adapters=adapters)
    return validate_real_adapter_regression_source_report(
        payload,
        version=version,
        reference_pair=_REFERENCE_PAIR,
        operation=_SEMANTIC_OPERATION,
        target_type=_TARGET_TYPE,
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
        "expected_outcome": str(case_definition["expected_outcome"]),
        "observed_status": observed_status,
        "observed_error_category": observed_error_category,
    }
