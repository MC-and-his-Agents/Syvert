from __future__ import annotations

import json
import subprocess
import unittest
from unittest import mock

from scripts import spec_issue_sync


def completed(stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["gh"], returncode=0, stdout=stdout, stderr="")


class SpecIssueSyncTests(unittest.TestCase):
    def test_existing_issue_number_finds_closed_mirror_by_title(self) -> None:
        with mock.patch.object(
            spec_issue_sync,
            "run",
            return_value=completed(
                json.dumps(
                    {
                        "items": [
                            {
                                "number": 155,
                                "state": "closed",
                                "title": "[FR-0009-cli-task-query-and-core-path] FR-0009 CLI task query and core path",
                            }
                        ]
                    }
                )
            ),
        ) as run:
            issue_number = spec_issue_sync.existing_issue_number("FR-0009-cli-task-query-and-core-path", "owner/repo")

        self.assertEqual(issue_number, "155")
        self.assertEqual(run.call_args.args[0][0:4], ["gh", "api", "--method", "GET"])
        self.assertIn("search/issues", run.call_args.args[0])
        self.assertIn('q=repo:owner/repo "[FR-0009-cli-task-query-and-core-path]" in:title type:issue', run.call_args.args[0])
        self.assertNotIn("state:open", " ".join(run.call_args.args[0]))

    def test_upsert_existing_spec_mirror_updates_and_closes_issue(self) -> None:
        calls: list[list[str]] = []

        def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            calls.append(command)
            if command[:4] == ["gh", "api", "--method", "GET"]:
                return completed(json.dumps({"items": [{"number": 155, "title": "[FR-0009-cli-task-query-and-core-path] old"}]}))
            return completed()

        with mock.patch.object(spec_issue_sync, "run", side_effect=fake_run):
            spec_issue_sync.upsert_issue("docs/specs/FR-0009-cli-task-query-and-core-path/spec.md", "owner/repo")

        self.assertTrue(any(command[:4] == ["gh", "api", "--method", "GET"] for command in calls))
        self.assertFalse(any(command[:4] == ["gh", "api", "--method", "POST"] for command in calls))
        self.assertTrue(
            any(
                command[:5] == ["gh", "api", "--method", "PATCH", "repos/owner/repo/issues/155"]
                and any(item.startswith("title=[FR-0009-cli-task-query-and-core-path] ") for item in command)
                and any(item.startswith("body=") for item in command)
                for command in calls
            )
        )
        self.assertTrue(
            any(
                command[:5] == ["gh", "api", "--method", "PATCH", "repos/owner/repo/issues/155"]
                and "state=closed" in command
                and "state_reason=not_planned" in command
                for command in calls
            )
        )

    def test_upsert_new_spec_mirror_creates_and_closes_issue(self) -> None:
        calls: list[list[str]] = []

        def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            calls.append(command)
            if command[:4] == ["gh", "api", "--method", "GET"]:
                return completed(json.dumps({"items": []}))
            if command[:4] == ["gh", "api", "--method", "POST"]:
                return completed("987\n")
            return completed()

        with mock.patch.object(spec_issue_sync, "run", side_effect=fake_run):
            spec_issue_sync.upsert_issue("docs/specs/FR-0019-v0-6-operability-release-gate/spec.md", "owner/repo")

        self.assertTrue(
            any(
                command[:5] == ["gh", "api", "--method", "POST", "repos/owner/repo/issues"]
                and any(item.startswith("title=[FR-0019-v0-6-operability-release-gate] ") for item in command)
                and any(item.startswith("body=") for item in command)
                and "--jq" in command
                and ".number" in command
                for command in calls
            )
        )
        self.assertTrue(
            any(
                command[:5] == ["gh", "api", "--method", "PATCH", "repos/owner/repo/issues/987"]
                and "state=closed" in command
                and "state_reason=not_planned" in command
                for command in calls
            )
        )


if __name__ == "__main__":
    unittest.main()
