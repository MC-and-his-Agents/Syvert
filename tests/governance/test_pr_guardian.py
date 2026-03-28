from __future__ import annotations

import subprocess
import unittest
from unittest.mock import ANY, patch

from scripts.pr_guardian import build_review_markdown, extract_guardian_payload, merge_if_safe


class GuardianMarkerTests(unittest.TestCase):
    def test_review_markdown_round_trips_guardian_payload(self) -> None:
        payload = {
            "schema_version": 1,
            "pr_number": 1,
            "head_sha": "abc123",
            "verdict": "APPROVE",
            "safe_to_merge": True,
            "summary": "Looks good.",
            "reviewed_at": "2026-03-28T10:00:00Z",
        }
        markdown = build_review_markdown(
            {"verdict": "APPROVE", "safe_to_merge": True, "summary": "Looks good.", "findings": [], "required_actions": []},
            payload,
            include_marker=True,
        )

        extracted = extract_guardian_payload(markdown)
        self.assertEqual(extracted, payload)


class MergeIfSafeTests(unittest.TestCase):
    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_reuses_existing_guardian_result(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        pr_meta_mock.return_value = {
            "number": 1,
            "isDraft": False,
            "headRefOid": "sha-1",
        }
        find_result_mock.return_value = {
            "schema_version": 1,
            "pr_number": 1,
            "head_sha": "sha-1",
            "verdict": "APPROVE",
            "safe_to_merge": True,
            "summary": "cached",
            "reviewed_at": "2026-03-28T10:00:00Z",
        }
        run_mock.return_value = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout="", stderr="")

        exit_code = merge_if_safe(1, post=False, delete_branch=False, refresh_review=False)

        self.assertEqual(exit_code, 0)
        review_once_mock.assert_not_called()
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)
        run_mock.assert_called_once_with(
            ["gh", "pr", "merge", "1", "--squash", "--match-head-commit", "sha-1"],
            cwd=ANY,
        )

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result", return_value=None)
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_runs_review_when_no_cached_result(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        pr_meta_mock.side_effect = [
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-2",
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-2",
            },
        ]
        review_once_mock.return_value = (
            {
                "number": 1,
                "headRefOid": "sha-2",
            },
            {
                "verdict": "APPROVE",
                "safe_to_merge": True,
                "summary": "fresh",
            },
        )
        run_mock.return_value = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout="", stderr="")

        exit_code = merge_if_safe(1, post=False, delete_branch=True, refresh_review=False)

        self.assertEqual(exit_code, 0)
        review_once_mock.assert_called_once_with(1, post=False, json_output=None)
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)
        run_mock.assert_called_once_with(
            ["gh", "pr", "merge", "1", "--squash", "--match-head-commit", "sha-2", "--delete-branch"],
            cwd=ANY,
        )


if __name__ == "__main__":
    unittest.main()
