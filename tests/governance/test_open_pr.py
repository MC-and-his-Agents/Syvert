from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from unittest.mock import patch

from scripts.common import CommandError
from scripts.open_pr import build_body, build_issue_summary, parse_args, validate_current_worktree_binding, validate_pr_preflight


def write_exec_plan(
    repo: Path,
    *,
    item_key: str = "GOV-0015-item-context-gate",
    issue: str = "#19",
    item_type: str = "GOV",
    release: str = "v0.1.0",
    sprint: str = "2026-S14",
    active_item_key: str = "GOV-0015-item-context-gate",
    related_spec: str | None = None,
    related_decision: str | None = None,
) -> None:
    exec_plans = repo / "docs" / "exec-plans"
    exec_plans.mkdir(parents=True, exist_ok=True)
    (exec_plans / f"{item_key}.md").write_text(
        "\n".join(
            [
                "# plan",
                "",
                "## 关联信息",
                "",
                f"- item_key：`{item_key}`",
                f"- Issue：`{issue}`",
                f"- item_type：`{item_type}`",
                f"- release：`{release}`",
                f"- sprint：`{sprint}`",
                *( [f"- 关联 spec：`{related_spec}`"] if related_spec else [] ),
                *( [f"- 关联 decision：`{related_decision}`"] if related_decision else [] ),
                f"- active 收口事项：`{active_item_key}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_formal_spec_suite(
    repo: Path,
    *,
    suite_name: str = "FR-0001-governance-stack-v1",
    with_todo: bool = False,
) -> None:
    fr_dir = repo / "docs" / "specs" / suite_name
    fr_dir.mkdir(parents=True, exist_ok=True)
    (fr_dir / "spec.md").write_text(
        "\n".join(
            [
                "# spec",
                "",
                "## GWT 验收场景",
                "",
                "Given x",
                "When y",
                "Then z",
                "",
                "## 异常与边界场景",
                "",
                "- x",
                "",
                "## 验收标准",
                "",
                "- [ ] x",
            ]
        ),
        encoding="utf-8",
    )
    (fr_dir / "plan.md").write_text(
        "\n".join(
            [
                "# plan",
                "",
                "## 实施目标",
                "",
                "- x",
                "",
                "## 分阶段拆分",
                "",
                "- x",
                "",
                "## 实现约束",
                "",
                "- x",
                "",
                "## 测试与验证策略",
                "",
                "- x",
                "",
                "## TDD 范围",
                "",
                "- x",
                "",
                "## 并行 / 串行关系",
                "",
                "- x",
                "",
                "## 进入实现前条件",
                "",
                "- [ ] x",
            ]
        ),
        encoding="utf-8",
    )
    if with_todo:
        (fr_dir / "TODO.md").write_text("# todo\n", encoding="utf-8")


def write_decision(repo: Path, path: str, *, issue: str, item_key: str) -> None:
    decision_path = repo / path
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(
        "\n".join(
            [
                "# ADR",
                "",
                f"- Issue：`{issue}`",
                f"- item_key：`{item_key}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


class OpenPrPreflightTests(unittest.TestCase):
    def test_build_issue_summary_extracts_minimal_high_value_issue_context(self) -> None:
        payload = {
            "body": "\n".join(
                [
                    "## Goal",
                    "",
                    "- 对齐模板",
                    "",
                    "## Scope",
                    "",
                    "- 调整 open_pr 和 guardian",
                    "",
                    "## Out of Scope",
                    "",
                    "- 不改 merge_pr",
                ]
            )
        }

        with patch(
            "scripts.open_pr.run",
            return_value=type("Completed", (), {"returncode": 0, "stdout": __import__("json").dumps(payload)})(),
        ):
            summary = build_issue_summary(25)

        self.assertIn("## Goal", summary)
        self.assertIn("## Scope", summary)
        self.assertIn("## Out of Scope", summary)
    def test_legacy_filename_exec_plan_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            exec_plans = repo / "docs" / "exec-plans"
            exec_plans.mkdir(parents=True, exist_ok=True)
            (exec_plans / "governance-stack-v1.md").write_text(
                "\n".join(
                    [
                        "# plan",
                        "",
                        "## 事项上下文",
                        "",
                        "- Issue：`#6`",
                        "- item_key：`FR-0001-governance-stack-v1`",
                        "- item_type：`FR`",
                        "- release：`v0.1.0`",
                        "- sprint：`2026-S13`",
                        "- 关联 spec：`docs/specs/FR-0001-governance-stack-v1/`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                6,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S13",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_inactive_exec_plan_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo)
            exec_plan = repo / "docs" / "exec-plans" / "GOV-0015-item-context-gate.md"
            exec_plan.write_text(exec_plan.read_text(encoding="utf-8") + "- 状态：`inactive for PR #18`\n", encoding="utf-8")
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少 active `exec-plan`" in error for error in errors))

    def test_duplicate_exec_plan_metadata_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo)
            exec_plan = repo / "docs" / "exec-plans" / "GOV-0015-item-context-gate.md"
            exec_plan.write_text(
                exec_plan.read_text(encoding="utf-8") + "- release：`v0.2.0`\n",
                encoding="utf-8",
            )
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("重复键" in error for error in errors))

    def test_unrelated_duplicate_exec_plan_metadata_does_not_block_current_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo, related_decision="docs/decisions/ADR-0001.md")
            exec_plans = repo / "docs" / "exec-plans"
            (exec_plans / "broken-other.md").write_text(
                "\n".join(
                    [
                        "# broken",
                        "",
                        "## 关联信息",
                        "",
                        "- item_key：`GOV-0099-other`",
                        "- item_key：`GOV-0099-other-shadow`",
                        "- Issue：`#99`",
                        "- item_type：`GOV`",
                        "- release：`v0.1.0`",
                        "- sprint：`2026-S14`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            write_decision(repo, "docs/decisions/ADR-0001.md", issue="#19", item_key="GOV-0015-item-context-gate")
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_duplicate_metadata_in_secondary_file_for_same_item_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo)
            exec_plans = repo / "docs" / "exec-plans"
            (exec_plans / "shadow.md").write_text(
                "\n".join(
                    [
                        "# shadow",
                        "",
                        "## 关联信息",
                        "",
                        "- item_key：`GOV-0015-item-context-gate`",
                        "- Issue：`#19`",
                        "- item_type：`GOV`",
                        "- release：`v0.1.0`",
                        "- release：`v0.2.0`",
                        "- sprint：`2026-S14`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("重复键" in error for error in errors))

    def test_duplicate_metadata_in_secondary_file_is_rejected_even_when_duplicate_precedes_item_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo)
            exec_plans = repo / "docs" / "exec-plans"
            (exec_plans / "shadow.md").write_text(
                "\n".join(
                    [
                        "# shadow",
                        "",
                        "## 关联信息",
                        "",
                        "- release：`v0.1.0`",
                        "- release：`v0.2.0`",
                        "- item_key：`GOV-0015-item-context-gate`",
                        "- Issue：`#19`",
                        "- item_type：`GOV`",
                        "- sprint：`2026-S14`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("重复键" in error for error in errors))

    def test_duplicate_active_exec_plans_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo)
            exec_plans = repo / "docs" / "exec-plans"
            (exec_plans / "legacy-duplicate.md").write_text(
                "\n".join(
                    [
                        "# duplicate",
                        "",
                        "## 事项上下文",
                        "",
                        "- Issue：`#19`",
                        "- item_key：`GOV-0015-item-context-gate`",
                        "- item_type：`GOV`",
                        "- release：`v0.1.0`",
                        "- sprint：`2026-S14`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("多个 active `exec-plan`" in error for error in errors))

    def test_different_active_item_under_same_issue_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo)
            exec_plans = repo / "docs" / "exec-plans"
            (exec_plans / "other-item.md").write_text(
                "\n".join(
                    [
                        "# other",
                        "",
                        "## 事项上下文",
                        "",
                        "- Issue：`#19`",
                        "- item_key：`GOV-0014-release-sprint-structure`",
                        "- item_type：`GOV`",
                        "- release：`v0.1.0`",
                        "- sprint：`2026-S14`",
                        "- active 收口事项：`GOV-0014-release-sprint-structure`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("当前 `Issue` 存在多个 active `exec-plan`" in error for error in errors))

    def test_governance_without_issue_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            errors = validate_pr_preflight("governance", None, None, None, None, None, ["AGENTS.md"], repo_root=repo)
        self.assertTrue(any("缺少完整事项上下文" in error for error in errors))

    def test_issue_must_match_current_worktree_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            with patch("scripts.open_pr.REPO_ROOT", repo):
                with patch("scripts.open_pr.git_current_branch", return_value="issue-19-demo"):
                    with patch("scripts.open_pr.load_worktree_binding_for_branch", return_value={"issue": 18, "branch": "issue-19-demo"}):
                        errors = validate_current_worktree_binding(19, repo_root=repo)
        self.assertTrue(any("branch/worktree 绑定的事项不一致" in error for error in errors))

    def test_worktree_path_must_match_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            other = repo / "other"
            other.mkdir()
            with patch("scripts.open_pr.REPO_ROOT", repo):
                with patch("scripts.open_pr.git_current_branch", return_value="issue-19-demo"):
                    with patch(
                        "scripts.open_pr.load_worktree_binding_for_branch",
                        return_value={"issue": 19, "branch": "issue-19-demo", "path": str(other)},
                    ):
                        errors = validate_current_worktree_binding(19, repo_root=repo)
        self.assertTrue(any("worktree `path` 不一致" in error for error in errors))

    def test_binding_check_is_skipped_for_foreign_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            with patch("scripts.open_pr.git_current_branch", return_value="issue-19-demo"):
                with patch(
                    "scripts.open_pr.load_worktree_binding_for_branch",
                    return_value={"issue": 18, "branch": "issue-19-demo"},
                ):
                    errors = validate_current_worktree_binding(19, repo_root=repo)
        self.assertEqual(errors, [])

    def test_branch_read_failure_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            with patch("scripts.open_pr.REPO_ROOT", repo):
                with patch("scripts.open_pr.git_current_branch", side_effect=CommandError(["git"], 1, "", "boom")):
                    errors = validate_current_worktree_binding(19, repo_root=repo)
        self.assertTrue(any("无法识别当前分支" in error for error in errors))

    def test_duplicate_branch_bindings_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            with patch("scripts.open_pr.REPO_ROOT", repo):
                with patch("scripts.open_pr.git_current_branch", return_value="issue-19-demo"):
                    with patch(
                        "scripts.open_pr.load_worktree_binding_for_branch",
                        return_value={"conflict": "multiple_branch_bindings", "branch": "issue-19-demo"},
                    ):
                        errors = validate_current_worktree_binding(19, repo_root=repo)
        self.assertTrue(any("多个 worktree 绑定" in error for error in errors))

    def test_invalid_worktree_state_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            with patch("scripts.open_pr.REPO_ROOT", repo):
                with patch("scripts.open_pr.git_current_branch", return_value="issue-19-demo"):
                    with patch(
                        "scripts.open_pr.load_worktree_binding_for_branch",
                        return_value={"conflict": "invalid_worktree_state", "branch": "issue-19-demo"},
                    ):
                        errors = validate_current_worktree_binding(19, repo_root=repo)
        self.assertTrue(any("`worktrees.json` 已损坏" in error for error in errors))

    def test_invalid_binding_issue_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            with patch("scripts.open_pr.REPO_ROOT", repo):
                with patch("scripts.open_pr.git_current_branch", return_value="issue-19-demo"):
                    with patch(
                        "scripts.open_pr.load_worktree_binding_for_branch",
                        return_value={"issue": "not-a-number", "branch": "issue-19-demo"},
                    ):
                        errors = validate_current_worktree_binding(19, repo_root=repo)
        self.assertTrue(any("`issue` 值非法" in error for error in errors))

    def test_missing_active_exec_plan_for_issue_has_precise_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo)
            exec_plan = repo / "docs" / "exec-plans" / "GOV-0015-item-context-gate.md"
            exec_plan.write_text(exec_plan.read_text(encoding="utf-8") + "- 状态：`inactive for PR #18`\n", encoding="utf-8")
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("当前事项缺少 active `exec-plan`" in error or "当前 `Issue` 缺少 active `exec-plan`" in error for error in errors))

    def test_missing_release_or_sprint_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo)
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                None,
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少完整事项上下文" in error for error in errors))

    def test_invalid_item_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo, item_key="GOV-0015-item-context-gate")
            errors = validate_pr_preflight(
                "governance",
                19,
                "FR-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("`item_key` 必须匹配" in error for error in errors))

    def test_missing_exec_plan_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少 active `exec-plan`" in error for error in errors))

    def test_mismatched_exec_plan_context_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo, release="v0.2.0")
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("active `exec-plan` 的 `release`" in error for error in errors))

    def test_active_item_key_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo, active_item_key="GOV-0014-release-sprint-structure")
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少 active `exec-plan`" in error or "active 收口事项" in error for error in errors))

    def test_core_item_without_spec_or_bootstrap_contract_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo, item_key="FR-0001-governance-stack-v1", issue="#1", item_type="FR")
            errors = validate_pr_preflight(
                "spec",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["docs/process/delivery-funnel.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_core_item_with_valid_formal_spec_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "spec",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["docs/specs/FR-0001-governance-stack-v1/spec.md"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_governance_repo_scan_accepts_valid_bound_formal_spec(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_unrelated_formal_spec_cannot_replace_bound_spec(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_spec="docs/specs/FR-9999-missing/",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("formal spec 或 bootstrap contract" in error or "formal spec 套件" in error for error in errors))

    def test_unrelated_touched_formal_spec_cannot_replace_invalid_bound_spec(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_spec="docs/specs/FR-9999-missing/",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["docs/specs/FR-0001-governance-stack-v1/spec.md"],
                repo_root=repo,
            )
        self.assertTrue(any("formal spec 或 bootstrap contract" in error or "formal spec 套件" in error for error in errors))

    def test_governance_without_bound_spec_cannot_fallback_to_unrelated_repo_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("formal spec 或 bootstrap contract" in error or "formal spec 套件" in error for error in errors))

    def test_legacy_bound_spec_file_path_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_spec="docs/specs/FR-0001-governance-stack-v1/spec.md",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_bound_formal_spec_rejects_unrelated_touched_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
            )
            write_formal_spec_suite(repo, with_todo=False)
            write_formal_spec_suite(repo, suite_name="FR-9999-unrelated", with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                [
                    "docs/specs/FR-0001-governance-stack-v1/spec.md",
                    "docs/specs/FR-9999-unrelated/spec.md",
                ],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_bound_formal_spec_accepts_only_its_own_touched_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["docs/specs/FR-0001-governance-stack-v1/spec.md"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_bound_formal_spec_must_be_reviewable_not_just_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
            )
            suite_dir = repo / "docs" / "specs" / "FR-0001-governance-stack-v1"
            suite_dir.mkdir(parents=True, exist_ok=True)
            (suite_dir / "spec.md").write_text("# spec\n", encoding="utf-8")
            (suite_dir / "plan.md").write_text("# plan\n", encoding="utf-8")
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_template_spec_binding_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_spec="docs/specs/_template/",
            )
            template_dir = repo / "docs" / "specs" / "_template"
            template_dir.mkdir(parents=True, exist_ok=True)
            (template_dir / "spec.md").write_text("# spec\n", encoding="utf-8")
            (template_dir / "plan.md").write_text("# plan\n", encoding="utf-8")
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("formal spec 或 bootstrap contract" in error or "formal spec 套件" in error for error in errors))

    def test_governance_with_bootstrap_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_decision(repo, "docs/decisions/ADR-0001.md", issue="#5", item_key="GOV-0015-item-context-gate")
            write_exec_plan(repo, issue="#5", related_decision="docs/decisions/ADR-0001.md")
            errors = validate_pr_preflight(
                "governance",
                5,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_legacy_placeholder_related_spec_still_uses_bootstrap_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_decision(repo, "docs/decisions/ADR-0001.md", issue="#5", item_key="GOV-0015-item-context-gate")
            write_exec_plan(
                repo,
                issue="#5",
                related_spec="无（治理文档事项）",
                related_decision="docs/decisions/ADR-0001.md",
            )
            errors = validate_pr_preflight(
                "governance",
                5,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_governance_formal_spec_mode_cannot_fallback_to_bootstrap_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_decision(repo, "docs/decisions/ADR-0001.md", issue="#5", item_key="GOV-0015-item-context-gate")
            write_exec_plan(
                repo,
                issue="#5",
                related_spec="docs/specs/FR-9999-missing/",
                related_decision="docs/decisions/ADR-0001.md",
            )
            errors = validate_pr_preflight(
                "governance",
                5,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_governance_with_unrelated_bootstrap_decision_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "docs" / "decisions").mkdir(parents=True)
            (repo / "docs" / "decisions" / "ADR-GOV-9999-unrelated.md").write_text(
                """# ADR-GOV-9999

- Issue：`#999`
- item_key：`GOV-9999-unrelated`
""",
                encoding="utf-8",
            )
            write_exec_plan(repo, issue="#5", related_decision="docs/decisions/ADR-GOV-9999-unrelated.md")
            errors = validate_pr_preflight(
                "governance",
                5,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_governance_bootstrap_contract_requires_valid_current_item_decision_binding(self) -> None:
        scenarios = (
            ("missing", None),
            ("nonexistent", "docs/decisions/ADR-0001-missing.md"),
            ("out_of_repo", "../outside-decision.md"),
            ("wrong_dir", "docs/exec-plans/GOV-0015-item-context-gate.md"),
            ("metadata_free", "docs/decisions/ADR-0002-empty.md"),
            ("duplicate_metadata", "docs/decisions/ADR-0003-duplicate.md"),
        )
        for label, related_decision in scenarios:
            with self.subTest(case=label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo = Path(temp_dir)
                    if related_decision and related_decision.startswith("docs/decisions/"):
                        (repo / "docs" / "decisions").mkdir(parents=True)
                    if label == "metadata_free":
                        (repo / "docs" / "decisions" / "ADR-0002-empty.md").write_text("# ADR\n", encoding="utf-8")
                    if label == "duplicate_metadata":
                        (repo / "docs" / "decisions" / "ADR-0003-duplicate.md").write_text(
                            """# ADR\n\n- Issue：`#5`\n- Issue：`#6`\n- item_key：`GOV-0015-item-context-gate`\n""",
                            encoding="utf-8",
                        )
                    write_exec_plan(repo, issue="#5", related_decision=related_decision)
                    errors = validate_pr_preflight(
                        "governance",
                        5,
                        "GOV-0015-item-context-gate",
                        "GOV",
                        "v0.1.0",
                        "2026-S14",
                        ["AGENTS.md"],
                        repo_root=repo,
                    )
                self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_unrelated_repo_bootstrap_contract_cannot_replace_current_item_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_decision(repo, "docs/decisions/ADR-0001.md", issue="#5", item_key="GOV-0015-item-context-gate")
            write_exec_plan(repo, issue="#5")
            write_exec_plan(
                repo,
                item_key="GOV-9999-unrelated-bootstrap",
                issue="#9999",
                active_item_key="GOV-9999-unrelated-bootstrap",
                related_decision="docs/decisions/ADR-0001.md",
            )
            errors = validate_pr_preflight(
                "governance",
                5,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_spec_class_without_spec_changes_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "docs" / "decisions").mkdir(parents=True)
            (repo / "docs" / "decisions" / "ADR-0001.md").write_text("# adr\n", encoding="utf-8")
            write_exec_plan(repo, item_key="FR-0003-demo-spec", issue="#3", item_type="FR")
            errors = validate_pr_preflight(
                "spec",
                3,
                "FR-0003-demo-spec",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["code_review.md"],
                repo_root=repo,
            )
        self.assertTrue(any("核心文件变更" in error or "正式规约区变更" in error for error in errors))

    def test_spec_pr_rejects_todo_only_changes_without_spec_core_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "spec",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["docs/specs/FR-0001-governance-stack-v1/TODO.md"],
                repo_root=repo,
            )
        self.assertTrue(any("核心文件变更" in error for error in errors))

    def test_spec_pr_rejects_adjunct_only_suite_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
            )
            write_formal_spec_suite(repo, with_todo=False)
            adjunct = repo / "docs" / "specs" / "FR-0001-governance-stack-v1" / "contracts" / "README.md"
            adjunct.parent.mkdir(parents=True, exist_ok=True)
            adjunct.write_text("# contracts\n", encoding="utf-8")
            errors = validate_pr_preflight(
                "spec",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["docs/specs/FR-0001-governance-stack-v1/contracts/README.md"],
                repo_root=repo,
            )
        self.assertTrue(any("核心文件变更" in error for error in errors))

    def test_unbound_fr_item_requires_its_own_touched_formal_spec_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
            )
            write_formal_spec_suite(repo, suite_name="FR-9999-unrelated", with_todo=False)
            errors = validate_pr_preflight(
                "spec",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["docs/specs/FR-9999-unrelated/spec.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_legacy_implementation_pr_accepts_existing_local_formal_spec_suite_for_fr_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "implementation",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["scripts/tool.py"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_implementation_pr_accepts_legacy_metadata_free_adr_for_formal_spec_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0002-content-detail-runtime-v0-1",
                issue="#38",
                item_type="FR",
                active_item_key="FR-0002-content-detail-runtime-v0-1",
                related_spec="docs/specs/FR-0002-content-detail-runtime-v0-1/",
                related_decision="docs/decisions/ADR-0001-governance-bootstrap-contract.md",
            )
            write_formal_spec_suite(repo, suite_name="FR-0002-content-detail-runtime-v0-1", with_todo=False)
            (repo / "docs" / "decisions").mkdir(parents=True, exist_ok=True)
            (repo / "docs" / "decisions" / "ADR-0001-governance-bootstrap-contract.md").write_text(
                "# ADR-0001 bootstrap\n",
                encoding="utf-8",
            )
            errors = validate_pr_preflight(
                "implementation",
                38,
                "FR-0002-content-detail-runtime-v0-1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["scripts/tool.py"],
                repo_root=repo,
                validate_worktree_binding_check=False,
            )
        self.assertEqual(errors, [])

    def test_formal_spec_mode_rejects_inconsistent_optional_related_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
                related_decision="docs/decisions/ADR-0003-shared.md",
            )
            write_formal_spec_suite(repo, with_todo=False)
            write_decision(repo, "docs/decisions/ADR-0003-shared.md", issue="#2", item_key="GOV-0002-other")
            errors = validate_pr_preflight(
                "spec",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["docs/specs/FR-0001-governance-stack-v1/spec.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_spec_pr_does_not_accept_bootstrap_contract_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_decision="docs/decisions/ADR-0003-example.md",
            )
            write_decision(
                repo,
                "docs/decisions/ADR-0003-example.md",
                issue="#57",
                item_key="GOV-0028-harness-compat-migration",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "spec",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["docs/specs/FR-0001-governance-stack-v1/spec.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error for error in errors))

    def test_governance_pr_does_not_accept_unbound_fr_local_formal_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["docs/AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_implementation_pr_requires_local_formal_input_for_fr_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
            )
            errors = validate_pr_preflight(
                "implementation",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["scripts/tool.py"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_implementation_pr_requires_formal_input_for_hotfix_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="HOTFIX-0001-critical-patch",
                issue="#1",
                item_type="HOTFIX",
                active_item_key="HOTFIX-0001-critical-patch",
            )
            errors = validate_pr_preflight(
                "implementation",
                1,
                "HOTFIX-0001-critical-patch",
                "HOTFIX",
                "v0.1.0",
                "2026-S14",
                ["scripts/tool.py"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_implementation_pr_requires_formal_input_for_chore_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="CHORE-0001-doc-refresh",
                issue="#1",
                item_type="CHORE",
                active_item_key="CHORE-0001-doc-refresh",
            )
            errors = validate_pr_preflight(
                "implementation",
                1,
                "CHORE-0001-doc-refresh",
                "CHORE",
                "v0.1.0",
                "2026-S14",
                ["docs/AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_build_body_contains_item_context(self) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--issue",
                "19",
                "--item-key",
                "GOV-0015-item-context-gate",
                "--item-type",
                "GOV",
                "--release",
                "v0.1.0",
                "--sprint",
                "2026-S14",
                "--dry-run",
            ]
        )
        body = build_body(args, ["AGENTS.md"])
        self.assertIn("item_key: `GOV-0015-item-context-gate`", body)
        self.assertIn("item_type: `GOV`", body)
        self.assertIn("release: `v0.1.0`", body)
        self.assertIn("sprint: `2026-S14`", body)
        self.assertIn("- 审查关注：", body)
        self.assertNotIn("## 变更文件", body)
        self.assertNotIn("## 检查清单", body)


if __name__ == "__main__":
    unittest.main()
