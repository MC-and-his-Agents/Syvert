from __future__ import annotations

from copy import deepcopy
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


PASS_VERDICT = "pass"
FAIL_VERDICT = "fail"

RELEASE = "v0.6.0"
FR_ITEM_KEY = "FR-0019-v0-6-operability-release-gate"
GATE_ID = "v0.6.0-operability-gate"
MATRIX_VERSION = "v0.6.0-operability-matrix-v1"

DIMENSION_TIMEOUT_RETRY_CONCURRENCY = "timeout_retry_concurrency"
DIMENSION_FAILURE_LOG_METRICS = "failure_log_metrics"
DIMENSION_HTTP_SUBMIT_STATUS_RESULT = "http_submit_status_result"
DIMENSION_CLI_API_SAME_PATH = "cli_api_same_path"
ALLOWED_DIMENSIONS = frozenset(
    {
        DIMENSION_TIMEOUT_RETRY_CONCURRENCY,
        DIMENSION_FAILURE_LOG_METRICS,
        DIMENSION_HTTP_SUBMIT_STATUS_RESULT,
        DIMENSION_CLI_API_SAME_PATH,
    }
)

APPROVED_CAPABILITY = "content_detail_by_url"
NORMATIVE_DEPENDENCIES = ("FR-0007", "FR-0016", "FR-0017", "FR-0018")

POLICY_SNAPSHOT = {
    "timeout_ms": 30000,
    "retry": {
        "max_attempts": 1,
        "backoff_ms": 0,
    },
    "concurrency": {
        "scope": "global",
        "max_in_flight": 1,
        "on_limit": "reject",
    },
}

REQUIRED_METRICS = (
    "submit_total",
    "success_total",
    "failure_total",
    "timeout_total",
    "retry_attempt_total",
    "concurrency_case_total",
    "concurrency_case_failure_total",
    "same_path_case_total",
    "same_path_case_failure_total",
)

