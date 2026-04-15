from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


SOURCE_HARNESS = "harness"
SOURCE_REAL_ADAPTER_REGRESSION = "real_adapter_regression"
SOURCE_PLATFORM_LEAKAGE = "platform_leakage"
SOURCE_VERSION_GATE = "version_gate"

PASS_VERDICT = "pass"
FAIL_VERDICT = "fail"

_HARNESS_ALLOWED_VERDICTS = frozenset(
    {"pass", "legal_failure", "contract_violation", "execution_precondition_not_met"}
)
_HARNESS_LEGAL_FAILURE_ALLOWED_ERROR_CATEGORIES = frozenset({"invalid_input", "unsupported", "platform"})
_OBSERVED_RUNTIME_STATUSES = frozenset({"success", "failed"})
_REAL_REGRESSION_ALLOWED_ERROR_CATEGORIES = frozenset({"invalid_input", "platform"})
_REAL_REGRESSION_EXPECTED_OUTCOMES = frozenset({"success", "allowed_failure"})
_FROZEN_REAL_REGRESSION_SURFACE_BY_VERSION = {
    "v0.2.0": {
        "semantic_operation": "content_detail_by_url",
        "target_type": "url",
        "accepted_operations": ("content_detail_by_url", "content_detail"),
    },
}
_FROZEN_REFERENCE_PAIR_BY_VERSION = {
    "v0.2.0": ("xhs", "douyin"),
}
_FROZEN_HARNESS_REQUIRED_SAMPLE_IDS_BY_VERSION: dict[str, tuple[str, ...]] = {}
_REQUIRED_LEAKAGE_BOUNDARIES = frozenset(
    {
        "core_runtime",
        "shared_input_model",
        "shared_error_model",
        "adapter_registry",
        "shared_result_contract",
        "version_gate_logic",
    }
)


def build_harness_source_report(
    validation_results: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]],
    required_sample_ids: Sequence[str] | Iterable[str],
    *,
    version: str,
) -> dict[str, Any]:
    canonical_version = _canonical_version(version)
    failures: list[dict[str, Any]] = []
    normalized_required = _normalize_required_sample_ids(required_sample_ids, failures)
    normalized_results = _normalize_harness_validation_results(validation_results, failures)

    result_index = {result["sample_id"]: result for result in normalized_results}
    missing_sample_ids = [sample_id for sample_id in normalized_required if sample_id not in result_index]
    if missing_sample_ids:
        failures.append(
            _failure(
                SOURCE_HARNESS,
                "missing_required_harness_samples",
                "required harness sample set is incomplete",
                details={"missing_sample_ids": missing_sample_ids},
            )
        )

    for result in normalized_results:
        verdict = result["verdict"]
        if verdict == "contract_violation":
            failures.append(
                _failure(
                    SOURCE_HARNESS,
                    "contract_violation_observed",
                    "harness observed contract violation",
                    details={
                        "sample_id": result["sample_id"],
                        "reason": dict(result["reason"]),
                    },
                )
            )
        elif verdict == "execution_precondition_not_met":
            failures.append(
                _failure(
                    SOURCE_HARNESS,
                    "execution_precondition_not_met_observed",
                    "harness execution precondition is not met",
                    details={
                        "sample_id": result["sample_id"],
                        "reason": dict(result["reason"]),
                    },
                )
            )

    evidence_refs = [f"harness_validation:{sample_id}" for sample_id in sorted(result_index)]
    if not _is_non_empty_string(version):
        failures.append(
            _failure(
                SOURCE_HARNESS,
                "missing_version",
                "harness source report requires non-empty version",
            )
        )
    evidence_refs = _finalize_evidence_refs(evidence_refs, source=SOURCE_HARNESS, failures=failures)

    summary = (
        f"harness passed for version `{version}` with {len(normalized_results)} validated samples"
        if not failures
        else f"harness failed for version `{version or 'unknown'}`"
    )
    return _source_report(
        source=SOURCE_HARNESS,
        version=canonical_version,
        verdict=PASS_VERDICT if not failures else FAIL_VERDICT,
        summary=summary,
        evidence_refs=evidence_refs,
        details={
            "required_sample_ids": list(normalized_required),
            "observed_sample_ids": sorted(result_index),
            "validation_results": normalized_results,
            "failures": failures,
        },
    )


