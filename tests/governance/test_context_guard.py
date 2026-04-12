from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

from unittest.mock import patch

from scripts.context_guard import infer_current_issue, main as context_guard_main, validate_context_rules, validate_repository


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_valid_template_docs(repo: Path, *, include_todo: bool = False) -> None:
    write_file(
        repo / "docs" / "exec-plans" / "_template.md",
        """# ITEM-KEY 执行计划

## 关联信息

- item_key：
- Issue：
- item_type：
- release：
- sprint：

## 最近一次 checkpoint 对应的 head SHA
""",
    )
    write_file(
        repo / "docs" / "specs" / "_template" / "spec.md",
        """# FR-XXXX 标题

## 关联信息

- item_key：
- Issue：
- item_type：
- release：
- sprint：
""",
    )
    write_file(
        repo / "docs" / "specs" / "_template" / "plan.md",
        """# FR-XXXX 实施计划

## 关联信息

- item_key：
- Issue：
- item_type：
- release：
- sprint：
""",
    )
    if include_todo:
        write_file(
            repo / "docs" / "specs" / "_template" / "TODO.md",
            """# FR-XXXX TODO

## 关联信息

- item_key：
- Issue：
- item_type：
- release：
- sprint：
- exec_plan：
""",
        )
    write_file(
        repo / "docs" / "releases" / "_template.md",
        """# Release vX.Y.Z

## 目标

- x

## 明确不在范围

- x

## 目标判据

- x

## 纳入事项

- x

## 关联工件

- roadmap：`docs/roadmap-v0-to-v1.md`
- sprint：`docs/sprints/2026-S13.md`
- spec：`docs/specs/FR-0001-example/`
- exec-plan：
  - `docs/exec-plans/GOV-0001-release-sprint-structure.md`
- decision：`docs/decisions/ADR-0001-example.md`
""",
    )
    write_file(
        repo / "docs" / "sprints" / "_template.md",
        """# Sprint YYYY-SNN

## release

- `v0.1.0`

## 本轮目标

- x

## 入口事项

- x

## 目标判据

- x

## 协作入口

- GitHub Project / iteration：x

## 关联工件

- release：`docs/releases/v0.1.0.md`
- spec：`docs/specs/FR-0001-example/`
- exec-plan：
  - `docs/exec-plans/GOV-0001-release-sprint-structure.md`
- decision：`docs/decisions/ADR-0001-example.md`
""",
    )


def write_valid_governance_docs(repo: Path, *, include_spec_todo: bool = False, include_template_todo: bool = False) -> None:
    write_file(
        repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md",
        """# GOV-0001 执行计划

## 关联信息

- item_key：`GOV-0001-release-sprint-structure`
- Issue：`#1`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 spec：`docs/specs/FR-0001-example/`
- 关联 decision：`docs/decisions/ADR-0001-example.md`

## 最近一次 checkpoint 对应的 head SHA

- `1234567890abcdef1234567890abcdef12345678`
""",
    )
    write_file(
        repo / "docs" / "specs" / "FR-0001-example" / "spec.md",
        """# FR-0001 Example

## 关联信息

- item_key：`FR-0001-example`
- Issue：`#2`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S13`

## 背景与目标

- 背景：x
- 目标：x

## 范围

- 本次纳入：x
- 本次不纳入：x

## 需求说明

- 功能需求：x
- 契约需求：x
- 非功能需求：x

## 约束

- 阶段约束：x
- 架构约束：x

## GWT 验收场景

### 场景 1

Given
When
Then

## 异常与边界场景

- 异常场景：x
- 边界场景：x

## 验收标准

- [ ] x
""",
    )
    write_file(
        repo / "docs" / "specs" / "FR-0001-example" / "contracts" / "README.md",
        "# contracts\n",
    )
    write_file(
        repo / "docs" / "specs" / "FR-0001-example" / "plan.md",
        """# FR-0001 Plan

## 关联信息

- item_key：`FR-0001-example`
- Issue：`#2`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 exec-plan：`docs/exec-plans/GOV-0001-release-sprint-structure.md`

## 实施目标

- x

## 分阶段拆分

- x

## 实现约束

- x

## 测试与验证策略

- x

## TDD 范围

- x

## 并行 / 串行关系

- x

## 进入实现前条件

- [ ] x
""",
    )
    if include_spec_todo:
        write_file(
            repo / "docs" / "specs" / "FR-0001-example" / "TODO.md",
            """# FR-0001 TODO

## 关联信息

- item_key：`FR-0001-example`
- Issue：`#2`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S13`
- exec_plan：`docs/exec-plans/GOV-0001-release-sprint-structure.md`
""",
        )
    write_file(
        repo / "docs" / "decisions" / "ADR-0001-example.md",
        """# ADR-0001

- Issue：`#1`
- item_key：`GOV-0001-release-sprint-structure`
""",
    )
    write_file(
        repo / "docs" / "releases" / "v0.1.0.md",
        """# Release v0.1.0

## 目标

- x

## 明确不在范围

- x

## 目标判据

- x

## 纳入事项

- `GOV-0001-release-sprint-structure`

## 相关前提

- x

## 关联工件

- roadmap：`docs/roadmap-v0-to-v1.md`
- sprint：`docs/sprints/2026-S13.md`
- spec：`docs/specs/FR-0001-example/`
- exec-plan：
  - `docs/exec-plans/GOV-0001-release-sprint-structure.md`
- decision：`docs/decisions/ADR-0001-example.md`
""",
    )
    write_file(
        repo / "docs" / "sprints" / "2026-S13.md",
        """# Sprint 2026-S13

## release

- `v0.1.0`

## 本轮目标

- x

## 入口事项

- `GOV-0001-release-sprint-structure`

## 进入前依赖

- x

## 目标判据

- x

## 协作入口

- GitHub Project / iteration：x
- 相关 Issue / PR：x

## 关联工件

- release：`docs/releases/v0.1.0.md`
- spec：`docs/specs/FR-0001-example/`
- exec-plan：
  - `docs/exec-plans/GOV-0001-release-sprint-structure.md`
- decision：`docs/decisions/ADR-0001-example.md`
""",
    )
    write_file(repo / "docs" / "roadmap-v0-to-v1.md", "# roadmap\n")
    write_valid_template_docs(repo, include_todo=include_template_todo)


