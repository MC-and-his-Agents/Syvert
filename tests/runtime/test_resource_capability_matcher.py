from __future__ import annotations

import unittest
from unittest import mock

from syvert import registry
from syvert.registry import (
    AdapterResourceRequirementDeclaration,
    AdapterResourceRequirementDeclarationV2,
    AdapterResourceRequirementProfile,
    baseline_required_resource_requirement_declaration,
)
from syvert.resource_capability_evidence import (
    ApprovedSharedResourceRequirementProfileEvidenceEntry,
    ExecutionPathDescriptor,
)
from syvert.runtime import (
    MATCH_STATUS_MATCHED,
    MATCH_STATUS_UNMATCHED,
    ResourceCapabilityMatcherContractError,
    ResourceCapabilityMatcherInput,
    match_resource_capabilities,
)


class ResourceCapabilityMatcherTests(unittest.TestCase):
    @staticmethod
    def _multi_profile_declaration(adapter_key: str = "xhs") -> AdapterResourceRequirementDeclarationV2:
        return AdapterResourceRequirementDeclarationV2(
            adapter_key=adapter_key,
            capability="content_detail",
            resource_requirement_profiles=(
                AdapterResourceRequirementProfile(
                    profile_key="account_proxy",
                    resource_dependency_mode="required",
                    required_capabilities=("account", "proxy"),
                    evidence_refs=("fr-0027:profile:content-detail-by-url-hybrid:account-proxy",),
                ),
                AdapterResourceRequirementProfile(
                    profile_key="account",
                    resource_dependency_mode="required",
                    required_capabilities=("account",),
                    evidence_refs=("fr-0027:profile:content-detail-by-url-hybrid:account",),
                ),
            ),
        )

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

    def test_matcher_returns_matched_when_any_v2_profile_is_satisfied(self) -> None:
        result = match_resource_capabilities(
            ResourceCapabilityMatcherInput(
                task_id="task-match-v2-one-of",
                adapter_key="xhs",
                capability="content_detail",
                requirement_declaration=self._multi_profile_declaration(),
                available_resource_capabilities=("account",),
            )
        )

        self.assertEqual(result.match_status, MATCH_STATUS_MATCHED)

    def test_matcher_returns_unmatched_when_no_v2_profile_is_satisfied(self) -> None:
        result = match_resource_capabilities(
            ResourceCapabilityMatcherInput(
                task_id="task-match-v2-unmatched",
                adapter_key="xhs",
                capability="content_detail",
                requirement_declaration=self._multi_profile_declaration(),
                available_resource_capabilities=("proxy",),
            )
        )

        self.assertEqual(result.match_status, MATCH_STATUS_UNMATCHED)

    def test_matcher_rejects_v2_profile_without_approved_profile_proof(self) -> None:
        with self.assertRaises(ResourceCapabilityMatcherContractError) as context:
            match_resource_capabilities(
                ResourceCapabilityMatcherInput(
                    task_id="task-match-v2-unapproved-proof",
                    adapter_key="xhs",
                    capability="content_detail",
                    requirement_declaration=AdapterResourceRequirementDeclarationV2(
                        adapter_key="xhs",
                        capability="content_detail",
                        resource_requirement_profiles=(
                            AdapterResourceRequirementProfile(
                                profile_key="proxy",
                                resource_dependency_mode="required",
                                required_capabilities=("proxy",),
                                evidence_refs=("fr-0027:profile:content-detail-by-url-hybrid:proxy",),
                            ),
                        ),
                    ),
                    available_resource_capabilities=("proxy",),
                )
            )

        self.assertEqual(context.exception.code, "invalid_resource_requirement")

    def test_matcher_rejects_v2_semantically_duplicate_profiles(self) -> None:
        with self.assertRaises(ResourceCapabilityMatcherContractError) as context:
            match_resource_capabilities(
                ResourceCapabilityMatcherInput(
                    task_id="task-match-v2-duplicate-profile",
                    adapter_key="xhs",
                    capability="content_detail",
                    requirement_declaration=AdapterResourceRequirementDeclarationV2(
                        adapter_key="xhs",
                        capability="content_detail",
                        resource_requirement_profiles=(
                            AdapterResourceRequirementProfile(
                                profile_key="account-a",
                                resource_dependency_mode="required",
                                required_capabilities=("account",),
                                evidence_refs=("fr-0027:profile:content-detail-by-url-hybrid:account",),
                            ),
                            AdapterResourceRequirementProfile(
                                profile_key="account-b",
                                resource_dependency_mode="required",
                                required_capabilities=("account",),
                                evidence_refs=("fr-0027:profile:content-detail-by-url-hybrid:account",),
                            ),
                        ),
                    ),
                    available_resource_capabilities=("account",),
                )
            )

        self.assertEqual(context.exception.code, "invalid_resource_requirement")

    def test_matcher_keeps_none_profile_semantics_when_profile_has_approved_proof(self) -> None:
        approved_none_profile = ApprovedSharedResourceRequirementProfileEvidenceEntry(
            profile_ref="test:profile:none",
            capability="content_detail",
            execution_path=ExecutionPathDescriptor(
                operation="content_detail_by_url",
                target_type="url",
                collection_mode="hybrid",
            ),
            resource_dependency_mode="none",
            required_capabilities=(),
            reference_adapters=("xhs", "douyin"),
            shared_status="shared",
            decision="approve_profile_for_v0_8_0",
            evidence_refs=("test:evidence:none",),
        )

        with mock.patch.object(
            registry,
            "approved_shared_resource_requirement_profile_evidence_entries",
            return_value=(approved_none_profile,),
        ):
            result = match_resource_capabilities(
                ResourceCapabilityMatcherInput(
                    task_id="task-match-v2-none-profile",
                    adapter_key="xhs",
                    capability="content_detail",
                    requirement_declaration=AdapterResourceRequirementDeclarationV2(
                        adapter_key="xhs",
                        capability="content_detail",
                        resource_requirement_profiles=(
                            AdapterResourceRequirementProfile(
                                profile_key="none",
                                resource_dependency_mode="none",
                                required_capabilities=(),
                                evidence_refs=("test:profile:none",),
                            ),
                        ),
                    ),
                    available_resource_capabilities=(),
                )
            )

        self.assertEqual(result.match_status, MATCH_STATUS_MATCHED)

    def test_matcher_keeps_none_mode_semantics_in_pure_matcher_layer(self) -> None:
        approved_evidence_refs = baseline_required_resource_requirement_declaration(
            adapter_key="xhs",
            capability="content_detail",
        ).evidence_refs
        result = match_resource_capabilities(
            ResourceCapabilityMatcherInput(
                task_id="task-match-none",
                adapter_key="xhs",
                capability="content_detail",
                requirement_declaration=AdapterResourceRequirementDeclaration(
                    adapter_key="xhs",
                    capability="content_detail",
                    resource_dependency_mode="none",
                    required_capabilities=(),
                    evidence_refs=approved_evidence_refs,
                ),
                available_resource_capabilities=(),
            )
        )

        self.assertEqual(result.match_status, MATCH_STATUS_MATCHED)

    def test_matcher_rejects_none_mode_declaration_with_unapproved_evidence_refs(self) -> None:
        with self.assertRaises(ResourceCapabilityMatcherContractError) as context:
            match_resource_capabilities(
                ResourceCapabilityMatcherInput(
                    task_id="task-match-none-invalid-evidence",
                    adapter_key="xhs",
                    capability="content_detail",
                    requirement_declaration=AdapterResourceRequirementDeclaration(
                        adapter_key="xhs",
                        capability="content_detail",
                        resource_dependency_mode="none",
                        required_capabilities=(),
                        evidence_refs=("matcher:none-mode",),
                    ),
                    available_resource_capabilities=(),
                )
            )

        self.assertEqual(context.exception.code, "invalid_resource_requirement")

    def test_matcher_rejects_none_mode_declaration_with_wrong_adapter_evidence_provenance(self) -> None:
        wrong_provenance_refs = baseline_required_resource_requirement_declaration(
            adapter_key="douyin",
            capability="content_detail",
        ).evidence_refs

        with self.assertRaises(ResourceCapabilityMatcherContractError) as context:
            match_resource_capabilities(
                ResourceCapabilityMatcherInput(
                    task_id="task-match-none-wrong-provenance",
                    adapter_key="xhs",
                    capability="content_detail",
                    requirement_declaration=AdapterResourceRequirementDeclaration(
                        adapter_key="xhs",
                        capability="content_detail",
                        resource_dependency_mode="none",
                        required_capabilities=(),
                        evidence_refs=wrong_provenance_refs,
                    ),
                    available_resource_capabilities=(),
                )
            )

        self.assertEqual(context.exception.code, "invalid_resource_requirement")

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

    def test_matcher_rejects_required_declaration_with_noncanonical_evidence_refs(self) -> None:
        with self.assertRaises(ResourceCapabilityMatcherContractError) as context:
            match_resource_capabilities(
                ResourceCapabilityMatcherInput(
                    task_id="task-match-forged-evidence",
                    adapter_key="xhs",
                    capability="content_detail",
                    requirement_declaration=AdapterResourceRequirementDeclaration(
                        adapter_key="xhs",
                        capability="content_detail",
                        resource_dependency_mode="required",
                        required_capabilities=("account", "proxy"),
                        evidence_refs=("forged:evidence",),
                    ),
                    available_resource_capabilities=("account", "proxy"),
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

    def test_matcher_rejects_subclassed_matcher_input_carrier(self) -> None:
        class ShadowMatcherInput(ResourceCapabilityMatcherInput):
            pass

        with self.assertRaises(ResourceCapabilityMatcherContractError) as context:
            match_resource_capabilities(
                ShadowMatcherInput(
                    task_id="task-match-shadow-input-subclass",
                    adapter_key="xhs",
                    capability="content_detail",
                    requirement_declaration=baseline_required_resource_requirement_declaration(
                        adapter_key="xhs",
                        capability="content_detail",
                    ),
                    available_resource_capabilities=("account", "proxy"),
                )
            )

        self.assertEqual(context.exception.code, "invalid_resource_requirement")

    def test_matcher_rejects_subclassed_requirement_declaration_carrier(self) -> None:
        class ShadowRequirementDeclaration(AdapterResourceRequirementDeclaration):
            pass

        with self.assertRaises(ResourceCapabilityMatcherContractError) as context:
            match_resource_capabilities(
                ResourceCapabilityMatcherInput(
                    task_id="task-match-shadow-declaration-subclass",
                    adapter_key="xhs",
                    capability="content_detail",
                    requirement_declaration=ShadowRequirementDeclaration(
                        adapter_key="xhs",
                        capability="content_detail",
                        resource_dependency_mode="required",
                        required_capabilities=("account", "proxy"),
                        evidence_refs=("xhs:content_detail:account", "xhs:content_detail:proxy"),
                    ),
                    available_resource_capabilities=("account", "proxy"),
                )
            )

        self.assertEqual(context.exception.code, "invalid_resource_requirement")


if __name__ == "__main__":
    unittest.main()