def validate_real_adapter_regression_source_report(
    report: Mapping[str, Any] | None,
    *,
    version: str,
    reference_pair: Sequence[str] | Iterable[str],
    operation: str = "content_detail_by_url",
    target_type: str | None = None,
) -> dict[str, Any]:
    source = SOURCE_REAL_ADAPTER_REGRESSION
    canonical_version = _canonical_version(version)
    failures: list[dict[str, Any]] = []
    if not _is_non_empty_string(version):
        failures.append(
            _failure(
                source,
                "missing_version",
                "real adapter regression source report requires non-empty version",
            )
        )
    expected_reference_pair = _normalize_reference_pair(reference_pair, source, failures)
    _enforce_frozen_reference_pair(version, expected_reference_pair, source, failures)
    frozen_surface = _frozen_real_regression_surface(version)
    if frozen_surface is None:
        failures.append(
            _failure(
                source,
                "missing_frozen_operation_for_version",
                "real adapter regression operation surface is not frozen for this version and must fail closed",
                details={"version": version},
            )
        )
        expected_surface = None
    else:
        expected_surface = _normalize_real_regression_surface(
            operation,
            target_type,
            version=version,
            source=source,
            failures=failures,
            code="operation_not_frozen_for_version",
            message="real adapter regression validator operation surface must match the formal-spec approved regression surface",
        )
    payload = _require_mapping(report, source, "invalid_real_adapter_regression_report", failures)
    evidence_refs = _normalize_evidence_refs(
        payload.get("evidence_refs"),
        source=source,
        field_name="evidence_refs",
        failures=failures,
    )

    payload_version = payload.get("version")
    if payload_version != version:
        failures.append(
            _failure(
                source,
                "version_mismatch",
                "real adapter regression report version does not match gate version",
                details={"expected_version": version, "actual_version": payload_version},
            )
        )

    if frozen_surface is None:
        payload_surface = None
    else:
        payload_surface = _normalize_real_regression_surface(
            payload.get("operation"),
            payload.get("target_type"),
            version=version,
            source=source,
            failures=failures,
            code="operation_mismatch",
            message="real adapter regression report operation surface does not match the formal-spec approved regression surface",
        )

    payload_reference_pair = _normalize_reference_pair(
        payload.get("reference_pair"),
        source,
        failures,
        code="invalid_report_reference_pair",
        message="real adapter regression report must carry a complete reference pair",
    )
    if payload_reference_pair and sorted(payload_reference_pair) != sorted(expected_reference_pair):
        failures.append(
            _failure(
                source,
                "reference_pair_mismatch",
                "real adapter regression report reference pair does not match gate reference pair",
                details={
                    "expected_reference_pair": expected_reference_pair,
                    "actual_reference_pair": payload_reference_pair,
                },
            )
        )

    adapter_results = _normalize_adapter_results(payload.get("adapter_results"), source, failures)
    adapters_by_key = {entry["adapter_key"]: entry for entry in adapter_results}
    for adapter_key in expected_reference_pair:
        adapter_result = adapters_by_key.get(adapter_key)
        if adapter_result is None:
            failures.append(
                _failure(
                    source,
                    "missing_adapter_result",
                    "real adapter regression report is missing adapter coverage",
                    details={"adapter_key": adapter_key},
                )
            )
            continue
        cases = adapter_result["cases"]
        success_covered = False
        failure_covered = False
        for case in cases:
            expected_outcome = case["expected_outcome"]
            observed_status = case["observed_status"]
            observed_error_category = case["observed_error_category"]
            case_details = {"adapter_key": adapter_key, "case_id": case["case_id"]}
            if expected_outcome == "success":
                if observed_status == "success":
                    success_covered = True
                    continue
                failures.append(
                    _failure(
                        source,
                        "expected_success_not_observed",
                        "real adapter regression expected success but observed failure",
                        details=case_details,
                    )
                )
                continue
            if observed_status != "failed":
                failures.append(
                    _failure(
                        source,
                        "expected_failure_not_observed",
                        "real adapter regression expected allowed failure but observed success",
                        details=case_details,
                    )
                )
                continue
            if observed_error_category not in _REAL_REGRESSION_ALLOWED_ERROR_CATEGORIES:
                failures.append(
                    _failure(
                        source,
                        "disallowed_failure_category",
                        "real adapter regression observed failure category outside allowed set",
                        details={
                            **case_details,
                            "observed_error_category": observed_error_category,
                        },
                    )
                )
                continue
            failure_covered = True
        if not success_covered:
            failures.append(
                _failure(
                    source,
                    "missing_success_coverage",
                    "real adapter regression is missing at least one successful case",
                    details={"adapter_key": adapter_key},
                )
            )
        if not failure_covered:
            failures.append(
                _failure(
                    source,
                    "missing_allowed_failure_coverage",
                    "real adapter regression is missing at least one allowed failure case",
                    details={"adapter_key": adapter_key},
                )
            )

    unexpected_adapters = sorted(set(adapters_by_key) - set(expected_reference_pair))
    if unexpected_adapters:
        failures.append(
            _failure(
                source,
                "unexpected_adapter_results",
                "real adapter regression report carries unexpected adapter coverage",
                details={"unexpected_adapter_keys": unexpected_adapters},
            )
        )

    evidence_refs = _finalize_evidence_refs(evidence_refs, source=source, failures=failures)
    summary = (
        f"real adapter regression passed for version `{version}`"
        if not failures
        else f"real adapter regression failed for version `{version}`"
    )
    return _source_report(
        source=source,
        version=canonical_version,
        verdict=PASS_VERDICT if not failures else FAIL_VERDICT,
        summary=summary,
        evidence_refs=evidence_refs,
        details={
            "reference_pair": _canonical_reference_pair(version, expected_reference_pair),
            "operation": (
                payload_surface["operation"]
                if payload_surface is not None
                else expected_surface["operation"]
                if expected_surface is not None
                else frozen_surface["semantic_operation"]
                if frozen_surface is not None
                else ""
            ),
            "target_type": (
                payload_surface["target_type"]
                if payload_surface is not None
                else expected_surface["target_type"]
                if expected_surface is not None
                else frozen_surface["target_type"]
                if frozen_surface is not None
                else ""
            ),
            "semantic_operation": frozen_surface["semantic_operation"] if frozen_surface is not None else "",
            "adapter_results": adapter_results,
            "failures": failures,
        },
    )


def validate_platform_leakage_source_report(
    report: Mapping[str, Any] | None,
    *,
    version: str,
) -> dict[str, Any]:
    source = SOURCE_PLATFORM_LEAKAGE
    canonical_version = _canonical_version(version)
    failures: list[dict[str, Any]] = []
    if not _is_non_empty_string(version):
        failures.append(
            _failure(
                source,
                "missing_version",
                "platform leakage source report requires non-empty version",
            )
        )
    payload = _require_mapping(report, source, "invalid_platform_leakage_report", failures)
    evidence_refs = _normalize_evidence_refs(
        payload.get("evidence_refs"),
        source=source,
        field_name="evidence_refs",
        failures=failures,
    )

    payload_version = payload.get("version")
    if payload_version != version:
        failures.append(
            _failure(
                source,
                "version_mismatch",
                "platform leakage report version does not match gate version",
                details={"expected_version": version, "actual_version": payload_version},
            )
        )

    boundaries = _normalize_boundaries(payload.get("boundary_scope"), source, failures)
    missing_boundaries = sorted(_REQUIRED_LEAKAGE_BOUNDARIES - set(boundaries))
    if missing_boundaries:
        failures.append(
            _failure(
                source,
                "missing_boundary_scope",
                "platform leakage report does not cover the full required boundary scope",
                details={"missing_boundaries": missing_boundaries},
            )
        )
    unexpected_boundaries = sorted(set(boundaries) - _REQUIRED_LEAKAGE_BOUNDARIES)
    if unexpected_boundaries:
        failures.append(
            _failure(
                source,
                "unexpected_boundary_scope",
                "platform leakage report must not carry boundaries outside the fixed leakage contract",
                details={"unexpected_boundaries": unexpected_boundaries},
            )
        )

    findings = _normalize_leakage_findings(payload.get("findings"), source, failures)
    payload_verdict = _normalize_allowed_string(
        payload.get("verdict"),
        source=source,
        field_name="verdict",
        allowed_values=frozenset({PASS_VERDICT, FAIL_VERDICT}),
        failures=failures,
        code="invalid_leakage_verdict",
        message="platform leakage report verdict must be `pass` or `fail`",
        actual_key="actual_verdict",
    )
    if payload_verdict is None:
        payload_verdict = FAIL_VERDICT

    if payload_verdict == PASS_VERDICT and findings:
        failures.append(
            _failure(
                source,
                "pass_report_with_findings",
                "platform leakage pass report cannot carry findings",
            )
        )
    if payload_verdict == FAIL_VERDICT and not findings:
        failures.append(
            _failure(
                source,
                "failure_report_without_findings",
                "platform leakage failure report must carry findings",
            )
        )

    gate_failures = [_failure_from_leakage_finding(source, finding) for finding in findings] if payload_verdict == FAIL_VERDICT else []
    normalized_failures = failures + gate_failures
    evidence_refs = _finalize_evidence_refs(evidence_refs, source=source, failures=normalized_failures)
    summary = str(payload.get("summary") or "").strip()
    if normalized_failures:
        summary = f"platform leakage failed for version `{version}`"
    elif not summary:
        summary = (
            f"platform leakage passed for version `{version}`"
            if not normalized_failures
            else f"platform leakage failed for version `{version}`"
        )

    return _source_report(
        source=source,
        version=canonical_version,
        verdict=PASS_VERDICT if not normalized_failures else FAIL_VERDICT,
        summary=summary,
        evidence_refs=evidence_refs,
        details={
            "boundary_scope": boundaries,
            "report_verdict": payload_verdict,
            "findings": findings,
            "failures": normalized_failures,
        },
    )


