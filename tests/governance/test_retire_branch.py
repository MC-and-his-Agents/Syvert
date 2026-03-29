from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import ANY, patch

from scripts import retire_branch


class RetireBranchTests(unittest.TestCase):
    def test_archive_tag_name_is_deterministic(self) -> None:
        self.assertEqual(
            retire_branch.archive_tag_name("codex/repo-governance"),
            "archive/branches/codex/repo-governance",
        )

    def test_worktree_state_keys_for_branch_filters_matching_entries(self) -> None:
        state = {
            "worktrees": {
                "issue-8-demo": {"branch": "issue-8-demo"},
                "legacy": {"branch": "codex/repo-governance"},
            }
        }
        self.assertEqual(
            retire_branch.worktree_state_keys_for_branch("codex/repo-governance", state),
            ["legacy"],
        )

    def test_prune_worktree_state_removes_matching_branch_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "worktrees.json"
            state_path.write_text(
                '{"worktrees":{"keep":{"branch":"main"},"drop":{"branch":"codex/repo-governance"}}}',
                encoding="utf-8",
            )

            removed = retire_branch.prune_worktree_state("codex/repo-governance", path=state_path)

            self.assertEqual(removed, ["drop"])
            payload = retire_branch.load_worktree_state(state_path)
            self.assertIn("keep", payload["worktrees"])
            self.assertNotIn("drop", payload["worktrees"])

    @patch("scripts.retire_branch.run")
    @patch("scripts.retire_branch.load_worktree_state")
    @patch("scripts.retire_branch.archive_tag_exists", return_value=False)
    @patch("scripts.retire_branch.git_rev_parse", return_value="sha-1")
    @patch("scripts.retire_branch.branch_attached_to_worktree", return_value=False)
    @patch("scripts.retire_branch.git_worktree_entries", return_value=[])
    @patch("scripts.retire_branch.git_current_branch", return_value="main")
    @patch("scripts.retire_branch.git_local_branch_exists", return_value=True)
    @patch("scripts.retire_branch.require_cli")
    def test_dry_run_reports_actions_without_mutation(
        self,
        require_cli_mock,
        local_exists_mock,
        current_branch_mock,
        worktrees_mock,
        attached_mock,
        rev_parse_mock,
        archive_exists_mock,
        load_state_mock,
        run_mock,
    ) -> None:
        load_state_mock.return_value = {"worktrees": {"legacy": {"branch": "codex/repo-governance"}}}

        payload = retire_branch.retire_branch(
            "codex/repo-governance",
            replaced_by="main",
            strategy="superseded",
            reason="absorbed by PR #1",
            delete_remote=True,
            dry_run=True,
        )

        self.assertEqual(payload["archive_tag"], "archive/branches/codex/repo-governance")
        self.assertEqual(payload["state_keys_removed"], ["legacy"])
        self.assertIn("git push origin --delete codex/repo-governance", payload["actions"])
        run_mock.assert_not_called()
        require_cli_mock.assert_called_once_with("git")
        local_exists_mock.assert_called_once()
        current_branch_mock.assert_called_once()
        worktrees_mock.assert_called_once()
        attached_mock.assert_called_once()
        rev_parse_mock.assert_called_once()
        archive_exists_mock.assert_called_once()

    @patch("scripts.retire_branch.branch_attached_to_worktree", return_value=True)
    @patch("scripts.retire_branch.git_worktree_entries", return_value=[{"branch": "refs/heads/codex/repo-governance"}])
    @patch("scripts.retire_branch.git_current_branch", return_value="main")
    @patch("scripts.retire_branch.git_local_branch_exists", return_value=True)
    @patch("scripts.retire_branch.require_cli")
    def test_rejects_branch_with_attached_worktree(
        self,
        require_cli_mock,
        local_exists_mock,
        current_branch_mock,
        worktrees_mock,
        attached_mock,
    ) -> None:
        with self.assertRaises(SystemExit) as ctx:
            retire_branch.retire_branch(
                "codex/repo-governance",
                replaced_by="main",
                strategy="superseded",
                reason="absorbed by PR #1",
                delete_remote=False,
                dry_run=False,
            )

        self.assertIn("仍绑定活跃 worktree", str(ctx.exception))
        require_cli_mock.assert_called_once_with("git")

    @patch("scripts.retire_branch.prune_worktree_state", return_value=["legacy"])
    @patch("scripts.retire_branch.run")
    @patch("scripts.retire_branch.load_worktree_state", return_value={"worktrees": {"legacy": {"branch": "codex/repo-governance"}}})
    @patch("scripts.retire_branch.archive_tag_exists", return_value=False)
    @patch("scripts.retire_branch.git_rev_parse", return_value="sha-1")
    @patch("scripts.retire_branch.branch_attached_to_worktree", return_value=False)
    @patch("scripts.retire_branch.git_worktree_entries", return_value=[])
    @patch("scripts.retire_branch.git_current_branch", return_value="main")
    @patch("scripts.retire_branch.git_local_branch_exists", return_value=True)
    @patch("scripts.retire_branch.require_cli")
    def test_retire_branch_executes_tag_push_delete_and_state_prune(
        self,
        require_cli_mock,
        local_exists_mock,
        current_branch_mock,
        worktrees_mock,
        attached_mock,
        rev_parse_mock,
        archive_exists_mock,
        load_state_mock,
        run_mock,
        prune_state_mock,
    ) -> None:
        run_mock.return_value = subprocess.CompletedProcess(args=["git"], returncode=0, stdout="", stderr="")

        payload = retire_branch.retire_branch(
            "codex/repo-governance",
            replaced_by="main",
            strategy="superseded",
            reason="absorbed by PR #1",
            delete_remote=True,
            dry_run=False,
        )

        self.assertEqual(payload["state_keys_removed"], ["legacy"])
        prune_state_mock.assert_called_once_with("codex/repo-governance")
        commands = [call.args[0] for call in run_mock.mock_calls]
        self.assertIn(["git", "tag", "-a", "archive/branches/codex/repo-governance", "sha-1", "-m", ANY], commands)
        self.assertIn(["git", "push", "origin", "refs/tags/archive/branches/codex/repo-governance"], commands)
        self.assertIn(["git", "branch", "-D", "codex/repo-governance"], commands)
        require_cli_mock.assert_called_once_with("git")

    @patch("scripts.retire_branch.branch_is_ancestor", return_value=False)
    @patch("scripts.retire_branch.branch_attached_to_worktree", return_value=False)
    @patch("scripts.retire_branch.git_worktree_entries", return_value=[])
    @patch("scripts.retire_branch.git_current_branch", return_value="main")
    @patch("scripts.retire_branch.git_local_branch_exists", return_value=True)
    @patch("scripts.retire_branch.require_cli")
    def test_merged_strategy_requires_true_ancestry(
        self,
        require_cli_mock,
        local_exists_mock,
        current_branch_mock,
        worktrees_mock,
        attached_mock,
        is_ancestor_mock,
    ) -> None:
        with self.assertRaises(SystemExit) as ctx:
            retire_branch.retire_branch(
                "codex/remove-soft-collab-language",
                replaced_by="main",
                strategy="merged",
                reason=None,
                delete_remote=False,
                dry_run=False,
            )

        self.assertIn("不能按 merged 策略退役", str(ctx.exception))
        is_ancestor_mock.assert_called_once_with("codex/remove-soft-collab-language", "main", repo_root=retire_branch.REPO_ROOT)


if __name__ == "__main__":
    unittest.main()
