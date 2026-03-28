from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.open_pr import validate_pr_preflight


class OpenPrPreflightTests(unittest.TestCase):
    def test_governance_without_issue_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            errors = validate_pr_preflight("governance", None, ["AGENTS.md"], repo_root=repo)
        self.assertTrue(any("必须绑定 Issue" in error for error in errors))

    def test_core_item_without_spec_or_bootstrap_contract_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            errors = validate_pr_preflight("spec", 1, ["docs/process/delivery-funnel.md"], repo_root=repo)
        self.assertTrue(any("formal spec 或 bootstrap contract" in error for error in errors))

    def test_governance_with_bootstrap_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "docs" / "decisions").mkdir(parents=True)
            (repo / "docs" / "exec-plans").mkdir(parents=True)
            (repo / "docs" / "decisions" / "ADR-0001.md").write_text("# adr\n", encoding="utf-8")
            (repo / "docs" / "exec-plans" / "v2.md").write_text("# plan\n", encoding="utf-8")
            errors = validate_pr_preflight("governance", 5, ["AGENTS.md"], repo_root=repo)
        self.assertEqual(errors, [])

    def test_spec_class_without_spec_changes_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "docs" / "decisions").mkdir(parents=True)
            (repo / "docs" / "exec-plans").mkdir(parents=True)
            (repo / "docs" / "decisions" / "ADR-0001.md").write_text("# adr\n", encoding="utf-8")
            (repo / "docs" / "exec-plans" / "v2.md").write_text("# plan\n", encoding="utf-8")
            errors = validate_pr_preflight("spec", 3, ["code_review.md"], repo_root=repo)
        self.assertTrue(any("必须包含正式规约区变更" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