def orchestrate_version_gate(
    *,
    version: str,
    reference_pair: Sequence[str] | Iterable[str],
    harness_report: Mapping[str, Any] | None,
    real_adapter_regression_report: Mapping[str, Any] | None,
    platform_leakage_report: Mapping[str, Any] | None,
    required_harness_sample_ids: Sequence[str] | Iterable[str] | None = None,
) -> dict[str, Any]:
    canonical_version = _canonical_version(version)
    failures: list[dict[str, Any]] = []
    normalized_reference_pair = _normalize_reference_pair(
        reference_pair,
        SOURCE_VERSION_GATE,
        failures,
        code="invalid_reference_pair",
        message="version gate requires a complete reference pair",
    )
    _enforce_frozen_reference_pair(version, normalized_reference_pair, SOURCE_VERSION_GATE, failures)
    if not _is_non_empty_string(version):
        failures.append(
            _failure(
                SOURCE_VERSION_GATE,
                "missing_version",
                "version gate requires non-empty version",
            )
        )
    normalized_required_harness_sample_ids = _resolve_gate_required_harness_sample_ids(
        required_harness_sample_ids,
        version=version,
        failures=failures,
    )

    source_reports = {
        SOURCE_HARNESS: _normalize_existing_source_report(
            harness_report,
            SOURCE_HARNESS,
            version=canonical_version,
            gate_reference_pair=_canonical_reference_pair(version, normalized_reference_pair),
            gate_required_harness_sample_ids=normalized_required_harness_sample_ids,
        ),
        SOURCE_REAL_ADAPTER_REGRESSION: _normalize_existing_source_report(
            real_adapter_regression_report,
            SOURCE_REAL_ADAPTER_REGRESSION,
            version=canonical_version,
            gate_reference_pair=_canonical_reference_pair(version, normalized_reference_pair),
            gate_required_harness_sample_ids=normalized_required_harness_sample_ids,
        ),
        SOURCE_PLATFORM_LEAKAGE: _normalize_existing_source_report(
            platform_leakage_report,
            SOURCE_PLATFORM_LEAKAGE,
            version=canonical_version,
            gate_reference_pair=_canonical_reference_pair(version, normalized_reference_pair),
            gate_required_harness_sample_ids=normalized_required_harness_sample_ids,
        ),
    }

    for report in source_reports.values():
        failures.extend(report["details"]["failures"])
        if report["verdict"] != PASS_VERDICT and not report["details"]["failures"]:
            failures.append(
                _failure(
                    report["source"],
                    "source_report_failed_without_reason",
                    "source report failed without explicit failure payload",
                )
            )

    verdict = PASS_VERDICT if not failures else FAIL_VERDICT
    failing_sources = [source for source, report in source_reports.items() if report["verdict"] != PASS_VERDICT]
    if failures and not failing_sources and any(item["source"] == SOURCE_VERSION_GATE for item in failures):
        failing_sources.append(SOURCE_VERSION_GATE)

    summary = (
        f"version gate passed for version `{canonical_version}`"
        if verdict == PASS_VERDICT
        else f"version gate failed for version `{canonical_version}` via {', '.join(sorted(set(failing_sources)))}"
    )
    return {
        "version": canonical_version,
        "reference_pair": _canonical_reference_pair(version, normalized_reference_pair),
        "verdict": verdict,
        "safe_to_release": verdict == PASS_VERDICT,
        "summary": summary,
        "source_reports": source_reports,
        "failures": failures,
    }


