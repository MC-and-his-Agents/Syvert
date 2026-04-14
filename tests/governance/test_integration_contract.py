from __future__ import annotations

import re
import unittest
from pathlib import Path

from scripts.common import REPO_ROOT, normalize_integration_ref_for_comparison
from scripts.integration_contract import (
    CONTRACT_SOURCE_MACHINE_READABLE,
    CONTRACT_SOURCE_MODULE,
    FIELD_ORDER,
    ISSUE_SCOPE_FIELDS,
    PR_SCOPE_FIELDS,
    build_review_packet,
    extract_issue_canonical_integration_fields,
    field_choices,
    markdown_section_label,
    parse_pr_integration_check,
    render_contract_reference_lines,
    render_issue_form_guidance_lines,
    render_pr_template_guidance_lines,
    validate_pr_merge_gate_payload,
)


PR_TEMPLATE_PATH = REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"
WORKFLOW_PATH = REPO_ROOT / "WORKFLOW.md"
CODE_REVIEW_PATH = REPO_ROOT / "code_review.md"
EXEC_PLAN_PATH = REPO_ROOT / "docs" / "exec-plans" / "GOV-0105-integration-governance-baseline.md"
EVIDENCE_PATH = REPO_ROOT / "docs" / "governance-rollouts" / "GOV-0105-platform-evidence.md"
ISSUE_FORM_PATHS = [
    REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "fr.yml",
    REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "governance.yml",
    REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "work-item.yml",
]


def form_block(text: str, field_id: str) -> str:
    match = re.search(rf"\n\s+id: {re.escape(field_id)}\n(?P<body>.*?)(?=\n  - type:|\Z)", text, re.S)
    if not match:
        raise AssertionError(f"未找到 issue form 字段: {field_id}")
    return match.group("body")


def dropdown_options(block: str) -> list[str]:
    options_match = re.search(r"options:\n(?P<opts>(?:\s*-\s+.+\n)+)", block)
    if not options_match:
        return []
    options: list[str] = []
    for raw_line in options_match.group("opts").splitlines():
        stripped = raw_line.strip()
        if not stripped.startswith("- "):
            continue
        options.append(stripped[2:].strip().strip('"'))
    return options


