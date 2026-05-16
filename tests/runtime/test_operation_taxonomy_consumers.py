from __future__ import annotations

from datetime import datetime, timezone
import unittest
from unittest import mock

from syvert.adapter_capability_requirement import (
    ADAPTER_REQUIREMENT_STATUS_INVALID,
    APPROVED_ADAPTER_CAPABILITY,
    APPROVED_EXECUTION_REQUIREMENT,
    AdapterCapabilityRequirementValidationInput,
    validate_adapter_capability_requirement,
)
from syvert.adapter_provider_compatibility_decision import (
    COMPATIBILITY_DECISION_STATUS_INVALID_CONTRACT,
    decide_adapter_provider_compatibility,
)
from syvert.batch_dataset import (
    BatchDatasetContractError,
    BatchRequest,
    BatchTargetItem,
    ReferenceDatasetSink,
    execute_batch_request,
    validate_batch_target_item,
)
from syvert.operation_taxonomy import stable_operation_entry
from syvert.provider_capability_offer import (
    APPROVED_CAPABILITY_OFFER,
    APPROVED_PROVIDER_CAPABILITY,
    PROVIDER_OFFER_STATUS_INVALID,
    validate_provider_capability_offer,
)
from tests.runtime.adapter_capability_requirement_fixtures import copy_requirement
from tests.runtime.adapter_provider_compatibility_decision_fixtures import copy_decision_input
from tests.runtime.provider_capability_offer_fixtures import copy_offer
from tests.runtime.test_task_record import TEST_ADAPTER_KEY, make_comment_collection_result


class CursorCommentAdapter:
    supported_capabilities = frozenset({"comment_collection"})
    supported_targets = frozenset({"content"})
    supported_collection_modes = frozenset({"paginated"})

    def __init__(self) -> None:
        self.request_cursors = []

    def execute(self, request):
        self.request_cursors.append(request.input.comment_request_cursor)
        payload = make_comment_collection_result(target_ref=request.input.content_ref or "")
        payload["items"][0]["dedup_key"] = "comment:reply-1"
        payload["items"][0]["source_id"] = "reply-1"
        payload["items"][0]["source_ref"] = "comment://reply-1"
        payload["items"][0]["normalized"]["source_id"] = "reply-1"
        payload["items"][0]["normalized"]["canonical_ref"] = "comment:reply-1"
        payload["items"][0]["normalized"]["parent_comment_ref"] = "comment:root-1"
        payload["items"][0]["normalized"]["target_comment_ref"] = "comment:root-1"
        return payload