def _normalize_existing_source_report(
    report: Mapping[str, Any] | None,
    expected_source: str,
    *,
    version: str,
    gate_reference_pair: Sequence[str] | None,
    gate_required_harness_sample_ids: Sequence[str],
) -> dict[str, Any]:
    if not isinstance(report, Mapping):
        return _synthetic_failed_source_report(
            source=expected_source,
            version=version,
            gate_reference_pair=gate_reference_pair,
            summary=f"{expected_source} source report is missing",
            failure=_failure(
                expected_source,
                "missing_source_report",
                "version gate requires all mandatory source reports",
            ),
        )

    source = report.get("source")
    if source != expected_source:
        return _synthetic_failed_source_report(
            source=expected_source,
            version=version,
            gate_reference_pair=gate_reference_pair,
            summary=f"{expected_source} source report is invalid",
            failure=_failure(
                expected_source,
                "source_mismatch",
                "source report name does not match expected source",
                details={"actual_source": source},
            ),
        )

    report_version = report.get("version")
    if report_version != version:
        return _synthetic_failed_source_report(
            source=expected_source,
            version=version,
            gate_reference_pair=gate_reference_pair,
            summary=f"{expected_source} source report version mismatch",
            failure=_failure(
                expected_source,
                "source_report_version_mismatch",
                "source report version does not match orchestrated version",
                details={"expected_version": version, "actual_version": report_version},
            ),
        )
    report_verdict_failures: list[dict[str, Any]] = []
    report_verdict = _normalize_allowed_string(
        report.get("verdict"),
        source=expected_source,
        field_name="verdict",
        allowed_values=frozenset({PASS_VERDICT, FAIL_VERDICT}),
        failures=report_verdict_failures,
        code="invalid_source_verdict",
        message="source report verdict must be `pass` or `fail`",
        actual_key="actual_verdict",
    )
    if report_verdict is None:
        return _synthetic_failed_source_report(
            source=expected_source,
            version=version,
            gate_reference_pair=gate_reference_pair,
            summary=f"{expected_source} source report is invalid",
            failure=report_verdict_failures[0],
        )
    evidence_refs = report.get("evidence_refs")
    if not _is_string_sequence(evidence_refs) or not evidence_refs:
        return _synthetic_failed_source_report(
            source=expected_source,
            version=version,
            gate_reference_pair=gate_reference_pair,
            summary=f"{expected_source} source report is missing evidence refs",
            failure=_failure(
                expected_source,
                "missing_source_evidence_refs",
                "source report must carry non-empty evidence refs",
            ),
        )
    report_summary = str(report.get("summary") or "").strip()
    if not report_summary:
        return _synthetic_failed_source_report(
            source=expected_source,
            version=version,
            gate_reference_pair=gate_reference_pair,
            summary=f"{expected_source} source report is invalid",
            failure=_failure(
                expected_source,
                "missing_source_summary",
                "source report must carry non-empty summary",
            ),
        )

    details = report.get("details")
    if not isinstance(details, Mapping):
        return _synthetic_failed_source_report(
            source=expected_source,
            version=version,
            gate_reference_pair=gate_reference_pair,
            summary=f"{expected_source} source report is invalid",
            failure=_failure(
                expected_source,
                "invalid_source_details",
                "source report details must be a mapping",
            ),
        )
    report_failures = details.get("failures")
    if not isinstance(report_failures, list):
        return _synthetic_failed_source_report(
            source=expected_source,
            version=version,
            gate_reference_pair=gate_reference_pair,
            summary=f"{expected_source} source report is invalid",
            failure=_failure(
                expected_source,
                "missing_source_failures",
                "source report details must carry a failures list",
            ),
        )

    if expected_source == SOURCE_HARNESS:
        raw_required_sample_ids = details.get("required_sample_ids")
        raw_observed_sample_ids = details.get("observed_sample_ids")
        raw_validation_results = details.get("validation_results")
        if raw_required_sample_ids is None or raw_observed_sample_ids is None or raw_validation_results is None:
            return _synthetic_failed_source_report(
                source=expected_source,
                version=version,
                gate_reference_pair=gate_reference_pair,
                summary=f"{expected_source} source report is incomplete",
                failure=_failure(
                    expected_source,
                    "missing_harness_details",
                    "harness source report must carry required_sample_ids, observed_sample_ids and validation_results",
                ),
            )
        normalized_required_sample_ids = _normalize_report_required_sample_ids(raw_required_sample_ids)
        if normalized_required_sample_ids is None:
            return _synthetic_failed_source_report(
                source=expected_source,
                version=version,
                gate_reference_pair=gate_reference_pair,
                summary=f"{expected_source} source report is invalid",
                failure=_failure(
                    expected_source,
                    "invalid_required_sample_ids",
                    "harness source report required_sample_ids must be a string list without duplicates",
                ),
            )
        if sorted(normalized_required_sample_ids) != sorted(gate_required_harness_sample_ids):
            return _synthetic_failed_source_report(
                source=expected_source,
                version=version,
                gate_reference_pair=gate_reference_pair,
                summary=f"{expected_source} source report is invalid",
                failure=_failure(
                    expected_source,
                    "harness_required_sample_ids_mismatch",
                    "harness source report required_sample_ids must match the version-gate required sample baseline",
                    details={
                        "expected_required_sample_ids": list(gate_required_harness_sample_ids),
                        "actual_required_sample_ids": list(normalized_required_sample_ids),
                    },
                ),
            )
        rebuilt_report = build_harness_source_report(
            raw_validation_results,
            gate_required_harness_sample_ids,
            version=version,
        )
        normalized_observed_sample_ids = _normalize_harness_observed_sample_ids(
            raw_observed_sample_ids,
            expected_source,
            version=version,
            gate_reference_pair=gate_reference_pair,
        )
        if normalized_observed_sample_ids is None:
            return _synthetic_failed_source_report(
                source=expected_source,
                version=version,
                gate_reference_pair=gate_reference_pair,
                summary=f"{expected_source} source report is invalid",
                failure=_failure(
                    expected_source,
                    "invalid_harness_observed_sample_ids",
                    "harness source report observed_sample_ids must be a string list without duplicates",
                ),
            )
        rebuilt_observed_sample_ids = rebuilt_report["details"]["observed_sample_ids"]
        if sorted(normalized_observed_sample_ids) != rebuilt_observed_sample_ids:
            return _synthetic_failed_source_report(
                source=expected_source,
                version=version,
                gate_reference_pair=gate_reference_pair,
                summary=f"{expected_source} source report is invalid",
                failure=_failure(
                    expected_source,
                    "harness_observed_sample_ids_mismatch",
                    "harness source report observed_sample_ids must match validation_results",
                    details={
                        "expected_observed_sample_ids": rebuilt_observed_sample_ids,
                        "actual_observed_sample_ids": normalized_observed_sample_ids,
                    },
                ),
            )
        if report_verdict == PASS_VERDICT and list(evidence_refs) != rebuilt_report["evidence_refs"]:
            return _synthetic_failed_source_report(
                source=expected_source,
                version=version,
                gate_reference_pair=gate_reference_pair,
                summary=f"{expected_source} source report is invalid",
                failure=_failure(
                    expected_source,
                    "harness_evidence_refs_mismatch",
                    "harness source report evidence_refs must match the deterministic builder output",
                    details={
                        "expected_evidence_refs": rebuilt_report["evidence_refs"],
                        "actual_evidence_refs": list(evidence_refs),
                    },
                ),
            )
        return _merge_rebuilt_source_report_with_input_failures(
            rebuilt_report,
            input_verdict=report_verdict,
            input_summary=report_summary,
            input_evidence_refs=evidence_refs,
            normalized_report_failures=_normalize_failure_entries(report_failures, expected_source),
        )

    if expected_source == SOURCE_REAL_ADAPTER_REGRESSION:
        raw_reference_pair = details.get("reference_pair")
        raw_operation = details.get("operation")
        raw_target_type = details.get("target_type")
        raw_semantic_operation = details.get("semantic_operation")
        raw_adapter_results = details.get("adapter_results")
        if (
            raw_reference_pair is None
            or raw_operation is None
            or raw_target_type is None
            or raw_semantic_operation is None
            or raw_adapter_results is None
        ):
            return _synthetic_failed_source_report(
                source=expected_source,
                version=version,
                gate_reference_pair=gate_reference_pair,
                summary=f"{expected_source} source report is incomplete",
                failure=_failure(
                    expected_source,
                    "missing_real_regression_details",
                    "real adapter regression source report must carry reference_pair, operation, target_type, semantic_operation and adapter_results",
                ),
            )
        rebuilt_report = validate_real_adapter_regression_source_report(
            {
                "version": version,
                "reference_pair": raw_reference_pair,
                "operation": raw_operation,
                "target_type": raw_target_type,
                "adapter_results": raw_adapter_results,
                "evidence_refs": evidence_refs,
            },
            version=version,
            reference_pair=gate_reference_pair or raw_reference_pair,
            operation=raw_operation,
            target_type=raw_target_type,
        )
        rebuilt_details = rebuilt_report["details"]
        if raw_semantic_operation != rebuilt_details["semantic_operation"]:
            return _synthetic_failed_source_report(
                source=expected_source,
                version=version,
                gate_reference_pair=gate_reference_pair,
                summary=f"{expected_source} source report is invalid",
                failure=_failure(
                    expected_source,
                    "real_regression_semantic_operation_mismatch",
                    "real adapter regression source report semantic_operation must match the normalized regression surface",
                    details={
                        "expected_semantic_operation": rebuilt_details["semantic_operation"],
                        "actual_semantic_operation": raw_semantic_operation,
                    },
                ),
            )
        return _merge_rebuilt_source_report_with_input_failures(
            rebuilt_report,
            input_verdict=report_verdict,
            input_summary=report_summary,
            input_evidence_refs=evidence_refs,
            normalized_report_failures=_normalize_failure_entries(report_failures, expected_source),
        )

    raw_boundary_scope = details.get("boundary_scope")
    raw_report_verdict = details.get("report_verdict")
    raw_findings = details.get("findings")
    if raw_boundary_scope is None or raw_report_verdict is None or raw_findings is None:
        return _synthetic_failed_source_report(
            source=expected_source,
            version=version,
            gate_reference_pair=gate_reference_pair,
            summary=f"{expected_source} source report is incomplete",
            failure=_failure(
                expected_source,
                "missing_platform_leakage_details",
                "platform leakage source report must carry boundary_scope, report_verdict and findings",
            ),
        )
    rebuilt_report = validate_platform_leakage_source_report(
        {
            "version": version,
            "boundary_scope": raw_boundary_scope,
            "verdict": raw_report_verdict,
            "summary": str(report.get("summary") or "").strip(),
            "findings": raw_findings,
            "evidence_refs": evidence_refs,
        },
        version=version,
    )
    return _merge_rebuilt_source_report_with_input_failures(
        rebuilt_report,
        input_verdict=report_verdict,
        input_summary=report_summary,
        input_evidence_refs=evidence_refs,
        normalized_report_failures=_normalize_failure_entries(report_failures, expected_source),
    )