class IntegrationContractTests(unittest.TestCase):
    def test_scope_fields_follow_contract_order(self) -> None:
        self.assertEqual(ISSUE_SCOPE_FIELDS, FIELD_ORDER[: len(ISSUE_SCOPE_FIELDS)])
        self.assertEqual(PR_SCOPE_FIELDS, FIELD_ORDER)

    def test_normalize_integration_ref_for_comparison_supports_all_documented_forms(self) -> None:
        self.assertEqual(
            normalize_integration_ref_for_comparison("#12"),
            "issue:mc-and-his-agents/syvert#12",
        )
        self.assertEqual(
            normalize_integration_ref_for_comparison("MC-and-his-Agents/Syvert#12"),
            "issue:mc-and-his-agents/syvert#12",
        )
        self.assertEqual(
            normalize_integration_ref_for_comparison("https://github.com/MC-and-his-Agents/Syvert/issues/12"),
            "issue:mc-and-his-agents/syvert#12",
        )
        self.assertEqual(
            normalize_integration_ref_for_comparison(
                "https://github.com/orgs/MC-and-his-Agents/projects/3/views/1?pane=issue&itemId=PVTI_test"
            ),
            "project-item:mc-and-his-agents/3#PVTI_test",
        )
        self.assertEqual(
            normalize_integration_ref_for_comparison(
                "https://github.com/orgs/MC-and-his-Agents/projects/3?itemId=PVTI_test&pane=issue"
            ),
            "project-item:mc-and-his-agents/3#PVTI_test",
        )

    def test_extract_issue_canonical_integration_fields_uses_issue_scope_fields(self) -> None:
        body = "\n".join(
            [
                "### integration_touchpoint",
                "",
                "active",
                "",
                "### shared_contract_changed",
                "",
                "yes",
                "",
                "### integration_ref",
                "",
                "#12",
                "",
                "### external_dependency",
                "",
                "both",
                "",
                "### merge_gate",
                "",
                "integration_check_required",
                "",
                "### contract_surface",
                "",
                "runtime_modes",
                "",
                "### joint_acceptance_needed",
                "",
                "yes",
                "",
                "### integration_status_checked_before_pr",
                "",
                "yes",
            ]
        )

        payload = extract_issue_canonical_integration_fields(body)

        self.assertEqual(tuple(payload.keys()), ISSUE_SCOPE_FIELDS)
        self.assertNotIn("integration_status_checked_before_pr", payload)

    def test_parse_pr_integration_check_uses_full_pr_scope_fields(self) -> None:
        body = "\n".join(
            [
                "## integration_check",
                "",
                "- integration_touchpoint: active",
                "- shared_contract_changed: no",
                "- integration_ref: #12",
                "- external_dependency: both",
                "- merge_gate: integration_check_required",
                "- contract_surface: runtime_modes",
                "- joint_acceptance_needed: yes",
                "- integration_status_checked_before_pr: yes",
                "- integration_status_checked_before_merge: no",
            ]
        )

        payload = parse_pr_integration_check(body)

        self.assertEqual(tuple(payload.keys()), PR_SCOPE_FIELDS)

    def test_build_review_packet_surfaces_issue_and_pr_canonical_metadata(self) -> None:
        packet = build_review_packet(
            "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: active",
                    "- shared_contract_changed: no",
                    "- integration_ref: https://github.com/MC-and-his-Agents/Syvert/issues/12",
                    "- external_dependency: both",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: runtime_modes",
                    "- joint_acceptance_needed: yes",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: no",
                ]
            ),
            issue_number=105,
            issue_canonical={
                "integration_touchpoint": "active",
                "shared_contract_changed": "no",
                "integration_ref": "#12",
                "external_dependency": "both",
                "merge_gate": "integration_check_required",
                "contract_surface": "runtime_modes",
                "joint_acceptance_needed": "yes",
            },
            issue_error="",
        )

        self.assertEqual(packet["issue_number"], 105)
        self.assertIn("integration_ref", packet["issue_canonical"])
        self.assertIn("integration_ref", packet["pr_canonical"])
        self.assertEqual(packet["normalized_issue_canonical"]["integration_ref"], "issue:mc-and-his-agents/syvert#12")
        self.assertEqual(packet["normalized_pr_canonical"]["integration_ref"], "issue:mc-and-his-agents/syvert#12")
        self.assertFalse(packet["comparison_errors"])
        self.assertEqual(packet["merge_validation_errors"], [])
        self.assertTrue(packet["merge_gate_requires_recheck"])

    def test_validate_pr_merge_gate_payload_keeps_legacy_compatibility_decision_outside_payload_validation(self) -> None:
        payload = {
            "integration_touchpoint": "none",
            "shared_contract_changed": "no",
            "integration_ref": "none",
            "external_dependency": "none",
            "merge_gate": "local_only",
            "contract_surface": "none",
            "joint_acceptance_needed": "no",
            "integration_status_checked_before_pr": "no",
            "integration_status_checked_before_merge": "no",
        }

        errors = validate_pr_merge_gate_payload(
            payload,
            issue_number=None,
            issue_canonical={},
            require_merge_time_recheck=True,
        )

        self.assertEqual(errors, [])

    def test_workflow_and_code_review_reference_canonical_contract(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        review = CODE_REVIEW_PATH.read_text(encoding="utf-8")

        self.assertIn(CONTRACT_SOURCE_MACHINE_READABLE, workflow)
        self.assertIn(CONTRACT_SOURCE_MODULE, workflow)
        self.assertIn("canonical integration contract", review)
        self.assertNotIn("`none`：纯本仓库事项", workflow)

    def test_pr_template_integration_section_matches_contract(self) -> None:
        template = PR_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn(render_contract_reference_lines()[0], template)
        for field in PR_SCOPE_FIELDS:
            self.assertIn(markdown_section_label(field), template)
        for guidance in render_pr_template_guidance_lines():
            self.assertIn(guidance, template)

    def test_issue_forms_consume_contract_source_and_enum_choices(self) -> None:
        for path in ISSUE_FORM_PATHS:
            text = path.read_text(encoding="utf-8")
            self.assertIn(render_contract_reference_lines()[0], text)
            for guidance in render_issue_form_guidance_lines():
                self.assertIn(guidance, text)
            for field in ISSUE_SCOPE_FIELDS:
                block = form_block(text, field)
                choices = field_choices(field)
                if choices:
                    self.assertEqual(dropdown_options(block), list(choices))
            integration_ref_block = form_block(text, "integration_ref")
            self.assertIn("canonical contract", integration_ref_block)

    def test_exec_plan_references_evidence_instead_of_claiming_platform_rollout_as_repo_fact(self) -> None:
        text = EXEC_PLAN_PATH.read_text(encoding="utf-8")

        self.assertIn("docs/governance-rollouts/GOV-0105-platform-evidence.md", text)
        self.assertNotIn("labels 与 issue 回填层面建立联动基线", text)

    def test_platform_evidence_contains_verification_entry_points(self) -> None:
        text = EVIDENCE_PATH.read_text(encoding="utf-8")

        self.assertIn("https://github.com/orgs/MC-and-his-Agents/projects/3", text)
        self.assertIn("gh project view 3 --owner MC-and-his-Agents", text)
        self.assertIn("gh label list --repo MC-and-his-Agents/Syvert", text)
        self.assertIn("Syvert#105", text)


if __name__ == "__main__":
    unittest.main()
