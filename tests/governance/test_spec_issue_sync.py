from __future__ import annotations

import json
import subprocess
import unittest
from unittest import mock

from scripts import spec_issue_sync


def completed(stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["gh"], returncode=0, stdout=stdout, stderr="")


class SpecIssueSyncTests(unittest.TestCase):
    def test_existing_issue_index_filters_pull_requests(self) -> None:
        with mock.patch.object(
            spec_issue_sync,
            "run",
            return_value=completed(
                json.dumps(
                    [
                        {
                            "number": 155,
                            "title": "[FR-0009-cli-task-query-and-core-path] mirror",
                        },
                        {
                            "number": 280,
                            "title": "[FR-0022-github-api-quota-fallback-hardening] implementation PR",
                            "pull_request": {"url": "https://api.github.com/repos/owner/repo/pulls/280"},
                        },
                    ]
                )
            ),
        ):
            index = spec_issue_sync.existing_issue_index("owner/repo")

        self.assertEqual(index, {"FR-0009-cli-task-query-and-core-path": "155"})

    def test_existing_issue_index_paginates_until_complete(self) -> None:
        first_page = [{"number": index, "title": f"regular issue {index}"} for index in range(100)]
        second_page = [
            {
                "number": 301,
                "title": "[FR-0022-github-api-quota-fallback-hardening] mirror",
            }
        ]
        with mock.patch.object(
            spec_issue_sync,
            "run",
            side_effect=[completed(json.dumps(first_page)), completed(json.dumps(second_page))],
        ) as run:
            index = spec_issue_sync.existing_issue_index("owner/repo")

        self.assertEqual(index, {"FR-0022-github-api-quota-fallback-hardening": "301"})
        self.assertEqual(run.call_count, 2)
        self.assertIn("page=1", run.call_args_list[0].args[0])
        self.assertIn("page=2", run.call_args_list[1].args[0])

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

    def test_upsert_uses_bulk_index_without_search_when_mirror_exists(self) -> None:
        calls: list[list[str]] = []

        def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            calls.append(command)
            return completed()

        with mock.patch.object(spec_issue_sync, "run", side_effect=fake_run):
            spec_issue_sync.upsert_issue(
                "docs/specs/FR-0019-v0-6-operability-release-gate/spec.md",
                "owner/repo",
                {"FR-0019-v0-6-operability-release-gate": "987"},
            )

        self.assertFalse(any("search/issues" in command for command in calls))
        self.assertTrue(
            any(command[:5] == ["gh", "api", "--method", "PATCH", "repos/owner/repo/issues/987"] for command in calls)
        )

    def test_upsert_index_miss_creates_without_per_spec_search(self) -> None:
        calls: list[list[str]] = []

        def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            calls.append(command)
            if command[:4] == ["gh", "api", "--method", "POST"]:
                return completed("988\n")
            return completed()

        with mock.patch.object(spec_issue_sync, "run", side_effect=fake_run):
            spec_issue_sync.upsert_issue(
                "docs/specs/FR-0022-github-api-quota-fallback-hardening/spec.md",
                "owner/repo",
                {"FR-0019-v0-6-operability-release-gate": "987"},
            )

        self.assertFalse(any("search/issues" in command for command in calls))
        self.assertTrue(any(command[:5] == ["gh", "api", "--method", "POST", "repos/owner/repo/issues"] for command in calls))
        self.assertTrue(any(command[:5] == ["gh", "api", "--method", "PATCH", "repos/owner/repo/issues/988"] for command in calls))

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

    def test_main_builds_existing_issue_index_once_for_changed_files(self) -> None:
        files = [
            "docs/specs/FR-0019-v0-6-operability-release-gate/spec.md",
            "docs/specs/FR-0022-github-api-quota-fallback-hardening/spec.md",
        ]
        with mock.patch.object(spec_issue_sync, "require_cli"):
            with mock.patch.object(spec_issue_sync, "run", return_value=completed("mc\n")) as run:
                with mock.patch.object(spec_issue_sync, "changed_spec_files", return_value=files):
                    with mock.patch.object(spec_issue_sync, "existing_issue_index", return_value={"FR-0019-v0-6-operability-release-gate": "987"}) as index:
                        with mock.patch.object(spec_issue_sync, "upsert_issue") as upsert:
                            exit_code = spec_issue_sync.main(["--before-sha", "base", "--repo", "owner/repo"])

        self.assertEqual(exit_code, 0)
        run.assert_called_once_with(["gh", "api", "user", "--jq", ".login"], cwd=spec_issue_sync.REPO_ROOT)
        index.assert_called_once_with("owner/repo")
        self.assertEqual(upsert.call_count, 2)
        self.assertIs(upsert.call_args_list[0].args[2], index.return_value)


if __name__ == "__main__":
    unittest.main()
