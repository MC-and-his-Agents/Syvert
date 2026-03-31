from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import governance_status


class GovernanceStatusTests(unittest.TestCase):
    def test_aggregates_guardian_reviewer_and_worktree_state(self) -> None:
        with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {"7": {"verdict": "APPROVE"}}}):
            with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {"7": {"head_sha": "abc"}}}):
                with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k"}}}):
                    with patch("scripts.governance_status.fetch_pr_meta", return_value={"headRefOid": "sha-1", "headRefName": "feature/x", "body": "item_key: `GOV-0015-item-context-gate`"}):
                        with patch("scripts.governance_status.find_latest_guardian_result", return_value={"verdict": "APPROVE", "head_sha": "sha-1"}):
                            with patch("scripts.governance_status.fetch_checks_summary", return_value=[{"name": "check", "bucket": "pass", "state": "SUCCESS"}]):
                                with patch(
                                    "scripts.governance_status.load_item_context_from_exec_plan",
                                    return_value={
                                        "Issue": "19",
                                        "item_key": "GOV-0015-item-context-gate",
                                        "item_type": "GOV",
                                        "release": "v0.1.0",
                                        "sprint": "2026-S14",
                                        "exec_plan": "docs/exec-plans/GOV-0015-item-context-gate.md",
                                    },
                                ):
                                    payload = governance_status.build_status_payload(pr_number=7)

        self.assertEqual(payload["guardian"]["verdict"], "APPROVE")
        self.assertEqual(payload["review_poller"]["head_sha"], "abc")
        self.assertEqual(len(payload["worktrees"]), 1)
        self.assertEqual(payload["checks"][0]["name"], "check")
        self.assertEqual(payload["item_context"]["item_key"], "GOV-0015-item-context-gate")

    def test_pr_without_active_exec_plan_returns_empty_item_context(self) -> None:
        with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
            with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k", "issue": 19}}}):
                    with patch("scripts.governance_status.fetch_pr_meta", return_value={"headRefOid": "sha-1", "headRefName": "feature/x", "body": ""}):
                        with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                            with patch("scripts.governance_status.matching_exec_plan_for_issue", return_value={}):
                                payload = governance_status.build_status_payload(pr_number=7)

        self.assertEqual(payload["item_context"], {})

    def test_issue_status_ignores_inactive_legacy_exec_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            exec_plans = repo / "docs" / "exec-plans"
            exec_plans.mkdir(parents=True, exist_ok=True)
            (exec_plans / "legacy.md").write_text(
                "\n".join(
                    [
                        "# legacy",
                        "",
                        "## 事项上下文",
                        "",
                        "- Issue：`#6`",
                        "- item_key：`FR-0001-governance-stack-v1`",
                        "- item_type：`FR`",
                        "- release：`v0.1.0`",
                        "- sprint：`2026-S13`",
                        "- 状态：`inactive for PR #15`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with patch("scripts.governance_status.REPO_ROOT", repo):
                payload = governance_status.build_status_payload(issue_number=6)

        self.assertEqual(payload["item_context"], {})

    def test_pr_status_ignores_inactive_exec_plan_from_pr_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            exec_plans = repo / "docs" / "exec-plans"
            exec_plans.mkdir(parents=True, exist_ok=True)
            (exec_plans / "GOV-0015-item-context-gate.md").write_text(
                "\n".join(
                    [
                        "# plan",
                        "",
                        "## 关联信息",
                        "",
                        "- Issue：`#19`",
                        "- item_key：`GOV-0015-item-context-gate`",
                        "- item_type：`GOV`",
                        "- release：`v0.1.0`",
                        "- sprint：`2026-S14`",
                        "- 状态：`inactive for PR #18`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            with patch("scripts.governance_status.REPO_ROOT", repo):
                with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
                    with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                        with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k"}}}):
                            with patch("scripts.governance_status.fetch_pr_meta", return_value={"headRefOid": "sha-1", "headRefName": "feature/x", "body": "item_key: `GOV-0015-item-context-gate`"}):
                                with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                                    payload = governance_status.build_status_payload(pr_number=20)

        self.assertEqual(payload["item_context"], {})

    def test_pr_status_does_not_fallback_to_other_issue_plan_when_body_item_key_misses(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            exec_plans = repo / "docs" / "exec-plans"
            exec_plans.mkdir(parents=True, exist_ok=True)
            (exec_plans / "other-active.md").write_text(
                "\n".join(
                    [
                        "# other",
                        "",
                        "## 关联信息",
                        "",
                        "- Issue：`#19`",
                        "- item_key：`GOV-0014-release-sprint-structure`",
                        "- item_type：`GOV`",
                        "- release：`v0.1.0`",
                        "- sprint：`2026-S14`",
                        "- active 收口事项：`GOV-0014-release-sprint-structure`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            with patch("scripts.governance_status.REPO_ROOT", repo):
                with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
                    with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                        with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k", "issue": 19}}}):
                            with patch(
                                "scripts.governance_status.fetch_pr_meta",
                                return_value={
                                    "headRefOid": "sha-1",
                                    "headRefName": "feature/x",
                                    "body": "Issue: #19\nitem_key: `GOV-0015-item-context-gate`\nitem_type: `GOV`\nrelease: `v0.1.0`\nsprint: `2026-S14`\n",
                                },
                            ):
                                with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                                    payload = governance_status.build_status_payload(pr_number=20)

        self.assertEqual(payload["item_context"], {})

    def test_load_state_with_legacy_reads_legacy_when_primary_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            primary = root / "new.json"
            legacy = root / "legacy.json"
            legacy.write_text(json.dumps({"prs": {"1": {"head_sha": "legacy-sha"}}}), encoding="utf-8")

            payload = governance_status.load_state_with_legacy(primary, legacy)

        self.assertIn("prs", payload)
        self.assertEqual(payload["prs"]["1"]["head_sha"], "legacy-sha")

    def test_text_and_json_outputs_are_consistent(self) -> None:
        sample = {
            "guardian": {"verdict": "APPROVE", "safe_to_merge": True, "head_sha": "sha-x", "reviewed_at": "2026-03-29T10:00:00Z"},
            "review_poller": {"head_sha": "sha-x", "reviewed_at": "2026-03-29T10:00:01Z"},
            "worktrees": [{"key": "issue-1-demo", "branch": "issue-1-demo", "path": "/tmp/demo"}],
            "item_context": {
                "Issue": "19",
                "item_key": "GOV-0015-item-context-gate",
                "item_type": "GOV",
                "release": "v0.1.0",
                "sprint": "2026-S14",
                "exec_plan": "docs/exec-plans/GOV-0015-item-context-gate.md",
            },
            "checks": [{"name": "Validate Governance Tooling", "bucket": "pass", "state": "SUCCESS"}],
        }

        text_output = governance_status.render_text(sample)
        json_output = json.loads(json.dumps(sample, ensure_ascii=False))

        self.assertIn("verdict=APPROVE", text_output)
        self.assertIn("count=1", text_output)
        self.assertIn("item_key=GOV-0015-item-context-gate", text_output)
        self.assertEqual(json_output["guardian"]["head_sha"], "sha-x")
        self.assertEqual(len(json_output["worktrees"]), 1)


if __name__ == "__main__":
    unittest.main()