_MANDATORY_CASES: dict[str, dict[str, Any]] = {
    "trc-timeout-platform-control-code": {
        "dimension": DIMENSION_TIMEOUT_RETRY_CONCURRENCY,
        "entrypoints": ("core",),
        "fields": (
            ("error.category", "==", "platform"),
            ("error.details.control_code", "==", "execution_timeout"),
            ("policy.timeout_ms", "==", 30000),
            ("policy.retry.max_attempts", "==", 1),
            ("policy.retry.backoff_ms", "==", 0),
        ),
        "side_effects": (
            "ExecutionControlEvent.details.control_code=execution_timeout",
            "TaskRecord.status=failed",
        ),
    },
    "trc-retryable-platform-budget-closed": {
        "dimension": DIMENSION_TIMEOUT_RETRY_CONCURRENCY,
        "entrypoints": ("core",),
        "fields": (
            ("error.category", "==", "platform"),
            ("error.details.retryable", "==", True),
            ("policy.retry.max_attempts", "==", 1),
            ("idempotency_safety_gate", "==", "pass"),
            ("retry.attempts", "==", 0),
        ),
        "side_effects": (
            "no_extra_retry_attempt",
            "preserve_original_failed_envelope",
        ),
    },
    "trc-non-retryable-fail-closed": {
        "dimension": DIMENSION_TIMEOUT_RETRY_CONCURRENCY,
        "entrypoints": ("core",),
        "fields": (
            ("retry.predicate.match", "==", "none"),
            ("policy.retry.max_attempts", "==", 1),
        ),
        "side_effects": (
            "no_new_retry_attempt",
            "preserve_original_failed_envelope",
        ),
    },
    "trc-pre-accept-concurrency-reject": {
        "dimension": DIMENSION_TIMEOUT_RETRY_CONCURRENCY,
        "entrypoints": ("core", "cli", "http"),
        "fields": (
            ("request_ref", "!=", ""),
            ("stage", "==", "pre_admission"),
            ("result.status", "==", "failed"),
            ("error.category", "==", "invalid_input"),
            ("policy.concurrency.scope", "==", "global"),
            ("policy.concurrency.max_in_flight", "==", 1),
            ("policy.concurrency.on_limit", "==", "reject"),
            ("metrics.concurrency_case_total", ">=", 1),
        ),
        "side_effects": ("TaskRecord.not_created",),
    },
    "trc-concurrent-status-shared-truth": {
        "dimension": DIMENSION_TIMEOUT_RETRY_CONCURRENCY,
        "entrypoints": ("core", "http"),
        "fields": (
            ("status.read_a.task_id", "==", "status.read_b.task_id"),
            ("status.read_a.status", "==", "status.read_b.status"),
            ("case.verdict", "==", "pass"),
            ("metrics.concurrency_case_total", ">=", 1),
        ),
        "side_effects": ("no_extra_TaskRecord", "no_status_regression"),
    },
    "trc-concurrent-result-shared-truth": {
        "dimension": DIMENSION_TIMEOUT_RETRY_CONCURRENCY,
        "entrypoints": ("core", "http"),
        "fields": (
            ("result.read_a.task_id", "==", "result.read_b.task_id"),
            ("result.read_a.envelope_ref", "==", "result.read_b.envelope_ref"),
            ("case.verdict", "==", "pass"),
            ("metrics.concurrency_case_total", ">=", 1),
        ),
        "side_effects": ("no_shadow_result", "terminal_state_not_rewritten"),
    },
    "flm-success-observable": {
        "dimension": DIMENSION_FAILURE_LOG_METRICS,
        "entrypoints": ("core",),
        "fields": (("result.status", "==", "succeeded"), ("metrics.success_total", ">=", 1)),
        "side_effects": ("structured_log.task_id_entrypoint_stage_result_status", "evidence_refs.non_empty"),
    },
    "flm-business-failure-observable": {
        "dimension": DIMENSION_FAILURE_LOG_METRICS,
        "entrypoints": ("core",),
        "fields": (("error.category", "in", ("invalid_input", "unsupported", "platform")), ("metrics.failure_total", ">=", 1)),
        "side_effects": ("structured_log.task_id_entrypoint_stage_error_category",),
    },
    "flm-contract-failure-fail-closed": {
        "dimension": DIMENSION_FAILURE_LOG_METRICS,
        "entrypoints": ("core",),
        "fields": (("error.category", "==", "runtime_contract"), ("gate.verdict", "==", "fail")),
        "side_effects": ("structured_log.error.category=runtime_contract", "no_success_envelope"),
    },
    "flm-timeout-observable": {
        "dimension": DIMENSION_FAILURE_LOG_METRICS,
        "entrypoints": ("core",),
        "fields": (
            ("error.category", "==", "platform"),
            ("error.details.control_code", "==", "execution_timeout"),
            ("metrics.timeout_total", ">=", 1),
        ),
        "side_effects": ("structured_log.timeout_classification",),
    },
    "flm-retry-budget-closed-observable": {
        "dimension": DIMENSION_FAILURE_LOG_METRICS,
        "entrypoints": ("core",),
        "fields": (
            ("policy.retry.max_attempts", "==", 1),
            ("retry.attempts", "==", 0),
            ("metrics.retry_attempt_total", "==", 0),
        ),
        "side_effects": ("structured_log.retry_budget_closed",),
    },
    "flm-store-unavailable-fail-closed": {
        "dimension": DIMENSION_FAILURE_LOG_METRICS,
        "entrypoints": ("core", "cli", "http"),
        "fields": (
            ("error.code", "==", "task_record_unavailable"),
            ("error.category", "==", "runtime_contract"),
            ("gate.verdict", "==", "fail"),
        ),
        "side_effects": ("structured_log.store_unavailable", "no_shadow_status_or_result"),
    },
    "flm-http-invalid-input-observable": {
        "dimension": DIMENSION_FAILURE_LOG_METRICS,
        "entrypoints": ("http",),
        "fields": (
            ("request_ref", "!=", ""),
            ("entrypoint", "==", "http"),
            ("stage", "==", "pre_admission"),
            ("result.status", "==", "failed"),
            ("error.category", "==", "invalid_input"),
            ("metrics.failure_total", ">=", 1),
        ),
        "side_effects": ("structured_log.http_pre_admission_failure", "TaskRecord.not_created"),
    },
    "flm-cli-invalid-input-observable": {
        "dimension": DIMENSION_FAILURE_LOG_METRICS,
        "entrypoints": ("cli",),
        "fields": (
            ("request_ref", "!=", ""),
            ("entrypoint", "==", "cli"),
            ("stage", "==", "pre_admission"),
            ("result.status", "==", "failed"),
            ("error.category", "==", "invalid_input"),
            ("metrics.failure_total", ">=", 1),
        ),
        "side_effects": ("structured_log.cli_pre_admission_failure", "TaskRecord.not_created"),
    },
    "flm-same-path-violation-observable": {
        "dimension": DIMENSION_FAILURE_LOG_METRICS,
        "entrypoints": ("cli", "http"),
        "fields": (("same_path.verdict", "==", "fail"), ("metrics.same_path_case_failure_total", ">=", 1)),
        "side_effects": ("structured_log.shared_truth_mismatch_reason", "overall_gate.verdict=fail"),
    },
    "http-submit-status-result-shared-truth": {
        "dimension": DIMENSION_HTTP_SUBMIT_STATUS_RESULT,
        "entrypoints": ("http",),
        "fields": (
            ("submit.request.capability", "==", APPROVED_CAPABILITY),
            ("metrics.submit_total", ">=", 1),
            ("status.task_id", "==", "result.task_id"),
            ("status.task_record_ref", "==", "result.task_record_ref"),
            ("result.envelope_ref", "!=", ""),
        ),
        "side_effects": ("single_shared_TaskRecord", "result_reads_shared_envelope"),
    },
    "same-path-success-shared-truth": {
        "dimension": DIMENSION_CLI_API_SAME_PATH,
        "entrypoints": ("cli", "http"),
        "fields": (
            ("cli.task_record_ref", "==", "http.task_record_ref"),
            ("cli.envelope_ref", "==", "http.envelope_ref"),
            ("same_path.verdict", "==", "pass"),
            ("metrics.same_path_case_total", ">=", 1),
        ),
        "side_effects": ("same_state_transition",),
    },
    "same-path-pre-admission-invalid-input": {
        "dimension": DIMENSION_CLI_API_SAME_PATH,
        "entrypoints": ("cli", "http"),
        "fields": (
            ("cli.request_ref", "!=", ""),
            ("http.request_ref", "!=", ""),
            ("cli.stage", "==", "pre_admission"),
            ("http.stage", "==", "pre_admission"),
            ("cli.result.status", "==", "failed"),
            ("http.result.status", "==", "failed"),
            ("cli.error.category", "==", "invalid_input"),
            ("http.error.category", "==", "invalid_input"),
            ("cli.error.code", "==", "http.error.code"),
            ("same_path.verdict", "==", "pass"),
            ("metrics.same_path_case_total", ">=", 1),
        ),
        "side_effects": ("cli_no_TaskRecord", "http_no_TaskRecord"),
    },
    "same-path-durable-record-unavailable": {
        "dimension": DIMENSION_CLI_API_SAME_PATH,
        "entrypoints": ("cli", "http"),
        "fields": (
            ("cli.error.code", "==", "task_record_unavailable"),
            ("http.error.code", "==", "task_record_unavailable"),
            ("cli.error.category", "==", "runtime_contract"),
            ("http.error.category", "==", "runtime_contract"),
            ("same_path.verdict", "==", "pass"),
            ("metrics.same_path_case_total", ">=", 1),
        ),
        "side_effects": ("cli_fail_closed", "http_fail_closed"),
    },
    "same-path-terminal-result-read": {
        "dimension": DIMENSION_CLI_API_SAME_PATH,
        "entrypoints": ("cli", "http"),
        "fields": (
            ("cli.result.task_id", "==", "http.result.task_id"),
            ("cli.result.envelope_ref", "==", "http.result.envelope_ref"),
            ("same_path.verdict", "==", "pass"),
            ("metrics.same_path_case_total", ">=", 1),
        ),
        "side_effects": ("shared_terminal_TaskRecord", "shared_runtime_result_refs"),
    },
}


