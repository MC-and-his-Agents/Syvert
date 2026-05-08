from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any

from syvert.adapter_capability_requirement import baseline_adapter_capability_requirement
from syvert.adapter_provider_compatibility_decision import (
    COMPATIBILITY_DECISION_STATUS_INVALID_CONTRACT,
    COMPATIBILITY_DECISION_STATUS_MATCHED,
    COMPATIBILITY_DECISION_STATUS_UNMATCHED,
    AdapterProviderCompatibilityDecision,
    baseline_compatibility_decision_context,
    decide_adapter_provider_compatibility,
    project_compatibility_decision_for_core,
)
from syvert.adapters.xhs import XhsAdapter
from syvert.adapters.xhs_provider import XhsProviderContext, XhsProviderResult
from syvert.provider_no_leakage_guard import (
    PROVIDER_NO_LEAKAGE_STATUS_PASSED,
    guard_core_provider_no_leakage,
)
from syvert.registry import AdapterRegistry, baseline_multi_profile_resource_requirement_declaration
from syvert.resource_lifecycle import MANAGED_ACCOUNT_ADAPTER_KEY_FIELD, ResourceRecord, snapshot_to_dict
from syvert.resource_lifecycle_store import LocalResourceLifecycleStore
from syvert.resource_trace import resource_trace_event_to_dict
from syvert.resource_trace_store import LocalResourceTraceStore
from syvert.runtime import PlatformAdapterError, TaskInput, TaskRequest, execute_task_with_record
from syvert.runtime import DEFAULT_FAILURE_RELEASE_REASON, DEFAULT_SUCCESS_RELEASE_REASON
from syvert.task_record import task_record_to_dict
from syvert.task_record_store import LocalTaskRecordStore


EXTERNAL_PROVIDER_SAMPLE_ID = "v0.9.0-external-provider-sample-content-detail"
EXTERNAL_PROVIDER_KEY = "external_fixture_content_detail_provider"
EXTERNAL_PROVIDER_OFFER_EVIDENCE_REF = (
    "fr-0025:offer-manifest-fixture-validator:v0-9-external-provider-sample"
)
EXTERNAL_PROVIDER_ADAPTER_BINDING_EVIDENCE_REF = (
    "fr-0025:offer-manifest-fixture-validator:v0-9-external-provider-adapter-binding"
)
EXTERNAL_PROVIDER_PROVENANCE_ARTIFACT_REF = (
    "syvert/fixtures/v0_9_external_provider_sample_provenance.json"
)
FR0355_EVIDENCE_REF = "fr-0355:external-provider-sample-evidence:v0-9"
FR0351_GATE_REF = "FR-0351:provider_compatibility_sample"
FR0026_DECISION_EVIDENCE_REF = "fr-0026:runtime-tests:adapter-provider-compatibility-decision"
EVIDENCE_ARTIFACT_PATH = (
    "docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md"
)
VALIDATION_EVIDENCE_ARTIFACT_PATH = (
    "docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-validation.json"
)
EVIDENCE_ARTIFACT_JSON_START = "<!-- syvert:evidence-report-json:start -->"
EVIDENCE_ARTIFACT_JSON_END = "<!-- syvert:evidence-report-json:end -->"
VALIDATION_MODULE_PATHS = {
    "tests.runtime.test_real_provider_sample_evidence": "tests/runtime/test_real_provider_sample_evidence.py",
    "tests.runtime.test_adapter_provider_compatibility_decision": (
        "tests/runtime/test_adapter_provider_compatibility_decision.py"
    ),
    "tests.runtime.test_provider_no_leakage_guard": "tests/runtime/test_provider_no_leakage_guard.py",
    "tests.runtime.test_real_adapter_regression": "tests/runtime/test_real_adapter_regression.py",
    "tests.runtime.test_third_party_adapter_contract_entry": "tests/runtime/test_third_party_adapter_contract_entry.py",
    "tests.runtime.test_cli_http_same_path": "tests/runtime/test_cli_http_same_path.py",
}
VALIDATION_SOURCE_BINDING_PATHS = (
    "syvert/real_provider_sample_evidence.py",
    "syvert/fixtures/v0_9_external_provider_sample_manifest.json",
    "syvert/fixtures/v0_9_external_provider_sample_provenance.json",
    "tests/runtime/test_real_provider_sample_evidence.py",
    "tests/runtime/test_adapter_provider_compatibility_decision.py",
    "tests/runtime/test_provider_no_leakage_guard.py",
    "tests/runtime/test_real_adapter_regression.py",
    "tests/runtime/test_third_party_adapter_contract_entry.py",
    "tests/runtime/test_cli_http_same_path.py",
)
REQUIRED_VALIDATION_COMMANDS = (
    (
        "external provider sample evidence",
        ("tests.runtime.test_real_provider_sample_evidence",),
    ),
    (
        "compatibility decision / no-leakage / sample",
        (
            "tests.runtime.test_adapter_provider_compatibility_decision",
            "tests.runtime.test_provider_no_leakage_guard",
            "tests.runtime.test_real_provider_sample_evidence",
        ),
    ),
    (
        "dual reference / third-party entry / API CLI same path",
        (
            "tests.runtime.test_real_adapter_regression",
            "tests.runtime.test_third_party_adapter_contract_entry",
            "tests.runtime.test_cli_http_same_path",
        ),
    ),
)
REQUIRED_CORE_NO_LEAKAGE_SURFACES = (
    "registry_discovery",
    "core_routing",
    "task_record",
    "resource_lifecycle",
    "resource_trace",
    "core_facing_failed_envelope",
)
APPROVED_SLICE = {
    "capability": "content_detail",
    "operation": "content_detail_by_url",
    "target_type": "url",
    "collection_mode": "hybrid",
}
REQUIRED_MANIFEST_FIELDS = (
    "manifest_id",
    "provenance_ref",
    "provenance_artifact_ref",
    "author_path",
)
EXPECTED_MANIFEST_FIXTURE_REFS = (
    "external-fixture://content-detail/success#raw",
    "external-fixture://content-detail/success#normalized",
    "external-fixture://content-detail/provider-timeout#adapter-mapped-failed-envelope",
)
FORBIDDEN_MANIFEST_CLAIM_TOKENS = (
    "selector",
    "fallback",
    "marketplace",
    "provider_product_support",
    "product_support",
    "sla",
)


