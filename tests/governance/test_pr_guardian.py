from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import ANY, patch

from scripts.pr_guardian import (
    find_latest_guardian_result,
    load_guardian_state,
    merge_if_safe,
    run_codex_review,
    save_guardian_result,
)


class GuardianStateTests(unittest.TestCase):
    def test_load_guardian_state_falls_back_to_legacy_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_new = Path(temp_dir) / "missing-guardian.json"
            legacy_path = Path(temp_dir) / "syvert-pr-guardian-results.json"
            legacy_path.write_text('{"prs":{"1":{"verdict":"APPROVE"}}}', encoding="utf-8")

            with patch("scripts.pr_guardian.DEFAULT_STATE_FILE", missing_new):
                with patch("scripts.pr_guardian.guardian_legacy_state_path", return_value=legacy_path):
                    payload = load_guardian_state(missing_new)

            self.assertIn("prs", payload)
            self.assertIn("1", payload["prs"])

    def test_find_latest_guardian_result_uses_local_state_for_matching_head(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "guardian.json"
            save_guardian_result(
                1,
                {
                    "schema_version": 1,
                    "pr_number": 1,
                    "head_sha": "sha-1",
                    "verdict": "APPROVE",
                    "safe_to_merge": True,
                    "summary": "cached",
                    "reviewed_at": "2026-03-28T10:00:00Z",
                },
                path=state_path,
            )

            payload = find_latest_guardian_result(1, "sha-1", path=state_path)

            self.assertIsNotNone(payload)
            self.assertEqual(payload["head_sha"], "sha-1")

    def test_find_latest_guardian_result_rejects_stale_head(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "guardian.json"
            save_guardian_result(
                1,
                {
                    "schema_version": 1,
                    "pr_number": 1,
                    "head_sha": "sha-1",
                    "verdict": "APPROVE",
                    "safe_to_merge": True,
                    "summary": "cached",
                    "reviewed_at": "2026-03-28T10:00:00Z",
                },
                path=state_path,
            )

            payload = find_latest_guardian_result(1, "sha-2", path=state_path)

            self.assertIsNone(payload)


class CodexReviewExecutionTests(unittest.TestCase):
    @patch("scripts.pr_guardian.subprocess.run")
    def test_run_codex_review_falls_back_to_stdout_json(self, subprocess_run_mock) -> None:
        subprocess_run_mock.return_value = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout='{"verdict":"APPROVE","safe_to_merge":true,"summary":"ok","findings":[],"required_actions":[]}',
            stderr="",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_codex_review(Path(temp_dir), "prompt", Path(temp_dir) / "review.json")

        self.assertEqual(result["verdict"], "APPROVE")
        self.assertTrue(result["safe_to_merge"])

    def test_find_latest_guardian_result_rejects_invalid_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "guardian.json"
            save_guardian_result(
                1,
                {
                    "schema_version": 1,
                    "pr_number": 1,
                    "head_sha": "sha-1",
                    "verdict": "MAYBE",
                    "safe_to_merge": True,
                    "summary": "cached",
                    "reviewed_at": "2026-03-28T10:00:00Z",
                },
                path=state_path,
            )

            payload = find_latest_guardian_result(1, "sha-1", path=state_path)

            self.assertIsNone(payload)


class MergeIfSafeTests(unittest.TestCase):
    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_rejects_cached_request_changes(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        run_mock,
    ) -> None:
        pr_meta_mock.return_value = {
            "number": 1,
            "isDraft": False,
            "headRefOid": "sha-request-changes",
        }
        find_result_mock.return_value = {
            "schema_version": 1,
            "pr_number": 1,
            "head_sha": "sha-request-changes",
            "verdict": "REQUEST_CHANGES",
            "safe_to_merge": False,
            "summary": "blocked",
            "reviewed_at": "2026-03-28T10:00:00Z",
        }

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(1, post=False, delete_branch=False, refresh_review=False)

        self.assertIn("guardian 未给出 APPROVE", str(ctx.exception))
        review_once_mock.assert_not_called()
        run_mock.assert_not_called()
        require_auth_mock.assert_called_once()

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_rejects_cached_safe_to_merge_false(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        run_mock,
    ) -> None:
        pr_meta_mock.return_value = {
            "number": 1,
            "isDraft": False,
            "headRefOid": "sha-safe-false",
        }
        find_result_mock.return_value = {
            "schema_version": 1,
            "pr_number": 1,
            "head_sha": "sha-safe-false",
            "verdict": "APPROVE",
            "safe_to_merge": False,
            "summary": "blocked",
            "reviewed_at": "2026-03-28T10:00:00Z",
        }

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(1, post=False, delete_branch=False, refresh_review=False)

        self.assertIn("guardian 认为当前 PR 不安全", str(ctx.exception))
        review_once_mock.assert_not_called()
        run_mock.assert_not_called()
        require_auth_mock.assert_called_once()

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

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_refresh_review_ignores_cached_result(
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
                "headRefOid": "sha-3",
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-3",
            },
        ]
        review_once_mock.return_value = (
            {
                "number": 1,
                "headRefOid": "sha-3",
            },
            {
                "verdict": "APPROVE",
                "safe_to_merge": True,
                "summary": "refreshed",
            },
        )
        run_mock.return_value = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout="", stderr="")

        exit_code = merge_if_safe(1, post=False, delete_branch=False, refresh_review=True)

        self.assertEqual(exit_code, 0)
        find_result_mock.assert_not_called()
        review_once_mock.assert_called_once_with(1, post=False, json_output=None)
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_rejects_when_head_changes_after_cached_review(
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
            "headRefOid": "sha-current",
        }
        find_result_mock.return_value = {
            "schema_version": 1,
            "pr_number": 1,
            "head_sha": "sha-reviewed",
            "verdict": "APPROVE",
            "safe_to_merge": True,
            "summary": "cached",
            "reviewed_at": "2026-03-28T10:00:00Z",
        }

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(1, post=False, delete_branch=False, refresh_review=False)

        self.assertIn("审查后 PR HEAD 已变化", str(ctx.exception))
        review_once_mock.assert_not_called()
        run_mock.assert_not_called()
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_not_called()

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=False)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_rejects_when_checks_not_green_after_cached_review(
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
            "headRefOid": "sha-green-check",
        }
        find_result_mock.return_value = {
            "schema_version": 1,
            "pr_number": 1,
            "head_sha": "sha-green-check",
            "verdict": "APPROVE",
            "safe_to_merge": True,
            "summary": "cached",
            "reviewed_at": "2026-03-28T10:00:00Z",
        }

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(1, post=False, delete_branch=False, refresh_review=False)

        self.assertIn("GitHub checks 未全部通过", str(ctx.exception))
        review_once_mock.assert_not_called()
        run_mock.assert_not_called()
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