def mandatory_operability_case_ids() -> tuple[str, ...]:
    return tuple(_MANDATORY_CASES)


def build_mandatory_operability_cases(*, verdict: str = PASS_VERDICT) -> list[dict[str, Any]]:
    return [_case_from_definition(case_id, definition, verdict=verdict) for case_id, definition in _MANDATORY_CASES.items()]


def orchestrate_operability_gate(
    *,
    execution_revision: str,
    baseline_gate_ref: str,
    cases: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]],
    metrics_snapshot: Mapping[str, Any],
    release: str = RELEASE,
    fr_item_key: str = FR_ITEM_KEY,
    gate_id: str = GATE_ID,
    matrix_version: str = MATRIX_VERSION,
    policy_snapshot: Mapping[str, Any] | None = None,
    evidence_refs: Sequence[str] | Iterable[str] | None = None,
    normative_dependencies: Sequence[str] | Iterable[str] = NORMATIVE_DEPENDENCIES,
) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    normalized_release = _non_empty_string(release) or "unknown"
    if release != RELEASE:
        failures.append(_failure("operability_gate", "release_mismatch", "operability gate release must be v0.6.0"))
    if fr_item_key != FR_ITEM_KEY:
        failures.append(_failure("operability_gate", "fr_item_key_mismatch", "operability gate FR item key mismatch"))
    if gate_id != GATE_ID:
        failures.append(_failure("operability_gate", "gate_id_mismatch", "operability gate_id must match the frozen FR-0019 gate id"))
    if matrix_version != MATRIX_VERSION:
        failures.append(
            _failure("operability_gate", "matrix_version_mismatch", "operability matrix_version must match the frozen FR-0019 matrix")
        )
    if not _non_empty_string(execution_revision):
        failures.append(_failure("operability_gate", "missing_execution_revision", "operability gate requires an execution revision"))
    if not _non_empty_string(baseline_gate_ref):
        failures.append(_failure("operability_gate", "missing_baseline_gate_ref", "operability gate requires FR-0007 baseline gate ref"))
    elif not baseline_gate_ref.startswith("FR-0007:version_gate:"):
        failures.append(
            _failure(
                "operability_gate",
                "invalid_baseline_gate_ref",
                "baseline_gate_ref must be traceable to the FR-0007 baseline gate",
                details={"baseline_gate_ref": baseline_gate_ref},
            )
        )

    normalized_dependencies = _normalize_string_list(normative_dependencies, "normative_dependencies", failures)
    missing_dependencies = sorted(set(NORMATIVE_DEPENDENCIES) - set(normalized_dependencies))
    if missing_dependencies:
        failures.append(
            _failure(
                "operability_gate",
                "missing_normative_dependencies",
                "operability gate must name all normative dependencies",
                details={"missing_dependencies": missing_dependencies},
            )
        )

    normalized_policy = _normalize_policy_snapshot(policy_snapshot, failures)
    normalized_metrics = _normalize_metrics_snapshot(metrics_snapshot, failures)
    normalized_evidence_refs = _normalize_evidence_refs(evidence_refs, failures)
    normalized_cases = _normalize_cases(cases, failures, metrics_snapshot=normalized_metrics, policy_snapshot=normalized_policy)
    _validate_mandatory_case_coverage(normalized_cases, failures)

    for case in normalized_cases:
        normalized_evidence_refs.extend(case["evidence_refs"])
        if case["verdict"] == FAIL_VERDICT and case["gate_impact"] == "mandatory":
            failures.append(
                _failure(
                    case["dimension"],
                    "mandatory_case_failed",
                    "mandatory operability matrix case failed",
                    details={"case_id": case["case_id"]},
                )
            )

    normalized_evidence_refs = _dedupe_sorted(normalized_evidence_refs)
    _validate_revision_evidence_binding(execution_revision, normalized_evidence_refs, failures)
    if not normalized_evidence_refs:
        failures.append(_failure("operability_gate", "missing_evidence_refs", "operability gate requires evidence refs"))
        normalized_evidence_refs = ["operability_gate:failure:missing_evidence_refs"]

    failed_case_ids = _failed_case_ids(normalized_cases, failures)
    failed_dimensions = sorted(
        {
            str(case["dimension"])
            for case in normalized_cases
            if str(case["case_id"]) in failed_case_ids
        }
    )
    summary = {
        "case_total": len(normalized_cases),
        "pass_case_total": max(len(normalized_cases) - len(failed_case_ids), 0),
        "fail_case_total": len(failed_case_ids),
        "failed_case_ids": sorted(failed_case_ids),
        "failed_dimensions": failed_dimensions,
    }
    verdict = PASS_VERDICT if not failures else FAIL_VERDICT
    return {
        "release": normalized_release,
        "fr_item_key": fr_item_key,
        "gate_id": gate_id,
        "execution_revision": execution_revision,
        "baseline_gate_ref": baseline_gate_ref,
        "matrix_version": matrix_version,
        "normative_dependencies": list(normalized_dependencies),
        "policy_snapshot": normalized_policy,
        "cases": normalized_cases,
        "summary": summary,
        "metrics_snapshot": normalized_metrics,
        "evidence_refs": normalized_evidence_refs,
        "verdict": verdict,
        "safe_to_release": verdict == PASS_VERDICT,
        "failures": _dedupe_failures(failures),
    }


