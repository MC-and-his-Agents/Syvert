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
                f"- active 收口事项：`{active_item_key}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_formal_spec_suite(repo: Path, *, with_todo: bool = False) -> None:
    fr_dir = repo / "docs" / "specs" / "FR-0001-governance-stack-v1"
    fr_dir.mkdir(parents=True, exist_ok=True)
    (fr_dir / "spec.md").write_text("# spec\n", encoding="utf-8")
    (fr_dir / "plan.md").write_text("# plan\n", encoding="utf-8")
    if with_todo:
        (fr_dir / "TODO.md").write_text("# todo\n", encoding="utf-8")


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
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (repo / "docs" / "decisions").mkdir(parents=True)
            (repo / "docs" / "decisions" / "ADR-0001.md").write_text("# adr\n", encoding="utf-8")
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
            write_exec_plan(repo)
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
            (repo / "docs" / "decisions").mkdir(parents=True)
            (repo / "docs" / "decisions" / "ADR-0001.md").write_text("# adr\n", encoding="utf-8")
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
        self.assertTrue(any("formal spec 或 bootstrap contract" in error for error in errors))

    def test_core_item_with_new_minimal_formal_spec_passes_without_todo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo, item_key="FR-0001-governance-stack-v1", issue="#1", item_type="FR", active_item_key="FR-0001-governance-stack-v1")
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

    def test_governance_repo_scan_accepts_minimal_formal_spec_without_todo(self) -> None:
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
            (repo / "docs" / "decisions").mkdir(parents=True)
            (repo / "docs" / "decisions" / "ADR-0001.md").write_text("# adr\n", encoding="utf-8")
            write_exec_plan(repo, issue="#5")
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
        self.assertTrue(any("必须包含正式规约区变更" in error for error in errors))

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
