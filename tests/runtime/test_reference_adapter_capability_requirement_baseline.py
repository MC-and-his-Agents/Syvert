from __future__ import annotations

from dataclasses import replace
import unittest

from syvert.adapter_capability_requirement import (
    ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT,
    ADAPTER_REQUIREMENT_STATUS_DECLARED,
    ADAPTER_REQUIREMENT_STATUS_INVALID,
    ADAPTER_REQUIREMENT_STATUS_UNMATCHED,
    AdapterCapabilityRequirementValidationInput,
    validate_adapter_capability_requirement,
)
from syvert.adapters.douyin import DouyinAdapter
from syvert.adapters.xhs import XhsAdapter
from syvert.runtime import CONTENT_DETAIL


REFERENCE_ADAPTERS = (XhsAdapter, DouyinAdapter)


class ReferenceAdapterCapabilityRequirementBaselineTests(unittest.TestCase):
    def test_reference_adapters_expose_fr0024_requirement_from_fr0027_resource_truth(self) -> None:
        for adapter_type in REFERENCE_ADAPTERS:
            with self.subTest(adapter_key=adapter_type.adapter_key):
                requirements = adapter_type.capability_requirement_declarations

                self.assertEqual(len(requirements), 1)
                requirement = requirements[0]
                self.assertEqual(requirement.adapter_key, adapter_type.adapter_key)
                self.assertEqual(requirement.capability, CONTENT_DETAIL)
                self.assertEqual(
                    requirement.resource_requirement,
                    adapter_type.resource_requirement_declarations[0],
                )
                self.assertEqual(
                    requirement.evidence.resource_profile_evidence_refs,
                    (
                        "fr-0027:profile:content-detail-by-url-hybrid:account-proxy",
                        "fr-0027:profile:content-detail-by-url-hybrid:account",
                    ),
                )
                self.assertEqual(
                    requirement.evidence.capability_requirement_evidence_refs,
                    ("fr-0024:reference-adapter-migration:xhs-douyin-content-detail",),
                )
                self.assertTrue(requirement.fail_closed)

    def test_reference_adapter_requirements_validate_as_declared_when_profile_is_satisfied(self) -> None:
        for adapter_type in REFERENCE_ADAPTERS:
            with self.subTest(adapter_key=adapter_type.adapter_key):
                result = validate_adapter_capability_requirement(
                    AdapterCapabilityRequirementValidationInput(
                        requirement=adapter_type.capability_requirement_declarations[0],
                        available_resource_capabilities=("account",),
                    )
                )

                self.assertEqual(result.status, ADAPTER_REQUIREMENT_STATUS_DECLARED)
                self.assertEqual(result.adapter_key, adapter_type.adapter_key)
                self.assertEqual(result.capability, CONTENT_DETAIL)
                self.assertEqual(
                    result.details,
                    {
                        "match_status": "matched",
                        "requirement_id": (
                            f"{adapter_type.adapter_key}:content_detail:content_detail_by_url:url:hybrid"
                        ),
                    },
                )

    def test_reference_adapter_requirements_validate_as_unmatched_without_satisfied_profile(self) -> None:
        for adapter_type in REFERENCE_ADAPTERS:
            with self.subTest(adapter_key=adapter_type.adapter_key):
                result = validate_adapter_capability_requirement(
                    AdapterCapabilityRequirementValidationInput(
                        requirement=adapter_type.capability_requirement_declarations[0],
                        available_resource_capabilities=("proxy",),
                    )
                )

                self.assertEqual(result.status, ADAPTER_REQUIREMENT_STATUS_UNMATCHED)
                self.assertEqual(result.adapter_key, adapter_type.adapter_key)
                self.assertEqual(result.capability, CONTENT_DETAIL)
                self.assertEqual(
                    result.details,
                    {
                        "match_status": "unmatched",
                        "requirement_id": (
                            f"{adapter_type.adapter_key}:content_detail:content_detail_by_url:url:hybrid"
                        ),
                    },
                )

    def test_reference_adapter_requirement_baseline_fails_closed_when_contract_drifts(self) -> None:
        for adapter_type in REFERENCE_ADAPTERS:
            with self.subTest(adapter_key=adapter_type.adapter_key):
                requirement = replace(
                    adapter_type.capability_requirement_declarations[0],
                    fail_closed=False,
                )

                result = validate_adapter_capability_requirement(requirement)

                self.assertEqual(result.status, ADAPTER_REQUIREMENT_STATUS_INVALID)
                self.assertEqual(result.error_code, ADAPTER_REQUIREMENT_ERROR_INVALID_CONTRACT)
                self.assertEqual(result.details, {"fail_closed": False})


if __name__ == "__main__":
    unittest.main()
