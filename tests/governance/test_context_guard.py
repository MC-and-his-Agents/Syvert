from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.context_guard import validate_context_rules, validate_repository


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_valid_governance_docs(repo: Path) -> None:
    write_file(
        repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md",
        """# GOV-0001 执行计划

## 关联信息

- item_key：`GOV-0001-release-sprint-structure`
- Issue：`#1`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S13`
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
        "# ADR-0001\n",
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


class ContextGuardTests(unittest.TestCase):
    def test_valid_context_docs_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            errors = validate_repository(repo)
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

    def test_bootstrap_contract_requires_decision_when_exec_plan_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            decision = repo / "docs" / "decisions" / "ADR-0001-example.md"
            decision.unlink()
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0001-release-sprint-structure.md"],
            )
        self.assertTrue(any("decision" in error.lower() or "decisions" in error.lower() for error in errors))

    def test_bootstrap_contract_requires_exec_plan_when_decision_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            exec_plan = repo / "docs" / "exec-plans" / "GOV-0001-release-sprint-structure.md"
            exec_plan.unlink()
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/decisions/ADR-0001-example.md"],
            )
        self.assertTrue(any("exec-plan" in error.lower() or "exec-plans" in error.lower() for error in errors))

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

    def test_valid_governance_exec_plan_with_related_decision_passes_diff_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_governance_docs(repo)
            errors = validate_context_rules(
                repo,
                changed_paths=["docs/exec-plans/GOV-0001-release-sprint-structure.md"],
            )
        self.assertEqual(errors, [])

    def test_diff_mode_deleted_governance_doc_returns_error_instead_of_crash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            try:
                errors = validate_context_rules(repo, changed_paths=["docs/releases/v0.1.0.md"])
            except FileNotFoundError as exc:
                self.fail(f"validate_context_rules should not raise FileNotFoundError: {exc}")
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
