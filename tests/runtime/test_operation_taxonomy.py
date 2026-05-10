from __future__ import annotations

import unittest

from syvert.operation_taxonomy import (
    ADMISSION_ERROR_DUPLICATE_OPERATION,
    ADMISSION_ERROR_INVALID_ENTRY,
    ADMISSION_ERROR_NOT_STABLE,
    ADMISSION_STATUS_ADMITTED,
    ADMISSION_STATUS_INVALID_CONTRACT,
    CAPABILITY_LIFECYCLE_DEPRECATED,
    CAPABILITY_LIFECYCLE_PROPOSED,
    CAPABILITY_LIFECYCLE_STABLE,
    DEFAULT_OPERATION_TAXONOMY,
    OperationTaxonomyContractError,
    OperationTaxonomyEntry,
    STABLE_CONTENT_DETAIL_ENTRY,
    is_stable_operation,
    proposed_operation_taxonomy_entries,
    stable_operation_entry,
    validate_operation_taxonomy_entry,
    validate_operation_taxonomy_registry,
)


class OperationTaxonomyTests(unittest.TestCase):
    def test_stable_content_detail_lookup_returns_runtime_entry(self) -> None:
        entry = stable_operation_entry(
            operation="content_detail_by_url",
            target_type="url",
            collection_mode="hybrid",
        )

        self.assertEqual(entry.capability_family, "content_detail")
        self.assertEqual(entry.lifecycle, CAPABILITY_LIFECYCLE_STABLE)
        self.assertTrue(entry.runtime_delivery)
        self.assertTrue(
            is_stable_operation(
                operation="content_detail_by_url",
                target_type="url",
                collection_mode="hybrid",
            )
        )

    def test_stable_search_and_list_by_creator_lookup_return_runtime_entry(self) -> None:
        search = stable_operation_entry(
            operation="content_search_by_keyword",
            target_type="keyword",
            collection_mode="paginated",
        )
        listing = stable_operation_entry(
            operation="content_list_by_creator",
            target_type="creator",
            collection_mode="paginated",
        )

        self.assertEqual(search.capability_family, "content_search")
        self.assertTrue(search.runtime_delivery)
        self.assertEqual(search.lifecycle, CAPABILITY_LIFECYCLE_STABLE)
        self.assertEqual(listing.capability_family, "content_list")
        self.assertTrue(listing.runtime_delivery)
        self.assertEqual(listing.lifecycle, CAPABILITY_LIFECYCLE_STABLE)
        self.assertTrue(
            is_stable_operation(
                operation="content_search_by_keyword",
                target_type="keyword",
                collection_mode="paginated",
            )
        )
        self.assertTrue(
            is_stable_operation(
                operation="content_list_by_creator",
                target_type="creator",
                collection_mode="paginated",
            )
        )

    def test_stable_comment_collection_lookup_returns_runtime_entry(self) -> None:
        entry = stable_operation_entry(
            operation="comment_collection",
            target_type="content",
            collection_mode="paginated",
        )

        self.assertEqual(entry.capability_family, "comment_collection")
        self.assertTrue(entry.runtime_delivery)
        self.assertEqual(entry.lifecycle, CAPABILITY_LIFECYCLE_STABLE)
        self.assertEqual(entry.contract_refs, ("FR-0404",))
        self.assertTrue(
            is_stable_operation(
                operation="comment_collection",
                target_type="content",
                collection_mode="paginated",
            )
        )

    def test_proposed_candidates_are_registered_but_not_stable_runtime_operations(self) -> None:
        proposed_operations = {entry.operation for entry in proposed_operation_taxonomy_entries()}

        self.assertEqual(
            proposed_operations,
            {
                "content_search",
                "content_list",
                "creator_profile",
                "media_asset_fetch",
                "media_upload",
                "content_publish",
                "batch_execution",
                "scheduled_execution",
                "dataset_sink",
            },
        )
        for entry in proposed_operation_taxonomy_entries():
            self.assertEqual(entry.lifecycle, CAPABILITY_LIFECYCLE_PROPOSED)
            self.assertFalse(entry.runtime_delivery)
            report = validate_operation_taxonomy_entry(entry)
            self.assertEqual(report.status, ADMISSION_STATUS_ADMITTED)
            self.assertFalse(
                is_stable_operation(
                    operation=entry.operation,
                    target_type=entry.target_type,
                    collection_mode=entry.collection_mode,
                )
            )

    def test_stable_lookup_rejects_proposed_candidate(self) -> None:
        with self.assertRaises(OperationTaxonomyContractError) as raised:
            stable_operation_entry(
                operation="content_search",
                target_type="query",
                collection_mode="paginated",
            )

        self.assertEqual(raised.exception.code, ADMISSION_ERROR_NOT_STABLE)

    def test_duplicate_operation_slice_is_invalid_contract(self) -> None:
        duplicate = OperationTaxonomyEntry(
            capability_family=STABLE_CONTENT_DETAIL_ENTRY.capability_family,
            operation=STABLE_CONTENT_DETAIL_ENTRY.operation,
            target_type=STABLE_CONTENT_DETAIL_ENTRY.target_type,
            execution_mode=STABLE_CONTENT_DETAIL_ENTRY.execution_mode,
            collection_mode=STABLE_CONTENT_DETAIL_ENTRY.collection_mode,
            lifecycle=CAPABILITY_LIFECYCLE_PROPOSED,
            runtime_delivery=False,
            contract_refs=("FR-0368",),
            admission_evidence_refs=(),
        )

        reports = validate_operation_taxonomy_registry((STABLE_CONTENT_DETAIL_ENTRY, duplicate))

        self.assertTrue(
            any(
                report.status == ADMISSION_STATUS_INVALID_CONTRACT
                and report.error_code == ADMISSION_ERROR_DUPLICATE_OPERATION
                for report in reports
            )
        )

    def test_invalid_lifecycle_is_invalid_contract(self) -> None:
        report = validate_operation_taxonomy_entry(
            {
                "capability_family": "content_search",
                "operation": "content_search",
                "target_type": "query",
                "execution_mode": "single",
                "collection_mode": "paginated",
                "lifecycle": "reserved",
                "runtime_delivery": False,
                "contract_refs": ("FR-0368",),
                "admission_evidence_refs": (),
            }
        )

        self.assertEqual(report.status, ADMISSION_STATUS_INVALID_CONTRACT)
        self.assertEqual(report.error_code, ADMISSION_ERROR_INVALID_ENTRY)

    def test_operation_must_project_from_capability_family(self) -> None:
        report = validate_operation_taxonomy_entry(
            {
                "capability_family": "content_search",
                "operation": "comment_collection",
                "target_type": "query",
                "execution_mode": "single",
                "collection_mode": "paginated",
                "lifecycle": CAPABILITY_LIFECYCLE_PROPOSED,
                "runtime_delivery": False,
                "contract_refs": ("FR-0368",),
                "admission_evidence_refs": (),
            }
        )

        self.assertEqual(report.status, ADMISSION_STATUS_INVALID_CONTRACT)
        self.assertEqual(report.error_code, ADMISSION_ERROR_INVALID_ENTRY)
        self.assertIn("capability family", str(report.details))

    def test_deprecated_operation_is_not_stable(self) -> None:
        deprecated = OperationTaxonomyEntry(
            capability_family="content_detail",
            operation="content_detail_legacy",
            target_type="url",
            execution_mode="single",
            collection_mode="hybrid",
            lifecycle=CAPABILITY_LIFECYCLE_DEPRECATED,
            runtime_delivery=False,
            contract_refs=("FR-0368",),
            admission_evidence_refs=(),
        )

        report = validate_operation_taxonomy_entry(deprecated)
        self.assertEqual(report.status, ADMISSION_STATUS_ADMITTED)
        with self.assertRaises(OperationTaxonomyContractError) as raised:
            stable_operation_entry(
                operation="content_detail_legacy",
                target_type="url",
                collection_mode="hybrid",
                entries=(*DEFAULT_OPERATION_TAXONOMY, deprecated),
            )

        self.assertEqual(raised.exception.code, ADMISSION_ERROR_NOT_STABLE)

    def test_forbidden_platform_or_workflow_fields_are_rejected(self) -> None:
        report = validate_operation_taxonomy_entry(
            {
                "capability_family": "content_search",
                "operation": "content_search",
                "target_type": "query",
                "execution_mode": "single",
                "collection_mode": "paginated",
                "lifecycle": CAPABILITY_LIFECYCLE_PROPOSED,
                "runtime_delivery": False,
                "contract_refs": ("FR-0368",),
                "admission_evidence_refs": (),
                "provider_selector": "not-core-taxonomy",
            }
        )

        self.assertEqual(report.status, ADMISSION_STATUS_INVALID_CONTRACT)
        self.assertIn("provider_selector", str(report.details))


if __name__ == "__main__":
    unittest.main()
