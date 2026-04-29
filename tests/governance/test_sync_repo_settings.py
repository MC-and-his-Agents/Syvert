from __future__ import annotations

import subprocess
import unittest
from unittest import mock

from scripts import sync_repo_settings


def completed(
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["gh"], returncode=returncode, stdout=stdout, stderr=stderr)


class SyncRepoSettingsTests(unittest.TestCase):
    def test_current_rulesets_hard_fails_when_read_fails(self) -> None:
        with mock.patch.object(
            sync_repo_settings,
            "run",
            return_value=completed(stderr="rate limit exceeded", returncode=1),
        ):
            with self.assertRaises(SystemExit) as raised:
                sync_repo_settings.current_rulesets("owner/repo")

        self.assertEqual(str(raised.exception), "rate limit exceeded")

    def test_main_does_not_write_when_rulesets_read_fails(self) -> None:
        with (
            mock.patch.object(sync_repo_settings, "require_cli"),
            mock.patch.object(
                sync_repo_settings,
                "current_repo_settings",
                return_value=sync_repo_settings.desired_repo_settings(),
            ),
            mock.patch.object(
                sync_repo_settings,
                "current_branch_protection",
                return_value=sync_repo_settings.desired_branch_protection(),
            ),
            mock.patch.object(
                sync_repo_settings,
                "current_rulesets",
                side_effect=SystemExit("rulesets unavailable"),
            ),
            mock.patch.object(sync_repo_settings, "run_gh_with_json") as run_gh_with_json,
        ):
            with self.assertRaises(SystemExit) as raised:
                sync_repo_settings.main(["--repo", "owner/repo"])

        self.assertEqual(str(raised.exception), "rulesets unavailable")
        run_gh_with_json.assert_not_called()


if __name__ == "__main__":
    unittest.main()