def _case_from_definition(case_id: str, definition: Mapping[str, Any], *, verdict: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "dimension": definition["dimension"],
        "capability": APPROVED_CAPABILITY,
        "entrypoints": list(definition["entrypoints"]),
        "preconditions": [f"precondition:{case_id}"],
        "expected_result": {
            "fields": [
                {"path": path, "operator": operator, "value": deepcopy(value)}
                for path, operator, value in definition["fields"]
            ],
            "side_effects": list(definition["side_effects"]),
            "forbidden_mutations": ["shadow_status", "shadow_result"],
        },
        "actual_result_ref": f"operability:{case_id}",
        "actual_result": _actual_result_from_definition(case_id, definition),
        "gate_impact": "mandatory",
        "evidence_refs": [f"operability:{case_id}"],
        "verdict": verdict,
    }


def _normalize_cases(
    raw_cases: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]],
    failures: list[dict[str, Any]],
    *,
    metrics_snapshot: Mapping[str, Any],
    policy_snapshot: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if isinstance(raw_cases, Mapping) or isinstance(raw_cases, (str, bytes)):
        failures.append(_failure("operability_gate", "invalid_cases", "operability cases must be a sequence of mappings"))
        return []
    try:
        candidates = list(raw_cases)
    except TypeError:
        failures.append(_failure("operability_gate", "invalid_cases", "operability cases must be iterable"))
        return []

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw_case in enumerate(candidates):
        if not isinstance(raw_case, Mapping):
            failures.append(_failure("operability_gate", "invalid_case", "operability case must be a mapping", details={"index": index}))
            continue
        case_id = _non_empty_string(raw_case.get("case_id"))
        if not case_id:
            failures.append(_failure("operability_gate", "missing_case_id", "operability case requires case_id", details={"index": index}))
            continue
        if case_id in seen:
            failures.append(_failure("operability_gate", "duplicate_case_id", "operability case ids must be unique", details={"case_id": case_id}))
            continue
        seen.add(case_id)
        definition = _MANDATORY_CASES.get(case_id)
        dimension = _non_empty_string(raw_case.get("dimension"))
        if not dimension:
            failures.append(_case_failure(case_id, "missing_case_dimension", "operability case requires dimension"))
        elif dimension not in ALLOWED_DIMENSIONS:
            failures.append(
                _case_failure(
                    case_id,
                    "invalid_case_dimension",
                    "operability case dimension must be one of the FR-0019 allowed dimensions",
                    details={"actual_dimension": dimension},
                )
            )
        elif definition and dimension != definition["dimension"]:
            failures.append(
                _case_failure(
                    case_id,
                    "case_dimension_mismatch",
                    "mandatory case dimension must match the frozen matrix",
                    details={"expected_dimension": definition["dimension"], "actual_dimension": dimension},
                )
            )
        capability = _non_empty_string(raw_case.get("capability"))
        if capability != APPROVED_CAPABILITY:
            failures.append(
                _case_failure(
                    case_id,
                    "invalid_case_capability",
                    "operability case capability must be content_detail_by_url",
                    details={"actual_capability": capability},
                )
            )
        entrypoints = _normalize_string_list(raw_case.get("entrypoints"), "entrypoints", failures, failure_source=case_id)
        if definition and sorted(entrypoints) != sorted(definition["entrypoints"]):
            failures.append(
                _case_failure(
                    case_id,
                    "case_entrypoints_mismatch",
                    "mandatory case entrypoints must match the frozen matrix",
                    details={"expected_entrypoints": list(definition["entrypoints"]), "actual_entrypoints": entrypoints},
                )
            )
        verdict = _non_empty_string(raw_case.get("verdict"))
        if verdict not in {PASS_VERDICT, FAIL_VERDICT}:
            failures.append(_case_failure(case_id, "invalid_case_verdict", "operability case verdict must be pass or fail"))
            verdict = FAIL_VERDICT
        gate_impact = _non_empty_string(raw_case.get("gate_impact")) or "mandatory"
        if definition and gate_impact != "mandatory":
            failures.append(_case_failure(case_id, "mandatory_case_gate_impact_mismatch", "mandatory case must have mandatory gate impact"))
        actual_result_ref = _non_empty_string(raw_case.get("actual_result_ref"))
        if not actual_result_ref:
            failures.append(_case_failure(case_id, "missing_actual_result_ref", "operability case requires actual_result_ref"))
        if "evidence_refs" not in raw_case:
            failures.append(_case_failure(case_id, "missing_case_evidence_refs", "operability case requires evidence_refs"))
            evidence_refs = []
        else:
            evidence_refs = _normalize_evidence_refs(raw_case.get("evidence_refs"), failures, source=case_id)
        expected_result = _normalize_expected_result(case_id, raw_case.get("expected_result"), definition, failures)
        actual_result = raw_case.get("actual_result")
        if not isinstance(actual_result, Mapping):
            failures.append(_case_failure(case_id, "invalid_actual_result", "operability case requires actual_result mapping"))
            actual_result = {}
        _validate_case_actual_result(
            case_id,
            expected_result.get("fields", []),
            actual_result,
            metrics_snapshot=metrics_snapshot,
            policy_snapshot=policy_snapshot,
            failures=failures,
        )
        normalized.append(
            {
                "case_id": case_id,
                "dimension": dimension,
                "capability": capability,
                "entrypoints": entrypoints,
                "preconditions": _normalize_string_list(raw_case.get("preconditions"), "preconditions", failures, failure_source=case_id),
                "expected_result": expected_result,
                "actual_result_ref": actual_result_ref,
                "actual_result": _json_safe(actual_result),
                "gate_impact": gate_impact,
                "evidence_refs": evidence_refs,
                "verdict": verdict,
            }
        )
    return normalized


