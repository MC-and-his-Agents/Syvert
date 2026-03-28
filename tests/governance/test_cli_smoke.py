from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


class CliSmokeTests(unittest.TestCase):
    def test_help_commands_exit_zero(self) -> None:
        commands = [
            "scripts/open_pr.py",
            "scripts/pr_guardian.py",
            "scripts/merge_pr.py",
            "scripts/review_poller.py",
            "scripts/spec_issue_sync.py",
            "scripts/start_sprint.py",
        ]
        for command in commands:
            with self.subTest(command=command):
                result = run_script(command, "--help")
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_start_sprint_dry_run(self) -> None:
        result = run_script("scripts/start_sprint.py", "--name", "sprint-test", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Dry run", result.stdout)


if __name__ == "__main__":
    unittest.main()
