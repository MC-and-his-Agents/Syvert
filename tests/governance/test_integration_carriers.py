from __future__ import annotations

import re
import unittest

from scripts.common import REPO_ROOT
from scripts.integration_contract import ISSUE_SCOPE_FIELDS, PR_SCOPE_FIELDS, render_contract_reference_lines


class IntegrationCarrierTests(unittest.TestCase):
    def test_pr_template_exposes_pr_scope_fields_in_contract_order(self) -> None:
        body = (REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
        for line in render_contract_reference_lines():
            self.assertIn(line, body)

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
            positions = []
            for field in ISSUE_SCOPE_FIELDS:
                marker = f"id: {field}"
                index = body.find(marker)
                self.assertGreaterEqual(index, 0, msg=f"{name} missing {field}")
                positions.append(index)
            self.assertEqual(positions, sorted(positions), msg=f"{name} issue carrier order drifted from canonical contract")

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


if __name__ == "__main__":
    unittest.main()
