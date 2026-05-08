from __future__ import annotations

import unittest

from syvert.adapter_capability_requirement import (
    ADAPTER_REQUIREMENT_STATUS_INVALID,
    APPROVED_ADAPTER_CAPABILITY,
    APPROVED_EXECUTION_REQUIREMENT,
    validate_adapter_capability_requirement,
)
from syvert.adapter_provider_compatibility_decision import (
    COMPATIBILITY_DECISION_STATUS_INVALID_CONTRACT,
    decide_adapter_provider_compatibility,
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
