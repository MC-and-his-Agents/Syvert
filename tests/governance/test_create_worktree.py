from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import create_worktree


class CreateWorktreeTests(unittest.TestCase):
    def test_path_naming_uses_issue_number_and_slug(self) -> None:
        contract = {
            "workspace": {
                "root": "$SYVERT_WORKSPACE_ROOT",
                "naming": "issue-{number}-{slug}",
            }
        }
        metadata = create_worktree.build_worktree_metadata(12, "Fix Parser Regression", contract)
        self.assertEqual(metadata["key"], "issue-12-fix-parser-regression")
        self.assertEqual(metadata["branch"], "issue-12-fix-parser-regression")

    @patch("scripts.create_worktree.save_state")
    @patch("scripts.create_worktree.find_existing_worktree", return_value=False)
    @patch("scripts.create_worktree.git_head_sha", return_value="base-sha")
    @patch("scripts.create_worktree.issue_title_for_number", return_value="Bootstrap Harness")
    @patch("scripts.create_worktree.load_workflow_contract")
    @patch("scripts.create_worktree.run")
    def test_dry_run_does_not_persist_state_or_add_worktree(
        self,
        run_mock,
        load_contract_mock,
        issue_title_mock,
        git_head_sha_mock,
        find_existing_mock,
        save_state_mock,
    ) -> None:
        load_contract_mock.return_value = (
            {
                "workspace": {
                    "root": "$SYVERT_WORKSPACE_ROOT",
                    "naming": "issue-{number}-{slug}",
                }
            },
            "",
        )
        run_mock.return_value.returncode = 0

        payload = create_worktree.ensure_worktree(88, "governance", "main", dry_run=True)

        self.assertEqual(payload["issue"], 88)
        self.assertFalse(payload["reused"])
        self.assertFalse(any(call.args and call.args[0][:3] == ["git", "worktree", "add"] for call in run_mock.mock_calls))
        save_state_mock.assert_not_called()
        issue_title_mock.assert_called_once_with(88)
        git_head_sha_mock.assert_called_once_with("origin/main")
        find_existing_mock.assert_called_once()

    @patch("scripts.create_worktree.save_state")
    @patch("scripts.create_worktree.load_state", return_value={"worktrees": {}})
    @patch("scripts.create_worktree.find_existing_worktree", return_value=True)
    @patch("scripts.create_worktree.git_head_sha", return_value="base-sha")
    @patch("scripts.create_worktree.issue_title_for_number", return_value="Reuse Existing")
    @patch("scripts.create_worktree.load_workflow_contract")
    @patch("scripts.create_worktree.run")
    def test_existing_worktree_is_reused(
        self,
        run_mock,
        load_contract_mock,
        issue_title_mock,
        git_head_sha_mock,
        find_existing_mock,
        load_state_mock,
        save_state_mock,
    ) -> None:
        load_contract_mock.return_value = (
            {
                "workspace": {
                    "root": "$SYVERT_WORKSPACE_ROOT",
                    "naming": "issue-{number}-{slug}",
                }
            },
            "",
        )
        run_mock.return_value.returncode = 0
        run_mock.return_value.stdout = ""

        payload = create_worktree.ensure_worktree(99, "implementation", "main", dry_run=False)

        self.assertTrue(payload["reused"])
        self.assertFalse(any(call.args and call.args[0][:3] == ["git", "worktree", "add"] for call in run_mock.mock_calls))
        save_state_mock.assert_called_once()
        load_state_mock.assert_called_once()
        issue_title_mock.assert_called_once_with(99)
        git_head_sha_mock.assert_called_once_with("origin/main")
        find_existing_mock.assert_called_once()

    def test_missing_issue_argument_is_rejected(self) -> None:
        with self.assertRaises(SystemExit):
            create_worktree.parse_args(["--class", "governance"])

    def test_invalid_class_is_rejected(self) -> None:
        with self.assertRaises(SystemExit):
            create_worktree.parse_args(["--issue", "1", "--class", "invalid"])


if __name__ == "__main__":
    unittest.main()