def build_real_provider_sample_evidence_report(
    *,
    manifest_override: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = dict(manifest_override) if manifest_override is not None else external_provider_sample_manifest()
    matched_decision = decide_adapter_provider_compatibility(external_provider_decision_input())
    unmatched_decision = decide_adapter_provider_compatibility(external_provider_unmatched_decision_input())
    invalid_contract_decision = decide_adapter_provider_compatibility(
        external_provider_invalid_contract_decision_input()
    )
    adapter_bound_execution = build_adapter_bound_execution_evidence(matched_decision)
    no_leakage = build_core_surface_no_leakage_evidence(
        matched_decision,
        adapter_bound_execution=adapter_bound_execution,
    )
    validation_evidence = _expected_validation_evidence_stub()
    report = {
        "report_id": "CHORE-0358-v0-9-external-provider-sample-evidence",
        "release": "v0.9.0",
        "fr_ref": "FR-0355",
        "consumed_gate_ref": FR0351_GATE_REF,
        "approved_slice": dict(manifest.get("approved_slice", {})),
        "sample_origin": manifest.get("sample_origin"),
        "provider_support_claim": manifest.get("provider_support_claim"),
        "status": "pending",
        "decision_matrix_ref": "docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md#decision-matrix",
        "adapter_bound_execution_ref": "docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md#adapter-bound-execution-evidence",
        "no_leakage_ref": "docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md#no-leakage-evidence",
        "dual_reference_ref": "tests.runtime.test_real_adapter_regression",
        "third_party_adapter_entry_ref": "tests.runtime.test_third_party_adapter_contract_entry",
        "api_cli_same_core_path_ref": "tests.runtime.test_cli_http_same_path",
        "external_provider_sample": {
            "sample_id": EXTERNAL_PROVIDER_SAMPLE_ID,
            "manifest_id": manifest.get("manifest_id"),
            "provenance_ref": manifest.get("provenance_ref"),
            "provenance_artifact_ref": manifest.get("provenance_artifact_ref"),
            "manifest_ref": "syvert/fixtures/v0_9_external_provider_sample_manifest.json",
            "controlled_record_ref": manifest.get("provenance_ref"),
            "author_path": manifest.get("author_path"),
            "adapter_key": manifest.get("adapter_key"),
            "provider_identity_scope": manifest.get("provider_identity_scope"),
            "provider_key_redaction": manifest.get("provider_key_redaction"),
            "requirement_ref": "fr-0024:reference-adapter-migration:xhs-douyin-content-detail",
            "offer_ref": EXTERNAL_PROVIDER_OFFER_EVIDENCE_REF,
            "adapter_binding_ref": EXTERNAL_PROVIDER_ADAPTER_BINDING_EVIDENCE_REF,
            "decision_ref": "v0-9-external-provider-sample-matched",
            "decision_contract_ref": FR0026_DECISION_EVIDENCE_REF,
            "profile_proof_refs": (
                "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                "fr-0027:profile:content-detail-by-url-hybrid:account",
            ),
            "not_native_provider_self_evidence": manifest.get("not_native_provider_self_evidence"),
            "provider_support_claim": manifest.get("provider_support_claim"),
            "forbidden_claims": tuple(manifest.get("forbidden_claims", ())),
        },
        "decision_matrix": {
            "matched_case_ref": "fr-0355:decision-matrix:matched",
            "matched_case": _decision_summary(matched_decision),
            "unmatched_case_ref": "fr-0355:decision-matrix:unmatched",
            "unmatched_case": _decision_summary(unmatched_decision),
            "invalid_contract_case_ref": "fr-0355:decision-matrix:invalid-contract",
            "invalid_contract_case": _decision_summary(invalid_contract_decision),
            "validator_commands": tuple(
                _validation_command_text(modules) for _, modules in REQUIRED_VALIDATION_COMMANDS
            ),
        },
        "adapter_bound_execution": adapter_bound_execution,
        "core_surface_no_leakage": no_leakage,
        "validation_evidence": validation_evidence,
        "required_evidence_refs": (
            FR0355_EVIDENCE_REF,
            "fr-0024:reference-adapter-migration:xhs-douyin-content-detail",
            EXTERNAL_PROVIDER_OFFER_EVIDENCE_REF,
            EXTERNAL_PROVIDER_ADAPTER_BINDING_EVIDENCE_REF,
            FR0026_DECISION_EVIDENCE_REF,
            "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
            "fr-0027:profile:content-detail-by-url-hybrid:account",
        ),
        "not_provider_product_support": manifest.get("not_provider_product_support"),
    }
    snapshot_sha256 = _evidence_report_snapshot_sha256(report)
    validation_evidence = build_required_validation_evidence(report_snapshot_sha256=snapshot_sha256)
    fail_closed_reasons = _fail_closed_reasons(
        matched_decision=matched_decision,
        unmatched_decision=unmatched_decision,
        invalid_contract_decision=invalid_contract_decision,
        adapter_bound_execution=adapter_bound_execution,
        no_leakage=no_leakage,
        manifest=manifest,
        validation_evidence=validation_evidence,
    )
    report["status"] = "pass" if not fail_closed_reasons else "fail"
    report["validation_evidence"] = validation_evidence
    report["evidence_snapshot_sha256"] = snapshot_sha256
    if fail_closed_reasons:
        report["decision_matrix"]["fail_closed_reason"] = fail_closed_reasons
    artifact_reasons = _evidence_ref_fail_closed_reasons(report)
    if artifact_reasons:
        fail_closed_reasons = (*fail_closed_reasons, *artifact_reasons)
        report["status"] = "fail"
        report["decision_matrix"]["fail_closed_reason"] = fail_closed_reasons
    return report


def external_provider_sample_manifest() -> dict[str, Any]:
    manifest_path = Path(__file__).parent / "fixtures" / "v0_9_external_provider_sample_manifest.json"
    with manifest_path.open(encoding="utf-8") as manifest_file:
        return json.load(manifest_file)


def external_provider_decision_input() -> dict[str, Any]:
    return {
        "requirement": external_adapter_capability_requirement(),
        "offer": external_provider_capability_offer(),
        "decision_context": baseline_compatibility_decision_context(
            decision_id="v0-9-external-provider-sample-matched"
        ),
    }


def external_provider_unmatched_decision_input() -> dict[str, Any]:
    input_value = external_provider_decision_input()
    requirement = deepcopy(input_value["requirement"])
    offer = deepcopy(input_value["offer"])
    requirement["resource_requirement"]["resource_requirement_profiles"] = [
        requirement["resource_requirement"]["resource_requirement_profiles"][0]
    ]
    requirement["evidence"]["resource_profile_evidence_refs"] = [
        "fr-0027:profile:content-detail-by-url-hybrid:account-proxy"
    ]
    requirement["observability"]["profile_keys"] = ["account_proxy"]
    requirement["observability"]["proof_refs"] = [
        "fr-0027:profile:content-detail-by-url-hybrid:account-proxy"
    ]
    offer["resource_support"]["supported_profiles"] = [offer["resource_support"]["supported_profiles"][1]]
    offer["evidence"]["resource_profile_evidence_refs"] = [
        "fr-0027:profile:content-detail-by-url-hybrid:account"
    ]
    offer["observability"]["profile_keys"] = ["account"]
    offer["observability"]["proof_refs"] = ["fr-0027:profile:content-detail-by-url-hybrid:account"]
    return {
        "requirement": requirement,
        "offer": offer,
        "decision_context": baseline_compatibility_decision_context(
            decision_id="v0-9-external-provider-sample-unmatched"
        ),
    }


def external_provider_invalid_contract_decision_input() -> dict[str, Any]:
    input_value = external_provider_decision_input()
    offer = deepcopy(input_value["offer"])
    offer["selected_provider"] = EXTERNAL_PROVIDER_KEY
    return {
        "requirement": input_value["requirement"],
        "offer": offer,
        "decision_context": baseline_compatibility_decision_context(
            decision_id="v0-9-external-provider-sample-invalid-contract"
        ),
    }


def external_adapter_capability_requirement(*, adapter_key: str = "xhs") -> dict[str, Any]:
    requirement = baseline_adapter_capability_requirement(
        adapter_key=adapter_key,
        resource_requirement=baseline_multi_profile_resource_requirement_declaration(
            adapter_key=adapter_key,
            capability=APPROVED_SLICE["capability"],
        ),
    )
    return {
        "adapter_key": requirement.adapter_key,
        "capability": requirement.capability,
        "execution_requirement": {
            "operation": requirement.execution_requirement.operation,
            "target_type": requirement.execution_requirement.target_type,
            "collection_mode": requirement.execution_requirement.collection_mode,
        },
        "resource_requirement": {
            "adapter_key": requirement.resource_requirement.adapter_key,
            "capability": requirement.resource_requirement.capability,
            "resource_requirement_profiles": [
                {
                    "profile_key": profile.profile_key,
                    "resource_dependency_mode": profile.resource_dependency_mode,
                    "required_capabilities": list(profile.required_capabilities),
                    "evidence_refs": list(profile.evidence_refs),
                }
                for profile in requirement.resource_requirement.resource_requirement_profiles
            ],
        },
        "evidence": {
            "resource_profile_evidence_refs": list(requirement.evidence.resource_profile_evidence_refs),
            "capability_requirement_evidence_refs": list(
                requirement.evidence.capability_requirement_evidence_refs
            ),
        },
        "lifecycle": {
            "requires_core_resource_bundle": requirement.lifecycle.requires_core_resource_bundle,
            "resource_profiles_drive_admission": requirement.lifecycle.resource_profiles_drive_admission,
            "uses_existing_disposition_hint": requirement.lifecycle.uses_existing_disposition_hint,
        },
        "observability": {
            "requirement_id": requirement.observability.requirement_id,
            "profile_keys": list(requirement.observability.profile_keys),
            "proof_refs": list(requirement.observability.proof_refs),
            "admission_outcome_fields": list(requirement.observability.admission_outcome_fields),
        },
        "fail_closed": requirement.fail_closed,
    }


def external_provider_capability_offer(
    *,
    adapter_key: str = "xhs",
    provider_key: str = EXTERNAL_PROVIDER_KEY,
) -> dict[str, Any]:
    resource_profile_evidence_refs = [
        "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
        "fr-0027:profile:content-detail-by-url-hybrid:account",
    ]
    return {
        "provider_key": provider_key,
        "adapter_binding": {
            "adapter_key": adapter_key,
            "binding_scope": "adapter_bound",
            "provider_port_ref": f"{adapter_key}:adapter-owned-provider-port",
        },
        "capability_offer": dict(APPROVED_SLICE),
        "resource_support": {
            "supported_profiles": [
                {
                    "profile_key": "account_proxy",
                    "resource_dependency_mode": "required",
                    "required_capabilities": ["account", "proxy"],
                    "evidence_refs": ["fr-0027:profile:content-detail-by-url-hybrid:account-proxy"],
                },
                {
                    "profile_key": "account",
                    "resource_dependency_mode": "required",
                    "required_capabilities": ["account"],
                    "evidence_refs": ["fr-0027:profile:content-detail-by-url-hybrid:account"],
                },
            ],
            "resource_profile_contract_ref": "FR-0027",
        },
        "error_carrier": {
            "invalid_offer_code": "invalid_provider_offer",
            "provider_unavailable_code": "provider_unavailable",
            "contract_violation_code": "provider_contract_violation",
            "adapter_mapping_required": True,
        },
        "version": {
            "contract_version": "v0.8.0",
            "requirement_contract_ref": "FR-0024",
            "resource_profile_contract_ref": "FR-0027",
            "provider_port_boundary_ref": "FR-0021",
        },
        "evidence": {
            "provider_offer_evidence_refs": [EXTERNAL_PROVIDER_OFFER_EVIDENCE_REF],
            "resource_profile_evidence_refs": resource_profile_evidence_refs,
            "adapter_binding_evidence_refs": [EXTERNAL_PROVIDER_ADAPTER_BINDING_EVIDENCE_REF],
        },
        "lifecycle": {
            "invoked_by_adapter_only": True,
            "core_discovery_allowed": False,
            "consumes_adapter_execution_context": True,
            "uses_existing_resource_bundle_view": True,
            "adapter_error_mapping_required": True,
        },
        "observability": {
            "offer_id": (
                f"{adapter_key}:{provider_key}:content_detail:"
                "content_detail_by_url:url:hybrid:v0.8.0"
            ),
            "provider_key": provider_key,
            "adapter_key": adapter_key,
            "capability": "content_detail",
            "operation": "content_detail_by_url",
            "profile_keys": ["account_proxy", "account"],
            "proof_refs": resource_profile_evidence_refs,
            "contract_version": "v0.8.0",
            "validation_outcome_fields": [
                "validation_status",
                "error_code",
                "failure_category",
            ],
        },
        "fail_closed": True,
    }


def build_adapter_bound_execution_evidence(
    decision: AdapterProviderCompatibilityDecision,
    *,
    execution_override: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if decision.decision_status != COMPATIBILITY_DECISION_STATUS_MATCHED:
        return {
            "status": "fail",
            "reason": "adapter_bound_execution_requires_matched_decision",
            "matched_decision_ref": decision.decision_id,
        }
    execution = (
        deepcopy(dict(execution_override))
        if execution_override is not None
        else run_external_provider_sample_runtime_execution()
    )
    success = execution.get("success") if isinstance(execution.get("success"), Mapping) else {}
    failure = execution.get("failure") if isinstance(execution.get("failure"), Mapping) else {}
    success_envelope = success.get("envelope") if isinstance(success.get("envelope"), Mapping) else {}
    failed_envelope = failure.get("envelope") if isinstance(failure.get("envelope"), Mapping) else {}
    checks = _adapter_bound_execution_checks(execution, decision)
    fail_closed_reasons = (
        *_adapter_bound_execution_shape_reasons(execution),
        *_adapter_bound_execution_check_reasons(checks),
    )
    evidence_status = (
        "pass"
        if (
            success_envelope.get("status") == "success"
            and failed_envelope.get("status") == "failed"
            and success.get("provider_calls")
            and failure.get("provider_calls")
            and all(checks.values())
            and not fail_closed_reasons
        )
        else "fail"
    )
    evidence = {
        "status": evidence_status,
        "matched_decision_ref": "fr-0355:decision-matrix:matched",
        "matched_decision_id": decision.decision_id,
        "adapter_owned_provider_seam_ref": "xhs:adapter-owned-provider-port:external-fixture",
        "raw_payload_ref": "external-fixture://content-detail/success#raw",
        "raw_payload": deepcopy(success_envelope.get("raw")),
        "raw_payload_present": checks["raw_payload_present"],
        "normalized_result_ref": "external-fixture://content-detail/success#normalized",
        "normalized_result": deepcopy(success_envelope.get("normalized")),
        "normalized_result_present": checks["normalized_result_present"],
        "adapter_mapped_failed_envelope_ref": (
            "external-fixture://content-detail/provider-timeout#adapter-mapped-failed-envelope"
        ),
        "adapter_mapped_failed_envelope": deepcopy(failed_envelope),
        "provider_error_mapping": deepcopy(failure.get("provider_error_mapping", {})),
        "provider_error_mapping_checked": checks["provider_error_mapping_checked"],
        "resource_profile_consumption_checked": checks["resource_profile_consumption_checked"],
        "resource_lifecycle_disposition_checked": checks["resource_lifecycle_disposition_checked"],
        "resource_lifecycle_disposition_hint": None,
        "resource_lifecycle_release_reason": checks["success_release_reason"],
        "resource_lifecycle_failure_release_reason": checks["failure_release_reason"],
        "observability_carrier_checked": checks["observability_carrier_checked"],
        "runtime_execution_ref": execution.get("runtime_execution_ref"),
        "success_task_record_ref": success.get("task_record_ref"),
        "failure_task_record_ref": failure.get("task_record_ref"),
        "observability": _adapter_bound_observability_carrier(decision),
        "core_surface_projection_ref": (
            "docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md"
            "#core-surface-projection"
        ),
        "core_surface_projection": _core_surface_status_projection(decision),
        "core_runtime_surfaces": deepcopy(execution.get("core_runtime_surfaces", {})),
    }
    if fail_closed_reasons:
        evidence["fail_closed_reason"] = fail_closed_reasons
    return evidence


def build_core_surface_no_leakage_evidence(
    decision: AdapterProviderCompatibilityDecision,
    *,
    surface_overrides: Mapping[str, Any] | None = None,
    adapter_bound_execution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if adapter_bound_execution is None:
        adapter_bound_execution = build_adapter_bound_execution_evidence(decision)
    execution = (
        adapter_bound_execution.get("core_runtime_surfaces")
        if isinstance(adapter_bound_execution, Mapping)
        else None
    )
    if isinstance(execution, Mapping):
        surfaces = deepcopy(dict(execution))
        surfaces["core_projection"] = _core_surface_status_projection(decision)
    else:
        surfaces = {"core_projection": _core_surface_status_projection(decision)}
    if surface_overrides:
        surfaces.update(surface_overrides)
    missing_surfaces = tuple(surface for surface in REQUIRED_CORE_NO_LEAKAGE_SURFACES if surface not in surfaces)
    surface_results = {
        name: guard_core_provider_no_leakage(surface_name=name, surface=surface, decision=decision)
        for name, surface in surfaces.items()
    }
    provider_identity_in_core_surface = any(
        result.evidence.forbidden_field_paths or result.evidence.forbidden_value_paths
        for result in surface_results.values()
    )
    return {
        "status": "pass"
        if not missing_surfaces
        and all(result.status == PROVIDER_NO_LEAKAGE_STATUS_PASSED for result in surface_results.values())
        else "fail",
        "provider_identity_in_core_surface": provider_identity_in_core_surface,
        "registry_discovery_checked": "registry_discovery" in surfaces,
        "core_routing_checked": "core_routing" in surfaces,
        "task_record_checked": "task_record" in surfaces,
        "resource_lifecycle_checked": "resource_lifecycle" in surfaces,
        "failed_envelope_checked": "core_facing_failed_envelope" in surfaces,
        "missing_required_surfaces": missing_surfaces,
        "all_forbidden_paths_empty": all(
            not result.evidence.forbidden_field_paths and not result.evidence.forbidden_value_paths
            for result in surface_results.values()
        ),
        "surfaces": {
            name: {
                "status": result.status,
                "forbidden_field_paths": result.evidence.forbidden_field_paths,
                "forbidden_value_paths": result.evidence.forbidden_value_paths,
            }
            for name, result in surface_results.items()
        },
    }


def _adapter_bound_execution_checks(
    execution: Mapping[str, Any],
    decision: AdapterProviderCompatibilityDecision,
) -> dict[str, bool]:
    success = execution.get("success") if isinstance(execution.get("success"), Mapping) else {}
    failure = execution.get("failure") if isinstance(execution.get("failure"), Mapping) else {}
    success_envelope = success.get("envelope") if isinstance(success.get("envelope"), Mapping) else {}
    failed_envelope = failure.get("envelope") if isinstance(failure.get("envelope"), Mapping) else {}
    provider_error_mapping = (
        failure.get("provider_error_mapping") if isinstance(failure.get("provider_error_mapping"), Mapping) else {}
    )
    failed_error = failed_envelope.get("error") if isinstance(failed_envelope.get("error"), Mapping) else {}
    failed_details = failed_error.get("details") if isinstance(failed_error.get("details"), Mapping) else {}
    success_trace_events = tuple(
        event for event in success.get("resource_trace_events", ()) if isinstance(event, Mapping)
    )
    failure_trace_events = tuple(
        event for event in failure.get("resource_trace_events", ()) if isinstance(event, Mapping)
    )
    success_task_record = success.get("task_record") if isinstance(success.get("task_record"), Mapping) else {}
    failure_task_record = failure.get("task_record") if isinstance(failure.get("task_record"), Mapping) else {}
    success_result = success_task_record.get("result") if isinstance(success_task_record.get("result"), Mapping) else {}
    failure_result = failure_task_record.get("result") if isinstance(failure_task_record.get("result"), Mapping) else {}
    success_terminal_envelope = (
        success_result.get("envelope") if isinstance(success_result.get("envelope"), Mapping) else {}
    )
    failure_terminal_envelope = (
        failure_result.get("envelope") if isinstance(failure_result.get("envelope"), Mapping) else {}
    )
    success_release_reason = _single_release_reason(success_trace_events)
    failure_release_reason = _single_release_reason(failure_trace_events)
    observability_carrier = _adapter_bound_observability_carrier(decision)
    return {
        "raw_payload_present": isinstance(success_envelope.get("raw"), Mapping),
        "normalized_result_present": isinstance(success_envelope.get("normalized"), Mapping),
        "provider_error_mapping_checked": (
            provider_error_mapping.get("provider_side_error_code") == "provider_unavailable"
            and provider_error_mapping.get("adapter_mapped_error_code") == "external_sample_unavailable"
            and provider_error_mapping.get("source_error") == "external_sample_timeout"
            and
            failed_envelope.get("status") == "failed"
            and failed_envelope.get("capability") == "content_detail_by_url"
            and failed_error.get("category") == "platform"
            and failed_error.get("code") == "external_sample_unavailable"
            and failed_details.get("source_error") == "external_sample_timeout"
        ),
        "resource_profile_consumption_checked": _trace_events_cover_account_proxy_profile(success_trace_events),
        "resource_lifecycle_disposition_checked": (
            _trace_events_released_to_available(success_trace_events)
            and _trace_events_released_to_available(failure_trace_events)
            and success_release_reason == DEFAULT_SUCCESS_RELEASE_REASON
            and failure_release_reason == DEFAULT_FAILURE_RELEASE_REASON
        ),
        "success_release_reason": success_release_reason,
        "failure_release_reason": failure_release_reason,
        "observability_carrier_checked": (
            success_task_record.get("status") == "succeeded"
            and failure_task_record.get("status") == "failed"
            and success_terminal_envelope.get("adapter_key") == decision.adapter_key
            and failure_terminal_envelope.get("adapter_key") == decision.adapter_key
            and success_terminal_envelope.get("capability") == "content_detail_by_url"
            and failure_terminal_envelope.get("capability") == "content_detail_by_url"
            and observability_carrier["adapter_key"] == decision.adapter_key
            and observability_carrier["capability"] == decision.capability
            and observability_carrier["operation"] == "content_detail_by_url"
            and observability_carrier["decision_status"] == COMPATIBILITY_DECISION_STATUS_MATCHED
            and bool(observability_carrier["proof_refs"])
        ),
    }


def _adapter_bound_execution_shape_reasons(execution: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    if not execution.get("runtime_execution_ref"):
        reasons.append("runtime_execution_ref_missing")
    success = execution.get("success")
    failure = execution.get("failure")
    if not isinstance(success, Mapping):
        reasons.append("success_execution_missing")
    elif not isinstance(success.get("envelope"), Mapping):
        reasons.append("success_envelope_missing")
    if not isinstance(failure, Mapping):
        reasons.append("failure_execution_missing")
    elif not isinstance(failure.get("envelope"), Mapping):
        reasons.append("failure_envelope_missing")
    return tuple(reasons)


def _adapter_bound_execution_check_reasons(checks: Mapping[str, Any]) -> tuple[str, ...]:
    boolean_checks = {
        "raw_payload_present",
        "normalized_result_present",
        "provider_error_mapping_checked",
        "resource_profile_consumption_checked",
        "resource_lifecycle_disposition_checked",
        "observability_carrier_checked",
    }
    return tuple(f"{check_name}_failed" for check_name in sorted(boolean_checks) if checks.get(check_name) is not True)


def _adapter_bound_observability_carrier(
    decision: AdapterProviderCompatibilityDecision,
) -> dict[str, Any]:
    return {
        "adapter_key": decision.adapter_key,
        "capability": decision.capability,
        "operation": decision.execution_slice.operation if decision.execution_slice else None,
        "decision_status": decision.decision_status,
        "proof_refs": decision.evidence.resource_profile_evidence_refs,
    }


def _trace_events_cover_account_proxy_profile(events: tuple[Mapping[str, Any], ...]) -> bool:
    acquired_resource_types = {
        event.get("resource_type")
        for event in events
        if event.get("event_type") == "acquired" and event.get("to_status") == "IN_USE"
    }
    return {"account", "proxy"}.issubset(acquired_resource_types)


def _trace_events_released_to_available(events: tuple[Mapping[str, Any], ...]) -> bool:
    released_resource_types = {
        event.get("resource_type")
        for event in events
        if event.get("event_type") == "released" and event.get("to_status") == "AVAILABLE"
    }
    return {"account", "proxy"}.issubset(released_resource_types)


def _single_release_reason(events: tuple[Mapping[str, Any], ...]) -> str | None:
    reasons = {
        str(event.get("reason"))
        for event in events
        if event.get("event_type") == "released" and event.get("reason")
    }
    if len(reasons) != 1:
        return None
    return next(iter(reasons))


class ExternalProviderSampleError(Exception):
    def __init__(self, *, code: str, message: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})


class ExternalProviderSampleXhsAdapter(XhsAdapter):
    def __init__(self, *, provider: Any) -> None:
        super().__init__(provider=provider)
        self.provider_error_mappings: list[dict[str, Any]] = []

    def execute(self, request: Any) -> dict[str, Any]:
        try:
            return super().execute(request)
        except ExternalProviderSampleError as error:
            mapped = {
                "provider_side_error_code": error.code,
                "adapter_mapped_error_code": "external_sample_unavailable",
                "source_error": error.details.get("source_error"),
            }
            self.provider_error_mappings.append(mapped)
            raise PlatformAdapterError(
                code="external_sample_unavailable",
                message="adapter mapped external sample failure",
                details={
                    "source_error": "external_sample_timeout",
                    "retryable": False,
                },
            ) from error


class ExternalFixtureXhsProvider:
    def __init__(self, *, mode: str) -> None:
        self.mode = mode
        self.calls: list[dict[str, Any]] = []

    def fetch_content_detail(self, context: XhsProviderContext, input_url: str) -> XhsProviderResult:
        self.calls.append(
            {
                "note_id": context.parsed_target.note_id,
                "xsec_token": context.parsed_target.xsec_token,
                "timeout_seconds": context.session.timeout_seconds,
                "input_url": input_url,
            }
        )
        if self.mode == "failure":
            raise ExternalProviderSampleError(
                code="provider_unavailable",
                message="external provider sample timed out",
                details={"source_error": "external_sample_timeout", "retryable": False},
            )
        return XhsProviderResult(
            raw_payload={
                "sample_id": EXTERNAL_PROVIDER_SAMPLE_ID,
                "source_payload_ref": "external-fixture://content-detail/success",
                "resource_profile": "account_proxy",
            },
            platform_detail={
                "note_id": context.parsed_target.note_id,
                "type": "normal",
                "title": "external provider sample",
                "desc": "external provider sample body",
                "time": 1712304300,
                "user": {"user_id": "external-sample-author", "nickname": "External Sample"},
                "interact_info": {
                    "liked_count": "11",
                    "comment_count": "12",
                    "share_count": "13",
                    "collected_count": "14",
                },
                "image_list": [{"url_default": "https://cdn.example/external-sample-image.jpg"}],
            },
        )


def run_external_provider_sample_runtime_execution() -> dict[str, Any]:
    return deepcopy(_cached_external_provider_sample_runtime_execution())


@lru_cache(maxsize=1)
def _cached_external_provider_sample_runtime_execution() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="syvert-v0-9-provider-sample-") as temp_dir:
        temp_path = Path(temp_dir)
        task_store = LocalTaskRecordStore(temp_path / "task-records")
        resource_store = LocalResourceLifecycleStore(temp_path / "resource-lifecycle.json")
        trace_store = LocalResourceTraceStore(temp_path / "resource-trace-events.jsonl")
        _seed_external_provider_sample_resources(resource_store)
        success_provider = ExternalFixtureXhsProvider(mode="success")
        failure_provider = ExternalFixtureXhsProvider(mode="failure")
        success_adapter = ExternalProviderSampleXhsAdapter(provider=success_provider)
        failure_adapter = ExternalProviderSampleXhsAdapter(provider=failure_provider)
        success = _execute_external_provider_sample(
            adapter=success_adapter,
            task_id="task-v0-9-sample-success",
            task_store=task_store,
            resource_store=resource_store,
            trace_store=trace_store,
        )
        failure = _execute_external_provider_sample(
            adapter=failure_adapter,
            task_id="task-v0-9-sample-failure",
            task_store=task_store,
            resource_store=resource_store,
            trace_store=trace_store,
        )
        registry = AdapterRegistry.from_mapping({"xhs": success_adapter})
        return {
            "runtime_execution_ref": "syvert.runtime.execute_task_with_record:v0-9-external-provider-sample",
            "success": {
                **success,
                "provider_calls": tuple(success_provider.calls),
            },
            "failure": {
                **failure,
                "provider_calls": tuple(failure_provider.calls),
                "provider_error_mapping": deepcopy(failure_adapter.provider_error_mappings[-1])
                if failure_adapter.provider_error_mappings
                else {},
            },
            "core_runtime_surfaces": {
                "registry_discovery": {
                    "adapter_key": "xhs",
                    "capabilities": tuple(sorted(registry.discover_capabilities("xhs") or ())),
                    "targets": tuple(sorted(registry.discover_targets("xhs") or ())),
                    "collection_modes": tuple(sorted(registry.discover_collection_modes("xhs") or ())),
                    "resource_requirements": _resource_requirements_summary(
                        registry.discover_resource_requirements("xhs") or ()
                    ),
                },
                "core_routing": {
                    "adapter_key": "xhs",
                    "capability": "content_detail_by_url",
                    "target_type": "url",
                    "collection_mode": "hybrid",
                    "dispatch_status": "adapter_selected",
                    "runtime_execution_ref": "syvert.runtime.execute_task_with_record",
                },
                "task_record": {
                    "success": success["task_record"],
                    "failure": failure["task_record"],
                },
                "resource_lifecycle": snapshot_to_dict(resource_store.load_snapshot()),
                "resource_trace": tuple(
                    resource_trace_event_to_dict(event) for event in trace_store.load_events()
                ),
                "core_facing_failed_envelope": failure["envelope"],
            },
        }


def _execute_external_provider_sample(
    *,
    adapter: XhsAdapter,
    task_id: str,
    task_store: LocalTaskRecordStore,
    resource_store: LocalResourceLifecycleStore,
    trace_store: LocalResourceTraceStore,
) -> dict[str, Any]:
    result = execute_task_with_record(
        TaskRequest(
            adapter_key="xhs",
            capability="content_detail_by_url",
            input=TaskInput(
                url="https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8?xsec_token=token-1"
            ),
        ),
        adapters={"xhs": adapter},
        task_id_factory=lambda: task_id,
        task_record_store=task_store,
        resource_lifecycle_store=resource_store,
        resource_trace_store=trace_store,
    )
    task_record = task_record_to_dict(result.task_record) if result.task_record is not None else None
    return {
        "envelope": result.envelope,
        "task_record": task_record,
        "task_record_ref": f"task_record:{task_id}" if task_record is not None else "none",
        "resource_trace_events": tuple(
            resource_trace_event_to_dict(event) for event in trace_store.task_usage_log(task_id).events
        ),
    }


def _seed_external_provider_sample_resources(store: LocalResourceLifecycleStore) -> None:
    account_material = {
        "cookies": "a=1; b=2",
        "user_agent": "Mozilla/5.0 TestAgent",
        "sign_base_url": "http://127.0.0.1:8000",
        "timeout_seconds": 5,
        MANAGED_ACCOUNT_ADAPTER_KEY_FIELD: "xhs",
    }
    store.seed_resources(
        (
            ResourceRecord(
                resource_id="sample-account-001",
                resource_type="account",
                status="AVAILABLE",
                material=account_material,
            ),
            ResourceRecord(
                resource_id="sample-proxy-001",
                resource_type="proxy",
                status="AVAILABLE",
                material={"proxy_endpoint": "http://proxy-001"},
            ),
        )
    )


def _resource_requirements_summary(declarations: tuple[Any, ...]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "adapter_key": declaration.adapter_key,
            "capability": declaration.capability,
            "profiles": tuple(
                {
                    "profile_key": profile.profile_key,
                    "resource_dependency_mode": profile.resource_dependency_mode,
                    "required_capabilities": profile.required_capabilities,
                    "evidence_refs": profile.evidence_refs,
                }
                for profile in declaration.resource_requirement_profiles
            ),
        }
        for declaration in declarations
    )


def build_required_validation_evidence(
    *,
    report_snapshot_sha256: str | None = None,
) -> dict[str, Any]:
    repo_root = Path(__file__).parents[1]
    artifact_path = repo_root / VALIDATION_EVIDENCE_ARTIFACT_PATH
    if not artifact_path.exists():
        return {"status": "fail", "commands": (), "reason": "validation_evidence_artifact_missing"}
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {
            "status": "fail",
            "commands": (),
            "reason": "validation_evidence_artifact_unreadable",
            "error_type": error.__class__.__name__,
        }
    if not isinstance(payload, Mapping):
        return {"status": "fail", "commands": (), "reason": "validation_evidence_artifact_not_object"}
    commands = payload.get("commands")
    normalized_commands = (
        tuple(command for command in commands if isinstance(command, Mapping))
        if isinstance(commands, list)
        else ()
    )
    status = (
        "pass"
        if _validation_artifact_is_pass(
            payload,
            normalized_commands,
            report_snapshot_sha256=report_snapshot_sha256,
        )
        else "fail"
    )
    return {
        "status": status,
        "artifact_ref": VALIDATION_EVIDENCE_ARTIFACT_PATH,
        "run_id": payload.get("run_id"),
        "validated_source_sha256": payload.get("validated_source_sha256"),
        "report_snapshot_sha256": payload.get("report_snapshot_sha256"),
        "commands": normalized_commands,
    }


def _validation_artifact_is_pass(
    payload: Mapping[str, Any],
    commands: tuple[Mapping[str, Any], ...],
    *,
    report_snapshot_sha256: str | None = None,
) -> bool:
    expected_commands = tuple(_validation_command_text(modules) for _, modules in REQUIRED_VALIDATION_COMMANDS)
    artifact_snapshot_sha256 = payload.get("report_snapshot_sha256")
    expected_source_sha256 = _validation_source_binding_sha256()
    snapshot_binding_checked = (
        artifact_snapshot_sha256 == report_snapshot_sha256
        if report_snapshot_sha256 is not None
        else isinstance(artifact_snapshot_sha256, str) and len(artifact_snapshot_sha256) == 64
    )
    execution_binding_checked = (
        isinstance(payload.get("run_id"), str)
        and bool(str(payload.get("run_id")).strip())
        and isinstance(payload.get("executed_at"), str)
        and bool(str(payload.get("executed_at")).strip())
        and payload.get("validated_source_sha256") == expected_source_sha256
        and tuple(payload.get("source_binding_paths", ())) == VALIDATION_SOURCE_BINDING_PATHS
        and all(
            command.get("returncode") == 0
            and isinstance(command.get("output_sha256"), str)
            and len(command.get("output_sha256")) == 64
            for command in commands
        )
    )
    return (
        payload.get("report_id") == "CHORE-0358-v0-9-external-provider-sample-evidence"
        and payload.get("release") == "v0.9.0"
        and payload.get("fr_ref") == "FR-0355"
        and payload.get("consumed_gate_ref") == FR0351_GATE_REF
        and snapshot_binding_checked
        and execution_binding_checked
        and payload.get("status") == "pass"
        and tuple(command.get("command") for command in commands) == expected_commands
        and all(command.get("status") == "pass" for command in commands)
    )


def _expected_validation_evidence_stub() -> dict[str, Any]:
    return {
        "artifact_ref": VALIDATION_EVIDENCE_ARTIFACT_PATH,
        "commands": tuple(
            {
                "validation": validation_name,
                "command": _validation_command_text(modules),
            }
            for validation_name, modules in REQUIRED_VALIDATION_COMMANDS
        ),
    }


def _validation_source_binding_sha256() -> str:
    repo_root = Path(__file__).parents[1]
    digest = hashlib.sha256()
    for relative_path in VALIDATION_SOURCE_BINDING_PATHS:
        path = repo_root / relative_path
        if not path.exists():
            return "missing-validation-source-binding-path"
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _validation_command_text(modules: tuple[str, ...]) -> str:
    return "python3 -m unittest " + " ".join(modules)


def _decision_summary(decision: AdapterProviderCompatibilityDecision) -> dict[str, Any]:
    return {
        "decision_id": decision.decision_id,
        "adapter_key": decision.adapter_key,
        "capability": decision.capability,
        "execution_slice": decision.execution_slice.__dict__ if decision.execution_slice else None,
        "decision_status": decision.decision_status,
        "error_code": decision.error.error_code if decision.error else None,
        "matched_profile_keys": tuple(profile.requirement_profile_key for profile in decision.matched_profiles),
        "resource_profile_evidence_refs": decision.evidence.resource_profile_evidence_refs,
        "compatibility_decision_evidence_refs": decision.evidence.compatibility_decision_evidence_refs,
        "adapter_bound_provider_evidence_present": decision.evidence.adapter_bound_provider_evidence is not None,
        "core_projection": _core_surface_status_projection(decision),
    }


def _core_surface_status_projection(decision: AdapterProviderCompatibilityDecision) -> dict[str, Any]:
    core_projection = project_compatibility_decision_for_core(decision)
    return {
        "decision_status": core_projection["decision_status"],
        "error_code": core_projection["error_code"],
        "failure_category": core_projection["failure_category"],
        "fail_closed": core_projection["fail_closed"],
    }


def _fail_closed_reasons(
    *,
    matched_decision: AdapterProviderCompatibilityDecision,
    unmatched_decision: AdapterProviderCompatibilityDecision,
    invalid_contract_decision: AdapterProviderCompatibilityDecision,
    adapter_bound_execution: Mapping[str, Any],
    no_leakage: Mapping[str, Any],
    manifest: Mapping[str, Any],
    validation_evidence: Mapping[str, Any],
) -> tuple[str, ...]:
    reasons: list[str] = []
    reasons.extend(_manifest_fail_closed_reasons(manifest))
    reasons.extend(_validation_fail_closed_reasons(validation_evidence))
    if matched_decision.decision_status != COMPATIBILITY_DECISION_STATUS_MATCHED:
        reasons.append("matched_case_not_matched")
    if unmatched_decision.decision_status != COMPATIBILITY_DECISION_STATUS_UNMATCHED:
        reasons.append("unmatched_case_not_unmatched")
    if invalid_contract_decision.decision_status != COMPATIBILITY_DECISION_STATUS_INVALID_CONTRACT:
        reasons.append("invalid_contract_case_not_invalid_contract")
    if adapter_bound_execution.get("status") != "pass":
        reasons.append("adapter_bound_execution_not_pass")
    if no_leakage.get("status") != "pass":
        reasons.append("core_surface_no_leakage_not_pass")
    return tuple(reasons)


def _validation_fail_closed_reasons(validation_evidence: Mapping[str, Any]) -> tuple[str, ...]:
    if validation_evidence.get("status") != "pass":
        return ("required_validation_not_pass",)
    commands = validation_evidence.get("commands")
    if not isinstance(commands, tuple) or len(commands) != len(REQUIRED_VALIDATION_COMMANDS):
        return ("required_validation_commands_missing",)
    reasons: list[str] = []
    for command in commands:
        if not isinstance(command, Mapping) or command.get("status") != "pass":
            reasons.append("required_validation_command_not_pass")
    return tuple(reasons)


def _manifest_fail_closed_reasons(manifest: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    for field_name in REQUIRED_MANIFEST_FIELDS:
        if not manifest.get(field_name):
            reasons.append(f"manifest_required_field_missing:{field_name}")
    if manifest.get("sample_origin") != "external_provider_sample":
        reasons.append("manifest_sample_origin_not_external_provider_sample")
    if manifest.get("provider_support_claim") is not False:
        reasons.append("manifest_provider_support_claim_not_false")
    if manifest.get("not_native_provider_self_evidence") is not True:
        reasons.append("manifest_not_native_provider_self_evidence_not_true")
    if manifest.get("not_provider_product_support") is not True:
        reasons.append("manifest_not_provider_product_support_not_true")
    if manifest.get("provider_identity_scope") != "adapter_bound":
        reasons.append("manifest_provider_identity_scope_not_adapter_bound")
    if manifest.get("approved_slice") != APPROVED_SLICE:
        reasons.append("manifest_approved_slice_drift")
    if manifest.get("provider_key") != EXTERNAL_PROVIDER_KEY:
        reasons.append("manifest_provider_key_drift")
    if manifest.get("adapter_key") != "xhs":
        reasons.append("manifest_adapter_key_not_single_xhs_binding")
    if manifest.get("provider_key_redaction") != "stable fixture provider key; not a product support claim":
        reasons.append("manifest_provider_key_redaction_drift")
    if manifest.get("provenance_ref") != "controlled-record:v0.9.0:external-provider-sample-content-detail":
        reasons.append("manifest_provenance_ref_not_canonical_controlled_record")
    if manifest.get("provenance_artifact_ref") != EXTERNAL_PROVIDER_PROVENANCE_ARTIFACT_REF:
        reasons.append("manifest_provenance_artifact_ref_not_canonical_fixture")
    reasons.extend(_provenance_artifact_fail_closed_reasons(manifest))
    if manifest.get("author_path") != "external-provider-author-fixture":
        reasons.append("manifest_author_path_not_external_fixture")
    if tuple(manifest.get("fixture_refs", ())) != EXPECTED_MANIFEST_FIXTURE_REFS:
        reasons.append("manifest_fixture_refs_drift")
    forbidden_claims = manifest.get("forbidden_claims")
    if not isinstance(forbidden_claims, list):
        reasons.append("manifest_forbidden_claims_not_list")
    else:
        for claim in forbidden_claims:
            normalized_claim = str(claim).lower().replace("-", "_")
            if any(token in normalized_claim for token in FORBIDDEN_MANIFEST_CLAIM_TOKENS):
                reasons.append(f"manifest_forbidden_claim_present:{normalized_claim}")
    return tuple(reasons)


def _provenance_artifact_fail_closed_reasons(manifest: Mapping[str, Any]) -> tuple[str, ...]:
    provenance_artifact_ref = manifest.get("provenance_artifact_ref")
    if provenance_artifact_ref != EXTERNAL_PROVIDER_PROVENANCE_ARTIFACT_REF:
        return ("provenance_artifact_ref_drift",)
    provenance_path = Path(__file__).parents[1] / EXTERNAL_PROVIDER_PROVENANCE_ARTIFACT_REF
    if not provenance_path.exists():
        return ("provenance_artifact_missing",)
    try:
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ("provenance_artifact_unreadable",)
    if not isinstance(provenance, Mapping):
        return ("provenance_artifact_not_object",)
    expected = {
        "record_id": manifest.get("provenance_ref"),
        "manifest_ref": "syvert/fixtures/v0_9_external_provider_sample_manifest.json",
        "sample_origin": "external_provider_sample",
        "author_path": manifest.get("author_path"),
        "author_path_kind": "repo_fixture",
        "adapter_key": "xhs",
        "provider_identity_scope": "adapter_bound",
        "provider_key_redaction": "stable fixture provider key; not a product support claim",
        "provider_support_claim": False,
        "not_native_provider_self_evidence": True,
        "not_provider_product_support": True,
        "fixture_refs": list(EXPECTED_MANIFEST_FIXTURE_REFS),
    }
    reasons: list[str] = []
    for field_name, expected_value in expected.items():
        if provenance.get(field_name) != expected_value:
            reasons.append(f"provenance_artifact_field_drift:{field_name}")
    boundary = provenance.get("boundary")
    if not isinstance(boundary, Mapping):
        reasons.append("provenance_artifact_boundary_missing")
    else:
        expected_boundary = {
            "live_network_required": False,
            "private_token_required": False,
            "native_provider_self_evidence": False,
            "provider_product_support_claim": False,
        }
        for field_name, expected_value in expected_boundary.items():
            if boundary.get(field_name) != expected_value:
                reasons.append(f"provenance_artifact_boundary_drift:{field_name}")
    reviewable_artifact_refs = provenance.get("reviewable_artifact_refs")
    if not isinstance(reviewable_artifact_refs, list):
        reasons.append("provenance_artifact_reviewable_refs_missing")
    else:
        required_refs = {
            EVIDENCE_ARTIFACT_PATH,
            VALIDATION_EVIDENCE_ARTIFACT_PATH,
            "tests/runtime/test_real_provider_sample_evidence.py",
        }
        missing_refs = required_refs.difference(reviewable_artifact_refs)
        for missing_ref in sorted(missing_refs):
            reasons.append(f"provenance_artifact_reviewable_ref_missing:{missing_ref}")
    return tuple(reasons)


def _evidence_report_snapshot_sha256(report: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json_bytes(_evidence_report_snapshot(report))).hexdigest()


def _evidence_report_snapshot(report: Mapping[str, Any]) -> dict[str, Any]:
    decision_matrix = report.get("decision_matrix", {})
    adapter_bound_execution = report.get("adapter_bound_execution", {})
    no_leakage = report.get("core_surface_no_leakage", {})
    external_provider_sample = report.get("external_provider_sample", {})
    provider_error_mapping = adapter_bound_execution.get("provider_error_mapping", {})
    snapshot = {
        "report_id": report.get("report_id"),
        "release": report.get("release"),
        "fr_ref": report.get("fr_ref"),
        "consumed_gate_ref": report.get("consumed_gate_ref"),
        "approved_slice": report.get("approved_slice"),
        "sample_origin": report.get("sample_origin"),
        "provider_support_claim": report.get("provider_support_claim"),
        "external_provider_sample": {
            "sample_id": external_provider_sample.get("sample_id"),
            "manifest_id": external_provider_sample.get("manifest_id"),
            "manifest_ref": external_provider_sample.get("manifest_ref"),
            "provenance_ref": external_provider_sample.get("provenance_ref"),
            "provenance_artifact_ref": external_provider_sample.get("provenance_artifact_ref"),
            "author_path": external_provider_sample.get("author_path"),
            "adapter_key": external_provider_sample.get("adapter_key"),
            "provider_identity_scope": external_provider_sample.get("provider_identity_scope"),
            "provider_key_redaction": external_provider_sample.get("provider_key_redaction"),
            "requirement_ref": external_provider_sample.get("requirement_ref"),
            "offer_ref": external_provider_sample.get("offer_ref"),
            "adapter_binding_ref": external_provider_sample.get("adapter_binding_ref"),
            "decision_ref": external_provider_sample.get("decision_ref"),
            "decision_contract_ref": external_provider_sample.get("decision_contract_ref"),
            "profile_proof_refs": external_provider_sample.get("profile_proof_refs"),
            "not_native_provider_self_evidence": external_provider_sample.get(
                "not_native_provider_self_evidence"
            ),
            "provider_support_claim": external_provider_sample.get("provider_support_claim"),
            "forbidden_claims": external_provider_sample.get("forbidden_claims"),
        },
        "decision_matrix": {
            "matched_case_ref": decision_matrix.get("matched_case_ref"),
            "matched_case_status": decision_matrix.get("matched_case", {}).get("decision_status"),
            "unmatched_case_ref": decision_matrix.get("unmatched_case_ref"),
            "unmatched_case_status": decision_matrix.get("unmatched_case", {}).get("decision_status"),
            "invalid_contract_case_ref": decision_matrix.get("invalid_contract_case_ref"),
            "invalid_contract_case_status": decision_matrix.get("invalid_contract_case", {}).get(
                "decision_status"
            ),
            "validator_commands": decision_matrix.get("validator_commands"),
        },
        "adapter_bound_execution": {
            "status": adapter_bound_execution.get("status"),
            "matched_decision_ref": adapter_bound_execution.get("matched_decision_ref"),
            "matched_decision_id": adapter_bound_execution.get("matched_decision_id"),
            "runtime_execution_ref": adapter_bound_execution.get("runtime_execution_ref"),
            "success_task_record_ref": adapter_bound_execution.get("success_task_record_ref"),
            "failure_task_record_ref": adapter_bound_execution.get("failure_task_record_ref"),
            "raw_payload_ref": adapter_bound_execution.get("raw_payload_ref"),
            "raw_payload_present": adapter_bound_execution.get("raw_payload_present"),
            "normalized_result_ref": adapter_bound_execution.get("normalized_result_ref"),
            "normalized_result_present": adapter_bound_execution.get("normalized_result_present"),
            "adapter_mapped_failed_envelope_ref": adapter_bound_execution.get(
                "adapter_mapped_failed_envelope_ref"
            ),
            "provider_error_mapping_checked": adapter_bound_execution.get(
                "provider_error_mapping_checked"
            ),
            "provider_side_error_code": provider_error_mapping.get("provider_side_error_code"),
            "adapter_mapped_error_code": provider_error_mapping.get("adapter_mapped_error_code"),
            "resource_profile_consumption_checked": adapter_bound_execution.get(
                "resource_profile_consumption_checked"
            ),
            "resource_lifecycle_disposition_checked": adapter_bound_execution.get(
                "resource_lifecycle_disposition_checked"
            ),
            "resource_lifecycle_disposition_hint": adapter_bound_execution.get(
                "resource_lifecycle_disposition_hint"
            ),
            "resource_lifecycle_release_reason": adapter_bound_execution.get(
                "resource_lifecycle_release_reason"
            ),
            "resource_lifecycle_failure_release_reason": adapter_bound_execution.get(
                "resource_lifecycle_failure_release_reason"
            ),
            "observability_carrier_checked": adapter_bound_execution.get(
                "observability_carrier_checked"
            ),
        },
        "core_surface_no_leakage": {
            "status": no_leakage.get("status"),
            "provider_identity_in_core_surface": no_leakage.get("provider_identity_in_core_surface"),
            "registry_discovery_checked": no_leakage.get("registry_discovery_checked"),
            "core_routing_checked": no_leakage.get("core_routing_checked"),
            "task_record_checked": no_leakage.get("task_record_checked"),
            "resource_lifecycle_checked": no_leakage.get("resource_lifecycle_checked"),
            "failed_envelope_checked": no_leakage.get("failed_envelope_checked"),
            "all_forbidden_paths_empty": no_leakage.get("all_forbidden_paths_empty"),
            "surfaces": no_leakage.get("surfaces"),
        },
        "validation_evidence_ref": VALIDATION_EVIDENCE_ARTIFACT_PATH,
    }
    return _canonical_json_value(snapshot)


def _canonical_json_value(value: Any) -> Any:
    return json.loads(_canonical_json_bytes(value).decode("utf-8"))


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _evidence_ref_fail_closed_reasons(report: Mapping[str, Any]) -> tuple[str, ...]:
    repo_root = Path(__file__).parents[1]
    reasons: list[str] = []
    artifact_path = repo_root / EVIDENCE_ARTIFACT_PATH
    if not artifact_path.exists():
        reasons.append("evidence_artifact_missing")
    else:
        try:
            artifact_text = artifact_path.read_text(encoding="utf-8")
        except OSError:
            reasons.append("evidence_artifact_unreadable")
        else:
            reasons.extend(_evidence_artifact_snapshot_reasons(artifact_text, report))
    validation_artifact_path = repo_root / VALIDATION_EVIDENCE_ARTIFACT_PATH
    if not validation_artifact_path.exists():
        reasons.append("validation_evidence_artifact_missing")
    elif report.get("validation_evidence", {}).get("artifact_ref") != VALIDATION_EVIDENCE_ARTIFACT_PATH:
        reasons.append("validation_evidence_artifact_ref_drift")
    manifest_path = repo_root / "syvert/fixtures/v0_9_external_provider_sample_manifest.json"
    if not manifest_path.exists():
        reasons.append("external_provider_sample_manifest_missing")
    for module_path in VALIDATION_MODULE_PATHS.values():
        if not (repo_root / module_path).exists():
            reasons.append(f"validation_module_missing:{module_path}")
    return tuple(reasons)


def _evidence_artifact_snapshot_reasons(
    artifact_text: str,
    report: Mapping[str, Any],
) -> tuple[str, ...]:
    start_index = artifact_text.find(EVIDENCE_ARTIFACT_JSON_START)
    end_index = artifact_text.find(EVIDENCE_ARTIFACT_JSON_END)
    if start_index == -1 or end_index == -1 or end_index <= start_index:
        return ("evidence_artifact_structured_snapshot_missing",)
    snapshot_text = artifact_text[start_index + len(EVIDENCE_ARTIFACT_JSON_START) : end_index].strip()
    if snapshot_text.startswith("```"):
        snapshot_lines = snapshot_text.splitlines()
        snapshot_text = "\n".join(snapshot_lines[1:-1]).strip()
    try:
        artifact_snapshot = json.loads(snapshot_text)
    except json.JSONDecodeError:
        return ("evidence_artifact_structured_snapshot_invalid_json",)
    if not isinstance(artifact_snapshot, Mapping):
        return ("evidence_artifact_structured_snapshot_not_object",)
    expected_snapshot = _evidence_report_snapshot(report)
    if _canonical_json_value(artifact_snapshot) != expected_snapshot:
        return ("evidence_artifact_structured_snapshot_drift",)
    expected_sha256 = _evidence_report_snapshot_sha256(report)
    if report.get("evidence_snapshot_sha256") != expected_sha256:
        return ("evidence_report_snapshot_sha256_drift",)
    validation_snapshot_sha256 = report.get("validation_evidence", {}).get("report_snapshot_sha256")
    if validation_snapshot_sha256 != expected_sha256:
        return ("validation_report_snapshot_sha256_drift",)
    return ()