class OperationTaxonomyConsumerMigrationTests(unittest.TestCase):
    def test_legacy_approved_constants_are_derived_from_taxonomy_stable_lookup(self) -> None:
        stable = stable_operation_entry(
            operation="content_detail_by_url",
            target_type="url",
            collection_mode="hybrid",
        )

        self.assertEqual(APPROVED_ADAPTER_CAPABILITY, stable.capability_family)
        self.assertEqual(APPROVED_PROVIDER_CAPABILITY, stable.capability_family)
        self.assertEqual(
            APPROVED_EXECUTION_REQUIREMENT,
            {
                "operation": stable.operation,
                "target_type": stable.target_type,
                "collection_mode": stable.collection_mode,
            },
        )
        self.assertEqual(
            APPROVED_CAPABILITY_OFFER,
            {
                "capability": stable.capability_family,
                "operation": stable.operation,
                "target_type": stable.target_type,
                "collection_mode": stable.collection_mode,
            },
        )

    def test_requirement_offer_and_decision_accept_stable_collection_runtime_slice(self) -> None:
        requirement = copy_requirement()
        requirement["capability"] = "content_search"
        requirement["resource_requirement"]["capability"] = "content_search"
        requirement["execution_requirement"] = {
            "operation": "content_search_by_keyword",
            "target_type": "keyword",
            "collection_mode": "paginated",
        }
        requirement["observability"]["requirement_id"] = "xhs:content_search:content_search_by_keyword:keyword:paginated"

        offer = copy_offer()
        offer["capability_offer"] = {
            "capability": "content_search",
            "operation": "content_search_by_keyword",
            "target_type": "keyword",
            "collection_mode": "paginated",
        }
        offer["observability"]["capability"] = "content_search"
        offer["observability"]["operation"] = "content_search_by_keyword"
        offer["observability"]["offer_id"] = (
            "xhs:native_xhs_detail:content_search:content_search_by_keyword:keyword:paginated:v0.8.0"
        )

        decision_input = copy_decision_input()
        decision_input["requirement"] = requirement
        decision_input["offer"] = offer

        self.assertEqual(
            validate_adapter_capability_requirement(
                AdapterCapabilityRequirementValidationInput(
                    requirement=requirement,
                    available_resource_capabilities=("account", "proxy"),
                )
            ).status,
            "declared",
        )
        self.assertEqual(validate_provider_capability_offer(offer).status, "declared")
        self.assertEqual(decide_adapter_provider_compatibility(decision_input).decision_status, "matched")

    def test_requirement_offer_and_decision_accept_comment_collection_runtime_slice(self) -> None:
        requirement = copy_requirement()
        requirement["capability"] = "comment_collection"
        requirement["resource_requirement"]["capability"] = "comment_collection"
        requirement["execution_requirement"] = {
            "operation": "comment_collection",
            "target_type": "content",
            "collection_mode": "paginated",
        }
        requirement["observability"]["requirement_id"] = "xhs:comment_collection:comment_collection:content:paginated"

        offer = copy_offer()
        offer["capability_offer"] = {
            "capability": "comment_collection",
            "operation": "comment_collection",
            "target_type": "content",
            "collection_mode": "paginated",
        }
        offer["observability"]["capability"] = "comment_collection"
        offer["observability"]["operation"] = "comment_collection"
        offer["observability"]["offer_id"] = (
            "xhs:native_xhs_detail:comment_collection:comment_collection:content:paginated:v0.8.0"
        )

        decision_input = copy_decision_input()
        decision_input["requirement"] = requirement
        decision_input["offer"] = offer

        self.assertEqual(
            validate_adapter_capability_requirement(
                AdapterCapabilityRequirementValidationInput(
                    requirement=requirement,
                    available_resource_capabilities=("account", "proxy"),
                )
            ).status,
            "declared",
        )
        self.assertEqual(validate_provider_capability_offer(offer).status, "declared")
        decision = decide_adapter_provider_compatibility(decision_input)
        self.assertEqual(decision.decision_status, "matched")
        self.assertEqual(decision.capability, "comment_collection")
        self.assertEqual(decision.execution_slice.operation, "comment_collection")

    def test_batch_target_items_consume_stable_read_side_runtime_slices(self) -> None:
        cases = (
            ("content_search_by_keyword", "keyword", "deep learning"),
            ("content_list_by_creator", "creator", "creator-001"),
            ("comment_collection", "content", "content-001"),
            ("creator_profile_by_id", "creator", "creator-001"),
            ("media_asset_fetch_by_ref", "media_ref", "media:asset-001"),
        )

        for operation, target_type, target_ref in cases:
            with self.subTest(operation=operation):
                collection_mode = (
                    "paginated"
                    if operation in {"content_search_by_keyword", "content_list_by_creator", "comment_collection"}
                    else "direct"
                )
                stable = stable_operation_entry(
                    operation=operation,
                    target_type=target_type,
                    collection_mode=collection_mode,
                )
                item = BatchTargetItem(
                    item_id=f"item-{operation}",
                    operation=operation,
                    adapter_key="xhs",
                    target_type=target_type,
                    target_ref=target_ref,
                    dedup_key=f"dedup:{operation}",
                )

                self.assertTrue(stable.runtime_delivery)
                self.assertEqual(validate_batch_target_item(item), item)

    def test_batch_runtime_consumes_cursor_comment_runtime_slice(self) -> None:
        stable = stable_operation_entry(
            operation="comment_collection",
            target_type="content",
            collection_mode="paginated",
        )
        cursor = {
            "reply_cursor": {
                "reply_cursor_token": "reply-cursor-1",
                "reply_cursor_family": "opaque",
                "resume_target_ref": "content:alpha",
                "resume_comment_ref": "comment:root-1",
                "issued_at": "2026-05-09T10:00:00Z",
            }
        }
        item = BatchTargetItem(
            item_id="comments",
            operation=stable.operation,
            adapter_key=TEST_ADAPTER_KEY,
            target_type=stable.target_type,
            target_ref="content:alpha",
            dedup_key="dedup:comments",
            request_cursor=cursor,
        )
        adapter = CursorCommentAdapter()

        with mock.patch.dict("syvert.runtime.RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE", {}, clear=True):
            result = execute_batch_request(
                BatchRequest(
                    batch_id="batch-comments",
                    target_set=(item,),
                    dataset_sink_ref="sink:reference",
                    audit_context={"evidence_ref": "evidence:batch"},
                ),
                adapters={TEST_ADAPTER_KEY: adapter},
                dataset_sink=ReferenceDatasetSink(),
                task_id_factory=lambda: "task-comment-batch",
                now_factory=lambda: datetime(2026, 5, 16, 10, 0, 0, tzinfo=timezone.utc),
            )

        self.assertEqual(adapter.request_cursors, [cursor])
        self.assertEqual(result.result_status, "complete")
        self.assertEqual(result.item_outcomes[0].operation, "comment_collection")
        self.assertEqual(result.item_outcomes[0].request_cursor_context, cursor)
        self.assertEqual(result.item_outcomes[0].dataset_record_ref, "dataset:batch-comments:comments")

    def test_batch_target_item_rejects_provider_compatibility_as_operation(self) -> None:
        with self.assertRaises(BatchDatasetContractError):
            validate_batch_target_item(
                BatchTargetItem(
                    item_id="item-provider",
                    operation="provider_compatibility_decision",
                    adapter_key="xhs",
                    target_type="content",
                    target_ref="content-001",
                    dedup_key="dedup:provider",
                )
            )

    def test_compatibility_consumers_do_not_accept_dataset_normalized_payload(self) -> None:
        private_dataset_payload = {
            "dataset_record": {
                "normalized_payload": {
                    "private_creator": "creator-private",
                    "provider_route": "provider:fallback:marketplace",
                }
            }
        }

        requirement = copy_requirement()
        requirement.update(private_dataset_payload)
        self.assertEqual(
            validate_adapter_capability_requirement(requirement).status,
            ADAPTER_REQUIREMENT_STATUS_INVALID,
        )

        offer = copy_offer()
        offer.update(private_dataset_payload)
        self.assertEqual(validate_provider_capability_offer(offer).status, PROVIDER_OFFER_STATUS_INVALID)

        decision_input = copy_decision_input()
        decision_input.update(private_dataset_payload)
        decision = decide_adapter_provider_compatibility(decision_input)
        self.assertEqual(decision.decision_status, COMPATIBILITY_DECISION_STATUS_INVALID_CONTRACT)
        self.assertEqual(decision.matched_profiles, ())

    def test_adapter_requirement_rejects_proposed_taxonomy_candidate(self) -> None:
        requirement = copy_requirement()
        requirement["capability"] = "content_search"
        requirement["execution_requirement"] = {
            "operation": "content_search",
            "target_type": "query",
            "collection_mode": "paginated",
        }
        requirement["observability"]["requirement_id"] = "xhs:content_search:content_search:query:paginated"

        result = validate_adapter_capability_requirement(requirement)

        self.assertEqual(result.status, ADAPTER_REQUIREMENT_STATUS_INVALID)
        self.assertEqual(result.capability, "content_search")

    def test_provider_offer_rejects_proposed_taxonomy_candidate(self) -> None:
        offer = copy_offer()
        offer["capability_offer"] = {
            "capability": "content_search",
            "operation": "content_search",
            "target_type": "query",
            "collection_mode": "paginated",
        }
        offer["observability"]["capability"] = "content_search"
        offer["observability"]["operation"] = "content_search"
        offer["observability"]["offer_id"] = "xhs:native_xhs_detail:content_search:content_search:query:paginated:v0.8.0"

        result = validate_provider_capability_offer(offer)

        self.assertEqual(result.status, PROVIDER_OFFER_STATUS_INVALID)
        self.assertEqual(result.capability, "content_search")

    def test_compatibility_decision_does_not_match_proposed_taxonomy_candidate(self) -> None:
        input_value = copy_decision_input()
        input_value["requirement"]["capability"] = "content_search"
        input_value["requirement"]["execution_requirement"] = {
            "operation": "content_search",
            "target_type": "query",
            "collection_mode": "paginated",
        }
        input_value["requirement"]["observability"]["requirement_id"] = "xhs:content_search:content_search:query:paginated"
        input_value["offer"]["capability_offer"] = {
            "capability": "content_search",
            "operation": "content_search",
            "target_type": "query",
            "collection_mode": "paginated",
        }
        input_value["offer"]["observability"]["capability"] = "content_search"
        input_value["offer"]["observability"]["operation"] = "content_search"
        input_value["offer"]["observability"]["offer_id"] = (
            "xhs:native_xhs_detail:content_search:content_search:query:paginated:v0.8.0"
        )

        decision = decide_adapter_provider_compatibility(input_value)

        self.assertEqual(decision.decision_status, COMPATIBILITY_DECISION_STATUS_INVALID_CONTRACT)
        self.assertEqual(decision.matched_profiles, ())


if __name__ == "__main__":
    unittest.main()
