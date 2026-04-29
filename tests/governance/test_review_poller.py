from __future__ import annotations

import copy
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import review_poller


def open_pr(
    *,
    number: int = 42,
    head_sha: str = "head-sha",
    base_branch: str = "main",
    milestone: str = "Sprint 1",
    pr_class: str = "implementation",
    is_draft: bool = False,
) -> dict[str, object]:
    return {
        "number": number,
        "title": "Demo PR",
        "headRefOid": head_sha,
        "headRefName": "feature/demo",
        "isDraft": is_draft,
        "baseRefName": base_branch,
        "milestone": {"title": milestone},
        "body": f"PR Class: `{pr_class}`",
    }


class ReviewPollerTests(unittest.TestCase):
    def test_unchanged_pr_with_matching_filters_skips_guardian_and_state_write(self) -> None:
        state = {"prs": {"42": {"head_sha": "head-sha"}}}
        original_state = copy.deepcopy(state)

        with patch("scripts.review_poller.require_cli"):
            with patch("scripts.review_poller.ensure_state_file"):
                with patch("scripts.review_poller.load_json", return_value=state):
                    with patch("scripts.review_poller.list_open_prs", return_value=[open_pr()]):
                        with patch("scripts.review_poller.review_pr") as review_pr:
                            with patch("scripts.review_poller.dump_json") as dump_json:
                                exit_code = review_poller.main(
                                    [
                                        "--state-file",
                                        "/tmp/review-poller.json",
                                        "--milestone",
                                        "Sprint 1",
                                        "--pr-class",
                                        "implementation",
                                    ]
                                )

        self.assertEqual(exit_code, 0)
        review_pr.assert_not_called()
        dump_json.assert_not_called()
        self.assertEqual(state, original_state)

    def test_head_change_triggers_guardian_once_and_updates_state_after_success(self) -> None:
        state = {"prs": {"42": {"head_sha": "old-sha"}}}

        with patch("scripts.review_poller.require_cli"):
            with patch("scripts.review_poller.ensure_state_file"):
                with patch("scripts.review_poller.load_json", return_value=state):
                    with patch("scripts.review_poller.list_open_prs", return_value=[open_pr(head_sha="new-sha")]):
                        with patch("scripts.review_poller.review_pr") as review_pr:
                            with patch("scripts.review_poller.dump_json") as dump_json:
                                exit_code = review_poller.main(["--state-file", "/tmp/review-poller.json"])

        self.assertEqual(exit_code, 0)
        review_pr.assert_called_once_with(42, post_review=True)
        dump_json.assert_called_once()
        state_path, dumped_state = dump_json.call_args.args
        self.assertEqual(state_path, Path("/tmp/review-poller.json"))
        self.assertEqual(dumped_state["prs"]["42"], {"head_sha": "new-sha"})

    def test_guardian_failure_does_not_update_state(self) -> None:
        state = {"prs": {"42": {"head_sha": "old-sha"}}}
        original_state = copy.deepcopy(state)

        with patch("scripts.review_poller.require_cli"):
            with patch("scripts.review_poller.ensure_state_file"):
                with patch("scripts.review_poller.load_json", return_value=state):
                    with patch("scripts.review_poller.list_open_prs", return_value=[open_pr(head_sha="new-sha")]):
                        with patch("scripts.review_poller.review_pr", side_effect=RuntimeError("guardian failed")):
                            with patch("scripts.review_poller.dump_json") as dump_json:
                                with self.assertRaisesRegex(RuntimeError, "guardian failed"):
                                    review_poller.main(["--state-file", "/tmp/review-poller.json"])

        dump_json.assert_not_called()
        self.assertEqual(state, original_state)


if __name__ == "__main__":
    unittest.main()
