from __future__ import annotations

import unittest

from syvert.adapter_capability_requirement import (
    ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
    ADAPTER_REQUIREMENT_ERROR_INVALID_RESOURCE_REQUIREMENT,
    ADAPTER_REQUIREMENT_STATUS_DECLARED,
    ADAPTER_REQUIREMENT_STATUS_INVALID,
    ADAPTER_REQUIREMENT_STATUS_UNMATCHED,
    AdapterCapabilityExecutionRequirement,
    AdapterCapabilityLifecycleExpectation,
    AdapterCapabilityObservabilityExpectation,
    AdapterCapabilityRequirement,
    AdapterCapabilityRequirementEvidence,
    AdapterCapabilityRequirementValidationInput,
    validate_adapter_capability_requirement,
)
from tests.runtime.adapter_capability_requirement_fixtures import (
    copy_requirement,
    valid_adapter_capability_requirement,
)


class AdapterCapabilityRequirementTests(unittest.TestCase):
    def test_validator_accepts_legal_requirement_as_declared_when_resource_profiles_are_satisfied(self) -> None:
        result = validate_adapter_capability_requirement(
            AdapterCapabilityRequirementValidationInput(
                requirement=valid_adapter_capability_requirement(),
                available_resource_capabilities=("account",),
            )
        )

        self.assertEqual(result.status, ADAPTER_REQUIREMENT_STATUS_DECLARED)
        self.assertEqual(result.adapter_key, "xhs")
        self.assertEqual(result.capability, "content_detail")
        self.assertEqual(result.error_code, None)
        self.assertEqual(
            result.details,
            {
                "match_status": "matched",
                "requirement_id": "xhs:content_detail:content_detail_by_url:url:hybrid",
            },
        )

    def test_validator_returns_unmatched_for_legal_requirement_when_no_profile_is_satisfied(self) -> None:
        result = validate_adapter_capability_requirement(
            AdapterCapabilityRequirementValidationInput(
                requirement=valid_adapter_capability_requirement(),
                available_resource_capabilities=("proxy",),
            )
        )

        self.assertEqual(result.status, ADAPTER_REQUIREMENT_STATUS_UNMATCHED)
        self.assertEqual(result.error_code, None)
        self.assertEqual(
            result.details,
            {
                "match_status": "unmatched",
                "requirement_id": "xhs:content_detail:content_detail_by_url:url:hybrid",
            },
        )

    def test_validator_rejects_missing_required_field_as_invalid_contract(self) -> None:
        requirement = copy_requirement()
        del requirement["execution_requirement"]

        result = validate_adapter_capability_requirement(requirement)

        self.assert_invalid(result, ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT)
        self.assertEqual(result.details["missing_fields"], ("execution_requirement",))

    def test_validator_rejects_fail_closed_not_true_as_invalid_contract(self) -> None:
        requirement = copy_requirement()
        requirement["fail_closed"] = False

        result = validate_adapter_capability_requirement(requirement)

        self.assert_invalid(result, ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT)
        self.assertEqual(result.details["fail_closed"], False)

    def test_validator_rejects_legacy_single_declaration_resource_carrier(self) -> None:
        requirement = copy_requirement()
        requirement["resource_requirement"] = {
            "adapter_key": "xhs",
            "capability": "content_detail",
            "resource_dependency_mode": "required",
            "required_capabilities": ["account", "proxy"],
            "evidence_refs": [
                "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                "fr-0015:xhs:content-detail:url:hybrid:account-material",
                "fr-0015:regression:xhs:managed-proxy-seed",
            ],
        }

        result = validate_adapter_capability_requirement(requirement)

        self.assert_invalid(result, ADAPTER_REQUIREMENT_ERROR_INVALID_RESOURCE_REQUIREMENT)

    def test_validator_rejects_unknown_capability_as_invalid_contract(self) -> None:
        requirement = copy_requirement()
        requirement["capability"] = "search"

        result = validate_adapter_capability_requirement(requirement)

        self.assert_invalid(result, ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT)
        self.assertEqual(result.details["capability"], "search")

    def test_validator_rejects_profile_proof_mismatch_as_invalid_resource_requirement(self) -> None:
        requirement = copy_requirement()
        profile = requirement["resource_requirement"]["resource_requirement_profiles"][0]
        profile["required_capabilities"] = ["proxy"]

        result = validate_adapter_capability_requirement(requirement)

        self.assert_invalid(result, ADAPTER_REQUIREMENT_ERROR_INVALID_RESOURCE_REQUIREMENT)

    def test_validator_rejects_missing_profile_proof_as_invalid_resource_requirement(self) -> None:
        requirement = copy_requirement()
        profile = requirement["resource_requirement"]["resource_requirement_profiles"][0]
        profile["evidence_refs"] = []

        result = validate_adapter_capability_requirement(requirement)

        self.assert_invalid(result, ADAPTER_REQUIREMENT_ERROR_INVALID_RESOURCE_REQUIREMENT)

    def test_validator_rejects_canonical_dataclass_with_raw_resource_requirement_without_crashing(self) -> None:
        raw_requirement = copy_requirement()
        raw_requirement["resource_requirement"]["resource_requirement_profiles"][0]["evidence_refs"] = [
            "fr-0027:profile:content-detail-by-url-hybrid:proxy"
        ]
        requirement = AdapterCapabilityRequirement(
            adapter_key=raw_requirement["adapter_key"],
            capability=raw_requirement["capability"],
            execution_requirement=AdapterCapabilityExecutionRequirement(
                **raw_requirement["execution_requirement"],
            ),
            resource_requirement=raw_requirement["resource_requirement"],  # type: ignore[arg-type]
            evidence=AdapterCapabilityRequirementEvidence(
                resource_profile_evidence_refs=tuple(
                    raw_requirement["evidence"]["resource_profile_evidence_refs"],
                ),
                capability_requirement_evidence_refs=tuple(
                    raw_requirement["evidence"]["capability_requirement_evidence_refs"],
                ),
            ),
            lifecycle=AdapterCapabilityLifecycleExpectation(
                **raw_requirement["lifecycle"],
            ),
            observability=AdapterCapabilityObservabilityExpectation(
                requirement_id=raw_requirement["observability"]["requirement_id"],
                profile_keys=tuple(raw_requirement["observability"]["profile_keys"]),
                proof_refs=tuple(raw_requirement["observability"]["proof_refs"]),
                admission_outcome_fields=tuple(raw_requirement["observability"]["admission_outcome_fields"]),
            ),
            fail_closed=raw_requirement["fail_closed"],
        )

        result = validate_adapter_capability_requirement(requirement)

        self.assert_invalid(result, ADAPTER_REQUIREMENT_ERROR_INVALID_RESOURCE_REQUIREMENT)

    def test_validator_rejects_unapproved_requirement_level_evidence(self) -> None:
        requirement = copy_requirement()
        requirement["evidence"]["capability_requirement_evidence_refs"] = ["tmp:runtime-log"]

        result = validate_adapter_capability_requirement(requirement)

        self.assert_invalid(result, ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT)
        self.assertEqual(
            result.details["unsupported_capability_requirement_evidence_refs"],
            ("tmp:runtime-log",),
        )

    def test_validator_rejects_fabricated_requirement_level_evidence_with_approved_prefix(self) -> None:
        requirement = copy_requirement()
        requirement["evidence"]["capability_requirement_evidence_refs"] = [
            "fr-0024:manifest-fixture-validator:not-real"
        ]

        result = validate_adapter_capability_requirement(requirement)

        self.assert_invalid(result, ADAPTER_REQUIREMENT_ERROR_INVALID_RESOURCE_REQUIREMENT)
        self.assertEqual(
            result.details["unsupported_capability_requirement_evidence_refs"],
            ("fr-0024:manifest-fixture-validator:not-real",),
        )

    def test_validator_rejects_mapping_payloads_for_string_array_fields(self) -> None:
        cases = (
            ("evidence", "resource_profile_evidence_refs"),
            ("evidence", "capability_requirement_evidence_refs"),
            ("observability", "profile_keys"),
            ("observability", "proof_refs"),
            ("observability", "admission_outcome_fields"),
        )
        for section, field_name in cases:
            with self.subTest(section=section, field_name=field_name):
                requirement = copy_requirement()
                requirement[section][field_name] = {"account": True}

                result = validate_adapter_capability_requirement(requirement)

                self.assert_invalid(result, ADAPTER_REQUIREMENT_ERROR_INVALID_RESOURCE_REQUIREMENT)
                self.assertEqual(result.details["actual_type"], "dict")

    def test_validator_rejects_lifecycle_boundary_violation(self) -> None:
        requirement = copy_requirement()
        requirement["lifecycle"]["resource_profiles_drive_admission"] = False

        result = validate_adapter_capability_requirement(requirement)

        self.assert_invalid(result, ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT)

    def test_validator_rejects_lifecycle_runtime_fields(self) -> None:
        requirement = copy_requirement()
        requirement["lifecycle"]["acquire_strategy"] = "adapter_pool"

        result = validate_adapter_capability_requirement(requirement)

        self.assert_invalid(result, ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT)
        self.assertEqual(result.details["extra_fields"], ("acquire_strategy",))

    def test_validator_rejects_observability_technical_field_leakage(self) -> None:
        leaked_values = ("browser_profile", "browserProfile", "networkTier", "providerKey", "xhs:provider:native")
        for leaked_value in leaked_values:
            with self.subTest(leaked_value=leaked_value):
                requirement = copy_requirement()
                requirement["observability"]["requirement_id"] = leaked_value

                result = validate_adapter_capability_requirement(requirement)

                self.assert_invalid(result, ADAPTER_REQUIREMENT_ERROR_INVALID_RESOURCE_REQUIREMENT)

    def test_validator_rejects_provider_priority_and_fallback_fields(self) -> None:
        requirement = copy_requirement()
        requirement["provider_offer"] = {"provider_key": "native"}

        result = validate_adapter_capability_requirement(requirement)

        self.assert_invalid(result, ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT)
        self.assertEqual(result.details["forbidden_fields"], ("provider_key", "provider_offer"))

        requirement = copy_requirement()
        requirement["resource_requirement"]["resource_requirement_profiles"][0]["priority"] = 1

        result = validate_adapter_capability_requirement(requirement)

        self.assert_invalid(result, ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT)
        self.assertEqual(result.details["forbidden_fields"], ("priority",))

        requirement = copy_requirement()
        requirement["resource_requirement"]["fallback"] = "account"

        result = validate_adapter_capability_requirement(requirement)

        self.assert_invalid(result, ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT)
        self.assertEqual(result.details["forbidden_fields"], ("fallback",))

    def test_legal_requirement_does_not_emit_provider_compatibility_fields(self) -> None:
        result = validate_adapter_capability_requirement(
            AdapterCapabilityRequirementValidationInput(
                requirement=valid_adapter_capability_requirement(adapter_key="douyin"),
                available_resource_capabilities=("account", "proxy"),
            )
        )

        self.assertEqual(result.status, ADAPTER_REQUIREMENT_STATUS_DECLARED)
        self.assertNotIn("provider_key", result.details)
        self.assertNotIn("compatibility_decision", result.details)

    def assert_invalid(self, result, error_code: str) -> None:
        self.assertEqual(result.status, ADAPTER_REQUIREMENT_STATUS_INVALID)
        self.assertEqual(result.failure_category, "runtime_contract")
        self.assertEqual(result.error_code, error_code)


if __name__ == "__main__":
    unittest.main()