def _normalize_required_sample_ids(
    raw_sample_ids: Sequence[str] | Iterable[str],
    failures: list[dict[str, Any]],
) -> list[str]:
    sample_ids = _normalize_string_list(
        raw_sample_ids,
        source=SOURCE_HARNESS,
        field_name="required_sample_ids",
        failures=failures,
        code="invalid_required_sample_ids",
        message="required harness sample ids must be a non-empty string sequence",
    )
    if not sample_ids:
        failures.append(
            _failure(
                SOURCE_HARNESS,
                "empty_required_sample_ids",
                "required harness sample ids cannot be empty",
            )
        )
    return sample_ids


def _normalize_harness_validation_results(
    validation_results: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]],
    failures: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if isinstance(validation_results, (str, bytes)) or not isinstance(validation_results, Iterable):
        failures.append(
            _failure(
                SOURCE_HARNESS,
                "invalid_validation_results",
                "harness validation results must be an iterable of mappings",
            )
        )
        return []

    normalized_results: list[dict[str, Any]] = []
    seen_sample_ids: set[str] = set()
    for index, result in enumerate(validation_results):
        if not isinstance(result, Mapping):
            failures.append(
                _failure(
                    SOURCE_HARNESS,
                    "invalid_validation_result_entry",
                    "harness validation result entry must be a mapping",
                    details={"index": index},
                )
            )
            continue
        sample_id = result.get("sample_id")
        if not _is_non_empty_string(sample_id):
            failures.append(
                _failure(
                    SOURCE_HARNESS,
                    "invalid_sample_id",
                    "harness validation result must carry non-empty sample_id",
                    details={"index": index},
                )
            )
            continue
        if sample_id in seen_sample_ids:
            failures.append(
                _failure(
                    SOURCE_HARNESS,
                    "duplicate_sample_id",
                    "harness validation results cannot repeat sample_id",
                    details={"sample_id": sample_id},
                )
            )
            continue
        seen_sample_ids.add(sample_id)

        verdict = _normalize_allowed_string(
            result.get("verdict"),
            source=SOURCE_HARNESS,
            field_name="verdict",
            allowed_values=_HARNESS_ALLOWED_VERDICTS,
            failures=failures,
            code="invalid_harness_verdict",
            message="harness validation result verdict is unsupported",
            details={"sample_id": sample_id},
        )
        if verdict is None:
            continue

        reason = result.get("reason")
        if not isinstance(reason, Mapping):
            failures.append(
                _failure(
                    SOURCE_HARNESS,
                    "invalid_reason_object",
                    "harness validation result must carry reason.code and reason.message",
                    details={"sample_id": sample_id},
                )
            )
            continue
        reason_code = reason.get("code")
        reason_message = reason.get("message")
        if not _is_non_empty_string(reason_code) or not _is_non_empty_string(reason_message):
            failures.append(
                _failure(
                    SOURCE_HARNESS,
                    "invalid_reason_fields",
                    "harness validation result reason must carry non-empty code and message",
                    details={"sample_id": sample_id},
                )
            )
            continue

        observed_status = result.get("observed_status")
        if observed_status is not None:
            observed_status = _normalize_allowed_string(
                observed_status,
                source=SOURCE_HARNESS,
                field_name="observed_status",
                allowed_values=_OBSERVED_RUNTIME_STATUSES,
                failures=failures,
                code="invalid_observed_status",
                message="harness validation result observed_status is unsupported",
                details={"sample_id": sample_id},
            )
            if observed_status is None:
                continue

        observed_error = result.get("observed_error")
        normalized_observed_error = _normalize_observed_error(
            observed_error,
            sample_id=sample_id,
            failures=failures,
        )
        if observed_error is not None and normalized_observed_error is None:
            continue

        if verdict == "pass":
            if observed_status != "success" or normalized_observed_error is not None:
                failures.append(
                    _failure(
                        SOURCE_HARNESS,
                        "inconsistent_pass_observation",
                        "harness pass verdict must observe success without runtime error",
                        details={"sample_id": sample_id},
                    )
                )
                continue
        elif verdict == "legal_failure":
            if observed_status != "failed" or normalized_observed_error is None:
                failures.append(
                    _failure(
                        SOURCE_HARNESS,
                        "inconsistent_legal_failure_observation",
                        "harness legal_failure verdict must observe failed runtime envelope with error",
                        details={"sample_id": sample_id},
                    )
                )
                continue
            if normalized_observed_error["category"] not in _HARNESS_LEGAL_FAILURE_ALLOWED_ERROR_CATEGORIES:
                failures.append(
                    _failure(
                        SOURCE_HARNESS,
                        "unsupported_legal_failure_category",
                        "harness legal_failure verdict must align to approved runtime error categories",
                        details={
                            "sample_id": sample_id,
                            "category": normalized_observed_error["category"],
                        },
                    )
                )
                continue
        elif verdict == "execution_precondition_not_met":
            if observed_status is not None or normalized_observed_error is not None:
                failures.append(
                    _failure(
                        SOURCE_HARNESS,
                        "inconsistent_precondition_observation",
                        "execution_precondition_not_met must not carry runtime observation",
                        details={"sample_id": sample_id},
                    )
                )
                continue
        else:
            if observed_status == "success" and normalized_observed_error is not None:
                failures.append(
                    _failure(
                        SOURCE_HARNESS,
                        "contract_violation_success_with_error",
                        "contract_violation with success observation cannot carry runtime error",
                        details={"sample_id": sample_id},
                    )
                )
                continue
            if observed_status == "failed" and normalized_observed_error is None:
                failures.append(
                    _failure(
                        SOURCE_HARNESS,
                        "contract_violation_failed_without_error",
                        "contract_violation with failed observation must carry runtime error",
                        details={"sample_id": sample_id},
                    )
                )
                continue

        normalized_results.append(
            {
                "sample_id": sample_id,
                "verdict": verdict,
                "reason": {
                    "code": reason_code,
                    "message": reason_message,
                },
                "observed_status": observed_status,
                "observed_error": normalized_observed_error,
            }
        )
    return normalized_results