def _normalize_expected_result(
    case_id: str,
    raw_expected_result: Any,
    definition: Mapping[str, Any] | None,
    failures: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(raw_expected_result, Mapping):
        failures.append(_case_failure(case_id, "invalid_expected_result", "expected_result must be a mapping"))
        return {"fields": [], "side_effects": [], "forbidden_mutations": []}
    raw_fields = raw_expected_result.get("fields")
    fields: list[dict[str, Any]] = []
    if not isinstance(raw_fields, Sequence) or isinstance(raw_fields, (str, bytes)):
        failures.append(_case_failure(case_id, "invalid_expected_result_fields", "expected_result.fields must be a sequence"))
    else:
        for index, raw_field in enumerate(raw_fields):
            if not isinstance(raw_field, Mapping):
                failures.append(_case_failure(case_id, "invalid_expected_result_field", "expected_result field must be a mapping", details={"index": index}))
                continue
            path = _non_empty_string(raw_field.get("path"))
            operator = _non_empty_string(raw_field.get("operator"))
            if not path or not operator or "value" not in raw_field:
                failures.append(_case_failure(case_id, "invalid_expected_result_field", "expected_result field requires path, operator and value", details={"index": index}))
                continue
            raw_value = raw_field.get("value")
            if operator == ">=" and (isinstance(raw_value, bool) or not isinstance(raw_value, (int, float))):
                failures.append(
                    _case_failure(
                        case_id,
                        "invalid_expected_result_field_value",
                        "expected_result >= assertions require a numeric value",
                        details={"index": index, "path": path},
                    )
                )
                continue
            if operator == "in" and (
                not isinstance(raw_value, Iterable) or isinstance(raw_value, (Mapping, str, bytes))
            ):
                failures.append(
                    _case_failure(
                        case_id,
                        "invalid_expected_result_field_value",
                        "expected_result in assertions require a non-string iterable value",
                        details={"index": index, "path": path},
                    )
                )
                continue
            fields.append({"path": path, "operator": operator, "value": _json_safe(raw_value)})
    if not any(field["operator"] in {"==", "!=", "in"} for field in fields):
        failures.append(_case_failure(case_id, "missing_exact_expected_field", "expected_result.fields requires at least one exact field assertion"))

    side_effects = _normalize_string_list(raw_expected_result.get("side_effects"), "side_effects", failures, failure_source=case_id)
    forbidden_mutations = _normalize_string_list(
        raw_expected_result.get("forbidden_mutations"),
        "forbidden_mutations",
        failures,
        failure_source=case_id,
        allow_empty=True,
    )
    if definition:
        field_index = {(field["path"], field["operator"], _canonical_json(field["value"])) for field in fields}
        missing_fields = [
            {"path": path, "operator": operator, "value": _json_safe(value)}
            for path, operator, value in definition["fields"]
            if (path, operator, _canonical_json(value)) not in field_index
        ]
        if missing_fields:
            failures.append(
                _case_failure(
                    case_id,
                    "mandatory_case_expected_fields_missing",
                    "mandatory case expected_result.fields must include the frozen field assertions",
                    details={"missing_fields": missing_fields},
                )
            )
        missing_side_effects = sorted(set(definition["side_effects"]) - set(side_effects))
        if missing_side_effects:
            failures.append(
                _case_failure(
                    case_id,
                    "mandatory_case_side_effects_missing",
                    "mandatory case expected_result.side_effects must include the frozen side effects",
                    details={"missing_side_effects": missing_side_effects},
                )
            )
    return {"fields": fields, "side_effects": side_effects, "forbidden_mutations": forbidden_mutations}


def _validate_case_actual_result(
    case_id: str,
    fields: Sequence[Mapping[str, Any]],
    actual_result: Mapping[str, Any],
    *,
    metrics_snapshot: Mapping[str, Any],
    policy_snapshot: Mapping[str, Any],
    failures: list[dict[str, Any]],
) -> None:
    fact_source = _merge_mappings(actual_result, {"metrics": metrics_snapshot, "policy": policy_snapshot})
    for field in fields:
        path = str(field.get("path") or "")
        operator = str(field.get("operator") or "")
        expected_value = field.get("value")
        actual_value = _get_path(fact_source, path)
        if operator == "==":
            if isinstance(expected_value, str) and "." in expected_value:
                expected_comparison_value = _get_path(fact_source, expected_value)
            else:
                expected_comparison_value = expected_value
            if actual_value != expected_comparison_value:
                failures.append(
                    _case_failure(
                        case_id,
                        "actual_result_field_mismatch",
                        "actual_result does not satisfy expected_result field assertion",
                        details={
                            "path": path,
                            "operator": operator,
                            "expected": _json_safe(expected_comparison_value),
                            "actual": _json_safe(actual_value),
                        },
                    )
                )
        elif operator == "!=":
            if actual_value == expected_value:
                failures.append(
                    _case_failure(
                        case_id,
                        "actual_result_field_mismatch",
                        "actual_result does not satisfy expected_result field assertion",
                        details={"path": path, "operator": operator, "forbidden": _json_safe(expected_value)},
                    )
                )
        elif operator == ">=":
            if isinstance(expected_value, bool) or not isinstance(expected_value, (int, float)):
                failures.append(
                    _case_failure(
                        case_id,
                        "invalid_expected_result_field_value",
                        "expected_result >= assertions require a numeric value",
                        details={"path": path, "actual_expected_value": _json_safe(expected_value)},
                    )
                )
            elif isinstance(actual_value, bool) or not isinstance(actual_value, (int, float)) or actual_value < expected_value:
                failures.append(
                    _case_failure(
                        case_id,
                        "actual_result_field_mismatch",
                        "actual_result does not satisfy expected_result field assertion",
                        details={
                            "path": path,
                            "operator": operator,
                            "expected": _json_safe(expected_value),
                            "actual": _json_safe(actual_value),
                        },
                    )
                )
        elif operator == "in":
            if not isinstance(expected_value, Iterable) or isinstance(expected_value, (Mapping, str, bytes)):
                failures.append(
                    _case_failure(
                        case_id,
                        "invalid_expected_result_field_value",
                        "expected_result in assertions require a non-string iterable value",
                        details={"path": path, "actual_expected_value": _json_safe(expected_value)},
                    )
                )
            elif actual_value not in expected_value:
                failures.append(
                    _case_failure(
                        case_id,
                        "actual_result_field_mismatch",
                        "actual_result does not satisfy expected_result field assertion",
                        details={
                            "path": path,
                            "operator": operator,
                            "allowed": _json_safe(expected_value),
                            "actual": _json_safe(actual_value),
                        },
                    )
                )
        else:
            failures.append(
                _case_failure(
                    case_id,
                    "unsupported_expected_result_operator",
                    "expected_result field operator is unsupported",
                    details={"path": path, "operator": operator},
                )
            )


def _validate_mandatory_case_coverage(normalized_cases: Sequence[Mapping[str, Any]], failures: list[dict[str, Any]]) -> None:
    observed_ids = {str(case.get("case_id")) for case in normalized_cases}
    missing = [case_id for case_id in _MANDATORY_CASES if case_id not in observed_ids]
    if missing:
        failures.append(
            _failure(
                "operability_gate",
                "missing_mandatory_cases",
                "operability gate must cover all mandatory matrix cases",
                details={"missing_case_ids": missing},
            )
        )
    observed_dimensions = {str(case.get("dimension")) for case in normalized_cases}
    required_dimensions = {
        DIMENSION_TIMEOUT_RETRY_CONCURRENCY,
        DIMENSION_FAILURE_LOG_METRICS,
        DIMENSION_HTTP_SUBMIT_STATUS_RESULT,
        DIMENSION_CLI_API_SAME_PATH,
    }
    missing_dimensions = sorted(required_dimensions - observed_dimensions)
    if missing_dimensions:
        failures.append(
            _failure(
                "operability_gate",
                "missing_mandatory_dimensions",
                "operability gate must cover all mandatory dimensions",
                details={"missing_dimensions": missing_dimensions},
            )
        )


def _normalize_policy_snapshot(raw_policy: Mapping[str, Any] | None, failures: list[dict[str, Any]]) -> dict[str, Any]:
    policy = deepcopy(POLICY_SNAPSHOT if raw_policy is None else raw_policy)
    expected_paths = {
        "timeout_ms": 30000,
        "retry.max_attempts": 1,
        "retry.backoff_ms": 0,
        "concurrency.scope": "global",
        "concurrency.max_in_flight": 1,
        "concurrency.on_limit": "reject",
    }
    if not isinstance(policy, Mapping):
        failures.append(_failure("operability_gate", "invalid_policy_snapshot", "policy_snapshot must be a mapping"))
        return deepcopy(POLICY_SNAPSHOT)
    for path, expected_value in expected_paths.items():
        actual_value = _get_path(policy, path)
        if actual_value != expected_value:
            failures.append(
                _failure(
                    "operability_gate",
                    "policy_snapshot_mismatch",
                    "policy_snapshot must match FR-0019 defaults",
                    details={"path": path, "expected": expected_value, "actual": _json_safe(actual_value)},
                )
            )
    return _json_safe(policy)


def _normalize_metrics_snapshot(raw_metrics: Mapping[str, Any], failures: list[dict[str, Any]]) -> dict[str, int]:
    if not isinstance(raw_metrics, Mapping):
        failures.append(_failure("operability_gate", "invalid_metrics_snapshot", "metrics_snapshot must be a mapping"))
        raw_metrics = {}
    normalized: dict[str, int] = {}
    for field in REQUIRED_METRICS:
        raw_value = raw_metrics.get(field)
        if isinstance(raw_value, bool) or not isinstance(raw_value, int) or raw_value < 0:
            failures.append(
                _failure(
                    "operability_gate",
                    "invalid_metrics_snapshot_field",
                    "metrics_snapshot fields must be non-negative integers",
                    details={"field": field, "actual": _json_safe(raw_value)},
                )
            )
            normalized[field] = 0
        else:
            normalized[field] = raw_value
    return normalized


def _actual_result_from_definition(case_id: str, definition: Mapping[str, Any]) -> dict[str, Any]:
    actual_result: dict[str, Any] = {"case": {"id": case_id}}
    for path, operator, expected_value in definition["fields"]:
        if isinstance(expected_value, str) and "." in expected_value and operator == "==":
            shared_value = f"shared:{case_id}:{path}"
            _set_path(actual_result, path, shared_value)
            _set_path(actual_result, expected_value, shared_value)
        elif operator == "!=":
            _set_path(actual_result, path, f"ref:{case_id}")
        elif operator == "in":
            allowed_values = list(expected_value)
            _set_path(actual_result, path, allowed_values[0] if allowed_values else "")
        else:
            _set_path(actual_result, path, deepcopy(expected_value))
    return actual_result


def _validate_revision_evidence_binding(
    execution_revision: str,
    evidence_refs: Sequence[str],
    failures: list[dict[str, Any]],
) -> None:
    revision = _non_empty_string(execution_revision)
    if not revision:
        return
    if not any(revision in evidence_ref for evidence_ref in evidence_refs):
        failures.append(
            _failure(
                "operability_gate",
                "execution_revision_evidence_mismatch",
                "execution_revision must be traceable from gate or case evidence refs",
                details={"execution_revision": revision},
            )
        )


def _normalize_string_list(
    raw_value: Any,
    field_name: str,
    failures: list[dict[str, Any]],
    *,
    failure_source: str = "operability_gate",
    allow_empty: bool = False,
) -> list[str]:
    if not isinstance(raw_value, Iterable) or isinstance(raw_value, (Mapping, str, bytes)):
        failures.append(_failure(failure_source, f"invalid_{field_name}", f"{field_name} must be a string sequence"))
        return []
    normalized: list[str] = []
    for item in raw_value:
        text = _non_empty_string(item)
        if not text:
            failures.append(_failure(failure_source, f"invalid_{field_name}", f"{field_name} entries must be non-empty strings"))
            continue
        normalized.append(text)
    if not allow_empty and not normalized:
        failures.append(_failure(failure_source, f"missing_{field_name}", f"{field_name} must be non-empty"))
    if len(set(normalized)) != len(normalized):
        failures.append(_failure(failure_source, f"duplicate_{field_name}", f"{field_name} must not contain duplicates"))
        normalized = _dedupe_sorted(normalized)
    return normalized


def _normalize_evidence_refs(
    raw_evidence_refs: Sequence[str] | Iterable[str] | None,
    failures: list[dict[str, Any]],
    *,
    source: str = "operability_gate",
) -> list[str]:
    if raw_evidence_refs is None:
        return []
    return _normalize_string_list(raw_evidence_refs, "evidence_refs", failures, failure_source=source)


def _failure(source: str, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        "source": source,
        "code": code,
        "message": message,
        "details": _json_safe(dict(details or {})),
    }


def _case_failure(case_id: str, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return _failure("operability_case", code, message, details={"case_id": case_id, **dict(details or {})})


def _dedupe_failures(failures: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for failure in failures:
        key = _canonical_json(failure)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(dict(failure))
    return normalized


def _failed_case_ids(cases: Sequence[Mapping[str, Any]], failures: Sequence[Mapping[str, Any]]) -> set[str]:
    failed_ids = {str(case["case_id"]) for case in cases if case.get("verdict") != PASS_VERDICT}
    known_case_ids = {str(case["case_id"]) for case in cases}
    for failure in failures:
        details = failure.get("details")
        if not isinstance(details, Mapping):
            continue
        case_id = details.get("case_id")
        if isinstance(case_id, str) and case_id in known_case_ids:
            failed_ids.add(case_id)
    return failed_ids


def _dedupe_sorted(values: Iterable[str]) -> list[str]:
    return sorted(set(values))


def _non_empty_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _get_path(mapping: Mapping[str, Any], path: str) -> Any:
    value: Any = mapping
    for segment in path.split("."):
        if not isinstance(value, Mapping) or segment not in value:
            return None
        value = value[segment]
    return value


def _set_path(mapping: dict[str, Any], path: str, value: Any) -> None:
    current = mapping
    segments = path.split(".")
    for segment in segments[:-1]:
        child = current.get(segment)
        if not isinstance(child, dict):
            child = {}
            current[segment] = child
        current = child
    current[segments[-1]] = value


def _merge_mappings(primary: Mapping[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    merged = _json_safe(primary)
    if not isinstance(merged, dict):
        merged = {}
    for key, value in overlay.items():
        if isinstance(merged.get(key), dict) and isinstance(value, Mapping):
            merged[key] = _merge_mappings(merged[key], value)
        else:
            merged[key] = _json_safe(value)
    return merged


def _canonical_json(value: Any) -> str:
    return str(_json_safe(value))


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)
