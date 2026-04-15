from __future__ import annotations

import re
import unittest

from scripts.common import REPO_ROOT
from scripts.integration_contract import (
    ISSUE_SCOPE_FIELDS,
    PR_SCOPE_FIELDS,
    extract_issue_canonical_integration_fields,
    field_choices,
    markdown_section_label,
    parse_pr_integration_check,
    render_contract_reference_lines,
    render_issue_form_guidance_lines,
    render_pr_template_guidance_lines,
)


class IntegrationCarrierTests(unittest.TestCase):
    @staticmethod
    def form_blocks(body: str) -> list[str]:
        starts = [match.start() for match in re.finditer(r"(?m)^  - type: ", body)]
        if not starts:
            return []
        starts.append(len(body))
        return [body[starts[index] : starts[index + 1]] for index in range(len(starts) - 1)]

    def block_for_id(self, body: str, field: str) -> str:
        for block in self.form_blocks(body):
            if re.search(rf"(?m)^    id: {re.escape(field)}$", block):
                return block
        self.fail(f"missing block for {field}")

    def test_pr_template_exposes_pr_scope_fields_in_contract_order(self) -> None:
        body = (REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
        for line in render_contract_reference_lines():
            self.assertIn(line, body)
        for line in render_pr_template_guidance_lines():
            self.assertIn(line, body)
        for field in PR_SCOPE_FIELDS:
            self.assertIn(markdown_section_label(field), body)
        self.assertEqual(tuple(parse_pr_integration_check(body).keys()), PR_SCOPE_FIELDS)

        positions = []
        for field in PR_SCOPE_FIELDS:
            marker = f"- {field}"
            index = body.find(marker)
            self.assertGreaterEqual(index, 0, msg=f"missing {field} in PR template")
            positions.append(index)
        self.assertEqual(positions, sorted(positions))

    def test_issue_forms_expose_issue_scope_fields(self) -> None:
        template_dir = REPO_ROOT / ".github" / "ISSUE_TEMPLATE"
        for name in ("fr.yml", "work-item.yml", "governance.yml"):
            body = (template_dir / name).read_text(encoding="utf-8")
            for line in render_contract_reference_lines():
                self.assertIn(line, body, msg=f"{name} missing canonical source line")
            for line in render_issue_form_guidance_lines():
                self.assertIn(line, body, msg=f"{name} missing guidance line")
            positions = []
            for field in ISSUE_SCOPE_FIELDS:
                block = self.block_for_id(body, field)
                index = body.find(f"id: {field}")
                positions.append(index)
                self.assertIn(f"label: {field}", block, msg=f"{name} label for {field} drifted from canonical name")
                choices = field_choices(field)
                if choices:
                    rendered = [item.strip().strip('"').strip("'") for item in re.findall(r"(?m)^        - (.+)$", block)]
                    self.assertEqual(rendered, list(choices), msg=f"{name} choices for {field} drifted from canonical contract")
            self.assertEqual(tuple(extract_issue_canonical_integration_fields(self.issue_form_sample_body(body)).keys()), ISSUE_SCOPE_FIELDS)
            self.assertEqual(positions, sorted(positions), msg=f"{name} issue carrier order drifted from canonical contract")
            for pr_only_field in ("integration_status_checked_before_pr", "integration_status_checked_before_merge"):
                self.assertNotIn(f"id: {pr_only_field}", body, msg=f"{name} should not expose PR-only carrier {pr_only_field}")

    def test_phase_form_explicitly_excludes_integration_metadata(self) -> None:
        body = (REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "phase.yml").read_text(encoding="utf-8")
        self.assertIn("不是 canonical integration metadata carrier", body)
        self.assertIn("FR / Work Item / governance issue", body)
        for field in ISSUE_SCOPE_FIELDS:
            self.assertNotRegex(body, rf"id:\s+{re.escape(field)}")

    def test_workflow_and_code_review_reference_canonical_source_without_redefining_template_choices(self) -> None:
        workflow = (REPO_ROOT / "WORKFLOW.md").read_text(encoding="utf-8")
        review = (REPO_ROOT / "code_review.md").read_text(encoding="utf-8")
        for body in (workflow, review):
            self.assertIn("canonical integration contract 的单一真相源", body)
            self.assertIn("scripts/policy/integration_contract.json", body)
            self.assertNotIn("`none` / `check_required` / `active` / `blocked` / `resolved`", body)

    def test_config_points_issue_creation_to_workflow_contract(self) -> None:
        body = (REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(encoding="utf-8")
        self.assertIn("blank_issues_enabled: false", body)
        self.assertIn("Syvert Repo Workflow Contract", body)
        self.assertIn("blob/main/WORKFLOW.md", body)

    def issue_form_sample_body(self, body: str) -> str:
        parts: list[str] = []
        for field in ISSUE_SCOPE_FIELDS:
            block = self.block_for_id(body, field)
            label_match = re.search(r"(?m)^      label: (.+)$", block)
            self.assertIsNotNone(label_match, msg=f"missing label for {field}")
            label = label_match.group(1).strip()
            choices = field_choices(field)
            if choices:
                value = choices[0]
            elif field == "integration_ref":
                value = "none"
            else:
                value = "sample"
            parts.extend([f"### {label}", "", value, ""])
        return "\n".join(parts)


if __name__ == "__main__":
    unittest.main()