def _normalize_observed_error(
    observed_error: Any,
    *,
    sample_id: str,
    failures: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if observed_error is None:
        return None
    if not isinstance(observed_error, Mapping):
        failures.append(
            _failure(
                SOURCE_HARNESS,
                "invalid_observed_error",
                "harness validation result observed_error must be a mapping or null",
                details={"sample_id": sample_id},
            )
        )
        return None
    category = observed_error.get("category")
    code = observed_error.get("code")
    message = observed_error.get("message")
    details = observed_error.get("details")
    if not _is_non_empty_string(category) or not _is_non_empty_string(code) or not _is_non_empty_string(message):
        failures.append(
            _failure(
                SOURCE_HARNESS,
                "invalid_observed_error_fields",
                "harness validation result observed_error must carry non-empty category/code/message",
                details={"sample_id": sample_id},
            )
        )
        return None
    if not isinstance(details, Mapping):
        failures.append(
            _failure(
                SOURCE_HARNESS,
                "invalid_observed_error_details",
                "harness validation result observed_error.details must be a mapping",
                details={"sample_id": sample_id},
            )
        )
        return None
    return {
        "category": category,
        "code": code,
        "message": message,
        "details": _sanitize_failure_details(details),
    }


def _normalize_adapter_results(
    raw_adapter_results: Any,
    source: str,
    failures: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if isinstance(raw_adapter_results, (str, bytes)) or not isinstance(raw_adapter_results, Iterable):
        failures.append(
            _failure(
                source,
                "invalid_adapter_results",
                "real adapter regression report must carry iterable adapter_results",
            )
        )
        return []

    normalized_results: list[dict[str, Any]] = []
    seen_adapter_keys: set[str] = set()
    for entry in raw_adapter_results:
        if not isinstance(entry, Mapping):
            failures.append(
                _failure(
                    source,
                    "invalid_adapter_result_entry",
                    "adapter_results entry must be a mapping",
                )
            )
            continue
        adapter_key = entry.get("adapter_key")
        if not _is_non_empty_string(adapter_key):
            failures.append(
                _failure(
                    source,
                    "invalid_adapter_key",
                    "adapter result must carry non-empty adapter_key",
                )
            )
            continue
        if adapter_key in seen_adapter_keys:
            failures.append(
                _failure(
                    source,
                    "duplicate_adapter_key",
                    "adapter_results cannot repeat adapter_key",
                    details={"adapter_key": adapter_key},
                )
            )
            continue
        seen_adapter_keys.add(adapter_key)
        cases = _normalize_regression_cases(entry.get("cases"), source, failures, adapter_key=adapter_key)
        normalized_results.append({"adapter_key": adapter_key, "cases": cases})
    return normalized_results


def _normalize_regression_cases(
    raw_cases: Any,
    source: str,
    failures: list[dict[str, Any]],
    *,
    adapter_key: str,
) -> list[dict[str, Any]]:
    if isinstance(raw_cases, (str, bytes)) or not isinstance(raw_cases, Iterable):
        failures.append(
            _failure(
                source,
                "invalid_adapter_cases",
                "adapter result must carry iterable cases",
                details={"adapter_key": adapter_key},
            )
        )
        return []

    normalized_cases: list[dict[str, Any]] = []
    seen_case_ids: set[str] = set()
    for entry in raw_cases:
        if not isinstance(entry, Mapping):
            failures.append(
                _failure(
                    source,
                    "invalid_case_entry",
                    "adapter regression case must be a mapping",
                    details={"adapter_key": adapter_key},
                )
            )
            continue
        case_id = entry.get("case_id")
        if not _is_non_empty_string(case_id):
            failures.append(
                _failure(
                    source,
                    "invalid_case_id",
                    "adapter regression case must carry non-empty case_id",
                    details={"adapter_key": adapter_key},
                )
            )
            continue
        if case_id in seen_case_ids:
            failures.append(
                _failure(
                    source,
                    "duplicate_case_id",
                    "adapter regression cases cannot repeat case_id",
                    details={"adapter_key": adapter_key, "case_id": case_id},
                )
            )
            continue
        seen_case_ids.add(case_id)
        expected_outcome = _normalize_allowed_string(
            entry.get("expected_outcome"),
            source=source,
            field_name="expected_outcome",
            allowed_values=_REAL_REGRESSION_EXPECTED_OUTCOMES,
            failures=failures,
            code="invalid_expected_outcome",
            message="adapter regression case expected_outcome is unsupported",
            details={"adapter_key": adapter_key, "case_id": case_id},
        )
        if expected_outcome is None:
            continue
        observed_status = _normalize_allowed_string(
            entry.get("observed_status"),
            source=source,
            field_name="observed_status",
            allowed_values=_OBSERVED_RUNTIME_STATUSES,
            failures=failures,
            code="invalid_observed_status",
            message="adapter regression case observed_status is unsupported",
            details={"adapter_key": adapter_key, "case_id": case_id},
        )
        if observed_status is None:
            continue
        observed_error_category = entry.get("observed_error_category")
        if observed_status == "success" and observed_error_category is not None:
            failures.append(
                _failure(
                    source,
                    "success_case_with_error_category",
                    "successful regression case cannot carry observed_error_category",
                    details={"adapter_key": adapter_key, "case_id": case_id},
                )
            )
            continue
        if observed_status == "failed" and not _is_non_empty_string(observed_error_category):
            failures.append(
                _failure(
                    source,
                    "failed_case_without_error_category",
                    "failed regression case must carry observed_error_category",
                    details={"adapter_key": adapter_key, "case_id": case_id},
                )
            )
            continue
        normalized_cases.append(
            {
                "case_id": case_id,
                "expected_outcome": expected_outcome,
                "observed_status": observed_status,
                "observed_error_category": observed_error_category,
            }
        )
    return normalized_cases


def _normalize_boundaries(
    raw_boundaries: Any,
    source: str,
    failures: list[dict[str, Any]],
) -> list[str]:
    return _normalize_string_list(
        raw_boundaries,
        source=source,
        field_name="boundary_scope",
        failures=failures,
        code="invalid_boundary_scope",
        message="platform leakage report boundary_scope must be a non-empty string sequence",
    )


def _normalize_leakage_findings(
    raw_findings: Any,
    source: str,
    failures: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if raw_findings is None:
        failures.append(
            _failure(
                source,
                "missing_leakage_findings",
                "platform leakage report must carry findings",
            )
        )
        return []
    if isinstance(raw_findings, (str, bytes)) or not isinstance(raw_findings, Iterable):
        failures.append(
            _failure(
                source,
                "invalid_leakage_findings",
                "platform leakage report findings must be iterable",
            )
        )
        return []
    normalized_findings: list[dict[str, Any]] = []
    for entry in raw_findings:
        if not isinstance(entry, Mapping):
            failures.append(
                _failure(
                    source,
                    "invalid_leakage_finding_entry",
                    "platform leakage finding must be a mapping",
                )
            )
            continue
        code = entry.get("code")
        message = entry.get("message")
        boundary = entry.get("boundary")
        evidence_ref = entry.get("evidence_ref")
        if not _is_non_empty_string(code) or not _is_non_empty_string(message):
            failures.append(
                _failure(
                    source,
                    "invalid_leakage_finding_fields",
                    "platform leakage finding must carry non-empty code and message",
                )
            )
            continue
        if not _is_non_empty_string(boundary):
            failures.append(
                _failure(
                    source,
                    "invalid_leakage_finding_boundary",
                    "platform leakage finding must carry non-empty boundary",
                    details={"code": code},
                )
            )
            continue
        if boundary not in _REQUIRED_LEAKAGE_BOUNDARIES:
            failures.append(
                _failure(
                    source,
                    "unsupported_leakage_finding_boundary",
                    "platform leakage finding boundary must stay within the shared leakage boundary contract",
                    details={"code": code, "boundary": boundary},
                )
            )
            continue
        if not _is_non_empty_string(evidence_ref):
            failures.append(
                _failure(
                    source,
                    "invalid_leakage_finding_evidence_ref",
                    "platform leakage finding must carry non-empty evidence_ref",
                    details={"code": code},
                )
            )
            continue
        normalized_findings.append(
            {
                "code": code,
                "message": message,
                "boundary": boundary,
                "evidence_ref": evidence_ref,
            }
        )
    return normalized_findings


def _normalize_reference_pair(
    raw_reference_pair: Sequence[str] | Iterable[str],
    source: str,
    failures: list[dict[str, Any]],
    *,
    code: str = "invalid_reference_pair",
    message: str = "reference pair must be a non-empty string sequence",
) -> list[str]:
    reference_pair = _normalize_string_list(
        raw_reference_pair,
        source=source,
        field_name="reference_pair",
        failures=failures,
        code=code,
        message=message,
    )
    if not reference_pair:
        failures.append(_failure(source, code, message))
    return reference_pair


def _normalize_evidence_refs(
    raw_evidence_refs: Any,
    *,
    source: str,
    field_name: str,
    failures: list[dict[str, Any]],
) -> list[str]:
    evidence_refs = _normalize_string_list(
        raw_evidence_refs,
        source=source,
        field_name=field_name,
        failures=failures,
        code="invalid_evidence_refs",
        message=f"{source} report must carry non-empty evidence refs",
    )
    if not evidence_refs:
        failures.append(
            _failure(
                source,
                "missing_evidence_refs",
                f"{source} report must carry non-empty evidence refs",
            )
        )
    return evidence_refs


def _finalize_evidence_refs(
    evidence_refs: Sequence[str],
    *,
    source: str,
    failures: Sequence[Mapping[str, Any]],
) -> list[str]:
    if evidence_refs:
        return list(evidence_refs)
    failure_code = next(
        (
            str(item.get("code"))
            for item in failures
            if isinstance(item, Mapping) and _is_non_empty_string(item.get("code"))
        ),
        "missing_evidence_refs",
    )
    return [f"synthetic:{source}:{failure_code}"]


def _normalize_string_list(
    raw_values: Any,
    *,
    source: str,
    field_name: str,
    failures: list[dict[str, Any]],
    code: str,
    message: str,
) -> list[str]:
    if isinstance(raw_values, (str, bytes, Mapping)) or not isinstance(raw_values, Iterable):
        failures.append(_failure(source, code, message, details={"field": field_name}))
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for value in raw_values:
        if not _is_non_empty_string(value):
            failures.append(_failure(source, code, message, details={"field": field_name}))
            return []
        if value in seen:
            failures.append(
                _failure(
                    source,
                    f"duplicate_{field_name}",
                    f"{field_name} cannot contain duplicates",
                )
            )
            return []
        seen.add(value)
        normalized.append(value)
    return normalized


def _require_mapping(
    raw_value: Any,
    source: str,
    code: str,
    failures: list[dict[str, Any]],
) -> Mapping[str, Any]:
    if not isinstance(raw_value, Mapping):
        failures.append(
            _failure(
                source,
                code,
                f"{source} report must be a mapping",
            )
        )
        return {}
    return raw_value


def _normalize_failure_entry(entry: Any, source: str) -> dict[str, Any]:
    if not isinstance(entry, Mapping):
        return _failure(source, "invalid_failure_entry", "failure entry must be a mapping")
    code = entry.get("code")
    message = entry.get("message")
    details = _sanitize_failure_details(entry.get("details"))
    return _failure(
        source,
        code if _is_non_empty_string(code) else "invalid_failure_code",
        message if _is_non_empty_string(message) else "failure entry is missing message",
        details=details,
    )


def _normalize_failure_entries(entries: list[Any], source: str) -> list[dict[str, Any]]:
    return [_normalize_failure_entry(entry, source) for entry in entries]


def _merge_rebuilt_source_report_with_input_failures(
    rebuilt_report: Mapping[str, Any],
    *,
    input_verdict: str,
    input_summary: str,
    input_evidence_refs: Sequence[str],
    normalized_report_failures: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    rebuilt_details = dict(rebuilt_report.get("details") or {})
    rebuilt_failures = list(rebuilt_details.get("failures") or [])
    if normalized_report_failures:
        rebuilt_failures = _dedupe_failures(list(normalized_report_failures) + rebuilt_failures)
    if input_verdict == FAIL_VERDICT and not rebuilt_failures:
        rebuilt_failures = [
            _failure(
                str(rebuilt_report.get("source") or SOURCE_VERSION_GATE),
                "upstream_failed_source_report",
                "source report entered version gate with failed verdict but no explicit failure payload",
            )
        ]
    rebuilt_details["failures"] = rebuilt_failures
    merged_report = dict(rebuilt_report)
    merged_report["details"] = rebuilt_details
    failure_summary = _failed_source_summary(
        str(merged_report.get("source") or SOURCE_VERSION_GATE),
        str(merged_report.get("version") or ""),
    )
    if input_verdict == FAIL_VERDICT:
        merged_report["summary"] = input_summary or failure_summary
    elif rebuilt_failures:
        merged_report["summary"] = failure_summary
    if input_verdict == FAIL_VERDICT or rebuilt_failures:
        merged_report["verdict"] = FAIL_VERDICT
    if input_verdict == FAIL_VERDICT and input_evidence_refs:
        merged_report["evidence_refs"] = list(input_evidence_refs)
    return merged_report


def _source_report(
    *,
    source: str,
    version: str,
    verdict: str,
    summary: str,
    evidence_refs: Sequence[str],
    details: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "source": source,
        "version": version,
        "verdict": verdict,
        "summary": summary,
        "evidence_refs": list(evidence_refs),
        "details": dict(details),
    }


def _synthetic_failed_source_report(
    *,
    source: str,
    version: str,
    gate_reference_pair: Sequence[str] | None,
    summary: str,
    failure: Mapping[str, Any],
) -> dict[str, Any]:
    canonical_version = _canonical_version(version)
    normalized_failure = _normalize_failure_entry(failure, source)
    return _source_report(
        source=source,
        version=canonical_version,
        verdict=FAIL_VERDICT,
        summary=summary,
        evidence_refs=[f"synthetic:{source}:{normalized_failure['code']}"],
        details=_synthetic_source_report_details(
            source,
            version=canonical_version,
            gate_reference_pair=gate_reference_pair,
            failures=[normalized_failure],
        ),
    )


def _failure(
    source: str,
    code: str,
    message: str,
    *,
    details: Any = None,
) -> dict[str, Any]:
    return {
        "source": source,
        "code": code,
        "message": message,
        "details": _sanitize_failure_details(details),
    }


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_string_sequence(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_is_non_empty_string(item) for item in value)


def _enforce_frozen_reference_pair(
    version: str,
    reference_pair: Sequence[str],
    source: str,
    failures: list[dict[str, Any]],
) -> None:
    expected_pair = _FROZEN_REFERENCE_PAIR_BY_VERSION.get(version)
    if expected_pair is None:
        failures.append(
            _failure(
                source,
                "missing_frozen_reference_pair_for_version",
                "reference pair is not frozen for this version and must fail closed",
                details={"version": version},
            )
        )
        return
    if set(reference_pair) != set(expected_pair):
        failures.append(
            _failure(
                source,
                "reference_pair_not_frozen_for_version",
                "reference pair does not match the formal-spec frozen adapters for this version",
                details={"expected_reference_pair": list(expected_pair), "actual_reference_pair": list(reference_pair)},
            )
        )


def _frozen_real_regression_surface(version: str) -> Mapping[str, Any] | None:
    return _FROZEN_REAL_REGRESSION_SURFACE_BY_VERSION.get(version)


def _canonical_version(version: str) -> str:
    return version.strip() if _is_non_empty_string(version) else "unknown"


def _canonical_reference_pair(version: str, reference_pair: Sequence[str]) -> list[str]:
    if reference_pair:
        return list(reference_pair)
    frozen_pair = _FROZEN_REFERENCE_PAIR_BY_VERSION.get(version)
    if frozen_pair:
        return list(frozen_pair)
    return ["unknown"]


def _failed_source_summary(source: str, version: str) -> str:
    normalized_version = version or "unknown"
    return f"{source} failed for version `{normalized_version}`"


def _synthetic_source_report_details(
    source: str,
    *,
    version: str,
    gate_reference_pair: Sequence[str] | None,
    failures: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    details = {"failures": list(failures)}
    if source == SOURCE_HARNESS:
        return {
            "required_sample_ids": [],
            "observed_sample_ids": [],
            "validation_results": [],
            **details,
        }
    if source == SOURCE_REAL_ADAPTER_REGRESSION:
        frozen_surface = _frozen_real_regression_surface(version) or {}
        return {
            "reference_pair": list(gate_reference_pair or []),
            "operation": str(frozen_surface.get("semantic_operation") or ""),
            "target_type": str(frozen_surface.get("target_type") or ""),
            "semantic_operation": str(frozen_surface.get("semantic_operation") or ""),
            "adapter_results": [],
            **details,
        }
    if source == SOURCE_PLATFORM_LEAKAGE:
        return {
            "boundary_scope": [],
            "report_verdict": FAIL_VERDICT,
            "findings": [],
            **details,
        }
    return details


def _failure_from_leakage_finding(source: str, finding: Mapping[str, Any]) -> dict[str, Any]:
    return _failure(
        source,
        str(finding.get("code") or "invalid_leakage_finding_fields"),
        str(finding.get("message") or "platform leakage finding is invalid"),
        details={
            "boundary": str(finding.get("boundary") or ""),
            "evidence_ref": str(finding.get("evidence_ref") or ""),
        },
    )


def _dedupe_failures(failures: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for failure in failures:
        key = json.dumps(failure, sort_keys=True, ensure_ascii=False, default=str)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(dict(failure))
    return deduped


def _sanitize_failure_details(raw_details: Any) -> dict[str, Any]:
    if not isinstance(raw_details, Mapping):
        return {}
    return {str(key): _sanitize_json_like(value) for key, value in raw_details.items()}


def _resolve_gate_required_harness_sample_ids(
    required_harness_sample_ids: Sequence[str] | Iterable[str] | None,
    *,
    version: str,
    failures: list[dict[str, Any]],
) -> list[str]:
    frozen_sample_ids = _FROZEN_HARNESS_REQUIRED_SAMPLE_IDS_BY_VERSION.get(version)
    if required_harness_sample_ids is None:
        if frozen_sample_ids is None:
            failures.append(
                _failure(
                    SOURCE_VERSION_GATE,
                    "missing_required_harness_sample_ids",
                    "version gate requires an explicit harness required sample baseline when the version has no frozen sample set",
                    details={"version": version},
                )
            )
            return []
        return list(frozen_sample_ids)
    normalized_sample_ids = _normalize_report_required_sample_ids(required_harness_sample_ids)
    if normalized_sample_ids is None:
        failures.append(
            _failure(
                SOURCE_VERSION_GATE,
                "invalid_required_harness_sample_ids",
                "version gate required_harness_sample_ids must be a string list without duplicates",
            )
        )
        return []
    if frozen_sample_ids is not None and sorted(normalized_sample_ids) != sorted(frozen_sample_ids):
        failures.append(
            _failure(
                SOURCE_VERSION_GATE,
                "required_harness_sample_ids_not_frozen_for_version",
                "version gate required_harness_sample_ids must match the frozen baseline for this version",
                details={
                    "expected_required_sample_ids": list(frozen_sample_ids),
                    "actual_required_sample_ids": list(normalized_sample_ids),
                },
            )
        )
        return list(frozen_sample_ids)
    return normalized_sample_ids


def _normalize_report_required_sample_ids(raw_required_sample_ids: Any) -> list[str] | None:
    if isinstance(raw_required_sample_ids, (str, bytes, Mapping)) or not isinstance(raw_required_sample_ids, Iterable):
        return None
    required_sample_ids: list[str] = []
    seen: set[str] = set()
    for value in raw_required_sample_ids:
        if not _is_non_empty_string(value) or value in seen:
            return None
        seen.add(value)
        required_sample_ids.append(value)
    return required_sample_ids


def _normalize_harness_observed_sample_ids(
    raw_observed_sample_ids: Any,
    source: str,
    *,
    version: str,
    gate_reference_pair: Sequence[str] | None,
) -> list[str] | None:
    if not isinstance(raw_observed_sample_ids, list):
        return None
    observed_sample_ids: list[str] = []
    seen: set[str] = set()
    for value in raw_observed_sample_ids:
        if not _is_non_empty_string(value) or value in seen:
            return None
        seen.add(value)
        observed_sample_ids.append(value)
    return observed_sample_ids


def _normalize_real_regression_surface(
    raw_operation: Any,
    raw_target_type: Any,
    *,
    version: str,
    source: str,
    failures: list[dict[str, Any]],
    code: str,
    message: str,
) -> dict[str, str] | None:
    frozen_surface = _frozen_real_regression_surface(version)
    if frozen_surface is None:
        return None
    normalized_operation = raw_operation.strip() if _is_non_empty_string(raw_operation) else ""
    if normalized_operation == frozen_surface["semantic_operation"] and raw_target_type is None:
        normalized_target_type = str(frozen_surface["target_type"])
    else:
        normalized_target_type = raw_target_type.strip() if _is_non_empty_string(raw_target_type) else ""
    if (
        normalized_operation not in frozen_surface["accepted_operations"]
        or normalized_target_type != frozen_surface["target_type"]
    ):
        failures.append(
            _failure(
                source,
                code,
                message,
                details={
                    "expected_semantic_operation": frozen_surface["semantic_operation"],
                    "expected_target_type": frozen_surface["target_type"],
                    "actual_operation": raw_operation,
                    "actual_target_type": raw_target_type,
                },
            )
        )
        return None
    return {
        "operation": normalized_operation,
        "target_type": normalized_target_type,
        "semantic_operation": str(frozen_surface["semantic_operation"]),
    }


def _normalize_allowed_string(
    raw_value: Any,
    *,
    source: str,
    field_name: str,
    allowed_values: frozenset[str],
    failures: list[dict[str, Any]],
    code: str,
    message: str,
    details: Mapping[str, Any] | None = None,
    actual_key: str | None = None,
) -> str | None:
    failure_details = dict(details or {})
    failure_details[actual_key or field_name] = raw_value
    if not _is_non_empty_string(raw_value):
        failures.append(_failure(source, code, message, details=failure_details))
        return None
    if raw_value not in allowed_values:
        failures.append(_failure(source, code, message, details=failure_details))
        return None
    return raw_value


def _sanitize_json_like(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _sanitize_json_like(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_json_like(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_json_like(item) for item in value]
    if isinstance(value, set):
        sanitized_items = [_sanitize_json_like(item) for item in value]
        return sorted(sanitized_items, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False, default=str))
    return str(value)


__all__ = [
    "build_harness_source_report",
    "orchestrate_version_gate",
    "validate_platform_leakage_source_report",
    "validate_real_adapter_regression_source_report",
]