class ContextGuardTests(unittest.TestCase):
    def test_valid_context_docs_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            errors = validate_repository(repo)
        self.assertEqual(errors, [])

    def test_new_formal_spec_without_todo_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            errors = validate_repository(repo)
        self.assertEqual(errors, [])

    def test_diff_mode_allows_touched_bound_formal_spec_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-0001-example/spec.md"],
            )
        self.assertEqual(errors, [])

    def test_invalid_item_key_format_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            text = plan.read_text(encoding="utf-8").replace(
                "GOV-0001-release-sprint-structure",
                "GOV-01-bad",
                1,
            )
            plan.write_text(text, encoding="utf-8")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0001-release-sprint-structure.md"],
            )
        self.assertTrue(any("item_key" in error for error in errors))

    def test_exec_plan_missing_required_fields_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            text = plan.read_text(encoding="utf-8")
            text = text.replace("- sprint：`2026-S13`\n", "")
            text = text.replace("## 最近一次 checkpoint 对应的 head SHA", "## checkpoint")
            plan.write_text(text, encoding="utf-8")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0001-release-sprint-structure.md"],
            )
        self.assertTrue(any("sprint" in error or "checkpoint" in error for error in errors))

    def test_formal_spec_missing_full_context_fields_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            spec = repo / "docs" / "specs" / "FR-0001-example" / "spec.md"
            text = spec.read_text(encoding="utf-8").replace("- item_type：`FR`\n", "")
            spec.write_text(text, encoding="utf-8")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-0001-example/spec.md"],
            )
        self.assertTrue(any("item_type" in error for error in errors))

    def test_release_sprint_missing_structure_or_broken_ref_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            release = repo / "docs" / "releases" / "v0.1.0.md"
            release.write_text("# Release v0.1.0\n\n## 目标\n\n- x\n", encoding="utf-8")
            sprint = repo / "docs" / "sprints" / "2026-S13.md"
            text = sprint.read_text(encoding="utf-8").replace(
                "docs/specs/FR-0001-example/",
                "docs/specs/FR-9999-missing/",
            )
            sprint.write_text(text, encoding="utf-8")
            errors = validate_repository(repo)
        self.assertTrue(any("release" in error or "sprint" in error or "不存在" in error for error in errors))

    def test_repository_mode_ignores_legacy_exec_plan_and_fr_spec_instances(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            write_file(
                repo / "docs" / "exec-plans" / "legacy.md",
                "# legacy\n\n- note：old format\n",
            )
            write_file(
                repo / "docs" / "specs" / "FR-0999-legacy" / "spec.md",
                "# legacy spec\n",
            )
            write_file(
                repo / "docs" / "specs" / "FR-0999-legacy" / "plan.md",
                "# legacy plan\n",
            )
            errors = validate_repository(repo)
        self.assertEqual(errors, [])

    def test_repository_mode_missing_required_template_should_fail(self) -> None:
        required_templates = (
            "docs/exec-plans/_template.md",
            "docs/specs/_template/spec.md",
            "docs/specs/_template/plan.md",
            "docs/releases/_template.md",
            "docs/sprints/_template.md",
        )
        for template_path in required_templates:
            with self.subTest(template=template_path):
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo = Path(temp_dir)
                    write_valid_governance_docs(repo)
                    (repo / template_path).unlink()
                    errors = validate_repository(repo)
                self.assertTrue(
                    any("缺少基线模板工件" in error and template_path in error for error in errors),
                    f"expected missing-template error for {template_path}, got: {errors}",
                )

    def test_legacy_todo_is_still_validated_when_touched(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            todo = repo / "docs" / "specs" / "FR-0001-example" / "TODO.md"
            todo.write_text("# FR-0001 TODO\n", encoding="utf-8")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-0001-example/TODO.md"],
            )
        self.assertTrue(any("退出正式治理流" in error for error in errors))

    def test_legacy_todo_is_still_validated_when_sibling_spec_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            todo = repo / "docs" / "specs" / "FR-0001-example" / "TODO.md"
            todo.write_text("# FR-0001 TODO\n", encoding="utf-8")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-0001-example/spec.md"],
            )
        self.assertEqual(errors, [])

    def test_deleted_legacy_todo_is_rejected_in_diff_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            todo = repo / "docs" / "specs" / "FR-0001-example" / "TODO.md"
            todo.write_text("# legacy todo\n", encoding="utf-8")
            todo.unlink()
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-0001-example/TODO.md"],
            )
        self.assertEqual(errors, [])

    def test_existing_legacy_template_todo_is_validated_in_repository_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            template_todo = repo / "docs" / "specs" / "_template" / "TODO.md"
            template_todo.write_text("# FR-XXXX TODO\n", encoding="utf-8")
            errors = validate_repository(repo)
        self.assertTrue(any(str(template_todo) in error and "退出正式治理流" in error for error in errors))

    def test_bootstrap_exec_plan_missing_bound_decision_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            plan.write_text(
                plan.read_text(encoding="utf-8").replace("- 关联 spec：`docs/specs/FR-0001-example/`\n", ""),
                encoding="utf-8",
            )
            decision = repo / "docs" / "decisions" / "ADR-0001-example.md"
            decision.unlink()
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0001-release-sprint-structure.md"],
            )
        self.assertTrue(any("`关联 decision`" in error and "不存在" in error for error in errors))

    def test_non_governance_exec_plan_changes_do_not_require_decision_docs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            for item_type, item_key in (
                ("FR", "FR-0001-example"),
                ("HOTFIX", "HOTFIX-0001-example"),
                ("CHORE", "CHORE-0001-example"),
            ):
                write_file(
                    repo / "docs" / "exec-plans" / f"{item_key}.md",
                    "\n".join(
                        [
                            f"# {item_key}",
                            "",
                            "## 关联信息",
                            "",
                            f"- item_key：`{item_key}`",
                            "- Issue：`#1`",
                            f"- item_type：`{item_type}`",
                            "- release：`v0.1.0`",
                            "- sprint：`2026-S13`",
                            "",
                            "## 最近一次 checkpoint 对应的 head SHA",
                            "",
                            "- `0123456789abcdef0123456789abcdef01234567`",
                            "",
                        ]
                    ),
                )
                errors = validate_context_rules(
                    repo,
                    changed_paths=[f"docs/exec-plans/{item_key}.md"],
                )
                self.assertEqual(errors, [], f"{item_type} exec-plan should not require bootstrap decision docs: {errors}")

    def test_governance_decision_without_bound_exec_plan_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            exec_plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            exec_plan.unlink()
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0001-example.md"],
            )
        self.assertTrue(any("未被任何 exec-plan" in error for error in errors))

    def test_infer_current_issue_accepts_common_git_ref_forms(self) -> None:
        self.assertEqual(infer_current_issue("issue-57-demo"), 57)
        self.assertEqual(infer_current_issue("refs/heads/issue-57-demo"), 57)
        self.assertEqual(infer_current_issue("origin/issue-57-demo"), 57)
        self.assertIsNone(infer_current_issue("refs/pull/60/head"))

    @patch("scripts.context_guard.validate_context_rules", return_value=[])
    @patch("scripts.context_guard.git_changed_files", return_value=["docs/exec-plans/GOV-0001-release-sprint-structure.md"])
    @patch("scripts.context_guard.git_current_branch", return_value="HEAD")
    def test_context_guard_main_rejects_diff_mode_without_issue_context(
        self,
        current_branch_mock,
        changed_files_mock,
        validate_context_rules_mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            stderr = StringIO()
            with redirect_stderr(stderr):
                exit_code = context_guard_main([
                    "--repo-root",
                    temp_dir,
                    "--base-ref",
                    "origin/main",
                    "--head-ref",
                    "refs/pull/60/head",
                ])
        self.assertEqual(exit_code, 1)
        self.assertIn("无法从 `--current-issue` / `--head-ref` / 当前分支推断当前事项", stderr.getvalue())
        changed_files_mock.assert_called_once()
        current_branch_mock.assert_called_once()
        validate_context_rules_mock.assert_not_called()

    def test_bootstrap_contract_touched_related_decision_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0001-example.md"],
            )
        self.assertEqual(errors, [])

    def test_touched_decision_linked_from_formal_spec_exec_plan_without_decision_metadata_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            decision = repo / "docs" / "decisions" / "ADR-0001-example.md"
            decision.write_text("# ADR-0001\n", encoding="utf-8")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0001-example.md"],
            )
        self.assertTrue(any("缺少 `Issue`" in error for error in errors))

    def test_touched_decision_linked_from_formal_spec_fr_exec_plan_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            exec_plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            exec_plan.write_text(
                exec_plan.read_text(encoding="utf-8").replace(
                    "- item_key：`GOV-0001-release-sprint-structure`\n- Issue：`#1`\n- item_type：`GOV`",
                    "- item_key：`FR-0001-example`\n- Issue：`#2`\n- item_type：`FR`",
                ),
                encoding="utf-8",
            )
            renamed_plan = repo / "docs" / "exec-plans" / "FR-0001-example.md"
            exec_plan.rename(renamed_plan)
            decision = repo / "docs" / "decisions" / "ADR-0001-example.md"
            decision.write_text(
                """# ADR-0001

- Issue：`#2`
- item_key：`FR-0001-example`
""",
                encoding="utf-8",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0001-example.md"],
                current_issue=2,
            )
        self.assertEqual(errors, [])

    def test_bootstrap_contract_touched_unrelated_decision_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            write_file(repo / "docs" / "decisions" / "ADR-GOV-9999-unrelated.md", "# ADR-GOV-9999\n")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-GOV-9999-unrelated.md"],
            )
        self.assertTrue(any("未被任何 exec-plan" in error for error in errors))

    def test_touched_typed_fr_decision_passes_with_current_exec_plan_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            (repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md").unlink()
            write_file(
                repo / "docs" / "exec-plans" / "FR-0001-example.md",
                """# FR-0001

## 关联信息

- item_key：`FR-0001-example`
- Issue：`#2`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 spec：`docs/specs/FR-0001-example/`
- 关联 decision：`docs/decisions/ADR-FR-0001-example.md`
- active 收口事项：`FR-0001-example`

## 最近一次 checkpoint 对应的 head SHA

- `1234567890abcdef1234567890abcdef12345678`
""",
            )
            write_file(
                repo / "docs" / "decisions" / "ADR-FR-0001-example.md",
                """# ADR-FR-0001

- Issue：`#2`
- item_key：`FR-0001-example`
""",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-FR-0001-example.md"],
                current_issue=2,
            )
        self.assertEqual(errors, [])

    def test_touched_typed_hotfix_decision_without_binding_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            write_file(repo / "docs" / "decisions" / "ADR-HOTFIX-0001-example.md", "# ADR-HOTFIX-0001\n")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-HOTFIX-0001-example.md"],
            )
        self.assertTrue(any("未被任何 exec-plan" in error for error in errors))

    def test_touched_typed_chore_decision_without_binding_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            write_file(repo / "docs" / "decisions" / "ADR-CHORE-0001-example.md", "# ADR-CHORE-0001\n")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-CHORE-0001-example.md"],
            )
        self.assertTrue(any("未被任何 exec-plan" in error for error in errors))

    def test_bootstrap_contract_touched_current_decision_with_only_legacy_exec_plan_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            (repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md").unlink()
            write_file(
                repo / "docs" / "exec-plans" / "GOV-0999-legacy.md",
                """# GOV-0999 legacy

## 关联信息

- item_key：`GOV-0999-legacy`
- Issue：`#999`
- item_type：`GOV`
- release：`v0.0.0`
- sprint：`2026-S01`
- 关联 decision：`docs/decisions/ADR-9999-legacy.md`

## 最近一次 checkpoint 对应的 head SHA

- `0123456789abcdef0123456789abcdef01234567`
""",
            )
            write_file(repo / "docs" / "decisions" / "ADR-9999-legacy.md", "# ADR-9999 legacy\n")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0001-example.md"],
            )
        self.assertTrue(any("未被任何 exec-plan" in error for error in errors))

    def test_touched_governance_decision_rejects_inactive_or_stale_exec_plan_bindings(self) -> None:
        scenarios = {
            "inactive": lambda text: text.replace(
                "- 关联 decision：`docs/decisions/ADR-0001-example.md`\n",
                "- 关联 decision：`docs/decisions/ADR-0001-example.md`\n- 状态：`inactive for PR #18`\n",
            ),
            "active_item_mismatch": lambda text: text.replace(
                "- 关联 decision：`docs/decisions/ADR-0001-example.md`\n",
                "- 关联 decision：`docs/decisions/ADR-0001-example.md`\n- active 收口事项：`GOV-9999-other`\n",
            ),
            "duplicate_release": lambda text: text.replace(
                "- release：`v0.1.0`\n",
                "- release：`v0.1.0`\n- release：`v0.2.0`\n",
            ),
        }
        for label, mutate in scenarios.items():
            with self.subTest(case=label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo = Path(temp_dir)
                    write_valid_governance_docs(repo)
                    plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
                    plan.write_text(mutate(plan.read_text(encoding="utf-8")), encoding="utf-8")
                    errors = validate_context_rules(
                        repo,
                        changed_paths=["docs/decisions/ADR-0001-example.md"],
                    )
                self.assertTrue(any("未被任何 exec-plan" in error for error in errors))

    def test_bootstrap_contract_requires_related_decision_for_touched_exec_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            text = plan.read_text(encoding="utf-8")
            text = text.replace(
                "docs/decisions/ADR-0001-example.md",
                "docs/decisions/ADR-9999-unrelated.md",
            )
            plan.write_text(text, encoding="utf-8")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0001-release-sprint-structure.md"],
            )
        self.assertTrue(any("关联 decision" in error for error in errors))

    def test_bootstrap_contract_touched_decision_issue_mismatch_with_exec_plan_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            decision = repo / "docs" / "decisions" / "ADR-0001-example.md"
            decision.write_text(
                """# ADR-0001

- Issue：`#999`
- item_key：`GOV-0001-release-sprint-structure`
""",
                encoding="utf-8",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0001-example.md"],
            )
        self.assertTrue(any("Issue" in error and "不一致" in error for error in errors))

    def test_bootstrap_contract_touched_exec_plan_issue_mismatch_with_decision_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            decision = repo / "docs" / "decisions" / "ADR-0001-example.md"
            decision.write_text(
                """# ADR-0001

- Issue：`#999`
- item_key：`GOV-0001-release-sprint-structure`
""",
                encoding="utf-8",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0001-release-sprint-structure.md"],
            )
        self.assertTrue(any("Issue" in error and "不一致" in error for error in errors))

    def test_bootstrap_contract_touched_exec_plan_item_key_mismatch_with_decision_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            decision = repo / "docs" / "decisions" / "ADR-0001-example.md"
            decision.write_text(
                """# ADR-0001

- Issue：`#1`
- item_key：`GOV-9999-unrelated`
""",
                encoding="utf-8",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0001-release-sprint-structure.md"],
            )
        self.assertTrue(any("item_key" in error and "不一致" in error for error in errors))

    def test_bootstrap_contract_touched_decision_with_only_weak_legacy_exec_plan_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            (repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md").unlink()
            write_file(
                repo / "docs" / "exec-plans" / "legacy.md",
                """# legacy

关联 decision: docs/decisions/ADR-0001-example.md
""",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0001-example.md"],
            )
        self.assertTrue(any("未被任何 exec-plan" in error for error in errors))

    def test_bootstrap_contract_weak_exec_plan_missing_context_fields_cannot_bind_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            (repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md").unlink()
            write_file(
                repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md",
                """# weak exec-plan

- 关联 decision：`docs/decisions/ADR-0001-example.md`
""",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0001-example.md"],
            )
        self.assertTrue(any("未被任何 exec-plan" in error for error in errors))

    def test_bootstrap_contract_non_item_key_exec_plan_filename_can_bind_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            (repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md").unlink()
            write_file(
                repo / "docs" / "exec-plans" / "legacy-binding.md",
                """# legacy binding

## 关联信息

- item_key：`GOV-0001-release-sprint-structure`
- Issue：`#1`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 decision：`docs/decisions/ADR-0001-example.md`

## 最近一次 checkpoint 对应的 head SHA

- `0123456789abcdef0123456789abcdef01234567`
""",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0001-example.md"],
            )
        self.assertEqual(errors, [])

    def test_context_guard_main_rejects_head_sha_only_without_explicit_issue_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            stderr = StringIO()
            with patch("scripts.context_guard.git_changed_files", return_value=["docs/specs/FR-0001-example/spec.md"]):
                with patch("scripts.context_guard.git_current_branch", return_value="issue-57-demo"):
                    with patch("scripts.context_guard.validate_context_rules", return_value=[]):
                        with redirect_stderr(stderr):
                            exit_code = context_guard_main([
                                "--repo-root",
                                temp_dir,
                                "--base-ref",
                                "origin/main",
                                "--head-sha",
                                "deadbeef",
                            ])
        self.assertEqual(exit_code, 1)
        self.assertIn("无法从 `--current-issue` / `--head-ref` / 当前分支推断当前事项", stderr.getvalue())

    def test_invalid_related_decision_cannot_authorize_touched_formal_spec_for_current_issue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            write_file(
                repo / "docs" / "decisions" / "ADR-0001-example.md",
                """# ADR-0001

```md
- Issue：`#1`
- item_key：`GOV-0001-release-sprint-structure`
```
""",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-0001-example/spec.md"],
                current_issue=1,
            )
        self.assertTrue(any("关联 decision" in error and "缺少 `Issue`" in error for error in errors))
        self.assertTrue(any("未被任何 active exec-plan 绑定" in error for error in errors))


    def test_invalid_active_exec_plan_binding_cannot_authorize_touched_formal_spec_for_current_issue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            plan.write_text(
                plan.read_text(encoding="utf-8").replace(
                    "- item_key：`GOV-0001-release-sprint-structure`\n- Issue：`#1`\n- item_type：`GOV`",
                    "- item_key：`invalid-item-key`\n- Issue：`#1`\n- item_type：`GOV`",
                ).replace(
                    "- 关联 decision：`docs/decisions/ADR-0001-example.md`",
                    "- 关联 decision：`docs/decisions/ADR-0001-invalid.md`",
                ).replace(
                    "- active 收口事项：`GOV-0001-release-sprint-structure`",
                    "- active 收口事项：`invalid-item-key`",
                ),
                encoding="utf-8",
            )
            write_file(
                repo / "docs" / "decisions" / "ADR-0001-invalid.md",
                """# ADR-0001 invalid

- Issue：`#1`
- item_key：`invalid-item-key`
""",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-0001-example/spec.md"],
                current_issue=1,
            )
        self.assertTrue(any("未被任何 active exec-plan 绑定" in error for error in errors))

    def test_invalid_related_spec_cannot_authorize_touched_decision_for_current_issue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            plan.write_text(
                plan.read_text(encoding="utf-8").replace(
                    "docs/specs/FR-0001-example/",
                    "docs/specs/FR-9999-missing/",
                ),
                encoding="utf-8",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0001-example.md"],
                current_issue=1,
            )
        self.assertTrue(any("关联 spec" in error and "不存在" in error for error in errors))
        self.assertTrue(any("未被任何 exec-plan" in error for error in errors))

    def test_fenced_exec_plan_metadata_cannot_authorize_touched_formal_spec(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            write_file(
                repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md",
                """# fenced exec-plan

## 关联信息

```md
- item_key：`GOV-0001-release-sprint-structure`
- Issue：`#1`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 spec：`docs/specs/FR-0001-example/`
- 关联 decision：`docs/decisions/ADR-0001-example.md`
- active 收口事项：`GOV-0001-release-sprint-structure`
```

## 最近一次 checkpoint 对应的 head SHA

- `1234567890abcdef1234567890abcdef12345678`
""",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-0001-example/spec.md"],
                current_issue=1,
            )
        self.assertTrue(any("缺少 active `exec-plan`" in error for error in errors))
        self.assertTrue(any("未被任何 active exec-plan 绑定" in error for error in errors))

    def test_fenced_formal_spec_metadata_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            spec = repo / "docs" / "specs" / "FR-0001-example" / "spec.md"
            spec.write_text(
                """# FR-0001 Example

## 关联信息

```md
- item_key：`FR-0001-example`
- Issue：`#2`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S13`
```

## 背景与目标

- 背景：x
- 目标：x

## 范围

- 本次纳入：x
- 本次不纳入：x

## 需求说明

- 功能需求：x
- 契约需求：x
- 非功能需求：x

## 约束

- 阶段约束：x
- 架构约束：x

## GWT 验收场景

### 场景 1

Given
When
Then

## 异常与边界场景

- 异常场景：x
- 边界场景：x

## 验收标准

- [ ] x
""",
                encoding="utf-8",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-0001-example/spec.md"],
                current_issue=1,
            )
        self.assertTrue(any("缺少 `Issue` 字段" in error for error in errors))
        self.assertTrue(any("缺少 `item_key` 字段" in error for error in errors))

    def test_touched_exec_plan_allows_legacy_metadata_free_adr_for_formal_spec_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            (repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md").unlink()
            write_file(
                repo / "docs" / "exec-plans" / "FR-0001-example.md",
                """# FR-0001 exec-plan

## 关联信息

- item_key：`FR-0001-example`
- Issue：`#1`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 spec：`docs/specs/FR-0001-example/`
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- active 收口事项：`FR-0001-example`

## 最近一次 checkpoint 对应的 head SHA

- `1234567890abcdef1234567890abcdef12345678`
""",
            )
            write_file(
                repo / "docs" / "decisions" / "ADR-0001-governance-bootstrap-contract.md",
                "# ADR-0001 bootstrap\n",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/FR-0001-example.md"],
                current_issue=1,
            )
        self.assertEqual(errors, [])

    def test_touched_decision_allows_legacy_metadata_free_adr_for_formal_spec_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            (repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md").unlink()
            write_file(
                repo / "docs" / "exec-plans" / "FR-0001-example.md",
                """# FR-0001 exec-plan

## 关联信息

- item_key：`FR-0001-example`
- Issue：`#1`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 spec：`docs/specs/FR-0001-example/`
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- active 收口事项：`FR-0001-example`

## 最近一次 checkpoint 对应的 head SHA

- `1234567890abcdef1234567890abcdef12345678`
""",
            )
            write_file(
                repo / "docs" / "decisions" / "ADR-0001-governance-bootstrap-contract.md",
                "# ADR-0001 bootstrap\n",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0001-governance-bootstrap-contract.md"],
                current_issue=1,
            )
        self.assertEqual(errors, [])


    def test_touched_decision_rejects_fake_legacy_adr_name_for_formal_spec_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            (repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md").unlink()
            write_file(
                repo / "docs" / "exec-plans" / "FR-0001-example.md",
                """# FR-0001 exec-plan

## 关联信息

- item_key：`FR-0001-example`
- Issue：`#1`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 spec：`docs/specs/FR-0001-example/`
- 关联 decision：`docs/decisions/ADR-0001-fake-bootstrap.md`
- active 收口事项：`FR-0001-example`

## 最近一次 checkpoint 对应的 head SHA

- `1234567890abcdef1234567890abcdef12345678`
""",
            )
            write_file(
                repo / "docs" / "decisions" / "ADR-0001-fake-bootstrap.md",
                "# ADR-0001 fake\n",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0001-fake-bootstrap.md"],
                current_issue=1,
            )
        self.assertTrue(any("缺少 `Issue` 字段" in error for error in errors))
        self.assertTrue(any("未被任何 exec-plan" in error for error in errors))

    def test_touched_decision_rejects_non_reviewable_bound_spec_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            spec = repo / "docs" / "specs" / "FR-0001-example" / "spec.md"
            spec.write_text("# FR-0001 Example\n", encoding="utf-8")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0001-example.md"],
                current_issue=1,
            )
        self.assertTrue(any("不可审查" in error for error in errors))
        self.assertTrue(any("未被任何 exec-plan" in error for error in errors))

    def test_touched_formal_spec_rejects_non_reviewable_bound_spec_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            spec = repo / "docs" / "specs" / "FR-0001-example" / "spec.md"
            spec.write_text("# FR-0001 Example\n", encoding="utf-8")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-0001-example/spec.md"],
                current_issue=1,
            )
        self.assertTrue(any("不可审查" in error for error in errors))
        self.assertTrue(any("未被任何 active exec-plan 绑定" in error for error in errors))

    def test_touched_spec_todo_is_rejected_after_legacy_flow_removal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            (repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md").unlink()
            write_file(
                repo / "docs" / "exec-plans" / "FR-0001-example.md",
                """# FR-0001 exec-plan

## 关联信息

- item_key：`FR-0001-example`
- Issue：`#1`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 spec：`docs/specs/FR-0001-example/`
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- active 收口事项：`FR-0001-example`

## 最近一次 checkpoint 对应的 head SHA

- `1234567890abcdef1234567890abcdef12345678`
""",
            )
            write_file(
                repo / "docs" / "decisions" / "ADR-0001-governance-bootstrap-contract.md",
                "# ADR-0001 bootstrap\n",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-0001-example/TODO.md"],
                current_issue=1,
            )
        self.assertEqual(errors, [])

    def test_touched_formal_spec_rejects_fake_legacy_adr_name_for_current_issue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            (repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md").unlink()
            write_file(
                repo / "docs" / "exec-plans" / "FR-0001-example.md",
                """# FR-0001 exec-plan

## 关联信息

- item_key：`FR-0001-example`
- Issue：`#1`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 spec：`docs/specs/FR-0001-example/`
- 关联 decision：`docs/decisions/ADR-0001-fake-bootstrap.md`
- active 收口事项：`FR-0001-example`

## 最近一次 checkpoint 对应的 head SHA

- `1234567890abcdef1234567890abcdef12345678`
""",
            )
            write_file(
                repo / "docs" / "decisions" / "ADR-0001-fake-bootstrap.md",
                "# ADR-0001 fake\n",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-0001-example/spec.md"],
                current_issue=1,
            )
        self.assertTrue(any("缺少 `Issue` 字段" in error for error in errors))
        self.assertTrue(any("未被任何 active exec-plan 绑定" in error for error in errors))

    def test_unbound_fr_authorization_requires_complete_reviewable_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            exec_plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            exec_plan.write_text(
                exec_plan.read_text(encoding="utf-8").replace(
                    "- item_key：`GOV-0001-release-sprint-structure`\n- Issue：`#1`\n- item_type：`GOV`",
                    "- item_key：`FR-0001-example`\n- Issue：`#1`\n- item_type：`FR`",
                ).replace(
                    "- 关联 spec：`docs/specs/FR-0001-example/`\n",
                    "",
                ).replace(
                    "- 关联 decision：`docs/decisions/ADR-0001-example.md`\n",
                    "",
                ).replace(
                    "- active 收口事项：`GOV-0001-release-sprint-structure`",
                    "- active 收口事项：`FR-0001-example`",
                ),
                encoding="utf-8",
            )
            exec_plan.rename(repo / "docs" / "exec-plans" / "FR-0001-example.md")
            (repo / "docs" / "specs" / "FR-0001-example" / "plan.md").unlink()
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-0001-example/spec.md"],
                current_issue=1,
            )
        self.assertTrue(any("未被任何 active exec-plan 绑定" in error for error in errors))

    def test_valid_governance_exec_plan_with_related_decision_passes_diff_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0001-release-sprint-structure.md"],
            )
        self.assertEqual(errors, [])

    def test_formal_spec_exec_plan_rejects_unrelated_touched_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            write_file(
                repo / "docs" / "specs" / "FR-9999-unrelated" / "spec.md",
                (repo / "docs" / "specs" / "FR-0001-example" / "spec.md").read_text(encoding="utf-8"),
            )
            write_file(
                repo / "docs" / "specs" / "FR-9999-unrelated" / "plan.md",
                (repo / "docs" / "specs" / "FR-0001-example" / "plan.md").read_text(encoding="utf-8").replace(
                    "FR-0001-example",
                    "FR-9999-unrelated",
                ),
            )
            plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            plan.write_text(
                plan.read_text(encoding="utf-8").replace(
                    "docs/specs/FR-0001-example/",
                    "docs/specs/FR-9999-unrelated/",
                ),
                encoding="utf-8",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=[
                    "docs/exec-plans/GOV-0001-release-sprint-structure.md",
                    "docs/specs/FR-0001-example/spec.md",
                ],
            )
        self.assertTrue(any("formal spec 套件" in error or "关联 spec" in error for error in errors))

    def test_formal_spec_exec_plan_accepts_its_own_touched_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            errors = validate_context_rules(
                repo,
                changed_paths=[
                    "docs/exec-plans/GOV-0001-release-sprint-structure.md",
                    "docs/specs/FR-0001-example/spec.md",
                ],
            )
        self.assertEqual(errors, [])

    def test_formal_spec_exec_plan_accepts_gov_0029_delete_only_legacy_todo_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            example_spec = (repo / "docs" / "specs" / "FR-0001-example" / "spec.md").read_text(encoding="utf-8")
            example_plan = (repo / "docs" / "specs" / "FR-0001-example" / "plan.md").read_text(encoding="utf-8")
            for suite_name, issue in (
                ("FR-0003-github-delivery-structure-and-repo-semantic-split", "#55"),
                ("FR-0002-content-detail-runtime-v0-1", "#38"),
            ):
                write_file(
                    repo / "docs" / "specs" / suite_name / "spec.md",
                    example_spec.replace("FR-0001-example", suite_name).replace("Issue：`#2`", f"Issue：`{issue}`"),
                )
                write_file(
                    repo / "docs" / "specs" / suite_name / "plan.md",
                    example_plan.replace("FR-0001-example", suite_name)
                    .replace("Issue：`#2`", f"Issue：`{issue}`")
                    .replace(
                        "docs/exec-plans/GOV-0001-release-sprint-structure.md",
                        "docs/exec-plans/GOV-0029-remove-legacy-todo-md.md",
                    ),
                )
                write_file(repo / "docs" / "specs" / suite_name / "contracts" / "README.md", "# contracts\n")
            todo = repo / "docs" / "specs" / "FR-0002-content-detail-runtime-v0-1" / "TODO.md"
            write_file(todo, "# TODO\n")
            write_file(
                repo / "docs" / "decisions" / "ADR-GOV-0029-remove-legacy-todo-md.md",
                """# ADR-GOV-0029

- Issue：`#58`
- item_key：`GOV-0029-remove-legacy-todo-md`
""",
            )
            write_file(
                repo / "docs" / "exec-plans" / "GOV-0029-remove-legacy-todo-md.md",
                """# GOV-0029

## 关联信息

- item_key：`GOV-0029-remove-legacy-todo-md`
- Issue：`#58`
- item_type：`GOV`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/`
- 额外关联 specs：docs/specs/FR-0002-content-detail-runtime-v0-1/
- 关联 decision：`docs/decisions/ADR-GOV-0029-remove-legacy-todo-md.md`
- active 收口事项：`GOV-0029-remove-legacy-todo-md`

## 最近一次 checkpoint 对应的 head SHA

- `1234567890abcdef1234567890abcdef12345678`
""",
            )
            todo.unlink()
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-0002-content-detail-runtime-v0-1/TODO.md"],
                current_issue=58,
            )
        self.assertEqual(errors, [])

    def test_formal_spec_exec_plan_rejects_non_delete_change_in_additional_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            example_spec = (repo / "docs" / "specs" / "FR-0001-example" / "spec.md").read_text(encoding="utf-8")
            example_plan = (repo / "docs" / "specs" / "FR-0001-example" / "plan.md").read_text(encoding="utf-8")
            for suite_name, issue in (
                ("FR-0003-github-delivery-structure-and-repo-semantic-split", "#55"),
                ("FR-0002-content-detail-runtime-v0-1", "#38"),
            ):
                write_file(
                    repo / "docs" / "specs" / suite_name / "spec.md",
                    example_spec.replace("FR-0001-example", suite_name).replace("Issue：`#2`", f"Issue：`{issue}`"),
                )
                write_file(
                    repo / "docs" / "specs" / suite_name / "plan.md",
                    example_plan.replace("FR-0001-example", suite_name)
                    .replace("Issue：`#2`", f"Issue：`{issue}`")
                    .replace(
                        "docs/exec-plans/GOV-0001-release-sprint-structure.md",
                        "docs/exec-plans/GOV-0029-remove-legacy-todo-md.md",
                    ),
                )
                write_file(repo / "docs" / "specs" / suite_name / "contracts" / "README.md", "# contracts\n")
            write_file(
                repo / "docs" / "decisions" / "ADR-GOV-0029-remove-legacy-todo-md.md",
                """# ADR-GOV-0029

- Issue：`#58`
- item_key：`GOV-0029-remove-legacy-todo-md`
""",
            )
            write_file(
                repo / "docs" / "exec-plans" / "GOV-0029-remove-legacy-todo-md.md",
                """# GOV-0029

## 关联信息

- item_key：`GOV-0029-remove-legacy-todo-md`
- Issue：`#58`
- item_type：`GOV`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/`
- 额外关联 specs：docs/specs/FR-0002-content-detail-runtime-v0-1/
- 关联 decision：`docs/decisions/ADR-GOV-0029-remove-legacy-todo-md.md`
- active 收口事项：`GOV-0029-remove-legacy-todo-md`

## 最近一次 checkpoint 对应的 head SHA

- `1234567890abcdef1234567890abcdef12345678`
""",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-0002-content-detail-runtime-v0-1/spec.md"],
                current_issue=58,
            )
        self.assertTrue(any("必须在当前 diff 中删除" in error for error in errors))

    def test_exec_plan_rejects_invalid_additional_spec_binding_even_without_touched_spec(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            example_spec = (repo / "docs" / "specs" / "FR-0001-example" / "spec.md").read_text(encoding="utf-8")
            example_plan = (repo / "docs" / "specs" / "FR-0001-example" / "plan.md").read_text(encoding="utf-8")
            write_file(
                repo / "docs" / "specs" / "FR-0003-github-delivery-structure-and-repo-semantic-split" / "spec.md",
                example_spec.replace("FR-0001-example", "FR-0003-github-delivery-structure-and-repo-semantic-split").replace("Issue：`#2`", "Issue：`#55`"),
            )
            write_file(
                repo / "docs" / "specs" / "FR-0003-github-delivery-structure-and-repo-semantic-split" / "plan.md",
                example_plan.replace("FR-0001-example", "FR-0003-github-delivery-structure-and-repo-semantic-split")
                .replace("Issue：`#2`", "Issue：`#55`")
                .replace(
                    "docs/exec-plans/GOV-0001-release-sprint-structure.md",
                    "docs/exec-plans/GOV-0029-remove-legacy-todo-md.md",
                ),
            )
            write_file(
                repo / "docs" / "specs" / "FR-0003-github-delivery-structure-and-repo-semantic-split" / "contracts" / "README.md",
                "# contracts\n",
            )
            write_file(
                repo / "docs" / "decisions" / "ADR-GOV-0029-remove-legacy-todo-md.md",
                """# ADR-GOV-0029

- Issue：`#58`
- item_key：`GOV-0029-remove-legacy-todo-md`
""",
            )
            write_file(
                repo / "docs" / "exec-plans" / "GOV-0029-remove-legacy-todo-md.md",
                """# GOV-0029

## 关联信息

- item_key：`GOV-0029-remove-legacy-todo-md`
- Issue：`#58`
- item_type：`GOV`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/`
- 额外关联 specs：`docs/specs/_template/`
- 关联 decision：`docs/decisions/ADR-GOV-0029-remove-legacy-todo-md.md`
- active 收口事项：`GOV-0029-remove-legacy-todo-md`

## 最近一次 checkpoint 对应的 head SHA

- `1234567890abcdef1234567890abcdef12345678`
""",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0029-remove-legacy-todo-md.md"],
                current_issue=58,
            )
        self.assertTrue(any("额外关联 specs" in error for error in errors))

    def test_non_governance_exec_plan_rejects_additional_spec_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            exec_plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            exec_plan.write_text(
                exec_plan.read_text(encoding="utf-8").replace(
                    "- item_key：`GOV-0001-release-sprint-structure`\n- Issue：`#1`\n- item_type：`GOV`",
                    "- item_key：`FR-0001-example`\n- Issue：`#2`\n- item_type：`FR`",
                ).replace(
                    "- active 收口事项：`GOV-0001-release-sprint-structure`",
                    "- active 收口事项：`FR-0001-example`",
                ).replace(
                    "- 关联 spec：`docs/specs/FR-0001-example/`\n",
                    "- 关联 spec：`docs/specs/FR-0001-example/`\n- 额外关联 specs：`docs/specs/FR-9999-unrelated/`\n",
                ),
                encoding="utf-8",
            )
            exec_plan.rename(repo / "docs" / "exec-plans" / "FR-0001-example.md")
            write_file(
                repo / "docs" / "specs" / "FR-9999-unrelated" / "spec.md",
                (repo / "docs" / "specs" / "FR-0001-example" / "spec.md").read_text(encoding="utf-8").replace(
                    "FR-0001-example",
                    "FR-9999-unrelated",
                ).replace(
                    "Issue：`#2`",
                    "Issue：`#9999`",
                ),
            )
            write_file(
                repo / "docs" / "specs" / "FR-9999-unrelated" / "plan.md",
                (repo / "docs" / "specs" / "FR-0001-example" / "plan.md").read_text(encoding="utf-8").replace(
                    "FR-0001-example",
                    "FR-9999-unrelated",
                ).replace(
                    "Issue：`#2`",
                    "Issue：`#9999`",
                ),
            )
            write_file(repo / "docs" / "specs" / "FR-9999-unrelated" / "contracts" / "README.md", "# contracts\n")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/FR-0001-example.md"],
                current_issue=2,
            )
        self.assertTrue(any("额外关联 specs" in error for error in errors))

    def test_formal_spec_spec_only_smuggling_without_matching_active_exec_plan_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            write_file(
                repo / "docs" / "specs" / "FR-9999-unrelated" / "spec.md",
                (repo / "docs" / "specs" / "FR-0001-example" / "spec.md").read_text(encoding="utf-8").replace(
                    "FR-0001-example",
                    "FR-9999-unrelated",
                ),
            )
            write_file(
                repo / "docs" / "specs" / "FR-9999-unrelated" / "plan.md",
                (repo / "docs" / "specs" / "FR-0001-example" / "plan.md").read_text(encoding="utf-8").replace(
                    "FR-0001-example",
                    "FR-9999-unrelated",
                ),
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-9999-unrelated/spec.md"],
            )
        self.assertTrue(any("未被任何 active exec-plan 绑定" in error for error in errors))

    def test_formal_spec_diff_is_scoped_to_current_issue_instead_of_repo_wide_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            write_file(
                repo / "docs" / "exec-plans" / "GOV-0002-other.md",
                """# GOV-0002

## 关联信息

- item_key：`GOV-0002-other`
- Issue：`#2`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 spec：`docs/specs/FR-9999-unrelated/`
- 关联 decision：`docs/decisions/ADR-0002-example.md`
- active 收口事项：`GOV-0002-other`

## 最近一次 checkpoint 对应的 head SHA

- `1234567890abcdef1234567890abcdef12345678`
""",
            )
            write_file(
                repo / "docs" / "decisions" / "ADR-0002-example.md",
                """# ADR-0002

- Issue：`#2`
- item_key：`GOV-0002-other`
""",
            )
            write_file(
                repo / "docs" / "specs" / "FR-9999-unrelated" / "spec.md",
                (repo / "docs" / "specs" / "FR-0001-example" / "spec.md").read_text(encoding="utf-8").replace(
                    "FR-0001-example",
                    "FR-9999-unrelated",
                ),
            )
            write_file(
                repo / "docs" / "specs" / "FR-9999-unrelated" / "plan.md",
                (repo / "docs" / "specs" / "FR-0001-example" / "plan.md").read_text(encoding="utf-8").replace(
                    "FR-0001-example",
                    "FR-9999-unrelated",
                ),
            )
            write_file(repo / "docs" / "specs" / "FR-9999-unrelated" / "TODO.md", "# TODO\n")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-9999-unrelated/spec.md"],
                current_issue=1,
            )
        self.assertTrue(any("未被任何 active exec-plan 绑定" in error for error in errors))

    def test_touched_exec_plan_is_scoped_to_current_issue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            write_file(
                repo / "docs" / "exec-plans" / "GOV-0002-other.md",
                """# GOV-0002

## 关联信息

- item_key：`GOV-0002-other`
- Issue：`#2`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 decision：`docs/decisions/ADR-0002-example.md`
- active 收口事项：`GOV-0002-other`

## 最近一次 checkpoint 对应的 head SHA

- `1234567890abcdef1234567890abcdef12345678`
""",
            )
            write_file(
                repo / "docs" / "decisions" / "ADR-0002-example.md",
                """# ADR-0002

- Issue：`#2`
- item_key：`GOV-0002-other`
""",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0002-other.md"],
                current_issue=1,
            )
        self.assertTrue(any("当前执行回合 `#1` 不一致" in error for error in errors))

    def test_touched_inactive_cross_issue_exec_plan_is_allowed_for_retirement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            write_file(
                repo / "docs" / "exec-plans" / "GOV-0002-other.md",
                """# GOV-0002

## 关联信息

- item_key：`GOV-0002-other`
- Issue：`#2`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 spec：`docs/specs/FR-0001-example/`
- 状态：`inactive after PR #18 merge`
- active 收口事项：`GOV-0002-other`

## 最近一次 checkpoint 对应的 head SHA

- `1234567890abcdef1234567890abcdef12345678`
""",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0002-other.md"],
                current_issue=1,
            )
        self.assertEqual(errors, [])

    def test_touched_decision_is_scoped_to_current_issue_instead_of_repo_wide_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            write_file(
                repo / "docs" / "exec-plans" / "GOV-0002-other.md",
                """# GOV-0002

## 关联信息

- item_key：`GOV-0002-other`
- Issue：`#2`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 decision：`docs/decisions/ADR-0002-example.md`
- active 收口事项：`GOV-0002-other`

## 最近一次 checkpoint 对应的 head SHA

- `1234567890abcdef1234567890abcdef12345678`
""",
            )
            write_file(
                repo / "docs" / "decisions" / "ADR-0002-example.md",
                """# ADR-0002

- Issue：`#2`
- item_key：`GOV-0002-other`
""",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0002-example.md"],
                current_issue=1,
            )
        self.assertTrue(any("未被任何 exec-plan" in error for error in errors))

    def test_multiple_active_exec_plans_for_current_issue_reject_foreign_formal_spec_auth(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            write_file(
                repo / "docs" / "exec-plans" / "GOV-0002-other.md",
                """# GOV-0002

## 关联信息

- item_key：`GOV-0002-other`
- Issue：`#1`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 spec：`docs/specs/FR-9999-unrelated/`
- 关联 decision：`docs/decisions/ADR-0002-example.md`
- active 收口事项：`GOV-0002-other`

## 最近一次 checkpoint 对应的 head SHA

- `1234567890abcdef1234567890abcdef12345678`
""",
            )
            write_file(
                repo / "docs" / "decisions" / "ADR-0002-example.md",
                """# ADR-0002

- Issue：`#1`
- item_key：`GOV-0002-other`
""",
            )
            write_file(
                repo / "docs" / "specs" / "FR-9999-unrelated" / "spec.md",
                (repo / "docs" / "specs" / "FR-0001-example" / "spec.md").read_text(encoding="utf-8").replace(
                    "FR-0001-example",
                    "FR-9999-unrelated",
                ),
            )
            write_file(
                repo / "docs" / "specs" / "FR-9999-unrelated" / "plan.md",
                (repo / "docs" / "specs" / "FR-0001-example" / "plan.md").read_text(encoding="utf-8").replace(
                    "FR-0001-example",
                    "FR-9999-unrelated",
                ),
            )
            write_file(repo / "docs" / "specs" / "FR-9999-unrelated" / "TODO.md", "# TODO\n")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-9999-unrelated/spec.md"],
                current_issue=1,
            )
        self.assertTrue(any("多个 active `exec-plan`" in error for error in errors))

    def test_multiple_active_exec_plans_for_current_issue_reject_decision_auth(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            write_file(
                repo / "docs" / "exec-plans" / "GOV-0002-other.md",
                """# GOV-0002

## 关联信息

- item_key：`GOV-0002-other`
- Issue：`#1`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S13`
- 关联 spec：`docs/specs/FR-9999-unrelated/`
- 关联 decision：`docs/decisions/ADR-0002-example.md`
- active 收口事项：`GOV-0002-other`

## 最近一次 checkpoint 对应的 head SHA

- `1234567890abcdef1234567890abcdef12345678`
""",
            )
            write_file(
                repo / "docs" / "decisions" / "ADR-0002-example.md",
                """# ADR-0002

- Issue：`#1`
- item_key：`GOV-0002-other`
""",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0001-example.md"],
                current_issue=1,
            )
        self.assertTrue(any("多个 active `exec-plan`" in error for error in errors))

    def test_touched_exec_plan_rejects_non_reviewable_bound_spec_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            spec = repo / "docs" / "specs" / "FR-0001-example" / "spec.md"
            spec.write_text("# FR-0001 Example\n", encoding="utf-8")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0001-release-sprint-structure.md"],
            )
        self.assertTrue(any("不可审查" in error for error in errors))

    def test_valid_governance_bootstrap_exec_plan_with_related_decision_passes_diff_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            plan.write_text(
                plan.read_text(encoding="utf-8").replace("- 关联 spec：`docs/specs/FR-0001-example/`\n", ""),
                encoding="utf-8",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0001-release-sprint-structure.md"],
            )
        self.assertEqual(errors, [])

    def test_legacy_placeholder_related_spec_still_takes_bootstrap_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            plan.write_text(
                plan.read_text(encoding="utf-8").replace(
                    "- 关联 spec：`docs/specs/FR-0001-example/`\n",
                    "- 关联 spec：`无（治理文档事项）`\n",
                ),
                encoding="utf-8",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0001-release-sprint-structure.md"],
            )
        self.assertEqual(errors, [])

    def test_touched_exec_plan_rejects_missing_related_spec_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            exec_plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            exec_plan.write_text(
                exec_plan.read_text(encoding="utf-8").replace(
                    "docs/specs/FR-0001-example/",
                    "docs/specs/FR-9999-missing/",
                ),
                encoding="utf-8",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0001-release-sprint-structure.md"],
            )
        self.assertTrue(any("`关联 spec` 指向的路径不存在" in error for error in errors))

    def test_touched_exec_plan_rejects_out_of_repo_related_spec(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            exec_plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            exec_plan.write_text(
                exec_plan.read_text(encoding="utf-8").replace(
                    "docs/specs/FR-0001-example/",
                    "../outside-spec/",
                ),
                encoding="utf-8",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0001-release-sprint-structure.md"],
            )
        self.assertTrue(any("仓库外路径" in error for error in errors))

    def test_touched_exec_plan_accepts_legacy_related_spec_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            exec_plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            exec_plan.write_text(
                exec_plan.read_text(encoding="utf-8").replace(
                    "docs/specs/FR-0001-example/",
                    "docs/specs/FR-0001-example/spec.md",
                ),
                encoding="utf-8",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0001-release-sprint-structure.md"],
            )
        self.assertEqual(errors, [])

    def test_touched_exec_plan_rejects_template_related_spec(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            exec_plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            exec_plan.write_text(
                exec_plan.read_text(encoding="utf-8").replace(
                    "docs/specs/FR-0001-example/",
                    "docs/specs/_template/",
                ),
                encoding="utf-8",
            )
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0001-release-sprint-structure.md"],
            )
        self.assertTrue(any("FR formal spec 套件根目录" in error for error in errors))

    def test_diff_mode_deleted_governance_doc_returns_error_instead_of_crash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            try:
                errors = validate_context_rules(repo, changed_paths=["docs/releases/v0.1.0.md"])
            except FileNotFoundError as exc:
                self.fail(f"validate_context_rules should not raise FileNotFoundError: {exc}")
        self.assertEqual(len(errors), 1)
        self.assertIn("docs/releases/v0.1.0.md", errors[0])
        self.assertIn("变更目标不存在（可能已删除）", errors[0])


if __name__ == "__main__":
    unittest.main()
