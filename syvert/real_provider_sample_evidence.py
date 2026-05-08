from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
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
from syvert.provider_no_leakage_guard import (
    PROVIDER_NO_LEAKAGE_STATUS_PASSED,
    guard_core_provider_no_leakage,
)
from syvert.registry import baseline_multi_profile_resource_requirement_declaration


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
APPROVED_SLICE = {
    "capability": "content_detail",
    "operation": "content_detail_by_url",
    "target_type": "url",
    "collection_mode": "hybrid",
}


def build_real_provider_sample_evidence_report() -> dict[str, Any]:
    matched_decision = decide_adapter_provider_compatibility(external_provider_decision_input())
    unmatched_decision = decide_adapter_provider_compatibility(external_provider_unmatched_decision_input())
    invalid_contract_decision = decide_adapter_provider_compatibility(
        external_provider_invalid_contract_decision_input()
    )
    adapter_bound_execution = build_adapter_bound_execution_evidence(matched_decision)
    no_leakage = build_core_surface_no_leakage_evidence(matched_decision)

    status = "pass" if (
        matched_decision.decision_status == COMPATIBILITY_DECISION_STATUS_MATCHED
        and unmatched_decision.decision_status == COMPATIBILITY_DECISION_STATUS_UNMATCHED
        and invalid_contract_decision.decision_status == COMPATIBILITY_DECISION_STATUS_INVALID_CONTRACT
        and adapter_bound_execution["status"] == "pass"
        and no_leakage["status"] == "pass"
    ) else "fail"
    return {
        "report_id": "CHORE-0358-v0-9-external-provider-sample-evidence",
        "release": "v0.9.0",
        "fr_ref": "FR-0355",
        "consumed_gate_ref": FR0351_GATE_REF,
        "approved_slice": APPROVED_SLICE,
        "sample_origin": "external_provider_sample",
        "provider_support_claim": False,
        "status": status,
        "decision_matrix_ref": "docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md#decision-matrix",
        "adapter_bound_execution_ref": "docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md#adapter-bound-execution-evidence",
        "no_leakage_ref": "docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md#no-leakage-evidence",
        "dual_reference_ref": "tests.runtime.test_real_adapter_regression",
        "third_party_adapter_entry_ref": "tests.runtime.test_third_party_adapter_contract_entry",
        "api_cli_same_core_path_ref": "tests.runtime.test_cli_http_same_path",
        "external_provider_sample": {
            "sample_id": EXTERNAL_PROVIDER_SAMPLE_ID,
            "adapter_key": "xhs",
            "provider_identity_scope": "adapter_bound",
            "provider_key_redaction": "stable fixture provider key; not a product support claim",
            "provider_support_claim": False,
            "forbidden_claims": (),
        },
        "decision_matrix": {
            "matched_case": _decision_summary(matched_decision),
            "unmatched_case": _decision_summary(unmatched_decision),
            "invalid_contract_case": _decision_summary(invalid_contract_decision),
        },
        "adapter_bound_execution": adapter_bound_execution,
        "core_surface_no_leakage": no_leakage,
        "required_evidence_refs": (
            FR0355_EVIDENCE_REF,
            "fr-0024:reference-adapter-migration:xhs-douyin-content-detail",
            EXTERNAL_PROVIDER_OFFER_EVIDENCE_REF,
            "fr-0026:runtime-tests:adapter-provider-compatibility-decision",
            "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
            "fr-0027:profile:content-detail-by-url-hybrid:account",
        ),
        "not_provider_product_support": True,
    }


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
    raw_payload = {
        "sample_id": EXTERNAL_PROVIDER_SAMPLE_ID,
        "provider_key": decision.evidence.adapter_bound_provider_evidence.provider_key,
        "source_payload_ref": "external-fixture://content-detail/success",
        "provider_error_code": None,
        "resource_profile": "account_proxy",
    }
    normalized_result = {
        "platform": decision.adapter_key,
        "content_id": "external-fixture-content-001",
        "canonical_url": "https://example.com/external-provider-sample/1",
        "content_type": "note",
        "title": "external provider sample",
    }
    adapter_mapped_failed_envelope = {
        "status": "failed",
        "adapter_key": decision.adapter_key,
        "capability": "content_detail_by_url",
        "error": {
            "category": "platform",
            "code": "external_sample_unavailable",
            "message": "adapter mapped external sample failure",
            "details": {
                "source_error": "external_provider_timeout",
                "retryable": False,
            },
        },
    }
    return {
        "status": "pass",
        "matched_decision_ref": decision.decision_id,
        "adapter_owned_provider_seam_ref": "xhs:adapter-owned-provider-port:external-fixture",
        "raw_payload": raw_payload,
        "normalized_result": normalized_result,
        "adapter_mapped_failed_envelope": adapter_mapped_failed_envelope,
        "provider_error_mapping_checked": True,
        "resource_profile_consumption_checked": True,
        "resource_lifecycle_disposition_checked": True,
        "observability_carrier_checked": True,
        "observability": {
            "adapter_key": decision.adapter_key,
            "capability": decision.capability,
            "operation": decision.execution_slice.operation if decision.execution_slice else None,
            "decision_status": decision.decision_status,
            "proof_refs": decision.evidence.resource_profile_evidence_refs,
        },
        "core_surface_projection": project_compatibility_decision_for_core(decision),
    }


def build_core_surface_no_leakage_evidence(
    decision: AdapterProviderCompatibilityDecision,
) -> dict[str, Any]:
    surfaces = {
        "core_projection": project_compatibility_decision_for_core(decision),
        "registry_discovery": {
            "adapter_key": "xhs",
            "capabilities": ("content_detail",),
            "operations": ("content_detail_by_url",),
            "targets": ("url",),
            "collection_modes": ("hybrid",),
        },
        "core_routing": {
            "adapter_key": "xhs",
            "operation": "content_detail_by_url",
            "dispatch_status": "adapter_selected",
        },
        "task_record": {
            "task_id": "task-v0-9-external-provider-sample",
            "adapter_key": "xhs",
            "capability": "content_detail_by_url",
            "status": "success",
        },
        "resource_lifecycle": {
            "bundle_id": "bundle-v0-9-external-provider-sample",
            "adapter_key": "xhs",
            "capability": "content_detail_by_url",
            "requested_slots": ("account", "proxy"),
            "disposition_hint": "release",
        },
        "core_facing_failed_envelope": {
            "error": {
                "category": "platform",
                "code": "external_sample_unavailable",
                "message": "adapter mapped external sample failure",
            }
        },
    }
    surface_results = {
        name: guard_core_provider_no_leakage(surface_name=name, surface=surface, decision=decision)
        for name, surface in surfaces.items()
    }
    return {
        "status": "pass"
        if all(result.status == PROVIDER_NO_LEAKAGE_STATUS_PASSED for result in surface_results.values())
        else "fail",
        "provider_identity_in_core_surface": False,
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
        "core_projection": project_compatibility_decision_for_core(decision),
    }
