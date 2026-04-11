from __future__ import annotations

import unittest

from unittest.mock import patch

from scripts import governance_gate


class GovernanceGateTests(unittest.TestCase):
    @patch("scripts.governance_gate.validate_context_rules", return_value=[])
    @patch("scripts.governance_gate.validate_context_repository", return_value=[])
    @patch("scripts.governance_gate.validate_workflow_repository", return_value=[])
    @patch("scripts.governance_gate.classify_paths", return_value=[])
    @patch("scripts.governance_gate.git_changed_files", return_value=["scripts/context_guard.py"])
    @patch("scripts.governance_gate.git_current_branch", return_value="HEAD")
    def test_prefers_head_ref_for_current_issue_in_ci(
        self,
        current_branch_mock,
        changed_files_mock,
        classify_paths_mock,
        workflow_repo_mock,
        context_repo_mock,
        context_rules_mock,
    ) -> None:
        exit_code = governance_gate.main(["--mode", "ci", "--base-ref", "origin/main", "--head-ref", "issue-57-demo"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(context_rules_mock.call_args.kwargs["current_issue"], 57)
        current_branch_mock.assert_not_called()
        changed_files_mock.assert_called_once()
        classify_paths_mock.assert_called_once_with(["scripts/context_guard.py"])
        workflow_repo_mock.assert_called_once()
        context_repo_mock.assert_called_once()

    @patch("scripts.governance_gate.validate_context_rules", return_value=[])
    @patch("scripts.governance_gate.validate_context_repository", return_value=[])
    @patch("scripts.governance_gate.validate_workflow_repository", return_value=[])
    @patch("scripts.governance_gate.classify_paths", return_value=[])
    @patch("scripts.governance_gate.git_changed_files", return_value=["scripts/context_guard.py"])
    @patch("scripts.governance_gate.git_current_branch", return_value="issue-57-demo")
    def test_falls_back_to_current_branch_when_head_ref_has_no_issue(
        self,
        current_branch_mock,
        changed_files_mock,
        classify_paths_mock,
        workflow_repo_mock,
        context_repo_mock,
        context_rules_mock,
    ) -> None:
        exit_code = governance_gate.main(["--mode", "ci", "--base-ref", "origin/main", "--head-ref", "HEAD"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(context_rules_mock.call_args.kwargs["current_issue"], 57)
        current_branch_mock.assert_called_once()
        changed_files_mock.assert_called_once()
        classify_paths_mock.assert_called_once_with(["scripts/context_guard.py"])
        workflow_repo_mock.assert_called_once()
        context_repo_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
