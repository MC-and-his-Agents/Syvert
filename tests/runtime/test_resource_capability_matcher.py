from __future__ import annotations

import unittest

from syvert.registry import (
    AdapterResourceRequirementDeclaration,
    baseline_required_resource_requirement_declaration,
)
from syvert.runtime import (
    MATCH_STATUS_MATCHED,
    MATCH_STATUS_UNMATCHED,
    ResourceCapabilityMatcherContractError,
    ResourceCapabilityMatcherInput,
    match_resource_capabilities,
)


class ResourceCapabilityMatcherTests(unittest.TestCase):
    def test_matcher_returns_matched_when_available_capabilities_cover_required_capabilities(self) -> None:
        result = match_resource_capabilities(
            ResourceCapabilityMatcherInput(
                task_id="task-match-1",
                adapter_key="xhs",
                capability="content_detail",
                requirement_declaration=baseline_required_resource_requirement_declaration(
                    adapter_key="xhs",
                    capability="content_detail",
                ),
                available_resource_capabilities=("account", "proxy"),
            )
        )

        self.assertEqual(result.match_status, MATCH_STATUS_MATCHED)
        self.assertEqual(
            tuple(result.__dict__.keys()),
            ("task_id", "adapter_key", "capability", "match_status"),
        )

    def test_matcher_returns_unmatched_when_available_capabilities_are_subset_of_required_capabilities(self) -> None:
        result = match_resource_capabilities(
            ResourceCapabilityMatcherInput(
                task_id="task-match-2",
                adapter_key="douyin",
                capability="content_detail",
                requirement_declaration=baseline_required_resource_requirement_declaration(
                    adapter_key="douyin",
                    capability="content_detail",
                ),
                available_resource_capabilities=("account",),
            )
        )

        self.assertEqual(result.match_status, MATCH_STATUS_UNMATCHED)

    def test_matcher_keeps_none_mode_semantics_in_pure_matcher_layer(self) -> None:
        result = match_resource_capabilities(
            ResourceCapabilityMatcherInput(
                task_id="task-match-none",
                adapter_key="stub",
                capability="content_detail",
                requirement_declaration=AdapterResourceRequirementDeclaration(
                    adapter_key="stub",
                    capability="content_detail",
                    resource_dependency_mode="none",
                    required_capabilities=(),
                    evidence_refs=("matcher:none-mode",),
                ),
                available_resource_capabilities=(),
            )
        )

        self.assertEqual(result.match_status, MATCH_STATUS_MATCHED)

    def test_matcher_rejects_context_mismatch_between_input_and_declaration(self) -> None:
        with self.assertRaises(ResourceCapabilityMatcherContractError) as context:
            match_resource_capabilities(
                ResourceCapabilityMatcherInput(
                    task_id="task-match-context-mismatch",
                    adapter_key="douyin",
                    capability="content_detail",
                    requirement_declaration=baseline_required_resource_requirement_declaration(
                        adapter_key="xhs",
                        capability="content_detail",
                    ),
                    available_resource_capabilities=("account", "proxy"),
                )
            )

        self.assertEqual(context.exception.code, "invalid_resource_requirement")

    def test_matcher_rejects_unknown_available_capability(self) -> None:
        with self.assertRaises(ResourceCapabilityMatcherContractError) as context:
            match_resource_capabilities(
                ResourceCapabilityMatcherInput(
                    task_id="task-match-unknown-capability",
                    adapter_key="xhs",
                    capability="content_detail",
                    requirement_declaration=baseline_required_resource_requirement_declaration(
                        adapter_key="xhs",
                        capability="content_detail",
                    ),
                    available_resource_capabilities=("account", "browser_state"),
                )
            )

        self.assertEqual(context.exception.code, "invalid_resource_requirement")

    def test_matcher_rejects_duplicate_available_capability(self) -> None:
        with self.assertRaises(ResourceCapabilityMatcherContractError) as context:
            match_resource_capabilities(
                ResourceCapabilityMatcherInput(
                    task_id="task-match-duplicate-capability",
                    adapter_key="xhs",
                    capability="content_detail",
                    requirement_declaration=baseline_required_resource_requirement_declaration(
                        adapter_key="xhs",
                        capability="content_detail",
                    ),
                    available_resource_capabilities=("account", "account"),
                )
            )

        self.assertEqual(context.exception.code, "invalid_resource_requirement")

    def test_matcher_rejects_shadow_requirement_declaration_carrier(self) -> None:
        with self.assertRaises(ResourceCapabilityMatcherContractError) as context:
            match_resource_capabilities(
                ResourceCapabilityMatcherInput(
                    task_id="task-match-shadow-carrier",
                    adapter_key="xhs",
                    capability="content_detail",
                    requirement_declaration={  # type: ignore[arg-type]
                        "adapter_key": "xhs",
                        "capability": "content_detail",
                        "resource_dependency_mode": "required",
                        "required_capabilities": ("account", "proxy"),
                        "evidence_refs": ("shadow:carrier",),
                    },
                    available_resource_capabilities=("account", "proxy"),
                )
            )

        self.assertEqual(context.exception.code, "invalid_resource_requirement")


if __name__ == "__main__":
    unittest.main()
