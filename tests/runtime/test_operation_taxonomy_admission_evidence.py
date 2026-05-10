from __future__ import annotations

import unittest

from syvert.adapter_provider_compatibility_decision import (
    COMPATIBILITY_DECISION_STATUS_MATCHED,
    decide_adapter_provider_compatibility,
)
from syvert.operation_taxonomy import (
    ADMISSION_ERROR_INVALID_ENTRY,
    ADMISSION_ERROR_NOT_STABLE,
    ADMISSION_STATUS_ADMITTED,
    ADMISSION_STATUS_INVALID_CONTRACT,
    OperationTaxonomyContractError,
    stable_operation_entry,
    validate_operation_taxonomy_entry,
)
from tests.runtime.adapter_provider_compatibility_decision_fixtures import copy_decision_input
from tests.runtime.operation_taxonomy_admission_fixtures import (
    copy_fake_adapter_admission_manifest,
    proposed_content_search_entry,
    stable_comment_collection_entry,
)


class OperationTaxonomyAdmissionEvidenceTests(unittest.TestCase):
    def test_fake_adapter_can_express_proposed_content_search_and_stable_comment_collection(self) -> None:
        manifest = copy_fake_adapter_admission_manifest()

        reports = [validate_operation_taxonomy_entry(entry) for entry in manifest["declared_taxonomy_entries"]]

        self.assertEqual([report.status for report in reports], [ADMISSION_STATUS_ADMITTED, ADMISSION_STATUS_ADMITTED])
        self.assertEqual({report.operation for report in reports}, {"content_search", "comment_collection"})
        self.assertTrue(manifest["execution_contract"]["comment_collection_runtime_delivery_allowed"])
        self.assertFalse(manifest["execution_contract"]["stable_lookup_allowed"])
        self.assertTrue(manifest["execution_contract"]["compatibility_match_allowed"])

    def test_proposed_content_search_is_not_stable_but_comment_collection_is_runtime_capability(self) -> None:
        content_search = proposed_content_search_entry()
        with self.assertRaises(OperationTaxonomyContractError) as raised:
            stable_operation_entry(
                operation=content_search["operation"],
                target_type=content_search["target_type"],
                collection_mode=content_search["collection_mode"],
            )

        self.assertEqual(raised.exception.code, ADMISSION_ERROR_NOT_STABLE)

        comment = stable_comment_collection_entry()
        entry = stable_operation_entry(
            operation=comment["operation"],
            target_type=comment["target_type"],
            collection_mode=comment["collection_mode"],
        )
        self.assertEqual(entry.contract_refs, ("FR-0404",))

    def test_comment_collection_stable_slice_matches_after_consumer_migration(self) -> None:
        input_value = copy_decision_input()
        input_value["requirement"]["capability"] = "comment_collection"
        input_value["requirement"]["resource_requirement"]["capability"] = "comment_collection"
        input_value["requirement"]["execution_requirement"] = {
            "operation": "comment_collection",
            "target_type": "content",
            "collection_mode": "paginated",
        }
        input_value["requirement"]["observability"]["requirement_id"] = (
            "xhs:comment_collection:comment_collection:content:paginated"
        )
        input_value["offer"]["capability_offer"] = {
            "capability": "comment_collection",
            "operation": "comment_collection",
            "target_type": "content",
            "collection_mode": "paginated",
        }
        input_value["offer"]["observability"]["capability"] = "comment_collection"
        input_value["offer"]["observability"]["operation"] = "comment_collection"
        input_value["offer"]["observability"]["offer_id"] = (
            "xhs:native_xhs_detail:comment_collection:comment_collection:content:paginated:v0.8.0"
        )

        decision = decide_adapter_provider_compatibility(input_value)

        self.assertEqual(decision.decision_status, COMPATIBILITY_DECISION_STATUS_MATCHED)
        self.assertNotEqual(decision.matched_profiles, ())

    def test_taxonomy_rejects_provider_workflow_marketplace_and_platform_private_fields(self) -> None:
        forbidden_fields = (
            "provider_selector",
            "fallback",
            "marketplace",
            "application_workflow",
            "platform_private_business_object",
        )
        for field_name in forbidden_fields:
            with self.subTest(field_name=field_name):
                entry = proposed_content_search_entry()
                entry[field_name] = "forbidden"

                report = validate_operation_taxonomy_entry(entry)

                self.assertEqual(report.status, ADMISSION_STATUS_INVALID_CONTRACT)
                self.assertEqual(report.error_code, ADMISSION_ERROR_INVALID_ENTRY)
                self.assertIn(field_name, str(report.details))


if __name__ == "__main__":
    unittest.main()
