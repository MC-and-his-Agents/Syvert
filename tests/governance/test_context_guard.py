from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.context_guard import validate_context_rules, validate_repository


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_valid_template_docs(repo: Path, *, include_todo: bool = True) -> None:
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


def write_valid_governance_docs(repo: Path, *, include_spec_todo: bool = True, include_template_todo: bool = True) -> None:
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
            write_valid_governance_docs(repo, include_spec_todo=False, include_template_todo=False)
            errors = validate_repository(repo)
        self.assertEqual(errors, [])

    def test_diff_mode_allows_touched_formal_spec_without_todo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo, include_spec_todo=False, include_template_todo=False)
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
            write_file(
                repo / "docs" / "specs" / "FR-0999-legacy" / "TODO.md",
                "# legacy todo\n",
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
        self.assertTrue(any("Issue" in error for error in errors))

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
        self.assertTrue(any("Issue" in error for error in errors))

    def test_deleted_legacy_todo_is_rejected_in_diff_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            (repo / "docs" / "specs" / "FR-0001-example" / "TODO.md").unlink()
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/specs/FR-0001-example/TODO.md"],
            )
        self.assertTrue(any("变更目标不存在（可能已删除）" in error for error in errors))

    def test_existing_legacy_template_todo_is_validated_in_repository_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            template_todo = repo / "docs" / "specs" / "_template" / "TODO.md"
            template_todo.write_text("# FR-XXXX TODO\n", encoding="utf-8")
            errors = validate_repository(repo)
        self.assertTrue(any(str(template_todo) in error and "Issue" in error for error in errors))

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

    def test_bootstrap_contract_touched_related_decision_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0001-example.md"],
            )
        self.assertEqual(errors, [])

    def test_touched_decision_linked_from_formal_spec_exec_plan_without_decision_metadata_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            decision = repo / "docs" / "decisions" / "ADR-0001-example.md"
            decision.write_text("# ADR-0001\n", encoding="utf-8")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0001-example.md"],
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

    def test_bootstrap_contract_touched_fr_decision_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            write_file(repo / "docs" / "decisions" / "ADR-FR-0001-example.md", "# ADR-FR-0001\n")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-FR-0001-example.md"],
            )
        self.assertEqual(errors, [])

    def test_bootstrap_contract_touched_hotfix_decision_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            write_file(repo / "docs" / "decisions" / "ADR-HOTFIX-0001-example.md", "# ADR-HOTFIX-0001\n")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-HOTFIX-0001-example.md"],
            )
        self.assertEqual(errors, [])

    def test_bootstrap_contract_touched_chore_decision_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            write_file(repo / "docs" / "decisions" / "ADR-CHORE-0001-example.md", "# ADR-CHORE-0001\n")
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-CHORE-0001-example.md"],
            )
        self.assertEqual(errors, [])

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

    def test_bootstrap_contract_non_item_key_exec_plan_filename_cannot_bind_decision(self) -> None:
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
        self.assertTrue(any("未被任何 exec-plan" in error for error in errors))

    def test_valid_governance_exec_plan_with_related_decision_passes_diff_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0001-release-sprint-structure.md"],
            )
        self.assertEqual(errors, [])

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
        self.assertTrue(any("`关联 spec` 必须绑定到具体 FR formal spec 套件" in error for error in errors))

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
