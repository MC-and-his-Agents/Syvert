from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from functools import lru_cache
import json
import os
from pathlib import Path
import subprocess
import sys
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
FR0355_EVIDENCE_REF = "fr-0355:external-provider-sample-evidence:v0-9"
FR0351_GATE_REF = "FR-0351:provider_compatibility_sample"
FR0026_DECISION_EVIDENCE_REF = "fr-0026:runtime-tests:adapter-provider-compatibility-decision"
EVIDENCE_ARTIFACT_PATH = (
    "docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md"
)
EVIDENCE_ARTIFACT_REQUIRED_ANCHORS = (
    "## Decision Matrix",
    "## Adapter-Bound Execution Evidence",
    "## No-Leakage Evidence",
    "## Validation Evidence",
)
VALIDATION_MODULE_PATHS = {
    "tests.runtime.test_real_provider_sample_evidence": "tests/runtime/test_real_provider_sample_evidence.py",
    "tests.runtime.test_real_adapter_regression": "tests/runtime/test_real_adapter_regression.py",
    "tests.runtime.test_third_party_adapter_contract_entry": "tests/runtime/test_third_party_adapter_contract_entry.py",
    "tests.runtime.test_cli_http_same_path": "tests/runtime/test_cli_http_same_path.py",
}
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
NESTED_VALIDATION_ENV = "SYVERT_REAL_PROVIDER_SAMPLE_NESTED_VALIDATION"
REQUIRED_CORE_NO_LEAKAGE_SURFACES = (
    "registry_discovery",
    "core_routing",
    "task_record",
    "resource_lifecycle",
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
    validation_evidence = build_required_validation_evidence()

    fail_closed_reasons = _fail_closed_reasons(
        matched_decision=matched_decision,
        unmatched_decision=unmatched_decision,
        invalid_contract_decision=invalid_contract_decision,
        adapter_bound_execution=adapter_bound_execution,
        no_leakage=no_leakage,
        manifest=manifest,
        validation_evidence=validation_evidence,
    )
    status = "pass" if not fail_closed_reasons else "fail"
    report = {
        "report_id": "CHORE-0358-v0-9-external-provider-sample-evidence",
        "release": "v0.9.0",
        "fr_ref": "FR-0355",
        "consumed_gate_ref": FR0351_GATE_REF,
        "approved_slice": dict(manifest.get("approved_slice", {})),
        "sample_origin": manifest.get("sample_origin"),
        "provider_support_claim": manifest.get("provider_support_claim"),
        "status": status,
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
) -> dict[str, Any]:
    if decision.decision_status != COMPATIBILITY_DECISION_STATUS_MATCHED:
        return {
            "status": "fail",
            "reason": "adapter_bound_execution_requires_matched_decision",
            "matched_decision_ref": decision.decision_id,
        }
    execution = run_external_provider_sample_runtime_execution()
    success_envelope = execution["success"]["envelope"]
    failed_envelope = execution["failure"]["envelope"]
    checks = _adapter_bound_execution_checks(execution)
    evidence_status = (
        "pass"
        if (
            success_envelope.get("status") == "success"
            and failed_envelope.get("status") == "failed"
            and execution["success"]["provider_calls"]
            and execution["failure"]["provider_calls"]
            and all(checks.values())
        )
        else "fail"
    )
    return {
        "status": evidence_status,
        "matched_decision_ref": "fr-0355:decision-matrix:matched",
        "matched_decision_id": decision.decision_id,
        "adapter_owned_provider_seam_ref": "xhs:adapter-owned-provider-port:external-fixture",
        "raw_payload_ref": "external-fixture://content-detail/success#raw",
        "raw_payload": deepcopy(success_envelope.get("raw")),
        "normalized_result_ref": "external-fixture://content-detail/success#normalized",
        "normalized_result": deepcopy(success_envelope.get("normalized")),
        "adapter_mapped_failed_envelope_ref": (
            "external-fixture://content-detail/provider-timeout#adapter-mapped-failed-envelope"
        ),
        "adapter_mapped_failed_envelope": deepcopy(failed_envelope),
        "provider_error_mapping": deepcopy(execution["failure"].get("provider_error_mapping", {})),
        "provider_error_mapping_checked": checks["provider_error_mapping_checked"],
        "resource_profile_consumption_checked": checks["resource_profile_consumption_checked"],
        "resource_lifecycle_disposition_checked": checks["resource_lifecycle_disposition_checked"],
        "resource_lifecycle_disposition_hint": "release",
        "observability_carrier_checked": checks["observability_carrier_checked"],
        "runtime_execution_ref": execution["runtime_execution_ref"],
        "success_task_record_ref": execution["success"]["task_record_ref"],
        "failure_task_record_ref": execution["failure"]["task_record_ref"],
        "observability": {
            "adapter_key": decision.adapter_key,
            "capability": decision.capability,
            "operation": decision.execution_slice.operation if decision.execution_slice else None,
            "decision_status": decision.decision_status,
            "proof_refs": decision.evidence.resource_profile_evidence_refs,
        },
        "core_surface_projection_ref": (
            "docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md"
            "#core-surface-projection"
        ),
        "core_surface_projection": _core_surface_status_projection(decision),
        "core_runtime_surfaces": deepcopy(execution["core_runtime_surfaces"]),
    }


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


def _adapter_bound_execution_checks(execution: Mapping[str, Any]) -> dict[str, bool]:
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
    return {
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
        ),
        "observability_carrier_checked": (
            success_task_record.get("status") == "succeeded"
            and failure_task_record.get("status") == "failed"
            and isinstance(success_task_record.get("result"), Mapping)
            and isinstance(failure_task_record.get("result"), Mapping)
        ),
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


def build_required_validation_evidence() -> dict[str, Any]:
    return _build_required_validation_evidence_cached()


@lru_cache(maxsize=1)
def _build_required_validation_evidence_cached() -> dict[str, Any]:
    repo_root = Path(__file__).parents[1]
    env = dict(os.environ)
    env[NESTED_VALIDATION_ENV] = "1"
    commands: list[dict[str, Any]] = []
    for validation_name, modules in REQUIRED_VALIDATION_COMMANDS:
        command = (sys.executable, "-m", "unittest", *modules)
        completed = subprocess.run(
            command,
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        commands.append(
            {
                "validation": validation_name,
                "command": _validation_command_text(modules),
                "status": "pass" if completed.returncode == 0 else "fail",
                "returncode": completed.returncode,
                "stdout_tail": completed.stdout[-1000:],
                "stderr_tail": completed.stderr[-1000:],
            }
        )
    return {
        "status": "pass" if all(command["status"] == "pass" for command in commands) else "fail",
        "commands": tuple(commands),
    }


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


def _evidence_ref_fail_closed_reasons(report: Mapping[str, Any]) -> tuple[str, ...]:
    repo_root = Path(__file__).parents[1]
    reasons: list[str] = []
    artifact_path = repo_root / EVIDENCE_ARTIFACT_PATH
    if not artifact_path.exists():
        reasons.append("evidence_artifact_missing")
    else:
        artifact_text = artifact_path.read_text(encoding="utf-8")
        for anchor in EVIDENCE_ARTIFACT_REQUIRED_ANCHORS:
            if anchor not in artifact_text:
                reasons.append(f"evidence_artifact_anchor_missing:{anchor}")
        reasons.extend(_artifact_report_consistency_reasons(artifact_text, report))
    manifest_path = repo_root / "syvert/fixtures/v0_9_external_provider_sample_manifest.json"
    if not manifest_path.exists():
        reasons.append("external_provider_sample_manifest_missing")
    for module_path in VALIDATION_MODULE_PATHS.values():
        if not (repo_root / module_path).exists():
            reasons.append(f"validation_module_missing:{module_path}")
    return tuple(reasons)


def _artifact_report_consistency_reasons(artifact_text: str, report: Mapping[str, Any]) -> tuple[str, ...]:
    required_tokens = (
        f"release：`{report.get('release')}`",
        f"fr_ref：`{report.get('fr_ref')}`",
        f"consumed_gate_ref：`{report.get('consumed_gate_ref')}`",
        f"sample_origin：`{report.get('sample_origin')}`",
        f"provider_support_claim：`{str(report.get('provider_support_claim')).lower()}`",
        f"status：`{report.get('status')}`",
        f"matched_case_ref：`{report.get('decision_matrix', {}).get('matched_case_ref')}`",
        f"unmatched_case_ref：`{report.get('decision_matrix', {}).get('unmatched_case_ref')}`",
        f"invalid_contract_case_ref：`{report.get('decision_matrix', {}).get('invalid_contract_case_ref')}`",
        "provider_side_error_code=provider_unavailable",
        "provider_unavailable -> external_sample_unavailable",
        "provider_identity_in_core_surface：`false`",
    )
    reasons = [
        f"evidence_artifact_token_missing:{token}"
        for token in required_tokens
        if token not in artifact_text
    ]
    for command in report.get("decision_matrix", {}).get("validator_commands", ()):
        if str(command) not in artifact_text:
            reasons.append(f"evidence_artifact_validator_command_missing:{command}")
    for fixture_ref in EXPECTED_MANIFEST_FIXTURE_REFS:
        if fixture_ref not in artifact_text:
            reasons.append(f"evidence_artifact_fixture_ref_missing:{fixture_ref}")
    return tuple(reasons)
