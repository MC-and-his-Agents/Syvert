from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from unittest.mock import patch

from scripts.open_pr import build_body, parse_args, validate_current_worktree_binding, validate_pr_preflight


def write_exec_plan(
    repo: Path,
    *,
    item_key: str = "GOV-0015-item-context-gate",
    issue: str = "#19",
    item_type: str = "GOV",
    release: str = "v0.1.0",
    sprint: str = "2026-S14",
    active_item_key: str = "GOV-0015-item-context-gate",
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
                f"- active 收口事项：`{active_item_key}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


class OpenPrPreflightTests(unittest.TestCase):
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

    def test_governance_without_issue_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            errors = validate_pr_preflight("governance", None, None, None, None, None, ["AGENTS.md"], repo_root=repo)
        self.assertTrue(any("缺少完整事项上下文" in error for error in errors))

    def test_issue_must_match_current_worktree_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            with patch("scripts.open_pr.git_current_branch", return_value="issue-19-demo"):
                with patch("scripts.open_pr.load_worktree_binding_for_branch", return_value={"issue": 18, "branch": "issue-19-demo"}):
                    errors = validate_current_worktree_binding(19, repo_root=repo)
        self.assertTrue(any("branch/worktree 绑定的事项不一致" in error for error in errors))

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
        self.assertTrue(any("active 收口事项" in error for error in errors))

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


if __name__ == "__main__":
    unittest.main()
