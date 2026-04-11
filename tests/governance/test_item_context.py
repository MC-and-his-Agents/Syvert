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
    parse_exec_plan_metadata,
    validate_bound_decision_contract,
    validate_bound_formal_spec_scope,
    validate_bound_spec_contract,
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

    def test_validate_bound_decision_contract_ignores_metadata_inside_fenced_code_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            decision = repo / "docs" / "decisions" / "ADR-GOV-0001-example.md"
            write_file(
                decision,
                """# ADR-GOV-0001

```md
- Issue：`#1`
- item_key：`GOV-0001-example`
```
""",
            )
            payload = {
                "Issue": "1",
                "item_key": "GOV-0001-example",
                "关联 decision": "docs/decisions/ADR-GOV-0001-example.md",
            }
            errors = validate_bound_decision_contract(repo, payload, require_present=True)
        self.assertTrue(any("缺少 `Issue`" in error for error in errors))
        self.assertTrue(any("缺少 `item_key`" in error for error in errors))

    def test_parse_exec_plan_metadata_ignores_metadata_inside_fenced_code_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            exec_plan = repo / "docs" / "exec-plans" / "GOV-0001-example.md"
            write_file(
                exec_plan,
                """# exec-plan

## 关联信息

```md
- item_key：`GOV-0001-example`
- Issue：`#1`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S14`
- 关联 spec：`docs/specs/FR-0001-example/`
```
""",
            )
            payload = parse_exec_plan_metadata(exec_plan)
        self.assertEqual(payload, {"exec_plan": exec_plan.as_posix()})

    def test_validate_bound_spec_contract_rejects_nested_subdirectory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            suite_dir = repo / "docs" / "specs" / "FR-0001-example"
            write_file(suite_dir / "spec.md", "# spec\n")
            write_file(suite_dir / "plan.md", "# plan\n")
            shadow_dir = suite_dir / "shadow"
            write_file(shadow_dir / "spec.md", "# shadow spec\n")
            write_file(shadow_dir / "plan.md", "# shadow plan\n")
            errors = validate_bound_spec_contract(
                repo,
                {"关联 spec": "docs/specs/FR-0001-example/shadow/"},
            )
        self.assertTrue(any("FR formal spec 套件根目录" in error for error in errors))

    def test_validate_bound_formal_spec_scope_accepts_authorized_additional_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            first = repo / "docs" / "specs" / "FR-0001-example"
            second = repo / "docs" / "specs" / "FR-0002-example"
            write_file(first / "spec.md", "# spec\n")
            write_file(first / "plan.md", "# plan\n")
            write_file(second / "spec.md", "# spec\n")
            write_file(second / "plan.md", "# plan\n")
            errors = validate_bound_formal_spec_scope(
                repo,
                {
                    "关联 spec": "docs/specs/FR-0001-example/",
                    "额外关联 specs": "docs/specs/FR-0002-example/",
                },
                [
                    "docs/specs/FR-0001-example/spec.md",
                    "docs/specs/FR-0002-example/spec.md",
                ],
            )
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
