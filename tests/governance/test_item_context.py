from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.item_context import (
    INPUT_MODE_BOOTSTRAP,
    INPUT_MODE_FORMAL_SPEC,
    INPUT_MODE_UNBOUND,
    classify_exec_plan_input_mode,
    normalize_bound_spec_dir,
    validate_bound_decision_contract,
)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class ItemContextTests(unittest.TestCase):
    def test_classify_exec_plan_input_mode(self) -> None:
        self.assertEqual(
            classify_exec_plan_input_mode({"item_type": "GOV", "关联 spec": "docs/specs/FR-0001-example/"}),
            INPUT_MODE_FORMAL_SPEC,
        )
        self.assertEqual(
            classify_exec_plan_input_mode({"item_type": "GOV"}),
            INPUT_MODE_BOOTSTRAP,
        )
        self.assertEqual(
            classify_exec_plan_input_mode({"item_type": "FR"}),
            INPUT_MODE_UNBOUND,
        )
        self.assertEqual(
            classify_exec_plan_input_mode({"item_type": "GOV", "关联 spec": "无（治理文档事项）"}),
            INPUT_MODE_BOOTSTRAP,
        )

    def test_normalize_bound_spec_dir_accepts_directory_and_legacy_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            suite_dir = repo / "docs" / "specs" / "FR-0001-example"
            write_file(suite_dir / "spec.md", "# spec\n")
            write_file(suite_dir / "plan.md", "# plan\n")

            self.assertEqual(
                normalize_bound_spec_dir(repo, "docs/specs/FR-0001-example/"),
                suite_dir.resolve(),
            )
            self.assertEqual(
                normalize_bound_spec_dir(repo, "docs/specs/FR-0001-example/spec.md"),
                suite_dir.resolve(),
            )
            self.assertIsNone(normalize_bound_spec_dir(repo, "docs/specs/_template/"))

    def test_validate_bound_decision_contract_checks_issue_and_item_key_consistency(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            decision = repo / "docs" / "decisions" / "ADR-GOV-0001-example.md"
            write_file(
                decision,
                """# ADR-GOV-0001

- Issue：`#1`
- item_key：`GOV-0001-example`
""",
            )
            payload = {
                "Issue": "1",
                "item_key": "GOV-0001-example",
                "关联 decision": "docs/decisions/ADR-GOV-0001-example.md",
            }
            self.assertEqual(validate_bound_decision_contract(repo, payload, require_present=True), [])

            mismatched = dict(payload)
            mismatched["Issue"] = "2"
            errors = validate_bound_decision_contract(repo, mismatched, require_present=True)
            self.assertTrue(any("Issue" in error and "不一致" in error for error in errors))

    def test_bootstrap_decision_contract_requires_current_item_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            decision = repo / "docs" / "decisions" / "ADR-GOV-0001-example.md"
            write_file(decision, "# ADR-GOV-0001\n")
            payload = {
                "Issue": "1",
                "item_key": "GOV-0001-example",
                "关联 decision": "docs/decisions/ADR-GOV-0001-example.md",
            }
            errors = validate_bound_decision_contract(repo, payload, require_present=True)
        self.assertTrue(any("缺少 `Issue`" in error for error in errors))
        self.assertTrue(any("缺少 `item_key`" in error for error in errors))

    def test_validate_bound_decision_contract_requires_docs_decisions_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_file(repo / "docs" / "exec-plans" / "GOV-0001-example.md", "# exec-plan\n")
            payload = {
                "Issue": "1",
                "item_key": "GOV-0001-example",
                "关联 decision": "docs/exec-plans/GOV-0001-example.md",
            }
            errors = validate_bound_decision_contract(repo, payload, require_present=True)
        self.assertTrue(any("docs/decisions/*.md" in error for error in errors))

    def test_validate_bound_decision_contract_rejects_duplicate_metadata_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            decision = repo / "docs" / "decisions" / "ADR-GOV-0001-example.md"
            write_file(
                decision,
                """# ADR-GOV-0001

- Issue：`#1`
- Issue：`#2`
- item_key：`GOV-0001-example`
""",
            )
            payload = {
                "Issue": "1",
                "item_key": "GOV-0001-example",
                "关联 decision": "docs/decisions/ADR-GOV-0001-example.md",
            }
            errors = validate_bound_decision_contract(repo, payload, require_present=True)
        self.assertTrue(any("重复键" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
